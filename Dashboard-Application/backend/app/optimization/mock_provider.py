import uuid
from datetime import datetime, timezone
from typing import Optional, List
from app.optimization.interfaces import BatteryOptimizationProvider
from app.schemas.forecast import PVForecastResponse, LoadForecastResponse
from app.schemas.battery import (
    BatteryConfigSchema,
    BatteryScheduleResponse,
    BatteryScheduleStepSchema
)
from app.schemas.grid import GridConfigSchema


class MockBatteryOptimizationProvider(BatteryOptimizationProvider):
    """
    Mock heuristic rule-based scheduling provider that enforces strict physical energy conservation
    and battery constraints (capacity, SOC bounds, charge/discharge rates, and efficiencies).
    """

    def generate_schedule(
        self,
        pv_forecast: PVForecastResponse,
        load_forecast: LoadForecastResponse,
        battery_config: BatteryConfigSchema,
        grid_config: GridConfigSchema,
        current_soc: Optional[float] = None,
        horizon_hours: int = 24
    ) -> BatteryScheduleResponse:
        steps: List[BatteryScheduleStepSchema] = []
        schedule_id = f"SCHED-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)

        soc = current_soc if current_soc is not None else battery_config.initial_soc
        # Clamp initial SOC between min and max
        soc = max(battery_config.min_soc, min(battery_config.max_soc, soc))
        capacity = battery_config.capacity_kwh
        total_cost = 0.0

        num_steps = min(
            horizon_hours,
            len(pv_forecast.forecast_points),
            len(load_forecast.forecast_points)
        )

        for i in range(num_steps):
            pv_pt = pv_forecast.forecast_points[i]
            load_pt = load_forecast.forecast_points[i]
            ts = pv_pt.timestamp

            pv_kw = pv_pt.value_kw
            load_kw = load_pt.value_kw
            net_power = pv_kw - load_kw  # positive = surplus, negative = deficit

            soc_before = round(soc, 2)
            action = "IDLE"
            battery_power_kw = 0.0
            grid_import_kw = 0.0
            grid_export_kw = 0.0

            # Delta time is 1 hour
            dt = 1.0

            if net_power > 0.05:
                # Surplus solar available -> attempt charging battery
                max_charge_power = min(net_power, battery_config.max_charge_kw)
                # Calculate how much energy battery can accept before reaching max_soc
                headroom_kwh = max(0.0, (battery_config.max_soc - soc) / 100.0 * capacity)
                # Power that can enter battery after charging efficiency
                max_battery_input_power = headroom_kwh / (dt * battery_config.charge_efficiency) if battery_config.charge_efficiency > 0 else 0.0
                actual_charge_kw = min(max_charge_power, max_battery_input_power)

                if actual_charge_kw > 0.1:
                    action = "CHARGE"
                    battery_power_kw = round(actual_charge_kw, 2)
                    energy_stored = actual_charge_kw * dt * battery_config.charge_efficiency
                    soc_gain = (energy_stored / capacity) * 100.0
                    soc = min(battery_config.max_soc, soc + soc_gain)
                else:
                    action = "IDLE"
                    battery_power_kw = 0.0

                # Any surplus remaining after charging goes to grid export
                surplus_remaining = net_power - battery_power_kw
                grid_export_kw = round(min(surplus_remaining, grid_config.export_limit_kw), 2)

            elif net_power < -0.05:
                # Deficit power needed by load -> attempt discharging battery
                deficit_kw = abs(net_power)
                max_discharge_power = min(deficit_kw, battery_config.max_discharge_kw)
                # Calculate available stored energy above min_soc
                available_kwh = max(0.0, (soc - battery_config.min_soc) / 100.0 * capacity)
                # Output power battery can provide considering discharging efficiency
                max_output_power = available_kwh * battery_config.discharge_efficiency / dt
                actual_discharge_kw = min(max_discharge_power, max_output_power)

                if actual_discharge_kw > 0.1:
                    action = "DISCHARGE"
                    battery_power_kw = round(actual_discharge_kw, 2)
                    energy_drawn = (actual_discharge_kw * dt) / battery_config.discharge_efficiency
                    soc_loss = (energy_drawn / capacity) * 100.0
                    soc = max(battery_config.min_soc, soc - soc_loss)
                else:
                    action = "IDLE"
                    battery_power_kw = 0.0

                # Remaining deficit must be supplied by grid import
                unmet_deficit = deficit_kw - battery_power_kw
                grid_import_kw = round(min(unmet_deficit, grid_config.import_limit_kw), 2)

            else:
                action = "IDLE"
                battery_power_kw = 0.0

            soc_after = round(soc, 2)

            # Step financial cost calculation
            step_import_cost = grid_import_kw * dt * grid_config.import_tariff
            step_export_revenue = grid_export_kw * dt * grid_config.export_tariff
            step_cost = round(step_import_cost - step_export_revenue, 4)
            total_cost += step_cost

            steps.append(
                BatteryScheduleStepSchema(
                    step_index=i,
                    timestamp=ts,
                    pv_forecast_kw=round(pv_kw, 2),
                    load_forecast_kw=round(load_kw, 2),
                    action=action,
                    battery_power_kw=battery_power_kw,
                    soc_before=soc_before,
                    soc_after=soc_after,
                    grid_import_kw=grid_import_kw,
                    grid_export_kw=grid_export_kw,
                    step_cost=step_cost
                )
            )

        return BatteryScheduleResponse(
            schedule_id=schedule_id,
            generated_at=now,
            status="GENERATED",
            total_cost=round(total_cost, 2),
            algorithm="Heuristic Energy Balance (SIMULATED)",
            is_simulated=True,
            status_label="SIMULATED SCHEDULE — OPTIMIZATION ENGINE NOT CONNECTED",
            notes="Calculated using physical constraints: capacity, SOC limits, efficiency, and grid limits.",
            steps=steps
        )
