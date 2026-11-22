from src.dcf_engine import DCFProjectConfig, DynamicDCFEngine
from src.excel_exporter import export_dcf_to_excel


def get_preset_apex() -> DCFProjectConfig:
    """Apex Co 2-Year Production Case (Real WACC + Specific Inflation + 1-Yr Tax Lag)."""
    return DCFProjectConfig(
        project_name="Apex Co - 2-Year Production Expansion",
        project_life=2,
        capex=200_000,
        scrap_value=60_000,
        units=5_000,
        selling_price=80.0,
        price_base="Y1",
        price_inflation=0.05,
        variable_cost=40.0,
        var_cost_base="Y0",
        var_cost_inflation=0.10,
        initial_wc=50_000,
        wc_inflation=0.05,
        tax_rate=0.20,
        tax_lag=1,
        tad_rate=0.25,
        tad_method="reducing_balance",
        wacc=0.10,
        discount_rate_type="real",
        general_inflation=0.05,
    )


def get_custom_config() -> DCFProjectConfig:
    """Prompts user for dynamic project inputs via CLI."""
    print("\n--- Custom Dynamic DCF Configuration ---")
    name = input("Project Name: ").strip() or "Custom Capital Project"
    life = int(input("Operational Project Life (years): "))
    capex = float(input("Initial CapEx at Year 0 ($): "))
    scrap = float(input("Scrap / Residual Value at End of Project ($): "))
    units = float(input("Annual Sales Volume (units): "))

    price = float(input("Selling Price per Unit ($): "))
    p_base = input("Selling Price Base ('Y0' for current prices / 'Y1' for Year 1 prices): ").strip().upper()
    p_inf = float(input("Selling Price Annual Inflation (e.g., 0.05 for 5%): "))

    vc = float(input("Variable Cost per Unit ($): "))
    vc_base = input("Variable Cost Base ('Y0' or 'Y1'): ").strip().upper()
    vc_inf = float(input("Variable Cost Annual Inflation (e.g., 0.10 for 10%): "))

    fc = float(input("Annual Fixed Costs ($): "))
    fc_base = input("Fixed Cost Base ('Y0' or 'Y1'): ").strip().upper()
    fc_inf = float(input("Fixed Cost Annual Inflation (e.g., 0.04 for 4%): "))

    wc = float(input("Initial Working Capital at Year 0 ($): "))
    wc_inf = float(input("Working Capital Annual Inflation (e.g., 0.05 for 5%): "))

    tax_rate = float(input("Corporation Tax Rate (e.g., 0.20 for 20%): "))
    tax_lag = int(input("Tax Lag in Years (0 = same year, 1 = 1 year in arrears): "))
    tad_rate = float(input("Tax-Allowable Depreciation Rate (e.g., 0.25 for 25%): "))

    rate_type = input("Discount Rate Type ('nominal' or 'real'): ").strip().lower()
    wacc = float(input(f"Enter {rate_type.capitalize()} WACC (e.g., 0.12 for 12%): "))
    gen_inf = float(input("General Inflation Rate (needed if Real WACC, else 0): ")) if rate_type == "real" else 0.0

    return DCFProjectConfig(
        project_name=name,
        project_life=life,
        capex=capex,
        scrap_value=scrap,
        units=units,
        selling_price=price,
        price_base=p_base,
        price_inflation=p_inf,
        variable_cost=vc,
        var_cost_base=vc_base,
        var_cost_inflation=vc_inf,
        fixed_costs=fc,
        fixed_cost_base=fc_base,
        fixed_cost_inflation=fc_inf,
        initial_wc=wc,
        wc_inflation=wc_inf,
        tax_rate=tax_rate,
        tax_lag=tax_lag,
        tad_rate=tad_rate,
        wacc=wacc,
        discount_rate_type=rate_type,
        general_inflation=gen_inf,
    )


def main():
    print("=" * 62)
    print("  ACCA AFM DYNAMIC DCF & CAPITAL APPRAISAL ENGINE")
    print("=" * 62)
    print("1. Run Preset Case: Apex Co (2-Year Project + Real WACC + Tax Lag)")
    print("2. Enter Custom Project Parameters Interactively")
    choice = input("\nSelect option (1 or 2): ").strip()

    config = get_custom_config() if choice == "2" else get_preset_apex()
    engine = DynamicDCFEngine(config)
    results = engine.run()

    print(f"\n--- Master Cash Flow Schedule: {config.project_name} ---")
    print(results["schedule"].to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

    print("\n--- Executive Valuation Summary ---")
    print(f"Nominal Discount Rate (WACC): {results['nominal_wacc']:.2%}")
    print(f"Net Present Value (NPV):      ${results['npv']:,.2f}")
    print(f"Internal Rate of Return:      {results['irr']:.2%}")
    print(f"MIRR (ACCA Operational Life): {results['mirr_acca']:.2%}")
    print(f"MIRR (Excel Full Horizon):    {results['mirr_excel']:.2%}")
    print(f"Board Decision:               {results['decision']}")

    safe_filename = config.project_name.lower().replace(" ", "_").replace("-", "") + ".xlsx"
    excel_path = export_dcf_to_excel(results, f"outputs/{safe_filename}")
    print(f"\nDynamic Excel model exported to: {excel_path}")


if __name__ == "__main__":
    main()