from flask import Flask, request, jsonify, send_file, render_template
import tempfile
from bond_excel_generator import generate_excel
import os
from typing import Any

app = Flask(__name__, template_folder="templates")
TEMP_DIR = tempfile.gettempdir()

@app.route("/")
def index() -> str:
    """
    Render the main index page.

    Returns:
        str: Rendered HTML for the index page.
    """
    return render_template("index.html")

@app.route("/calculate", methods=["POST"])
def calculate() -> Any:
    """
    Calculate bond investment summary and generate downloadable Excel file.

    Returns:
        Response: JSON containing summary, investment table, and download URL.
    """
    data = request.json
    temp_path = os.path.join(TEMP_DIR, next(tempfile._get_candidate_names()) + ".xlsx")
    
    buy_price, sell_price, summary = generate_excel(
        issue_date=data["issue_date"],
        maturity_date=data["maturity_date"],
        face_value=data["face_value"],
        coupon_rate=data["coupon_rate"],
        frequency=int(data["frequency"]),
        bought_date=data["bought_date"],
        sold_date=data["sold_date"],
        rate=data["rate"],
        quantity=data["quantity"],
        client_type=data["client_type"],
        filepath=temp_path,
        discount_method=data["discount_method"],
        discount_input=data["discount_input"],
        product_type=data["product_type"],
        trading_fee=data["trading_fee"],
        apply_trading_fee=data["apply_trading_fee"]
    )

    return jsonify({
        "summary": summary,
        "investment_table": summary.get("investment_table", []),
        "download_url": f"/download/{os.path.basename(temp_path)}"
    })

@app.route("/download/<filename>")
def download(filename: str) -> Any:
    """
    Send a generated Excel file to the client for download.

    Args:
        filename (str): The name of the file to be downloaded.

    Returns:
        Response: File download response.
    """
    return send_file(os.path.join(TEMP_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
