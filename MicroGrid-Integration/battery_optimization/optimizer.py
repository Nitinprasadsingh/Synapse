"""
Pyomo MILP Battery Scheduling Optimizer for MicroGrid Battery Optimization.

This module implements a Mixed-Integer Linear Program (MILP) for optimal
battery energy storage system (BESS) scheduling over a rolling planning horizon.
The optimizer co-optimises grid import, grid export, PV curtailment, and
battery charge/discharge decisions to minimise total operating cost while
respecting all physical and operational constraints.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

from battery_optimization.exceptions import ConfigurationError, OptimizationError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BatteryOptimizer
# ---------------------------------------------------------------------------

class BatteryOptimizer:
    """
    MILP-based battery scheduling optimiser powered by Pyomo + HiGHS.

    Parameters
    ----------
    config : dict
        System configuration dictionary.  The following keys are consumed
        (all others are silently ignored):

        Battery parameters
        ------------------
        MAX_CHARGE_POWER_KW       float  – maximum charge rate (kW)
        MAX_DISCHARGE_POWER_KW    float  – maximum discharge rate (kW)
        BATTERY_CAPACITY_KWH      float  – nameplate capacity (kWh)
        MIN_SOC_PERCENT           float  – minimum SOC as a fraction [0, 1]
        MAX_SOC_PERCENT           float  – maximum SOC as a fraction [0, 1]
        CHARGE_EFFICIENCY         float  – round-trip charge efficiency [0, 1]
        DISCHARGE_EFFICIENCY      float  – round-trip discharge efficiency [0, 1]
        DEGRADATION_COST_PER_KWH  float  – battery wear cost ($/kWh throughput)

        Grid parameters
        ---------------
        GRID_IMPORT_LIMIT_KW      float  – maximum grid import power (kW)
        GRID_EXPORT_LIMIT_KW      float  – maximum grid export power (kW)

        Tariff / cost parameters
        ------------------------
        EXPORT_TARIFF             float  – flat export revenue ($/kWh)
        CURTAILMENT_PENALTY       float  – curtailment penalty ($/kWh)

        Optimisation horizon
        --------------------
        OPTIMIZATION_HORIZON_HOURS int   – number of hourly time steps
        DT                        float  – time-step duration in hours (default 1.0)
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self._validate_config()

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def _validate_config(self) -> None:
        """Raise ConfigurationError for missing or obviously invalid keys."""
        required = [
            "MAX_CHARGE_POWER_KW",
            "MAX_DISCHARGE_POWER_KW",
            "BATTERY_CAPACITY_KWH",
            "MIN_SOC_PERCENT",
            "MAX_SOC_PERCENT",
            "CHARGE_EFFICIENCY",
            "DISCHARGE_EFFICIENCY",
            "DEGRADATION_COST_PER_KWH",
            "GRID_IMPORT_LIMIT_KW",
            "GRID_EXPORT_LIMIT_KW",
            "EXPORT_TARIFF",
            "CURTAILMENT_PENALTY",
            "OPTIMIZATION_HORIZON_HOURS",
        ]
        missing = [k for k in required if k not in self.config]
        if missing:
            raise ConfigurationError(
                f"Missing required configuration keys: {missing}"
            )

        cap = self.config["BATTERY_CAPACITY_KWH"]
        if cap <= 0:
            raise ConfigurationError("BATTERY_CAPACITY_KWH must be positive.")

        for eff_key in ("CHARGE_EFFICIENCY", "DISCHARGE_EFFICIENCY"):
            eff = self.config[eff_key]
            if not (0 < eff <= 1):
                raise ConfigurationError(
                    f"{eff_key} must be in (0, 1]. Got {eff}."
                )

    @property
    def _T(self) -> int:
        return int(self.config["OPTIMIZATION_HORIZON_HOURS"])

    @property
    def _dt(self) -> float:
        return float(self.config.get("DT", 1.0))

    @property
    def _capacity(self) -> float:
        return float(self.config["BATTERY_CAPACITY_KWH"])

    @property
    def _min_soc_kwh(self) -> float:
        return self._capacity * float(self.config["MIN_SOC_PERCENT"])

    @property
    def _max_soc_kwh(self) -> float:
        return self._capacity * float(self.config["MAX_SOC_PERCENT"])

    @property
    def _max_charge_kw(self) -> float:
        return float(self.config["MAX_CHARGE_POWER_KW"])

    @property
    def _max_discharge_kw(self) -> float:
        return float(self.config["MAX_DISCHARGE_POWER_KW"])

    @property
    def _charge_eff(self) -> float:
        return float(self.config["CHARGE_EFFICIENCY"])

    @property
    def _discharge_eff(self) -> float:
        return float(self.config["DISCHARGE_EFFICIENCY"])

    @property
    def _grid_import_limit(self) -> float:
        return float(self.config["GRID_IMPORT_LIMIT_KW"])

    @property
    def _grid_export_limit(self) -> float:
        return float(self.config["GRID_EXPORT_LIMIT_KW"])

    @property
    def _export_tariff(self) -> float:
        return float(self.config["EXPORT_TARIFF"])

    @property
    def _degradation_cost(self) -> float:
        return float(self.config["DEGRADATION_COST_PER_KWH"])

    @property
    def _curtailment_penalty(self) -> float:
        return float(self.config["CURTAILMENT_PENALTY"])

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    def _validate_inputs(
        self,
        pv_forecast_kw: List[float],
        load_forecast_kw: List[float],
        import_tariffs: List[float],
    ) -> None:
        """Check that all forecast arrays have the correct length."""
        T = self._T
        for name, arr in [
            ("pv_forecast_kw", pv_forecast_kw),
            ("load_forecast_kw", load_forecast_kw),
            ("import_tariffs", import_tariffs),
        ]:
            if len(arr) != T:
                raise ConfigurationError(
                    f"'{name}' has length {len(arr)} but "
                    f"OPTIMIZATION_HORIZON_HOURS={T}."
                )
            if any(float(value) < 0 for value in arr):
                raise ConfigurationError(f"'{name}' cannot contain negative values.")

    # ------------------------------------------------------------------
    # Model building
    # ------------------------------------------------------------------

    def build_model(
        self,
        pv_forecast_kw: List[float],
        load_forecast_kw: List[float],
        initial_soc_kwh: float,
        import_tariffs: List[float],
        export_tariff: float,
        allow_export: bool = True,
        terminal_soc_kwh: Optional[float] = None,
    ) -> pyo.ConcreteModel:
        """
        Build and return a Pyomo ConcreteModel for the battery scheduling MILP.

        The returned model is not yet solved; call :meth:`solve` to optimise it.

        Parameters
        ----------
        pv_forecast_kw : list[float]
            Hourly PV generation forecast (kW), length T.
        load_forecast_kw : list[float]
            Hourly load forecast (kW), length T.
        initial_soc_kwh : float
            Battery state-of-charge at the start of the horizon (kWh).
        import_tariffs : list[float]
            Time-of-use import tariff ($/kWh) per time step, length T.
        export_tariff : float
            Flat export tariff ($/kWh).
        allow_export : bool
            Whether grid export is allowed.  If False the GridExport upper
            bound is forced to zero.
        terminal_soc_kwh : float, optional
            Minimum required SOC at the final time step.  Defaults to
            ``initial_soc_kwh`` (energy-neutral constraint).

        Returns
        -------
        pyo.ConcreteModel
        """
        self._validate_inputs(pv_forecast_kw, load_forecast_kw, import_tariffs)

        if terminal_soc_kwh is None:
            terminal_soc_kwh = initial_soc_kwh

        # Clamp initial / terminal SOC to feasible range
        initial_soc_kwh = float(
            np.clip(initial_soc_kwh, self._min_soc_kwh, self._max_soc_kwh)
        )
        terminal_soc_kwh = float(
            np.clip(terminal_soc_kwh, self._min_soc_kwh, self._max_soc_kwh)
        )

        T = self._T
        dt = self._dt

        model = pyo.ConcreteModel(name="BatteryScheduling")

        # ----------------------------------------------------------
        # Sets
        # ----------------------------------------------------------
        model.T = pyo.Set(initialize=range(T), ordered=True)

        # ----------------------------------------------------------
        # Parameters (store forecasts / tariffs on the model for
        # later result extraction without passing them around)
        # ----------------------------------------------------------
        model.pv_kw = pyo.Param(model.T, initialize=dict(enumerate(pv_forecast_kw)))
        model.load_kw = pyo.Param(model.T, initialize=dict(enumerate(load_forecast_kw)))
        model.import_tariff = pyo.Param(model.T, initialize=dict(enumerate(import_tariffs)))
        model.export_tariff = pyo.Param(initialize=export_tariff)
        model.initial_soc = pyo.Param(initialize=initial_soc_kwh)
        model.terminal_soc = pyo.Param(initialize=terminal_soc_kwh)

        # ----------------------------------------------------------
        # Decision variables
        # ----------------------------------------------------------
        model.Charge = pyo.Var(
            model.T, domain=pyo.NonNegativeReals,
            bounds=(0, self._max_charge_kw)
        )
        model.Discharge = pyo.Var(
            model.T, domain=pyo.NonNegativeReals,
            bounds=(0, self._max_discharge_kw)
        )
        model.GridImport = pyo.Var(
            model.T, domain=pyo.NonNegativeReals,
            bounds=(0, self._grid_import_limit)
        )

        # Export upper bound: 0 when export is disabled
        export_ub = self._grid_export_limit if allow_export else 0.0
        model.GridExport = pyo.Var(
            model.T, domain=pyo.NonNegativeReals,
            bounds=(0, export_ub)
        )

        # Curtailment bounded above by PV forecast per time step
        def _curtail_bounds(m, t):
            return (0, m.pv_kw[t])
        model.Curtailment = pyo.Var(model.T, domain=pyo.NonNegativeReals,
                                    bounds=_curtail_bounds)

        model.SOC = pyo.Var(
            model.T, domain=pyo.NonNegativeReals,
            bounds=(self._min_soc_kwh, self._max_soc_kwh)
        )

        # Binary variables: 1 → charging / discharging at time step t
        model.Charge_binary = pyo.Var(model.T, domain=pyo.Binary)
        model.Discharge_binary = pyo.Var(model.T, domain=pyo.Binary)

        # ----------------------------------------------------------
        # Constraints
        # ----------------------------------------------------------

        # 1. Power balance
        def _power_balance(m, t):
            return (
                m.pv_kw[t] + m.GridImport[t] + m.Discharge[t]
                == m.load_kw[t] + m.Charge[t] + m.GridExport[t] + m.Curtailment[t]
            )
        model.PowerBalance = pyo.Constraint(model.T, rule=_power_balance)

        # 2a. SOC initialisation
        model.SOC_init = pyo.Constraint(
            expr=model.SOC[0] == model.initial_soc
        )

        # 2b. SOC dynamics
        def _soc_dynamics(m, t):
            if t == T - 1:
                return pyo.Constraint.Skip
            return (
                m.SOC[t + 1]
                == m.SOC[t]
                + self._charge_eff * m.Charge[t] * dt
                - m.Discharge[t] * dt / self._discharge_eff
            )
        model.SOC_dynamics = pyo.Constraint(model.T, rule=_soc_dynamics)

        # 3a. Charge bounded by binary
        def _charge_binary_link(m, t):
            return m.Charge[t] <= self._max_charge_kw * m.Charge_binary[t]
        model.ChargeBinaryLink = pyo.Constraint(model.T, rule=_charge_binary_link)

        # 3b. Discharge bounded by binary
        def _discharge_binary_link(m, t):
            return m.Discharge[t] <= self._max_discharge_kw * m.Discharge_binary[t]
        model.DischargeBinaryLink = pyo.Constraint(model.T, rule=_discharge_binary_link)

        # 3c. Mutual exclusion of charge and discharge
        def _mutual_exclusion(m, t):
            return m.Charge_binary[t] + m.Discharge_binary[t] <= 1
        model.MutualExclusion = pyo.Constraint(model.T, rule=_mutual_exclusion)

        # 4. Terminal SOC constraint
        model.TerminalSOC = pyo.Constraint(
            expr=model.SOC[T - 1] >= model.terminal_soc
        )

        # ----------------------------------------------------------
        # Objective: minimise total operating cost
        # ----------------------------------------------------------
        def _objective(m):
            cost = 0
            for t in m.T:
                cost += (
                    # Grid import cost
                    m.GridImport[t] * dt * m.import_tariff[t]
                    # Grid export revenue (negative cost)
                    - m.GridExport[t] * dt * m.export_tariff
                    # Battery wear (degradation)
                    + (m.Charge[t] + m.Discharge[t]) * dt * self._degradation_cost
                    # PV curtailment penalty
                    + m.Curtailment[t] * dt * self._curtailment_penalty
                )
            return cost

        model.Objective = pyo.Objective(rule=_objective, sense=pyo.minimize)

        return model

    # ------------------------------------------------------------------
    # Solver
    # ------------------------------------------------------------------

    def _get_solver(self) -> Any:
        """
        Return a configured HiGHS solver instance.

        Raises
        ------
        OptimizationError
            If neither ``appsi_highs`` nor the AMPL ``highs`` interface is
            available on this system.
        """
        try:
            solver = pyo.SolverFactory("appsi_highs")
            if solver.available():
                logger.debug("Using Pyomo APPSI HiGHS solver.")
                return solver
        except Exception as exc:
            logger.warning("appsi_highs setup failed: %s", exc)

        # Fallback: standard HiGHS interface (requires highs executable)
        try:
            solver = pyo.SolverFactory("highs")
            if solver.available():
                logger.debug("Using standard HiGHS solver (executable).")
                return solver
        except Exception as exc:
            logger.warning("highs fallback failed: %s", exc)

        raise OptimizationError(
            "HiGHS solver not available.  "
            "Ensure 'highspy' is installed (`pip install highspy`) or that the "
            "HiGHS executable is on your PATH."
        )

    def solve(self, model: pyo.ConcreteModel) -> Dict[str, Any]:
        """
        Solve a pre-built Pyomo model and return a status dictionary.

        Parameters
        ----------
        model : pyo.ConcreteModel
            A model returned by :meth:`build_model`.

        Returns
        -------
        dict
            ``{"status": "optimal"|"infeasible"|...,
               "solver_status": str,
               "termination_condition": str,
               "objective_value": float | None}``

        Raises
        ------
        OptimizationError
            If the solver is unavailable or the problem is infeasible /
            unbounded.
        """
        solver = self._get_solver()

        try:
            result = solver.solve(model, tee=False)
        except Exception as exc:
            raise OptimizationError(f"Solver call failed: {exc}") from exc

        tc = result.solver.termination_condition
        ss = result.solver.status

        logger.info(
            "Solver finished – status=%s, termination=%s", ss, tc
        )

        # Map Pyomo termination conditions to a human-readable status
        if tc == TerminationCondition.optimal:
            status = "optimal"
        elif tc in (
            TerminationCondition.infeasible,
            TerminationCondition.infeasibleOrUnbounded,
        ):
            raise OptimizationError(
                f"Optimisation problem is infeasible "
                f"(termination condition: {tc}).  "
                "Check that initial/terminal SOC are within [MIN_SOC, MAX_SOC] "
                "and that load can be met by PV + grid within the given limits."
            )
        elif tc == TerminationCondition.unbounded:
            raise OptimizationError(
                "Optimisation problem is unbounded – check objective coefficients."
            )
        else:
            raise OptimizationError(
                f"Solver did not find an optimal solution "
                f"(status={ss}, termination={tc})."
            )

        try:
            obj_val = float(pyo.value(model.Objective))
        except Exception:
            obj_val = None

        return {
            "status": status,
            "solver_status": str(ss),
            "termination_condition": str(tc),
            "objective_value": obj_val,
        }

    # ------------------------------------------------------------------
    # Result extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _clip(value: float, threshold: float = 1e-6) -> float:
        """Return 0 if abs(value) < threshold, else value (removes numerical noise)."""
        return 0.0 if abs(value) < threshold else value

    def extract_results(
        self,
        model: pyo.ConcreteModel,
        pv_forecast_kw: List[float],
        load_forecast_kw: List[float],
        import_tariffs: List[float],
    ) -> pd.DataFrame:
        """
        Extract the solved decision-variable values into a DataFrame.

        Each row corresponds to one time step in the optimisation horizon.

        Parameters
        ----------
        model : pyo.ConcreteModel
            A *solved* model.
        pv_forecast_kw : list[float]
            PV forecast used to build the model (kW), length T.
        load_forecast_kw : list[float]
            Load forecast used to build the model (kW), length T.
        import_tariffs : list[float]
            Import tariff per time step ($/kWh), length T.

        Returns
        -------
        pd.DataFrame
            Columns: t, pv_kw, load_kw, charge_kw, discharge_kw, soc_kwh,
            soc_percent, grid_import_kw, grid_export_kw, curtailment_kw,
            import_tariff, grid_import_cost, grid_export_revenue,
            battery_degradation_cost, net_cost, battery_action.
        """
        T = self._T
        dt = self._dt
        cap = self._capacity
        rows = []

        for t in range(T):
            charge = self._clip(pyo.value(model.Charge[t]))
            discharge = self._clip(pyo.value(model.Discharge[t]))
            grid_import = self._clip(pyo.value(model.GridImport[t]))
            grid_export = self._clip(pyo.value(model.GridExport[t]))
            curtailment = self._clip(pyo.value(model.Curtailment[t]))
            soc = self._clip(pyo.value(model.SOC[t]))

            tariff = import_tariffs[t]
            export_rev = grid_export * dt * float(pyo.value(model.export_tariff))
            import_cost = grid_import * dt * tariff
            deg_cost = (charge + discharge) * dt * self._degradation_cost
            net_cost = import_cost - export_rev + deg_cost + curtailment * dt * self._curtailment_penalty

            # Battery action label
            if charge > 0.01:
                battery_action = "CHARGING"
            elif discharge > 0.01:
                battery_action = "DISCHARGING"
            else:
                battery_action = "IDLE"

            rows.append({
                "t": t,
                "pv_kw": pv_forecast_kw[t],
                "load_kw": load_forecast_kw[t],
                "charge_kw": charge,
                "discharge_kw": discharge,
                "soc_kwh": soc,
                "soc_percent": (soc / cap * 100.0) if cap > 0 else 0.0,
                "grid_import_kw": grid_import,
                "grid_export_kw": grid_export,
                "curtailment_kw": curtailment,
                "import_tariff": tariff,
                "grid_import_cost": import_cost,
                "grid_export_revenue": export_rev,
                "battery_degradation_cost": deg_cost,
                "net_cost": net_cost,
                "battery_action": battery_action,
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def optimize(
        self,
        pv_forecast_kw: List[float],
        load_forecast_kw: List[float],
        initial_soc_kwh: float,
        import_tariffs: Optional[List[float]] = None,
        export_tariffs: Optional[List[float]] = None,
        terminal_soc_kwh: Optional[float] = None,
        allow_export: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the full optimisation pipeline: build → solve → extract results.

        Parameters
        ----------
        pv_forecast_kw : list[float]
            Hourly PV generation forecast (kW), length T.
        load_forecast_kw : list[float]
            Hourly load forecast (kW), length T.
        initial_soc_kwh : float
            Battery SOC at the start of the horizon (kWh).
        import_tariffs : list[float], optional
            Time-of-use import tariff ($/kWh) per time step.  Defaults to
            the flat ``IMPORT_TARIFF`` value from config (or 0.12 $/kWh).
        terminal_soc_kwh : float, optional
            Minimum required SOC at the final time step.  Defaults to
            ``initial_soc_kwh``.
        allow_export : bool
            Whether grid export is permitted.

        Returns
        -------
        dict
            Keys: ``status``, ``solver_status``, ``objective_value``,
            ``schedule`` (list of per-timestep dicts with all decision
            variable values and cost components).
        """
        T = self._T

        # Default import tariffs
        if import_tariffs is None:
            flat_tariff = float(self.config.get("IMPORT_TARIFF", 0.12))
            import_tariffs = [flat_tariff] * T

        if export_tariffs is not None and len(export_tariffs) != T:
            raise ConfigurationError(
                f"'export_tariffs' has length {len(export_tariffs)} but horizon is {T}."
            )
        export_tariff = float(self.config.get("EXPORT_TARIFF", self._export_tariff))
        if export_tariffs is not None and len(set(export_tariffs)) > 1:
            raise ConfigurationError("The current model supports one flat export tariff.")

        # Build
        model = self.build_model(
            pv_forecast_kw=pv_forecast_kw,
            load_forecast_kw=load_forecast_kw,
            initial_soc_kwh=initial_soc_kwh,
            import_tariffs=import_tariffs,
            export_tariff=export_tariff,
            allow_export=allow_export,
            terminal_soc_kwh=terminal_soc_kwh,
        )

        # Solve
        solve_info = self.solve(model)

        # Extract
        df = self.extract_results(model, pv_forecast_kw, load_forecast_kw, import_tariffs)
        schedule = df.to_dict(orient="records")

        return {
            "status": solve_info["status"],
            "solver_status": solve_info["solver_status"],
            "objective_value": solve_info["objective_value"],
            "schedule": schedule,
            "battery_charge_kw": df["charge_kw"].tolist(),
            "battery_discharge_kw": df["discharge_kw"].tolist(),
            "grid_import_kw": df["grid_import_kw"].tolist(),
            "grid_export_kw": df["grid_export_kw"].tolist(),
            "solar_curtailment_kw": df["curtailment_kw"].tolist(),
            "battery_degradation_cost": df["battery_degradation_cost"].tolist(),
        }

    # ------------------------------------------------------------------
    # Feasibility checker
    # ------------------------------------------------------------------

    def check_feasibility(
        self,
        model: pyo.ConcreteModel,
        tolerance: float = 1e-4,
    ) -> Dict[str, Any]:
        """
        Verify that power-balance constraints hold within *tolerance*.

        Parameters
        ----------
        model : pyo.ConcreteModel
            A solved Pyomo model.
        tolerance : float
            Acceptable absolute violation per time step (kW).

        Returns
        -------
        dict
            ``{"feasible": bool, "max_violation": float,
               "violations": list[dict]}``
            where each violation dict has keys ``t``, ``lhs``, ``rhs``,
            and ``violation``.
        """
        violations = []

        for t in range(self._T):
            lhs = (
                pyo.value(model.pv_kw[t])
                + pyo.value(model.GridImport[t])
                + pyo.value(model.Discharge[t])
            )
            rhs = (
                pyo.value(model.load_kw[t])
                + pyo.value(model.Charge[t])
                + pyo.value(model.GridExport[t])
                + pyo.value(model.Curtailment[t])
            )
            viol = abs(lhs - rhs)
            if viol > tolerance:
                violations.append({"t": t, "lhs": lhs, "rhs": rhs, "violation": viol})

        max_viol = max((v["violation"] for v in violations), default=0.0)
        return {
            "feasible": len(violations) == 0,
            "max_violation": max_viol,
            "violations": violations,
        }
