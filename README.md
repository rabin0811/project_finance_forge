# project_finance_forge

## Finance Forge (Enomy-Finances) — Prototype

A Flask web prototype for a finance advisory system: currency conversion, investment projections, client records, role-based login, and data visualization.

- Original location: `D:\Computers Files\work\ismt\Samir dost\samir\finance-forge` (standardized copy)
- Working copy: `D:\PROJECTS_READY\project_finance_forge`
- Stack: Python 3, Flask 3, SQLite, HTML/CSS/JavaScript

## Folder layout

```text
project_finance_forge/
  backend/    Flask app, templates, static assets, SQLite DB, tests
  docs/       Project documentation
```

## Setup and run

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000/login>.

## Tests

```powershell
cd backend
python -m unittest tests.test_app
```

## Verified status (2026-11-09)

- [x] `python -m unittest tests.test_app` passed 7/7 tests
- [x] `/login` returned HTTP 200
- [x] `/` returned HTTP 200 after authentication flow
- [x] Currency conversion and investment projection logic covered by tests
- [ ] Live external exchange-rate API not required; the app has a static fallback

## Notes and limitations

- Uses SQLite (`finance.db`); no external database is required.
- The app includes demo accounts seeded in the database; change credentials before deployment.
- The exchange-rate API is optional; offline fallback rates are built in.
- Do not commit `.env`, the SQLite database, or virtual environments.

## Troubleshooting

- **`ModuleNotFoundError: flask`**: activate the virtual environment and install `requirements.txt`.
- **Login fails**: inspect the seeded users or reset the SQLite database.
- **Port 5000 in use**: change the Flask port or stop the conflicting process.
- **Currency API offline**: the static fallback keeps the conversion page usable.
