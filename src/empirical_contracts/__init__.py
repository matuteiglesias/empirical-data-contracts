"""Stable, typed contracts for reproducible empirical data systems.

The public models are immutable, reject undeclared fields, and serialize through
Pydantic. Serialized field names and enum values are part of the compatibility
surface of this package.
"""

from .models import (
    AuthorityLevel,
    CoverageContract,
    DataLayer,
    DatasetRef,
    GeographySpec,
    GrainSpec,
    MeasurementContract,
    MeasurementStatus,
    PeriodScheme,
    QAResult,
    RunManifest,
    SourceFileRef,
    SourceSnapshotRef,
)

__all__ = [
    "AuthorityLevel",
    "CoverageContract",
    "DataLayer",
    "DatasetRef",
    "GeographySpec",
    "GrainSpec",
    "MeasurementContract",
    "MeasurementStatus",
    "PeriodScheme",
    "QAResult",
    "RunManifest",
    "SourceFileRef",
    "SourceSnapshotRef",
]
