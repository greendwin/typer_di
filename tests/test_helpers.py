import pytest

from .helpers import assert_words_in_message


def test_assert_on_missing_word():
    with pytest.raises(AssertionError, match='Missing word "bubu"'):
        assert_words_in_message("bubu", "there is no booboo")


def test_assert_match_ignore_case():
    assert_words_in_message("bubu", "there is no BubU")
    assert_words_in_message("bubu", "there is no BUBU")
    assert_words_in_message("BUBU", "there is no bubu")


def test_assert_ignore_order():
    assert_words_in_message("foo bar zoo", "foo zoo bar")
    assert_words_in_message("foo bar zoo", "bar foo zoo")
    assert_words_in_message("foo bar zoo", "zoo bar foo")


def test_check_same_line():
    with pytest.raises(AssertionError, match=r"foo(.*)bar(.*)same line"):
        assert_words_in_message(
            "foo bar",
            """
                foo on one line
                and bar on another
            """,
            require_same_line=True,
        )
