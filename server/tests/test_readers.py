"""Samples are built by hand so the suite needs no fixture binaries besides one .xls."""

import io
import struct
import zipfile
from pathlib import Path

import openpyxl
import pytest
from pypdf import PdfWriter

from sado.domain.errors import UnreadablePaperError, UnsupportedPaperError
from sado.domain.vision import Paper
from sado.infrastructure.documents.readers import CompositeDocumentReader

_PDF = "application/pdf"
_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_DOC = "application/msword"
_XLS = "application/vnd.ms-excel"
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
_ODT = "application/vnd.oasis.opendocument.text"


def sample_pdf_bytes(text: str = "Permit 42 expires soon") -> bytes:
    content = f"BT /F1 12 Tf 10 180 Td ({text}) Tj ET".encode()
    objects = [
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n",
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n",
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R"
        b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n",
        b"4 0 obj<</Length "
        + str(len(content)).encode()
        + b">>stream\n"
        + content
        + b"\nendstream\nendobj\n",
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj
    xref_at = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += (
        f"trailer\n<</Size {len(objects) + 1}/Root 1 0 R>>\n".encode()
        + f"startxref\n{xref_at}\n".encode()
        + b"%%EOF\n"
    )
    return pdf


def _zipped(path: str, xml: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr(path, xml)
    return buf.getvalue()


def sample_docx_bytes() -> bytes:
    return _zipped(
        "word/document.xml",
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Permit 42</w:t></w:r></w:p>"
        "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>expires soon</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
        "</w:body></w:document>",
    )


def sample_pptx_bytes() -> bytes:
    return _zipped(
        "ppt/slides/slide1.xml",
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
        ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        "<a:p><a:r><a:t>Quarterly results</a:t></a:r></a:p></p:sld>",
    )


def sample_odt_bytes() -> bytes:
    return _zipped(
        "content.xml",
        "<office:document-content"
        ' xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
        ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
        "<text:p>Permit 42 expires soon</text:p></office:document-content>",
    )


def sample_doc_bytes(text: str = "Salom dunyo, ruxsatnoma 42") -> bytes:
    """Minimal OLE2 file; olefile itself cannot create one, so it is built by hand."""
    stream = text.encode("cp1251") + bytes(5000 - len(text.encode("cp1251")))
    sectors = [stream[i : i + 512].ljust(512, b"\x00") for i in range(0, len(stream), 512)]
    header = bytearray(512)
    header[0:8] = bytes.fromhex("D0CF11E0A1B11AE1")
    struct.pack_into("<H", header, 24, 0x3E)
    struct.pack_into("<H", header, 26, 0x03)
    struct.pack_into("<H", header, 28, 0xFFFE)
    struct.pack_into("<H", header, 30, 9)
    struct.pack_into("<H", header, 32, 6)
    struct.pack_into("<I", header, 44, 1)
    struct.pack_into("<i", header, 48, 1)
    struct.pack_into("<I", header, 56, 0)
    struct.pack_into("<I", header, 60, 0xFFFFFFFF)
    struct.pack_into("<I", header, 68, 0xFFFFFFFF)
    struct.pack_into("<I", header, 76, 0)
    for i in range(1, 109):
        struct.pack_into("<I", header, 76 + i * 4, 0xFFFFFFFF)
    fat = bytearray(512)
    struct.pack_into("<I", fat, 0, 0xFFFFFFFD)
    struct.pack_into("<I", fat, 4, 0xFFFFFFFE)
    for index in range(len(sectors)):
        nxt = 0xFFFFFFFE if index == len(sectors) - 1 else 2 + index + 1
        struct.pack_into("<I", fat, (2 + index) * 4, nxt)
    for i in range(2 + len(sectors), 128):
        struct.pack_into("<I", fat, i * 4, 0xFFFFFFFF)
    directory = (
        _dir_entry("Root Entry", 5, 0xFFFFFFFE, 0, child=1)
        + _dir_entry("WordDocument", 2, 2, len(stream))
        + bytes(128)
        + bytes(128)
    )
    return bytes(header) + bytes(fat) + directory + b"".join(sectors)


def _dir_entry(name: str, obj_type: int, start: int, size: int, child: int = -1) -> bytes:
    entry = bytearray(128)
    raw = name.encode("utf-16-le")
    entry[0 : len(raw)] = raw
    struct.pack_into("<H", entry, 64, len(raw) + 2)
    entry[66] = obj_type
    entry[67] = 1
    struct.pack_into("<iii", entry, 68, -1, -1, child)
    struct.pack_into("<I", entry, 116, start)
    struct.pack_into("<q", entry, 120, size)
    return bytes(entry)


def sample_xlsx_bytes() -> bytes:
    book = openpyxl.Workbook()
    sheet = book.active
    sheet["A1"] = "Item"
    sheet["B1"] = "Price"
    sheet["A2"] = "Bread"
    sheet["B2"] = 12000
    buf = io.BytesIO()
    book.save(buf)
    return buf.getvalue()


def sample_xls_bytes() -> bytes:
    # Generated once with xlwt; kept as a file because nothing installed writes .xls.
    return (Path(__file__).parent / "fixtures" / "permit.xls").read_bytes()


def _read(data: bytes, media_type: str) -> str:
    return CompositeDocumentReader().read(Paper(data=data, media_type=media_type))


def test_reads_a_pdf() -> None:
    assert _read(sample_pdf_bytes(), _PDF) == "Permit 42 expires soon"


def test_reads_a_word_file() -> None:
    assert _read(sample_docx_bytes(), _DOCX) == "Permit 42\nexpires soon"


def test_reads_a_legacy_word_file() -> None:
    assert "Salom dunyo, ruxsatnoma 42" in _read(sample_doc_bytes(), _DOC)


def test_reads_a_spreadsheet() -> None:
    assert _read(sample_xls_bytes(), _XLS) == "Item Price\nBread 12000.0"


def test_reads_a_modern_spreadsheet() -> None:
    assert _read(sample_xlsx_bytes(), _XLSX) == "Item Price\nBread 12000"


def test_reads_a_presentation() -> None:
    assert _read(sample_pptx_bytes(), _PPTX) == "Quarterly results"


def test_reads_an_opendocument_file() -> None:
    assert _read(sample_odt_bytes(), _ODT) == "Permit 42 expires soon"


def test_reads_a_web_page_without_scripts() -> None:
    html = b"<h1>Notice</h1><p>Permit <b>42</b></p><script>evil()</script>"

    text = _read(html, "text/html")

    assert "Permit" in text and "42" in text
    assert "evil" not in text


def test_rejects_a_type_without_a_reader() -> None:
    with pytest.raises(UnsupportedPaperError):
        _read(b"data", "application/zip")


def test_rejects_a_pdf_without_readable_text() -> None:
    buf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(buf)

    with pytest.raises(UnreadablePaperError):
        _read(buf.getvalue(), _PDF)


def test_rejects_a_broken_office_file() -> None:
    with pytest.raises(UnreadablePaperError):
        _read(b"not a zip file", _DOCX)
