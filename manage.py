#!/usr/bin/env python
"""AutoPilot — Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    # Ajouter les packages locaux au PYTHONPATH pour le développement
    packages_dir = Path(__file__).resolve().parent / "packages"
    if packages_dir.exists():
        for pkg in packages_dir.iterdir():
            pkg_src = pkg / "src"
            if pkg_src.exists():
                sys.path.insert(0, str(pkg_src.resolve()))

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev"),
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
