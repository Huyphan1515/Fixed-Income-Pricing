from flask import Flask, request, jsonify, send_file, render_template
import tempfile
from bond_excel_generator import generate_excel
import os
import requests
from bs4 import BeautifulSoup
from typing import Any
import openai

# --- Secure OpenAI API key loading ---
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

app = Flask(__name__, template_folder="templates")
TEMP_DIR = tempfile.gettempdir()

@app.route("/")
def index() -> str:
    return render_template("index.html")

@app.route("/posts")
def posts():
    posts = [
        {
            "title": "What is a Bond?",
            "desc": "A beginner's guide to bonds and how they work.",
            "url": "https://www.investopedia.com/terms/b/bond.asp"
        },
        {
            "title": "The Basics of Bonds",
            "desc": "Learn the fundamentals of bonds, their types, and how they are used.",
            "url": "https://www.investopedia.com/financial-edge/0312/the-basics-of-bonds.aspx"
        },
        {
            "title": "Bond Yields Explained",
            "desc": "Understand what bond yield means and how it is calculated.",
            "url": "https://www.investopedia.com/terms/b/bond-yield.asp"
        },
        {
            "title": "Bond Valuation",
            "desc": "How to calculate the value of a bond.",
            "url": "https://www.investopedia.com/terms/b/bond-valuation.asp"
        }
    ]
    return render_template("posts.html", posts=posts)

def get_interest_rate_table():
    url = "https://cafef.vn/du-lieu/lai-suat-ngan-hang.chn"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        table_container = soup.find("div", class_="table-responsive")
        table = table_container.find("table") if table_container else None
        return str(table) if table else "<p>Interest rate table not found.</p>"
    except Exception as e:
        return f"<p>Unable to fetch interest rates. ({e})</p>"

@app.route("/interest-rates")
def interest_rates():
    table_html = get_interest_rate_table()
    return render_template("interest_rates.html", table_html=table_html)

@app.route("/calculate", methods=["POST"])
def calculate() -> Any:
    data = request.json
    temp_path = os.path.join(TEMP_DIR, next(tempfile._get_candidate_names()) + ".xlsx")
    bond_type = data.get("bond_type", "fixed")
    num_periods = int(data.get("num_periods", 0))
    coupon_rates = data.get("coupon_rates", [])
    discount_rate = safe_float(data.get("discount_rate", 0))

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

# --- NLP (Q&A and Summarize) route: now SAFE and compatible with openai>=1.0.0 ---
@app.route("/nlp", methods=["GET", "POST"])
def nlp():
    answer = summary = None
    user_input = ""
    function = "qa"
    if request.method == 'POST':
        user_input = request.form['user_input']
        function = request.form['function']
        prompt = (
            f"Answer this question clearly and concisely:\n{user_input}"
            if function == 'qa'
            else f"Summarize the following text:\n{user_input}"
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=512
        )
        result = response.choices[0].message.content
        if function == 'qa':
            answer = result
        else:
            summary = result
    return render_template("nlp.html",
                           answer=answer,
                           summary=summary,
                           user_input=user_input,
                           function=function)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
