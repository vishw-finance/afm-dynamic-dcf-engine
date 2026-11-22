# Dynamic Capital Investment Appraisal (DCF) & Valuation Engine

An institutional-grade Python capital budgeting engine aligned with **ACCA Advanced Financial Management (AFM)** standards. It automates multi-year nominal cash flow forecasting and exports fully formatted Microsoft Excel workbooks populated with **live dynamic Excel formulas**.

## Core Financial Mechanics Implemented
* **Specific vs. General Inflation:** Supports independent line-item inflation rates across revenue, variable costs, fixed costs, and working capital, handling both Year 0 (`Y0`) and Year 1 (`Y1`) pricing bases.
* **Fisher Equation Integration:** Automatically converts Real WACC inputs to Nominal WACC via $(1 + i) = (1 + r)(1 + h)$.
* **Tax-Allowable Depreciation (TAD) & Balancing Adjustments:** Models reducing-balance and straight-line capital allowances, automatically computing final-year balancing allowances/charges upon asset disposal.
* **Taxation Timing Shifts:** Dynamically extends the appraisal horizon to capture corporation tax outflows and TAD tax shields payable one year in arrears.
* **Incremental Working Capital Engine:** Models initial Year 0 outlays, annual inflation top-ups, and full terminal release at project closure.
* **Dual MIRR Calculation:** Outputs both the ACCA formula-sheet MIRR (anchored to operational project life $n$) and the standard Excel `=MIRR()` horizon figure alongside NPV and IRR.
* **Live Excel Formula Exporter:** Uses `openpyxl` to build `.xlsx` models containing dynamic `=SUM()`, `=NPV()`, `=IRR()`, `=MIRR()`, and `=IF()` formulas rather than hardcoded outputs.

## Quickstart
```bash
git clone [https://github.com/vishw-finance/afm-dynamic-dcf-engine.git](https://github.com/vishw-finance/afm-dynamic-dcf-engine.git)
cd afm-dynamic-dcf-engine
pip install -r requirements.txt
python main.py