import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def test_release_version_is_consistent():
    source = (ROOT / "evcockpit.py").read_text(encoding="utf-8")
    match = re.search(r'^VERSION = "([0-9]+\.[0-9]+\.[0-9]+)"$', source, re.MULTILINE)
    assert match, "evcockpit.py muss eine eindeutige VERSION enthalten"

    update = json.loads((ROOT / "website/ev-cockpit/version.json").read_text(encoding="utf-8"))
    assert update["version"] == match.group(1)

    whats_new = (ROOT / "website/ev-cockpit/neu.html").read_text(encoding="utf-8")
    assert f"Version {match.group(1)}" in whats_new
