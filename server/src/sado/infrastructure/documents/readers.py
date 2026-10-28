"""Plain-text reading of document papers: PDF, Office, OpenDocument and web files."""

import io
import re
import zipfile
from collections.abc import Mapping
from html.parser import HTMLParser
from xml.etree import ElementTree

import olefile
import openpyxl
import xlrd
from pypdf import PdfReader

from sado.domain.errors import UnreadablePaperError, UnsupportedPaperError
from sado.domain.vision import DocumentReader, Paper, decode_text


def _checked(text: str) -> str:
    if not text.strip():
        raise UnreadablePaperError
    return text


class PdfTextReader:
    def read(self, paper: Paper) -> str:
        try:
            reader = PdfReader(io.BytesIO(paper.data))
            locked = reader.is_encrypted and reader.decrypt("") == 0
            text = "" if locked else "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as error:
            raise UnreadablePaperError from error
        return _checked(text)


class DocxTextReader:
    _DOCUMENT_XML = "word/document.xml"
    _PARAGRAPH = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
    _TEXT_RUN = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"

    def read(self, paper: Paper) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(paper.data)) as docx:
                xml = docx.read(self._DOCUMENT_XML)
            root = ElementTree.fromstring(xml)
        except Exception as error:
            raise UnreadablePaperError from error
        lines = [
            "".join(run.text or "" for run in paragraph.iter(self._TEXT_RUN))
            for paragraph in root.iter(self._PARAGRAPH)
        ]
        return _checked("\n".join(lines))


class DocTextReader:
    """Best-effort reading of legacy .doc files, whose text mixes with binary."""

    _WORD_STREAM = "WordDocument"
    _TEXT_RUN = re.compile(rb"[\x20-\x7e\xa0-\xff]{3,}")

    def read(self, paper: Paper) -> str:
        try:
            with olefile.OleFileIO(io.BytesIO(paper.data)) as doc:
                stream = doc.openstream(self._WORD_STREAM).read()
        except Exception as error:
            raise UnreadablePaperError from error
        runs = [run.decode("cp1251", errors="ignore") for run in self._TEXT_RUN.findall(stream)]
        return _checked(" ".join(runs))


class XlsTextReader:
    def read(self, paper: Paper) -> str:
        try:
            book = xlrd.open_workbook(file_contents=paper.data)
            lines = [
                " ".join(str(cell.value) for cell in row if str(cell.value).strip())
                for sheet in book.sheets()
                for row in sheet.get_rows()
            ]
        except Exception as error:
            raise UnreadablePaperError from error
        return _checked("\n".join(line for line in lines if line.strip()))


class XlsxTextReader:
    def read(self, paper: Paper) -> str:
        try:
            book = openpyxl.load_workbook(io.BytesIO(paper.data), read_only=True, data_only=True)
            try:
                lines = [
                    " ".join(str(cell.value) for cell in row if cell.value is not None)
                    for sheet in book.worksheets
                    for row in sheet.iter_rows()
                ]
            finally:
                book.close()
        except Exception as error:
            raise UnreadablePaperError from error
        return _checked("\n".join(line for line in lines if line.strip()))


class PptxTextReader:
    _SLIDE_PREFIX = "ppt/slides/"
    _TEXT_RUN = "{http://schemas.openxmlformats.org/drawingml/2006/main}t"

    def read(self, paper: Paper) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(paper.data)) as deck:
                names = sorted(
                    name
                    for name in deck.namelist()
                    if name.startswith(self._SLIDE_PREFIX) and name.endswith(".xml")
                )
                slides = [deck.read(name) for name in names]
        except Exception as error:
            raise UnreadablePaperError from error
        if not slides:
            raise UnreadablePaperError
        lines: list[str] = []
        for slide in slides:
            try:
                root = ElementTree.fromstring(slide)
            except ElementTree.ParseError as error:
                raise UnreadablePaperError from error
            lines.extend(run.text or "" for run in root.iter(self._TEXT_RUN))
        return _checked("\n".join(lines))


class OdfTextReader:
    _TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
    _CONTENT_XML = "content.xml"

    def read(self, paper: Paper) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(paper.data)) as doc:
                root = ElementTree.fromstring(doc.read(self._CONTENT_XML))
        except Exception as error:
            raise UnreadablePaperError from error
        blocks = (f"{self._TEXT}p", f"{self._TEXT}h")
        lines = ["".join(element.itertext()) for element in root.iter() if element.tag in blocks]
        return _checked("\n".join(lines))


class _TextOnlyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skipped = 0

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in ("script", "style"):
            self._skipped += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skipped = max(0, self._skipped - 1)

    def handle_data(self, data: str) -> None:
        if not self._skipped:
            self.parts.append(data)


class HtmlTextReader:
    def read(self, paper: Paper) -> str:
        parser = _TextOnlyParser()
        try:
            parser.feed(decode_text(paper.data))
        except Exception as error:
            raise UnreadablePaperError from error
        return _checked(" ".join(parser.parts))


class CompositeDocumentReader:
    """Reads any supported document through the reader of its exact media type."""

    def __init__(self, readers: Mapping[str, DocumentReader] | None = None) -> None:
        self._readers = dict(readers) if readers is not None else _default_readers()

    def read(self, paper: Paper) -> str:
        reader = self._readers.get(paper.media_type)
        if reader is None:
            raise UnsupportedPaperError(paper.media_type)
        return reader.read(paper)


def _default_readers() -> dict[str, DocumentReader]:
    return {
        "application/pdf": PdfTextReader(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
            DocxTextReader()
        ),
        "application/msword": DocTextReader(),
        "application/vnd.ms-excel": XlsTextReader(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": XlsxTextReader(),
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": (
            PptxTextReader()
        ),
        "application/vnd.oasis.opendocument.text": OdfTextReader(),
        "application/vnd.oasis.opendocument.spreadsheet": OdfTextReader(),
        "application/vnd.oasis.opendocument.presentation": OdfTextReader(),
        "text/html": HtmlTextReader(),
    }
