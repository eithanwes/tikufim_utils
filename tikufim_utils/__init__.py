import datetime
import warnings

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

OBJECT_ID_DICT = {"by_line": "OfficeLineId", "by_station": "StationId"}

COLUMNS_DICT = {
    "by_line": [
        "OperatorId",
        "operator_nm",
        "ClusterId",
        "cluster_nm",
        "OperatorLineId",
        "OfficeLineId",
        "Direction",
        "hour_a",
        "year_key",
        "month_key",
    ],
    "by_station": [
        "StationId",
        "StationName",
        "LowOrPeakDescFull",
        "year_key",
        "month_key",
    ],
}


def get_day_col_prefix(df):
    # Detect day column prefix
    day_prefix = None
    # Switch-style check for specific day column formats
    if "day_1" in df.columns:
        day_prefix = "day_"
    elif "D1" in df.columns:
        day_prefix = "D"
    elif "1" in df.columns:
        day_prefix = ""
    else:
        # If no day prefix is found, raise an error
        raise ValueError(
            "No day column found in DataFrame. Expected 'day_1', 'D1', or '1'."
        )
    if day_prefix is None:
        raise ValueError(
            "No day column prefix found in DataFrame. Expected 'day_' or 'D'."
        )

    return day_prefix


def get_hourly_counts(df, object_id, start_date, end_date, year, direction=None):
    start_month = datetime.datetime.strptime(start_date, "%Y-%m-%d").month
    end_month = datetime.datetime.strptime(end_date, "%Y-%m-%d").month
    id_col = "StationId" if "StationId" in df.columns else "OfficeLineId"
    period_df = df[
        (df[id_col] == object_id)
        & (df["year_key"] == year)
        & (df["month_key"] >= start_month)
        & (df["month_key"] <= end_month)
    ]

    # Detect day column prefix
    day_prefix = get_day_col_prefix(df)

    counts = []
    datetimes = []
    for month in range(start_month, end_month + 1):
        month_df = period_df[period_df["month_key"] == month]
        if not month_df.empty:
            days_in_month = pd.Timestamp(f"{year}-{month:02d}-01").days_in_month
            for day in range(1, days_in_month + 1):
                day_col = f"{day_prefix}{day}"
                if day_col in month_df.columns:
                    day_date = pd.Timestamp(year=year, month=month, day=day)
                    if not (
                        day_date.date() >= pd.Timestamp(start_date).date()
                        and day_date.date() <= pd.Timestamp(end_date).date()
                    ):
                        continue
                    for hour in sorted(month_df["hour_a"].unique()):
                        hour_rows = month_df[month_df["hour_a"] == hour]
                        count = hour_rows[day_col].sum()
                        counts.append(count)
                        datetimes.append(
                            pd.Timestamp(year=year, month=month, day=day, hour=hour)
                        )
    return counts, datetimes


def get_daily_counts_df(
    df, start_date, end_date, object_id_lst=None, day_of_week_exclude=None
):
    day_col = "day"

    df = df.copy()

    group_category_type = "by_line" if "OfficeLineId" in df.columns else "by_station"

    id_col = OBJECT_ID_DICT[group_category_type]

    if object_id_lst is not None:
        if isinstance(object_id_lst, (int)):
            object_id_lst = [object_id_lst]
        if isinstance(object_id_lst, str):
            object_id_lst = [int(object_id_lst)]
        df = df[df[id_col].isin(object_id_lst)]

    # 1. Define the columns that should remain as they are
    id_vars = COLUMNS_DICT[group_category_type]

    # 2. Use melt to turn day_1, day_2, etc. into rows
    df_long = df.melt(id_vars=id_vars, var_name=day_col, value_name="pax_count")

    # 3. Clean the 'Day' column: change "day_1" to 1 (integer)
    df_long[day_col] = (
        df_long[day_col].str.replace(get_day_col_prefix(df), "").astype(int)
    )

    # Create a proper date column
    df_long["date"] = pd.to_datetime(
        df_long[["year_key", "month_key", day_col]].rename(
            columns={"year_key": "year", "month_key": "month", day_col: "day"}
        ),
        errors="coerce",
    )

    df_long["week_number"] = df_long["date"].dt.isocalendar().week

    # Filter by date range
    df_long = df_long[
        (df_long["date"] >= pd.to_datetime(start_date))
        & (df_long["date"] <= pd.to_datetime(end_date))
    ]

    return df_long


def get_daily_counts(
    df, object_id, start_date, end_date, direction=None, day_of_week_exclude=None
):
    warnings.warn(
        "get_daily_counts is deprecated. Use get_daily_counts_df instead.",
        DeprecationWarning,
    )
    start_month = datetime.datetime.strptime(start_date, "%Y-%m-%d").month
    end_month = datetime.datetime.strptime(end_date, "%Y-%m-%d").month

    start_year = datetime.datetime.strptime(start_date, "%Y-%m-%d").year
    end_year = datetime.datetime.strptime(end_date, "%Y-%m-%d").year

    # Determine which column to use for filtering
    id_col = "StationId" if "StationId" in df.columns else "OfficeLineId"
    if object_id is not None:
        df = df[df[id_col] == object_id]

    day_prefix = get_day_col_prefix(df)

    daily_counts = []
    day_dates = []
    for year in range(start_year, end_year + 1):
        for month in range(start_month, end_month + 1):
            month_df = df[(df["month_key"] == month) & (df["year_key"] == year)]
            if not month_df.empty:
                days_in_month = pd.Timestamp(f"{year}-{month:02d}-01").days_in_month
                for day in range(1, days_in_month + 1):
                    day_col = f"{day_prefix}{day}"
                    if day_col in month_df.columns:
                        day_date = pd.Timestamp(year=year, month=month, day=day).date()
                        if not (
                            day_date >= pd.Timestamp(start_date).date()
                            and day_date <= pd.Timestamp(end_date).date()
                        ):
                            continue
                        if day_of_week_exclude is not None:
                            if (day_date.weekday() + 1) % 7 + 1 in day_of_week_exclude:
                                continue
                        count = month_df[day_col].sum()
                        daily_counts.append(count)
                        day_dates.append(day_date)
    return daily_counts, day_dates


def get_weekly_counts(df, object_id, start_date, end_date, year, direction=None):
    daily_counts, day_dates = get_daily_counts(
        df, object_id, start_date, end_date, year, direction
    )
    week_df = pd.DataFrame({"date": day_dates, "count": daily_counts})
    week_df["week"] = week_df["date"].apply(lambda d: d.isocalendar()[1])
    week_df["year"] = week_df["date"].apply(lambda d: d.isocalendar()[0])
    grouped = (
        week_df.groupby(["year", "week"])
        .agg({"count": "sum", "date": "min"})
        .reset_index()
    )
    weekly_counts = grouped["count"].tolist()
    week_dates = grouped["date"].tolist()
    return weekly_counts, week_dates


def get_monthly_counts(df, object_id, start_date, end_date, year=None, direction=None):
    day_prefix = get_day_col_prefix(df)

    result = df.copy()
    result.fillna(0, inplace=True)
    result.loc[:, "count"] = result.loc[:, f"{day_prefix}1" : f"{day_prefix}31"].sum(
        axis=1
    )

    result.loc[:, "date"] = pd.to_datetime(
        dict(year=result["year_key"], month=result["month_key"], day=1)
    )
    result = result[
        (result["date"] >= pd.to_datetime(start_date))
        & (result["date"] <= pd.to_datetime(end_date))
    ]

    id_col = "StationId" if "StationId" in result.columns else "OfficeLineId"
    if object_id is not None:
        result = result[result[id_col] == object_id]
        result = result.groupby(["date", id_col], as_index=False)["count"].sum()
    else:
        result = result.groupby("date", as_index=False)["count"].sum()
    monthly_counts = result["count"].tolist()
    month_dates = result["date"].tolist()
    return monthly_counts, month_dates


def plot_counts(dates, counts, title="Passenger Counts", xlabel="Date", ylabel="Count"):
    plt.figure(figsize=(20, 10))
    plt.plot(dates, counts, marker="o")
    plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(1))
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%d-%m-%y"))
    plt.gca().tick_params(axis="x", which="minor", length=4, color="gray")
    plt.gca().tick_params(axis="x", which="major", length=8, color="black")
    plt.xticks(rotation=45, ha="right")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_counts_plotly(
    dates,
    counts,
    title="Passenger Counts",
    xlabel="Date",
    ylabel="Count",
    html_file=None,
    show=True,
):
    """Interactive Plotly line plot for counts over time.

    Parameters:
        dates (list-like): x values (datetime/date or strings)
        counts (list-like): y values
        title (str): plot title
        xlabel (str): x-axis label
        ylabel (str): y-axis label
        html_file (str|None): if provided, write the interactive plot to this HTML file
        show (bool): whether to call `fig.show()`

    Returns:
        plotly.graph_objects.Figure
    """

    df = pd.DataFrame({"date": dates, "count": counts})
    fig = px.line(
        df,
        x="date",
        y="count",
        markers=True,
        title=title,
        labels={"date": xlabel, "count": ylabel},
    )
    fig.update_layout(hovermode="x unified")
    if html_file:
        fig.write_html(html_file, include_plotlyjs="cdn")
    if show:
        fig.show()
    return fig
