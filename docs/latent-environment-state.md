# LES Latent Environment State and Model Hierarchy

## Status

This document records the current architectural direction for the Living Environment System (LES). It is a design contract, not a claim that every component is implemented.

LES is an open, GIS-native planning substrate for multidisciplinary climate adaptation, ecological restoration, farming, catchment management, and related land–water–food decisions. It does not replace specialist scientific models. It gives them a shared world state, coupling contracts, validation lanes, and a planning layer.

The central implementation principle is:

> Use authoritative process models to generate and validate reduced representations; perform broad spatial search and scenario exploration in efficient latent spaces; escalate selected or uncertain cases to higher-fidelity analysis.

Visualisation is a downstream client of the scientific world state rather than the owner of it.

---

## 1. The problem being solved

Environmental planning currently spans several incompatible tool families:

- GIS and remote sensing describe where things are.
- Hydrology, soil, nutrient, vegetation, fire, and ecological models estimate what happens.
- Farm-management and asset suites record operations.
- Optimisers search candidate actions.
- Rendering and game-engine systems efficiently represent detailed worlds.

These tools commonly disagree about grids, projections, units, timesteps, state semantics, uncertainty, and execution environments. Many scientific models are monolithic, file-coupled, CPU-oriented, and designed to evaluate a prescribed management plan rather than generate one.

LES should therefore standardise contracts rather than mandate a single engine, solver, storage backend, or renderer.

---

## 2. World state: graph, fields, volumes, events, and evidence

The LES world state is a spatial-temporal state with five complementary views.

### 2.1 Geospatial fields

Schema-bearing arrays or meshes represent continuous and categorical quantities such as:

- elevation, slope, curvature, flow accumulation;
- soil texture, depth, hydraulic conductivity, available water capacity;
- rainfall, temperature, radiation, wind, humidity, VPD;
- surface water, groundwater head, soil moisture, runoff and infiltration;
- nitrate, ammonium, phosphorus, salinity, dissolved oxygen and carbon pools;
- canopy height, LAI, roughness, fuel moisture and habitat suitability;
- prices, labour availability, fuel cost and operational accessibility.

Every field must declare units, CRS/grid, temporal support, ownership, uncertainty, valid range, and provenance.

### 2.2 Structural and ecological graphs

Graphs represent entities and relations that do not fit naturally into a raster alone:

- parcels, paddocks, roads, fences, pipes and waterways;
- trees, plant modules, root systems and canopy adjacency;
- river and drainage networks;
- ecological functional groups and interaction edges;
- pollination, predation, dispersal and nutrient-flow networks;
- machinery routes, labour tasks and supply chains.

A graph node may be linked to one or more spatial cells, volumes, observations, or management assets.

### 2.3 Sparse volumes and geometric proxies

Fine structural or physical coupling may use:

- signed-distance or level-set fields;
- porous canopy and root volumes;
- water occupancy and flood volumes;
- smoke, heat and fuel fields;
- LiDAR-derived crowns and tree skeletons.

The interchange contract matters more than a particular volume technology.

### 2.4 Events and interventions

Events are time-stamped changes such as:

- rainfall bursts, fire ignition, flood peaks and heatwaves;
- fertilisation, planting, harvest, thinning, grazing and irrigation;
- pump failure, fish feeding or aeration changes;
- pollution observations and regulatory restrictions.

Interventions are explicit candidate actions with footprint, schedule, cost, resource demand, eligibility conditions, expected effects and uncertainty.

### 2.5 Evidence and observations

Observations must remain distinguishable from model state. Sources include:

- GIS and remote-sensing products;
- LiDAR and point clouds;
- field samples and surveys;
- water-quality and soil tests;
- weather stations and IoT sensors;
- farm-management records;
- market and futures data.

LES should preserve the observation, preprocessing chain, uncertainty, and model-assimilation step separately.

---

## 3. Ecological representation

### 3.1 Functional groups first, species when required

LES should model ecology primarily through functional groups and guilds, while allowing species-specific refinement where conservation, regulation, or available evidence requires it.

Example functional groups include:

- nitrogen fixers, nutrient scavengers, deep-rooted perennials and riparian stabilisers;
- arbuscular and ectomycorrhizal fungi, saprotrophs and pathogens;
- managed honeybees, native solitary bees, hoverflies and nocturnal pollinators;
- grazers, browsers, predators, detritivores and soil engineers;
- submerged and floating macrophytes, phytoplankton and filter feeders.

### 3.2 Interaction graph

An interaction edge is not a universal scalar. It is conditional on context:

```text
source_group -> target_group
  effect: positive | negligible | negative
  mechanism: pollination | competition | predation | nutrient_transfer | habitat | disease | ...
  spatial_support: local | corridor | catchment | dispersal_kernel | flow_network
  temporal_support: season / phenological window / event window
  confidence: distribution or evidence grade
  conditions: soil, climate, density, management, species, scale
```

This allows LES to evaluate questions such as:

- Can fewer managed hives provide adequate crop pollination with less pressure on native bees?
- Which planting layout improves nesting, forage continuity and predator shelter trade-offs?
- Which mycorrhizal functional group is compatible with the target crop, soil and tillage regime?
- Which guild supports a threatened species without creating an unacceptable fire, pest or water-use burden?

### 3.3 Guilds

A guild is a reusable but parameterised interaction motif: a set of co-located functional groups and management conditions expected to produce a useful system-level effect.

Guilds are hypotheses, not recipes. They must carry climatic and edaphic validity ranges, evidence, failure modes and management requirements.

---

## 4. Multi-scale vegetation structure

LES may represent vegetation at several simultaneous depths:

1. landscape cells or cohorts;
2. individual plants or trees;
3. reusable structural modules such as stems, crowns, branches and roots;
4. fine geometry only where required by measurement, local physics, or visualisation.

This follows the useful module → plant → ecosystem pattern found in functional-structural and synthetic-silviculture work, but LES must distinguish structural plausibility from mechanistic physiological validity.

Remote sensing can initialise or constrain this hierarchy:

- ALS/LiDAR → terrain and canopy-height models;
- crown segmentation → individual-tree footprints and heights;
- point-cloud skeleton reconstruction → stem/branch graphs;
- repeated observations → growth, mortality and disturbance evidence.

Derived structural outputs can drive microclimate, interception, roughness, habitat, fuel, biomass and nutrient demand.

---

## 5. Continuous envelope over discrete depth

LES may use balanced ternary observables for compact, auditable effect states:

\[
T = \{-1,0,+1\}.
\]

A depth stream is

\[
d=(d_0,d_1,\ldots)\in T^{\mathbb N},
\]

where depth denotes scale or explanatory refinement. A continuous envelope is obtained by fixing \(0<\lambda<1\) and defining

\[
\Phi(d)=\sum_{k\ge 0} d_k\lambda^k.
\]

The intended claims are deliberately limited:

- \(\Phi\) is continuous;
- it is injective when \(\lambda<1/3\);
- its image is Cantor-like rather than a smooth manifold;
- Euclidean analysis is performed after embedding, not directly on the 3-adic or digit space.

The associated depth metric is controlled by the first differing digit and therefore preserves the cylinder-set notion of nearness: states are close when they agree to deep resolution.

For LES:

- shallow depth represents coarse functional effects or planning regimes;
- deeper digits activate species, chemistry, geometry or timing detail;
- truncation is a controlled coarse-graining operation;
- additional depth incurs complexity, compute and evidence costs.

Ternary effects must not replace quantitative state. They are decision-facing observables derived from latent real quantities and must retain thresholds, confidence and provenance.

---

## 6. Graph–Latent Environment State (GLES)

GLES is the proposed shared reduced state linking authoritative models, spatial planning and fast compute.

It contains:

- graph embeddings for structures, networks, functional groups and guilds;
- field embeddings for climate, soil, hydrology, nutrients and economics;
- optional sparse geometric embeddings;
- uncertainty, regime and out-of-distribution indicators;
- links back to the authoritative source state and model run.

GLES is not assumed to be a single neural vector. Implementations may use typed tensors, heterogeneous graphs, reduced bases, response surfaces, symbolic features, or learned encoders. The contract is semantic and auditable.

### 6.1 Training and generation

Trusted scientific models and observations generate trajectories over representative combinations of:

- climate and extreme-event regimes;
- soils, terrain and hydrology;
- land cover, functional groups and management;
- farm scale, machinery, labour and input prices;
- interventions and disturbances.

These trajectories train or fit reduced models. Every surrogate must record its training domain, error distribution, conservation behaviour and unsupported regimes.

### 6.2 Runtime use

Broad candidate generation and optimisation occur in the reduced state. Candidate plans that are high-value, uncertain, novel, regulation-sensitive, or close to physical thresholds are promoted to mechanistic analysis.

The reduced layer therefore amortises trusted simulation rather than replacing it.

---

## 7. Path A → Path B → Path C hierarchy

### Path A: screening and deterministic diagnosis

Purpose: cheap, explainable site analysis and candidate generation.

Methods may include:

- terrain derivatives, flow networks and wetness indices;
- erosion, accessibility and machinery constraint masks;
- rule-based planting, buffer, swale, dam and corridor candidates;
- simple mass balances and stock-flow models;
- conservative bounds and known regulatory exclusions.

Path A should reject impossible actions quickly and produce interpretable reasons.

### Path B: latent and surrogate exploration

Purpose: evaluate large design spaces efficiently.

Methods may include:

- graph neural operators or message passing;
- reduced-order hydrology, nutrient and vegetation models;
- learned response surfaces from APSIM, DNDC, AQUATOX, SWAT, forest models or local calibrated models;
- ensemble emulators and probabilistic risk models;
- GPU-resident multi-objective evaluation.

Path B must expose uncertainty and out-of-distribution status. It cannot silently promote an unsupported prediction.

### Path C: authoritative finite analysis

Purpose: validate consequential candidates with the highest justified fidelity.

Path C invokes full mechanistic engines, detailed finite analysis, calibration, expert review, or field validation. Examples include:

- dynamic soil–crop–nitrogen models;
- catchment and receiving-water models;
- detailed forest physiology and disturbance models;
- flood, sediment and infrastructure analysis;
- threatened-species or regulatory assessment.

A plan may move both directions: Path C results update the latent model and Path B anomalies identify where new Path C runs are needed.

---

## 8. Model selection and escalation

LES should select not only an intervention but also the least-cost adequate model depth.

A conceptual objective is:

\[
J(\theta,a)=L_{\mathrm{misfit}}+\lambda_c L_{\mathrm{complexity}}+\lambda_r L_{\mathrm{risk}}+\lambda_u L_{\mathrm{uncertainty}}+L_{\mathrm{resource}},
\]

where \(\theta\) denotes the selected model/chart and \(a\) the intervention plan.

This is an MDL-style principle: choose the shallowest effective degrees of freedom consistent with observations, conservation constraints and decision stakes.

Escalation triggers include:

- residuals exceeding calibrated tolerance;
- conservation or balance failure;
- proximity to flood, toxicity, erosion or extinction thresholds;
- unsupported climate, soil, species or management regime;
- large disagreement among surrogates;
- high economic, ecological or legal consequence.

---

## 9. Inverse analysis and source attribution

LES must support inverse questions as well as forward simulation.

Examples:

- Which upstream sources best explain a nutrient plume or algal bloom?
- Which management history is consistent with observed soil degradation?
- Which intervention failure caused downstream habitat loss?

The output is a ranked set of hypotheses, not an unsupported attribution of blame.

A defensible inverse workflow is:

1. preserve observations and their uncertainty;
2. define candidate source processes and transport pathways;
3. perform adjoint, Bayesian, ensemble, optimisation or constraint-based inference;
4. penalise unnecessary source complexity;
5. report identifiability, confounding and alternative explanations;
6. propose measurements that maximally reduce uncertainty.

Flow networks, timing, tracer behaviour and mass conservation should constrain the inference before learned correlations are considered.

---

## 10. Whole-farm and catchment intervention primitives

The planning layer should support composable primitives rather than hard-coded ideologies.

### Planting

Species or functional group, spatial pattern, density, phenology, establishment method, irrigation, expected products, habitat role, mycorrhizal association and management schedule.

### Grazing

Stock class, stocking density, movement schedule, rest period, forage demand, compaction risk, water access and fencing/labour requirements.

### Soil remediation

Cover crops, deep-rooted plants, fungal inoculation, compost, amendments, ripping, controlled traffic, erosion protection and time-to-effect.

### Water and earthworks

Dams, detention basins, wetlands, swales, keyline/ripping layouts, culverts, channels, floating planters, shading and nutrient interception systems.

### Infrastructure and operations

Roads, machinery paths, turning radii, slope and soil-bearing limits, pumps, energy systems, labour tasks, maintenance and failure modes.

### Economics

Capital cost, labour, machinery, fuel, water, energy, input prices, sale prices, futures/scenarios, opportunity cost and risk tolerance.

All primitives must remain scale-sensitive. A labour-intensive plan may dominate where labour is available and machinery is expensive; the reverse may hold elsewhere.

---

## 11. Example: eutrophic or weed-dominated lake

Given a lake and its catchment, LES should be able to:

1. ingest terrain, drainage, land use, soils, water-quality observations and management records;
2. identify likely nutrient and sediment pathways;
3. distinguish immediate symptom control from catchment remediation;
4. generate interventions such as upstream buffers, wetlands, fertiliser timing changes, floating planters, selective shading, harvesting or inflow redesign;
5. model ecological side effects, including native habitat and oxygen dynamics;
6. rank portfolios by water quality, cost, maintenance, amenity and uncertainty;
7. recommend additional sampling where source attribution is weak.

The rendered lake is useful for communication, but the recommendation must derive from budgets, transport, ecology and evidence.

---

## 12. Compute policy

LES is GPU-first where algorithms and validation permit, not GPU-exclusive.

- Keep dense fields, graph evaluation, spatial search, ensemble evaluation and surrogate inference device-resident where possible.
- Use task graphs, batching, sparse updates and precomputed conservative remapping weights.
- Avoid repeated host/device transfers.
- Retain CPU or external execution for legacy authoritative models, irregular control work, unsupported kernels, exact optimisation methods, and validation paths.
- Port measured hotspots rather than rewriting entire scientific engines prematurely.

The architecture must remain backend-neutral. CUDA, Vulkan, SYCL, JAX, PyTorch, CuPy, CPU SIMD and HPC model couplers are implementation options, not LES semantics.

---

## 13. Validation lanes

Every module or surrogate belongs to one of three lanes:

- **canonical**: preferred and validated for declared scenarios;
- **experimental**: useful but not promoted to authoritative planning;
- **validation**: references, counterexamples, invariants and regression harnesses.

Required evidence includes:

- declared domain and assumptions;
- units and conservation behaviour;
- calibration and validation datasets;
- error metrics by regime;
- deterministic or seeded reproducibility;
- concrete failing witnesses where possible;
- provenance linking recommendations to inputs and model versions.

---

## 14. Near-term implementation sequence

1. Define typed world-state and intervention schemas.
2. Implement GIS intake, CRS/units validation and provenance manifests.
3. Add Path A terrain, hydrology, machinery and constraint diagnostics.
4. Implement an ecological functional-group graph with uncertainty-bearing edges.
5. Wrap one vegetation model, one nutrient/soil model and one hydrology model behind explicit adapters.
6. Generate a small authoritative simulation ensemble and fit a transparent Path B surrogate.
7. Implement escalation and out-of-domain gates.
8. Demonstrate one whole-farm case and one catchment/lake inverse case.
9. Add optional visual clients only after the scientific contracts and validation scenarios are stable.

---

## 15. Canonical positioning

> LES is an open, GIS-native planning substrate that couples observations, environmental process models, ecological interaction graphs, reduced-order computation, spatial optimisation and human judgement within a shared, auditable world state. It supports coarse-to-fine analysis: rapid diagnosis and latent-space exploration for broad planning, followed by authoritative finite analysis where uncertainty or consequence demands it.
