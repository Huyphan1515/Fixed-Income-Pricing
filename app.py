import os
import requests
from flask import Flask, request, render_template, jsonify, send_file
import tempfile
from bond_excel_generator import generate_excel
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder="templates")
TEMP_DIR = tempfile.gettempdir()

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

# Hugging Face Summarization with error handling
def hf_summarize(text):
    api_token = os.environ.get("HUGGINGFACE_API_TOKEN")
    if not api_token:
        return "Hugging Face API token not set."
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {api_token}"}
    data = {"inputs": text}
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        try:
            result = response.json()
        except Exception:
            # Non-JSON response (likely model is loading or error)
            return f"Error: Hugging Face returned non-JSON response: {response.text}"
        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]
        elif isinstance(result, dict) and "error" in result:
            return f"Error: {result['error']}"
        else:
            return str(result)
    except requests.exceptions.RequestException as e:
        return f"Error communicating with Hugging Face: {e}"

# Hugging Face Q&A with error handling
def hf_qa(question, context):
    api_token = os.environ.get("HUGGINGFACE_API_TOKEN")
    if not api_token:
        return "Hugging Face API token not set."
    API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
    headers = {"Authorization": f"Bearer {api_token}"}
    data = {"inputs": {"question": question, "context": context}}
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        try:
            result = response.json()
        except Exception:
            return f"Error: Hugging Face returned non-JSON response: {response.text}"
        if isinstance(result, dict) and "answer" in result:
            return result["answer"]
        elif isinstance(result, dict) and "error" in result:
            return f"Error: {result['error']}"
        else:
            return str(result)
    except requests.exceptions.RequestException as e:
        return f"Error communicating with Hugging Face: {e}"

@app.route("/")
def index():
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
def calculate():
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
def download(filename):
    return send_file(os.path.join(TEMP_DIR, filename), as_attachment=True)

@app.route("/nlp", methods=["GET", "POST"])
def nlp():
    answer = summary = None
    user_input = ""
    function = "qa"
    if request.method == 'POST':
        user_input = request.form['user_input']
        function = request.form['function']
        if function == 'qa':
            answer = hf_qa(user_input, user_input)
        elif function == 'summarize':
            summary = hf_summarize(user_input)
    return render_template(
        "nlp.html",
        answer=answer,
        summary=summary,
        user_input=user_input,
        function=function
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
