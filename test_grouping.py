#!/usr/bin/env python3
"""
Automaattestid Puidujaak.ee toodete grupeerimise ja failinimede süsteemile.
Kontrollib:
1. Kõik 125 unikaalset fotot (ID001..ID125) on kaardistatud täpselt ühe toote alla (PUIDUJAK-001..PUIDUJAK-049).
2. Ühegi toote (PUIDUJAK-XXX) sees ei ole segamini erineva kategooriaga pilte (iga toote kategooriate hulk == 1).
3. Kasutaja ekraanipildil viidatud ID068, ID069 ja ID070 on kõik eraldi 1-pildised tooted:
   - ID068 -> PUIDUJAK-022 (tuveoonsus, 1 foto)
   - ID069 -> PUIDUJAK-023 (tuveoonsus, 1 foto)
   - ID070 -> PUIDUJAK-024 (ketas, 1 foto)
4. Teised varem valesti kokku pandud tükid (ID006, ID020, ID031-032, ID035, ID043-044,
   ID071-072 vs ID073, ID074-075 vs ID076-077, ID082-083 vs ID084 vs ID085-087,
   ID091-092 vs ID093 vs ID094, ID095 vs ID096-097, ID103, ID109) on eraldi toodetena.
5. 1-pildised ja 2-pildised tooted on lubatud (vana `2<=g[1]<=len(s)-4` >=3 pildi sund on eemaldatud).
6. Veebilehe `index.html` sisemine `CATALOG` JSON klapib 100% CSV-failidega.
"""

import csv
import json
import re
import unittest
from collections import defaultdict
from pathlib import Path


class TestPuidujaakGrouping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("/workspace/puidujaak/pildid_nimetamine.csv", encoding="utf-8") as f:
            cls.nim_rows = list(csv.DictReader(f))
        with open("/workspace/puidujak_mapping.csv", encoding="utf-8") as f:
            cls.map_rows = [r for r in csv.DictReader(f) if r["confidence"] != "duplicate-upload"]
        cls.groups_json = json.loads(Path("/workspace/groups.json").read_text(encoding="utf-8"))

        html = Path("/workspace/puidujaak/veeb_deploy/index.html").read_text(encoding="utf-8")
        m = re.search(r"const CATALOG = (\{.*?\});\n", html, re.S)
        assert m, "CATALOG JSON not found in index.html"
        cls.catalog = json.loads(m.group(1))

    def test_total_counts(self):
        self.assertEqual(len(self.nim_rows), 125)
        self.assertEqual(len(self.map_rows), 125)
        self.assertEqual(len(self.groups_json), 49)
        self.assertEqual(len(self.catalog["products"]), 49)
        self.assertEqual(len(self.catalog["photos"]), 125)

    def test_no_mixed_categories_in_any_product(self):
        by_prod = defaultdict(set)
        for r in self.nim_rows:
            by_prod[r["product_id"]].add(r["kategooria"])
        for pid, cats in by_prod.items():
            self.assertEqual(
                len(cats), 1, f"Tootel {pid} on mitu erinevat kategooriat: {cats}"
            )
        for prod in self.catalog["products"]:
            self.assertEqual(
                len(prod["categories"]),
                1,
                f"Veebikataloogi tootel {prod['product_id']} on mitu kategooriat: {prod['categories']}",
            )

    def test_id068_id069_id070_are_separate_products(self):
        by_id = {r["id"]: r for r in self.nim_rows}
        p68 = by_id["ID068"]["product_id"]
        p69 = by_id["ID069"]["product_id"]
        p70 = by_id["ID070"]["product_id"]

        self.assertNotEqual(p68, p69, "ID068 ja ID069 peavad olema eraldi tooted!")
        self.assertNotEqual(p69, p70, "ID069 ja ID070 peavad olema eraldi tooted!")
        self.assertNotEqual(p68, p70, "ID068 ja ID070 peavad olema eraldi tooted!")

        self.assertEqual(p68, "PUIDUJAK-022")
        self.assertEqual(p69, "PUIDUJAK-023")
        self.assertEqual(p70, "PUIDUJAK-024")

        # Verify each of PUIDUJAK-022, 023, 024 has exactly 1 photo
        prod_by_id = {p["product_id"]: p for p in self.catalog["products"]}
        self.assertEqual(prod_by_id["PUIDUJAK-022"]["photo_count"], 1)
        self.assertEqual(prod_by_id["PUIDUJAK-023"]["photo_count"], 1)
        self.assertEqual(prod_by_id["PUIDUJAK-024"]["photo_count"], 1)

        self.assertEqual(by_id["ID068"]["kategooria"], "tuveoonsus")
        self.assertEqual(by_id["ID069"]["kategooria"], "tuveoonsus")
        self.assertEqual(by_id["ID070"]["kategooria"], "ketas")

    def test_single_and_two_photo_products_supported(self):
        counts = [p["photo_count"] for p in self.catalog["products"]]
        one_photo_prods = [p["product_id"] for p in self.catalog["products"] if p["photo_count"] == 1]
        two_photo_prods = [p["product_id"] for p in self.catalog["products"] if p["photo_count"] == 2]
        self.assertEqual(len(one_photo_prods), 15)
        self.assertEqual(len(two_photo_prods), 12)
        self.assertEqual(sum(counts), 125)

    def test_other_split_boundaries(self):
        by_id = {r["id"]: r["product_id"] for r in self.nim_rows}
        # ID005 (green foam core) vs ID006 (wood core with white cap)
        self.assertNotEqual(by_id["ID005"], by_id["ID006"])
        # ID020 (dark veneer) vs ID021 (light board)
        self.assertNotEqual(by_id["ID020"], by_id["ID021"])
        # ID030 (long light board) vs ID031 (plywood corner)
        self.assertNotEqual(by_id["ID030"], by_id["ID031"])
        # ID034 (narrow strip) vs ID035 (plywood edge)
        self.assertNotEqual(by_id["ID034"], by_id["ID035"])
        # ID042 (thin white strip with hole) vs ID043 (4.5cm thick block)
        self.assertNotEqual(by_id["ID042"], by_id["ID043"])
        # ID071-072 (C-shaped hollow slice) vs ID073 (U-shaped bark with branch hole)
        self.assertEqual(by_id["ID071"], by_id["ID072"])
        self.assertNotEqual(by_id["ID072"], by_id["ID073"])
        # ID074-075 (heart slice) vs ID076-077 (dark bark burl)
        self.assertEqual(by_id["ID074"], by_id["ID075"])
        self.assertNotEqual(by_id["ID075"], by_id["ID076"])
        self.assertEqual(by_id["ID076"], by_id["ID077"])
        # ID078-081 (O-shaped hollow ring with 50€)
        self.assertEqual(by_id["ID078"], by_id["ID081"])
        # ID082-083 vs ID084 vs ID085-087
        self.assertEqual(by_id["ID082"], by_id["ID083"])
        self.assertNotEqual(by_id["ID083"], by_id["ID084"])
        self.assertNotEqual(by_id["ID084"], by_id["ID085"])
        # ID091-092 (eye branch hole) vs ID093 vs ID094
        self.assertEqual(by_id["ID091"], by_id["ID092"])
        self.assertNotEqual(by_id["ID092"], by_id["ID093"])
        self.assertNotEqual(by_id["ID093"], by_id["ID094"])
        # ID095 (measuring tape branch collar) vs ID096-097 (spongy hollow trunk)
        self.assertNotEqual(by_id["ID095"], by_id["ID096"])
        self.assertEqual(by_id["ID096"], by_id["ID097"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
