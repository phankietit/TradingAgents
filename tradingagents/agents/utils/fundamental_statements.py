"""Code-owned SEC observations: metric, period and units are not model prose.

Values must already have been resolved from the immutable source and rounded.
These sentences describe reported accounting facts, never company valuation.
"""

import re
from datetime import date

METRICS = {
    "total_assets": ("Total assets", "Tổng tài sản", True),
    "current_assets": ("Current assets", "Tài sản ngắn hạn", True),
    "cash_and_equivalents": ("Cash and equivalents", "Tiền và tương đương tiền", True),
    "total_liabilities": ("Total liabilities", "Tổng nợ phải trả", True),
    "current_liabilities": ("Current liabilities", "Nợ ngắn hạn", True),
    "stockholders_equity": ("Stockholders' equity", "Vốn chủ sở hữu", True),
    "revenue": ("Revenue", "Doanh thu", False),
    "cost_of_revenue": ("Cost of revenue", "Giá vốn doanh thu", False),
    "gross_profit": ("Gross profit", "Lợi nhuận gộp", False),
    "operating_income": ("Operating income", "Lợi nhuận hoạt động", False),
    "net_income": ("Net income", "Lợi nhuận ròng", False),
    "diluted_eps": ("Diluted EPS", "Lợi nhuận trên mỗi cổ phiếu pha loãng", False),
    "operating_cash_flow": ("Operating cash flow", "Dòng tiền từ hoạt động kinh doanh", False),
    "investing_cash_flow": ("Investing cash flow", "Dòng tiền từ hoạt động đầu tư", False),
    "financing_cash_flow": ("Financing cash flow", "Dòng tiền từ hoạt động tài chính", False),
    "capital_expenditure": ("Capital expenditure", "Chi tiêu vốn", False),
}


def is_fundamental_fact(fact_id):
    return fact_id.startswith("sec.")


def fundamental_statement(fact_id, number, *, vi=False):
    """Render exact supported metric/unit/period; fail closed on unknown IDs."""
    if not is_fundamental_fact(fact_id):
        return None
    match = re.fullmatch(
        r"sec\.([a-z_]+)\.(annual|quarterly)\.(\d{4}-\d{2}-\d{2})\.(usd_millions|usd_per_share)",
        fact_id,
    )
    if not match:
        raise ValueError("unsupported SEC statement")
    metric, frequency, end, unit = match.groups()
    date.fromisoformat(end)
    if metric not in METRICS or unit != ("usd_per_share" if metric == "diluted_eps" else "usd_millions"):
        raise ValueError("unsupported SEC metric/unit")
    en, vn, balance = METRICS[metric]
    if vi:
        period = "năm" if frequency == "annual" else "quý"
        when = f"tại ngày {end}, theo báo cáo {period}" if balance else f"trong kỳ {period} kết thúc ngày {end}"
        amount = f"{number} triệu USD" if unit == "usd_millions" else f"{number} USD/cổ phiếu"
        return f"{vn} {when}: {amount}."
    when = (f"as of {end}, reported in the {frequency} filing" if balance
            else f"for the {frequency} period ended {end}")
    amount = f"USD {number} million" if unit == "usd_millions" else f"USD {number} per share"
    return f"{en} {when}: {amount}."
