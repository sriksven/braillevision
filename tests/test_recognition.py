from braillevision.recognition import CAPITAL_INDICATOR, GRADE1, cells_to_text, pattern
from braillevision.segmentation import BrailleCell


def cell(pat, col=0):
    return BrailleCell(row=0, col=col, pattern=pat, center_x=0, center_y=0)


def test_all_letters_decode():
    letters = "abcdefghijklmnopqrstuvwxyz"
    reverse = {value: pat for pat, value in GRADE1.items()}
    cells = [cell(reverse[letter], col=i) for i, letter in enumerate(letters)]
    assert cells_to_text(cells) == letters


def test_capital_indicator_uppercases_next_cell():
    assert cells_to_text([cell(CAPITAL_INDICATOR, 0), cell(pattern(1), 1)]) == "A"


def test_number_indicator_switches_number_mode():
    assert (
        cells_to_text(
            [cell(pattern(3, 4, 5, 6), 0), cell(pattern(1), 1), cell(pattern(1, 2), 2)]
        )
        == "12"
    )


def test_unknown_pattern_returns_question_mark():
    assert cells_to_text([cell(pattern(4, 6))]) == "?"


def test_grade2_contractions_are_available():
    assert cells_to_text([cell(pattern(1, 3, 4, 5, 6))], grade2=True) == "you"
