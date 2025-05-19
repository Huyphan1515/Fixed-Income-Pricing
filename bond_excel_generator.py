import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import quote_sheetname
from openpyxl.styles import Font
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Tuple, Dict, Any

def get_coupon_schedule(
    issue_date: datetime,
    maturity_date: datetime,
    face_value: float,
    coupon_rate: float,
    frequency: int
) -> Tuple[List[datetime], List[List[Any]]]:
    """
    Generate a schedule of coupon dates and corresponding cashflows for a bond.

    Args:
        issue_date (datetime): The bond's issue date.
        maturity_date (datetime): The bond's maturity date.
        face_value (float): The nominal value of the bond.
        coupon_rate (float): Coupon rate, as a percentage.
        frequency (int): Number of coupon payments per year.

    Returns:
        Tuple[List[datetime], List[List[Any]]]: 
            - List of coupon dates (as datetime objects).
            - List of cashflow details, each entry is [coupon_date, ex_coupon_date, coupon_rate_string, cashflow_amount].
    """
    coupon_dates: List[datetime] = []
    cashflows: List[List[Any]] = []

    temp_date = issue_date
    while True:
        next_date = temp_date + relativedelta(months=12 // frequency)
        if next_date > maturity_date:
            break
        coupon_dates.append(next_date)
        temp_date = next_date

    for i, cd in enumerate(coupon_dates):
        ex_cd = cd - timedelta(days=10)
        prev_cd = issue_date if i == 0 else coupon_dates[i - 1]
        year_frac = (cd - prev_cd).days / 365
        cf = face_value * (coupon_rate / 100) * year_frac
        if i == len(coupon_dates) - 1:
            cf += face_value
        cashflows.append([cd.date(), ex_cd.date(), f"{coupon_rate}%", round(cf, 4)])

    return coupon_dates, cashflows

def generate_excel(
    issue_date: str,
    maturity_date: str,
    face_value: float,
    coupon_rate: float,
    frequency: int,
    bought_date: str,
    sold_date: str,
    rate: float,
    quantity: int,
    client_type: str,
    filepath: str,
    discount_method: str,
    discount_input: float,
    product_type: str,
    trading_fee: float,
    apply_trading_fee: bool
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Generates an Excel report for a bond investment and returns investment summary.

    Args:
        issue_date (str): Bond issue date in YYYY-MM-DD format.
        maturity_date (str): Bond maturity date in YYYY-MM-DD format.
        face_value (float): Bond face value.
        coupon_rate (float): Annual coupon rate as a percentage.
        frequency (int): Number of coupon payments per year.
        bought_date (str): Date of purchase in YYYY-MM-DD format.
        sold_date (str): Date of sale in YYYY-MM-DD format.
        rate (float): Repo or discount rate as a percentage.
        quantity (int): Number of bonds.
        client_type (str): 'Individual' or 'Corporation'.
        filepath (str): Filepath to save the Excel file.
        discount_method (str): Method to determine discount rate ('coupon', 'spread', 'fixed').
        discount_input (float): Input for spread or fixed rate calculation.
        product_type (str): 'Outright' or 'Repo'.
        trading_fee (float): Trading fee as a percentage.
        apply_trading_fee (bool): Whether to apply trading fee.

    Returns:
        Tuple[float, float, Dict[str, Any]]:
            - Total buy price for all bonds.
            - Total sell price for all bonds.
            - Investment summary dictionary with details.
    
    Raises:
        ValueError: If date parsing fails.
        IOError: If saving the Excel file fails.
    """
    try:
        issue_date_dt: datetime = datetime.strptime(issue_date, "%Y-%m-%d")
        maturity_date_dt: datetime = datetime.strptime(maturity_date, "%Y-%m-%d")
        bought_dt: datetime = datetime.strptime(bought_date, "%Y-%m-%d")
        sold_dt: datetime = datetime.strptime(sold_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")

    coupon_dates, cashflows = get_coupon_schedule(
        issue_date_dt, maturity_date_dt, face_value, coupon_rate, frequency
    )

    cf_df = pd.DataFrame(cashflows, columns=["Coupon Date", "Ex-Coupon Date", "Coupon Rate", "Cashflow"])

    wb = Workbook()
    ws_cf = wb.active
    ws_cf.title = "Cash Flow Table"
    for r in dataframe_to_rows(cf_df, index=False, header=True):
        ws_cf.append(r)
    for cell in ws_cf[1]:
        cell.font = Font(bold=True)

    ws_input = wb.create_sheet("User Input")
    ws_input.append(["Bought Date", "Sold Date", "Quantities", "Client Type", "Rate", "Trading Fee"])
    ws_input.append([bought_date, sold_date, quantity, client_type, rate / 100, trading_fee / 100])

    ws_tax = wb.create_sheet("Tax Table")
    ws_tax.append(["Client Type", "Coupon Tax", "Transaction Tax"])
    ws_tax.append(["Individual", 0.05, 0.001])
    ws_tax.append(["Corporation", 0.0, 0.0])

    ws_pv = wb.create_sheet("PV Table")
    ws_pv.append(["Coupon Date", "Ex-Coupon Date", "Coupon Rate", "Cashflow", "Year Frac", "Discount Factor", "Present Value"])
    for cell in ws_pv[1]:
        cell.font = Font(bold=True)

    cf_sheet = quote_sheetname("Cash Flow Table")
    input_sheet = quote_sheetname("User Input")

    # Determine discount rate based on user choice
    if discount_method == "coupon":
        discount_rate: float = coupon_rate / 100
    elif discount_method == "spread":
        discount_rate = (coupon_rate + discount_input) / 100
    else:
        discount_rate = discount_input / 100

    for i in range(len(coupon_dates)):
        row = i + 2
        ws_pv[f"A{row}"].value = f"={cf_sheet}!A{row}"
        ws_pv[f"B{row}"].value = f"={cf_sheet}!B{row}"
        ws_pv[f"C{row}"].value = f"={cf_sheet}!C{row}"
        ws_pv[f"D{row}"].value = f"={cf_sheet}!D{row}"
        ws_pv[f"E{row}"].value = f"=(A{row}-{input_sheet}!A2)/365"
        ws_pv[f"F{row}"].value = f"=1/(1+{discount_rate})^E{row}"
        ws_pv[f"G{row}"].value = f"=D{row}*F{row}"

    # Calculate backend summary
    txn_tax: float = 0.001 if client_type == "Individual" else 0.0
    coupon_tax: float = 0.05 if client_type == "Individual" else 0.0
    rate_decimal: float = rate / 100
    trading_fee_decimal: float = trading_fee / 100

    received_cashflows: List[List[Any]] = [cf for cf, cd in zip(cashflows, coupon_dates) if bought_dt <= cd <= sold_dt]
    total_coupon_received: float = sum(cf[3] * (1 - coupon_tax) for cf in received_cashflows)

    buy_price: float = sum([
        cf[3] / ((1 + discount_rate) ** ((cd - bought_dt).days / 365))
        for cf, cd in zip(cashflows, coupon_dates)
    ])

    if product_type == "Outright":
        sell_price: float = sum([
            cf[3] / ((1 + discount_rate) ** ((cd - sold_dt).days / 365))*(1 - txn_tax - trading_fee_decimal)
            for cf, cd in zip(cashflows, coupon_dates) if cd > sold_dt
        ])
    else:
        sell_price = (buy_price * (1 + rate_decimal * (sold_dt - bought_dt).days / 365) - total_coupon_received) / (1 - txn_tax - trading_fee_decimal)

    # Write investment summary
    ws_summary = wb.create_sheet("Investment Summary")
    ws_summary.append(["Buy Price", round(buy_price* (1 + trading_fee_decimal), 4)])
    ws_summary.append(["Transaction Tax Rate", txn_tax])
    ws_summary.append(["Trading Fee", trading_fee_decimal])
    ws_summary.append(["Total Coupon Received", round(total_coupon_received* (1 - coupon_tax), 4)])
    ws_summary.append(["Sell Price", round(sell_price* (1 - txn_tax), 4)])
    for cell in ws_summary[1]: cell.font = Font(bold=True)

    # Write investment table
    ws_table = wb.create_sheet("Investment Table")
    ws_table.append(["Date", "Event", "Net Amount Per Bond"])
    ws_table.append([bought_date, "Buy Bond", round(buy_price * (1 + trading_fee_decimal), 4)])
    for cf, cd in zip(cashflows, coupon_dates):
        if bought_dt <= cd <= sold_dt:
            ws_table.append([cd.date(), "Coupon Received", round(cf[3] * (1 - coupon_tax), 4)])
    ws_table.append([sold_date, "Sell Bond", round(sell_price * (1 - txn_tax), 4)])
    for cell in ws_table[1]: cell.font = Font(bold=True)

    try:
        wb.save(filepath)
    except Exception as e:
        raise IOError(f"Error saving Excel file: {e}")

    summary: Dict[str, Any] = {
        "buy_price": round(buy_price * quantity, 4),
        "sell_price": round(sell_price * quantity*(1-txn_tax), 4),
        "coupon_received": round(total_coupon_received * quantity, 4),
        "txn_tax": txn_tax,
        "trading_fee": trading_fee_decimal,
        "investment_table": [
            {"date": bought_date, "event": "Buy Bond", "amount": round(buy_price * (1 + trading_fee_decimal), 4)},
            *[
                {"date": str(cf[0]), "event": "Coupon Received", "amount": round(cf[3] * (1 - coupon_tax), 4)}
                for cf, cd in zip(cashflows, coupon_dates) if bought_dt <= cd <= sold_dt
            ],
            {"date": sold_date, "event": "Sell Bond", "amount": round(sell_price * (1 - txn_tax), 4)}
        ]
    }
    return buy_price * quantity, sell_price * quantity, summary
