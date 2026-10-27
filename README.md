# Pakistan E-commerce Store Insights

This Streamlit dashboard follows the analysis in `Untitled50.ipynb` and adds interactive filters, customer repeat-purchase analysis, payment comparisons, SKU rankings, and a data-quality view.

## Run locally

Place `Pakistan Largest Ecommerce Dataset.csv` beside `app.py`, or upload it from the dashboard sidebar. The CSV is not included in this project folder.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

The uploader accepts CSV files up to 500 MB. If your Python version does not have compatible wheels for a dependency, use a supported Python release (3.12 or 3.13) and repeat the setup in a fresh virtual environment.

## Data handling

The notebook reports 584,524 populated item rows and 464,051 blank trailing spreadsheet rows. It later fills missing sales-related numeric columns with their means; that makes the blank rows look like transactions and inflates totals. The dashboard removes rows without an item ID, keeps genuine missing values, and does not assign revenue to the unknown category unless you enable it. Recorded sales are the sum of `grand_total` on the filtered item rows. Order value is calculated by summing those rows per order ID, then averaging the order totals.
