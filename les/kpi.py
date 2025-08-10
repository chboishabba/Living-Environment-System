"""Key performance indicator calculations for the system."""


def energy_kpis(aq):
    """Return energy related KPIs for the given aquarium.

    Parameters
    ----------
    aq: object
        Aquarium-like instance containing ``energy_kwh``, ``total_fish_kg`` and
        ``water_volume_l`` attributes.
    """
    total_energy = getattr(aq, "energy_kwh", 0.0)
    fish_kg = getattr(aq, "total_fish_kg", 0.0)
    water_l = getattr(aq, "water_volume_l", 0.0)

    kpis = {}
    if fish_kg > 0:
        kpis["energy_per_kg_fish"] = total_energy / fish_kg
    if water_l > 0:
        kpis["energy_per_liter_water"] = total_energy / water_l
    return kpis
