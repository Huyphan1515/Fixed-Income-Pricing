from flask import Flask, request, jsonify, send_file, render_template
import tempfile
from bond_excel_generator import generate_excel
import os
from typing import Any

# --- PATCH START: Safe float helper ---
def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
# --- PATCH END ---

app = Flask(__name__, template_folder="templates")
TEMP_DIR = tempfile.gettempdir()

@app.route("/")
def index() -> str:
    return render_template("index.html")

@app.route("/calculate", methods=["POST"])
def calculate() -> Any:
    data = request.json
    temp_path = os.path.join(TEMP_DIR, next(tempfile._get_candidate_names()) + ".xlsx")
    bond_type = data.get("bond_type", "fixed")
    num_periods = int(data.get("num_periods", 0))
    coupon_rates = data.get("coupon_rates", [])
    discount_rate = safe_float(data.get("discount_rate", 0))

    # For backward compatibility with original form:
    coupon_rate = safe_float(data.get("coupon_rate", 0))
    frequency = int(data.get("frequency", 1))

    buy_price, sell_price, summary = generate_excel(
        bond_type=bond_type,
        issue_date=data["issue_date"],
        maturity_date=data["maturity_date"],
        face_value=safe_float(data["face_value"], 0),
        bought_date=data["bought_date"],
        sold_date=data["sold_date"],
        quantity=int(data["quantity"]),
        client_type=data["client_type"],
        product_type=data["product_type"],
        trading_fee=safe_float(data["trading_fee"], 0),
        apply_trading_fee=bool(data["apply_trading_fee"]),
        num_periods=num_periods,
        coupon_rates=coupon_rates,
        discount_rate=discount_rate,
        coupon_rate=coupon_rate,
        frequency=frequency,
        filepath=temp_path
    )

    return jsonify({
        "summary": summary,
        "investment_table": summary.get("investment_table", []),
        "download_url": f"/download/{os.path.basename(temp_path)}"
    })

@app.route("/download/<filename>")
def download(filename: str) -> Any:
    return send_file(os.path.join(TEMP_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
