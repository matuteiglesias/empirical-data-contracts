# empirical-data-contracts

Small, typed contracts for reproducible empirical data systems. The package
defines a common envelope for identity, provenance, grain, geography, time,
coverage, measurement state, quality assurance, and run manifests. Persisted
dataset schemas remain the responsibility of producing packages.

The package intentionally has no pandas, GeoPandas, DuckDB, raster, or
source-specific dependencies. It describes data; it does not load, transform,
or interpret it.

## Installation

Install the latest release from PyPI:

```bash
python -m pip install empirical-data-contracts
```

To remain on the compatible `0.1.x` contract line:

```bash
python -m pip install "empirical-data-contracts>=0.1,<0.2"
```

The distribution is named `empirical-data-contracts`; Python code imports
`empirical_contracts`. Python 3.10 or newer is required.

## Quick start

Contracts are immutable Pydantic models. Construct them from ordinary Python
values, serialize them to JSON, and validate them again at a system boundary:

```python
from datetime import date

from empirical_contracts import (
    AuthorityLevel,
    CoverageContract,
    DataLayer,
    DatasetRef,
    GeographySpec,
    GrainSpec,
)

grain = GrainSpec(keys=("region_id", "year"))
geography = GeographySpec(
    provider="example-provider",
    version="2026.1",
    scheme="administrative",
    level="region",
)
coverage = CoverageContract(
    geography_scope="coverage declared by the producing system",
    temporal_start=date(2020, 1, 1),
    temporal_end=date(2025, 12, 31),
    observation_semantics="records reported by the source",
    absent_row_semantics="unknown",
    authority=AuthorityLevel.L1_NORMALIZED,
    basis="producer documentation",
)
dataset = DatasetRef(
    dataset_id="example.observations",
    version="2026-08",
    schema_version="1.0.0",
    layer=DataLayer.SILVER,
    authority=AuthorityLevel.L1_NORMALIZED,
    grain=grain,
    geography=geography,
)

payload = dataset.model_dump_json()
restored = DatasetRef.model_validate_json(payload)
assert restored == dataset
```

The example describes only a contract. Its fictional names and coverage text
do not assert coverage for a real data source.

## How the contracts fit together

### Provenance and identity

`SourceFileRef` records a file's path, byte size, and SHA-256 digest.
`SourceSnapshotRef` groups one or more such files into a reproducible source
release. A snapshot can point to managed storage or an externally maintained,
immutable location.

`DatasetRef` identifies a produced dataset and records its data layer,
authority, grain, and optional geographic, temporal, and content-hash metadata.
Its versions have deliberately separate meanings:

- `version` identifies the dataset release;
- `schema_version` identifies the persisted dataset schema;
- `RunManifest.package_version` identifies the software that produced output;
- `SourceSnapshotRef.release` and `snapshot_id` identify source provenance.

Keeping these dimensions separate prevents a software release from silently
standing in for a data or schema release.

### Grain

`GrainSpec(keys=(...))` declares the ordered fields that uniquely identify an
observation. Keys must be nonempty and unique. A grain describes identity, not
a complete table schema, and it does not imply that missing combinations exist
or have a value of zero.

### Geography and time

`GeographySpec` identifies a provider, provider version, geographic scheme, and
level. Its `id` property produces a stable, colon-delimited identifier:

```python
from empirical_contracts import GeographySpec, PeriodScheme

geography = GeographySpec(
    provider="example", version="1", scheme="admin", level="2"
)
assert geography.id == "example:1:admin:2"

period = PeriodScheme(width_years=5, anchor_year=2000)
assert period.id == "T5_y2000"
```

`PeriodScheme` defines positive-width, year-based periods anchored to a year.
The only currently supported calendar is `gregorian_year`.

### Coverage and missing observations

`CoverageContract` makes spatial scope, temporal bounds, observation meaning,
authority, and evidence explicit. Temporal bounds are optional, but when both
are present the end cannot precede the start.

Absent rows default to `unknown`. Producers may instead explicitly declare:

- `zero_within_verified_coverage` — absence is zero only inside independently
  verified coverage;
- `not_observed` — the source did not observe the combination;
- `not_applicable` — the combination is outside the measurement's meaning.

**Never interpret row absence as zero without the explicit verified-coverage
declaration.** A coverage contract records a producer's supported declaration;
it must not be used to invent source coverage.

### Measurements

`MeasurementContract` connects a measure to its source dataset, output grain,
coverage, and optional unit, aggregation, geography, and period scheme.
Producer-specific settings belong in `parameters` rather than in new
source-specific top-level concepts:

```python
from empirical_contracts import MeasurementContract

measurement = MeasurementContract(
    measure_id="example.total",
    description="Illustrative total from the example dataset",
    source_dataset=dataset,
    output_grain=grain,
    unit="count",
    aggregation="sum",
    coverage=coverage,
    geography=geography,
    parameters={"producer_method": "documented-example-method"},
)
```

The package intentionally does not define treatment/control status, matching,
regression, lagged outcomes, job categories, or source-specific scientific
ontologies.

### Quality assurance and runs

`QAResult` records a named check as `GREEN`, `YELLOW`, or `RED`, together with a
human-readable message and scalar metrics. `RunManifest` joins source snapshots
and datasets to the parameters, outputs, QA results, timestamps, package
version, and optional code commit for a single run.

```python
from datetime import datetime, timezone

from empirical_contracts import QAResult, RunManifest

qa = QAResult(
    check_id="rows-present",
    state="GREEN",
    message="The output contains records",
    metrics={"rows": 120},
)
run = RunManifest(
    run_id="run-2026-08-23",
    package="example-producer",
    package_version="2.3.0",
    started_at=datetime(2026, 8, 23, 12, tzinfo=timezone.utc),
    outputs=(dataset,),
    qa=(qa,),
)
```

## Public API

All supported imports are available directly from `empirical_contracts`.

| Type | Purpose |
| --- | --- |
| `AuthorityLevel` | Authority from legacy-inherited (`L0`) through research-validated (`L4`) |
| `DataLayer` | Bronze, silver, gold, or legacy-compatibility dataset layer |
| `MeasurementStatus` | Provenance/state of an individual measurement value |
| `SourceFileRef` | File integrity metadata |
| `SourceSnapshotRef` | Reproducible external-source release and its files |
| `GrainSpec` | Ordered unique keys defining observation identity |
| `GeographySpec` | Versioned geographic scheme identity |
| `PeriodScheme` | Anchored, fixed-width year periods |
| `CoverageContract` | Explicit coverage and absent-row semantics |
| `DatasetRef` | Versioned produced-dataset identity and structure |
| `MeasurementContract` | Common measurement envelope |
| `QAResult` | One quality-check outcome and scalar metrics |
| `RunManifest` | Provenance connecting a software run, inputs, and outputs |

Use `help(empirical_contracts.DatasetRef)` or an IDE's symbol documentation for
field signatures, defaults, and API docstrings. Pydantic also exposes
`Model.model_json_schema()` when a machine-readable JSON Schema is needed.

## Validation behavior

Every model is frozen and rejects undeclared fields. This makes accidental
mutation and misspelled fields fail early. Additional guarantees include:

- file and content SHA-256 values are 64 lowercase hexadecimal characters;
- file sizes are nonnegative;
- source snapshots contain at least one file;
- grain keys are nonempty and unique;
- period widths are positive;
- coverage end dates do not precede start dates;
- run finish timestamps do not precede start timestamps.

Invalid input raises `pydantic.ValidationError`:

```python
from pydantic import ValidationError

try:
    GrainSpec(keys=("region_id", "region_id"))
except ValidationError as error:
    print(error)
```

## Compatibility and versioning

The package follows semantic versioning, and serialized JSON is part of the
public contract. Field names, field types, defaults, and serialized enum values
are compatibility-sensitive.

- **Patch releases** may fix implementation defects, tests, or documentation
  without changing the accepted or serialized contract.
- **Minor releases** may add models or backward-compatible optional fields with
  defaults. Payloads valid under the previous minor release should continue to
  round-trip.
- **Major releases** are required for incompatible serialization or validation
  changes, including renamed or removed fields, changed meanings or types,
  changed enum values, or newly rejected payloads.

When compatibility cannot be preserved, prefer an explicit migration path over
silent reinterpretation. Persist JSON with `model_dump_json()` and restore it
with the same model's `model_validate_json()`; do not depend on Python's
`repr()` as a storage format.

See [RELEASE.md](RELEASE.md) for the human-controlled release procedure and
PyPI Trusted Publishing setup.

## Development

Install the package with its development dependencies and run the checks:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m build
```
