from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    """Base class for immutable contracts that reject undeclared fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class AuthorityLevel(str, Enum):
    """Degree of authority associated with a dataset or coverage declaration.

    Values progress from inherited legacy material (``L0``) to output that has
    received explicit research validation (``L4``). The short values are the
    stable serialized representation.
    """

    L0_LEGACY_INHERITED = "L0"
    L1_NORMALIZED = "L1"
    L2_DERIVED = "L2"
    L3_REBUILT = "L3"
    L4_RESEARCH_VALIDATED = "L4"


class DataLayer(str, Enum):
    """A dataset's role in a conventional layered data architecture."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    LEGACY_COMPAT = "legacy_compat"


class MeasurementStatus(str, Enum):
    """How an individual measurement value came to be represented.

    In particular, source absence and a verified structural zero are distinct
    states. Consumers must not infer one from the other.
    """

    OBSERVED = "observed"
    AGGREGATED_FROM_OBSERVED = "aggregated_from_observed"
    INTERPOLATED = "interpolated"
    FORWARD_FILLED = "forward_filled"
    BACKWARD_FILLED = "backward_filled"
    NEAREST_EPOCH = "nearest_epoch"
    STRUCTURAL_ZERO = "structural_zero"
    SOURCE_ABSENT = "source_absent"
    OUTSIDE_COVERAGE = "outside_coverage"
    UNKNOWN = "unknown"


class SourceFileRef(StrictModel):
    """Integrity metadata for one file belonging to a source snapshot.

    ``sha256`` must be a lowercase, 64-character hexadecimal digest and
    ``size_bytes`` must be nonnegative.
    """

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class SourceSnapshotRef(StrictModel):
    """A reproducible reference to a particular release of an external source.

    A snapshot contains at least one file. ``origin`` can record where it came
    from without implying that the package has verified the source's coverage.
    """

    source: str
    release: str
    snapshot_id: str
    retrieved_at: datetime | None = None
    origin: str | None = None
    storage_mode: Literal["managed", "external_immutable"] = "external_immutable"
    files: tuple[SourceFileRef, ...]

    @field_validator("files")
    @classmethod
    def nonempty_files(cls, value: tuple[SourceFileRef, ...]):
        if not value:
            raise ValueError("a source snapshot must contain at least one file")
        return value


class GrainSpec(StrictModel):
    """Fields that uniquely identify observations at a dataset's declared grain.

    Keys are ordered, nonempty, and unique. Their names describe identity only;
    this contract does not prescribe a persisted table schema.
    """

    keys: tuple[str, ...]

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, value: tuple[str, ...]):
        if not value:
            raise ValueError("grain keys must be non-empty")
        if len(set(value)) != len(value):
            raise ValueError("grain keys must be unique")
        return value


class GeographySpec(StrictModel):
    """Identity of the provider, release, scheme, and level of a geography."""

    provider: str
    version: str
    scheme: str
    level: str
    scheme_version: str | None = None

    @property
    def id(self) -> str:
        """Return the stable colon-delimited geography identifier."""

        suffix = f":{self.scheme_version}" if self.scheme_version else ""
        return f"{self.provider}:{self.version}:{self.scheme}:{self.level}{suffix}"


class PeriodScheme(StrictModel):
    """A repeating year-based period scheme anchored to a calendar year."""

    width_years: int = Field(gt=0)
    anchor_year: int
    calendar: Literal["gregorian_year"] = "gregorian_year"

    @property
    def id(self) -> str:
        """Return the stable identifier for the period width and anchor year."""

        return f"T{self.width_years}_y{self.anchor_year}"


class CoverageContract(StrictModel):
    """Declared spatial, temporal, and absent-observation semantics.

    Coverage is descriptive rather than inferred. The default absent-row
    semantics are ``unknown``; zero is valid only when the producer explicitly
    declares ``zero_within_verified_coverage``.
    """

    geography_scope: str
    temporal_start: date | None = None
    temporal_end: date | None = None
    observation_semantics: str
    absent_row_semantics: Literal[
        "unknown", "zero_within_verified_coverage", "not_observed", "not_applicable"
    ] = "unknown"
    authority: AuthorityLevel
    basis: str

    @model_validator(mode="after")
    def dates_ordered(self):
        if self.temporal_start and self.temporal_end and self.temporal_end < self.temporal_start:
            raise ValueError("temporal_end must be >= temporal_start")
        return self


class DatasetRef(StrictModel):
    """Versioned identity and structural metadata for a produced dataset.

    ``version`` identifies the dataset release, while ``schema_version`` tracks
    its persisted schema independently. ``content_sha256`` is optional, but if
    supplied it must be a lowercase SHA-256 digest.
    """

    dataset_id: str
    version: str
    schema_version: str
    layer: DataLayer
    authority: AuthorityLevel
    grain: GrainSpec
    geography: GeographySpec | None = None
    period_scheme: PeriodScheme | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class MeasurementContract(StrictModel):
    """The common envelope describing a measurement derived from a dataset.

    ``parameters`` is the explicit extension field for producer-specific
    settings. It should not be used to promote a source-specific ontology into
    the package's shared top-level contract.
    """

    measure_id: str
    description: str
    source_dataset: DatasetRef
    output_grain: GrainSpec
    unit: str | None = None
    aggregation: str | None = None
    coverage: CoverageContract
    geography: GeographySpec | None = None
    period_scheme: PeriodScheme | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class QAResult(StrictModel):
    """Outcome and scalar metrics from one named quality-assurance check."""

    check_id: str
    state: Literal["GREEN", "YELLOW", "RED"]
    message: str
    metrics: dict[str, int | float | str | bool | None] = Field(default_factory=dict)


class RunManifest(StrictModel):
    """Provenance record connecting a software run to its inputs and outputs.

    ``package_version`` describes the producing software and is separate from
    source releases, dataset versions, and persisted schema versions.
    """

    run_id: str
    package: str
    package_version: str
    code_commit: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    inputs: tuple[SourceSnapshotRef | DatasetRef, ...] = ()
    parameters: dict[str, Any] = Field(default_factory=dict)
    outputs: tuple[DatasetRef, ...] = ()
    qa: tuple[QAResult, ...] = ()

    @model_validator(mode="after")
    def finish_after_start(self):
        if self.finished_at and self.finished_at < self.started_at:
            raise ValueError("finished_at must be >= started_at")
        return self
