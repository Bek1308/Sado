import pytest

from sado.infrastructure.languages.rules import RulePipelineNormalizer, plain_number_rule

_WORDS = {0: "zero", 2: "two", 5: "five", 15: "fifteen", 15_000: "fifteen-thousand"}


@pytest.mark.parametrize(
    ("text", "spoken"),
    [
        ("I have 2 cats", "I have two cats"),
        ("Price: 15 000", "Price: fifteen-thousand"),
        ("Rate 2.5", "Rate two point five"),
        ("Rate 2,05", "Rate two point zero five"),
        ("Growth 15%", "Growth fifteen percent"),
    ],
)
def test_plain_number_rule_spells_numbers(text: str, spoken: str) -> None:
    rule = plain_number_rule(_WORDS.__getitem__, decimal_word="point", percent_word="percent")

    assert rule(text) == spoken


def test_pipeline_applies_rules_in_order() -> None:
    normalizer = RulePipelineNormalizer(rules=(str.upper, lambda text: text + "!"))

    assert normalizer.normalize("salom") == "SALOM!"
