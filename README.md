[README.md](https://github.com/user-attachments/files/27009156/README.md)
# BuildRight R2R Command Center

**Record-to-Report Financial Close Simulator**
SAP FI Module · BuildRight Construction Pvt. Ltd.

---

## Project Details

| Field | Value |
|---|---|
| Student Name | Bipin Kumar |
| Roll Number | 2306196 |
| Batch | IT |
| Program | SAP Integration Developer |
| Topic | Record-to-Report (R2R) — Month-End/Year-End Financial Close |

---

## What Is Included

- Full interactive R2R simulator in `index.html`
- Python backend server in `app.py`
- Persistent SQLite database in `buildright_r2r.db` (auto-created)
- Enterprise SAP-style UI in `styles/app.css`
- Client logic in `scripts/app.js`
- Project documentation in `docs/`

## R2R Process Covered

| Step | Transaction | SAP Code |
|---|---|---|
| 1 | Journal Entry Posting | FB50 |
| 2 | Accruals and Provisions | FBS1 |
| 3 | Depreciation Run | AFAB |
| 4 | GL Reconciliation | FAGLF03 |
| 5 | Adjustment Entries | F-02 |
| 6 | Trial Balance | F.08 |
| 7 | Period / Year-End Close | OB52 |
| 8 | Financial Statements | F.01 |

## How To Run

```powershell
python app.py
```

Then open `http://127.0.0.1:8000` in your browser.

**Best demo flow:**
1. Open the app — click **Load Demo Data**
2. Browse Overview → Transactions → Trial Balance → Financials → Period Close
3. Use **Export Snapshot** to download the transaction state as JSON

## Features

- Real double-entry journal posting with GL account validation
- Auto-generated Trial Balance (balanced/unbalanced detection)
- Live P&L and Balance Sheet from posted entries
- Month-end and year-end close with 8-step checklist
- Depreciation (AFAB) and accruals (FBS1) simulation
- FAGLF03 reconciliation status with exception alerts
- Full GL Chart of Accounts (BRCOA) with 20 accounts
- Cost Center assignment per posting
- Persistent SQLite storage
- Export full snapshot as JSON
