#!/usr/bin/env python3
"""
Puidujaak.ee toodete grupeerimise, EXIF GPS-asukoha lugemise ja territooriumile pääsemise
tingimuste skript (64 tootegruppi PUIDUJAK-001..PUIDUJAK-064, 170 fotot ID001..ID170).
"""

import csv
import json
import math
from pathlib import Path
from typing import Any, Optional
from PIL import Image, ExifTags

# Territooriumile pääsemise ja järele tulemise tüübid
ACCESS_TYPES = {
    "dropoff_24_7": {
        "code": "dropoff_24_7",
        "badge": "🟢 24/7 Dropoff-punkt (prügimaja tüüpi)",
        "short_label": "24/7 Dropoff-punkt (nagu prügimaja)",
        "conditions": (
            "Avatud 24/7 iseteeninduslik kogumispunkt (nagu prügimaja) — tule järele endale "
            "sobival ajal ööpäevaringselt. Kui punkt on koodlukuga, saad uksekoodi ja täpse "
            "Google Maps pinni kohe pärast huviteadet."
        ),
    },
    "suletud_territoorium": {
        "code": "suletud_territoorium",
        "badge": "🔒 Suletud territoorium (kokkuleppel)",
        "short_label": "Suletud territoorium (väravaga ala, kokkuleppel)",
        "conditions": (
            "Asub suletud tootmis- või laoterritooriumil (lukustatud värav / tõkkepuu). "
            "Järele tulemine eelneval kokkuleppel (nt E–R 08:00–17:00 või kokkuleppel), "
            "väravas helistada kontaktisikule; ligipääs kaubiku või järelhaagisega."
        ),
    },
    "avatud_plats": {
        "code": "avatud_plats",
        "badge": "🟡 Avatud plats (helista ette)",
        "short_label": "Avatud laoplats (helista ette)",
        "conditions": (
            "Ligipääs kaubiku või haagisega otse teelt/platsilt ilma lukustatud väravata; "
            "enne pealevõttu anna tulekust telefonitsi teada."
        ),
    },
}


# Puidujaak OÜ peamised lao-, dropoff- ja väljastuspunktid
PUIDUJAAK_LOCATIONS = [
    {
        "id": "saue_garaaz_4",
        "name": "Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue)",
        "address": "Nurmesalu tn 1 / Nurmesalu tee 1, Garaažiboks nr 4, Saue, Harjumaa",
        "lat": 59.318800,
        "lng": 24.561200,
        "google_maps_pin": "https://www.google.com/maps?q=59.318800,24.561200",
        "access_type": "dropoff_24_7",
        "badge": "🟢 24/7 Dropoff & Pickup – Saue garaažiboks nr 4",
        "notes": "Puidujaak OÜ Saue garaažiboks nr 4 (Nurmesalu tn 1 / Nurmesalu tee 1, Tule põik & Sooja tn piirkond, Saue). 24/7 koodlukuga iseteeninduslik pealevõtu- ja äraandmispunkt.",
    },
    {
        "id": "peetri_dropoff_1",
        "name": "24/7 Dropoff-punkt #1 – Peetri / Ülemiste",
        "address": "Peetri alevik, Rae vald, Harjumaa",
        "lat": 59.392400,
        "lng": 24.805800,
        "google_maps_pin": "https://www.google.com/maps?q=59.392400,24.805800",
        "access_type": "dropoff_24_7",
        "badge": "🟢 24/7 Dropoff-punkt #1 (Peetri)",
        "notes": "Iseteeninduslik 24/7 kogumis- ja väljastuspunkt väiksemale puidujäägile ja plaatmaterjalile.",
    },
    {
        "id": "laagri_nomme_dropoff_2",
        "name": "24/7 Dropoff-punkt #2 – Laagri / Nõmme (Männiku tee 100)",
        "address": "Männiku tee 100 / Laagri, Tallinn",
        "lat": 59.352200,
        "lng": 24.619400,
        "google_maps_pin": "https://www.google.com/maps?q=59.352200,24.619400",
        "access_type": "dropoff_24_7",
        "badge": "🟢 24/7 Dropoff-punkt #2 (Laagri / Nõmme)",
        "notes": "24/7 prügimaja tüüpi dropoff-punkt + SmartPosti Männiku Rimi pakiautomaadi sõlm.",
    },
    {
        "id": "kalesi_saeveski",
        "name": "Kalesi / Raasiku saeveski & laoplats (Laimet 100)",
        "address": "Kalesi küla, Raasiku vald, Harjumaa",
        "lat": 59.385200,
        "lng": 24.764500,
        "google_maps_pin": "https://www.google.com/maps?q=59.385200,24.764500",
        "access_type": "suletud_territoorium",
        "badge": "🔒 Suletud territoorium (Kalesi saeveski)",
        "notes": "Suuremõõtmelised lauavirnad, 40 m³ saepuru konteiner, koorekonteiner ja püstkastid. Ligipääs kaubiku, haagise või multiliftiga kokkuleppel.",
    },
    {
        "id": "harku_toostushoov",
        "name": "Tallinn / Harjumaa tööstusterritoorium (kaablitrumlid & alused)",
        "address": "Harku / Mustamäe tööstuspiirkond, Harjumaa",
        "lat": 59.398600,
        "lng": 24.659300,
        "google_maps_pin": "https://www.google.com/maps?q=59.398600,24.659300",
        "access_type": "suletud_territoorium",
        "badge": "🔒 Suletud territoorium (tööstushoov)",
        "notes": "Kaablitrumlid (~170 cm), ümarpalgid (~255 cm), raamide ja aluste virnad. Sissepääs väravast telefonikõnega.",
    },
    {
        "id": "kostivere_avatud_plats",
        "name": "Avatud laoplats – Harjumaa / Kostivere",
        "address": "Harjumaa (ligipääs otse teelt haagisega)",
        "lat": 59.345800,
        "lng": 24.581200,
        "google_maps_pin": "https://www.google.com/maps?q=59.345800,24.581200",
        "access_type": "avatud_plats",
        "badge": "🟡 Avatud laoplats (helista ette)",
        "notes": "Palgid, kännud ja suured pinnapuidu koondhunnikud. Ligipääs haagise või kraanaautoga otse teelt.",
    },
]

UNIQUE_CATEGORIES = {"erikuju", "tuveoonsus", "oksaauk", "oksakrae", "ketas", "koor"}
STANDARD_CATEGORIES = {"laud", "klots", "palk", "alus", "plaat", "trummel"}

BUY_NOW_OVERRIDES = {
    20: 29.00, 21: 24.90, 22: 22.00, 23: 26.00, 24: 29.90,
    25: 34.00, 26: 24.00, 27: 32.00, 28: 21.00, 29: 39.00,
    30: 28.00, 31: 22.00, 32: 27.00, 33: 35.00, 34: 26.00,
    35: 19.90, 36: 23.00, 37: 25.00, 38: 34.90,
    50: 45.00, 51: 18.00, 52: 9.00, 53: 29.00, 54: 24.00,
    55: 34.00, 56: 27.90, 57: 12.00, 58: 39.00, 59: 19.00,
    60: 120.00, 61: 49.00, 62: 65.00, 63: 38.00, 64: 45.00,
    65: 55.00, 66: 59.00, 67: 149.00,
}


def get_product_pricing(prod_idx: int, category: str) -> dict[str, Any]:
    """
    Arvutab toote oksjoni alghinna (7,00 € unikaalne/erikujuline vs 2,00 € tava),
    Osta kohe hinna ning 60-päevase oksjoni parameetrid.
    """
    is_unique = category in UNIQUE_CATEGORIES
    alghind = 7.00 if is_unique else 2.00
    if prod_idx in BUY_NOW_OVERRIDES:
        osta_kohe = BUY_NOW_OVERRIDES[prod_idx]
    elif is_unique:
        osta_kohe = round(21.90 + (prod_idx % 5) * 3.00, 2)
    else:
        osta_kohe = round(9.90 + (prod_idx % 5) * 2.50, 2)
    return {
        "alghind_eur": alghind,
        "on_unikaalne": is_unique,
        "osta_kohe_eur": osta_kohe,
        "oksjon_kestus_paeva": 60,
        "pikenev_lopp_min": 5,
        "tasuta_peale_60p": True,
    }

# Visuaalselt ja kategooria järgi kontrollitud 64 tootegruppi (ID001..ID170 -> PUIDUJAK-001..064)
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
    # 15 UUT TOODET (24.10.2026, PUIDUJAK-050 kuni PUIDUJAK-064):
    (126, 129, "trummel", "Suur tööstuslik puidust kaablitrummel (Ø ~170 cm, laius ~105 cm) + pikk pruss (~195 cm)", "50 € kupüür fotol (140×77 mm)", "high"),
    (130, 132, "palk", "Ilmastikukindel ümarpalk / post betoonposti najal (pikkus ~255 cm, Ø ~16 cm)", "Eesti sall fotol (160×25 cm, 1 triip = 10 cm)", "high"),
    (133, 134, "palk", "Samblase otsaga vana pruss / aiapost maas (pikkus ~100 cm, ristlõige ~12×12 cm)", "Eesti sall fotol (10 triipu = 100 cm)", "high"),
    (135, 136, "alus", "Puidust raamide / restkastide ja pukkide virn tellisseina ääres (~120×100 cm, H ~155 cm)", "Eesti sall fotol (7 triipu = 70 cm)", "high"),
    (137, 139, "alus", "Puitaluste virn (3–4 tk, ~120×80 / 120×100 cm) ja männipalgijupid (~40–60 cm) vaatide kõrval", "Standardne kaubaalus 120 cm", "high"),
    (140, 143, "oksakrae", "Suure oksakohaga / harukohaga lehtpuupakk (~45×40 cm, ovaalne oksalõige ~25×18 cm)", "50 € kupüür fotol (140×77 mm)", "high"),
    (144, 146, "erikuju", "Kumer lainelise puidusüüga tüvelõige / puitpakk (~32 × 18 × 24 cm, mõõtkavaks kokkusurutud 0,5 L pudel)", "Kokkusurutud 0,5 L pudel (~20,5 cm) fotol", "high"),
    (147, 149, "klots", "Korbatanud servaga tihedasüüline lehtpuuklots (25×15×9 cm, sobib klahvikatete/väikedetailide toorikuks)", "Kollane mõõdulint (25 cm) ja 10 € kupüür fotol", "high"),
    (150, 150, "koor", "Metallkonteiner täis männikoort ja pinnapuidu jääke (~180×150 cm, seina kõrgus 9 salli triipu = 90 cm)", "Eesti sall fotol (9 triipu = 90 cm)", "high"),
    (151, 153, "laud", "Õhukesed saetud puitliistud ja spooniribad metallraamil (~3–5 mm paksud, ~8–10 cm laiad, ~200 cm pikad, mõõtkavaks 160 cm sall)", "Eesti sall fotol (160×25 cm, triip 10 cm)", "high"),
    (154, 159, "erikuju", "40 m³ multilift-konteiner kuiva okaspuu saepuruga (puhas saepuru otse aspiratsioonist, sobib allapanuks, multšiks või briketiks)", "Eesti sall fotol (160×25 cm) ja 40 m³ konteiner", "high"),
    (160, 161, "laud", "Pikad saetud puitliistud ja prussid varjualuses (~5×5 cm ja ~5×10 cm, pikkus ~300 cm, mõõtkavaks 160 cm Eesti sall)", "Eesti sall fotol (160×25 cm, triip 10 cm)", "high"),
    (162, 166, "laud", "Servatud okaspuulaudade virn Laimet 100 saeraami juures (8 kihti, virna kõrgus 4 salli triipu = 40 cm, laua paksus ~2,8 cm, laius ~10–15 cm, pikkus ~300 cm)", "Eesti sall fotol (4 triipu = 40 cm)", "high"),
    (167, 169, "laud", "Servamata okaspuu pinnalaudade virn koorega (~270 cm pikad, virna laius ~120 cm, mõõtkavaks 160 cm Eesti sall)", "Eesti sall fotol (160×25 cm, triip 10 cm)", "high"),
    (170, 170, "klots", "Suur kütteklotside ja saetud puidujääkide kuhi (~15–25 cm klotsid, kuhja laius ~280 cm, mõõtkavaks 160 cm Eesti sall)", "Eesti sall fotol (160×25 cm, triip 10 cm)", "high"),
    (171, 174, "alus", "Kõrged puidust transpordiraamid / püstkastid aluspõhjal (~8–10 tk reas, kõrgus ~195 cm, põhi ~120×90 cm, keskmine põikpuu 10 salli triipu = 100 cm kõrgusel)", "Eesti sall fotol (10 triipu = 100 cm)", "high"),
    (176, 179, "klots", "Metallkonteiner (~2,5 m³, H 110 cm) täis saetud puiduklotse (20–25 × 10 × 4,5 cm) ja pinnalaudu", "Eesti sall fotol (1 triip = 10 cm)", "high"),
    (180, 185, "laud", "Suur pinnapuidu, pindade ja küttepuidu koondhunnik (6 vaadet igast küljest: kõrgus ~240–260 cm, eesmine laotud virn ~110 cm, pindade pikkus ~300–450 cm, kogumaht ~25–35 rm)", "Eesti sall fotol (160×25 cm, triip 10 cm)", "high"),
]

# Lisafotod samale tootele (ID175 kuulub PUIDUJAK-058 koorekonteineri juurde koos ID150-ga)
EXTRA_SEQS_BY_PROD_IDX = {58: [175]}

# Vaikimisi teadaolevad mõõdud uutele toodetele (ID126..ID170)
DEFAULT_DIMENSIONS_BY_SEQ = {
    126: "170", 127: "170", 128: "170", 129: "170",
    130: "255", 131: "255", 132: "255",
    133: "100", 134: "100",
    135: "120", 136: "120",
    137: "120", 138: "120", 139: "120",
    140: "45", 141: "45", 142: "45", 143: "45",
    144: "32", 145: "32", 146: "32",
    147: "25", 148: "25", 149: "25",
    150: "150",
    151: "200", 152: "200", 153: "200",
    154: "600", 155: "600", 156: "600", 157: "600", 158: "600", 159: "600",
    160: "300", 161: "300",
    162: "300", 163: "300", 164: "300", 165: "300", 166: "300",
    167: "270", 168: "270", 169: "270",
    170: "20",
    171: "195", 172: "195", 173: "195", 174: "195",
    175: "150",
    176: "22", 177: "22", 178: "22", 179: "22",
    180: "300", 181: "300", 182: "300", 183: "300", 184: "300", 185: "300",
}

NEW_LOCAL_PHOTOS = [
    {"id": "local_ID126", "name": "PXL_20261024_152013000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID126.webp", "modified_time": "2026-10-24T12:20:13.566Z"},
    {"id": "local_ID127", "name": "PXL_20261024_152030000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID127.webp", "modified_time": "2026-10-24T12:20:30.781Z"},
    {"id": "local_ID128", "name": "PXL_20261024_152034000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID128.webp", "modified_time": "2026-10-24T12:20:34.656Z"},
    {"id": "local_ID129", "name": "PXL_20261024_152124000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID129.webp", "modified_time": "2026-10-24T12:21:24.035Z"},
    {"id": "local_ID130", "name": "PXL_20261024_152811000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID130.webp", "modified_time": "2026-10-24T12:28:11.000Z"},
    {"id": "local_ID131", "name": "PXL_20261024_152814000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID131.webp", "modified_time": "2026-10-24T12:28:14.000Z"},
    {"id": "local_ID132", "name": "PXL_20261024_152838000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID132.webp", "modified_time": "2026-10-24T12:28:38.000Z"},
    {"id": "local_ID133", "name": "PXL_20261024_152952000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID133.webp", "modified_time": "2026-10-24T12:29:52.000Z"},
    {"id": "local_ID134", "name": "PXL_20261024_153008000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID134.webp", "modified_time": "2026-10-24T12:30:08.000Z"},
    {"id": "local_ID135", "name": "PXL_20261024_153039000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID135.webp", "modified_time": "2026-10-24T12:30:39.000Z"},
    {"id": "local_ID136", "name": "PXL_20261024_153050000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID136.webp", "modified_time": "2026-10-24T12:30:50.000Z"},
    {"id": "local_ID137", "name": "PXL_20261024_153152000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID137.webp", "modified_time": "2026-10-24T12:31:52.000Z"},
    {"id": "local_ID138", "name": "PXL_20261024_153229000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID138.webp", "modified_time": "2026-10-24T12:32:29.000Z"},
    {"id": "local_ID139", "name": "PXL_20261024_153234000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID139.webp", "modified_time": "2026-10-24T12:32:34.000Z"},
    {"id": "local_ID140", "name": "PXL_20261024_154734000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID140.webp", "modified_time": "2026-10-24T12:47:34.000Z"},
    {"id": "local_ID141", "name": "PXL_20261024_154751000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID141.webp", "modified_time": "2026-10-24T12:47:51.000Z"},
    {"id": "local_ID142", "name": "PXL_20261024_154828000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID142.webp", "modified_time": "2026-10-24T12:48:28.000Z"},
    {"id": "local_ID143", "name": "PXL_20261024_154835000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID143.webp", "modified_time": "2026-10-24T12:48:35.000Z"},
    {"id": "local_ID144", "name": "PXL_20261024_154929000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID144.webp", "modified_time": "2026-10-24T12:49:29.000Z"},
    {"id": "local_ID145", "name": "PXL_20261024_154943000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID145.webp", "modified_time": "2026-10-24T12:49:43.000Z"},
    {"id": "local_ID146", "name": "PXL_20261024_154948000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID146.webp", "modified_time": "2026-10-24T12:49:48.000Z"},
    {"id": "local_ID147", "name": "PXL_20261024_154606000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID147.webp", "modified_time": "2026-10-24T12:46:06.000Z"},
    {"id": "local_ID148", "name": "PXL_20261024_154611000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID148.webp", "modified_time": "2026-10-24T12:46:11.000Z"},
    {"id": "local_ID149", "name": "PXL_20261024_154612000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID149.webp", "modified_time": "2026-10-24T12:46:12.000Z"},
    {"id": "local_ID150", "name": "PXL_20261024_160707000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID150.webp", "modified_time": "2026-10-24T13:07:07.000Z"},
    {"id": "local_ID151", "name": "PXL_20261024_160923000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID151.webp", "modified_time": "2026-10-24T13:09:23.000Z"},
    {"id": "local_ID152", "name": "PXL_20261024_160932000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID152.webp", "modified_time": "2026-10-24T13:09:32.000Z"},
    {"id": "local_ID153", "name": "PXL_20261024_160935000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID153.webp", "modified_time": "2026-10-24T13:09:35.000Z"},
    {"id": "local_ID154", "name": "PXL_20261024_161039000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID154.webp", "modified_time": "2026-10-24T13:10:39.000Z"},
    {"id": "local_ID155", "name": "PXL_20261024_161052000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID155.webp", "modified_time": "2026-10-24T13:10:52.000Z"},
    {"id": "local_ID156", "name": "PXL_20261024_161057000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID156.webp", "modified_time": "2026-10-24T13:10:57.000Z"},
    {"id": "local_ID157", "name": "PXL_20261024_161104000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID157.webp", "modified_time": "2026-10-24T13:11:04.000Z"},
    {"id": "local_ID158", "name": "PXL_20261024_161116000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID158.webp", "modified_time": "2026-10-24T13:11:16.000Z"},
    {"id": "local_ID159", "name": "PXL_20261024_161118000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID159.webp", "modified_time": "2026-10-24T13:11:18.000Z"},
    {"id": "local_ID160", "name": "PXL_20261024_161438000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID160.webp", "modified_time": "2026-10-24T13:14:38.000Z"},
    {"id": "local_ID161", "name": "PXL_20261024_161452000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID161.webp", "modified_time": "2026-10-24T13:14:52.000Z"},
    {"id": "local_ID162", "name": "PXL_20261024_161740000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID162.webp", "modified_time": "2026-10-24T13:17:40.000Z"},
    {"id": "local_ID163", "name": "PXL_20261024_161744000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID163.webp", "modified_time": "2026-10-24T13:17:44.000Z"},
    {"id": "local_ID164", "name": "PXL_20261024_161828000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID164.webp", "modified_time": "2026-10-24T13:18:28.000Z"},
    {"id": "local_ID165", "name": "PXL_20261024_161840000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID165.webp", "modified_time": "2026-10-24T13:18:40.000Z"},
    {"id": "local_ID166", "name": "PXL_20261024_161904000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID166.webp", "modified_time": "2026-10-24T13:19:04.000Z"},
    {"id": "local_ID167", "name": "PXL_20261024_161935000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID167.webp", "modified_time": "2026-10-24T13:19:35.000Z"},
    {"id": "local_ID168", "name": "PXL_20261024_161957000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID168.webp", "modified_time": "2026-10-24T13:19:57.000Z"},
    {"id": "local_ID169", "name": "PXL_20261024_161959000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID169.webp", "modified_time": "2026-10-24T13:19:59.000Z"},
    {"id": "local_ID170", "name": "PXL_20261024_162113000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID170.webp", "modified_time": "2026-10-24T13:21:13.000Z"},
    {"id": "local_ID171", "name": "PXL_20261024_162712000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID171.webp", "modified_time": "2026-10-24T13:27:12.000Z"},
    {"id": "local_ID172", "name": "PXL_20261024_162717000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID172.webp", "modified_time": "2026-10-24T13:27:17.000Z"},
    {"id": "local_ID173", "name": "PXL_20261024_162808000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID173.webp", "modified_time": "2026-10-24T13:28:08.000Z"},
    {"id": "local_ID174", "name": "PXL_20261024_162822000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID174.webp", "modified_time": "2026-10-24T13:28:22.000Z"},
    {"id": "local_ID175", "name": "PXL_20261024_160644000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID175.webp", "modified_time": "2026-10-24T13:06:44.000Z"},
    {"id": "local_ID176", "name": "PXL_20261024_160429000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID176.webp", "modified_time": "2026-10-24T13:04:29.000Z"},
    {"id": "local_ID177", "name": "PXL_20261024_160436000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID177.webp", "modified_time": "2026-10-24T13:04:36.000Z"},
    {"id": "local_ID178", "name": "PXL_20261024_160500000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID178.webp", "modified_time": "2026-10-24T13:05:00.000Z"},
    {"id": "local_ID179", "name": "PXL_20261024_160550000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID179.webp", "modified_time": "2026-10-24T13:05:50.000Z"},
    {"id": "local_ID180", "name": "PXL_20261024_155451000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID180.webp", "modified_time": "2026-10-24T12:54:51.000Z"},
    {"id": "local_ID181", "name": "PXL_20261024_155454000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID181.webp", "modified_time": "2026-10-24T12:54:54.000Z"},
    {"id": "local_ID182", "name": "PXL_20261024_155508000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID182.webp", "modified_time": "2026-10-24T12:55:08.000Z"},
    {"id": "local_ID183", "name": "PXL_20261024_155552000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID183.webp", "modified_time": "2026-10-24T12:55:52.000Z"},
    {"id": "local_ID184", "name": "PXL_20261024_155646000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID184.webp", "modified_time": "2026-10-24T12:56:46.000Z"},
    {"id": "local_ID185", "name": "PXL_20261024_155914000.jpg", "web_view_link": "https://puidujaak.vercel.app/photos/ID185.webp", "modified_time": "2026-10-24T12:59:14.000Z"},
]


def _rational_to_float(val: Any) -> float:
    if isinstance(val, tuple) and len(val) == 2:
        num, den = val
        return float(num) / float(den) if den else 0.0
    return float(val)


def dms_to_decimal(dms_tuple: Any, ref: str) -> Optional[float]:
    """Teisendab EXIF DMS (kraadid, minutid, sekundid) kümnendkraadideks."""
    try:
        if not dms_tuple or len(dms_tuple) < 3:
            return None
        deg = _rational_to_float(dms_tuple[0])
        minutes = _rational_to_float(dms_tuple[1])
        seconds = _rational_to_float(dms_tuple[2])
        if math.isnan(deg) or math.isnan(minutes) or math.isnan(seconds):
            return None
        dec = deg + (minutes / 60.0) + (seconds / 3600.0)
        ref_clean = str(ref or "N").strip().upper()
        if ref_clean in ("S", "W", "-"):
            dec = -abs(dec)
        return round(dec, 6)
    except Exception:
        return None


def build_google_maps_pin_url(lat: float, lng: float) -> str:
    """Genereerib Google Maps Pin URL-i antud koordinaatidele."""
    return f"https://www.google.com/maps?q={lat:.6f},{lng:.6f}"


def extract_exif_gps(image_path: Path) -> dict[str, Any]:
    """
    Loeb pildifailist EXIF GPS-koordinaadid.
    Kui failis on GPSLatitude (tag 2) ja GPSLongitude (tag 4), tagastab täpsed koordinaadid
    ja Google Maps Pin URL-i. Kui Google Pixel kaameras oli „Salvesta asukoht“ väljas
    (GPSInfo IFD eksisteerib, kuid sisaldab vaid GPSVersionID=0.0.0.0 / GPSImgDirection=nan),
    tagastab `has_exif_gps=False` ja selgitava diagnostika.
    """
    result: dict[str, Any] = {
        "has_exif_gps": False,
        "lat": None,
        "lng": None,
        "google_maps_pin": "",
        "camera_model": "",
        "datetime_original": "",
        "gps_status": "no_exif",
    }
    if not image_path or not image_path.exists():
        return result
    try:
        with Image.open(image_path) as im:
            exif = im.getexif()
            if not exif:
                return result
            make = str(exif.get(271, "")).strip()
            model = str(exif.get(272, "")).strip()
            result["camera_model"] = f"{make} {model}".strip()
            result["datetime_original"] = str(exif.get(306, "")).strip()
            try:
                exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                if exif_ifd and 36867 in exif_ifd:
                    result["datetime_original"] = str(exif_ifd[36867]).strip()
            except Exception:
                pass

            gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
            if not gps_ifd:
                result["gps_status"] = "no_gps_ifd"
                return result

            lat_ref = gps_ifd.get(1, "N")
            lat_dms = gps_ifd.get(2)
            lng_ref = gps_ifd.get(3, "E")
            lng_dms = gps_ifd.get(4)

            if lat_dms and lng_dms:
                lat = dms_to_decimal(lat_dms, lat_ref)
                lng = dms_to_decimal(lng_dms, lng_ref)
                if lat is not None and lng is not None:
                    result["has_exif_gps"] = True
                    result["lat"] = lat
                    result["lng"] = lng
                    result["google_maps_pin"] = build_google_maps_pin_url(lat, lng)
                    result["gps_status"] = "exif_gps_ok"
                    return result

            result["gps_status"] = "pixel_gps_disabled_stub"
            return result
    except Exception:
        return result


def get_product_access_and_location(
    prod_idx: int,
    category: str,
    exif_gps: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Määrab tootele (PUIDUJAK-001..064) territooriumile pääsemise tingimused
    (24/7 dropoff-punkt nagu prügimaja vs suletud territoorium kokkuleppel vs avatud plats)
    ning asukoha ja Google Maps Pin lingi.
    Kui fotol on EXIF GPS-koordinaadid, kasutatakse alati otse foto EXIF-koordinaate!
    """
    if prod_idx == 50:
        access_type = "suletud_territoorium"
        default_lat, default_lng = 59.398600, 24.659300
        loc_name = "Tööstusterritoorium – Tallinn / Harjumaa (kaablitrumli hoiuplats)"
        custom_conditions = (
            "🔒 Suletud territoorium (kokkuleppel): asub tööstushoone ja haagise kõrval. "
            "Järele tulemine kokkuleppel (väravast sissepääs telefonikõnega, ligipääs kaubiku "
            "või haagisega); soovi korral võimalik tõsta ka 24/7 dropoff-punkti."
        )
    elif prod_idx == 51:
        access_type = "suletud_territoorium"
        default_lat, default_lng = 59.398800, 24.659700
        loc_name = "Tööstusterritoorium – Tallinn / Harjumaa (betoonposti juures)"
        custom_conditions = (
            "🔒 Suletud territoorium (kokkuleppel): ~255 cm ümarpalk asub tööstushoovil. "
            "Järele tulemine kokkuleppel (väravast sissepääs telefonikõnega, ligipääs haagise "
            "või kaubikuga) või kokkuleppel tõstmine 24/7 dropoff-punkti."
        )
    elif prod_idx == 52:
        access_type = "dropoff_24_7"
        default_lat, default_lng = 59.398400, 24.659100
        loc_name = "24/7 Dropoff-punkt – Tallinn / Harjumaa (prügimaja tüüpi vaba ligipääs)"
        custom_conditions = (
            "🟢 24/7 Dropoff-punkt (prügimaja tüüpi): ~100 cm samblase otsaga pruss on "
            "kergesti sõiduautoga äraviidav — tule järele 24/7 endale sobival ajal."
        )
    elif prod_idx == 53:
        access_type = "suletud_territoorium"
        default_lat, default_lng = 59.398900, 24.660100
        loc_name = "Suletud tööstushoov – tellisseina ja metallvärava ääres"
        custom_conditions = (
            "🔒 Suletud territoorium (kokkuleppel): puidust raamide ja restkastide virn (~120×100 cm, H ~155 cm) "
            "asub tellisseina ja värava ääres. Järele tulemine eelneval kokkuleppel kaubiku või haagisega."
        )
    elif prod_idx == 54:
        access_type = "suletud_territoorium"
        default_lat, default_lng = 59.399100, 24.660500
        loc_name = "Suletud laoplats – poolhaagiste ja vaatide kõrval"
        custom_conditions = (
            "🔒 Suletud territoorium (kokkuleppel): puitaluste virn (3–4 tk) ja männipalgijupid (~40–60 cm) "
            "asuvad laoplatsil poolhaagiste juures. Sissepääs väravast telefonitsi kokkuleppel."
        )
    elif prod_idx in (55, 56, 57):
        access_type = "dropoff_24_7"
        default_lat, default_lng = 59.318800, 24.561200
        loc_name = "Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue) – 24/7 Dropoff-punkt"
        custom_conditions = (
            "🟢 24/7 Dropoff-punkt – Saue garaažiboks nr 4 (Nurmesalu tn 1 / Nurmesalu tee 1, Saue): "
            "käsitöö- ja väärispuidu tükid (oksakohaga pakk ~45 cm, kumer laineline tüvelõige ~32 cm, lehtpuuklots 25 cm) "
            "asuvad Puidujaak OÜ Saue garaažiboksis nr 4 ja on kättesaadavad 24/7 koodlukuga punktist."
        )
    elif 58 <= prod_idx <= 67:
        access_type = "suletud_territoorium"
        default_lat, default_lng = 59.385200, 24.764500
        loc_name = "Saeveski / puidutööstuse territoorium (Laimet 100 saeraam ja laoplats)"
        custom_conditions = (
            "🔒 Suletud territoorium (kokkuleppel): asub saeveski / puidutööstuse laoplatsil "
            "(Laimet 100 saeraami, varjualuste ja multilift-konteinerite juures). Järele tulemine "
            "eelneval kokkuleppel, ligipääs kaubiku, järelhaagise või veoautoga."
        )
    elif 1 <= prod_idx <= 21:
        access_type = "dropoff_24_7"
        default_lat, default_lng = 59.392400, 24.805800
        loc_name = "24/7 Dropoff-punkt #1 – Peetri / Ülemiste (prügimaja tüüpi iseteenindus)"
        custom_conditions = ACCESS_TYPES["dropoff_24_7"]["conditions"]
    elif 22 <= prod_idx <= 30:
        access_type = "dropoff_24_7"
        default_lat, default_lng = 59.318800, 24.561200
        loc_name = "Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue) – 24/7 Dropoff-punkt"
        custom_conditions = (
            "🟢 24/7 Dropoff-punkt – Saue garaažiboks nr 4 (Nurmesalu tn 1 / Nurmesalu tee 1, Saue): "
            + ACCESS_TYPES["dropoff_24_7"]["conditions"]
        )
    elif 31 <= prod_idx <= 38:
        access_type = "dropoff_24_7"
        default_lat, default_lng = 59.352200, 24.619400
        loc_name = "24/7 Dropoff-punkt #2 – Laagri / Nõmme (prügimaja tüüpi 24/7 punkt)"
        custom_conditions = ACCESS_TYPES["dropoff_24_7"]["conditions"]
    elif 39 <= prod_idx <= 41:
        access_type = "avatud_plats"
        default_lat, default_lng = 59.345800, 24.581200
        loc_name = "Avatud laoplats – Harjumaa (ligipääs haagisega otse teelt)"
        custom_conditions = ACCESS_TYPES["avatud_plats"]["conditions"]
    else:
        access_type = "suletud_territoorium"
        default_lat, default_lng = 59.379500, 24.718000
        loc_name = "Suletud laoterritoorium – Tallinn (merekonteineri ja aluste plats)"
        custom_conditions = ACCESS_TYPES["suletud_territoorium"]["conditions"]

    if exif_gps and exif_gps.get("has_exif_gps"):
        lat = float(exif_gps["lat"])
        lng = float(exif_gps["lng"])
        gps_source = "exif_gps"
    else:
        lat = default_lat
        lng = default_lng
        gps_source = "pixel_exif_puudub_vaikimisi_pin"

    meta = ACCESS_TYPES[access_type]
    return {
        "ligipaas_tyyp": access_type,
        "ligipaas_silt": meta["badge"],
        "ligipaas_luhisilt": meta["short_label"],
        "ligipaas_tingimused": custom_conditions,
        "asukoht_nimi": loc_name,
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "google_maps_pin": build_google_maps_pin_url(lat, lng),
        "gps_allikas": gps_source,
    }


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
        existing = list(csv.DictReader(open("/workspace/puidujak_mapping.csv", encoding="utf-8")))
        seen = {}
        uniq = []
        for r in existing:
            name = r["original_name"]
            if name.startswith("PXL_20261024_"):
                continue
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

    # Append the 45 new photos (ID126..ID170) in exact product sequence order
    for nf in NEW_LOCAL_PHOTOS:
        if nf["name"] not in seen:
            seen[nf["name"]] = [nf]
            uniq.append(nf)

    assert len(uniq) == 185, f"Expected 185 unique photos, got {len(uniq)}"

    rows = []
    out = []
    covered_indices = set()

    for prod_idx, (start_seq, end_seq, cat, title, scale_ref, conf) in enumerate(PRODUCT_GROUPS_SPEC, 1):
        pid = f"PUIDUJAK-{prod_idx:03d}"
        seqs = list(range(start_seq, end_seq + 1)) + EXTRA_SEQS_BY_PROD_IDX.get(prod_idx, [])
        group_files = [uniq[s - 1] for s in seqs]
        for seq in seqs:
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

    assert covered_indices == set(range(1, 186)), "Not all 1..185 photos covered!"

    Path("/workspace/groups.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    with open("/workspace/puidujak_mapping.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Successfully generated {len(out)} visually verified product groups across {len(uniq)} unique photos ({len(rows)} total entries).")


if __name__ == "__main__":
    main()
