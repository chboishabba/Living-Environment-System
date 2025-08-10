class Aquarium:
    """Simple aquarium model tracking device states and energy usage."""

    def __init__(self, *, pump_w=0.0, aerator_w=0.0, total_fish_kg=0.0, water_volume_l=0.0):
        self.pump_on = False
        self.aerator_on = False
        self.pump_w = float(pump_w)
        self.aerator_w = float(aerator_w)
        self.total_fish_kg = float(total_fish_kg)
        self.water_volume_l = float(water_volume_l)
        # Registered field that accumulates total energy use in kWh
        self.energy_kwh = 0.0
