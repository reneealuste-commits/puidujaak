#!/usr/bin/env python3
"""
Puidujaak.ee toodete grupeerimise skript (parandatud versioon).

Mis oli vana koodi viga:
1. Vana `group.py` grupeeris pilte ainult failinime kellaaja vahe (`>= 120` sekundit) järgi.
   22.10.2026 õuesessioonil pildistati erinevaid puidutükke 7–25 sekundi vahega, mistõttu
   kõik järjestikused tükid sattusid ühte suurde ajasegmenti.
2. Vana `split(s)` funktsioon sisaldas vigast kitsendust:
     `cand = [g for g in gaps if 2 <= g[1] <= len(s)-4] or gaps`
   ning lõpetas poolitamise kui `len(s) <= 6`. See sundis igasse gruppi jääma VÄHEMALT 3 fotot
   (`>= 3`), mistõttu 1-pildised (nt ID068, ID069, ID070, ID073, ID084, ID093, ID094, ID095)
   ja 2-pildised tooted kleebiti vägisi naabertoodete külge!
3. Vana kood ei kontrollinud kategooriate ega visuaalse eseme ühtsust grupi sees (nt pandi
   ühte patta `tuveoonsus` ID068, samblane pakk ID069 ja südamekujuline `ketas` ID070).

Parandatud loogika:
- Iga toode (`PUIDUJAK-001` .. `PUIDUJAK-049`) koosneb täpselt ühe ja sama füüsilise
  puidutüki (või aluse/palgipartii) fotodest (lubatud on 1, 2, 3 või enam fotot).
- Ühe toote sees ei tohi kunagi olla erineva kategooriaga fotosid.
"""

import csv
import json
from pathlib import Path

# Visuaalselt ja kategooria järgi kontrollitud 49 tootegruppi (ID001..ID125 -> PUIDUJAK-001..049)
# Formaat: (start_seq, end_seq, category, title, scale_ref, confidence)
PRODUCT_GROUPS_SPEC = [
    (1, 5, "plaat", "Helerohelise vahtsüdamikuga sandwich-plaat töökoja laual", "Ilma joonlauata laual", "high"),
    (6, 6, "plaat", "Valge kattega ja puitlaastsüdamikuga plaadiriba otsavaates", "Ilma joonlauata laual", "high"),
    (7, 12, "plaat", "Valge kattega sandwich-plaat (~2 cm) L-metalljoonlauaga", "L-metalljoonlaud fotol", "high"),
    (13, 15, "plaat", "Valge kattega sandwich-plaadi nurk metalljoonlauaga", "Metalljoonlaud fotol", "high"),
    (16, 19, "plaat", "Pikk valge kattega ja rohekassinise südamikuga sandwich-plaat (~32 cm)", "Metalljoonlaud fotol", "high"),
    (20, 20, "laud", "Õhuke tumedam peenekiuline spoonitükk (~5 cm lai)", "Metalljoonlaud fotol", "high"),
    (21, 23, "laud", "Hele õhuke höövelpinnaga puitlauake (~5,5 cm lai, ~6 mm paks)", "Metalljoonlaud fotol", "high"),
    (24, 27, "laud", "Hele puitliist (~15 mm servaprofiiliga)", "Metalljoonlaud fotol", "high"),
    (28, 30, "laud", "Pikk hele puitlauake (~5,5 cm lai, ~50 cm pikk)", "Metalljoonlaud fotol", "high"),
    (31, 32, "plaat", "Kihiline vineeri/kihtplaadi nurk (~1,5 cm paks)", "Metalljoonlaud fotol", "high"),
    (33, 34, "laud", "Kitsas hele puitliist (~3 × 1,5 cm)", "Metalljoonlaud fotol", "high"),
    (35, 35, "plaat", "Kihiline vineeri/kihtplaadi serv (~1,8 cm paks)", "Metalljoonlaud fotol", "high"),
    (36, 38, "klots", "Valge pinnakattega ruutprofiil / klots (~2,5 × 2,5 cm)", "Metalljoonlaud fotol", "high"),
    (39, 42, "plaat", "Pikk valge plaadiriba (~5 cm lai) ümmarguse avaga", "Metalljoonlaud fotol", "high"),
    (43, 44, "plaat", "Paks (~4,5 cm) helesinise servaga sandwich-plaadi plokk", "Metalljoonlaud fotol", "high"),
    (45, 47, "plaat", "Neli püstist valge kattega plaadiriba (~50 cm)", "Metalljoonlaud fotol", "high"),
    (48, 54, "plaat", "Suur valge kattega sandwich-plaat (~49,4 cm lai, 3 cm paks)", "Metalljoonlaud fotol", "high"),
    (55, 56, "plaat", "Õhem (~2 cm) valge kattega sandwich-plaat servavaates", "Metalljoonlaud fotol", "high"),
    (57, 59, "klots", "Liimpuidust / okaspuust paks klots (~4,5 × 10 cm)", "Metalljoonlaud fotol", "high"),
    (60, 66, "erikuju", "Kiilukujuline ümmarguse augu ja terava pinnuga hele puidujääk", "Metalljoonlaud fotol (ID061–066)", "high"),
    (67, 67, "erikuju", "Kaarjas laserlõigatud kasevineeri jääk (~48 cm)", "2× 50 cm metalljoonlaud fotol", "high"),
    (68, 68, "tuveoonsus", "Õhuke ümmargune seest tühi korbatanud tüverõngas", "Puitlaual (mõõtkavata)", "high"),
    (69, 69, "tuveoonsus", "Paks samblane seest õõnes tüvepakk", "20 € kupüür fotol", "high"),
    (70, 70, "ketas", "Südamekujuline tüveketas (ristlõige) kupüüriga", "20 € kupüür fotol", "high"),
    (71, 72, "tuveoonsus", "Hobuserauakujuline (C-kujuline) vaigune ja seenekirjaga tüveõõnsus", "20 € kupüür fotol (ID071)", "high"),
    (73, 73, "oksaauk", "U-kujuline oksaauguga korbatanud kooretükk", "Puitlaual (mõõtkavata)", "high"),
    (74, 75, "ketas", "Südamekujuline tüveketas sümmeetriliste aastarõngastega (lähivõtted)", "Lähivõte looduses", "high"),
    (76, 77, "koor", "Ümar tume korbatanud koore- ja pahatükk", "Lähivõte maas ja puitlaual", "high"),
    (78, 81, "tuveoonsus", "Suur sõõrikukujuline („O“-kujuline) paksu korbaga tüveõõnsus", "50 € kupüür fotol", "high"),
    (82, 83, "tuveoonsus", "Tüvelõige ülaosa pehkinud õõnsuse ja diagonaalse saejäljega", "50 € kupüür fotol (ID082)", "high"),
    (84, 84, "koor", "Kumer sügava tekstuuriga korbatanud kooretükk / pahk", "Puitlaual (mõõtkavata)", "high"),
    (85, 87, "ketas", "Paksu korbaga tüvepakk ja väike ümar tüveketas", "50 € kupüür fotol", "high"),
    (88, 90, "tuveoonsus", "Pealtvaates tüveketas suure keskse käsnja pehkinud õõnsusega", "50 € kupüür fotol", "high"),
    (91, 92, "oksaauk", "Suure ümara oksaauguga („silmaga“) korbatanud kooretükk", "Puitlaual (mõõtkavata)", "high"),
    (93, 93, "koor", "Väiksem tume korbatanud kooretükk", "50 € kupüür fotol", "high"),
    (94, 94, "tuveoonsus", "Seest pehkinud südamikuga väiksem tüvelõige", "50 € kupüür fotol", "high"),
    (95, 95, "oksakrae", "Kolme heleda oksakraega (~26 cm) okslik tüvejupp", "Kollane mõõdulint fotol (~26 cm)", "high"),
    (96, 97, "tuveoonsus", "Käsnjalt pehkinud suure siseõõnsuse ja oksatüükaga tüveosa", "Puitlaual (mõõtkavata)", "high"),
    (98, 99, "palk", "Kaks hallinenud okaspuupalki õues", "20 € kupüür fotol", "high"),
    (100, 102, "palk", "Suur harunev juurekaelaga tüveosa / känd punakaspruuni puiduga", "20 € kupüür fotol (ID100)", "high"),
    (103, 103, "palk", "Kuivanud okaspuukänd paljastunud juurtega", "Õues metsa all", "high"),
    (104, 106, "palk", "Pahklik püstise haruga juurekaela- ja tüveosa", "Vineerplaadil õues", "high"),
    (107, 108, "alus", "Üksik kasutatud puitalus kivisillutisel", "Standardne kaubaalus", "high"),
    (109, 109, "alus", "Kasutatud puitaluste virn (4–5 tk) murul", "Standardne kaubaalus", "high"),
    (110, 113, "palk", "Pikk hallinenud palk murul (üldvaated ja otsalõige)", "Mõõtkavakaart otsalõikel (ID112–113)", "high"),
    (114, 117, "alus", "Kõrge kasutatud puitaluste virn võrkaia ääres", "Standardne kaubaalus", "high"),
    (118, 120, "alus", "Madalamad kasutatud puitaluste virnad rohelise seina ääres", "Standardne kaubaalus", "high"),
    (121, 124, "laud", "Kaks pikka (~240 cm) okaspuulauda merekonteineri najal", "Kollane mõõdulint fotol (~240 cm)", "high"),
    (125, 125, "laud", "Laudade virn konteineri kõrval maas", "Õues konteineri ääres", "high"),
]


def main():
    raw_path = Path("/workspace/agent-tools/38b1f3db-02fe-44ae-a59f-09fc2cf9f90f.txt")
    if raw_path.exists():
        d = json.loads(raw_path.read_text(encoding="utf-8"))
        fs = [f for f in d["items"] if f["mime_type"] == "image/jpeg"]
        uniq = []
        seen = {}
        for f in fs:
            if f["name"] in seen:
                seen[f["name"]].append(f)
                continue
            seen[f["name"]] = [f]
            uniq.append(f)
        uniq.sort(key=lambda f: f["name"])
    else:
        # Fallback to existing puidujak_mapping.csv if raw listing file was cleaned up
        existing = list(csv.DictReader(open("/workspace/puidujak_mapping.csv", encoding="utf-8")))
        seen = {}
        uniq = []
        for r in existing:
            name = r["original_name"]
            entry = {
                "id": r["file_id"],
                "name": name,
                "web_view_link": r["web_view_link"],
                "modified_time": r["modified_time"],
            }
            if name in seen:
                seen[name].append(entry)
            else:
                seen[name] = [entry]
                uniq.append(entry)
        uniq.sort(key=lambda f: f["name"])

    assert len(uniq) == 125, f"Expected 125 unique photos, got {len(uniq)}"

    rows = []
    out = []
    covered_indices = set()

    for prod_idx, (start_seq, end_seq, cat, title, scale_ref, conf) in enumerate(PRODUCT_GROUPS_SPEC, 1):
        pid = f"PUIDUJAK-{prod_idx:03d}"
        group_files = uniq[start_seq - 1 : end_seq]
        assert len(group_files) == (end_seq - start_seq + 1)
        for seq in range(start_seq, end_seq + 1):
            assert seq not in covered_indices, f"Duplicate seq {seq}"
            covered_indices.add(seq)

        out.append((pid, conf, [x["name"] for x in group_files]))
        for k, x in enumerate(group_files, 1):
            for dup_i, f in enumerate(seen[x["name"]]):
                rows.append(
                    dict(
                        file_id=f["id"],
                        original_name=f["name"],
                        product_id=pid,
                        new_name=f"{pid}_A{k}.jpg" if dup_i == 0 else f"{pid}_A{k}_dup{dup_i}.jpg",
                        target_folder_id="",
                        confidence=conf if dup_i == 0 else "duplicate-upload",
                        web_view_link=f["web_view_link"],
                        modified_time=f["modified_time"],
                    )
                )

    assert covered_indices == set(range(1, 126)), "Not all 1..125 photos covered!"

    Path("/workspace/groups.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    with open("/workspace/puidujak_mapping.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Successfully generated {len(out)} visually verified product groups across {len(uniq)} unique photos ({len(rows)} total Drive entries).")


if __name__ == "__main__":
    main()
