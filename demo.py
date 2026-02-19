import pandas as pd
from functools import lru_cache

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

# Bounds and constraints
N_MAX = C_MAX = S_MAX = 5
N_MIN = C_MIN = S_MIN = 2

T = 4  # 4 seasonal steps

actions = list(prices.keys())

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def step_soil(N, C, S, act):
    dN, dC, dS = soil_delta[act]
    return (
        clamp(N + dN, 0, N_MAX),
        clamp(C + dC, 0, C_MAX),
        clamp(S + dS, 0, S_MAX),
    )

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
def dp(t, N, C, S, prev_fam):
    # Return (best_value, best_action, next_state_tuple)
    if t == T:
        return (0.0, None, None)

    best = (-1e18, None, None)
    for act in actions:
        fam = family[act]
        if not allowed(prev_fam, fam):
            continue

        N2, C2, S2 = step_soil(N, C, S, act)

        # Soil invariants: maintain minima at all times (after the action)
        if not (N2 >= N_MIN and C2 >= C_MIN and S2 >= S_MIN):
            continue

        val_next, _, _ = dp(t + 1, N2, C2, S2, fam)
        val = profit(act, t) + val_next

        if val > best[0]:
            best = (val, act, (N2, C2, S2, fam))
    return best

# Initial state (example)
N0, C0, S0 = 4, 4, 4
prev_fam0 = "None"

best_total, _, _ = dp(0, N0, C0, S0, prev_fam0)

# Reconstruct policy
rows = []
N, C, S, prev_fam = N0, C0, S0, prev_fam0
for t in range(T):
    val, act, nxt = dp(t, N, C, S, prev_fam)
    if act is None:
        rows.append({"Season": t+1, "Action": None, "Family": None, "Profit(AUD)": None,
                     "N": N, "C": C, "S": S, "N_next": None, "C_next": None, "S_next": None})
        break
    N2, C2, S2, fam = nxt
    rows.append({
        "Season": t+1,
        "Action": act,
        "Family": family[act],
        "Price(AUD/kg)": prices[act],
        "Yield(kg/bed)": yields[act][t],
        "Cost(AUD/bed)": costs[act][t],
        "Profit(AUD)": round(profit(act, t), 2),
        "N": N, "C": C, "S": S,
        "N_next": N2, "C_next": C2, "S_next": S2,
    })
    N, C, S, prev_fam = N2, C2, S2, fam

plan = pd.DataFrame(rows)

summary = {
    "Total profit (AUD)": round(plan["Profit(AUD)"].dropna().sum(), 2),
    "End soil (N,C,S)": (N, C, S),
    "Constraints": f"N,C,S >= ({N_MIN},{C_MIN},{S_MIN}); no same-family back-to-back (Cover resets)."
}

plan, summary

