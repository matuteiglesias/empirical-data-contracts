import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv


PUBLIC_IMPORTS = {
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
}


def test_built_wheel_exposes_public_api(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    project_root = tmp_path / "project"
    project_root.mkdir()

    for filename in ("pyproject.toml", "README.md", "RELEASE.md", "MANIFEST.in"):
        shutil.copy2(repo_root / filename, project_root / filename)
    shutil.copytree(repo_root / "src", project_root / "src")

    dist_dir = project_root / "dist"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--outdir",
            str(dist_dir),
        ],
        cwd=project_root,
        check=True,
    )

    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "wheel-venv"
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    venv_python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheels[0])],
        cwd=tmp_path,
        check=True,
    )

    verification = f"""
from pathlib import Path
import sysconfig
import empirical_contracts as contracts

expected = {PUBLIC_IMPORTS!r}
assert expected <= set(contracts.__all__)
for name in expected:
    assert getattr(contracts, name) is not None

package_path = Path(contracts.__file__).resolve()
purelib = Path(sysconfig.get_paths()[\"purelib\"]).resolve()
assert package_path.is_relative_to(purelib), (package_path, purelib)

contract = contracts.SourceFileRef(
    path=\"source.bin\",
    sha256=\"0\" * 64,
    size_bytes=1,
)
payload = contract.model_dump_json()
assert contracts.SourceFileRef.model_validate_json(payload) == contract
"""
    subprocess.run(
        [str(venv_python), "-c", verification],
        cwd=tmp_path,
        check=True,
    )
