#!/usr/bin/env python3
"""
Builds /workspace/puidujaak/veeb_deploy/index.html and /workspace/puidujaak/veeb/index.html with:
- 67 product groups (PUIDUJAK-001..PUIDUJAK-067) and 185 unique photos (ID001..ID185)
- Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue, lat 59.3188, lng 24.5612)
- 60-day auction countdown timer on every product:
  * 7,00 € starting price for unique/sculptural pieces (erikuju, tuveoonsus, oksaauk, oksakrae, ketas, koor)
  * 2,00 € starting price for standard wood (laud, klots, palk, alus, plaat, trummel)
  * 5 min extended end (pikenev lõpp 5 min)
  * Free (0,00 € TASUTA) after 60 days
- "Osta kohe" button on every product opening the 0 €/month Montonio + Merit Aktiva customer journey & PDF invoice modal
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/workspace")
from group import (
    ACCESS_TYPES,
    EXTRA_SEQS_BY_PROD_IDX,
    PRODUCT_GROUPS_SPEC,
    get_product_access_and_location,
)

UNIQUE_AUCTION_CATEGORIES = {"erikuju", "tuveoonsus", "oksaauk", "oksakrae", "ketas", "koor"}

SHOWCASE_PRODUCTS = {
    "PUIDUJAK-020": ("Erikujuline jääk", "Skulpturaalne kiilukujuline puidujääk läbiva ümmarguse augu ja kõrge terava pinnuga.", 0),
    "PUIDUJAK-021": ("Erikujuline jääk", "Laserlõikusest üle jäänud kahe poolkaarega 48 cm kasevineeri jääk metalljoonlaua kõrval.", 0),
    "PUIDUJAK-022": ("Tüveõõnsus / rõngas", "Õhuke ümmargune seest tühi korbatanud koorega tüverõngas puitlaual (eraldi toode).", 0),
    "PUIDUJAK-023": ("Tüveõõnsus / pakk", "Paks samblane seest õõnes tüvepakk 20 € kupüüriga (eraldi toode).", 0),
    "PUIDUJAK-024": ("Erikujuline / disain", "Looduslikult südamekujuline tüve ristlõige 20 € kupüüriga mõõtkavaks.", 0),
    "PUIDUJAK-025": ("Kahjustusega / seenmuster", "Hobuserauakujuline (C-kujuline) männipaku ristlõige sügava lõhe, mustade seenekirjadega (spalting) ja vaigulaikudega.", 1),
    "PUIDUJAK-026": ("Oksaauk", "U-kujuline oksaauguga korbatanud koore- ja tüveosa puitlaual.", 0),
    "PUIDUJAK-027": ("Erikujuline / disain", "Looduslikult südamekujuline tüve ristlõige kahe sümmeetrilise aastarõnga „silmaga“ lähivõttes.", 0),
    "PUIDUJAK-028": ("Koor ja pahk", "Sügavate vagude ja rohelise samblaga paks korbatanud pahatükk (terraariumi/dekoori materjal).", 0),
    "PUIDUJAK-029": ("Tüveõõnsus / rõngas", "30–35 cm läbimõõduga sõõrikukujuline („O“-kujuline) seest tühi tüverõngas paksu krobelise korbaga (50 € kõrval).", 2),
    "PUIDUJAK-030": ("Kahjustusega puit", "Paks puiduplank rusikasuuruse sisemise õõnsuse, tumeda veekahjustuse ja diagonaalse saesisselõikega (50 € kõrval).", 0),
    "PUIDUJAK-033": ("Käsnjas puit (Spongy)", "Pealtvaates tüveketas, mille keskel on tume käsnja servaga pehkinud õõnsus (50 € mõõtkavaks).", 0),
    "PUIDUJAK-034": ("Oksaauk", "Suure loodusliku ovaalse oksaauguga („silmaga“) vana korbatanud kooretükk.", 0),
    "PUIDUJAK-037": ("Oksakrae", "Kolme heleda oksakraega (~26 cm) okslik tüvejupp kollase mõõdulindi kõrval.", 0),
    "PUIDUJAK-038": ("Käsnjas puit (Spongy)", "Parim näide seest pehmeks ja muredaks pehkinud õõnsusega okslikust tüvetükist koos värske saelõikega.", 0),
    "PUIDUJAK-050": ("UUS! Kaablitrummel (~170 cm)", "Suur tööstuslik puidust kaablitrummel (ketta Ø ~165–175 cm, laius ~105 cm) + najale toetuv pikk pruss (~195 cm). Mõõtkavaks 50 € kupüür (140×77 mm).", 1),
    "PUIDUJAK-051": ("UUS! Ümarpalk (~255 cm)", "Ilmastikukindel ümarpalk/post betoonposti najal (pikkus ~250–260 cm, Ø ~15–18 cm). Mõõdetud Eesti salliga (13 triipu = 130 cm alumisel poolel).", 0),
    "PUIDUJAK-052": ("UUS! Samblane pruss (~100 cm)", "Samblase otsaga vana pruss / aiapost maas (pikkus ~100–105 cm, ristlõige ~12×12 cm). Kõrval täpselt 10 salli triipu (= 100 cm).", 0),
    "PUIDUJAK-053": ("UUS! Raamide virn (~120×100 cm)", "Puidust raamide / restkastide ja pukkide virn tellisseina ääres (laius ~120×100 cm, raami H ~75–80 cm, virna H ~155 cm; 7 salli triipu = 70 cm).", 0),
    "PUIDUJAK-054": ("UUS! Alused & palgijupid (~120 cm)", "Kasutatud puitaluste virn (3–4 tk, ~120×80 ja ~120×100 cm) + ümarad männipalgipakud (~40–60 cm, Ø ~25–30 cm) Valvoline vaatide kõrval.", 0),
    "PUIDUJAK-055": ("UUS! Oksakohaga pakk (~45 cm)", "Suure ovaalse oksakohaga (~25×18 cm) lehtpuupakk (~45×40 cm), mõõtkavaks 50 € kupüür.", 0),
    "PUIDUJAK-056": ("UUS! Laineline tüvelõige (~32 cm)", "Kumer lainelise puidusüüga tüvelõige / puitpakk (~32 × 18 × 24 cm), mõõtkavaks kokkusurutud 0,5 L pudel (~20,5 cm).", 0),
    "PUIDUJAK-057": ("UUS! Lehtpuuklots (25 cm)", "Tihedasüüline korbatanud servaga lehtpuuklots (25 × 15 × 9 cm), mõõdulindi ja 10 € kupüüriga.", 0),
    "PUIDUJAK-058": ("UUS! Koorekonteiner (~180 cm)", "Metallkonteiner täis männikoort ja pinnapuidu jääke (~180×150 cm, seina H = 9 salli triipu = 90 cm).", 0),
    "PUIDUJAK-059": ("UUS! Puitliistud & spoon (~200 cm)", "Õhukesed saetud puitliistud ja spooniribad metallraamil (~3–5 mm paksud, ~8–10 cm laiad, ~200 cm pikad).", 0),
    "PUIDUJAK-060": ("UUS! 40 m³ saepuru konteiner", "Suur 40 m³ multilift-konteiner puhta kuiva okaspuu saepuruga otse aspiratsioonist.", 0),
    "PUIDUJAK-061": ("UUS! Prussid varjualuses (~300 cm)", "Pikad saetud puitliistud ja prussid varjualuses (~5×5 ja ~5×10 cm, pikkus ~300 cm, 160 cm salliga).", 0),
    "PUIDUJAK-062": ("UUS! Servatud lauad (~300 cm)", "Servatud okaspuulaudade virn Laimet 100 saeraami juures (8 kihti, H = 4 salli triipu = 40 cm, L ~300 cm).", 0),
    "PUIDUJAK-063": ("UUS! Pinnalauad (~270 cm)", "Servamata okaspuu pinnalaudade virn koorega (~270 cm pikad, laius ~120 cm, 160 cm salliga).", 0),
    "PUIDUJAK-064": ("UUS! Kütteklotside kuhi (~280 cm)", "Suur kütteklotside ja saetud puidujääkide kuhi (~15–25 cm klotsid, kuhja laius ~280 cm).", 0),
    "PUIDUJAK-065": ("UUS! Püstkastid / raamid (~195 cm)", "Kõrged puidust transpordiraamid / püstkastid aluspõhjal (~8–10 tk reas, H ~195 cm, põhi ~120×90 cm).", 0),
    "PUIDUJAK-066": ("UUS! Klotsikonteiner (~2,5 m³)", "Metallkonteiner (H 110 cm) täis saetud puiduklotse (20–25 × 10 × 4,5 cm) ja pinnalaudu.", 0),
    "PUIDUJAK-067": ("UUS! Suur koondhunnik (~25–35 rm)", "Suur pinnapuidu, pindade ja küttepuidu koondhunnik (6 vaadet: H ~240–260 cm, eesmine virn ~110 cm, L ~300–450 cm).", 0),
    "PUIDUJAK-068": ("UUS 26.10! Lehtpuupakud (~45 cm)", "Kolm ümarat lehtpuupakku / tüvejuppi kivisel pinnasel (Ø ~35–45 cm).", 0),
    "PUIDUJAK-069": ("UUS 26.10! Tähekujuline tüveketas (~65 cm)", "Suur sakilise servaga tähekujuline tüveketas / ristlõige okste peal (~65 cm, aiareha mõõtkavaks).", 0),
    "PUIDUJAK-070": ("UUS 26.10! Mitme haruga känd (~55 cm)", "Mitme haruga skulpturaalne känd / puidust alus asfaldil (~55×45 cm).", 0),
    "PUIDUJAK-071": ("UUS 26.10! Südamekujuline ketas (50 €)", "Loodusliku südamekujuga tüveketas / ristlõige võrgu peal (~38 cm, mõõtkavaks 50 € kupüür).", 1),
    "PUIDUJAK-072": ("UUS 26.10! Õõnes tüvepakk (~50 cm)", "Suur seest pehkinud ja tumeda õõnsusega tüveosa võrgu peal (~50 cm, kupüüriga).", 0),
    "PUIDUJAK-073": ("UUS 26.10! Südamekujuline ketas (~42 cm)", "Südamekujuline ja erikujuline tüveketas lehtedel ja härmatisel (~42 cm).", 1),
    "PUIDUJAK-074": ("UUS 26.10! Tüvepost & palgid (~90 cm)", "Püstine tüvepost ja palgijupid sügislehtedel (~60–90 cm).", 0),
    "PUIDUJAK-075": ("UUS 26.10! Kännulaud / abilaud (~55 cm)", "Massiivsest tüveplaadist kolme puitjalaga rustikaalne abilaud / kännulaud (~55×45 cm, 5 vaadet).", 4),
    "PUIDUJAK-076": ("UUS 26.10! Õõnsusega tüvekauss (~40 cm)", "Südamekujulise kontuuri ja keskse õõnsusega paks tüveketas / kauss (~40 cm).", 0),
    "PUIDUJAK-077": ("UUS 26.10! Õõnes kasepakk (~35 cm)", "Seest õõnes valge kasetohuga kasepakk (~35 cm) kuuseokste juures.", 0),
    "PUIDUJAK-078": ("UUS 26.10! Korbatanud pahk (~30 cm)", "Sügava tekstuuriga tume korbatanud kooretükk / pahk (~30 cm).", 0),
    "PUIDUJAK-079": ("UUS 26.10! Õõnes tüveketas (~48 cm)", "Suur loodusliku siseõõnsusega tüveketas (~48 cm), ümar ketas ja paksu korbaga õõnes tüvejupp.", 0),
    "PUIDUJAK-080": ("UUS 26.10! Rustikaalne laud (~50 cm)", "Heledast servamata tüveplaadist okslike jalgadega rustikaalne diivanilaud / pukk (~50×45 cm, 5 vaadet).", 4),
}

PHOTO_SHOWCASE = {
    "ID060": ("Erikujuline jääk", "Skulpturaalne kiilukujuline puidujääk läbiva ümmarguse augu ja kõrge terava pinnuga."),
    "ID067": ("Erikujuline jääk", "Laserlõikusest üle jäänud kahe poolkaarega 48 cm kasevineeri jääk metalljoonlaua kõrval."),
    "ID068": ("Tüveõõnsus / rõngas", "Õhuke ümmargune seest tühi korbatanud koorega tüverõngas puitlaual (eraldi toode)."),
    "ID069": ("Tüveõõnsus / pakk", "Paks samblane seest õõnes tüvepakk 20 € kupüüriga (eraldi toode)."),
    "ID070": ("Erikujuline / disain", "Looduslikult südamekujuline tüve ristlõige 20 € kupüüriga mõõtkavaks."),
    "ID072": ("Kahjustusega / seenmuster", "Hobuserauakujuline (C-kujuline) männipaku ristlõige sügava lõhe, mustade seenekirjadega (spalting) ja vaigulaikudega."),
    "ID073": ("Oksaauk", "U-kujuline oksaauguga korbatanud koore- ja tüveosa puitlaual."),
    "ID074": ("Erikujuline / disain", "Looduslikult südamekujuline tüve ristlõige kahe sümmeetrilise aastarõnga „silmaga“ lähivõttes."),
    "ID076": ("Koor ja pahk", "Sügavate vagude ja rohelise samblaga paks korbatanud pahatükk (terraariumi/dekoori materjal)."),
    "ID080": ("Tüveõõnsus / rõngas", "30–35 cm läbimõõduga sõõrikukujuline („O“-kujuline) seest tühi tüverõngas paksu krobelise korbaga (50 € kõrval)."),
    "ID082": ("Kahjustusega puit", "Paks puiduplank rusikasuuruse sisemise õõnsuse, tumeda veekahjustuse ja diagonaalse saesisselõikega (50 € kõrval)."),
    "ID083": ("Käsnjas puit (Spongy)", "Suure mureda siseõõnsuse ja tumeda värvimuutusega dekoratiivne tüvelõige."),
    "ID088": ("Käsnjas puit (Spongy)", "Pealtvaates tüveketas, mille keskel on tume käsnja servaga pehkinud õõnsus (50 € mõõtkavaks)."),
    "ID091": ("Oksaauk", "Suure loodusliku ovaalse oksaauguga („silmaga“) vana korbatanud kooretükk."),
    "ID095": ("Oksakrae", "Kolme heleda oksakraega (~26 cm) okslik tüvejupp kollase mõõdulindi kõrval."),
    "ID096": ("Käsnjas puit (Spongy)", "Parim näide seest pehmeks ja muredaks pehkinud õõnsusega okslikust tüvetükist koos värske saelõikega."),
}


def compute_prices(prod_idx: int, cat: str) -> tuple[float, float, bool]:
    is_unique = cat in UNIQUE_AUCTION_CATEGORIES
    alghind = 7.00 if is_unique else 2.00
    if prod_idx == 56:
        osta_kohe = 27.90
    elif prod_idx in (50, 58, 60, 62, 63, 64, 65, 66, 67):
        osta_kohe = 45.00
    elif is_unique:
        osta_kohe = 24.90
    else:
        osta_kohe = 12.00
    return alghind, osta_kohe, is_unique


def build_catalog_dict() -> dict:
    nim_rows = list(csv.DictReader(open("/workspace/puidujaak/pildid_nimetamine.csv", encoding="utf-8")))
    map_rows = [
        r
        for r in csv.DictReader(open("/workspace/puidujak_mapping.csv", encoding="utf-8"))
        if r["confidence"] != "duplicate-upload"
    ]
    map_by_orig = {r["original_name"]: r for r in map_rows}

    photos_by_seq = {}
    all_photos = []
    for r in nim_rows:
        seq = int(r["seq_nr"])
        pid = r["product_id"]
        prod_idx = int(pid.split("-")[1])
        m_row = map_by_orig[r["originaal_failinimi"]]
        pid_id = r["id"]
        sc_tag, sc_note = PHOTO_SHOWCASE.get(pid_id, ("", ""))
        _s, _e, _cat, _title, scale_ref, _conf = PRODUCT_GROUPS_SPEC[prod_idx - 1]
        alghind, osta_kohe, is_unique = compute_prices(prod_idx, r["kategooria"])
        ph_obj = {
            "id": pid_id,
            "seq_nr": seq,
            "product_id": pid,
            "category": r["kategooria"],
            "moot_cm": r["moot_cm"],
            "mooduklass": r["mooduklass"],
            "short_title": r["uus_failinimi"],
            "original_name": r["originaal_failinimi"],
            "drive_id": m_row["file_id"],
            "drive_link": m_row["web_view_link"],
            "short_desc": r["luhikirjeldus"],
            "detail_desc": f"{r['luhikirjeldus']} ({scale_ref})",
            "showcase_tag": sc_tag,
            "showcase_note": sc_note,
            "ligipaas_tyyp": r["ligipaas_tyyp"],
            "ligipaas_silt": r["ligipaas_silt"],
            "ligipaas_tingimused": r["ligipaas_tingimused"],
            "asukoht_nimi": r["asukoht_nimi"],
            "lat": float(r["lat"]),
            "lng": float(r["lng"]),
            "google_maps_pin": r["google_maps_pin"],
            "gps_allikas": r["gps_allikas"],
            "is_new_20261024": prod_idx >= 50,
            "is_unique_auction": is_unique,
            "alghind_eur": alghind,
            "osta_kohe_eur": osta_kohe,
            "oksjon_kestus_paeva": 60,
            "pikenev_lopp_min": 5,
            "tasuta_peale_60p": True,
        }
        photos_by_seq[seq] = ph_obj
        all_photos.append(ph_obj)

    products = []
    for prod_idx, (start_s, end_s, cat, title, scale_ref, _conf) in enumerate(PRODUCT_GROUPS_SPEC, 1):
        pid = f"PUIDUJAK-{prod_idx:03d}"
        seqs = list(range(start_s, end_s + 1)) + EXTRA_SEQS_BY_PROD_IDX.get(prod_idx, [])
        p_photos = [photos_by_seq[s] for s in seqs]
        sc_info = SHOWCASE_PRODUCTS.get(pid)
        is_showcase = sc_info is not None
        sc_tag = sc_info[0] if sc_info else ""
        sc_note = sc_info[1] if sc_info else ""
        cover_idx = sc_info[2] if sc_info and sc_info[2] < len(p_photos) else 0
        cover_ph = p_photos[cover_idx]
        if EXTRA_SEQS_BY_PROD_IDX.get(prod_idx):
            id_range = ", ".join(f"ID{s:03d}" for s in seqs)
        else:
            id_range = f"ID{start_s:03d}" if start_s == end_s else f"ID{start_s:03d}–ID{end_s:03d}"

        alghind, osta_kohe, is_unique = compute_prices(prod_idx, cat)

        products.append(
            {
                "product_id": pid,
                "prod_nr": prod_idx,
                "title": title,
                "scale_ref": scale_ref,
                "primary_category": cat,
                "categories": [cat],
                "cover_index": cover_idx,
                "cover_photo_id": cover_ph["id"],
                "cover_short_title": cover_ph["short_title"],
                "photo_count": len(p_photos),
                "id_range": id_range,
                "is_showcase": is_showcase,
                "is_new": prod_idx >= 50,
                "showcase_tag": sc_tag,
                "showcase_note": sc_note,
                "ligipaas_tyyp": cover_ph["ligipaas_tyyp"],
                "ligipaas_silt": cover_ph["ligipaas_silt"],
                "ligipaas_tingimused": cover_ph["ligipaas_tingimused"],
                "asukoht_nimi": cover_ph["asukoht_nimi"],
                "lat": cover_ph["lat"],
                "lng": cover_ph["lng"],
                "google_maps_pin": cover_ph["google_maps_pin"],
                "gps_allikas": cover_ph["gps_allikas"],
                "is_unique_auction": is_unique,
                "alghind_eur": alghind,
                "osta_kohe_eur": osta_kohe,
                "oksjon_kestus_paeva": 60,
                "pikenev_lopp_min": 5,
                "tasuta_peale_60p": True,
                "photos": p_photos,
            }
        )

    return {"products": products, "photos": all_photos}


AUCTION_AND_JOURNEY_CSS = """
/* === 60-DAY AUCTION + OSTA KOHE + MERIT AKTIVA JOURNEY CSS === */
.auction-panel {
  margin-top: 0.55rem;
  padding: 0.65rem 0.75rem;
  border-radius: 10px;
  background: #fdfaf4;
  border: 1px solid #e2d5c1;
  font-size: 0.82rem;
}
.auction-panel.unique-tier {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #f59e0b;
}
.auction-panel.free-tier {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-color: #10b981;
}
.auction-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.auction-timer-pill {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-weight: 700;
  font-size: 0.8rem;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  background: #1e293b;
  color: #f8fafc;
}
.auction-timer-pill.sniping {
  background: #dc2626;
  color: #fff;
  animation: pulseBg 1.2s infinite;
}
.auction-timer-pill.free-now {
  background: #059669;
  color: #fff;
}
@keyframes pulseBg {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.78; }
}
.auction-price-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-top: 0.4rem;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.auction-bid-val {
  font-size: 1.05rem;
  font-weight: 800;
  color: #1e293b;
}
.auction-tier-badge {
  font-size: 0.73rem;
  font-weight: 700;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
}
.auction-tier-badge.unique {
  background: #fef08a;
  color: #854d0e;
  border: 1px solid #facc15;
}
.auction-btn-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.45rem;
  margin-top: 0.5rem;
}
.btn-bid {
  background: #b45309;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 0.6rem;
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
}
.btn-bid:hover { background: #92400e; }
.btn-buy-now {
  background: #15803d;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 0.6rem;
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
}
.btn-buy-now:hover { background: #166534; }
.auction-test-bar {
  display: flex;
  gap: 0.35rem;
  margin-top: 0.4rem;
  flex-wrap: wrap;
}
.auction-test-btn {
  background: rgba(255,255,255,0.75);
  border: 1px dashed #94a3b8;
  color: #475569;
  border-radius: 6px;
  padding: 0.15rem 0.42rem;
  font-size: 0.71rem;
  cursor: pointer;
}
.auction-test-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}
.access-loc-box {
  margin-top: 0.45rem;
  padding: 0.45rem 0.65rem;
  border-radius: 8px;
  font-size: 0.78rem;
  line-height: 1.35;
  border: 1px solid rgba(0,0,0,0.08);
}
.journey-step-tabs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.4rem;
  margin: 0.75rem 0;
}
.journey-step-tab {
  padding: 0.5rem 0.4rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  text-align: center;
}
.journey-step-tab.active {
  background: #1e3a8a;
  color: #fff;
  border-color: #1e3a8a;
}
"""

JOURNEY_MODAL_HTML = """
<!-- Osta Kohe / Montonio + Merit Aktiva 0 €/kuu Kliendi Teekond Modal -->
<div class="modal" id="buyNowJourneyModal" role="dialog" aria-modal="true" onclick="if(event.target===this)closeBuyNowModal()">
  <div class="mk" style="max-width:780px;width:96%;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;flex-wrap:wrap;">
      <div>
        <span style="background:#dbeafe;color:#1e40af;font-weight:700;font-size:0.75rem;padding:0.18rem 0.55rem;border-radius:999px;">0 €/kuu Puidujaak.ee automaatika (Montonio + Merit Aktiva PDF)</span>
        <h3 style="margin:0.35rem 0 0;font-size:1.22rem;" id="bnModalTitle">🛒 Osta kohe & Kliendi teekond</h3>
      </div>
      <button type="button" class="btn sec" style="padding:0.28rem 0.65rem;font-size:0.85rem;" onclick="closeBuyNowModal()">✕ Sulge</button>
    </div>

    <div class="journey-step-tabs">
      <button type="button" class="journey-step-tab active" id="jTab1" onclick="switchJourneyStep(1)">1. Montonio Kassa</button>
      <button type="button" class="journey-step-tab" id="jTab2" onclick="switchJourneyStep(2)">2. E-kiri #1 (Kätte saadud)</button>
      <button type="button" class="journey-step-tab" id="jTab3" onclick="switchJourneyStep(3)">3. E-kiri #2 (Arve manusega)</button>
      <button type="button" class="journey-step-tab" id="jTab4" onclick="switchJourneyStep(4)">4. Merit Aktiva PDF-arve</button>
    </div>

    <!-- STEP 1: MONTONIO CHECKOUT -->
    <div id="journeyStep1">
      <div style="display:flex;gap:0.8rem;align-items:center;background:#faf6ef;padding:0.7rem;border-radius:10px;border:1px solid var(--border);margin-bottom:0.75rem;">
        <img id="bnThumb" src="/photos/ID140.webp" alt="" style="width:72px;height:62px;object-fit:cover;border-radius:8px;flex-shrink:0;">
        <div style="flex:1;font-size:0.86rem;">
          <div><b id="bnProdId">PUIDUJAK-056</b> · <code id="bnShortTitle">erikuju_alla50cm_ID140.jpg</code></div>
          <div id="bnProdDesc" style="color:var(--m);margin-top:2px;">Kumer lainelise puidusüüga tüvelõige (~32 × 18 × 24 cm)</div>
          <div id="bnLocLine" style="font-size:0.78rem;color:#15803d;font-weight:600;margin-top:3px;">📍 Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue) – 24/7 Dropoff</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.75rem;color:var(--m);">Toote hind</div>
          <div id="bnItemPrice" style="font-size:1.25rem;font-weight:800;color:#15803d;">27,90 €</div>
        </div>
      </div>

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:0.8rem;">
        <label style="margin-top:0;">1. Vali kättesaamise viis (Montonio Tarne / 24/7 Garaažiboks):</label>
        <select id="bnShippingSelect" style="width:100%;padding:0.55rem;border-radius:8px;border:1px solid #cbd5e1;font:inherit;margin-bottom:0.5rem;" onchange="updateBuyNowTotals()">
          <option value="3.50|SmartPosti pakiautomaat (Montonio)">📦 SmartPosti pakiautomaat (Montonio) — 3,50 €</option>
          <option value="0.00|Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue) 24/7 koodlukuga">🟢 Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue) 24/7 koodlukuga — 0,00 €</option>
          <option value="0.00|Järele tulemine asukohapunktis (Google Maps Pin)">📍 Järele tulemine kaardipunktis (Google Maps Pin) — 0,00 €</option>
        </select>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">
          <div>
            <label>Ostja nimi:</label>
            <input type="text" id="bnBuyerName" value="Renee Aluste" oninput="updateBuyNowTotals()">
          </div>
          <div>
            <label>Ostja e-post (kuhu saadetakse PDF-arve ja kood):</label>
            <input type="email" id="bnBuyerEmail" value="reneealuste@gmail.com" oninput="updateBuyNowTotals()">
          </div>
        </div>

        <div style="margin-top:0.7rem;padding:0.65rem;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
          <div style="font-size:0.84rem;">
            Pangaülekanne (Montonio: LHV / Swedbank / SEB / Coop) · Viitenumber <b>107026</b> (7-3-1 kontrolljärguga)
          </div>
          <div style="font-size:1.1rem;font-weight:800;color:#0f172a;" id="bnGrandTotal">Kokku: 31,40 €</div>
        </div>

        <div style="display:flex;gap:0.5rem;margin-top:0.75rem;flex-wrap:wrap;">
          <button type="button" class="btn-buy-now" style="flex:1;padding:0.65rem;font-size:0.92rem;" onclick="completeSimulatedMontonioOrder()">
            💳 Maksa Montonio pangalingiga & Genereeri Merit Aktiva PDF-arve →
          </button>
          <a href="/Puidujaak-OU-Arve-nr-2026-00514.pdf" target="_blank" class="btn sec" style="padding:0.65rem 0.9rem;font-size:0.86rem;">
            📄 Laadi alla PDF-arve (#2026-00514)
          </a>
        </div>
      </div>
    </div>

    <!-- STEP 2: EMAIL #1 -->
    <div id="journeyStep2" style="display:none;">
      <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;padding:0.75rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;flex-wrap:wrap;gap:0.4rem;">
          <div style="font-size:0.85rem;"><b>Teema:</b> Sinu tellimus lehel Puidujaak.ee saadi kätte! (#2026-00514)</div>
          <a href="/email_1_tellimus_kaes.html" target="_blank" class="btn sec" style="padding:0.25rem 0.6rem;font-size:0.78rem;">Ava täisekraanil ↗</a>
        </div>
        <iframe src="/email_1_tellimus_kaes.html" style="width:100%;height:380px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;"></iframe>
      </div>
    </div>

    <!-- STEP 3: EMAIL #2 -->
    <div id="journeyStep3" style="display:none;">
      <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;padding:0.75rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;flex-wrap:wrap;gap:0.4rem;">
          <div style="font-size:0.85rem;"><b>Teema:</b> Arve 2026-00514 sinu tellimusele #2026-00514 (manuses PDF)</div>
          <a href="/email_2_arve_manusega.html" target="_blank" class="btn sec" style="padding:0.25rem 0.6rem;font-size:0.78rem;">Ava täisekraanil ↗</a>
        </div>
        <iframe src="/email_2_arve_manusega.html" style="width:100%;height:380px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;"></iframe>
      </div>
    </div>

    <!-- STEP 4: MERIT AKTIVA PDF INVOICE -->
    <div id="journeyStep4" style="display:none;">
      <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;padding:0.75rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;flex-wrap:wrap;gap:0.4rem;">
          <div style="font-size:0.84rem;">
            <b>Merit Aktiva stiilis `#afddff` päisega PDF-arve:</b> <code>Puidujaak-OU-Arve-nr-2026-00514.pdf</code> (Viitenumber <code>107026</code> · Viivis <code>0,05% päevas</code>)
          </div>
          <a href="/Puidujaak-OU-Arve-nr-2026-00514.pdf" download class="btn-buy-now" style="padding:0.35rem 0.75rem;font-size:0.8rem;text-decoration:none;">⬇ Laadi alla PDF-arve</a>
        </div>
        <iframe src="/Puidujaak-OU-Arve-nr-2026-00514.pdf" style="width:100%;height:420px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;"></iframe>
      </div>
    </div>
  </div>
</div>
"""

AUCTION_AND_JOURNEY_JS = """
// === 60-DAY AUCTION STATE & MONTONIO + MERIT AKTIVA JOURNEY ===
const SIXTY_DAYS_SEC = 60 * 24 * 3600; // 5,184,000 sec
const EXTEND_WINDOW_SEC = 5 * 60;      // 300 sec (5 min anti-sniping)
let auctionState = {}; // product_id -> { remainingSec, currentBid, bidCount, isFree }

CATALOG.products.forEach((p, idx) => {
  // Stagger initial seconds slightly for realistic live countdowns while keeping ~59d 23h+
  const offsetSec = (idx * 137) % 3600;
  auctionState[p.product_id] = {
    remainingSec: SIXTY_DAYS_SEC - offsetSec,
    currentBid: p.alghind_eur || (p.is_unique_auction ? 7.00 : 2.00),
    bidCount: 0,
    isFree: false
  };
});

function formatCountdown(sec) {
  if (sec <= 0) return '0p 00t 00m 00s (60p TÄIS → TASUTA 0 €)';
  const d = Math.floor(sec / 86400);
  const h = Math.floor((sec % 86400) / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const pad = n => String(n).padStart(2, '0');
  return `${d}p ${pad(h)}t ${pad(m)}m ${pad(s)}s`;
}

function renderAccessBadge(item) {
  if (!item || !item.ligipaas_silt) return '';
  const bg = item.ligipaas_tyyp === 'dropoff_24_7' ? '#ecfdf5' : (item.ligipaas_tyyp === 'suletud_territoorium' ? '#fff7ed' : '#fefce8');
  const fg = item.ligipaas_tyyp === 'dropoff_24_7' ? '#14532d' : (item.ligipaas_tyyp === 'suletud_territoorium' ? '#9a3412' : '#854d0e');
  const pinUrl = item.google_maps_pin || ('https://www.google.com/maps?q=' + (item.lat || 59.3188) + ',' + (item.lng || 24.5612));
  return `<div class="access-loc-box" style="background:${bg};color:${fg};">
    <div style="font-weight:700;display:flex;justify-content:space-between;align-items:center;gap:6px;flex-wrap:wrap;">
      <span>${item.ligipaas_silt}</span>
      <a href="${pinUrl}" target="_blank" rel="noopener" onclick="event.stopPropagation();" style="color:#1d4ed8;text-decoration:underline;font-weight:700;">📍 Google Maps Pin ↗</a>
    </div>
    <div style="margin-top:2px;color:#334155;font-size:0.75rem;">${item.asukoht_nimi || ''}</div>
  </div>`;
}

function renderAuctionAndBuyNowBox(p, ph) {
  const st = auctionState[p.product_id] || {
    remainingSec: SIXTY_DAYS_SEC,
    currentBid: p.alghind_eur || 2.00,
    bidCount: 0,
    isFree: false
  };
  const isUnique = !!p.is_unique_auction;
  const isSnipingWindow = st.remainingSec > 0 && st.remainingSec <= EXTEND_WINDOW_SEC;
  const isFree = st.remainingSec <= 0 || st.isFree;
  const panelCls = isFree ? 'auction-panel free-tier' : (isUnique ? 'auction-panel unique-tier' : 'auction-panel');
  const timerCls = isFree ? 'auction-timer-pill free-now' : (isSnipingWindow ? 'auction-timer-pill sniping' : 'auction-timer-pill');
  const tierLabel = isUnique ? '✨ Erikujuline / unikaalne (alghind 7,00 €)' : '🪵 Tava puidujääk (alghind 2,00 €)';
  const currentPriceStr = isFree ? '0,00 € (TASUTA)' : `${st.currentBid.toFixed(2).replace('.', ',')} €`;
  const buyNowPrice = isFree ? 0.00 : (p.osta_kohe_eur || 12.00);
  const buyNowStr = isFree ? '🎁 Võta TASUTA (0,00 €)' : `🛒 Osta kohe (${buyNowPrice.toFixed(2).replace('.', ',')} €)`;

  return `
    <div class="${panelCls}" data-auction-panel="${p.product_id}">
      <div class="auction-top-row">
        <span class="auction-tier-badge ${isUnique ? 'unique' : ''}">${tierLabel}</span>
        <span class="${timerCls}" data-timer-for="${p.product_id}">⏱️ ${formatCountdown(st.remainingSec)}</span>
      </div>
      <div class="auction-price-row">
        <div>
          <span style="font-size:0.74rem;color:var(--m);">${st.bidCount > 0 ? `Pakkumisi (${st.bidCount})` : 'Oksjoni alghind'}:</span>
          <span class="auction-bid-val" data-bid-val-for="${p.product_id}">${currentPriceStr}</span>
        </div>
        <span style="font-size:0.72rem;color:#475569;">Pikenev lõpp: <b>5 min</b> · Peale 60p: <b>0 €</b></span>
      </div>
      <div class="auction-btn-grid">
        <button type="button" class="btn-bid" onclick="placeAuctionBid('${p.product_id}', '${ph.id}')">
          🔨 Pakun (${(st.currentBid + 1).toFixed(2).replace('.', ',')} €)
        </button>
        <button type="button" class="btn-buy-now" onclick="openBuyNowModal('${p.product_id}', '${ph.id}')">
          ${buyNowStr}
        </button>
      </div>
      <div class="auction-test-bar">
        <button type="button" class="auction-test-btn" onclick="simulateSnipingWindow('${p.product_id}')" title="Testi pikenevat lõppu (<5 min jäänud)">
          ⚡ Testi &lt;5 min (04:10)
        </button>
        <button type="button" class="auction-test-btn" onclick="simulateSixtyDaysExpired('${p.product_id}')" title="Testi 60 päeva täitumist (toode muutub 0 € tasuta äraandmiseks)">
          🎁 Testi 60p täis → 0 € TASUTA
        </button>
      </div>
    </div>
  `;
}

function placeAuctionBid(productId, photoId) {
  const st = auctionState[productId];
  if (!st) return;
  if (st.remainingSec <= 0 || st.isFree) {
    showToast(`🎁 60 päeva on täis! Toode ${productId} on nüüd TASUTA (0,00 €) — vajuta „Võta TASUTA“!`);
    openBuyNowModal(productId, photoId);
    return;
  }
  st.currentBid += 1.00;
  st.bidCount += 1;
  let extendedMsg = '';
  if (st.remainingSec < EXTEND_WINDOW_SEC) {
    st.remainingSec = EXTEND_WINDOW_SEC;
    extendedMsg = ' · ⚡ Pikenev lõpp (5 min): taimer pikenes 05:00 peale!';
  }
  showToast(`🔨 Pakkumine ${st.currentBid.toFixed(2).replace('.', ',')} € tootele ${productId} registreeritud!${extendedMsg}`);
  renderCatalog();
}

function simulateSnipingWindow(productId) {
  const st = auctionState[productId];
  if (!st) return;
  st.isFree = false;
  st.remainingSec = 250; // 04m 10s (< 5 min)
  showToast(`⚡ ${productId}: taimer seatud 04m 10s peale (< 5 min). Vajuta nüüd „Pakun“, et näha 5 min pikenemist!`);
  renderCatalog();
}

function simulateSixtyDaysExpired(productId) {
  const st = auctionState[productId];
  if (!st) return;
  st.remainingSec = 0;
  st.isFree = true;
  showToast(`🎁 ${productId}: 60 päeva täis! Toode on nüüd automaatselt 0,00 € (TASUTA äraandmine).`);
  renderCatalog();
}

setInterval(() => {
  Object.keys(auctionState).forEach(pid => {
    const st = auctionState[pid];
    if (st.remainingSec > 0 && !st.isFree) {
      st.remainingSec -= 1;
      if (st.remainingSec <= 0) {
        st.remainingSec = 0;
        st.isFree = true;
      }
    }
    document.querySelectorAll(`[data-timer-for="${pid}"]`).forEach(el => {
      el.textContent = `⏱️ ${formatCountdown(st.remainingSec)}`;
    });
  });
}, 1000);

let activeBuyNowProduct = null;
let activeBuyNowPhoto = null;

function openBuyNowModal(productId, photoId) {
  const prod = CATALOG.products.find(p => p.product_id === productId) || CATALOG.products[55] || CATALOG.products[0];
  const photo = (photoId && CATALOG.photos.find(x => x.id === photoId)) || prod.photos[0];
  activeBuyNowProduct = prod;
  activeBuyNowPhoto = photo;

  const st = auctionState[prod.product_id] || { isFree: false };
  const isFree = st.isFree || st.remainingSec <= 0;
  const price = isFree ? 0.00 : (prod.osta_kohe_eur || 27.90);
  const info = computePhotoTitleAndDim(photo);

  document.getElementById('bnModalTitle').textContent = isFree
    ? `🎁 Võta TASUTA (0,00 € peale 60p): ${prod.product_id}`
    : `🛒 Osta kohe: ${prod.product_id} (${price.toFixed(2).replace('.', ',')} €)`;
  document.getElementById('bnThumb').src = `/photos/${photo.id}.webp`;
  document.getElementById('bnProdId').textContent = `${prod.product_id} · ${photo.id}`;
  document.getElementById('bnShortTitle').textContent = info.shortTitle;
  document.getElementById('bnProdDesc').textContent = prod.title;
  document.getElementById('bnLocLine').textContent = `📍 ${prod.asukoht_nimi || 'Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue)'}`;
  document.getElementById('bnItemPrice').textContent = `${price.toFixed(2).replace('.', ',')} €`;

  switchJourneyStep(1);
  updateBuyNowTotals();
  document.getElementById('buyNowJourneyModal').classList.add('on');
}

function closeBuyNowModal() {
  document.getElementById('buyNowJourneyModal').classList.remove('on');
}

function switchJourneyStep(stepNum) {
  [1, 2, 3, 4].forEach(n => {
    const el = document.getElementById(`journeyStep${n}`);
    const tab = document.getElementById(`jTab${n}`);
    if (el) el.style.display = (n === stepNum) ? 'block' : 'none';
    if (tab) tab.classList.toggle('active', n === stepNum);
  });
}

function updateBuyNowTotals() {
  if (!activeBuyNowProduct) return;
  const st = auctionState[activeBuyNowProduct.product_id] || { isFree: false };
  const isFree = st.isFree || st.remainingSec <= 0;
  const itemPrice = isFree ? 0.00 : (activeBuyNowProduct.osta_kohe_eur || 27.90);
  const shipRaw = (document.getElementById('bnShippingSelect').value || '3.50').split('|')[0];
  const shipPrice = parseFloat(shipRaw) || 0.0;
  const total = itemPrice + shipPrice;
  document.getElementById('bnGrandTotal').textContent = `Kokku: ${total.toFixed(2).replace('.', ',')} €`;
}

function completeSimulatedMontonioOrder() {
  showToast('✅ Montonio makse kinnitatud! E-kiri #1, E-kiri #2 ja Merit Aktiva stiilis PDF-arve (#2026-00514) genereeritud!');
  switchJourneyStep(4);
}
"""


def update_index_html():
    catalog_obj = build_catalog_dict()
    catalog_json_str = json.dumps(catalog_obj, ensure_ascii=False)
    html_path = Path("/workspace/puidujaak/veeb_deploy/index.html")
    html = html_path.read_text(encoding="utf-8")

    # 1. Replace CATALOG JSON
    html, n_sub = re.subn(
        r"const CATALOG = \{.*?\};\n",
        f"const CATALOG = {catalog_json_str};\n",
        html,
        count=1,
        flags=re.S,
    )
    assert n_sub == 1, "Failed to replace CATALOG JSON in index.html"

    # 2. Ensure trummel is in CATEGORY_META
    if '"trummel":' not in html:
        html = html.replace(
            '"alus": { label: "alus (Puitalus)", icon: "📦" }',
            '"alus": { label: "alus (Puitalus)", icon: "📦" },\n  "trummel": { label: "trummel (Kaablitrummel)", icon: "🎡", highlight: true }',
        )

    # 3. Inject CSS before </style> if not present
    if "/* === 60-DAY AUCTION + OSTA KOHE + MERIT AKTIVA JOURNEY CSS === */" not in html:
        html = html.replace("</style>", AUCTION_AND_JOURNEY_CSS + "\n</style>", 1)

    # 4. Add topbar button to open the Montonio + Merit Aktiva Journey modal
    if "openBuyNowModal('PUIDUJAK-056'" not in html:
        html = html.replace(
            '<a href="#kontakt">Kontakt</a>',
            '<a href="#kontakt" onclick="openBuyNowModal(\'PUIDUJAK-056\', \'ID140\');return false;" style="color:#15803d;font-weight:700;">🛒 Kliendi teekond &amp; Merit PDF-arve</a>\n      <a href="#kontakt">Kontakt</a>',
            1,
        )

    # 5. Update hero stats to highlight 60p oksjon (2 € / 7 €) + Osta kohe
    html = html.replace(
        "<b>0 € ettemaks</b>\n      <span>1-klikiga „Olen huvitatud“ eeltellimine</span>",
        "<b>60p oksjon + Osta kohe</b>\n      <span>Alghind 2 € / erikuju 7 € · 5 min pikenev lõpp · peale 60p 0 €</span>",
    )

    # 6. Inject JOURNEY_MODAL_HTML before <!-- Lightbox Modal
    if 'id="buyNowJourneyModal"' not in html:
        html = html.replace(
            "<!-- Lightbox Modal for full photo view -->",
            JOURNEY_MODAL_HTML + "\n<!-- Lightbox Modal for full photo view -->",
            1,
        )

    # 7. Inject AUCTION_AND_JOURNEY_JS before function renderCatalog()
    if "renderAuctionAndBuyNowBox" not in html:
        html = html.replace(
            "function renderCatalog() {",
            AUCTION_AND_JOURNEY_JS + "\nfunction renderCatalog() {",
            1,
        )

    # 8. Inject renderAccessBadge(p) and renderAuctionAndBuyNowBox(p, ph) into renderProductCard(p)
    if "${renderAuctionAndBuyNowBox(p, ph)}" not in html:
        html = html.replace(
            '<p class="pcard-desc">${ph.detail_desc} · <span style="opacity:0.8">Fotod: ${p.id_range}</span></p>\n        ${showcaseBox}',
            '<p class="pcard-desc">${ph.detail_desc} · <span style="opacity:0.8">Fotod: ${p.id_range}</span></p>\n        ${showcaseBox}\n        ${renderAccessBadge(p)}\n        ${renderAuctionAndBuyNowBox(p, ph)}',
            1,
        )

    # 9. Inject renderAccessBadge(ph) and renderAuctionAndBuyNowBox(prod || ph, ph) into renderSinglePhotoCard(ph)
    if "${renderAuctionAndBuyNowBox(prod || ph, ph)}" not in html:
        html = html.replace(
            '${ph.showcase_note ? `<div class="showcase-box">${ph.showcase_note}</div>` : \'\'}',
            '${ph.showcase_note ? `<div class="showcase-box">${ph.showcase_note}</div>` : \'\'}\n        ${renderAccessBadge(ph)}\n        ${renderAuctionAndBuyNowBox(prod || ph, ph)}',
            1,
        )

    html_path.write_text(html, encoding="utf-8")
    veeb_copy = Path("/workspace/puidujaak/veeb/index.html")
    if veeb_copy.parent.exists():
        veeb_copy.write_text(html, encoding="utf-8")
    print(
        f"Updated {html_path}: {len(catalog_obj['products'])} products, "
        f"{len(catalog_obj['photos'])} photos, size={len(html)} bytes"
    )


if __name__ == "__main__":
    update_index_html()


def inject_unified_features():
    import shutil
    html_path = Path("/workspace/puidujaak/veeb_deploy/index.html")
    base_snap = Path("/workspace/puidujaak/index_base_snapshot.html")
    if base_snap.exists():
        shutil.copyfile(base_snap, html_path)

    update_index_html()
    html = html_path.read_text(encoding="utf-8")

    # 1. Add Leaflet CSS + unified.css in <head>
    head_inject = (
        '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">\n'
        '<link rel="stylesheet" href="/unified.css">\n</head>'
    )
    if '/unified.css' not in html:
        html = html.replace('</head>', head_inject, 1)

    # 2. Add Mode Switcher (Basic / Advanced), Shortlist & Theme Toggle in Topbar
    topbar_controls = """
    <div class="mode-cluster">
      <div class="mode-switch-group" role="group" aria-label="Vaate režiim">
        <button type="button" class="mode-switch-btn" id="modeBasicBtn" onclick="switchAppMode('basic')">🔥 Basic (Swipe)</button>
        <button type="button" class="mode-switch-btn active" id="modeAdvancedBtn" onclick="switchAppMode('advanced')">🛠️ Advanced</button>
      </div>
      <button type="button" class="shortlist-nav-btn" id="shortlistNavBtn" onclick="openShortlistModal()">💚 Lemmikud (<span id="shortlistCountBadge">0</span>)</button>
      <button type="button" class="theme-toggle-btn" id="themeToggleBtn" onclick="toggleTheme()">🌙 Tume</button>
    </div>
    """
    if 'id="modeBasicBtn"' not in html:
        html = html.replace(
            '<div class="nav-links">',
            topbar_controls + '\n    <div class="nav-links">\n      <a href="#mootmine" onclick="switchAppMode(\'advanced\')"><b>📏 Mõõda puitu</b></a>\n      <a href="#kaart" onclick="switchAppMode(\'advanced\')">🗺️ Kaart</a>',
            1
        )

    # 3. Add hero mode quick buttons
    if 'id="heroBasicBtn"' not in html:
        html = html.replace(
            '<a class="btn" href="#turuplats">Sirvi 80 toodet (212 fotot) ↓</a>',
            '<a class="btn" href="#turuplats" onclick="switchAppMode(\'advanced\')">Sirvi 80 toodet ↓</a>\n      <button class="btn sec" type="button" id="heroBasicBtn" onclick="switchAppMode(\'basic\')">🔥 Ava Basic Mode (Tinder-Swipe)</button>\n      <a class="btn sec" href="#mootmine" onclick="switchAppMode(\'advanced\')">📏 Ava puidu mõõtmislõuend</a>',
            1
        )

    # 4. Inject unified_sections.html before <section id="turuplats"
    sections_html = Path("/workspace/puidujaak/veeb_deploy/unified_sections.html").read_text(encoding="utf-8")
    if 'id="basicSwipeSection"' not in html:
        html = html.replace('<section id="turuplats"', sections_html + '\n<section id="turuplats"', 1)

    # 5. Add "📏 Mõõda lõuendil" & "💚 Lemmik" buttons to product cards
    if 'loadCatalogPhotoIntoMeasure' not in html:
        html = html.replace(
            '<div class="pcard-actions">',
            '<div class="pcard-actions">\n          <div style="display:flex;gap:0.4rem;">\n            <button type="button" class="btn sec" style="flex:1;padding:0.45rem 0.6rem;font-size:0.82rem;" onclick="loadCatalogPhotoIntoMeasure(\'${ph.id}\', \'${p.product_id}\')">📏 Mõõda lõuendil</button>\n            <button type="button" class="btn sec" style="padding:0.45rem 0.65rem;font-size:0.82rem;" onclick="toggleShortlist(\'${p.product_id}\')">💚 Lemmik</button>\n          </div>',
            1
        )

    # 6. Include Leaflet JS + unified.js before </body>
    if '/unified.js' not in html:
        html = html.replace(
            '</body>',
            '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>\n<script src="/unified.js"></script>\n</body>',
            1
        )

    html_path.write_text(html, encoding="utf-8")
    veeb_dir = Path("/workspace/puidujaak/veeb")
    if veeb_dir.exists():
        (veeb_dir / "index.html").write_text(html, encoding="utf-8")
        shutil.copyfile("/workspace/puidujaak/veeb_deploy/unified.css", veeb_dir / "unified.css")
        shutil.copyfile("/workspace/puidujaak/veeb_deploy/unified.js", veeb_dir / "unified.js")
    print("Successfully injected unified features (Light/Dark, Basic Swipe, Advanced Map & Wood Measure).")


if __name__ == "__main__":
    inject_unified_features()
