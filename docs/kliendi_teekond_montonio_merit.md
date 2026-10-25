# Puidujaak OÜ (`puidujaak.ee`) – 0 €/kuus Kliendi Teekond (Montonio + Merit Aktiva stiilis PDF-arve + 2 automaatkirja)

**Kuupäev:** 25. oktoober 2026  
**Referentsmudel:** Trivium OÜ arve nr `2026-00514` (`PDFsharp 1.50.5147` / Merit Aktiva kujundus) + WooCommerce & Montonio (`montonio-for-woocommerce`) 2 järjestikust automaatkirja.

---

## 1. Arhitektuur ja püsikulu võrdlus (0 €/kuus lahendus)

| Komponent | Valmis-pluginate komplekt (WooCommerce + Montonio + Merit Aktiva Pro) | Puidujaak.ee oma 0 €/kuus lahendus (`arve_ja_klienditeekond.py` + `veeb_deploy/index.html`) |
|---|---|---|
| **Veeb ja ostukorv** | WordPress + WooCommerce (~9–13 €/kuus veebimajutuses) | **0 €/kuus** (Vercel + GitHub `reneealuste-commits/puidujaak` + Sanderi `media` server) |
| **Pangalingid & pakiautomaadid** | Montonio Start (`0 €/kuus`, 0,05–0,15 € makse) või Standard (`11 €/kuus`) | **0 €/kuus** (Montonio Start API / MakeCommerce Marketplace 8% agendimudel) |
| **Sinise päisega A4 PDF-arve** | Merit Aktiva API + WooCommerce liides (~15–39 €/kuus peale tasuta mahtu) | **0 €/kuus** (`arve_ja_klienditeekond.py` + kliendipoolne A4 PDF/print mootor täpselt samade `#afddff` koordinaatidega) |
| **Automaatkirjad (#1 ja #2)** | WooCommerce `customer_processing_order` + `customer_invoice` | **0 €/kuus** (`email_1_tellimus_kaes.html` + `email_2_arve_manusega.html` + SMTP/FormSubmit) |
| **Kuu püsikulu kokku** | **0 € – 50 € / kuus** | **0 € / kuus** |

---

## 2. Kliendi 4-sammuline teekond (`puidujaak.ee`)

### Samm 1: Toote ja kättesaamisviisi valik + Montonio pangalink
1. Klient valib kataloogist toote (nt `PUIDUJAK-056` – *Laineline tüvelõige ~32×18×24 cm*, `klots_alla50cm_ID145.jpg`, **27,90 €**).
2. Klient valib kättesaamisviisi:
   - **📦 SmartPosti / Omniva / DPD pakiautomaat (3,50 €):** väiksemad puidutükid (`alla30cm`, `alla50cm`), nt *Tallinna Männiku Rimi, Männiku tee 100*.
   - **🟢 24/7 Dropoff-punkt – Saue garaažiboks nr 4 (Nurmesalu tn 1, Saue, 0,00 €):** ööpäevaringne iseteeninduslik pealelaadimine koodiga + **📍 Google Maps Pin (`59.3188, 24.5612`)**.
   - **🔒 Suletud territoorium (kokkuleppel, 0,00 €):** ligipääs laoplatsile peale tellimuse kinnitust.
   - **🚛 Puidujaak transport (haagis / multilift / kraanaauto):** suuremahulistele konteineritele ja virnadele (`PUIDUJAK-050`..`067`).
3. Klient tasub **„Maksa pangas“** (Montonio pangalink: LHV, Swedbank, SEB, Coop, Luminor). Puidujaak OÜ 8% agendimudelis arvestatakse **8% vahendustasu (2,23 €)** Puidujaak OÜ-le ja **92% (25,67 €)** müüjale.

### Samm 2: Automaatkiri #1 (1 sekund peale makset)
* **Pealkiri:** `Sinu tellimus lehel Puidujaak.ee saadi kätte!`
* **Sisu:**
  - Tervitus (*„Tere, Renee Aluste! Oleme sinu tellimuse kätte saanud ja see on nüüd töötlemisel.“*)
  - Tellimuse kokkuvõte `Tellimus #2026-00514 (25.10.2026)` koos `48×48 px` tootefoto, koguse, vahesumma, Montonio pakiautomaadi / 24/7 Dropoff-punkti rea ja kogusummaga (**31,40 €**).
  - **Kollane infokast (`border: 1px solid #e0c36e`):** täitmise kuupäev, 24/7 väravakoodi info ja otselink **📍 Ava täpne Google Maps Pin**.

### Samm 3: Automaatkiri #2 (2 sekundit peale makset, koos PDF-arvega manuses)
* **Pealkiri:** `Arve 2026-00514 sinu tellimusele #2026-00514`
* **Sisu:** Tellimuse kokkuvõte + teade *„Sinu arve on lisatud selle e-kirja manusesse.“* + manuses `Puidujaak-OU-Arve-nr-2026-00514.pdf`.

### Samm 4: Merit Aktiva stiilis sinise päisega A4 PDF-arve
* Täpsed visuaalsed parameetrid (`Trivium-OU-Arve-nr-2026-00514.pdf` järgi):
  - Helesinine päisekast ja tabelipäis: `RGB(175, 221, 255)` (`#afddff` / `#b8dcff`), raam `RGB(122, 154, 178)` (`#7a9ab2`).
  - Ülal vasakul: `Arve saaja` + kliendi nimi.
  - Ülal paremal: `Arve nr 2026-00514`, `Kuupäev: 25.10.2026`, `Maksetähtpäev: 30.10.2026`, Eesti 7-3-1 `Viitenumber: 107026`, `Viivis: 0.05% päevas`.
  - Müüja plokk: **Puidujaak OÜ**, aadress, `Rg-kood 17104829`.
  - Tabel: `Kirjeldus | Kogus | Ühik | Hind | Summa`.
  - Kokkuvõte: `Ei ole käibemaksukohustuslane` (või 24% KM valik) ja **Arve kokku (EUR) 31,40**.
  - Jalus: `LHV SWIFT LHVBEE22` ja `IBAN EE777700771009845123`.

---

---

## 3. Oksjoni, "Osta kohe" ja 60-päevase taimeri reeglid (`puidujaak.ee`)

Kõigil **67 tootel (`PUIDUJAK-001`..`PUIDUJAK-067`)** kehtib ühtne dünaamiline hinnastuse ja ringmajanduse reeglistik:

1. **Kahetasemeline oksjoni alghind (2,00 € vs. 7,00 €):**
   - **Tavaline puidujääk (`2,00 €`):** Standardkategooriad (`laud`, `klots`, `palk`, `alus`, `plaat`, `trummel`) algavad alghinnaga **2,00 €** (`alghind_eur = 2.00`).
   - **Erikujuline puidujääk / unikaalsed jupid (`7,00 €`):** Unikaalsed ja dekoratiivsed tükid (`erikuju`, `tuveoonsus`, `oksaauk`, `oksakrae`, `ketas`, `koor`) algavad kõrgema alghinnaga **7,00 €** (`alghind_eur = 7.00`, märgisega `✨ Unikaalne / Erikujuline · Alghind 7 €`).
2. **60-päevane oksjoni taimer:** Iga toode saab lisamisel **60-päevase taimeri** (`60 päeva = 5 184 000 sekundit`), mis tiksub reaalajas sekundite täpsusega igal tootekaardil ja modaalaknas.
3. **Pikenev lõpp (5 min):** Kui pakkumine tehakse siis, kui taimeril on jäänud vähem kui **5 minutit (`< 05:00`)**, pikeneb oksjoni lõpuaeg automaatselt **5 minutini (`05:00`)** (*anti-sniping / pikenev lõpp 5 min*).
4. **Osta kohe (`🛒 Osta kohe`):** Igal tootel on fikseeritud **Osta kohe** hind (nt `27,90 €` tootel `PUIDUJAK-056`), millega saab toote kohe ilma oksjoni lõppu ootamata ära osta — avaneb **Montonio + Merit Aktiva stiilis 4-sammuline kassa ja automaatarve**.
5. **Peale 60 päeva on toode TASUTA (`0,00 €`):** Kui 60 päeva jooksul toodet ära ei osteta ega pakkumist ei tehta, muutub toote hind automaatselt **0,00 € (`🎁 TASUTA — 60 päeva täis!`)**, et puit ei jääks laoplatsile mädanema ja leiaks kindlasti taaskasutaja.

---

## 4. Eesti 7-3-1 viitenumbri valem (`arvuta_viitenumber`)

Eesti Pangaliidu viitenumbri kontrolljärk arvutatakse korrutades alusnumbri numbrid paremalt vasakule kaaludega `7, 3, 1, 7, 3, 1...`:
- Näide alusnumbriga `10702`:
  - `2 × 7 = 14`
  - `0 × 3 = 0`
  - `7 × 1 = 7`
  - `0 × 7 = 0`
  - `1 × 3 = 3`
  - Summa = `24` -> järgmine kümnekordne on `30` -> kontrolljärk `30 - 24 = 6` -> **`107026`**.

---

## 5. Genereeritud failid `/workspace/puidujaak/` kaustas

- `/workspace/puidujaak/arve_ja_klienditeekond.py` – PDF-arve, 7-3-1 viitenumbri ja e-kirjade generaator
- `/workspace/puidujaak/Puidujaak-OU-Arve-nr-2026-00514.pdf` (ja koopia `/workspace/puidujaak/veeb_deploy/Puidujaak-OU-Arve-nr-2026-00514.pdf`)
- `/workspace/puidujaak/email_1_tellimus_kaes.html` (ja koopia `veeb_deploy/` kaustas)
- `/workspace/puidujaak/email_2_arve_manusega.html` (ja koopia `veeb_deploy/` kaustas)
