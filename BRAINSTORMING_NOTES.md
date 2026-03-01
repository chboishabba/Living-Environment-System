# Brainstorming Notes (Non‑Core)

This file consolidates brainstorming content captured in repo PDFs and external notes. It is **not** normative LES design or implementation guidance. Each entry includes an LES relevance note and whether it is cross‑project.

## PDFs In This Repo

1. `LES - Living Environment System.pdf`
   - ChatGPT export with mixed content, including LES architecture snippets and data-pipeline ideas (e.g., LiDAR‑derived canopy structure feeding LES/GLES).
   - **LES relevance:** Medium. Useful as brainstorming/archive, not a spec.
   - **Cross‑project:** Contains unrelated material (e.g., lobster prediction market).

2. `LES - Environment modelling tools.pdf`
   - Catalog of ecosystem, erosion, hydrology, climate, and game‑engine tools plus a concrete LiDAR/tree‑structure pipeline and a mapping of outputs into LES fields.
   - **Tools/algos mentioned:** NetLogo, GAMA, EcoSim; CAESAR‑Lisflood, Landlab, LSDTopoTools; WRF, WEAP, SWAT+; Simile, Envision, Madingley; Unity/Unreal w/ erosion/weather/wildlife plugins; SimAdapt.
   - **Identified gaps:** integration across domains, temporal scale mismatch, spatial resolution mismatch, limited behavioral ecology, weak bidirectional feedback loops.
   - **LiDAR→LES pipeline:** derive per‑tree `height_max`, crown footprint, location (optionally species) → compute LAI/canopy density, surface roughness, fuel distribution, old‑growth patches → feed microclimate downscaling, fire modules, hydrology (interception/roughness), and forest PBMs (CASTANEA/iLand) as initial structure.
   - **LES relevance:** High. Useful for module selection and data‑ingestion planning.
   - **Cross‑project:** No, mostly LES‑adjacent.

3. `LES - Plant Guilds for Crop Rotations.pdf`
   - Lists plant guild sources and outlines how to convert them into a deterministic crop‑rotation state machine.
   - **LES relevance:** High. Directly informs rotation optimizer/state machine design.
   - **Cross‑project:** No.

4. `les - manuscript.pdf`
   - Academic paper on synthetic tree growth driven by ODEs and rendered in real time.
   - **LES relevance:** Medium. Useful for visualization and coupling biological models to 3D rendering.
   - **Cross‑project:** No.

5. `Branch · DASHI vs LES.pdf`
   - Conceptual discussion contrasting DASHI kernel ideas with LES; fidelity vs speed framing.
   - **LES relevance:** Low–Medium. Helps clarify fidelity tradeoffs, but not implementation‑ready.
   - **Cross‑project:** Yes (DASHI).

6. `Branch · Formalism Bridging GR and MDL - LES.pdf`
   - Theoretical mapping between GR/differential geometry and a DASHI/MDL formalism.
   - **LES relevance:** Low. Indirect, theoretical context only.
   - **Cross‑project:** Yes (DASHI/MDL).

7. `les - Glove seam optimisation papers.pdf`
   - Literature summary on glove seam/pattern optimization and pressure simulation.
   - **LES relevance:** None. Keep only for pattern‑optimization methodology.
   - **Cross‑project:** Yes (garment/mesh optimization).

8. `les - seameinit.pdf`
   - Notes on parametric body‑suit generators, garment modeling, and related tools.
   - **LES relevance:** None. Background exploration only.
   - **Cross‑project:** Yes (garment/CAD).

## Lobster Prediction Markets (Two Systems)

### CICADA/SOL Lobster Prediction Market (DeepWiki)

Summary provided by the user from DeepWiki (“discuss lobster prediction market” in `meta‑introspector/shards`):

- A Solana‑based prediction market for ship profitability, regional catch totals, lobster prices, and Chi resonance outcomes.
- Components: Anchor smart contracts, JS market dashboard, Python punter interface, Rust oracle resolver.
- Uses Prolog/MiniZinc models for topological classification and behavior odds; feeds into market predictions and consensus.

**LES relevance:** In scope as a reference architecture for market‑based signal aggregation and scenario wagering.  
**Cross‑project:** Yes (CICADA‑71 / Solana stack).

### LES Lobster Prediction Market (PDF)

This is the LES‑scoped lobster market described in the repo PDF export (distinct from the CICADA/SOL system above).

**LES relevance:** In scope as a potential LES module or scenario layer.  
**Cross‑project:** No (treated as LES‑native in this repo).
