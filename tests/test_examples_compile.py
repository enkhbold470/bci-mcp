from pathlib import Path

EXAMPLES = (Path(__file__).resolve().parent.parent / "examples")


def test_all_examples_compile():
    py_files = list(EXAMPLES.glob("*.py"))
    assert py_files, "no example scripts found"
    for f in py_files:
        compile(f.read_text(), f.name, "exec")
