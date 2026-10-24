"""Guards .github/dependabot.yml: Dependabot gives a dependency to the FIRST group that matches,
so the runtime group has to sit before the catch-all or it silently never applies."""

import re
from fnmatch import fnmatch
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PACKAGES = ("pipecat-ai", "sqlalchemy", "google-genai")


def _updates() -> dict:
    config = yaml.safe_load((REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
    return {entry["package-ecosystem"]: entry for entry in config["updates"]}


def test_runtime_group_comes_before_pip_catch_all_and_matches_each_package() -> None:
    groups = _updates()["pip"]["groups"]
    names = list(groups)
    assert names.index("runtime") < names.index("pip")
    for package in RUNTIME_PACKAGES:
        assert any(fnmatch(package, pattern) for pattern in groups["runtime"]["patterns"]), package


def test_runtime_packages_are_still_pinned_in_requirements() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for package in RUNTIME_PACKAGES:
        assert re.search(rf"^{re.escape(package)}(\[|==|$)", requirements, re.MULTILINE), package


def test_docker_ecosystem_is_tracked() -> None:
    assert "docker" in _updates()
