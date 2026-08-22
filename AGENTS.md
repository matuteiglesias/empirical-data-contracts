# Agent Instructions — empirical-data-contracts

This package is a semantic boundary. Keep it small.

## Must
- preserve backwards-compatible serialization whenever possible;
- make invalid states difficult to represent;
- use enums / typed models for cross-system concepts;
- keep source-specific details in explicit extension fields rather than adding FCV-specific top-level concepts;
- add tests for every new validation rule.

## Must not
- import pandas, geopandas, shapely, duckdb, rasterio, or FCV packages;
- define treatment/control, matching, regression, lagged outcomes, jobs categories, or source-specific scientific ontologies;
- interpret row absence as zero;
- invent source coverage.

If a requested feature requires domain knowledge, stop at the contract boundary and ask for a source-specific spec.
