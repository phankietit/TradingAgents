"""Deterministic EN/VI statements for snapshot percentage relationships.

Only the fact ID chooses the subject and denominator. The caller must resolve
and validate its value first. These are observations, never investment advice.
"""

import re

LABELS = {
    "close_10_ema": ("10-day EMA", "EMA 10 ngày"),
    "close_50_sma": ("50-day SMA", "SMA 50 ngày"),
    "close_200_sma": ("200-day SMA", "SMA 200 ngày"),
    "boll": ("middle Bollinger band", "dải giữa Bollinger"),
    "boll_ub": ("upper Bollinger band", "dải trên Bollinger"),
    "boll_lb": ("lower Bollinger band", "dải dưới Bollinger"),
    "atr": ("ATR", "ATR"), "rsi": ("RSI", "RSI"),
    "macd": ("MACD", "MACD"), "macds": ("MACD signal", "đường tín hiệu MACD"),
    "macdh": ("MACD histogram", "histogram MACD"),
}
CANDLES = {"open": ("open", "giá mở cửa"), "high": ("high", "giá cao nhất"),
           "low": ("low", "giá thấp nhất"), "close": ("close", "giá đóng cửa"),
           "volume": ("volume", "khối lượng"),
           "adjusted_close": ("adjusted close", "giá đóng cửa điều chỉnh")}


def is_percentage_fact(fact_id):
    return (fact_id.endswith((".pct", "_pct", ".pct_of_latest_close"))
            or fact_id.startswith(("calc.pct_change(", "calc.abs_pct_change(")))


def _label(fact_id, vi):
    index = int(vi)
    if fact_id.startswith("latest.") and fact_id[7:] in CANDLES:
        label = CANDLES[fact_id[7:]][index]
        return f"{label} gần nhất" if vi else f"latest {label}"
    if fact_id.startswith("indicator.") and fact_id[10:] in LABELS:
        return LABELS[fact_id[10:]][index]
    if fact_id == "observed_window.high":
        return "đỉnh trong khoảng dữ liệu quan sát" if vi else "observed-window high"
    match = re.fullmatch(r"history\.(\d+)\.(candle|indicator)\.([a-z0-9_]+)", fact_id)
    if match:
        row, kind, name = match.groups()
        names = CANDLES if kind == "candle" else LABELS
        if name in names:
            label = names[name][index]
            return f"{label} tại quan sát {row}" if vi else f"{label} at observation {row}"
    match = re.fullmatch(r"window\.(\d+)\.(candle|indicator)\.([a-z0-9_]+)\.(min|max)", fact_id)
    if match:
        count, kind, name, operation = match.groups()
        names = CANDLES if kind == "candle" else LABELS
        if name in names:
            label = names[name][index]
            if vi:
                return f"{label} {'nhỏ nhất' if operation == 'min' else 'lớn nhất'} trong {count} quan sát"
            return f"{'minimum' if operation == 'min' else 'maximum'} {label} over {count} observations"
    raise ValueError("unsupported percentage operand label")


def percentage_statement(fact_id, number, *, vi=False):
    """Render an already-verified, already-rounded value without recomputing it."""
    if not is_percentage_fact(fact_id):
        return None
    value = f"{number}%"
    match = re.fullmatch(r"return\.(\d+)_calendar_days\.pct", fact_id)
    if match:
        days = match[1]
        return (f"Lợi suất giá trong {days} ngày lịch: {value}." if vi
                else f"Price return over {days} calendar days: {value}.")
    if fact_id == "observed_window.latest_close_vs_high_pct":
        return (f"Mức thay đổi từ đỉnh trong khoảng dữ liệu quan sát đến giá đóng cửa gần nhất: {value}." if vi
                else f"Change from the observed-window high to the latest close: {value}.")
    if fact_id == "observed_window.drawdown_magnitude_pct":
        return (f"Giá đóng cửa gần nhất thấp hơn đỉnh trong khoảng dữ liệu quan sát {value}." if vi
                else f"The latest close is {value} below the observed-window high.")
    match = re.fullmatch(r"indicator\.([a-z0-9_]+)\.(pct_of_latest_close|distance_from_latest_close_pct|latest_close_vs_indicator_pct|latest_close_distance_magnitude_pct)", fact_id)
    if match:
        name, relation = match.groups()
        reference = _label(f"indicator.{name}", vi)
        close = _label("latest.close", vi)
        if relation == "pct_of_latest_close":
            return (f"{reference} tính theo tỷ lệ của {close}: {value}." if vi
                    else f"{reference} as a percentage of {close}: {value}.")
        if relation == "distance_from_latest_close_pct":
            subject, baseline = reference, close
        else:
            subject, baseline = close, reference
        absolute = relation == "latest_close_distance_magnitude_pct"
    else:
        match = re.fullmatch(r"calc\.(pct_change|abs_pct_change)\(([a-z0-9_.]+),([a-z0-9_.]+)\)", fact_id)
        if not match:
            raise ValueError("unsupported percentage relation")
        operation, left, right = match.groups()
        subject, baseline = _label(left, vi), _label(right, vi)
        absolute = operation == "abs_pct_change"
    if absolute:
        return (f"Độ chênh lệch tuyệt đối giữa {subject} và {baseline}, lấy {baseline} làm gốc: {value}." if vi
                else f"Absolute percentage difference between {subject} and {baseline}, measured against {baseline}: {value}.")
    return (f"Chênh lệch của {subject} so với {baseline}, lấy {baseline} làm gốc: {value}." if vi
            else f"Percentage difference of {subject} relative to {baseline}, using {baseline} as the baseline: {value}.")
