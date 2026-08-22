# empirical-data-contracts

Small shared schemas for empirical data pipelines. This package intentionally has no pandas, GeoPandas, DuckDB, raster, or FCV dependencies.

The contracts define identity, provenance, grain, geography, time, coverage, measurement state, QA, and run manifests. Persisted dataset schemas remain source-specific; these contracts form the common envelope around them.

## Installation

Once a release is published on PyPI, downstream repositories can install the package directly:

```bash
python -m pip install empirical-data-contracts
```

For consumers that want the compatible `0.1.x` contract line without automatically crossing a minor-version boundary:

```bash
python -m pip install "empirical-data-contracts>=0.1,<0.2"
```

The import package is `empirical_contracts`.

## Compatibility and versioning

The package follows semantic versioning, and serialized JSON is part of the public contract. Field names, field types, defaults, and serialized enum values should therefore be treated as compatibility-sensitive.

- **Patch releases** may fix implementation defects, tests, or documentation without changing the accepted or serialized contract.
- **Minor releases** may add new models or backward-compatible optional fields with defaults. They should preserve round-tripping of payloads valid under the previous minor release.
- **Major releases** are required for incompatible serialization or validation changes, including renaming or removing fields, changing field meaning or type, changing serialized enum values, or newly rejecting payloads that were previously valid.

Persisted dataset schemas are versioned independently through `DatasetRef.schema_version`. A producing package records its own release in `RunManifest.package_version`; source releases and snapshot identifiers remain separate provenance dimensions.

When compatibility cannot be preserved, prefer an explicit migration path over silent reinterpretation. In particular, row absence must not be reinterpreted as zero unless a coverage contract explicitly declares `zero_within_verified_coverage`.

See [RELEASE.md](RELEASE.md) for the human-controlled release procedure and PyPI Trusted Publishing setup.
