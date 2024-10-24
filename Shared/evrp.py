class EVRP:
    @staticmethod
    def drain_battery(current_battery: float, distance_cost: int, energy_consumption: float) -> float:
        new_current_battery = current_battery - (distance_cost * energy_consumption)
        return new_current_battery

    @property
    def charge_battery(self) -> float:
        max_battery = 1.0
        return max_battery
