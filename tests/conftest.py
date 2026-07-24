import os
import sys

# Ajouter les packages locaux au PYTHONPATH
packages_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "packages")
if os.path.exists(packages_dir):
    for pkg in os.listdir(packages_dir):
        pkg_src = os.path.join(packages_dir, pkg, "src")
        if os.path.exists(pkg_src):
            sys.path.insert(0, pkg_src)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
