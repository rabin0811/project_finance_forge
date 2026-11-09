import sqlite3
import functools
import urllib.request
import json
from datetime import datetime
from flask import Flask, g, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "finance-forge-demo-secret-change-me"

DATABASE = "finance.db"

# Currencies supported by the system (from the report: GBP, USD, EUR, BRL, JPY, TRY, NPR)
SUPPORTED_CURRENCIES = ["GBP", "USD", "EUR", "BRL", "JPY", "TRY", "NPR"]

# Fallback static rates relative to GBP (used when the live API is unavailable)
FALLBACK_RATES = {
    "GBP": 1.0,
    "USD": 1.27,
    "EUR": 1.17,
    "BRL": 6.30,
    "JPY": 191.0,
    "TRY": 40.8,
    "NPR": 169.0,
}

CURRENCY_SYMBOLS = {
    "GBP": "£", "USD": "$", "EUR": "€", "BRL": "R$",
    "JPY": "¥", "TRY": "₺", "NPR": "रू",
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            full_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            rate REAL NOT NULL,
            converted_amount REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS currency_rates (
            currency TEXT PRIMARY KEY,
            rate REAL NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS investment_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            initial_amount REAL NOT NULL,
            monthly_contribution REAL NOT NULL DEFAULT 0,
            annual_rate REAL NOT NULL,
            years INTEGER NOT NULL,
            projected_value REAL NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    # Seed an admin and staff account (demo only - plaintext hashes)
    cur = db.execute("SELECT COUNT(*) AS c FROM users")
    total = cur.fetchone()[0]
    if total == 0:
        db.executemany(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?,?,?,?)",
            [
                ("admin", "admin123", "admin", "System Administrator"),
                ("staff", "staff123", "staff", "Finance Advisor"),
                ("client", "client123", "client", "Demo Client"),
            ],
        )
        db.execute(
            "INSERT INTO clients (user_id, name, email, phone, notes, created_at) VALUES (?,?,?,?,?,?)",
            (3, "Demo Client", "client@example.com", "01-1234567", "Sample client record",
             datetime.utcnow().isoformat()),
        )
    db.commit()
    db.close()


def get_fx_rates():
    """Fetch live exchange rates vs GBP, falling back to static rates."""
    base = "GBP"
    cached = {}
    db = get_db()
    try:
        rows = db.execute("SELECT currency, rate, updated_at FROM currency_rates").fetchall()
        for r in rows:
            cached[r["currency"]] = {"rate": r["rate"], "updated_at": r["updated_at"]}
    except sqlite3.Error:
        pass

    try:
        url = f"https://api.frankfurter.app/latest?from={base}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        rates = data["rates"]
        rates[base] = 1.0
        now = datetime.utcnow().isoformat()
        rates = {c: (rates[c] if c in rates else FALLBACK_RATES[c]) for c in SUPPORTED_CURRENCIES}
        for c, r in rates.items():
            db.execute(
                "INSERT OR REPLACE INTO currency_rates (currency, rate, updated_at) VALUES (?,?,?)",
                (c, float(r), now),
            )
        db.commit()
        return rates, now
    except Exception:
        # Fall back to static rates (optionally from cache)
        rates = {}
        for c in SUPPORTED_CURRENCIES:
            if c in cached:
                rates[c] = cached[c]["rate"]
            else:
                rates[c] = FALLBACK_RATES[c]
        return rates, (cached.get("GBP", {}).get("updated_at", "static"))


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, password),
        ).fetchone()
        if user is None:
            flash("Invalid username or password.", "danger")  # Error state (EFSM)
            return render_template("login.html")
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["full_name"] = user["full_name"]
        flash(f"Welcome, {user['full_name']}!", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user_id = session["user_id"]
    role = session["role"]
    recent = db.execute(
        """SELECT * FROM transactions
           WHERE user_id = ? OR ? = 'admin'
           ORDER BY created_at DESC LIMIT 10""",
        (user_id, role),
    ).fetchall()
    return render_template(
        "dashboard.html",
        recent=recent,
        role=role,
        CURRENCY_SYMBOLS=CURRENCY_SYMBOLS,
    )


@app.route("/convert", methods=["GET", "POST"])
@login_required
def convert():
    rates, updated = get_fx_rates()
    result = None
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount"))
            from_cur = request.form.get("from_currency", "GBP").upper()
            to_cur = request.form.get("to_currency", "USD").upper()
            if amount <= 0:
                flash("Amount must be greater than zero.", "warning")
            else:
                rate = rates[to_cur] / rates[from_cur]
                converted = round(amount * rate, 2)
                result = {
                    "amount": amount,
                    "from": from_cur,
                    "to": to_cur,
                    "rate": round(rate, 6),
                    "converted": converted,
                }
                db = get_db()
                db.execute(
                    """INSERT INTO transactions
                       (user_id, amount, from_currency, to_currency, rate, converted_amount, created_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (session["user_id"], amount, from_cur, to_cur, rate, converted,
                     datetime.utcnow().isoformat()),
                )
                db.commit()
        except (ValueError, TypeError, KeyError):
            flash("Please provide a valid amount and select currencies.", "warning")
    return render_template(
        "convert.html",
        rates=rates,
        result=result,
        currencies=SUPPORTED_CURRENCIES,
        CURRENCY_SYMBOLS=CURRENCY_SYMBOLS,
        updated=updated,
    )


def project_growth(initial, monthly, annual_rate, years):
    """Compound interest with monthly contributions factored monthly."""
    monthly_rate = annual_rate / 100 / 12
    months = int(years * 12)
    balance = initial
    for _ in range(months):
        balance = balance * (1 + monthly_rate) + monthly
    return balance


@app.route("/projection", methods=["GET", "POST"])
@login_required
def projection():
    result = None
    chart = None
    if request.method == "POST":
        try:
            initial = float(request.form.get("initial", 0))
            monthly = float(request.form.get("monthly", 0))
            rate = float(request.form.get("annual_rate", 5))
            years = int(request.form.get("years", 10))
            if years <= 0 or years > 50:
                flash("Years must be between 1 and 50.", "warning")
            else:
                projected = project_growth(initial, monthly, rate, years)
                result = {
                    "initial": initial,
                    "monthly": monthly,
                    "rate": rate,
                    "years": years,
                    "projected": round(projected, 2),
                    "contributed": round(initial + monthly * 12 * years, 2),
                }
                # data visualization: yearly growth series
                labels = []
                series = []
                for y in range(1, years + 1):
                    labels.append(str(y))
                    series.append(round(project_growth(initial, monthly, rate, y), 2))
                chart = {"labels": labels, "data": series}
                db = get_db()
                db.execute(
                    """INSERT INTO investment_plans
                       (initial_amount, monthly_contribution, annual_rate, years, projected_value, created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (initial, monthly, rate, years, projected, datetime.utcnow().isoformat()),
                )
                db.commit()
        except (ValueError, TypeError):
            flash("Please enter valid numeric values.", "warning")
    return render_template("projection.html", result=result, chart=chart,
                           CURRENCY_SYMBOLS=CURRENCY_SYMBOLS)


@app.route("/clients")
@role_required("admin", "staff")
def clients():
    db = get_db()
    rows = db.execute(
        """SELECT c.*, u.username FROM clients c
           LEFT JOIN users u ON u.id = c.user_id ORDER BY c.name"""
    ).fetchall()
    return render_template("clients.html", clients=rows)


@app.route("/clients/add", methods=["GET", "POST"])
@role_required("admin", "staff")
def add_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        notes = request.form.get("notes", "").strip()
        if not name:
            flash("Client name is required.", "warning")
        else:
            db = get_db()
            db.execute(
                """INSERT INTO clients (user_id, name, email, phone, notes, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (session["user_id"], name, email, phone, notes, datetime.utcnow().isoformat()),
            )
            db.commit()
            flash("Client added successfully.", "success")
            return redirect(url_for("clients"))
    return render_template("add_client.html")


@app.route("/reports")
@login_required
def reports():
    db = get_db()
    role = session["role"]
    user_id = session["user_id"]
    recent = db.execute(
        """SELECT * FROM transactions
           WHERE user_id = ? OR ? = 'admin'
           ORDER BY created_at DESC LIMIT 50""",
        (user_id, role),
    ).fetchall()
    return render_template("reports.html", transactions=recent, CURRENCY_SYMBOLS=CURRENCY_SYMBOLS)


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
