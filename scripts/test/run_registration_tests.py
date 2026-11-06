"""Run registration tests without using the working directory's database."""

import os
from pathlib import Path
import sys
import tempfile

import pytest


def main():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    os.environ.pop("RAILWAY_ENVIRONMENT", None)
    os.environ.pop("SENDGRID_API_KEY", None)
    extra_args = [
        str(root / argument) if argument.endswith(".py") and (root / argument).is_file() else argument
        for argument in sys.argv[1:]
    ]
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="camppowerup-tests-") as temporary:
        os.chdir(temporary)
        try:
            return pytest.main([
                "-q",
                str(root / "scripts" / "test" / "test_thanksgiving_session.py"),
                str(root / "scripts" / "test" / "test_parent_contact.py"),
                str(root / "scripts" / "test" / "test_admin_workflows.py"),
                str(root / "scripts" / "test" / "test_discord_attendance.py"),
                str(root / "scripts" / "test" / "test_startup_secret_logging.py"),
                str(root / "scripts" / "test" / "test_healthz.py"),
                *extra_args,
            ])
        finally:
            os.chdir(previous)


if __name__ == "__main__":
    raise SystemExit(main())
