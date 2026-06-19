from pathlib import Path

import pandas as pd
import pytest

from tikufim_utils import (
    get_daily_counts,
    get_daily_counts_df,
    get_day_col_prefix,
    get_hourly_counts,
    get_monthly_counts,
)


@pytest.fixture(params=Path("tests/sample_data").glob("tikufim_*.csv"))
def real_sample_df(request):
    """Fixture that runs a test once for every sample file found."""
    return pd.read_csv(request.param)


def _base_line_row(**overrides):
    row = {
        "OperatorId": 1,
        "operator_nm": "op",
        "ClusterId": 10,
        "cluster_nm": "cluster",
        "OperatorLineId": 100,
        "OfficeLineId": 200,
        "Direction": 1,
        "hour_a": 8,
        "year_key": 2024,
        "month_key": 1,
    }
    for day in range(1, 32):
        row[f"day_{day}"] = 0
    row.update(overrides)
    return row


def test_get_day_col_prefix_day_style():
    df = pd.DataFrame({"day_1": [1], "day_2": [2]})
    assert get_day_col_prefix(df) == "day_"


def test_get_day_col_prefix_d_style_real_data(real_sample_df):
    assert get_day_col_prefix(real_sample_df) in ["day_", "D", ""]


def test_get_day_col_prefix_d_style():
    df = pd.DataFrame({"D1": [1], "D2": [2]})
    assert get_day_col_prefix(df) == "D"


def test_get_day_col_prefix_numeric_style():
    df = pd.DataFrame({"1": [1], "2": [2]})
    assert get_day_col_prefix(df) == ""


def test_get_day_col_prefix_missing_raises():
    df = pd.DataFrame({"x": [1]})
    with pytest.raises(ValueError, match="No day column found"):
        get_day_col_prefix(df)


def test_get_daily_counts_filters_object_and_date_range():
    row_a = _base_line_row(day_1=10, day_2=20)
    row_b = _base_line_row(OfficeLineId=999, day_1=100, day_2=200)
    df = pd.DataFrame([row_a, row_b])

    counts, dates = get_daily_counts(
        df=df,
        object_id=200,
        start_date="2024-01-01",
        end_date="2024-01-02",
    )

    assert counts == [10, 20]
    assert [d.isoformat() for d in dates] == ["2024-01-01", "2024-01-02"]


def test_get_daily_counts_with_excluded_weekday():
    row = _base_line_row(day_1=10, day_2=20)
    df = pd.DataFrame([row])

    # API expects 1..7 where 7=Sunday; 2=Monday is excluded here.
    counts, dates = get_daily_counts(
        df=df,
        object_id=200,
        start_date="2024-01-01",
        end_date="2024-01-02",
        day_of_week_exclude=[2],
    )

    assert counts == [20]
    assert [d.isoformat() for d in dates] == ["2024-01-02"]


def test_get_daily_counts_df_returns_long_filtered_rows():
    row = _base_line_row(day_1=11, day_2=22, day_3=33)
    df = pd.DataFrame([row])

    out = get_daily_counts_df(
        df=df,
        start_date="2024-01-02",
        end_date="2024-01-03",
        object_id_lst=[200],
    )

    assert out["pax_count"].tolist() == [22, 33]
    assert out["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-01-02",
        "2024-01-03",
    ]
    assert "week_number" in out.columns


def test_get_hourly_counts_sums_by_hour_and_day():
    row_8 = _base_line_row(hour_a=8, day_1=5, day_2=7)
    row_9 = _base_line_row(hour_a=9, day_1=3, day_2=4)
    df = pd.DataFrame([row_8, row_9])

    counts, datetimes = get_hourly_counts(
        df=df,
        object_id=200,
        start_date="2024-01-01",
        end_date="2024-01-02",
        year=2024,
    )

    assert counts == [5, 3, 7, 4]
    assert [dt.strftime("%Y-%m-%d %H") for dt in datetimes] == [
        "2024-01-01 08",
        "2024-01-01 09",
        "2024-01-02 08",
        "2024-01-02 09",
    ]


def test_get_monthly_counts_aggregates_days_for_object():
    row_jan = _base_line_row(month_key=1, day_1=1, day_2=2)
    row_feb = _base_line_row(month_key=2, day_1=3, day_2=4)
    row_other = _base_line_row(OfficeLineId=999, month_key=1, day_1=50, day_2=50)
    df = pd.DataFrame([row_jan, row_feb, row_other])

    counts, dates = get_monthly_counts(
        df=df,
        object_id=200,
        start_date="2024-01-01",
        end_date="2024-02-28",
    )

    assert counts == [3, 7]
    assert [d.strftime("%Y-%m-%d") for d in dates] == ["2024-01-01", "2024-02-01"]


def test_get_daily_counts_df_returns_only_valid_dates():
    row = _base_line_row(month_key=2, day_1=10, day_2=20, day_31=None)
    df = pd.DataFrame([row])

    out = get_daily_counts_df(
        df=df,
        start_date="2024-01-01",
        end_date="2024-03-01",
    )
    assert out.shape[0] == 29
