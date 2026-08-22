from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from empirical_contracts import (
    AuthorityLevel,
    CoverageContract,
    DataLayer,
    DatasetRef,
    GeographySpec,
    GrainSpec,
    PeriodScheme,
    RunManifest,
    SourceFileRef,
    SourceSnapshotRef,
)


def test_geography_and_period_ids_are_stable():
    geo = GeographySpec(provider="gadm", version="4.1", scheme="admin", level="2")
    period = PeriodScheme(width_years=2, anchor_year=2001)
    assert geo.id == "gadm:4.1:admin:2"
    assert period.id == "T2_y2001"


def test_grain_rejects_duplicate_keys():
    with pytest.raises(ValidationError):
        GrainSpec(keys=("GID", "GID"))


def test_snapshot_requires_valid_sha256():
    with pytest.raises(ValidationError):
        SourceFileRef(path="x.csv", sha256="bad", size_bytes=1)


def test_dataset_roundtrip_json():
    ds = DatasetRef(
        dataset_id="geography.gadm.units",
        version="4.1",
        schema_version="0.1.0",
        layer=DataLayer.SILVER,
        authority=AuthorityLevel.L3_REBUILT,
        grain=GrainSpec(keys=("geo_uid",)),
        geography=GeographySpec(provider="gadm", version="4.1", scheme="native", level="all"),
    )
    assert DatasetRef.model_validate_json(ds.model_dump_json()) == ds


def test_run_manifest_rejects_reversed_time():
    f = SourceFileRef(path="gadm.gpkg", sha256="0" * 64, size_bytes=10)
    src = SourceSnapshotRef(source="gadm", release="4.1", snapshot_id="gadm-4.1-0000", files=(f,))
    with pytest.raises(ValidationError):
        RunManifest(
            run_id="r1",
            package="spatial-foundation",
            package_version="0.1.0",
            started_at=datetime(2026, 8, 22, 20, tzinfo=timezone.utc),
            finished_at=datetime(2026, 8, 22, 19, tzinfo=timezone.utc),
            inputs=(src,),
        )


def test_coverage_dates_are_ordered():
    with pytest.raises(ValidationError):
        CoverageContract(
            geography_scope="Africa",
            temporal_start=date(2020, 1, 1),
            temporal_end=date(2010, 1, 1),
            observation_semantics="event records",
            authority=AuthorityLevel.L3_REBUILT,
            basis="raw source",
        )
