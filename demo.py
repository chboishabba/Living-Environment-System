from functools import lru_cache

import pandas as pd

from les_state_reduction import (
    SoilBounds,
    SoilBuckets,
    SoilDelta,
    apply_soil_delta_guarded,
)

# --- "Simple version" demo: 1 bed, 1 year (4 seasonal slots), 10-action palette ---
# Prices: AUD/kg (seeded from earlier discussion; treat as illustrative inputs).
prices = {
    "Tomato": 3.98,
    "Zucchini": 1.73,
    "Cucumber": 3.23,
    "Broccoli": 3.18,
    "Cabbage": 1.15,   # midpoint-ish between 1.05–1.22 in earlier notes
    "Potato": 1.92,    # midpoint-ish 1.89–1.96
    "Pumpkin": 1.13,
    "Beans": 7.16,
    "Leek": 3.59,
    "CoverCrop": 0.0,  # not sold in this simple model
}

# Families (rotation pressure classes)
family = {
    "Tomato": "Solanaceae",
    "Potato": "Solanaceae",
    "Broccoli": "Brassicaceae",
    "Cabbage": "Brassicaceae",
    "Cucumber": "Cucurbitaceae",
    "Zucchini": "Cucurbitaceae",
    "Pumpkin": "Cucurbitaceae",
    "Leek": "Allium",
    "Beans": "Legume",
    "CoverCrop": "Cover",
}

# Yields per season (kg per "bed" per season).
# These are illustrative; swap with your real yield expectations.
yields = {
    "Tomato":   [120,  80,  60, 100],
    "Zucchini": [140, 100,  60, 110],
    "Cucumber": [110, 120,  70,  90],
    "Broccoli": [ 60,  70,  80,  60],
    "Cabbage":  [ 80,  90,  95,  70],
    "Potato":   [160, 180, 200, 140],
    "Pumpkin":  [220, 140, 100, 180],
    "Beans":    [ 45,  55,  60,  40],
    "Leek":     [ 65,  70,  70,  60],
    "CoverCrop":[  0,   0,   0,   0],
}

# Variable costs per season (AUD per bed per season).
# Again illustrative. Covers: seed + labor without sales.
costs = {
    "Tomato":   [180, 160, 150, 170],
    "Zucchini": [120, 115, 110, 120],
    "Cucumber": [140, 145, 130, 135],
    "Broccoli": [110, 115, 120, 110],
    "Cabbage":  [ 90,  95, 100,  90],
    "Potato":   [160, 170, 185, 150],
    "Pumpkin":  [ 95,  90,  85,  95],
    "Beans":    [130, 135, 140, 125],
    "Leek":     [120, 125, 125, 115],
    "CoverCrop":[ 70,  70,  70,  70],
}

# Soil deltas (bucket model): ΔN, ΔC, ΔS
soil_delta = {
    "Tomato":   (-2, -1, -1),
    "Potato":   (-2, -1, -2),
    "Broccoli": (-1, -1,  0),
    "Cabbage":  (-1, -1,  0),
    "Cucumber": (-1, -1,  0),
    "Zucchini": (-1, -1,  0),
    "Pumpkin":  (-1, -1,  0),
    "Leek":     (-1, -1,  0),
    "Beans":    ( 0, -1,  0),  # legume cash: N neutral here, still draws C via harvest/disturbance
    "CoverCrop":(+2, +2, +1),
}

# Disease deltas (bucket model): ΔD (pressure)
disease_delta = {
    "Tomato":   +1,
    "Potato":   +1,
    "Broccoli":  0,
    "Cabbage":   0,
    "Cucumber":  0,
    "Zucchini":  0,
    "Pumpkin":   0,
    "Leek":      0,
    "Beans":    -1,
    "CoverCrop":-2,
}

# Resource deltas per action: water use and compost credits
resource_delta = {
    "Tomato":   (3,  0),
    "Zucchini": (3,  0),
    "Cucumber": (3,  0),
    "Broccoli": (2,  0),
    "Cabbage":  (2,  0),
    "Potato":   (2,  0),
    "Pumpkin":  (3,  0),
    "Beans":    (2, +1),
    "Leek":     (2,  0),
    "CoverCrop":(1, +2),
}

# Bounds and constraints
N_MAX = C_MAX = S_MAX = 5
N_MIN = C_MIN = S_MIN = 2
D_MAX = 5

W_BUDGET = 6  # water units per season
K_MAX = 6   # compost credits stock

SEASONS_PER_YEAR = 4
HORIZON_YEARS = 20
HORIZON_SEASONS = HORIZON_YEARS * SEASONS_PER_YEAR
T = HORIZON_SEASONS

# Disease half-life (in seasons). 8 seasons = 2 years.
DISEASE_HALF_LIFE = 8

actions = list(prices.keys())

def expand_series(series, total_len):
    if not series:
        raise ValueError("Series cannot be empty")
    out = []
    while len(out) < total_len:
        out.extend(series)
    return out[:total_len]

for act in actions:
    yields[act] = expand_series(yields[act], T)
    costs[act] = expand_series(costs[act], T)

def validate_inputs():
    sets = [
        ("prices", prices),
        ("family", family),
        ("yields", yields),
        ("costs", costs),
        ("soil_delta", soil_delta),
        ("disease_delta", disease_delta),
        ("resource_delta", resource_delta),
    ]
    keys = None
    for name, mapping in sets:
        mapping_keys = set(mapping.keys())
        if keys is None:
            keys = mapping_keys
        elif mapping_keys != keys:
            raise ValueError(f"Action keys mismatch in {name}: {mapping_keys ^ keys}")

    for act in keys or []:
        if prices[act] < 0:
            raise ValueError(f"Negative price for {act}")
        if len(yields[act]) != T:
            raise ValueError(f"Yield length for {act} does not match T={T}")
        if len(costs[act]) != T:
            raise ValueError(f"Cost length for {act} does not match T={T}")
        if any(y < 0 for y in yields[act]):
            raise ValueError(f"Negative yield for {act}")
        if any(c < 0 for c in costs[act]):
            raise ValueError(f"Negative cost for {act}")

validate_inputs()

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def disease_decay_factor(half_life_seasons: int) -> float:
    if half_life_seasons <= 0:
        raise ValueError("half-life must be positive")
    return 0.5 ** (1.0 / half_life_seasons)

def step_soil(N, C, S, D, act):
    dN, dC, dS = soil_delta[act]
    dD = disease_delta[act]
    state = SoilBuckets(n=N, c=C, s=S, d=D, f=0)
    decayed = int(round(D * disease_decay_factor(DISEASE_HALF_LIFE)))
    delta = SoilDelta(dn=dN, dc=dC, ds=dS, dd=dD + (decayed - D))
    limits = {"n": N_MAX, "c": C_MAX, "s": S_MAX, "d": D_MAX}
    bounds = SoilBounds(min_n=N_MIN, min_c=C_MIN, min_s=S_MIN, max_d=D_MAX)
    try:
        updated = apply_soil_delta_guarded(state, delta, limits, bounds)
    except ValueError:
        return None
    return (updated.n, updated.c, updated.s, updated.d)

def step_resources(K, act):
    water_use, dK = resource_delta[act]
    if water_use > W_BUDGET:
        return None
    if K + dK < 0:
        return None
    K2 = clamp(K + dK, 0, K_MAX)
    return K2

def profit(act, t_idx):
    return prices[act] * yields[act][t_idx] - costs[act][t_idx]

def allowed(prev_family, act_family):
    # Simple rotation rule: no same family consecutively,
    # but "Cover" resets pressure (allow following any, and allow cover after anything).
    if act_family == "Cover":
        return True
    if prev_family == "Cover":
        return True
    return act_family != prev_family

@lru_cache(None)
def dp(t, N, C, S, D, K, prev_fam, tomato_cd):
    # Return (best_value, best_action, next_state_tuple)
    if t == T:
        return (0.0, None, None)

    best = (-1e18, None, None)
    for act in actions:
        fam = family[act]
        if not allowed(prev_fam, fam):
            continue
        if act == "Tomato" and tomato_cd > 0:
            continue

        nxt_soil = step_soil(N, C, S, D, act)
        if nxt_soil is None:
            continue
        N2, C2, S2, D2 = nxt_soil

        K2 = step_resources(K, act)
        if K2 is None:
            continue

        next_cd = max(0, tomato_cd - 1)
        if act == "Tomato":
            next_cd = 2 * SEASONS_PER_YEAR

        val_next, _, _ = dp(t + 1, N2, C2, S2, D2, K2, fam, next_cd)
        val = profit(act, t) + val_next

        if val > best[0]:
            best = (val, act, (N2, C2, S2, D2, K2, fam, next_cd))
    return best

# Initial state (example)
N0, C0, S0, D0 = 4, 4, 4, 1
K0 = 2
prev_fam0 = "None"
tomato_cd0 = 0

best_total, _, _ = dp(0, N0, C0, S0, D0, K0, prev_fam0, tomato_cd0)

# Reconstruct policy
rows = []
N, C, S, D, K, prev_fam, tomato_cd = (N0, C0, S0, D0, K0, prev_fam0, tomato_cd0)
for t in range(T):
    val, act, nxt = dp(t, N, C, S, D, K, prev_fam, tomato_cd)
    if act is None:
        rows.append({"Season": t+1, "Action": None, "Family": None, "Profit(AUD)": None,
                     "N": N, "C": C, "S": S, "D": D, "K": K,
                     "N_next": None, "C_next": None, "S_next": None, "D_next": None,
                     "K_next": None, "W_used": None})
        break
    N2, C2, S2, D2, K2, fam, tomato_cd2 = nxt
    rows.append({
        "Season": t+1,
        "Action": act,
        "Family": family[act],
        "Price(AUD/kg)": prices[act],
        "Yield(kg/bed)": yields[act][t],
        "Cost(AUD/bed)": costs[act][t],
        "Profit(AUD)": round(profit(act, t), 2),
        "N": N, "C": C, "S": S, "D": D, "K": K,
        "N_next": N2, "C_next": C2, "S_next": S2, "D_next": D2,
        "K_next": K2, "W_used": resource_delta[act][0],
    })
    N, C, S, D, K, prev_fam, tomato_cd = N2, C2, S2, D2, K2, fam, tomato_cd2

plan = pd.DataFrame(rows)

summary = {
    "Total profit (AUD)": round(plan["Profit(AUD)"].dropna().sum(), 2),
    "End soil (N,C,S,D)": (N, C, S, D),
    "End resources (K)": (K,),
    "Constraints": (
        f"N,C,S >= ({N_MIN},{C_MIN},{S_MIN}); D <= {D_MAX}; "
        "no same-family back-to-back (Cover resets); "
        "Tomato cooldown 2 years."
    ),
}

plan, summary
