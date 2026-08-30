"""
Unit tests for review/frontmatter.py parsing and serialization.
"""
import pytest

from src.app.review.errors import ValidationError
from src.app.review.frontmatter import parse_frontmatter, serialize_frontmatter


def test_parse_frontmatter_roundtrip():
    frontmatter = {"id": "x-1", "domain": "PERSONAL", "nested": {"a": 1, "b": 2}}
    body = "Some body text."
    raw = serialize_frontmatter(frontmatter, body)

    parsed_frontmatter, parsed_body = parse_frontmatter(raw)

    assert parsed_frontmatter == frontmatter
    assert parsed_body == body


def test_parse_frontmatter_missing_opening_delimiter_raises():
    with pytest.raises(ValidationError):
        parse_frontmatter("id: x-1\n---\n\nbody")


def test_parse_frontmatter_missing_closing_delimiter_raises():
    with pytest.raises(ValidationError):
        parse_frontmatter("---\nid: x-1\n\nbody")


def test_parse_frontmatter_invalid_yaml_raises():
    with pytest.raises(ValidationError):
        parse_frontmatter("---\nid: [unclosed\n---\n\nbody")


def test_parse_frontmatter_non_mapping_raises():
    with pytest.raises(ValidationError):
        parse_frontmatter("---\n- a\n- b\n---\n\nbody")


def test_parse_frontmatter_empty_frontmatter_becomes_empty_dict():
    frontmatter, body = parse_frontmatter("---\n---\n\nbody")

    assert frontmatter == {}
    assert body == "body"


def test_parse_frontmatter_preserves_unknown_fields():
    frontmatter = {"id": "x-1", "some_future_field": "kept"}
    raw = serialize_frontmatter(frontmatter, "body")

    parsed_frontmatter, _ = parse_frontmatter(raw)

    assert parsed_frontmatter["some_future_field"] == "kept"


def test_serialize_frontmatter_matches_expected_framing():
    raw = serialize_frontmatter({"id": "x-1"}, "body text")

    assert raw.startswith("---\n")
    assert "---\n\nbody text" in raw
