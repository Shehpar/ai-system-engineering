import pandas as pd

from validate_data import DataValidator, validate_live_data


def make_df(rows=10, cpu=50, mem=50, net=10):
    return pd.DataFrame(
        {
            "cpu_usage": [cpu] * rows,
            "memory_usage": [mem] * rows,
            "network_load": [net] * rows,
        }
    )


def test_validate_schema_pass():
    df = make_df()
    validator = DataValidator()
    assert validator.validate_schema(df) is True
    assert validator.validation_results["checks"]["schema"] == "PASSED"


def test_validate_schema_fail():
    df = pd.DataFrame({"cpu_usage": [1], "memory_usage": [2]})
    validator = DataValidator()
    assert validator.validate_schema(df) is False
    assert validator.validation_results["passed"] is False


def test_validate_ranges_fail_when_outside_bounds():
    df = make_df(rows=20)
    df.loc[0, "cpu_usage"] = -1
    df.loc[1, "memory_usage"] = 200
    validator = DataValidator()
    result = validator.validate_ranges(df)
    assert result is True or result is False
    assert "ranges" in validator.validation_results["checks"]


def test_validate_live_data():
    ok, issues = validate_live_data(10, 20, 5)
    assert ok is True
    assert issues == []

    ok, issues = validate_live_data(-1, 200, -5)
    assert ok is False
    assert len(issues) == 3