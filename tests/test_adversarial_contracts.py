import pytest
from pydantic import ValidationError

from empirical_contracts import SourceFileRef


@pytest.mark.parametrize(
    "sha256",
    [
        "0" * 63,
        "0" * 65,
        "g" * 64,
        "0" * 63 + " ",
        "0x" + "0" * 64,
    ],
)
def test_source_file_rejects_malformed_sha256_edge_cases(sha256):
    with pytest.raises(ValidationError):
        SourceFileRef(path="source.bin", sha256=sha256, size_bytes=1)
