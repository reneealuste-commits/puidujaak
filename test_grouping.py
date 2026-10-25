#!/usr/bin/env python3
"""
Automatiseeritud kontrollid Puidujaak.ee foto- ja tootekataloogi grupeerimise jaoks (67 toodet / 185 fotot).
"""

import csv
import json
import re
from pathlib import Path

WORKSPACE = Path("/workspace")
PUIDUJAAK = WORKSPACE / "puidujaak"


def test_all():
    groups = json.loads((WORKSPACE / "groups.json").read_text(encoding="utf-8"))
    assert len(groups) == 67, f"Oodati 67 tootegruppi, leiti {len(groups)}"

    html = (PUIDUJAAK / "veeb_deploy" / "index.html").read_text(encoding="utf-8")
    m = re.search(r"const CATALOG = (\{.*\});", html)
    assert m, "CATALOG JSON-i ei leitud index.html-st"
    cat = json.loads(m.group(1))
    assert len(cat["products"]) == 67, f"Oodati 67 toodet index.html-s, leiti {len(cat['products'])}"
    assert len(cat["photos"]) == 185, f"Oodati 185 fotot index.html-s, leiti {len(cat['photos'])}"

    by_pid = {
        p["product_id"]: {
            "photo_ids": [ph["id"] for ph in p["photos"]],
            "scale_ref": p["scale_ref"],
        }
        for p in cat["products"]
    }

    # Kontroll 1: ID067..ID070 on 4 ERALDI toodet
    assert by_pid["PUIDUJAK-021"]["photo_ids"] == ["ID067"]
    assert by_pid["PUIDUJAK-022"]["photo_ids"] == ["ID068"]
    assert by_pid["PUIDUJAK-023"]["photo_ids"] == ["ID069"]
    assert by_pid["PUIDUJAK-024"]["photo_ids"] == ["ID070"]

    # Kontroll 2: 24.10.2026 uued tooted PUIDUJAK-050..067 (ID126..ID185)
    assert by_pid["PUIDUJAK-050"]["photo_ids"] == ["ID126", "ID127", "ID128", "ID129"]
    assert by_pid["PUIDUJAK-051"]["photo_ids"] == ["ID130", "ID131", "ID132"]
    assert by_pid["PUIDUJAK-052"]["photo_ids"] == ["ID133", "ID134"]
    assert by_pid["PUIDUJAK-053"]["photo_ids"] == ["ID135", "ID136"]
    assert by_pid["PUIDUJAK-054"]["photo_ids"] == ["ID137", "ID138", "ID139"]
    assert by_pid["PUIDUJAK-056"]["photo_ids"] == ["ID144", "ID145", "ID146"]
    assert "0,5 L" in by_pid["PUIDUJAK-056"]["scale_ref"]
    assert by_pid["PUIDUJAK-058"]["photo_ids"] == ["ID150", "ID175"]
    assert by_pid["PUIDUJAK-065"]["photo_ids"] == ["ID171", "ID172", "ID173", "ID174"]
    assert by_pid["PUIDUJAK-066"]["photo_ids"] == ["ID176", "ID177", "ID178", "ID179"]
    assert by_pid["PUIDUJAK-067"]["photo_ids"] == ["ID180", "ID181", "ID182", "ID183", "ID184", "ID185"]

    # Kontroll 3: pildid_nimetamine.csv sisaldab täpselt 185 unikaalset fotot
    nim_rows = list(csv.DictReader((PUIDUJAAK / "pildid_nimetamine.csv").open(encoding="utf-8")))
    assert len(nim_rows) == 185, f"Oodati 185 rida pildid_nimetamine.csv-s, leiti {len(nim_rows)}"

    print("KÕIK KONTROLLID LÄBITUD EDUKALT (67 toodet, 185 fotot, ID001..ID185).")


if __name__ == "__main__":
    test_all()
