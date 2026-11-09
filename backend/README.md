# Finance Forge (Enomy-Finances) — Prototype

A working web-based prototype built to demonstrate the designs described in the
SDLC assignment (Unit 7, Activity 3). It implements the system chosen in the
report: a **full web-based solution**, built **Agile/iterative**, using a
**cloud-first hybrid** hosting model in mind.

## Features (maps to the Functional Requirements in the report)

- **Currency Conversion** — real-time rates via the Frankfurter exchange API
  (GBP, USD, EUR, BRL, JPY, TRY, NPR), with a static fallback if offline.
- **Quotations / Investment Projection** — savings & investment growth with
  monthly compounding and monthly contributions, including a chart
  (data visualization).
- **Client Records** — staff/admin can add and view secure client records.
- **User Authentication** — role-based login (admin / staff / client) with
  secure sessions (the EFSM *invalid login → Error state* and *admin → Admin
  Panel* conditions).
- **Data visualization** — a drawn yearly-growth chart on the projection page.

## Designs covered

- Algorithmic design: pseudocode `ConvertCurrency()` is implemented in `app.py`.
- Data design: SQLite tables `users`, `transactions`, `currency_rates`,
  `clients`, `investment_plans` (mirrors the ERD entities/relationships).
- Logical design: role-based state transitions on login.

## Requirements

- Python 3.10+
- Flask (see `requirements.txt`)

## Setup & run

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in a browser.

### Demo accounts

| Username | Password | Role  |
|----------|----------|-------|
| admin    | admin123 | admin |
| staff    | staff123 | staff |
| client   | client123| client|

## Run tests (TDD examples from the report, section 7.2)

```bash
python -m unittest tests.test_app
```

## Project structure

```
finance-forge/
├── app.py               # Flask app, logic, DB schema (data design)
├── requirements.txt
├── static/style.css
├── templates/           # login, dashboard, convert, projection, clients, reports
├── tests/test_app.py    # unit tests (TDD)
└── finance.db           # created automatically on first run
```