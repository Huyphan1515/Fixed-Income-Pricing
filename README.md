# Bond Modeling / Fixed-Income Pricing

A web application for pricing and analyzing bonds, generating cash flow schedules, and downloading investment reports as Excel files. Built with Flask, pandas, and openpyxl.

---

## Features

- **Bond Price Calculator:**  
  Calculate buy/sell price, coupons, and taxes for bonds with variable parameters.

- **Excel Export:**  
  Download a detailed investment report including cash flows, PV calculations, and summary tables.

- **User-Friendly Interface:**  
  Intuitive web UI with Bootstrap styling and embedded financial widgets (exchange rates, economic calendar, etc).

- **Customizable Inputs:**  
  Supports different coupon frequencies, tax rates, client types, and calculation methods.

---

## Demo

![screenshot or gif placeholder]

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/Huyphan1515/Fixed-Income-Pricing.git
   cd Fixed-Income-Pricing
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```sh
   python app.py
   ```

4. **Open your browser:**  
   Go to [http://localhost:5000](http://localhost:5000)

---

## Usage

1. Fill out the bond details in the form (face value, coupon rate, dates, etc).
2. Click **Calculate**.
3. View the investment summary and table.
4. Download the Excel report for detailed analysis.

---

## Project Structure

```
.
├── app.py                  # Flask web server
├── bond_excel_generator.py # Bond calculation and Excel export logic
├── templates/
│   └── index.html          # Main webpage template
├── requirements.txt        # Python dependencies
├── render.yaml             # Deployment config (Render.com)
└── README.md
```

---

## API Endpoints

- `GET /`  
  Main web interface.

- `POST /calculate`  
  Accepts bond parameters (JSON) and returns investment summary and Excel download URL.

- `GET /download/<filename>`  
  Download the generated Excel report.

---

## Contributing

Pull requests welcome!  
If you find a bug or have a feature request, please open an issue.

---

## License

[MIT License](LICENSE)  
Built by Huy Phan.

---

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [pandas](https://pandas.pydata.org/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [Bootstrap](https://getbootstrap.com/)
- [Investing.com Widgets](https://www.investing.com/webmaster-tools/)

---

Let me know if you want this tailored further or want to add badges/screenshots!
