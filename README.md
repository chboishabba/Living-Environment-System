
LES = **Living Environment Simulator**
It’s our umbrella system for modelling **dynamic environmental progression** over time, including:

* **Weather patterns & climate data** (temperature, rainfall, wind, solar radiation).
* **Soil, hydrology & erosion** models.
* **Plant growth & succession** (forests, crops, aquaponics plants).
* **Animal population dynamics** (wildlife, livestock, aquaculture species).
* **Nutrient flows** between water, soil, plants, and animals.
* **Impact modelling** of interventions (e.g., planting windbreaks, changing feed, altering stocking density).

In our architecture:

* **Aquaponics-Calculator** is a *module* inside LES that focuses on **controlled water-based systems** (fish tanks, grow beds).
* LES is the *world engine* that can model both **inside-farm** (aquaponics, greenhouse) and **outside-farm** (pasture, forest, watershed) conditions.

This means:

* Diet & feed optimisation → changes ingredient sourcing → LES can simulate **knock-on environmental effects** (e.g., growing more duckweed reduces nutrient discharge into pond → improves oxygen saturation → changes fish growth curve).
* LES outputs → inform diet/feed optimiser constraints (e.g., predicted lower tomato yield → adjust meal plans, recommend alternative crops).



# 🌍 Living Environment Simulator (LES)

**Part of the Living Environment Platform**
*A modular, multi‑scale, feedback‑aware simulation framework that couples atmosphere, hydrology, geomorphology, vegetation, wildlife, and human systems — designed for research, planning, and interactive visualization.*
<img width="5261" height="26157" alt="NotebookLM Mind Map(5)" src="https://github.com/user-attachments/assets/fca6cab0-7803-4007-8e50-9992c179c908" />

---

## 🔎 Overview

**LES** aims to close the gap between siloed scientific models (weather, erosion, ecology) and interactive engines (games/visualization). It provides a **coupling layer**, **common data model**, and **plug‑in API** so specialist process models can exchange state **bidirectionally** on consistent spatial/temporal grids — fast enough for exploratory scenarios, accurate enough for scientific workflows.

**Primary use‑cases**

* Forest/landscape evolution under storms, droughts, wildfire, and management.
* Catchment hydrology: rainfall–runoff–sediment–nutrients with vegetation feedbacks.
* Habitat & wildlife dynamics tied to terrain change and climate variability.
* Decision support: restoration plans, floodplain design, erosion risk, fire mitigation.
* Educational/interactive “living world” demonstrators.

---
<img width="7909" height="14036" alt="NotebookLM Mind Map(13)" src="https://github.com/user-attachments/assets/c7915f5b-b22a-4f7c-9b3a-feb2d08611a7" />

## 🎯 Goals & Non‑Goals

**Goals**

* **Modular**: each physical/biological process is a replaceable module.
* **Multi‑scale**: hours→centuries; meters→basins; support grid nesting.
* **Bidirectional coupling**: vegetation ↔ erosion ↔ microclimate ↔ hydrology ↔ wildlife.
* **Reproducible**: CF/UDUNITS‑compliant metadata, deterministic runs, versioned inputs.
* **Performant**: Python orchestrator path (prototyping) and HPC path (MPI/ESMF) from day one.
* **Open**: permissive license, documented APIs, test datasets, example scenarios.

**Non‑Goals**

* A monolithic “one model to rule them all.” LES is a **framework** + curated modules.
* Perfect global climate fidelity; LES focuses on **meso/local** scales and coupling. But who knows!!

---

## 🧩 Architecture

```
+-----------------------------+       +-----------------------------+
|  Visualization / Frontends  | <---- |   Data Services (I/O, GIS)  |
|  • Web maps (deck.gl)       |       |   • Raster/Vector adapters   |
|  • Unreal/Unity bridge      |       |   • NetCDF/Zarr stores       |
+---------------^-------------+       +---------------^-------------+
                |                                 |
        +-------+---------------------------------+------+
        |          LES Orchestrator / Scheduler          |
        |  • Time manager  • Event bus  • Couplers       |
        |  • State registry (xarray)  • Unit/CF checks   |
        +--+---------------+-------------------+--------+
           |               |                   |
     +-----+-----+   +-----+-----+       +-----+-----+
     | Atmosphere |   |  Land/Soil|       | Hydrology |
     |  (Weather) |   |  & Veg    |       | (Surface/ |
     |            |   |           |       |  GW)      |
     +-----+------+   +-----+-----+       +-----+-----+
           |               |                   |
        +--+---------------+-------------------+--+
        |        Geomorphology / Erosion / Rivers  |
        +--+---------------+-------------------+--+
           |               |                   |
        +--+--+        +---+---+           +---+---+
        | Fire |        | Wildlife|         | Human  |
        |      |        | Agents  |         | Systems|
        +------+        +---------+         +--------+
```

### Orchestrator

* **Time manager**: discrete timesteps with sub‑stepping; adaptive where supported.
* **Couplers**: sequential or concurrent exchange with **conservative remapping** (area/flow preserving). Options: LES native coupler (xarray+Dask) or HPC coupler (ESMF/ESMPy, OpenMI, BMI adapters).
* **State registry**: shared **xarray** datasets with CF‑conventions; variable naming schema (e.g., `veg.canopy_cover`, `hyd.q_surface`, `atm.precip_rate`).
* **Event bus**: ZeroMQ/gRPC for module messages (e.g., fire ignition, management actions).

### Module API (LES‑BMI)

Minimal interface (inspired by **CSDMS BMI**):

* `initialize(config)` → returns capability flags (grid type, dt range, variables read/write).
* `update(dt)` → advances internal state; exposes `get_value(var)` / `set_value(var)`.
* `finalize()`
* Grid/mesh getters; CRS; metadata; checkpoint/restore hooks.

---

## 📦 Process Modules (first‑class citizens)

**Atmosphere**

* *Options*: Stochastic weather generator; WRF downscaled inputs; ERA5 reanalysis ingestion.
* *Exchanges*: precip, short/longwave radiation, wind, air T/RH, P.

**Hydrology**

* *Surface*: kinematic/kinematic‑wave or shallow‑water (Saint‑Venant) approximations.
* *Subsurface*: bucket/Richards‑lite soil moisture; TOPMODEL‑style runoff indices.
* *Exchanges*: infiltration, runoff, baseflow, soil moisture, ET components.

**Geomorphology / Erosion**

* Hillslope diffusion + stream power law; Exner sediment continuity.
* Channel hydraulics (bank shear stress, critical Shields number), sediment transport rating curves.
* *Exchanges*: updated DEM, sediment fluxes, bank stability → feeds habitat & vegetation.

**Vegetation / Ecosystem**

* Two tracks:

  1. **Procedural‑growth forest** (multi‑scale canopy competition à la “Natural Forest Growth” simulators) for interactive runs.
  2. **Biophysical DGVM‑lite** (LPJ‑style NPP, LAI, phenology, mortality) for climate sensitivity.
* *Exchanges*: canopy cover, root depth, roughness, litter, transpiration, shade, soil binding.

**Wildlife / Agents**

* Agent‑based movement (correlated random walk / step‑selection) with habitat suitability maps; energetic budgets and predation/grazing.
* *Exchanges*: grazing pressure, seed dispersal, disturbance, carcass nutrients.

**Fire (optional)**

* Empirical spread model (ROS from wind, slope, fuel moisture); crown vs surface fire; post‑fire mortality.
* *Exchanges*: canopy loss, soil hydrophobicity, smoke forcing.

**Human Systems (optional)**

* Land‑use transitions, management actions (thinning, planting, levees), water withdrawals/returns.

---

## 🧮 Numerics & Algorithms (baseline choices)

**Time stepping & coupling**

* **Operator splitting** with **sequential coupling** by default (A→B→C in a super‑step), with configurable **exchange frequency** per variable.
* Optional **concurrent/MPI** mode for HPC modules.

**Spatial discretization**

* Regular lat/lon or projected **rectilinear grids**; optional unstructured meshes via ESMF.
* **Nested grids** for hotspots (e.g., high‑res floodplain in coarse basin).

**Key formulations**

* Rainfall–runoff: Green–Ampt infiltration; Unit Hydrograph or Muskingum routing.
* ET: Penman–Monteith; canopy resistance from LAI & VPD.
* Hillslope: linear diffusion; channels: stream‑power incision ($E = K Q^m S^n$).
* Sediment: Exner: $\partial(\eta)/\partial t + (1/(1-\lambda_p))\nabla\cdot q_s = 0$.
* Vegetation light competition: Beer–Lambert; photosynthesis–respiration balance for NPP.
* Wildlife movement: step‑selection with resource selection functions (RSF); density‑dependent mortality.

**Units/metadata**

* **UDUNITS**; **CF‑1.x** variable names/attributes; **ISO‑8601** time. CRS via **PROJ/CRS‑WKT**.

---

## 🗂 GIS & Plans Intake

* **Raster**: Cloud‑Optimized GeoTIFF/GeoTIFF, NetCDF/GRIB and chunked Zarr stores ingested with **rioxarray/xarray**.
* **Vector**: **GeoPackage** and **FlatGeobuf** layers via **GeoPandas** (legacy Shapefile tolerated).
* **Catalogs**: **STAC** entries with optional caching to local Zarr/Parquet for reproducibility.
* **Plans**: **IFC/DWG/DXF** site plans converted (ifcopenshell/FME/QGIS) to GeoPackage layers; optional 3D path IFC → CityJSON/CityGML → Cesium 3D Tiles for visualization. Information loss outside native BIM is documented.
* **CRS policy**: all inputs reprojected to the scenario CRS and tagged with metadata; outputs remain **CF/UDUNITS** compliant.
* **Processing queue**: headless **QGIS Processing**/**GDAL** steps recompute derived rasters (slope, buffers, least‑cost paths) on demand.

---

## 🧭 Planning & Decision Support

* **Scenario manager**: YAML definitions of interventions and levers (planting density, setbacks, detention basins, stocking rates).
* **Multi‑criteria evaluation / geodesign**: weighted raster overlays and constraint maps built with **xarray+Dask** map algebra.
* **Optimisation**: multi‑objective solvers (e.g., **NSGA‑II**, **CP‑SAT**) explore trade‑offs among cost, erosion, habitat, yield.
* **Probabilistic reasoning**: **Bayesian networks** and risk models consume GIS layers and simulation outputs.
* **Agent‑based models**: movement and behaviour driven by GIS suitability rasters and network layers for wildlife or human agents.

Results feed closed‑loop controllers, diet/feed planners, and stakeholder dashboards.

---

## ⚙️ Execution & Visualization

* **Prototype mode**: Python orchestrator with **xarray+Dask** and headless **QGIS Processing** for geoprocessing.
* **HPC mode**: **ESMF/ESMPy** or **OpenMI** coupling on MPI for parallel modules with conservative remapping.
* **Visualization**: ParaView/QGIS for analysis; **Cesium 3D Tiles** or WebGL maps for interactive digital‑twin views.
* **Scenario UI**: sliders and dashboards driving YAML configurations for exploratory planning sessions.

---

## ✅ Current State of Play (SOTP) & SOTA Snapshot

**SOTP (what practitioners do today)**

* Run **specialist models** separately (WRF for weather; SWAT/MIKE SHE for hydrology; CAESAR‑Lisflood/LSDTopoTools for erosion; LPJ‑GUESS/SORTIE‑ND for vegetation; GAMA/HexSim for wildlife), then **hand‑off** static layers between them with coarse temporal sync.
* Limited **two‑way feedback**; high effort for data wrangling; results hard to visualize interactively.

**SOTA exemplars (by domain)**

* **Coupling frameworks**: **ESMF/ESMPy**, **OpenMI**, **CSDMS BMI**; coastal stacks like **MOSSCO**.
* **Atmosphere**: **WRF**, **OpenIFS+SURFEX** (downscaling, data assimilation).
* **Hydrology**: **MIKE SHE**, **Delft3D**, **SWAT+** (catchment to coastal coupling).
* **Geomorphology**: **Landlab** (composable Python components), **CAESAR‑Lisflood** (long‑term morphodynamics).
* **Vegetation**: **LPJ‑GUESS** (DGVM), **SORTIE‑ND** (forest gap dynamics), high‑performance **procedural forest growth** models for interactive scaling.
* **Wildlife**: **HexSim**, **GAMA** (spatial ABMs with GIS).

**Where LES advances**

* **Real‑time, multi‑domain coupling** with **bidirectional** exchanges at controllable frequencies.
* A **unified state registry** (xarray) with CF metadata to minimize glue code.
* **Two execution paths**: rapid Python+Dask prototyping **and** HPC MPI coupling for heavy runs.
* **Bridges to interactive engines**, enabling explainable scenario exploration.

---

## 🧪 Validation, Calibration, QA

* **Golden scenarios**: canonical test basins and forest plots with published benchmarks.
* **Regression tests**: numerical tolerances on time series and maps (pytest + xarray tests).
* **Calibration**: GLUE/Bayesian (e.g., `emcee`) parameter inference; Sobol sensitivity.
* **Uncertainty**: ensemble runs; propagate input/weather uncertainty to outputs.

---

## 🛠 Implementation Plan

**Code layout (suggested)**

```
les/
  core/            # orchestrator, scheduler, couplers, registry
  api/             # LES-BMI adapters, typing, metadata
  modules/
    atm/ hydro/ geomorph/ veg/ wildlife/ fire/ human/
  io/
    readers/ writers/ catalogs/
  viz/
    webmaps/ ue_bridge/
  scenarios/
    demo_catchment/
  tests/
```

**Language/tooling (suggested)**

* **Python 3.11+** (orchestrator): xarray, Dask, numba, cupy(optional), esmpy.
* **HPC modules**: C++/Fortran with BMI shims (C ABI) + MPI.
* **Messaging**: ZeroMQ/gRPC; **Config**: OmegaConf/YAML; **Env**: conda/mamba; **CI**: GitHub Actions.

---

## 🧭 Roadmap

**v0.1 – Minimal Coupled Demo (3–6 weeks)**

* Orchestrator (sequential coupling), CF/units checks, NetCDF/Zarr I/O.
* Modules: stochastic weather → hydrology (runoff/infiltration) → vegetation (canopy/ET) → erosion (hillslope+stream‑power).
* Demo scenario: 10×10 km catchment, 50 m grid, 5‑year run; basic web map and notebook.

**v0.2 – Bidirectional Feedbacks + Wildlife**

* Vegetation ↔ erosion feedbacks (root reinforcement, soil binding, roughness).
* Wildlife ABM prototype (grazing pressure, seed dispersal); habitat suitability from veg+hydro.
* Scenario manager + sliders; improved visualization.

**v0.3 – HPC Path & Nesting**

* ESMF/ESMPy coupler; optional MPI concurrency; nested grid support.
* Import WRF/ERA5 forcing; add Muskingum routing; better sediment transport.

**v0.4 – Fire & Management**

* Fire spread module; post‑fire hydrology changes; management actions API (thinning, planting).

**v1.0 – Stable API & Docs**

* Formal LES‑BMI 1.0 spec; plugin registry; gallery of validated scenarios; provenance/lineage tracking.

---

## 🔗 Interfaces & Example Config

**LES‑BMI variables** (illustrative)

* `atm.precip_rate` \[kg m-2 s-1], `atm.tair` \[K], `atm.rsw` \[W m-2]
* `hyd.theta_soil` \[m3 m-3], `hyd.q_surf` \[m2 s-1]
* `geom.eta` \[m], `geom.q_sed` \[kg m-1 s-1]
* `veg.lai` \[m2 m-2], `veg.canopy_cover` \[0..1], `veg.root_depth` \[m]
* `wild.grazing` \[kg m-2 s-1]

**Scenario YAML (excerpt)**

```yaml
scenario:
  name: hillslope_restoration
  grid:
    proj: EPSG:28356
    dx: 50
    dy: 50
    nx: 200
    ny: 200
  time:
    start: 2000-01-01
    end: 2010-01-01
    dt_seconds: 3600
  modules:
    atmosphere: { kind: stochastic_weather, params: { mean_rain_mm_day: 2.3 } }
    hydrology:  { kind: kinematic_wave }
    vegetation: { kind: procedural_forest, params: { species: [euc, acacia] } }
    geomorph:   { kind: stream_power, params: { K: 3.0e-6, m: 0.5, n: 1.0 } }
    wildlife:   { kind: grazing_abm, enabled: false }
  outputs:
    cadence_hours: 24
    variables: ["hyd.q_surf","geom.eta","veg.lai"]
```

---

## 🔒 Reproducibility & Provenance

* **Run manifests** (YAML) capture git SHAs, module versions, parameter hashes, input catalogs.
* **Determinism**: seeded RNG; numeric tolerances documented.
* **Lineage**: write **Provenance** JSON alongside outputs for audit trails.

---

## 🧑‍🤝‍🧑 Governance & Contributing

* **Module maintainers** for each domain; **API stewards** for LES‑BMI.
* Contribution guide covers variable naming, units, grid specs, testing minima, and review checklists.
* Code of Conduct applies across repos.

---

## 📜 License

Apache‑2.0 (proposed) to enable wide academic/industry adoption while protecting trademarks.

---

## 📚 References & Prior Art (non‑exhaustive)

* Coupling & frameworks: ESMF/ESMPy, OpenMI, CSDMS BMI, MOSSCO.
* Hydrology & morphodynamics: SWAT+, MIKE SHE, Delft3D, Landlab, CAESAR‑Lisflood, LSDTopoTools.
* Vegetation: LPJ‑GUESS, SORTIE‑ND; interactive procedural forest growth literature.
* Wildlife ABM: HexSim, GAMA; step‑selection and RSF methods.
* Visualization: ParaView, deck.gl, Unreal/Unity environmental pipelines.

---

**LES** turns a collection of excellent single‑domain models into a coherent, feedback‑aware system. If you build (or port) a module, start with the **LES‑BMI** adapter template and one of the **golden scenarios** to verify coupling and units. Ready to grow a living world? 🌱




# Farm-to-Plate-and-Pond Optimizer Roadmap from https://github.com/chboishabba/Aquaponics-Calculator/blob/master/docs/roadmap.md

The roadmap outlines phased development for integrating diet and feed optimisation with live environmental simulation (LES) and nutrient databases.

```mermaid
graph TD
  subgraph MVP
    A[Unified Ingredient & Nutrient DB]
    B[Dual Optimizers\nHuman Diet & Feed]
    C[Manual Inventory Input]
    D[Supplement List Generator]
    E[Static Reports]
    A --> B
    C --> B
    B --> D
    B --> E
  end
  subgraph "Phase 2"
    F[Live Inventory & Production Data]
    G[Scenario Simulation Link to LES]
    H[Procurement Optimizer]
    I[Expanded Species Support]
    J[Automation Hooks\nHome Assistant / MQTT]
    B --> F
    F --> G
    F --> H
    F --> I
    F --> J
  end
  subgraph "Phase 3"
    K[Machine Learning Enhancements]
    L[Multi-Objective Optimization]
    M[Real-Time Adaptive Control]
    N[User Preference Learning]
    O[Mobile App]
    F --> K
    K --> L
    L --> M
    M --> N
    N --> O
  end
  NutrientSources[AUSNUT/USDA & Feedipedia]
  NutrientSources --> A
  LES[LES Simulation]
  G --> LES
```

This diagram also serves as an elevator pitch visual, showing how nutrient data and LES integrate through each phase.

## Phase Details

### MVP (Phase&nbsp;1)

- Unified ingredient and nutrient database combining AUSNUT, USDA FDC, Feedipedia and aquaculture tables
- Basic dual optimizers for human diet planning and feed formulation sharing a common inventory
- Manual inventory input with expected harvest fields
- Simple supplement list generator outlining off‑farm needs
- Static reports summarising diet and feed plans with self‑sufficiency metrics

### Phase 2 – Live Data & Automation Hooks

- Live inventory and production integration pulling data from Aquaponics‑Calculator and LES forecasts
- Scenario simulation link to push plans into LES and evaluate environmental impacts
- Procurement optimizer comparing suppliers, prices and lead times
- Expanded species support covering multiple personas and animal types
- Home Assistant / MQTT hooks to automate aeration, feeding and dosing

### Phase 3 – Predictive & AI‑Enhanced

- Machine learning enhancements to predict yield shortfalls and fill missing nutrient data
- Multi‑objective optimisation balancing cost, sustainability and nutrient adequacy
- Real‑time adaptive control re‑optimising plans as conditions change
- User preference learning for tailored menu and feed suggestions
- Mobile app with offline mode for remote decision support



If we want this to stand out and actually work as **the** farm-to-plate-and-pond planner, the “must-haves” break down into five core feature clusters — anything less and we’re just reinventing one of the partial tools you listed.

---

## **1. Unified Ingredient & Nutrient Database**

**Why:** Everything downstream depends on accurate nutrient vectors and availability.

* ✅ **Single source of truth** for both human foods and feed ingredients.
* ✅ Support for **nutrient profiles** (macro, micro, amino acids, fatty acids, bioavailability modifiers).
* ✅ Source tags (`on_farm`, `supplier`, `wild_harvest`).
* ✅ **Seasonal yield forecasts** (from LES & Aquaponics-Calculator).
* ✅ Processing loss factors (cooking, drying, fermentation).

---

## **2. Dual Optimizers (Human Diet + Feed)**

**Why:** This is our differentiator — coupling human nutrition and animal/fish nutrition into one optimisation loop.

* **Human menu optimizer**

  * Meets RDI/NRV for chosen personas.
  * Enforces preferences (veg, allergies, cultural).
  * Maximises use of on-farm harvest.
  * Minimises cost / off-farm purchases.
  * Variety and meal-structure constraints.

* **Animal/fish feed optimizer**

  * Meets species-specific nutrient needs (digestible basis).
  * Applies inclusion caps (e.g., max % duckweed, azolla).
  * Minimises cost and waste.
  * Matches pellet/binder requirements.

* Both optimizers **share the same ingredient pool** and respect total inventory limits.

---

## **3. Inventory & Production Integration**

**Why:** You can’t optimise if you don’t know what’s coming in.

* Automatic import of **real-time inventory** from farm systems.
* Integration with **forecast modules** (plant growth, harvest dates, biomass models for fish).
* Yield uncertainty modelling (so the optimizer can plan for ± scenarios).
* Ability to log and adjust **unexpected events** (disease, crop failure).

---

## **4. Supplement & Procurement Planner**

**Why:** Tells you exactly what to buy to meet nutrition gaps.

* Generates **shopping list** of supplements/off-farm ingredients.
* Calculates **cheapest local source** or **preferred supplier**.
* Suggests **on-farm production adjustments** to reduce reliance on purchased items long-term.

---

## **5. Feedback & Scenario Loop**

**Why:** Links to LES for “what if” planning.

* Export diet/feed plans to **LES** for environmental impact modelling (water use, nutrient cycling, oxygen demand).
* Re-run optimisation under different scenarios:

  * Reduced sunlight (weather event)
  * Loss of specific crop
  * Higher/lower fish stocking density
  * Price spikes in purchased ingredients
* Reports KPIs: % self-sufficiency, cost, nutrient adequacy, sustainability score.

---

## **Nice-to-Haves (but not day-one critical)**

* 📈 **GHG and energy footprint** calculations.
* 🤖 ML-assisted menu/feed suggestions based on past choices and feedback.
* 🧪 HACCP-style safety logging for critical control points.
* 📱 Mobile app interface for quick adjustments on the go.
* 🌦 Weather integration for seasonal planting and yield forecasting.
* 🐟 Oxygen budget calculation tied to Home Assistant automation.

---


There are a few categories of tools that touch parts of what we’re describing, but we're trying to cover the **whole “design human diets + animal/fish feed from on-farm production with supplement top-ups”** loop out of the box.

Here’s the landscape:

---

## **1. Human diet formulation tools**

These do menu planning, but usually ignore feed loops and farm production constraints.

| Tool                                | Strengths                                                                         | Gaps for Our Use                                                          |
| ----------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Cronometer** (pro)                | Tracks nutrients vs RDI, can export CSV, supports custom foods.                   | No optimization, no link to farm inventory, manual data entry heavy.      |
| **Open Food Facts + Nutrient DBs**  | Massive open food composition database.                                           | Just data; no menu optimization or cost modelling.                        |
| **ESHA Food Processor / NutriBase** | Professional diet analysis & planning, supports custom ingredients.               | Expensive, closed-source, no farm integration, no feed coupling.          |
| **NutriSurvey**                     | Free, used in nutrition projects, basic linear programming for diet optimization. | Designed for humanitarian contexts; limited to human diets, manual setup. |
| **Optimeal**                        | Pet/human diet optimization, nutrient balancing.                                  | Proprietary, narrow species focus, no multi-species coupling.             |

---

## **2. Livestock/fish feed formulation**

These focus on least-cost ration formulation but don’t consider human diets or shared resource planning.

| Tool                                                                  | Strengths                                             | Gaps for Our Use                                                           |
| --------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------- |
| **WinFeed**                                                           | Windows app, least-cost formulation, can handle fish. | Closed-source, manual ingredient input, no integration with crops/harvest. |
| **BestMix / Format International**                                    | Industry-grade formulation software.                  | Expensive, locked-in, no farm-scale coupling.                              |
| **AquaFeed Formulation Software (various)**                           | Targeted to aquaculture species.                      | Proprietary, no human diet features, no on-farm resource matching.         |
| **Open Forage Ration Balancers** (DairyNZ, Feedipedia + spreadsheets) | Open data, known formulas.                            | Manual, species-limited, no central orchestrator.                          |

---

## **3. Farm resource planners**

These manage inventory/yields but not nutrient optimization.

| Tool                         | Strengths                                        | Gaps for Our Use                 |
| ---------------------------- | ------------------------------------------------ | -------------------------------- |
| **OpenFarm**                 | Open API for plant growing info.                 | No yield-to-diet integration.    |
| **Tend / Agrivi / FarmLogs** | Crop planning, yield tracking.                   | No diet/feed optimization layer. |
| **OpenAgInitiative**         | Community-driven controlled environment ag data. | Early stage; not an optimizer.   |

---

## **4. Research / academic prototypes**

Some projects come close conceptually:

* **FAO’s Diet Problem Linear Programming Spreadsheets** — Excel LP models for least-cost human diets with local foods.
* **Nutrient Optimiser** — open-source nutrient density tool, some LP diet functions.
* **Feedipedia + linear programming** — used in animal nutrition teaching.
* **SustainFarm project tools** — model integration of crop-livestock production for sustainability, but not interactive.

---

## **What’s Missing (Our Niche)**

We want one platform that:

* Pulls **real-time and forecast inventory** from farm production (LES/Aquaponics-Calculator).
* Uses **nutrient composition tables** for both human food and feed ingredients.
* Runs **multi-objective optimization** for:

  * Human diet plans that hit RDI and preferences.
  * Animal/fish feed formulas that hit species requirements.
* Minimizes **off-farm supplement purchases**.
* Feeds outputs into **LES scenarios** and **real-world automation**.

None of the tools above do all of this — the closest is to combine:

* Open nutrient DBs (AUSNUT, USDA FDC, Feedipedia).
* Open LP solvers (PuLP, OR-Tools, SciPy).
* Our existing **Aquaponics-Calculator** + LES data model.

---
Because we are cohabitating with our domesticated animals, we work on the presumption of ourselves as the active catalyst within the einvornment, and thus treat it as two tightly-coupled planners as a beginning point:

1. human **food design** (menus/recipes) using what you grow, topped up with supplements;
2. **feed design** for your fish (and plants via nutrient dosing), using on-farm inputs + targeted amino/mineral adds.

I’ll lay out goals, data you need, the optimization models, and how it plugs into your Aquaponics-Calculator + LES stack.

# What we’re building

* A **least-cost, nutrient-complete** *menu builder* for humans and *feed formulator* for fish, both driven by **what’s actually available on the farm** (seasonal harvests, yields) with the option to **buy only the gaps**.
* It runs weekly: ingests inventory & expected harvests → proposes menus/feeds that meet targets (nutrient RDIs / species requirements) → outputs **shopping/supplement list** + **production tasks**.

# Core datasets (add these tables)

* `ingredients` (humans) / `feed_ingredients` (fish): name, unit, cost/kg, **nutrient vector** (see below), allergens, processing losses (%), stock\_on\_hand, lead\_time, source={farm, supplier}.
* `nutrients`: id, name, unit, upper/lower bounds per **persona** (humans) or **species+life\_stage** (fish).
* `recipes` (humans): many-to-many `recipe_items` with grams per serving; processing: yield factor, cook loss (protein, vit C, etc.).
* `menus`: 7-day plan mapping people → recipes.
* `feed_formulas`: inclusion rates (% DM) → pellet size → daily ration by biomass.
* `harvest_forecasts`: item, expected\_kg, availability\_window.
* `supplements`: amino acids (lysine, methionine, threonine), vitamins/minerals, salt mix, oils.
* `constraints`: user prefs (vegan, allergies), cultural constraints, max inclusion rates (e.g., **duckweed ≤ 30% DM**, **BSFL ≤ 20% DM**, **azolla ≤ 15% DM** unless proven).

## Nutrient vectors

* **Humans**: energy, protein, **DIAAS** adj. protein, fat, n-6, n-3 (ALA/EPA/DHA), carbs, fibre, Ca, Fe (heme/non-heme), Zn, Mg, K, Na, I, Se, Cu, Mn, B12, folate, choline, vit A (RAE), D, E, K, C, B1/2/3/5/6/7. Include **bioavailability modifiers** (e.g., phytate → Fe/Zn).
* **Fish (tilapia/trout as examples)**: energy (MJ/kg), digestible protein, essential AAs (Lys, Met+Cys, Thr, Trp, Arg, Ile, Leu, Val, His, Phe+Tyr), lipid (n-3 HUFA targets for species), starch limit, fibre limit, Ca, P (digestible), NaCl, vitamin premix, ash max.

# Optimization models

## A) Human menus (weekly)

**Decision vars**

* $x_{i,d,m}$ grams of ingredient *i* used on day *d*, meal *m* (or recipe servings $y_{r,d,m}$).

**Objective**

* Minimize **purchased cost** $\sum c_i \cdot \max(0, \text{use}_i - \text{farm}_i)$
  or multi-objective: *cost – λ·farm\_utilization + μ·GHG\_intensity reduction*.

**Constraints**

* Nutrient coverage per person/day:
  $L_k \le \sum_i n_{ik} \cdot x_{i,d,\*} \le U_k$ for all nutrients *k*.
* Inventory & harvest windows:
  $\sum_{d} x_{i,d,\*} \le \text{stock}_i + \text{harvest}_i$.
* Meal structure (e.g., 3 meals/day), max prep time per day, kitchen capacity (optional).
* Dietary prefs: allergens $x_{i,\*,\*}=0$, vegetarian etc.
* Processing losses: apply yield matrices to cooked recipes.
* Variety/acceptability (soft): minimum distinct recipes per week, cap repeats.

**Solvers**

* Start with **OR-Tools CP-SAT** or linear programming (PuLP/OR-Tools LP); add integer vars for recipe servings.

## B) Fish feed formulation (batch)

**Decision vars**

* $z_j$ inclusion fraction of feed ingredient *j* (DM basis).

**Objective**

* Least cost: minimize $\sum_j c_j z_j$.

**Constraints**

* Target nutrient ranges (digestible basis):
  $L_a \le \sum_j AA_{ja} z_j \le U_a$ (for all essential amino acids),
  lipid range, fibre max, starch max, **Ca\:P digestible ratio**, ash max.
* Functional caps: e.g., **BSFL oil ≤ x%**, **duckweed ≤ y%**, **azolla ≤ y%**, **microalgae** inclusion for EPA/DHA.
* Pellet physics (optional): sum binders ≥ min, moisture target.
* Regularization (palatability): keep big changes small vs last formula (ℓ1 penalty).

**Solvers**

* Pure LP with bounds; switch to **QP** if you add smoothness penalties.

### C) Coupling with operations

* Daily ration $R = f(BW, T, SGR)$ → from your TGC growth model.
* Check **oxygen budget** vs planned feed; bump aeration if needed (your HA automation).

# On-farm ingredient strategy (what to grow/produce)

* **Protein**: duckweed, azolla, water spinach, microgreens; **BSF larvae** (on farm waste); **red wrigglers**; legumes (if space).
* **Lipids (n-3)**: microalgae (Nannochloropsis), flax/chia (ALA) + small **fish oil** supplement for HUFA (species dependent).
* **Minerals**: eggshell → CaCO₃; Mg via Epsom salt; K via ash/K₂SO₄; Fe chelate for plants.
* **Human staples**: leafy greens, herbs, tomatoes, peppers, cucumbers; grains/pulses optionally off-farm.
* **Processing**: fermentations (tempeh/koji) to boost **DIAAS**, reduce antinutrients; sprouting for vit C/folate; solar dehydration for shelf-stable veg powders.

# Bioavailability & safety

* Apply **phytate\:Zn** and **phytate\:Fe** penalty functions to adjust effective intake.
* **HACCP** steps for feed/food: critical control points (water activity, pH after fermentation, storage temps, mycotoxin risk in BSF/feeds), traceability logs.

# How this plugs into your stack

**Aquaponics-Calculator**

* Add endpoints: `/optimize/human-menu`, `/optimize/fish-feed`.
* Ingest: `harvest_forecasts`, `ingredients`, `nutrients`, `supplements`, `prices`.
* Emit: menu PDFs/shopping list; feed formula + pellet batch sheet.
* Tie to **alerts**: if optimizer requires off-farm purchase > threshold, flag “deficit” and suggest which crop/supplement closes the gap.

**LES (Environment Simulator)**

* Scenario linkage: change planting density → changes expected harvest → changes feasible menu/feed space; conversely, nutrition targets can imply required cropland/bed area.
* Water/N balance: feed protein → TAN load → plant uptake requirement; close loops automatically.

# Minimal viable feature set (2 sprints)

**Sprint 1**

* Data model + ingestion (AUSNUT/USDA FoodData Central for humans; feed tables for fish + your on-farm items).
* LP feed formulator (tilapia starter/grower/finisher as a template).
* Menu LP for 1 adult persona; cost + farm-first objective.
* Exporter: shopping list (off-farm) + harvest utilization plan.

**Sprint 2**

* Processing losses & DIAAS adjustment; phytate penalty.
* TGC-driven ration + oxygen budget check → HA aeration target.
* Preference/variety constraints, simple weekly UI.
* “What to plant next” recommender: marginal gain in menu/feed feasibility per crop m².

# Example: tiny LP (fish feed) in math

Minimize $\sum_j c_j z_j$
s.t.

* $\sum_j z_j = 1$
* Protein: $\sum_j DP_j z_j \ge 0.34$ (34% DP grower)
* Lys: $\sum_j Lys_j z_j \ge 0.018$
* Met+Cys: $\sum_j MetCys_j z_j \ge 0.009$
* Lipid: $0.08 \le \sum_j Fat_j z_j \le 0.12$
* Fibre: $\sum_j Fibre_j z_j \le 0.06$
* Digestible P: $\sum_j dP_j z_j \ge 0.006$
* BSFL ≤ 0.20, Duckweed ≤ 0.30, Azolla ≤ 0.15, Binder ≥ 0.03.

# Example: weekly human menu (sketch)

* Personas: Adult M 10.5 MJ, Adult F 8.5 MJ.
* Hard constraints: protein ≥ 1.0 g/kg BW; Ca ≥ 1000 mg; Fe ≥ 8/18 mg (sex-specific); B12 ≥ 2.4 µg; omega-3 ALA ≥ 1.6/1.1 g; sodium ≤ 2 g.
* Farm inputs favored: lettuce, basil, cherry tomato, kale, tilapia, duckweed powder, microgreens, eggs, herbs.
* Optimizer proposes meals; **supplement list** might be: iodized salt, B12 (if mainly plant-based), Vit D in winter, small fish oil for DHA/EPA if desired.

# Safety & compliance

* Keep human nutrition targets aligned with **NHMRC (Australia) NRVs**;
  fish feed targets from species literature; log sources in metadata.
* Label allergens, maintain traceability for every batch.





Here’s a side-by-side framing of **our Aquaponics-Calculator + Environment Simulator** vs. a variety of plant/gardening data APIs.

---

## **Scope & Purpose**

|                      | **Our Stack**                                                                                                     | **Listed APIs (Perenual, Verdantly, etc.)**                                             |
| -------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Primary domain**   | Dynamic simulation + monitoring of live systems (water chemistry, fish/plant growth, weather, erosion, wildlife). | Static botanical/cultivation metadata — species traits, planting advice, climate zones. |
| **Use case**         | Real-time control, forecasting, decision support for aquaponics, aquaculture, and larger landscape models.        | Garden planning, plant identification, care scheduling, species databases.              |
| **Integration role** | Acts as the *engine* + *data manager* for live operations.                                                        | Acts as a *reference library* or enrichment source for species data.                    |

---

## **Data Model**

|                            | **Our Stack**                                                                                                               | **Listed APIs**                                                                     |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Entities**               | Species + live stock batches, sensors, water chemistry readings, feed logs, growth records, hardware, events.               | Species + static attributes (soil type, watering needs, hardiness, flowering time). |
| **Temporal aspect**        | Time-series, high-frequency sensor logs, calculated KPIs, forecasts.                                                        | Mostly static; some seasonal planting windows.                                      |
| **Environmental coupling** | Yes — pH/temp/DO affect plant/fish growth; environment simulator couples weather, hydrology, erosion, vegetation, wildlife. | Indirect — climate zone tags; no continuous environmental feedback.                 |

---

## **Technical Depth**

|                | **Our Stack**                                                                             | **Listed APIs**                                              |
| -------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **Analytics**  | FCR, SGR, nutrient balances, DO saturation, NH₃ toxicity, erosion rates, habitat changes. | Minimal; mostly filter/search functions.                     |
| **Simulation** | Multi-domain coupling (weather, hydrology, geomorphology, vegetation, wildlife).          | None; purely data retrieval.                                 |
| **Automation** | Hooks to Home Assistant/MQTT for actuators (aeration, dosing, feeding).                   | None; external systems must decide what to do with the data. |

---

## **Where They Complement Us**

* **Species trait enrichment**:
  We could pull from **Perenual, APIFarmer, Trefle** to populate our `species` table with growth ranges, tolerances, nutrient needs, and phenology.
* **Garden planning intelligence**:
  Verdantly-style recommendations could be an “advisory layer” in our dashboard for selecting compatible crops or plants in aquaponics beds.
* **Climate zone mapping**:
  APIs with USDA/FAO zone data could pre-set defaults in scenarios for the Environment Simulator.

---

## **Where We Surpass Them**

* Live feedback loops (sensor data → analytics → control).
* Multi-species, multi-domain simulation.
* Direct actuation for real-world systems.
* Scenario forecasting (what-if storms, droughts, feed changes).

---

## **Integration Example**

Imagine LES + Aquaponics-Calculator running a simulated or real system:

1. **Species data import** from APIFarmer → populate plant nutrient uptake and tolerance.
2. **Weather forcing** from WRF or ERA5.
3. **Simulation loop**:

   * Forecast evapotranspiration & nutrient loads.
   * Adjust irrigation/nutrient dosing via Home Assistant.
4. **Visualize** growth progression and environmental impact over months/years.

---













Working:




## 0) Sets and indices

* Time steps (within 1 year):
  [
  t \in {1,\dots,T}
  ]
  Choose (T) (e.g. 4 seasonal slots, or 6–8 crop windows).

* Beds/fields (optional, for multi-block planning):
  [
  b \in {1,\dots,B}
  ]

* Crop/guild actions (your palette):
  [
  c \in \mathcal{C},\quad |\mathcal{C}| = 10 \text{ (example)}
  ]

* Input actions (KNF, compost, minerals, purchased fert, irrigation events):
  [
  i \in \mathcal{I}
  ]

* Livestock management actions (graze, rest, move poultry tractor, cut-and-carry):
  [
  \ell \in \mathcal{L}
  ]

We bundle “what you do at time (t)” into one **composite action**:
[
a_t = (c_t, i_t, \ell_t)
]
Some components can be “none”.

---

## 1) State

### 1.1 Bed/field state (per bed (b))

A minimal, rotation-capable soil + memory state:

[
x_{t}^{(b)} = \big(N_{t}^{(b)},, C_{t}^{(b)},, S_{t}^{(b)},, F_{t}^{(b)},, D_{t}^{(b)}\big)
]

Where (use either buckets or physical units):

* (N): available fertility / N-credit bucket (or kg/ha available N)
* (C): soil carbon/OM bucket (or %SOC / tC/ha proxy)
* (S): soil structure bucket (compaction/aggregate proxy)
* (F): last crop family / pressure class (categorical)
* (D): disease/pest pressure bucket (optional but useful)

**Minimal-minimal** is ((N,C,S,F)). (D) can be derived from (F) with a rule, but explicit (D) is cleaner.

### 1.2 Farm-global resource state (shared across beds)

This is where KNF + livestock constraints live:

[
g_t = (W_t,, L_t,, A_t,, K^N_t,, K^C_t,, K^K_t,, M_t,, B_t,, P_t,, Z_t)
]

You can drop what you don’t need; the minimal useful subset is:

* (W_t): water budget (kL)
* (L_t): labor hours budget
* (A_t): “processing area / capacity” (e.g., barrel space, compost bays)
* (K^N_t): KNF “N-equivalent credits” available
* (K^C_t): carbon/compost/mulch credits available
* (M_t): manure credits available (or split N/P/K)
* (B_t): available forage/biomass (if grazing)
* (P_t): parasite pressure (if ruminants)
* (Z_t): stocking / head-days capacity remaining (optional)

**Key idea:** KNF and livestock are not “vibes”; they are *stocks and flows* that appear in the same balance as fertility and costs.

### 1.3 Full system state

Single bed:
[
X_t = (x_t, g_t)
]

Multiple beds:
[
X_t = \big(x_t^{(1)},\dots,x_t^{(B)},, g_t\big)
]

---

## 2) Actions

At each step (t) and bed (b):

### 2.1 Crop/guild action (c_t^{(b)} \in \mathcal{C})

Each crop/guild has attributes:

* family: (fam(c))
* revenue: (Rev_t(c)) (may depend on season (t))
* variable cost: (Cost_t(c))
* resource demands: (w(c), \ell(c)) etc.
* soil impacts: (\Delta_N(c), \Delta_C(c), \Delta_S(c))
* nutrient demand vector (optional): (dem(c) = (n(c),p(c),k(c)))

You can interpret (\Delta_N(c)) as nutrient removal, or as “net effect given typical residue return”.

### 2.2 Input action (i_t \in \mathcal{I})

Inputs are **production** and/or **application** operations, e.g.:

* produce KNF N: `make_KNF_N`
* apply KNF N to bed (b): `apply_KNF_N(b, u)`
* compost production: `make_compost`
* compost application: `apply_compost(b, u)`
* purchased fertiliser: `buy_N(u)`
* irrigation event: `irrigate(u)` (or water is baked into crop demand)

Each input action consumes resources and adds to either farm stocks or bed soil:

* consumes: water/labor/space/money/biomass
* produces: (K^N, K^C,) etc., or directly increases (N,C,S) on a bed

### 2.3 Livestock action (\ell_t \in \mathcal{L})

Examples:

* graze paddock/cover on bed (b) (ruminants)
* poultry tractor pass on bed (b)
* rest/recovery (no animals)
* cut-and-carry biomass into compost system

Livestock actions have:

* revenue: eggs/milk/meat value (or can be modelled separately)
* costs: labor, feed, water, fencing moves
* soil effects: manure adds (N/C), but traffic can reduce (S)
* forage/manure flows: (\Delta B, \Delta M)
* parasite pressure updates: (\Delta P)

---

## 3) Deterministic transition function

### 3.1 Bed transition

For each bed (b):
[
x_{t+1}^{(b)} = T_{bed}\big(x_t^{(b)},, c_t^{(b)},, i_t,, \ell_t,, g_t\big)
]

In the simple additive bucket model:
[
\begin{aligned}
N' &= clamp(N + \Delta_N(c) + \Delta_N(i,\ell),, 0..N_{\max})\
C' &= clamp(C + \Delta_C(c) + \Delta_C(i,\ell),, 0..C_{\max})\
S' &= clamp(S + \Delta_S(c) + \Delta_S(i,\ell),, 0..S_{\max})\
F' &= fam(c) \quad (\text{or unchanged if } c=\text{none})\
D' &= clamp(D + \Delta_D(c,F,D) + \Delta_D(\ell),, 0..D_{\max})
\end{aligned}
]

A good deterministic disease rule is:

* if you repeat family too soon → (D) increases
* if you break family → (D) decreases
* livestock/poultry pass can decrease (D) for some pests but might increase for others; keep it coarse.

### 3.2 Global resource transition

[
g_{t+1} = T_{farm}(g_t, {c_t^{(b)}}_b, i_t, \ell_t)
]

Typical updates:

* (W' = W - \text{water used by crops and inputs})
* (L' = L - \text{labor used})
* (A' = A - \text{space occupied}) (or capacity constraint per step)
* (K^N) increases when you *make* KNF inputs, decreases when you *apply* them
* (B) (forage) decreases when grazed, increases under rest/growth/cover crops
* (M) (manure credits) increases with grazing/stocking, decreases when applied/exported
* (P) (parasites) increases with grazing pressure, decreases with rest windows

Everything is deterministic: fixed deltas per action (or piecewise by state bucket).

---

## 4) Constraints (soil maintenance + feasibility)

### 4.1 Soil invariants (hard)

For all (t) and beds (b):
[
N_t^{(b)} \ge N_{\min},\quad C_t^{(b)} \ge C_{\min},\quad S_t^{(b)} \ge S_{\min}
]

Optionally:
[
D_t^{(b)} \le D_{\max}
]

### 4.2 Rotation constraints (hard)

Examples:

* No same family back-to-back:
  [
  fam(c_t^{(b)}) \ne F_t^{(b)}
  ]

* Cooldown of length (k): keep last (k) families in state, forbid repeats (still deterministic; state includes a short history).

### 4.3 Resource constraints (hard)

Per step:
[
W_t \ge 0,\quad L_t \ge 0,\quad A_t \ge 0,\quad K^N_t \ge 0,\quad \dots
]

Livestock-specific:

* forbid grazing if soil too wet/fragile:
  [
  \text{if } S_t^{(b)} \le S_{wet} \text{ then grazing action disallowed}
  ]
  (or use a separate “traffic risk” scalar if you want).

---

## 5) Reward / profit model

Per step (t), total profit is:

[
R_t(X_t, a_t) =
\sum_{b=1}^{B}\Big( Rev_t(c_t^{(b)}) - Cost_t(c_t^{(b)})\Big)
;-; Cost_t(i_t);-;Cost_t(\ell_t)
]

Where costs include:

* labor valued at a wage (or opportunity cost)
* water at marginal cost
* materials (fish hydrolysate, sugars, minerals, bedding)
* depreciation if you want

### Soil not just “maintained”, but incentivized

If you only use hard minima, the optimizer tends to “hug the boundary”. Add an end-of-year soil value:

[
R_{terminal}(X_{T+1}) = \lambda_N \sum_b N_{T+1}^{(b)} + \lambda_C \sum_b C_{T+1}^{(b)} + \lambda_S \sum_b S_{T+1}^{(b)}
]

This makes it prefer soil-positive plans when profit differences are small.

---

## 6) The optimization problem

### Single bed (DP)

[
\max_{a_1,\dots,a_T} \sum_{t=1}^{T} R_t(X_t,a_t) + R_{terminal}(X_{T+1})
]
subject to:
[
X_{t+1} = T(X_t,a_t),\quad X_t \in \text{Feasible} ;\forall t
]

### Multiple beds with coupling (MIP recommended)

If beds share labor/water/KNF stocks, the optimal choice is a coupled optimization. DP can still work if you keep global state small; MIP scales better.

---

## 7) Solution methods

### 7.1 Deterministic Dynamic Programming (exact, easy for 1 bed)

Value function:
[
V_t(X_t) = \max_{a_t \in \mathcal{A}(X_t)} \left(R_t(X_t,a_t) + V_{t+1}(T(X_t,a_t))\right)
]
with (V_{T+1} = R_{terminal}).

Works great when state is bucketed and small.

### 7.2 Mixed Integer Programming (exact, best for many beds)

Binary decision variables like:

* (y_{t,b,c} \in {0,1}): choose crop (c) on bed (b) at time (t)
* (u_{t,i}\ge 0): amount of input action (i) at time (t)
* (z_{t,\ell}\in{0,1}): livestock action choices

Then linear constraints enforce:

* one crop per bed per step
* resource budgets
* soil bucket transitions (piecewise linear or discretized)
* rotation rules
  Objective is linear: maximize revenue minus costs.

---

## 8) Data schema (what you must supply)

### Crop/guild record

* `name`
* `family`
* `rev[t]` (or price × yield model)
* `cost[t]`
* `water[t]`, `labor[t]`
* `delta_soil`: `(ΔN, ΔC, ΔS, ΔD)` buckets
* optional: `nutrient_demand`: `(n,p,k)` physical units

### Input record (KNF / compost / purchased)

* `name`
* `type`: `produce` or `apply` or `buy`
* resource consumption: labor, water, space, money, biomass
* stock changes: `ΔK^N`, `ΔK^C`, `ΔM`, etc.
* bed effect if applied: `ΔN,ΔC,ΔS`

### Livestock record

* `name`
* revenue/cost per step
* forage consumption / manure production
* soil and disease impacts
* guards (e.g., minimum structure or maximum wetness)

### Feasibility thresholds

* soil minima ((N_{\min}, C_{\min}, S_{\min}))
* disease max (D_{\max})
* resource budgets per step ((W_t,L_t,A_t,\dots))

---

## 9) Deterministic “dispatch” policy view (state machine)

The whole thing is a deterministic automaton with an optimal controller:

* **States:** (X_t)
* **Actions:** (a_t)
* **Transition:** (X_{t+1}=T(X_t,a_t))
* **Accepting states:** Feasible (soil maintained, resources nonnegative)
* **Controller:** chooses (a_t) to maximize cumulative reward

So: **state machine + optimizer = most profitable feasible rotations**.












---

# 🌱 Integrated Farm Optimization Formalism

**(Crops + KNF Inputs + Livestock + Soil Invariants)**

---

# 1. Time

Discrete time horizon:

[
t \in {1,2,\dots,T}
]

For 1-year planning:

* (T = 4) (quarters), or
* (T = 6\text{–}8) (market garden windows)

---

# 2. Sets

* Beds: (b \in {1,\dots,B})
* Crop actions: (c \in \mathcal{C})
* Input actions: (i \in \mathcal{I})
* Livestock actions: (\ell \in \mathcal{L})

Composite action per bed per time:

[
a_t^{(b)} = (c_t^{(b)}, i_t^{(b)}, \ell_t^{(b)})
]

Global actions (shared resources) allowed if needed.

---

# 3. State Space

## 3.1 Bed State

For each bed (b):

[
x_t^{(b)} =
(N_t^{(b)}, C_t^{(b)}, S_t^{(b)}, F_t^{(b)}, D_t^{(b)})
]

Where:

* (N) = fertility bucket (0…5)
* (C) = soil carbon bucket (0…5)
* (S) = structure bucket (0…5)
* (F) = last crop family (categorical)
* (D) = disease/pest pressure bucket (0…5)

Minimal version removes (D).

---

## 3.2 Global Farm Resource State

[
g_t =
(W_t, L_t, A_t, K^N_t, K^C_t, M_t, B_t, P_t)
]

Where:

* (W_t) = water available
* (L_t) = labor hours available
* (A_t) = input production capacity (space)
* (K^N_t) = KNF nitrogen credits
* (K^C_t) = compost/carbon credits
* (M_t) = manure credits
* (B_t) = forage biomass
* (P_t) = parasite pressure

Minimal subset:
[
(W, L, K^N, K^C, B)
]

---

## 3.3 Full System State

[
X_t = \big(x_t^{(1)},\dots,x_t^{(B)}, g_t\big)
]

---

# 4. Action Definitions

## 4.1 Crop Action (c)

Each crop (c \in \mathcal{C}) defines:

* (fam(c))
* Revenue (Rev_t(c))
* Cost (Cost_t(c))
* Resource use (w(c), \ell(c))
* Soil deltas:
  [
  \Delta(c) = (\Delta_N, \Delta_C, \Delta_S, \Delta_D)
  ]

---

## 4.2 Input Action (i)

Each input action defines:

* Resource consumption:
  [
  (\Delta W, \Delta L, \Delta A)
  ]
* Stock production:
  [
  (\Delta K^N, \Delta K^C, \Delta M)
  ]
* Optional direct soil effects if applied.

Example:

* `make_KNF_N`:
  ( \Delta L = -2,; \Delta W = -1,; \Delta K^N = +3 )

* `apply_KNF_N(b,u)`:
  ( K^N -= u,; N^{(b)} += u )

---

## 4.3 Livestock Action (\ell)

Defines:

* Revenue (Rev(\ell))
* Costs (Cost(\ell))
* Soil impact:
  [
  (\Delta_N^\ell, \Delta_C^\ell, \Delta_S^\ell)
  ]
* Biomass/manure flow:
  [
  \Delta B,; \Delta M
  ]
* Parasite update:
  [
  \Delta P
  ]

Example:

* Poultry pass:

  * ( \Delta_N = +1 )
  * ( \Delta_S = -1 ) (if overworked)
  * revenue from eggs
  * labor cost

---

# 5. Deterministic Transition Function

## 5.1 Bed Transition

For each bed:

[
\begin{aligned}
N' &= clamp(N + \Delta_N(c) + \Delta_N(i,\ell), 0, 5) \
C' &= clamp(C + \Delta_C(c) + \Delta_C(i,\ell), 0, 5) \
S' &= clamp(S + \Delta_S(c) + \Delta_S(i,\ell), 0, 5) \
D' &= clamp(D + \Delta_D(c,\ell), 0, 5) \
F' &= fam(c)
\end{aligned}
]

All transitions are deterministic.

---

## 5.2 Global Resource Transition

[
g_{t+1} = g_t + \sum \Delta(\text{inputs}) + \sum \Delta(\text{livestock}) - \sum \Delta(\text{crop resource use})
]

Subject to:

[
W_t, L_t, A_t, K^N_t, K^C_t, B_t \ge 0
]

---

# 6. Constraints

## 6.1 Soil Invariants (Hard)

For all (t,b):

[
N_t^{(b)} \ge N_{\min}
]
[
C_t^{(b)} \ge C_{\min}
]
[
S_t^{(b)} \ge S_{\min}
]

---

## 6.2 Rotation Constraint

No same family consecutively:

[
fam(c_t^{(b)}) \ne F_t^{(b)}
]

Extendable to k-period memory.

---

## 6.3 Livestock Guardrails

Example:

If (S_t^{(b)} \le S_{wet}), grazing disallowed.

If (P_t \ge P_{max}), force rest action.

---

# 7. Objective Function

Total profit over horizon:

[
\max_{a_1,\dots,a_T}
\left(
\sum_{t=1}^{T} R_t(X_t,a_t)

* R_{terminal}(X_{T+1})
  \right)
  ]

Where:

[
R_t =
\sum_b \big(Rev(c_t^{(b)}) - Cost(c_t^{(b)})\big)

* Cost(i_t)
* Cost(\ell_t)
  ]

Optional terminal soil value:

[
R_{terminal} =
\lambda_N \sum_b N_{T+1}^{(b)}
+
\lambda_C \sum_b C_{T+1}^{(b)}
+
\lambda_S \sum_b S_{T+1}^{(b)}
]

---

# 8. Solution Methods

### Single bed

Dynamic Programming:

[
V_t(X) = \max_{a \in \mathcal{A}(X)} \left( R_t(X,a) + V_{t+1}(T(X,a)) \right)
]

### Multi-bed

Mixed Integer Programming (binary crop decisions + linear soil/resource updates).

---

# 9. Minimal Implementable Instance (1-Year, 4 Slots)

State buckets:

* (N,C,S \in {0,\dots,5})
* Families: {Solanaceae, Brassica, Cucurbit, Legume, Allium}

Actions:

* 10 crop options
* 2 input actions (make/apply KNF)
* 1 livestock action (poultry pass)
* 1 rest action

Constraints:

* Soil ≥ (2,2,2)
* No family repeat

That system is:

* Fully deterministic
* Economically optimizing
* Soil-constrained
* KNF-aware
* Livestock-aware

---

# 10. Conceptual Summary

This formalism models the farm as:

[
\textbf{Deterministic State Machine}
+
\textbf{Resource Balance System}
+
\textbf{Constrained Optimal Control Problem}
]

Crops extract.
KNF converts labor/biomass → fertility.
Livestock converts forage → manure + revenue.
Soil state enforces long-term viability.
Optimizer selects the profit-maximizing feasible trajectory.






# **LES + Farm-to-Plate-and-Pond roadmap**


# 🔁 1. Close the Nutrient Loop (Mass-Balance Extension)

Right now, soil fertility is bucketed. LES explicitly models:

* nutrient flows between water, soil, plants, animals 

So extend soil state from buckets to **explicit mass balance**:

### Add State Variables

For each bed:

[
x_t^{(b)} =
(N_t, P_t, K_t, C_t, S_t, F_t, D_t)
]

And for water bodies (aquaponics or pond):

[
w_t =
(TAN_t, NO_2_t, NO_3_t, PO_4_t, DO_t)
]

Now crop uptake becomes:

[
N_{t+1} = N_t - U_N(c) + M_N(\ell,i)
]

Fish feed becomes:

[
TAN_{t+1} = TAN_t + f(\text{protein input}) - nitrification
]

Plants remove:

[
NO_3_{t+1} = NO_3_t - U_{NO3}(plant)
]

This integrates aquaponics nutrient cycling *directly* into crop fertility and removes the artificial separation between soil and water fertility.

---

# 🌧 2. Weather & Climate Forcing (LES Coupling)

LES includes:

* weather
* hydrology
* evapotranspiration 

Add exogenous climate forcing:

[
\omega_t = (Rain_t, Temp_t, Solar_t, Wind_t)
]

Now crop yield becomes:

[
Yield(c,t) = Y_{base}(c) \cdot g(N_t, C_t, S_t, \omega_t)
]

Water budget:

[
W_{t+1} = W_t + Rain_t - ET_t - Irrigation_t
]

This turns the optimizer into:

> Optimal control under stochastic environmental forcing.

Now you can:

* simulate drought years
* evaluate irrigation investment
* test windbreak planting effect on evapotranspiration

---

# 🐄 3. Energy & Oxygen Budgets

Your roadmap includes automation and oxygen hooks.

Add:

For aquaculture:

[
DO_{t+1} = DO_t + Aeration_t - O_2_consumption(fish, microbes)
]

Constraint:

[
DO_t \ge DO_{critical}
]

Now feed formulation directly affects oxygen risk.
The optimizer may reduce protein % or increase aeration if electricity cost is lower.

This creates a real energy-nutrient tradeoff.

---

# 💰 4. Capital & Infrastructure State

LES supports management interventions.

Add infrastructure state:

[
I_t = (Greenhouse_area, Tank_volume, Aerator_capacity, Fencing_capacity)
]

Actions may include:

* build greenhouse
* add tank
* install aerator

State evolves:

[
I_{t+1} = I_t + Build_t
]

Add depreciation + capital constraint.

Now you can optimize:

* whether expanding tank volume is better than buying feed
* whether windbreak reduces irrigation cost enough to justify planting

This moves the model from “rotation optimizer” to **farm growth optimizer**.

---

# 📈 5. Risk & Uncertainty Layer

LES roadmap includes probabilistic reasoning.

Extend:

Let yield be stochastic:

[
Yield(c,t) = \bar{Y}(c,t) + \epsilon_t
]

Then solve:

* Expected profit maximization
* CVaR (Conditional Value at Risk)
* Robust optimization

Objective:

[
\max \mathbb{E}[Profit] - \rho \cdot Risk
]

Now the optimizer may choose diversified crops rather than high-margin monoculture.

---

# 🧠 6. Multi-Objective Optimization

Roadmap explicitly includes multi-objective optimisation 

Extend objective vector:

[
\max (Profit,; SoilHealth,; SelfSufficiency,; GHG,; Biodiversity)
]

Compute Pareto frontier via:

* NSGA-II
* ε-constraint method

This gives decision space instead of a single solution.

---

# 🐝 7. Biodiversity & Habitat Variable

LES includes wildlife & habitat modeling 

Add habitat index:

[
H_t = f(Cover, Crop\ Diversity, Hedgerows)
]

Constraint or objective:

[
H_t \ge H_{min}
]

Livestock + crop choices influence biodiversity.

---

# 🌱 8. Succession / Long-Term Soil Carbon

Right now soil is bounded bucket.

Add long-term carbon dynamics:

[
C_{t+1} = C_t + inputs - respiration(C_t, Temp_t)
]

Respiration increases with temperature → climate sensitivity.

This allows evaluation of:

* cover crop frequency
* grazing intensity
* compost use
* reduced tillage

---

# 🔄 9. Cross-Domain Coupling (Diet ↔ Feed ↔ Farm)

From the roadmap:

* diet optimizer shares ingredient pool with feed optimizer 

Add shared inventory:

[
Inventory_t = (Veg, Fish, Eggs, BSFL, Duckweed)
]

Human optimizer and feed optimizer both consume from:

[
Inventory_{t+1} = Inventory_t + Production_t - HumanUse_t - FeedUse_t
]

Now:

* eating more fish reduces feed demand
* feeding more BSFL reduces compost input
* planting more duckweed increases feed self-sufficiency

This is a **closed ecological-economical loop**.

---

# ⚡ 10. Automation Control Loop

Roadmap Phase 3 includes real-time adaptive control 

Add:

[
Control_t = \pi(X_t)
]

Where policy π is learned (RL or MPC).

This converts the system into:

> Model Predictive Control over a living farm.

---

# 🔬 11. Emergent Property Metrics

Add emergent indicators:

* Nutrient circularity ratio
* % On-farm protein
* Energy return on energy invested (EROEI)
* Net ecosystem productivity
* Water use efficiency

These are functions of state trajectory:

[
Metric = \Phi(X_1,\dots,X_T)
]

These allow evaluation beyond raw profit.

---

# 🧩 12. Formal Unification

The fully extended formalism becomes:

[
X_{t+1} = T(X_t, a_t, \omega_t)
]

[
a_t \in \mathcal{A}(X_t)
]

[
\max_{a_{1:T}} \sum_{t=1}^{T} R(X_t,a_t)
]

Subject to:

* Soil invariants
* Resource invariants
* Water & oxygen invariants
* Habitat invariants
* Capital constraints

Where:

[
X_t =
(\text{Soil}, \text{Water}, \text{Livestock}, \text{Inventory}, \text{Infrastructure}, \text{Climate})
]

This is a **deterministic hybrid dynamical system with constrained optimal control**.

---

# 🏁 What This Becomes

You now have:

* Farm rotation optimizer
* Nutrient loop optimizer
* Feed & diet co-optimizer
* Environmental simulator
* Infrastructure planner
* Risk-aware controller
* Automation-ready control core

That is no longer a “rotation planner.”

It is:

> A fully coupled agro-ecological optimal control system.
