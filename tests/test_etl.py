import pandas as pd

import etl
import make_sample


def _df(rows):
    return pd.DataFrame(rows, columns=etl.COLUMNS)


GOOD = ["Norte", "Division Alfa", "Territorio-Uno", "Alpha", "AA", "10"]


def _with(**changes):
    row = dict(zip(etl.COLUMNS, GOOD))
    row.update(changes)
    return _df([list(row.values())])


def test_valid_row_passes_everything():
    out = etl.validate(_with())
    assert (out[etl.CHECKS] == "PASS").all().all()


def test_empty_cell_fails():
    out = etl.validate(_with(Division="  "))
    assert out.loc[0, "Empty_Check"] == "FAIL"
    assert out.loc[0, "Format_Check"] == "PASS"


def test_invalid_formats_fail():
    for col, bad in [("SAP_code", "Golf1"), ("abreviation", "aa"), ("abreviation", "AAA"),
                     ("#Poles", "-5"), ("#Poles", "abc"), ("Region", "Norte 9")]:
        assert etl.validate(_with(**{col: bad})).loc[0, "Format_Check"] == "FAIL", (col, bad)


def test_special_chars_fail():
    out = etl.validate(_with(Region="Norte@"))
    assert out.loc[0, "SpecialChars_Check"] == "FAIL"


def test_duplicates_first_passes_rest_fail():
    out = etl.validate(_df([GOOD, GOOD, GOOD]))
    assert list(out["Duplicate_Check"]) == ["PASS", "FAIL", "FAIL"]


def test_end_to_end_sample(tmp_path):
    src = make_sample.main(tmp_path / "in" / "input.xlsx")
    valid_path, invalid_path = etl.run(src.parent, tmp_path / "out")
    valid = pd.read_excel(valid_path, dtype=str)
    invalid = pd.read_excel(invalid_path, dtype=str)
    assert list(valid.columns) == etl.COLUMNS
    assert len(valid) + len(invalid) == len(make_sample.ROWS)
    for check in etl.CHECKS:
        assert "FAIL" in set(invalid[check])
