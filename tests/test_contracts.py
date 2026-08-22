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
    MeasurementContract,
    PeriodScheme,
    QAResult,
    RunManifest,
    SourceFileRef,
    SourceSnapshotRef,
)


def _examples():
    source_file = SourceFileRef(path="source.csv", sha256="0" * 64, size_bytes=42)
    snapshot = SourceSnapshotRef(
        source="example-source",
        release="2026-08",
        snapshot_id="example-source-2026-08",
        retrieved_at=datetime(2026, 8, 22, 20, tzinfo=timezone.utc),
        origin="https://example.invalid/source.csv",
        files=(source_file,),
    )
    grain = GrainSpec(keys=("geo_uid", "period"))
    geography = GeographySpec(
        provider="example-provider",
        version="1.0",
        scheme="admin",
        level="2",
        scheme_version="2026",
    )
    period = PeriodScheme(width_years=2, anchor_year=2001)
    coverage = CoverageContract(
        geography_scope="declared source coverage",
        temporal_start=date(2001, 1, 1),
        temporal_end=date(2025, 12, 31),
        observation_semantics="recorded observations",
        absent_row_semantics="unknown",
        authority=AuthorityLevel.L3_REBUILT,
        basis="source documentation",
    )
    dataset = DatasetRef(
        dataset_id="example.dataset",
        version="2026-08",
        schema_version="0.1.0",
        layer=DataLayer.SILVER,
        authority=AuthorityLevel.L3_REBUILT,
        grain=grain,
        geography=geography,
        period_scheme=period,
        content_sha256="1" * 64,
    )
    measurement = MeasurementContract(
        measure_id="example.measure",
        description="Example measurement contract",
        source_dataset=dataset,
        output_grain=grain,
        unit="count",
        aggregation="sum",
        coverage=coverage,
        geography=geography,
        period_scheme=period,
        parameters={"minimum_records": 1, "enabled": True},
    )
    qa = QAResult(
        check_id="example-check",
        state="GREEN",
        message="example check passed",
        metrics={"rows": 10, "ratio": 0.5, "complete": True},
    )
    run = RunManifest(
        run_id="run-001",
        package="example-package",
        package_version="0.1.0",
        code_commit="abc123",
        started_at=datetime(2026, 8, 22, 20, tzinfo=timezone.utc),
        finished_at=datetime(2026, 8, 22, 21, tzinfo=timezone.utc),
        inputs=(snapshot, dataset),
        parameters={"dry_run": False},
        outputs=(dataset,),
        qa=(qa,),
    )
    return (
        source_file,
        snapshot,
        grain,
        geography,
        period,
        coverage,
        dataset,
        measurement,
        qa,
        run,
    )


def test_geography_and_period_ids_are_stable():
    geo = GeographySpec(provider="gadm", version="4.1", scheme="admin", level="2")
    period = PeriodScheme(width_years=2, anchor_year=2001)
    assert geo.id == "gadm:4.1:admin:2"
    assert period.id == "T2_y2001"


@pytest.mark.parametrize("contract", _examples(), ids=lambda value: type(value).__name__)
def test_contract_json_roundtrip_is_stable(contract):
    payload = contract.model_dump_json()
    restored = type(contract).model_validate_json(payload)
    assert restored == contract
    assert restored.model_dump_json() == payload


@pytest.mark.parametrize("keys", [(), ("GID", "GID")])
def test_grain_rejects_empty_or_duplicate_keys(keys):
    with pytest.raises(ValidationError):
        GrainSpec(keys=keys)


def test_snapshot_requires_at_least_one_file():
    with pytest.raises(ValidationError):
        SourceSnapshotRef(source="source", release="1", snapshot_id="source-1", files=())


@pytest.mark.parametrize(
    ("sha256", "size_bytes"),
    [("bad", 1), ("A" * 64, 1), ("0" * 64, -1)],
)
def test_source_file_rejects_invalid_hash_or_size(sha256, size_bytes):
    with pytest.raises(ValidationError):
        SourceFileRef(path="x.csv", sha256=sha256, size_bytes=size_bytes)


def test_period_scheme_requires_positive_width():
    with pytest.raises(ValidationError):
        PeriodScheme(width_years=0, anchor_year=2000)


def test_dataset_rejects_invalid_content_hash():
    with pytest.raises(ValidationError):
        DatasetRef(
            dataset_id="dataset",
            version="1",
            schema_version="0.1.0",
            layer=DataLayer.SILVER,
            authority=AuthorityLevel.L3_REBUILT,
            grain=GrainSpec(keys=("id",)),
            content_sha256="bad",
        )


def test_run_manifest_rejects_reversed_time():
    source_file = SourceFileRef(path="gadm.gpkg", sha256="0" * 64, size_bytes=10)
    source = SourceSnapshotRef(
        source="gadm",
        release="4.1",
        snapshot_id="gadm-4.1-0000",
        files=(source_file,),
    )
    with pytest.raises(ValidationError):
        RunManifest(
            run_id="r1",
            package="spatial-foundation",
            package_version="0.1.0",
            started_at=datetime(2026, 8, 22, 20, tzinfo=timezone.utc),
            finished_at=datetime(2026, 8, 22, 19, tzinfo=timezone.utc),
            inputs=(source,),
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


def test_contracts_forbid_undeclared_fields():
    with pytest.raises(ValidationError):
        GrainSpec(keys=("id",), treatment="treated")
