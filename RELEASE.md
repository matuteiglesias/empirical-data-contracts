# Release procedure

Releases are human-triggered and published to PyPI through GitHub Actions Trusted Publishing. The repository must not store a PyPI username, password, or API token.

## Versioning contract

`empirical-data-contracts` follows semantic versioning, with serialized Pydantic JSON treated as public compatibility surface:

- patch releases may repair implementation defects, tests, packaging, or documentation without changing accepted or serialized contracts;
- minor releases may add new models or backward-compatible optional fields with defaults while preserving payloads from the previous minor release;
- major releases are required for incompatible serialization or validation changes.

Persisted dataset schema versions remain separate from the package version through `DatasetRef.schema_version`.

## One-time PyPI and GitHub setup

Before the first publication, configure a PyPI Trusted Publisher for this repository. For an existing PyPI project, add it under the project's **Publishing** settings; for a first release, PyPI's pending Trusted Publisher flow may be used.

Use these exact Trusted Publisher values:

- owner: `matuteiglesias`
- repository: `empirical-data-contracts`
- workflow: `release.yml`
- environment: `pypi`

In GitHub, create a repository environment named `pypi`. Protection rules or required reviewers are recommended so publication remains an explicit human-controlled action.

## Release steps

1. Confirm the intended version is set in `pyproject.toml` and that the change obeys the compatibility rules above.
2. Merge the release-ready changes to `main` only after CI is green.
3. Confirm the PyPI Trusted Publisher and GitHub `pypi` environment are configured as described above.
4. Create a GitHub Release from the exact intended `main` commit using tag `vX.Y.Z`, where `X.Y.Z` exactly matches the version in `pyproject.toml`.
5. Publish the GitHub Release. This triggers `.github/workflows/release.yml`.
6. The release workflow builds the wheel and sdist, checks that the release tag matches the package version, installs the wheel in a fresh virtual environment, performs a minimal contract round-trip, uploads those exact build artifacts between jobs, and then publishes them to PyPI using OIDC.
7. After the workflow succeeds, verify the released version from a clean environment with `python -m pip install empirical-data-contracts==X.Y.Z`.

The workflow intentionally has no manual dispatch and does not publish on ordinary branch or pull-request events.

## Downstream installation

Install the latest published release:

```bash
python -m pip install empirical-data-contracts
```

Or constrain a downstream repository to the `0.1.x` contract line:

```bash
python -m pip install "empirical-data-contracts>=0.1,<0.2"
```

Python code imports the package as `empirical_contracts`.
