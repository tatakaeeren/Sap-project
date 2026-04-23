import json
import sqlite3
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "buildright_r2r.db"

ORG_DATA = [
    ("Company Code", "BR01"),
    ("Company Name", "BuildRight Construction Pvt. Ltd."),
    ("Fiscal Year Variant", "K4 (Apr - Mar)"),
    ("Chart of Accounts", "BRCOA"),
    ("Controlling Area", "BR01"),
    ("Currency", "INR"),
    ("Posting Period", "Period 1 - April 2026"),
]

GL_ACCOUNTS = {
    "100000": "Cash and Bank",
    "110000": "Accounts Receivable",
    "120000": "Inventory - Raw Materials",
    "130000": "Prepaid Expenses",
    "200000": "Fixed Assets",
    "210000": "Accumulated Depreciation",
    "300000": "Accounts Payable",
    "310000": "Accrued Liabilities",
    "320000": "Short Term Loans",
    "400000": "Share Capital",
    "410000": "Retained Earnings",
    "420000": "Current Year Profit/Loss",
    "500000": "Revenue from Operations",
    "510000": "Other Income",
    "600000": "Cost of Goods Sold",
    "610000": "Salaries and Wages",
    "620000": "Depreciation Expense",
    "630000": "Administrative Expenses",
    "640000": "Finance Costs",
    "650000": "Tax Expense",
}

COST_CENTERS = {
    "CC001": "Finance and Accounting",
    "CC002": "Operations",
    "CC003": "Administration",
    "CC004": "Sales and Marketing",
}

SEQUENCE_DEFAULTS = {
    "je": 100000001,
    "tb": 200000001,
    "adj": 300000001,
    "recon": 400000001,
    "accrual": 500000001,
    "depreciation": 600000001,
    "close": 700000001,
    "report": 800000001,
}

PREFIXES = {
    "je": "JE",
    "tb": "TB",
    "adj": "ADJ",
    "recon": "REC",
    "accrual": "ACC",
    "depreciation": "DEP",
    "close": "CLO",
    "report": "RPT",
}

R2R_TIMELINE = [
    {"key": "je", "title": "Journal Entry Posting", "code": "FB50"},
    {"key": "accrual", "title": "Accruals and Provisions", "code": "FBS1"},
    {"key": "depreciation", "title": "Depreciation Run", "code": "AFAB"},
    {"key": "recon", "title": "GL Reconciliation", "code": "FAGLF03"},
    {"key": "adj", "title": "Adjustment Entries", "code": "F-02"},
    {"key": "tb", "title": "Trial Balance", "code": "F.08"},
    {"key": "close", "title": "Period/Year-End Close", "code": "OB52"},
    {"key": "report", "title": "Financial Statements", "code": "F.01"},
]


def utc_now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def decimal_value(value):
    return float(Decimal(str(value)).quantize(Decimal("1.00")))


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


class R2RDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = dict_factory
        return conn

    def initialize(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS organization_data (
                label TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS gl_accounts (
                account_code TEXT PRIMARY KEY,
                account_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cost_centers (
                cc_code TEXT PRIMARY KEY,
                cc_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sequences (
                key TEXT PRIMARY KEY,
                next_value INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                je_number TEXT NOT NULL UNIQUE,
                entry_type TEXT NOT NULL,
                description TEXT NOT NULL,
                debit_account TEXT NOT NULL,
                credit_account TEXT NOT NULL,
                amount REAL NOT NULL,
                cost_center TEXT NOT NULL,
                posting_date TEXT NOT NULL,
                period TEXT NOT NULL,
                status TEXT NOT NULL,
                created_on TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS period_close (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                close_number TEXT NOT NULL UNIQUE,
                close_type TEXT NOT NULL,
                period TEXT NOT NULL,
                fiscal_year TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                status TEXT NOT NULL,
                closed_by TEXT NOT NULL,
                created_on TEXT NOT NULL
            );
        """)

        cur.execute("SELECT COUNT(*) AS count FROM organization_data")
        if cur.fetchone()["count"] == 0:
            cur.executemany("INSERT INTO organization_data (label, value) VALUES (?, ?)", ORG_DATA)

        cur.execute("SELECT COUNT(*) AS count FROM gl_accounts")
        if cur.fetchone()["count"] == 0:
            cur.executemany("INSERT INTO gl_accounts (account_code, account_name) VALUES (?, ?)",
                            list(GL_ACCOUNTS.items()))

        cur.execute("SELECT COUNT(*) AS count FROM cost_centers")
        if cur.fetchone()["count"] == 0:
            cur.executemany("INSERT INTO cost_centers (cc_code, cc_name) VALUES (?, ?)",
                            list(COST_CENTERS.items()))

        cur.execute("SELECT COUNT(*) AS count FROM sequences")
        if cur.fetchone()["count"] == 0:
            cur.executemany("INSERT INTO sequences (key, next_value) VALUES (?, ?)",
                            list(SEQUENCE_DEFAULTS.items()))

        conn.commit()
        conn.close()

    def reset(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM journal_entries")
        cur.execute("DELETE FROM period_close")
        cur.execute("DELETE FROM sequences")
        cur.executemany("INSERT INTO sequences (key, next_value) VALUES (?, ?)",
                        list(SEQUENCE_DEFAULTS.items()))
        conn.commit()
        conn.close()

    def next_number(self, key):
        conn = self.connect()
        cur = conn.cursor()
        row = cur.execute("SELECT next_value FROM sequences WHERE key = ?", (key,)).fetchone()
        current = row["next_value"]
        cur.execute("UPDATE sequences SET next_value = ? WHERE key = ?", (current + 1, key))
        conn.commit()
        conn.close()
        return f"{PREFIXES[key]}{current}"

    def get_master_snapshot(self):
        conn = self.connect()
        cur = conn.cursor()
        org = cur.execute("SELECT label, value FROM organization_data").fetchall()
        accounts = cur.execute("SELECT account_code, account_name FROM gl_accounts ORDER BY account_code").fetchall()
        centers = cur.execute("SELECT cc_code, cc_name FROM cost_centers").fetchall()
        conn.close()
        return {
            "organization": [[r["label"], r["value"]] for r in org],
            "glAccounts": [[r["account_code"], r["account_name"]] for r in accounts],
            "costCenters": [[r["cc_code"], r["cc_name"]] for r in centers],
        }

    def create_journal_entry(self, entry_type, description, debit_account, credit_account,
                              amount, cost_center, posting_date, period, payload):
        je_number = self.next_number("je")
        created_on = utc_now()
        conn = self.connect()
        conn.execute("""
            INSERT INTO journal_entries
            (je_number, entry_type, description, debit_account, credit_account,
             amount, cost_center, posting_date, period, status, created_on, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (je_number, entry_type, description, debit_account, credit_account,
              decimal_value(amount), cost_center, posting_date, period, "Posted", created_on,
              json.dumps(payload)))
        conn.commit()
        conn.close()
        return je_number, created_on

    def list_journal_entries(self):
        conn = self.connect()
        rows = conn.execute("SELECT * FROM journal_entries ORDER BY id DESC").fetchall()
        conn.close()
        result = []
        for r in rows:
            result.append({
                "jeNumber": r["je_number"],
                "entryType": r["entry_type"],
                "description": r["description"],
                "debitAccount": r["debit_account"],
                "creditAccount": r["credit_account"],
                "amount": r["amount"],
                "costCenter": r["cost_center"],
                "postingDate": r["posting_date"],
                "period": r["period"],
                "status": r["status"],
                "createdOn": r["created_on"],
                "payload": json.loads(r["payload_json"]),
            })
        return result

    def latest_entry_by_type(self, entry_type):
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM journal_entries WHERE entry_type = ? ORDER BY id DESC LIMIT 1",
            (entry_type,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        row["payload"] = json.loads(row["payload_json"])
        return row

    def create_period_close(self, close_type, period, fiscal_year, steps, closed_by):
        close_number = self.next_number("close")
        created_on = utc_now()
        conn = self.connect()
        conn.execute("""
            INSERT INTO period_close
            (close_number, close_type, period, fiscal_year, steps_json, status, closed_by, created_on)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (close_number, close_type, period, fiscal_year, json.dumps(steps),
              "Completed", closed_by, created_on))
        conn.commit()
        conn.close()
        return close_number, created_on

    def list_period_closes(self):
        conn = self.connect()
        rows = conn.execute("SELECT * FROM period_close ORDER BY id DESC").fetchall()
        conn.close()
        result = []
        for r in rows:
            result.append({
                "closeNumber": r["close_number"],
                "closeType": r["close_type"],
                "period": r["period"],
                "fiscalYear": r["fiscal_year"],
                "steps": json.loads(r["steps_json"]),
                "status": r["status"],
                "closedBy": r["closed_by"],
                "createdOn": r["created_on"],
            })
        return result

    def get_trial_balance(self):
        conn = self.connect()
        rows = conn.execute("SELECT * FROM journal_entries WHERE status = 'Posted'").fetchall()
        conn.close()

        balances = {}
        for r in rows:
            da = r["debit_account"]
            ca = r["credit_account"]
            amt = r["amount"]
            if da not in balances:
                balances[da] = {"account": da, "name": GL_ACCOUNTS.get(da, da), "debit": 0, "credit": 0}
            if ca not in balances:
                balances[ca] = {"account": ca, "name": GL_ACCOUNTS.get(ca, ca), "debit": 0, "credit": 0}
            balances[da]["debit"] += amt
            balances[ca]["credit"] += amt

        tb_rows = sorted(balances.values(), key=lambda x: x["account"])
        total_debit = sum(r["debit"] for r in tb_rows)
        total_credit = sum(r["credit"] for r in tb_rows)
        balanced = abs(total_debit - total_credit) < 0.01

        return {
            "rows": tb_rows,
            "totalDebit": total_debit,
            "totalCredit": total_credit,
            "balanced": balanced,
        }

    def get_financial_statements(self):
        tb = self.get_trial_balance()
        balances = {r["account"]: r["debit"] - r["credit"] for r in tb["rows"]}

        revenue = abs(balances.get("500000", 0)) + abs(balances.get("510000", 0))
        cogs = balances.get("600000", 0)
        gross_profit = revenue - cogs
        opex = (balances.get("610000", 0) + balances.get("620000", 0) +
                balances.get("630000", 0))
        ebit = gross_profit - opex
        finance_costs = balances.get("640000", 0)
        pbt = ebit - finance_costs
        tax = balances.get("650000", 0)
        pat = pbt - tax

        assets = (balances.get("100000", 0) + balances.get("110000", 0) +
                  balances.get("120000", 0) + balances.get("130000", 0) +
                  balances.get("200000", 0) - abs(balances.get("210000", 0)))
        liabilities = (abs(balances.get("300000", 0)) + abs(balances.get("310000", 0)) +
                       abs(balances.get("320000", 0)))
        equity = abs(balances.get("400000", 0)) + abs(balances.get("410000", 0)) + pat

        return {
            "pnl": {
                "revenue": decimal_value(revenue),
                "cogs": decimal_value(cogs),
                "grossProfit": decimal_value(gross_profit),
                "opex": decimal_value(opex),
                "ebit": decimal_value(ebit),
                "financeCosts": decimal_value(finance_costs),
                "pbt": decimal_value(pbt),
                "tax": decimal_value(tax),
                "pat": decimal_value(pat),
            },
            "balanceSheet": {
                "totalAssets": decimal_value(assets),
                "totalLiabilities": decimal_value(liabilities),
                "totalEquity": decimal_value(equity),
                "balanced": abs(assets - (liabilities + equity)) < 1.0,
            }
        }

    def get_reconciliation_status(self):
        je_list = self.list_journal_entries()
        total_je = len(je_list)
        has_accrual = any(j["entryType"] == "accrual" for j in je_list)
        has_depreciation = any(j["entryType"] == "depreciation" for j in je_list)
        has_adjustment = any(j["entryType"] == "adj" for j in je_list)
        tb = self.get_trial_balance()

        items = [
            {"label": "Journal Entries Posted", "status": "done" if total_je > 0 else "pending",
             "detail": f"{total_je} entries posted"},
            {"label": "Accruals and Provisions", "status": "done" if has_accrual else "pending",
             "detail": "FBS1 accrual entry recorded" if has_accrual else "No accrual entries yet"},
            {"label": "Depreciation Run", "status": "done" if has_depreciation else "pending",
             "detail": "AFAB depreciation posted" if has_depreciation else "Depreciation not run"},
            {"label": "GL Reconciliation", "status": "done" if total_je >= 2 else "pending",
             "detail": "GL accounts reconciled" if total_je >= 2 else "Post more entries first"},
            {"label": "Adjustment Entries", "status": "done" if has_adjustment else "pending",
             "detail": "Adjustment entries recorded" if has_adjustment else "No adjustments posted"},
            {"label": "Trial Balance", "status": "done" if tb["balanced"] and total_je > 0 else (
                "error" if total_je > 0 and not tb["balanced"] else "pending"),
             "detail": "Balanced ✓" if tb["balanced"] and total_je > 0 else (
                 "UNBALANCED - review entries" if total_je > 0 else "No entries yet")},
            {"label": "Period Close", "status": "done" if len(self.list_period_closes()) > 0 else "pending",
             "detail": "Period successfully closed" if len(self.list_period_closes()) > 0 else "Period not closed"},
            {"label": "Financial Statements", "status": "done" if tb["balanced"] and total_je > 0 else "pending",
             "detail": "Statements generated" if tb["balanced"] and total_je > 0 else "Complete prior steps first"},
        ]
        completed = sum(1 for i in items if i["status"] == "done")
        return {"items": items, "completed": completed, "total": len(items)}

    def get_metrics(self):
        je_list = self.list_journal_entries()
        tb = self.get_trial_balance()
        fs = self.get_financial_statements()
        closes = self.list_period_closes()

        total_postings = len(je_list)
        total_debits = tb["totalDebit"]
        net_income = fs["pnl"]["pat"]
        period_closed = len(closes) > 0

        return {
            "totalPostings": total_postings,
            "totalDebits": total_debits,
            "netIncome": net_income,
            "periodClosed": period_closed,
            "trialBalanceBalanced": tb["balanced"],
            "closingCount": len(closes),
        }


db = R2RDatabase(DB_PATH)


def snapshot():
    je_list = db.list_journal_entries()
    tb = db.get_trial_balance()
    fs = db.get_financial_statements()
    closes = db.list_period_closes()
    recon = db.get_reconciliation_status()
    metrics = db.get_metrics()
    master = db.get_master_snapshot()

    process_data = {}
    for step in R2R_TIMELINE:
        key = step["key"]
        if key in ("je", "accrual", "depreciation", "adj"):
            entry = db.latest_entry_by_type(key)
            process_data[key] = {
                "number": entry["je_number"],
                "createdOn": entry["created_on"],
                "description": entry["description"],
                "amount": entry["amount"],
            } if entry else None
        elif key == "tb":
            process_data[key] = {"number": "TB-LIVE", "createdOn": utc_now(),
                                  "balanced": tb["balanced"]} if je_list else None
        elif key == "recon":
            process_data[key] = {"number": "REC-LIVE", "createdOn": utc_now(),
                                  "status": "Reconciled"} if len(je_list) >= 2 else None
        elif key == "close":
            process_data[key] = {"number": closes[0]["closeNumber"],
                                  "createdOn": closes[0]["createdOn"]} if closes else None
        elif key == "report":
            process_data[key] = {"number": "RPT-LIVE", "createdOn": utc_now(),
                                  "status": "Generated"} if tb["balanced"] and je_list else None

    return {
        "company": "BuildRight Construction Pvt. Ltd.",
        "masterData": master,
        "timeline": R2R_TIMELINE,
        "processData": process_data,
        "journalEntries": je_list,
        "trialBalance": tb,
        "financialStatements": fs,
        "periodCloses": closes,
        "reconciliation": recon,
        "metrics": metrics,
        "glAccounts": GL_ACCOUNTS,
        "costCenters": COST_CENTERS,
    }


def create_je(payload):
    entry_type = payload.get("entryType", "je")
    description = payload["description"]
    debit_account = payload["debitAccount"]
    credit_account = payload["creditAccount"]
    amount = decimal_value(payload["amount"])
    cost_center = payload.get("costCenter", "CC001")
    posting_date = payload["postingDate"]
    period = payload.get("period", "Period 1 - April 2026")

    if debit_account == credit_account:
        raise ValueError("Debit and credit accounts cannot be the same.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if debit_account not in GL_ACCOUNTS:
        raise ValueError(f"GL account {debit_account} not found in chart of accounts.")
    if credit_account not in GL_ACCOUNTS:
        raise ValueError(f"GL account {credit_account} not found in chart of accounts.")

    record = {
        "entryType": entry_type,
        "description": description,
        "debitAccount": debit_account,
        "debitAccountName": GL_ACCOUNTS[debit_account],
        "creditAccount": credit_account,
        "creditAccountName": GL_ACCOUNTS[credit_account],
        "amount": amount,
        "costCenter": cost_center,
        "postingDate": posting_date,
        "period": period,
    }
    je_number, created_on = db.create_journal_entry(
        entry_type, description, debit_account, credit_account,
        amount, cost_center, posting_date, period, record
    )
    record["jeNumber"] = je_number
    record["createdOn"] = created_on
    return record


def create_period_close(payload):
    close_type = payload.get("closeType", "month-end")
    period = payload["period"]
    fiscal_year = payload.get("fiscalYear", "2026")
    closed_by = payload.get("closedBy", "Finance Controller")

    je_list = db.list_journal_entries()
    tb = db.get_trial_balance()

    if not je_list:
        raise ValueError("Cannot close period without journal entries.")
    if not tb["balanced"]:
        raise ValueError("Trial balance is not balanced. Resolve discrepancies before closing.")

    steps = [
        {"step": "Verify all journal entries posted", "status": "Completed"},
        {"step": "Run depreciation (AFAB)", "status": "Completed"},
        {"step": "Post accruals (FBS1)", "status": "Completed"},
        {"step": "GL reconciliation (FAGLF03)", "status": "Completed"},
        {"step": "Trial balance validation (F.08)", "status": "Completed"},
        {"step": "Generate financial statements (F.01)", "status": "Completed"},
        {"step": f"Close posting period (OB52) - {period}", "status": "Completed"},
        {"step": "Carry forward balances", "status": "Completed" if close_type == "year-end" else "N/A"},
    ]

    close_number, created_on = db.create_period_close(close_type, period, fiscal_year, steps, closed_by)
    return {
        "closeNumber": close_number,
        "closeType": close_type,
        "period": period,
        "fiscalYear": fiscal_year,
        "steps": steps,
        "closedBy": closed_by,
        "createdOn": created_on,
        "status": "Completed",
    }


TRANSACTION_HANDLERS = {
    "je": create_je,
    "accrual": lambda p: create_je({**p, "entryType": "accrual"}),
    "depreciation": lambda p: create_je({**p, "entryType": "depreciation"}),
    "adj": lambda p: create_je({**p, "entryType": "adj"}),
    "close": create_period_close,
}


def seed_demo():
    db.reset()

    create_je({
        "entryType": "je",
        "description": "Revenue recognition - steel supply contract",
        "debitAccount": "110000",
        "creditAccount": "500000",
        "amount": 500000,
        "costCenter": "CC004",
        "postingDate": "2026-04-05",
        "period": "Period 1 - April 2026",
    })
    create_je({
        "entryType": "je",
        "description": "Cost of goods sold - structural steel rods",
        "debitAccount": "600000",
        "creditAccount": "120000",
        "amount": 300000,
        "costCenter": "CC002",
        "postingDate": "2026-04-05",
        "period": "Period 1 - April 2026",
    })
    create_je({
        "entryType": "je",
        "description": "Salaries for April 2026",
        "debitAccount": "610000",
        "creditAccount": "300000",
        "amount": 75000,
        "costCenter": "CC001",
        "postingDate": "2026-04-30",
        "period": "Period 1 - April 2026",
    })
    create_je({
        "entryType": "je",
        "description": "Cash received from accounts receivable",
        "debitAccount": "100000",
        "creditAccount": "110000",
        "amount": 500000,
        "costCenter": "CC001",
        "postingDate": "2026-04-15",
        "period": "Period 1 - April 2026",
    })
    create_je({
        "entryType": "accrual",
        "description": "Accrual for electricity expenses - April",
        "debitAccount": "630000",
        "creditAccount": "310000",
        "amount": 12000,
        "costCenter": "CC003",
        "postingDate": "2026-04-30",
        "period": "Period 1 - April 2026",
    })
    create_je({
        "entryType": "depreciation",
        "description": "Monthly depreciation run - fixed assets",
        "debitAccount": "620000",
        "creditAccount": "210000",
        "amount": 8500,
        "costCenter": "CC002",
        "postingDate": "2026-04-30",
        "period": "Period 1 - April 2026",
    })
    create_je({
        "entryType": "adj",
        "description": "Adjustment - prepaid insurance reclassification",
        "debitAccount": "130000",
        "creditAccount": "630000",
        "amount": 5000,
        "costCenter": "CC003",
        "postingDate": "2026-04-30",
        "period": "Period 1 - April 2026",
    })
    create_je({
        "entryType": "je",
        "description": "Tax provision for April 2026",
        "debitAccount": "650000",
        "creditAccount": "310000",
        "amount": 31500,
        "costCenter": "CC001",
        "postingDate": "2026-04-30",
        "period": "Period 1 - April 2026",
    })
    create_je({
        "entryType": "je",
        "description": "Payment to vendor - outstanding payable",
        "debitAccount": "300000",
        "creditAccount": "100000",
        "amount": 75000,
        "costCenter": "CC001",
        "postingDate": "2026-04-28",
        "period": "Period 1 - April 2026",
    })
    create_period_close({
        "closeType": "month-end",
        "period": "Period 1 - April 2026",
        "fiscalYear": "2026",
        "closedBy": "Finance Controller - BR01",
    })


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format, *args):
        pass

    def _json_response(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _handle_api_get(self, path):
        if path == "/api/state":
            self._json_response(snapshot())
            return True
        if path == "/api/export":
            self._json_response({"exportedAt": utc_now(), "snapshot": snapshot()})
            return True
        if path == "/api/trialbalance":
            self._json_response(db.get_trial_balance())
            return True
        if path == "/api/statements":
            self._json_response(db.get_financial_statements())
            return True
        return False

    def _handle_api_post(self, path):
        if path == "/api/reset":
            db.reset()
            self._json_response(snapshot())
            return True
        if path == "/api/seed":
            seed_demo()
            self._json_response(snapshot())
            return True
        if path.startswith("/api/transactions/"):
            txn_type = path.rsplit("/", 1)[-1]
            handler = TRANSACTION_HANDLERS.get(txn_type)
            if not handler:
                self._json_response({"error": "Transaction type not found."}, HTTPStatus.NOT_FOUND)
                return True
            try:
                payload = self._read_json()
                handler(payload)
                self._json_response(snapshot(), HTTPStatus.CREATED)
            except KeyError as e:
                self._json_response({"error": f"Missing required field: {e.args[0]}"}, HTTPStatus.BAD_REQUEST)
            except ValueError as e:
                self._json_response({"error": str(e)}, HTTPStatus.CONFLICT)
            return True
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            if not self._handle_api_get(parsed.path):
                self._json_response({"error": "Endpoint not found."}, HTTPStatus.NOT_FOUND)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            if not self._handle_api_post(parsed.path):
                self._json_response({"error": "Endpoint not found."}, HTTPStatus.NOT_FOUND)
            return
        self._json_response({"error": "Unsupported route."}, HTTPStatus.NOT_FOUND)


def run(port=8000):
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    print(f"\n  BuildRight R2R Command Center")
    print(f"  Running on http://127.0.0.1:{port}")
    print(f"  Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
