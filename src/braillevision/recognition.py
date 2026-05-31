"""Braille cell recognition tables."""

from __future__ import annotations

from braillevision.segmentation import BrailleCell

Pattern = tuple[int, int, int, int, int, int]


def pattern(*dots: int) -> Pattern:
    bits = [0, 0, 0, 0, 0, 0]
    for dot in dots:
        bits[dot - 1] = 1
    return tuple(bits)


GRADE1: dict[Pattern, str] = {
    pattern(1): "a",
    pattern(1, 2): "b",
    pattern(1, 4): "c",
    pattern(1, 4, 5): "d",
    pattern(1, 5): "e",
    pattern(1, 2, 4): "f",
    pattern(1, 2, 4, 5): "g",
    pattern(1, 2, 5): "h",
    pattern(2, 4): "i",
    pattern(2, 4, 5): "j",
    pattern(1, 3): "k",
    pattern(1, 2, 3): "l",
    pattern(1, 3, 4): "m",
    pattern(1, 3, 4, 5): "n",
    pattern(1, 3, 5): "o",
    pattern(1, 2, 3, 4): "p",
    pattern(1, 2, 3, 4, 5): "q",
    pattern(1, 2, 3, 5): "r",
    pattern(2, 3, 4): "s",
    pattern(2, 3, 4, 5): "t",
    pattern(1, 3, 6): "u",
    pattern(1, 2, 3, 6): "v",
    pattern(2, 4, 5, 6): "w",
    pattern(1, 3, 4, 6): "x",
    pattern(1, 3, 4, 5, 6): "y",
    pattern(1, 3, 5, 6): "z",
    pattern(2): ",",
    pattern(2, 3): ";",
    pattern(2, 5): ":",
    pattern(2, 5, 6): ".",
    pattern(2, 3, 5): "!",
    pattern(2, 3, 6): "?",
    pattern(3): "'",
    pattern(3, 6): "-",
    pattern(): " ",
}

CAPITAL_INDICATOR = pattern(6)
NUMBER_INDICATOR = pattern(3, 4, 5, 6)
NUMBER_MAP = {
    pattern(1): "1",
    pattern(1, 2): "2",
    pattern(1, 4): "3",
    pattern(1, 4, 5): "4",
    pattern(1, 5): "5",
    pattern(1, 2, 4): "6",
    pattern(1, 2, 4, 5): "7",
    pattern(1, 2, 5): "8",
    pattern(2, 4): "9",
    pattern(2, 4, 5): "0",
}

GRADE2_CONTRACTIONS: dict[Pattern, str] = {
    pattern(1, 2): "but",
    pattern(1, 2, 4): "from",
    pattern(1, 2, 4, 5): "go",
    pattern(1, 2, 5): "have",
    pattern(1, 2, 3): "like",
    pattern(1, 3, 4): "more",
    pattern(1, 3, 4, 5): "not",
    pattern(1, 2, 3, 4): "people",
    pattern(1, 2, 3, 4, 5): "quite",
    pattern(1, 2, 3, 5): "rather",
    pattern(2, 3, 4): "so",
    pattern(2, 3, 4, 5): "that",
    pattern(1, 3, 6): "us",
    pattern(1, 2, 3, 6): "very",
    pattern(2, 4, 5, 6): "will",
    pattern(1, 3, 4, 6): "it",
    pattern(1, 3, 4, 5, 6): "you",
    pattern(1, 3, 5, 6): "as",
}


def pattern_for_char(char: str) -> Pattern:
    lower = char.lower()
    for candidate, value in GRADE1.items():
        if value == lower:
            return candidate
    raise KeyError(f"unsupported Braille character: {char!r}")


def cells_to_text(cells: list[BrailleCell], grade2: bool = False) -> str:
    """Convert ordered Braille cells to text."""

    parts: list[str] = []
    cap_next = False
    number_mode = False
    current_row: int | None = None

    for cell in sorted(cells, key=lambda item: (item.row, item.col)):
        if current_row is None:
            current_row = cell.row
        elif cell.row != current_row:
            parts.append("\n")
            current_row = cell.row
            number_mode = False

        pat = tuple(cell.pattern)
        if pat == CAPITAL_INDICATOR:
            cap_next = True
            continue
        if pat == NUMBER_INDICATOR:
            number_mode = True
            continue

        if number_mode and pat in NUMBER_MAP:
            char = NUMBER_MAP[pat]
        elif grade2 and pat in GRADE2_CONTRACTIONS:
            char = GRADE2_CONTRACTIONS[pat]
        else:
            char = GRADE1.get(pat, "?")

        if char in {" ", "\n"}:
            number_mode = False
        if cap_next and char:
            char = char[0].upper() + char[1:]
            cap_next = False
        parts.append(char)

    return "".join(parts)
