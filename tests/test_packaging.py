import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_sdist_excludes_env_file():
    dist = ROOT / "dist"
    env_file = ROOT / ".env"
    had_env = env_file.exists()
    backup = env_file.read_text() if had_env else None
    env_file.write_text("UV_PUBLISH_TOKEN=pypi-should-not-ship\n")
    if dist.exists():
        shutil.rmtree(dist)
    try:
        subprocess.run(
            [sys.executable, "-m", "build", "--sdist"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        sdist = next(dist.glob("bci_mcp-*.tar.gz"))
        with tarfile.open(sdist, "r:gz") as tar:
            names = tar.getnames()
        leaked = [
            name
            for name in names
            if name.endswith(".env") or name.split("/")[-1] == ".env"
        ]
        assert not leaked, names
    finally:
        if had_env and backup is not None:
            env_file.write_text(backup)
        else:
            env_file.unlink(missing_ok=True)
        if dist.exists():
            shutil.rmtree(dist)
