# LES Roadmap

This roadmap focuses on the major unimplemented pillars called out in the repo: GIS/data services, HPC coupling, global optimization, continuous physical models, and visualization. It is intentionally phased to manage dependencies and keep a runnable end-to-end loop early.

## Phase 0: Foundations (0–1 month)

1. **Data model hardening**
   - Finalize core variable naming schema (CF-style) and minimal metadata for grids.
   - Decide on canonical time axis and coordinate conventions.
2. **State registry + config**
   - Central config for grid layout, time step, and module I/O signatures.
   - Formalize variable registration, ranges, and units.

## Phase 1: GIS + Data Services (1–2 months)

1. **Raster + vector adapters**
   - Raster: GeoTIFF + COG + NetCDF readers via `rioxarray/xarray`.
   - Vector: GeoPackage + FlatGeobuf via `geopandas`.
2. **NetCDF/Zarr ingestion**
   - NetCDF read/write + CF metadata validation.
   - Zarr store with chunking defaults for common grids.
3. **STAC catalog intake**
   - Parse STAC items into local caches.
   - Basic repro pipeline (hash + provenance).
4. **Integration goal**
   - Demonstrate ingest -> state registry -> module input -> output to Zarr.

## Phase 2: Continuous Physical Models (2–4 months)

1. **Hydrology (lite)**
   - Bucket/Richards-lite soil moisture.
   - Simple runoff + baseflow rule.
2. **ET + microclimate**
   - Penman–Monteith or simplified ET.
   - Canopy cover -> roughness -> ET feedback.
3. **Erosion (lite)**
   - Hillslope diffusion + stream power law.
4. **Integration goal**
   - Single catchment with time-varying climate forcing + hydrology + erosion.

## Phase 3: Optimizer + MIP (3–5 months)

1. **Multi-bed optimizer**
   - Extend DP to multiple beds (if feasible), otherwise move directly to MIP.
2. **MIP formulation**
   - Decision variables: crop per bed per season + resource usage.
   - Constraints: soil invariants, resource stocks, rotation cooldowns.
3. **Integration goal**
   - Run optimizer with outputs feeding into LES state registry.

## Phase 4: HPC Coupling (4–6 months)

1. **BMI/OpenMI adapters**
   - Wrap first hydrology + erosion modules in BMI interface.
2. **ESMF/ESMPy coupling**
   - Prototype conservative remapping between two grids.
3. **Distributed runner**
   - Minimal MPI or Dask-based runner for multi-module step.
4. **Integration goal**
   - Two modules running on separate grids with conservative exchange.

## Phase 5: Frontend + Visualization (3–6 months)

1. **Static outputs**
   - GeoTIFF + Zarr export with example maps.
2. **Interactive frontend**
   - Map viewer for time-series outputs (deck.gl or similar).
3. **Unity/Unreal bridge**
   - Export heightfields, vegetation layers, and water tables.
4. **Integration goal**
   - “Living world” demo: time slider + map layer toggles.

## Dependencies Summary

1. GIS/data services are foundational for almost everything.
2. Physical models depend on data ingestion and state registry.
3. Optimizer can run in parallel but needs consistent state definitions.
4. HPC coupling requires at least one module with BMI-like boundaries.
5. Visualization depends on stable output formats (Zarr/GeoTIFF).

## Immediate Next Actions

1. Decide on the canonical grid + coordinate system and CF metadata schema.
2. Stand up the GIS ingest pipeline and prove it with a small dataset.
3. Choose hydrology + erosion “lite” formulations for first integration.
