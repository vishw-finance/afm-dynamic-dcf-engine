import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def export_dcf_to_excel(results: dict, output_path: str) -> str:
    """Exports the DCF schedule into a formatted Excel workbook with live formulas."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cfg = results["config"]
    df = results["schedule"]
    total_years = len(df) - 1  # Excluding Year 0

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DCF Valuation Model"
    ws.views.sheetView[0].showGridLines = True

    # Institutional Styling Palette
    navy_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    sub_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    total_fill = PatternFill(start_color="F2F4F8", end_color="F2F4F8", fill_type="solid")

    title_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    section_font = Font(name="Calibri", size=11, bold=True, color="1B365D")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    bold_font = Font(name="Calibri", size=10, bold=True)
    regular_font = Font(name="Calibri", size=10)
    input_font = Font(name="Calibri", size=10, bold=True, color="0000FF")  # Blue = hardcode input

    thin_border = Border(
        top=Side(style="thin", color="BFBFBF"),
        bottom=Side(style="thin", color="BFBFBF"),
    )
    double_bottom = Border(
        top=Side(style="thin", color="000000"),
        bottom=Side(style="double", color="000000"),
    )

    currency_fmt = '$#,##0;($#,##0);"-"'
    pct_fmt = "0.00%"
    df_fmt = "0.0000"

    # --- Title Banner ---
    last_col_ltr = get_column_letter(2 + total_years)
    ws.merge_cells(f"A1:{last_col_ltr}1")
    ws["A1"] = f"CAPITAL INVESTMENT APPRAISAL (DCF): {cfg.project_name.upper()}"
    ws["A1"].font = title_font
    ws["A1"].fill = navy_fill
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 28

    # --- Section 1: Model Parameters ---
    ws["A3"] = "1. KEY MODEL PARAMETERS"
    ws["A3"].font = section_font

    assumptions = [
        ("Nominal Discount Rate (WACC)", results["nominal_wacc"], pct_fmt),
        ("Operational Project Life (Years)", cfg.project_life, "0"),
        ("Corporation Tax Rate", cfg.tax_rate, pct_fmt),
        ("Tax Payment Lag (Years)", cfg.tax_lag, "0"),
    ]
    for idx, (label, val, num_fmt) in enumerate(assumptions, start=4):
        ws[f"A{idx}"] = label
        ws[f"A{idx}"].font = regular_font
        ws[f"B{idx}"] = val
        ws[f"B{idx}"].font = input_font
        ws[f"B{idx}"].number_format = num_fmt

    # --- Section 2: Master Nominal Cash Flow Schedule ---
    ws["A9"] = "2. MASTER NOMINAL CASH FLOW SCHEDULE ($)"
    ws["A9"].font = section_font

    ws["A10"] = "Cash Flow Line Item"
    ws["A10"].font = header_font
    ws["A10"].fill = navy_fill
    ws["A10"].alignment = Alignment(horizontal="left", indent=1)

    for yr in range(total_years + 1):
        col_ltr = get_column_letter(2 + yr)
        cell = ws[f"{col_ltr}10"]
        cell.value = f"Year {yr}"
        cell.font = header_font
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="right")

    # Populate Cash Flow Rows (Rows 11 to 21)
    row_map = [
        (11, "Sales Revenue", "Sales_Revenue", False),
        (12, "Variable Costs", "Variable_Costs", False),
        (13, "Fixed Operating Costs", "Fixed_Costs", False),
        (14, "Operating Cash Flow", None, True),
        (15, "Tax on Operating Cash Flow", "Tax_on_Op_CF", False),
        (16, "TAD Tax Shield", "TAD_Tax_Shield", False),
        (17, "CapEx & Scrap Proceeds", "CapEx_and_Scrap", False),
        (18, "Working Capital Cash Flow", "Working_Capital", False),
        (19, "Net Nominal Cash Flow", None, True),
    ]

    for row_idx, label, df_col, is_subtotal in row_map:
        ws[f"A{row_idx}"] = label
        ws[f"A{row_idx}"].font = bold_font if is_subtotal else regular_font
        ws[f"A{row_idx}"].alignment = Alignment(horizontal="left", indent=1)
        if is_subtotal:
            ws[f"A{row_idx}"].fill = total_fill
            ws[f"A{row_idx}"].border = double_bottom if row_idx == 19 else thin_border

        for yr in range(total_years + 1):
            col_ltr = get_column_letter(2 + yr)
            cell = ws[f"{col_ltr}{row_idx}"]
            if row_idx == 14:
                cell.value = f"=SUM({col_ltr}11:{col_ltr}13)"
            elif row_idx == 19:
                cell.value = f"=SUM({col_ltr}14:{col_ltr}18)"
            else:
                cell.value = float(df.loc[yr, df_col])

            cell.font = bold_font if is_subtotal else regular_font
            cell.number_format = currency_fmt
            if is_subtotal:
                cell.fill = total_fill
                cell.border = double_bottom if row_idx == 19 else thin_border

    # Row 20: Live Discount Factor Formula
    ws["A20"] = "Discount Factor @ Nominal WACC"
    ws["A20"].font = regular_font
    ws["A20"].alignment = Alignment(horizontal="left", indent=1)
    for yr in range(total_years + 1):
        col_ltr = get_column_letter(2 + yr)
        cell = ws[f"{col_ltr}20"]
        cell.value = f"=(1+$B$4)^-{yr}"
        cell.font = regular_font
        cell.number_format = df_fmt

    # Row 21: Live Present Value Formula
    ws["A21"] = "Present Value of Cash Flow"
    ws["A21"].font = bold_font
    ws["A21"].fill = sub_fill
    ws["A21"].border = double_bottom
    ws["A21"].alignment = Alignment(horizontal="left", indent=1)
    for yr in range(total_years + 1):
        col_ltr = get_column_letter(2 + yr)
        cell = ws[f"{col_ltr}21"]
        cell.value = f"={col_ltr}19*{col_ltr}20"
        cell.font = bold_font
        cell.fill = sub_fill
        cell.border = double_bottom
        cell.number_format = currency_fmt

    # --- Section 3: Live Investment Appraisal Summary ---
    ws["A23"] = "3. EXECUTIVE APPRAISAL METRICS (DYNAMIC EXCEL FORMULAS)"
    ws["A23"].font = section_font

    y1_col = "C"
    metrics = [
        (24, "Net Present Value (NPV)", f"=B19+NPV(B4,{y1_col}19:{last_col_ltr}19)", currency_fmt),
        (25, "Internal Rate of Return (IRR)", f'=IFERROR(IRR(B19:{last_col_ltr}19),"N/A")', pct_fmt),
        (26, "MIRR (ACCA Formula Sheet - Operational Life n)", f"=((NPV(B4,{y1_col}19:{last_col_ltr}19)/ABS(B19))^(1/B5))*(1+B4)-1", pct_fmt),
        (27, "MIRR (Excel Built-In - Full Cash Flow Horizon)", f"=MIRR(B19:{last_col_ltr}19,B4,B4)", pct_fmt),
        (28, "Strategic Recommendation", '=IF(B24>0,"ACCEPT PROJECT (Value Accretive)","REJECT PROJECT (Value Destructive)")', "@"),
    ]

    for row_idx, label, formula, num_fmt in metrics:
        ws[f"A{row_idx}"] = label
        ws[f"A{row_idx}"].font = bold_font
        ws[f"B{row_idx}"] = formula
        ws[f"B{row_idx}"].font = bold_font
        ws[f"B{row_idx}"].number_format = num_fmt
        ws[f"B{row_idx}"].fill = total_fill
        ws[f"B{row_idx}"].border = thin_border

    # Auto-fit column widths cleanly
    ws.column_dimensions["A"].width = 44
    for yr in range(total_years + 1):
        col_ltr = get_column_letter(2 + yr)
        ws.column_dimensions[col_ltr].width = 16

    wb.save(output_path)
    return output_path