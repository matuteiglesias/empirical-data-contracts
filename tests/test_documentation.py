from pathlib import Path

import empirical_contracts as contracts


def test_every_public_api_object_has_a_docstring():
    undocumented = [
        name for name in contracts.__all__ if not getattr(contracts, name).__doc__
    ]
    assert undocumented == []


def test_package_has_a_docstring():
    assert contracts.__doc__


def test_readme_python_examples_execute():
    readme = Path(__file__).resolve().parents[1] / "README.md"
    blocks = readme.read_text(encoding="utf-8").split("```python\n")[1:]
    examples = [block.split("```", 1)[0] for block in blocks]

    assert examples
    # README examples are repository-controlled test inputs, not untrusted data.
    exec("\n".join(examples), {"__name__": "__readme_examples__"})  # noqa: S102
