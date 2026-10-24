#!/usr/bin/env python3
"""
Puidujaak.ee fotode sorteerimise, toodeteks grupeerimise ja lühikese ümbernimetamise süsteem.

Nõuded:
1. Iga foto saab lühikese ja selge nime, mis algab KATEGOORIAGA (et kaustas nime järgi
   sorteerides koondaks kõik sama tüüpi pildid kokku) ning sisaldab JÄRJEKORRANUMBRIT (ID001..ID125).
2. Iga foto kuulub täpselt ühe füüsilise toote (`PUIDUJAK-001`..`PUIDUJAK-049`) alla.
   Ühe toote sees on kõigil fotodel alati SAMA kategooria (ei mingeid segakategooriaid!).
   Üksikud pildid eraldi puidutükkidest (nt ID006, ID020, ID035, ID067, ID068, ID069, ID070,
   ID073, ID084, ID093, ID094, ID095, ID103, ID109, ID125) on eraldi 1-pildised tooted.
3. Lihtsad visuaalsed kategooriad:
   - oksaauk     (oksaauguga koor/puit)
   - oksakrae    (oksakrae, okslik tüvejupp)
   - tuveoonsus  (tüveõõnsus, seest pehkinud/käsnjas või õõnes tüveosa)
   - ketas       (tüveketas / ristlõige)
   - koor        (paks korbatanud koor või pahk)
   - erikuju     (erikujuline töökojajääk / CNC / laserlõige)
   - klots       (liimpuidu- või okaspuuklots / ruutprofiil)
   - plaat       (plaatmaterjal, sandwich-plaat, vineer)
   - laud        (laud, liist, spoon)
   - palk        (palk või känd)
   - alus        (puitalus)
4. Umbkaudsed mõõdud (`moot_cm`) sisestab kasutaja ise — skript EI paku ega arva
   pildilt mõõte (vaikimisi tühi ""). Kui kasutaja sisestab mõõdu (cm), arvutab kood
   automaatselt mõõdukategooria:
   - alla30cm  (< 30 cm)
   - alla50cm  (30–49.9 cm)
   - alla1m    (50–99.9 cm)
   - yle1m     (>= 100 cm)
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, "/workspace")
from group import PRODUCT_GROUPS_SPEC

# Lubatud lihtsad kategooriad
CATEGORIES = {
    "oksaauk": "Oksaauk (branch hole)",
    "oksakrae": "Oksakrae (branch collar / branch stub)",
    "tuveoonsus": "Tüveõõnsus (trunk cavity / spongy hollow)",
    "ketas": "Tüveketas (trunk slice / cross-section)",
    "koor": "Koor või pahk (thick bark / burl)",
    "erikuju": "Erikujuline jääk (odd-shaped offcut)",
    "klots": "Klots või profiil (wooden block / square profile)",
    "plaat": "Plaat või vineer (panel / plywood)",
    "laud": "Laud või liist (board / strip)",
    "palk": "Palk või känd (log / stump)",
    "alus": "Puitalus (wooden pallet)",
}


def get_dimension_category(max_cm: Optional[float]) -> str:
    """
    Arvutab mõõdukategooria kasutaja sisestatud mõõdu (cm) põhjal.
    Ei arva kunagi mõõtu ise: kui max_cm on None/tühi, tagastab tühja sõne "".
    """
    if max_cm is None:
        return ""
    if max_cm < 30:
        return "alla30cm"
    if max_cm < 50:
        return "alla50cm"
    if max_cm < 100:
        return "alla1m"
    return "yle1m"


def parse_caller_dimension_cm(raw_value: str) -> Optional[float]:
    """
    Loeb kasutaja sisestatud mõõdu (nt "25", "45cm", "30x20", "1.2m" -> cm).
    Kui väli on tühi, tagastab None (ei arva mõõtu!).
    """
    if not raw_value or not raw_value.strip():
        return None
    text = raw_value.strip().lower().replace(",", ".")
    m_match = re.search(r"(\d+(?:\.\d+)?)\s*m\b", text)
    if m_match and "mm" not in text and "cm" not in text:
        return float(m_match.group(1)) * 100.0
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    if not nums:
        return None
    return max(nums)


def build_short_filename(
    seq_id: int,
    category: str,
    caller_dim_raw: str = "",
    ext: str = ".jpg",
) -> str:
    """
    Koostab lühikese ja sorteeritava failinime:
      - Ilma mõõduta: `{kategooria}_ID{seq:03d}.jpg` (nt `tuveoonsus_ID068.jpg`)
      - Koos kasutaja mõõduga: `{kategooria}_{mooduklass}_ID{seq:03d}.jpg`
        (nt `oksaauk_alla30cm_ID091.jpg`)
    """
    cat_slug = category.strip().lower()
    if cat_slug not in CATEGORIES:
        raise ValueError(f"Tundmatu kategooria '{cat_slug}'. Lubatud: {list(CATEGORIES.keys())}")

    max_cm = parse_caller_dimension_cm(caller_dim_raw)
    dim_cat = get_dimension_category(max_cm)

    if dim_cat:
        return f"{cat_slug}_{dim_cat}_ID{seq_id:03d}{ext}"
    return f"{cat_slug}_ID{seq_id:03d}{ext}"


def get_product_spec_for_seq(seq_id: int) -> tuple[str, str, str, str]:
    """
    Tagastab (product_id, category, product_title, scale_ref) antud järjekorranumbrile (1..125).
    """
    for idx, (start_s, end_s, cat, title, scale_ref, _conf) in enumerate(PRODUCT_GROUPS_SPEC, 1):
        if start_s <= seq_id <= end_s:
            return f"PUIDUJAK-{idx:03d}", cat, title, scale_ref
    raise ValueError(f"Järjekorranumber {seq_id} ei kuulu ühtegi tootesse (1..125)")


def classify_photo_by_index(seq_id: int) -> tuple[str, str]:
    """
    Määrab 125 unikaalsele fotole (ID 1..125) visuaalse ülevaate põhjal
    ühtse kategooria ja täpse lühikirjelduse.
    """
    _pid, cat, title, _scale = get_product_spec_for_seq(seq_id)
    return cat, title


def parse_pildid_kategooriad_md(md_path: Path) -> list[dict]:
    """Loeb 125 unikaalse pildi järjekorra (1..125) ja originaalnimed."""
    items = {}
    pattern = re.compile(r"^-\s+(\d+)\.\s+(PXL_[0-9_]+(?:\.MP)?\.jpg)\s+–\s+(.+)$")
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line.strip())
        if m:
            seq_id = int(m.group(1))
            orig_name = m.group(2)
            old_desc = m.group(3)
            items[seq_id] = {
                "seq_id": seq_id,
                "original_name": orig_name,
                "old_desc": old_desc,
            }
    return [items[k] for k in sorted(items.keys())]


def generate_catalog_csv(
    md_path: Path,
    csv_out_path: Path,
    existing_dims: Optional[dict[int, str]] = None,
) -> list[dict]:
    """
    Genereerib täieliku CSV-tabeli 125 foto kohta, kus `moot_cm` väli on jäetud
    kasutajale täitmiseks (vaikimisi tühi).
    """
    photos = parse_pildid_kategooriad_md(md_path)
    rows = []
    for p in photos:
        seq_id = p["seq_id"]
        pid, cat, short_desc, _scale = get_product_spec_for_seq(seq_id)
        caller_dim = (existing_dims or {}).get(seq_id, "")
        max_cm = parse_caller_dimension_cm(caller_dim)
        dim_cat = get_dimension_category(max_cm)
        new_filename = build_short_filename(seq_id, cat, caller_dim, ext=".jpg")

        rows.append(
            {
                "id": f"ID{seq_id:03d}",
                "seq_nr": seq_id,
                "product_id": pid,
                "kategooria": cat,
                "moot_cm": caller_dim,
                "mooduklass": dim_cat,
                "uus_failinimi": new_filename,
                "originaal_failinimi": p["original_name"],
                "luhikirjeldus": short_desc,
            }
        )

    fieldnames = [
        "id",
        "seq_nr",
        "product_id",
        "kategooria",
        "moot_cm",
        "mooduklass",
        "uus_failinimi",
        "originaal_failinimi",
        "luhikirjeldus",
    ]
    with csv_out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


if __name__ == "__main__":
    md_file = Path("/workspace/puidujaak/pildid_kategooriad.md")
    csv_file = Path("/workspace/puidujaak/pildid_nimetamine.csv")
    rows = generate_catalog_csv(md_file, csv_file)
    print(f"Genereeritud {len(rows)} rida faili {csv_file}")
