from typing import Optional, Union


def assert_words_in_message(
    words: Union[str, list[str]],
    message: Union[str, Exception],
    require_same_line: bool = False,
) -> None:
    if isinstance(words, str):
        words = words.split()

    if isinstance(message, Exception):
        message = str(message)

    message_lwr = message.lower()
    words_lwr = [p.lower() for p in words]

    # check for missing words in whole message
    missing = _find_missing_word(words_lwr, message_lwr)
    if missing is not None:
        raise AssertionError(
            f'Missing word "{words[missing]}" in a message:\n\n{message}'
        )

    if require_same_line:
        # additional check that all words must be on the same line
        ok = False
        for line in message_lwr.splitlines():
            missing = _find_missing_word(words_lwr, line)
            if missing is None:
                ok = True
                break

        if not ok:
            raise AssertionError(
                f"Words {words!r} do not appear on the same line in a message:\n\n{message}"
            )


def _find_missing_word(words: list[str], text: str) -> Optional[int]:
    for idx, p in enumerate(words):
        if p not in text:
            return idx
    return None
