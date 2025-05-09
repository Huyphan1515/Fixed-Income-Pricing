from flask import Flask, request, send_file, jsonify, render_template
import tempfile
from bond_excel_generator import generate_excel
import os

app = Flask(__name__, template_folder="templates")
TEMP_DIR = tempfile.gettempdir()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.json
    temp_path = os.path.join(TEMP_DIR, next(tempfile._get_candidate_names()) + ".xlsx")
    buy_price, sell_price = generate_excel(
        bought_date=data["bought_date"],
        sold_date=data["sold_date"],
        quantity=data["quantity"],
        client_type=data["client_type"],
        rate=data["rate"],
        filepath=temp_path
    )
    return jsonify({
        "buy_price": round(buy_price, 2),
        "sell_price": round(sell_price, 2),
        "download_url": f"/download/{os.path.basename(temp_path)}"
    })

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(TEMP_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")