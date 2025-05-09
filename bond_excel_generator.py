def generate_excel(bought_date, sold_date, quantity, client_type, rate, filepath):
    import pandas as pd
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.utils import quote_sheetname
    from openpyxl.styles import Font
    from datetime import datetime, timedelta

    bond_par = 100000
    coupon_rate = 0.105
    coupon_dates = [datetime(2022, 6, 9), datetime(2023, 6, 9), datetime(2024, 6, 9)]
    issue_date = datetime(2021, 6, 9)

    bought_dt = datetime.strptime(bought_date, "%Y-%m-%d")
    sold_dt = datetime.strptime(sold_date, "%Y-%m-%d")

    cashflows = []
    for i, cd in enumerate(coupon_dates):
        ex_cd = cd - timedelta(days=10)
        prev_cd = issue_date if i == 0 else coupon_dates[i-1]
        year_frac = (cd - prev_cd).days / 365
        cf = bond_par * coupon_rate * year_frac
        if i == len(coupon_dates) - 1:
            cf += bond_par
        cashflows.append([cd.date(), ex_cd.date(), "10.5%", round(cf, 4)])

    cf_df = pd.DataFrame(cashflows, columns=["Coupon Date", "Ex-Coupon Date", "Coupon Rate", "Cashflow"])

    wb = Workbook()
    ws_cf = wb.active
    ws_cf.title = "Cash Flow Table"
    for r in dataframe_to_rows(cf_df, index=False, header=True):
        ws_cf.append(r)
    for cell in ws_cf[1]: cell.font = Font(bold=True)

    ws_input = wb.create_sheet("User Input")
    ws_input.append(["Bought Date", "Sold Date", "Quantities", "Client Type", "Rate"])
    ws_input.append([bought_date, sold_date, quantity, client_type, rate])

    ws_tax = wb.create_sheet("Tax Table")
    ws_tax.append(["Client Type", "Coupon Tax", "Transaction Tax"])
    ws_tax.append(["Individual", 0.05, 0.001])
    ws_tax.append(["Corporation", 0.0, 0.0])

    ws_pv = wb.create_sheet("PV Table")
    ws_pv.append(["Coupon Date", "Ex-Coupon Date", "Coupon Rate", "Cashflow", "Year Frac", "Discount Factor", "Present Value"])
    for cell in ws_pv[1]: cell.font = Font(bold=True)

    cf_sheet = quote_sheetname("Cash Flow Table")
    input_sheet = quote_sheetname("User Input")

    for i in range(3):
        row = i + 2
        ws_pv[f"A{row}"].value = f"={cf_sheet}!A{row}"
        ws_pv[f"B{row}"].value = f"={cf_sheet}!B{row}"
        ws_pv[f"C{row}"].value = f"={cf_sheet}!C{row}"
        ws_pv[f"D{row}"].value = f"={cf_sheet}!D{row}"
        ws_pv[f"E{row}"].value = f"=(A{row}-{input_sheet}!A2)/365"
        ws_pv[f"F{row}"].value = f"=1/(1+C{row}-0.2%)^E{row}"
        ws_pv[f"G{row}"].value = f"=D{row}*F{row}"

    ws_summary = wb.create_sheet("Summary")
    ws_summary["A1"] = "Buy Price"
    ws_summary["A2"] = "=SUM('PV Table'!G2:G4)"
    ws_summary["B1"] = "Cash Flow Receivable"
    ws_summary["B2"] = "=SUMPRODUCT(('Cash Flow Table'!B2:B4>=--'User Input'!A2)*('Cash Flow Table'!B2:B4<=--'User Input'!B2)*('Cash Flow Table'!D2:D4)*(1-IF('User Input'!D2=\"Individual\",0.05,0)))"

    ws_summary["C1"] = "Transaction Tax Rate"
    ws_summary["C2"] = "=IF('User Input'!D2=\"Individual\",0.001,0)"
    ws_summary["D1"] = "Sell Price"
    ws_summary["D2"] = "=(A2 * (100%+'User Input'!E2*('User Input'!B2-'User Input'!A2)/365)-B2)/(1-C2)"
    for cell in ws_summary["1:1"]: cell.font = Font(bold=True)

    wb.save(filepath)

    buy_price = sum([cf[3] / ((1 + coupon_rate + 0.02) ** ((cd - bought_dt).days / 365)) for cf, cd in zip(cashflows, coupon_dates)])
    sell_price = (buy_price * (1 + rate * (sold_dt - bought_dt).days / 365)) / (1 - (0.001 if client_type == "Individual" else 0))
    return buy_price, sell_price
