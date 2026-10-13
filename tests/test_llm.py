import pytest

from doc_extract import llm


def test_parse_plain_object():
    assert llm.parse_json_block('{"a": 1}') == {"a": 1}


def test_parse_fenced_block():
    reply = 'Here you go:\n```json\n{"vendor": "ACME"}\n```\nThanks!'
    assert llm.parse_json_block(reply) == {"vendor": "ACME"}


def test_parse_object_in_prose():
    reply = 'The result is {"total": 10} as requested.'
    assert llm.parse_json_block(reply) == {"total": 10}


def test_parse_garbage_raises():
    with pytest.raises(llm.LLMError):
        llm.parse_json_block("no json here at all")
