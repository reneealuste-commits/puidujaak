#!/usr/bin/env python3
"""
Puidujaak.ee fotode sorteerimise ja lühikese ümbernimetamise süsteem.

Nõuded:
1. Iga foto saab lühikese ja selge nime, mis algab KATEGOORIAGA (et kaustas nime järgi
   sorteerides koondaks kõik sama tüüpi pildid kokku) ning sisaldab JÄRJEKORRANUMBRIT (ID1..ID125).
2. Lihtsad visuaalsed kategooriad:
   - oksaauk     (oksaauguga koor/puit)
   - oksakrae    (oksakrae, okslik tüvejupp või koor oksakraega)
   - tuveoonsus  (tüveõõnsus, seest pehkinud/käsnjas või õõnes tüveosa)
   - ketas       (tüveketas / ristlõige)
   - koor        (paks korbatanud koor või pahk)
   - erikuju     (erikujuline töökojajääk / CNC / laserlõige)
   - klots       (liimpuidu- või okaspuuklots / ruutprofiil)
   - plaat       (plaatmaterjal, sandwich-plaat, vineer)
   - laud        (laud, liist, spoon)
   - palk        (palk või känd)
   - alus        (puitalus)
3. Umbkaudsed mõõdud (`pikkus_cm`) sisestab kasutaja ise — skript EI paku ega arva
   pildilt mõõte (vaikimisi tühi ""). Kui kasutaja sisestab mõõdu (cm), arvutab kood
   automaatselt mõõdukategooria:
   - alla30cm  (< 30 cm)
   - alla50cm  (30–49.9 cm)
   - alla1m    (50–99.9 cm)
   - yle1m     (>= 100 cm)
   Kui mõõt on veel sisestamata, jäetakse mõõduklass failinimest välja, et nimi püsiks lühike!
   Näide ilma mõõduta: `tuveoonsus_ID072.jpg` (või `oksaauk_ID091.jpg`)
   Näide sisestatud mõõduga (nt 28 cm): `oksaauk_alla30cm_ID091.jpg`
4. Originaalfaile ei kustutata ega teisaldata; `--apply-local` nimetab failid ümber
   (või loob sorteeritud nimega viited/ümbernimetuse).
"""

import argparse
import csv
import os
import re
from pathlib import Path
from typing import Optional

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
    # Kui on meetrites (nt "1.2m"), teisenda sentimeetriteks
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
      - Ilma mõõduta: `{kategooria}_ID{seq:03d}.jpg` (nt `tuveoonsus_ID072.jpg`)
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


def classify_photo_by_index(seq_id: int) -> tuple[str, str]:
    """
    Määrab 125 unikaalsele fotole (ID 1..125) visuaalse ülevaate põhjal
    lihtsa kategooria ja lühikirjelduse.
    """
    # 1. Plaadid, profiilid, klotsid, lauad (töökoda, ID 1..59)
    if 1 <= seq_id <= 19:
        return "plaat", "Valge/pinnakattega plaat"
    if 20 <= seq_id <= 30 or seq_id in (33, 34):
        return "laud", "Hele laud/liist või spoon"
    if seq_id in (31, 32, 35):
        return "plaat", "Vineeri/kihtplaadi serv"
    if 36 <= seq_id <= 38:
        return "klots", "Valge ruutprofiil"
    if 39 <= seq_id <= 56:
        return "plaat", "Valge plaadiriba"
    if 57 <= seq_id <= 59:
        return "klots", "Liimpuidust/okaspuust klots"

    # 2. Erikujulised töökojajäägid (ID 60..67)
    if 60 <= seq_id <= 66:
        return "erikuju", "Kiilukujuline augu ja pinnuga jääk"
    if seq_id == 67:
        return "erikuju", "Kaarjas laserlõigatud vineerijääk"

    # 3. Tüveõõnsus, oksaauk, oksakrae, tüvekettad ja koor (ID 68..97)
    if seq_id in (68, 72, 79, 80, 81, 82, 83, 88, 89, 90, 96, 97):
        return "tuveoonsus", "Tüveõõnsus / seest pehkinud tüveosa"
    if seq_id in (73, 91):
        return "oksaauk", "Oksaauguga korbatanud koor/tüveosa"
    if seq_id in (92, 95):
        return "oksakrae", "Oksakrae / okslik tüveosa"
    if seq_id in (74, 75):
        return "ketas", "Südamekujuline tüveketas"
    if seq_id in (69, 70, 71, 85, 86, 87):
        return "ketas", "Tüveketas ristlõikes"
    if seq_id in (76, 77, 78, 84, 93, 94):
        return "koor", "Paks korbatanud kooretükk / pahk"

    # 4. Palgid, kännud, puitalused, pikad lauad (ID 98..125)
    if 98 <= seq_id <= 106 or 110 <= seq_id <= 113:
        return "palk", "Palk või juurekaelaga känd õues"
    if 107 <= seq_id <= 109 or 114 <= seq_id <= 120:
        return "alus", "Puitalus / aluste virn"
    if 121 <= seq_id <= 125:
        return "laud", "Pikad okaspuulauad / lauavirn"

    return "plaat", "Puidujääk"


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
        cat, short_desc = classify_photo_by_index(seq_id)
        caller_dim = (existing_dims or {}).get(seq_id, "")
        max_cm = parse_caller_dimension_cm(caller_dim)
        dim_cat = get_dimension_category(max_cm)
        new_filename = build_short_filename(seq_id, cat, caller_dim, ext=".jpg")

        # Näidis sellest, kuidas nimi muutub kohe, kui kasutaja mõõdu sisestab
        rows.append(
            {
                "id": f"ID{seq_id:03d}",
                "seq_nr": seq_id,
                "kategooria": cat,
                "moot_cm": caller_dim,  # KASUTAJA TÄIDAB (nt "25", "45", "80", "120")
                "mooduklass": dim_cat,  # Arvutatakse automaatselt: alla30cm / alla50cm / alla1m / yle1m
                "uus_failinimi": new_filename,
                "originaal_failinimi": p["original_name"],
                "luhikirjeldus": short_desc,
            }
        )

    fieldnames = [
        "id",
        "seq_nr",
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


def update_names_from_csv(csv_path: Path, apply_local_dir: Optional[Path] = None) -> list[dict]:
    """
    Loeb CSV-faili (kuhu kasutaja on lisanud `moot_cm` või muutnud `kategooria` veergu),
    uuendab `mooduklass` ja `uus_failinimi` veerud ning soovi korral nimetab failid ümber.
    """
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    for r in rows:
        seq_id = int(r["seq_nr"])
        cat = r["kategooria"].strip()
        caller_dim = r.get("moot_cm", "").strip()
        max_cm = parse_caller_dimension_cm(caller_dim)
        r["mooduklass"] = get_dimension_category(max_cm)
        r["uus_failinimi"] = build_short_filename(seq_id, cat, caller_dim, ext=".jpg")

        if apply_local_dir:
            src = apply_local_dir / r["originaal_failinimi"]
            dst = apply_local_dir / r["uus_failinimi"]
            if src.exists() and src != dst:
                os.rename(src, dst)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Puidujaak.ee fotode lühinimetamine ja sorteerimine.")
    parser.add_argument(
        "--md",
        type=Path,
        default=Path("/workspace/puidujaak/pildid_kategooriad.md"),
        help="Sisend-markdown 125 fotoga",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("/workspace/puidujaak/pildid_nimetamine.csv"),
        help="Väljund/sisend CSV tabel (kuhu saab lisada mõõdud)",
    )
    parser.add_argument(
        "--recalc",
        action="store_true",
        help="Arvuta olemasolevast CSV-st mõõduklassid ja failinimed uuesti",
    )
    parser.add_argument(
        "--apply-local",
        type=Path,
        default=None,
        help="Valikuline: kaust, kus failid päriselt ümber nimetada",
    )
    args = parser.parse_args()

    if args.recalc and args.csv.exists():
        updated = update_names_from_csv(args.csv, apply_local_dir=args.apply_local)
        print(f"Uuendatud {len(updated)} kirjet failis {args.csv}")
    else:
        created = generate_catalog_csv(args.md, args.csv)
        print(f"Loodud {len(created)} kirjet failis {args.csv}")
