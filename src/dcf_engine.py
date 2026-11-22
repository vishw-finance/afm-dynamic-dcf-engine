from dataclasses import dataclass, field
from typing import List, Union, Dict, Optional
import pandas as pd
import numpy_financial as npf


@dataclass
class DCFProjectConfig:
    """Configuration schema for an ACCA AFM Dynamic DCF Appraisal."""
    project_name: str
    project_life: int                       # Operational life in years (n)
    capex: float                            # Initial Year 0 capital expenditure
    scrap_value: float = 0.0                # Disposal proceeds at end of Year n
    additional_capex: Dict[int, float] = field(default_factory=dict)  # {year: outflow}

    # Sales & Cost Drivers (units can be a single int/float or a list per operational year)
    units: Union[int, float, List[float]] = 0
    selling_price: float = 0.0
    price_base: str = "Y1"                  # "Y0" (current prices) or "Y1" (Year 1 prices)
    price_inflation: float = 0.0

    variable_cost: float = 0.0
    var_cost_base: str = "Y0"               # "Y0" or "Y1"
    var_cost_inflation: float = 0.0

    fixed_costs: float = 0.0
    fixed_cost_base: str = "Y0"             # "Y0" or "Y1"
    fixed_cost_inflation: float = 0.0

    # Working Capital ("Security Deposit" Rule)
    initial_wc: float = 0.0
    wc_inflation: float = 0.0

    # Taxation & Tax-Allowable Depreciation (TAD)
    tax_rate: float = 0.20
    tax_lag: int = 1                        # 0 = paid in same year, 1 = 1 year in arrears
    tad_rate: float = 0.25
    tad_method: str = "reducing_balance"    # "reducing_balance" or "straight_line"

    # Discount Rate (Fisher Equation applied automatically if discount_rate_type == "real")
    wacc: float = 0.10
    discount_rate_type: str = "nominal"     # "nominal" or "real"
    general_inflation: float = 0.0


class DynamicDCFEngine:
    """Executes multi-year nominal cash flow forecasting and investment appraisal."""

    def __init__(self, config: DCFProjectConfig):
        self.cfg = config
        self._validate_inputs()
        self.nominal_wacc = self._resolve_nominal_wacc()
        self.total_horizon = self.cfg.project_life + self.cfg.tax_lag

    def _validate_inputs(self) -> None:
        if self.cfg.project_life < 1:
            raise ValueError("project_life must be at least 1 year.")
        if self.cfg.price_base not in ("Y0", "Y1") or self.cfg.var_cost_base not in ("Y0", "Y1"):
            raise ValueError("Inflation base must be either 'Y0' or 'Y1'.")
        if self.cfg.discount_rate_type not in ("nominal", "real"):
            raise ValueError("discount_rate_type must be 'nominal' or 'real'.")
        if self.cfg.tad_method not in ("reducing_balance", "straight_line"):
            raise ValueError("tad_method must be 'reducing_balance' or 'straight_line'.")
        if isinstance(self.cfg.units, list) and len(self.cfg.units) != self.cfg.project_life:
            raise ValueError(f"units list length ({len(self.cfg.units)}) must match project_life ({self.cfg.project_life}).")

    def _resolve_nominal_wacc(self) -> float:
        """Applies the Fisher Equation (1+i) = (1+r)(1+h) if a real WACC is provided."""
        if self.cfg.discount_rate_type == "real":
            return (1.0 + self.cfg.wacc) * (1.0 + self.cfg.general_inflation) - 1.0
        return self.cfg.wacc

    def _get_annual_units(self) -> List[float]:
        if isinstance(self.cfg.units, (int, float)):
            return [float(self.cfg.units)] * self.cfg.project_life
        return [float(u) for u in self.cfg.units]

    @staticmethod
    def _inflate(base_amount: float, rate: float, year: int, base_type: str) -> float:
        exponent = year if base_type == "Y0" else (year - 1)
        return base_amount * ((1.0 + rate) ** exponent)

    def run(self) -> Dict:
        """Builds the complete cash flow schedule and computes NPV, IRR, and MIRR."""
        cols = self.total_horizon + 1  # Includes Year 0
        years = list(range(cols))

        sales = [0.0] * cols
        var_costs = [0.0] * cols
        fixed_costs = [0.0] * cols
        op_cf = [0.0] * cols
        tax_on_op = [0.0] * cols
        tad_schedule = [0.0] * cols
        tad_shield = [0.0] * cols
        capex_scrap = [0.0] * cols
        wc_cf = [0.0] * cols

        # 1. CapEx & Scrap Schedule
        capex_scrap[0] = -self.cfg.capex
        for yr, amount in self.cfg.additional_capex.items():
            if 0 <= yr <= self.cfg.project_life:
                capex_scrap[yr] -= amount
        capex_scrap[self.cfg.project_life] += self.cfg.scrap_value

        # 2. Specific Inflation & Operating Cash Flows (Years 1 to n)
        annual_units = self._get_annual_units()
        for t in range(1, self.cfg.project_life + 1):
            u = annual_units[t - 1]
            p_t = self._inflate(self.cfg.selling_price, self.cfg.price_inflation, t, self.cfg.price_base)
            vc_t = self._inflate(self.cfg.variable_cost, self.cfg.var_cost_inflation, t, self.cfg.var_cost_base)
            fc_t = self._inflate(self.cfg.fixed_costs, self.cfg.fixed_cost_inflation, t, self.cfg.fixed_cost_base)

            sales[t] = u * p_t
            var_costs[t] = -(u * vc_t)
            fixed_costs[t] = -fc_t
            op_cf[t] = sales[t] + var_costs[t] + fixed_costs[t]

            # Corporation tax on operating cash flow (shifted by tax_lag)
            tax_on_op[t + self.cfg.tax_lag] = -op_cf[t] * self.cfg.tax_rate

        # 3. Tax-Allowable Depreciation (TAD) & Balancing Adjustment
        total_depreciable_base = self.cfg.capex + sum(self.cfg.additional_capex.values())
        wdv = total_depreciable_base
        annual_sl_tad = (total_depreciable_base - self.cfg.scrap_value) / self.cfg.project_life

        for t in range(1, self.cfg.project_life + 1):
            if t < self.cfg.project_life:
                tad = (wdv * self.cfg.tad_rate) if self.cfg.tad_method == "reducing_balance" else annual_sl_tad
                wdv -= tad
            else:
                # Final year balancing allowance / (charge)
                tad = wdv - self.cfg.scrap_value
                wdv = 0.0

            tad_schedule[t] = tad
            tad_shield[t + self.cfg.tax_lag] = tad * self.cfg.tax_rate

        # 4. Working Capital ("Security Deposit" Incremental Flows)
        prev_wc = 0.0
        for t in range(self.cfg.project_life):
            req_wc = self.cfg.initial_wc * ((1.0 + self.cfg.wc_inflation) ** t)
            wc_cf[t] = -(req_wc - prev_wc)
            prev_wc = req_wc
        wc_cf[self.cfg.project_life] += prev_wc  # Full release at end of operational life

        # 5. Net Nominal Cash Flow, Discount Factors & Present Values
        net_cf = [
            op_cf[t] + tax_on_op[t] + tad_shield[t] + capex_scrap[t] + wc_cf[t]
            for t in years
        ]
        discount_factors = [(1.0 + self.nominal_wacc) ** (-t) for t in years]
        present_values = [net_cf[t] * discount_factors[t] for t in years]

        # 6. Appraisal Metrics
        npv = sum(present_values)
        irr = float(npf.irr(net_cf))

        # ACCA Formula-Sheet MIRR (uses operational life n = project_life)
        pv_i = abs(present_values[0])
        pv_r = sum(present_values[1:])
        mirr_acca = ((pv_r / pv_i) ** (1.0 / self.cfg.project_life)) * (1.0 + self.nominal_wacc) - 1.0

        # Excel Built-In MIRR (uses total_horizon including trailing tax years)
        mirr_excel = float(npf.mirr(net_cf, self.nominal_wacc, self.nominal_wacc))

        df_schedule = pd.DataFrame({
            "Year": years,
            "Sales_Revenue": sales,
            "Variable_Costs": var_costs,
            "Fixed_Costs": fixed_costs,
            "Operating_CF": op_cf,
            "Tax_on_Op_CF": tax_on_op,
            "TAD_Tax_Shield": tad_shield,
            "CapEx_and_Scrap": capex_scrap,
            "Working_Capital": wc_cf,
            "Net_Nominal_CF": net_cf,
            "Discount_Factor": discount_factors,
            "Present_Value": present_values,
        })

        return {
            "config": self.cfg,
            "schedule": df_schedule,
            "nominal_wacc": self.nominal_wacc,
            "npv": npv,
            "irr": irr,
            "mirr_acca": mirr_acca,
            "mirr_excel": mirr_excel,
            "decision": "ACCEPT" if npv > 0 else "REJECT",
        }