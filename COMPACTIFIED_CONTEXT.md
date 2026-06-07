# Compactified Context

## Purpose
Keep a minimal, durable record of key decisions for LES maintainers.

## Current Decisions

- Brainstorming content from repo PDFs is consolidated in `BRAINSTORMING_NOTES.md`, separate from core LES requirements.
- Lobster prediction market is in scope and documented in `BRAINSTORMING_NOTES.md`.
- LES docs now describe a near-term contract/validation foundation: schema-bearing state variables, explicit module contracts, `canonical`/`experimental`/`validation` lanes, and counterexample-style invariant checks.
- The docs intentionally stay modest about storage backends; the current implementation remains lightweight and dict-backed rather than promising a completed xarray migration.
- State reduction now explicitly includes trajectory comparison between detailed and reduced runners, plus a cheap divergence proxy vector for offline drift analysis or correction heuristics.

## Notes

- Local PDFs include a mix of LES-adjacent material and unrelated cross-project brainstorming.
- Documentation must clearly mark speculative or external systems as non-core.

---
Last updated: 2026-04-16
