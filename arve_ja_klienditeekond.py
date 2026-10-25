#!/usr/bin/env python3
"""
Puidujaak OÜ (puidujaak.ee) – 0 €/kuus Kliendi Teekond, Montonio makse + pakiautomaadi / 24/7 Dropoff voog,
Eesti 7-3-1 viitenumbri kalkulaator, Merit Aktiva stiilis sinise päisega A4 PDF-arve generaator
ning 2 automaatse e-kirja malli generaator (WooCommerce / Montonio stiilis).

Ei vaja ühtegi tasulist teenust ega välist PDF-teeki (puhtas Pythonis PDF 1.4 vektorgraafika).
"""

import json
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


def arvuta_viitenumber(alusnumber: str) -> str:
    """
    Arvutab Eesti pangaliidu standardi (7-3-1 kaalud paremalt vasakule) järgi
    kehtiva viitenumbri koos kontrolljärguga.
    Näide: '10702' -> '107026' (täpselt nagu arvel 2026-00514).
    """
    digits = "".join(ch for ch in str(alusnumber) if ch.isdigit())
    if not digits:
        digits = "10702"
    weights = [7, 3, 1]
    total = 0
    for idx, ch in enumerate(reversed(digits)):
        total += int(ch) * weights[idx % 3]
    check_digit = (10 - (total % 10)) % 10
    return f"{digits}{check_digit}"


def valideeri_viitenumber(viitenumber: str) -> bool:
    """Kontrollib, kas Eesti 7-3-1 viitenumber on kehtiv."""
    digits = "".join(ch for ch in str(viitenumber) if ch.isdigit())
    if len(digits) < 2:
        return False
    return arvuta_viitenumber(digits[:-1]) == digits


@dataclass
class InvoiceLine:
    description: str
    qty: float = 1.0
    unit: str = "tk"
    unit_price: float = 27.90

    @property
    def line_total(self) -> float:
        return round(self.qty * self.unit_price, 2)


@dataclass
class InvoiceData:
    invoice_no: str = "2026-00514"
    order_no: str = "2026-00514"
    issue_date: str = "25.10.2026"
    due_date: str = "30.10.2026"
    reference_base: str = "10702"
    late_fee: str = "0.05% päevas"
    # Buyer
    buyer_name: str = "Renee Aluste"
    buyer_company: str = ""
    buyer_phone: str = "56980062"
    buyer_email: str = "reneealuste@gmail.com"
    buyer_address: str = ""
    # Seller
    seller_name: str = "Puidujaak OÜ"
    seller_addr_1: str = "Nurmesalu tn 1 (Garaažiboks nr 4, Saue) / Männiku tee 100"
    seller_addr_2: str = "Saue linn, Saue vald / Nõmme, Tallinn"
    seller_addr_3: str = "11216 Harju maakond"
    seller_reg: str = "17104829"
    seller_kmkr: str = ""  # Tühi = "Ei ole käibemaksukohustuslane"
    seller_email: str = "info@puidujaak.ee"
    seller_bank_swift: str = "LHV SWIFT LHVBEE22"
    seller_iban: str = "EE777700771009845123"
    # Product & Delivery
    product_id: str = "PUIDUJAK-056"
    photo_id: str = "ID145"
    short_filename: str = "klots_alla50cm_ID145.jpg"
    payment_method: str = "Maksa pangas (Montonio pangalink – LHV / Swedbank / SEB)"
    delivery_method_title: str = "SmartPosti pakiautomaat"
    delivery_location: str = "Tallinna Männiku Rimi, Männiku tee 100"
    access_type: str = "dropoff_24_7"  # dropoff_24_7 | suletud_territoorium | avatud_plats | pakiautomaat
    access_notice: str = (
        "Tegemist on eeltellimusega / 24/7 Dropoff-punkti tellimusega (Saue garaažiboks nr 4, Nurmesalu tn 1, Saue). "
        "Tellimuse täitmine ja väljastamine algab 3. novembril 2026 "
        "(24/7 ligipääsukood ja Google Maps Pin saadetakse SMS-i ja e-kirjaga)."
    )
    google_maps_pin: str = "https://www.google.com/maps?q=59.3188,24.5612"
    lines: List[InvoiceLine] = field(
        default_factory=lambda: [
            InvoiceLine(
                description='PUIDUJAK-056 – Laineline tüvelõige (~32×18×24 cm, klots_alla50cm_ID145)',
                qty=1,
                unit="tk",
                unit_price=27.90,
            ),
            InvoiceLine(
                description="SmartPosti pakiautomaat – Tallinna Männiku Rimi, Männiku tee 100",
                qty=1,
                unit="",
                unit_price=3.50,
            ),
        ]
    )

    @property
    def reference_number(self) -> str:
        return arvuta_viitenumber(self.reference_base)

    @property
    def subtotal_products(self) -> float:
        if not self.lines:
            return 0.0
        return round(self.lines[0].line_total, 2)

    @property
    def shipping_total(self) -> float:
        if len(self.lines) < 2:
            return 0.0
        return round(sum(l.line_total for l in self.lines[1:]), 2)

    @property
    def total_eur(self) -> float:
        return round(sum(l.line_total for l in self.lines), 2)

    @property
    def marketplace_commission_8pct(self) -> float:
        return round(self.subtotal_products * 0.08, 2)

    @property
    def seller_payout_92pct(self) -> float:
        return round(self.subtotal_products - self.marketplace_commission_8pct, 2)


def _fmt_eur(val: float) -> str:
    return f"{val:.2f}".replace(".", ",")


def _pdf_escape_winansi(text: str) -> bytes:
    """Teisendab teksti CP1252 (WinAnsiEncoding) baitideks ja varjestab PDF sulud."""
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    raw = text.encode("cp1252", errors="replace")
    out = bytearray()
    for b in raw:
        if b in (0x28, 0x29, 0x5C):  # ( ) \
            out.append(0x5C)
            out.append(b)
        elif 32 <= b <= 126:
            out.append(b)
        else:
            out.extend(f"\\{b:03o}".encode("ascii"))
    return bytes(out)


def _approx_text_width(text: str, font_size: float = 9.0, bold: bool = False) -> float:
    """Arvutab ligikaudse teksti laiuse punktides Helvetica / Arial jaoks."""
    factor = 0.54 if bold else 0.50
    w = 0.0
    for ch in text:
        if ch in "ilI.,:;|!1' ":
            w += font_size * 0.27
        elif ch in "mwMW@%":
            w += font_size * 0.78
        elif ch.isupper():
            w += font_size * 0.62
        else:
            w += font_size * factor
    return w


def generate_merit_style_pdf(inv: InvoiceData, output_path: Path) -> Path:
    """
    Genereerib täpse Merit Aktiva (PDFsharp) kujundusega sinise päisega A4 PDF-arve:
    - Helesinised kastid RGB(0.686, 0.867, 1.0) = #afddff ja raam RGB(0.478, 0.604, 0.698) = #7a9ab2
    - Ülal vasakul 'Arve saaja' + kliendi nimi
    - Ülal paremal sinine kast 'Arve nr ...', all Kuupäev, Maksetähtpäev, Viitenumber (7-3-1), Viivis: 0.05% päevas
    - Paremal keskel ettevõtte plokk (Puidujaak OÜ, aadress, Rg-kood)
    - Sinise päisega tabel: Kirjeldus | Kogus | Ühik | Hind | Summa
    - Read + 'Ei ole käibemaksukohustuslane' + 'Arve kokku (EUR)'
    - All jaluses joon + LHV SWIFT LHVBEE22 ja IBAN
    """
    cmds: List[bytes] = []

    def add(line: str):
        cmds.append(line.encode("ascii"))

    def text_left(x: float, y: float, txt: str, size: float = 9.0, bold: bool = False):
        font = "/F1" if bold else "/F0"
        esc = _pdf_escape_winansi(txt)
        cmds.append(f"BT 0 0 0 rg {font} {size:.2f} Tf {x:.2f} {y:.2f} Td (".encode("ascii") + esc + b") Tj ET")

    def text_right(x_right: float, y: float, txt: str, size: float = 9.0, bold: bool = False):
        w = _approx_text_width(txt, size, bold)
        text_left(x_right - w, y, txt, size, bold)

    add("q")
    add("0.25 w 0 J 0 j [] 0 d")

    # 1. Vasakul üleval: Arve saaja
    text_left(52.0, 739.63, "Arve saaja", 9.0, bold=False)
    text_left(52.0, 723.38, inv.buyer_name, 9.0, bold=True)
    y_buyer = 710.0
    if inv.buyer_company:
        text_left(52.0, y_buyer, inv.buyer_company, 8.5, bold=False)
        y_buyer -= 11.5
    if inv.buyer_address:
        text_left(52.0, y_buyer, inv.buyer_address, 8.5, bold=False)
        y_buyer -= 11.5
    if inv.buyer_phone or inv.buyer_email:
        contact_line = " · ".join(x for x in [inv.buyer_phone, inv.buyer_email] if x)
        text_left(52.0, y_buyer, contact_line, 8.2, bold=False)

    # 2. Paremal üleval: helesinine kast "Arve nr 2026-00514"
    add("0.686 0.867 1 rg")
    add("382.596 720.878 182.244 18.224 re f")
    add("0.478 0.604 0.698 RG")
    add("382.596 720.878 182.244 18.224 re S")

    text_left(431.45, 726.48, f"Arve nr {inv.invoice_no}", 9.0, bold=True)

    # Metaandmed sinise kasti all
    meta_rows = [
        ("Kuupäev", inv.issue_date),
        ("Maksetähtpäev", inv.due_date),
        ("Viitenumber", inv.reference_number),
        ("Viivis", inv.late_fee),
    ]
    y_meta = 703.18
    for label, val in meta_rows:
        text_left(385.19, y_meta, label, 9.0, bold=False)
        text_right(562.0, y_meta, val, 9.0, bold=False)
        y_meta -= 12.2563

    # 3. Müüja plokk paremal (Puidujaak OÜ)
    text_right(562.0, 642.44, inv.seller_name, 9.0, bold=True)
    text_right(562.0, 618.14, inv.seller_addr_1, 9.0, bold=False)
    text_right(562.0, 605.88, inv.seller_addr_2, 9.0, bold=False)
    text_right(562.0, 593.63, inv.seller_addr_3, 9.0, bold=False)
    text_right(562.0, 557.39, f"Rg-kood {inv.seller_reg}", 9.0, bold=False)

    # 4. Tabeli päis (helesinine rida x=50..565, y=516.933, h=16.256)
    row_h = 16.2563
    y_top = 516.933
    add("0.686 0.867 1 rg")
    add(f"50 {y_top:.3f} 515 {row_h:.3f} re f")
    add("0.478 0.604 0.698 RG")
    add(f"50 {y_top:.3f} 515 {row_h:.3f} re S")

    text_left(52.0, y_top + 4.64, "Kirjeldus", 9.0, bold=False)
    text_right(362.0, y_top + 4.64, "Kogus", 9.0, bold=False)
    text_left(366.0, y_top + 4.64, "Ühik", 9.0, bold=False)
    text_right(492.0, y_top + 4.64, "Hind", 9.0, bold=False)
    text_right(562.0, y_top + 4.64, "Summa", 9.0, bold=False)

    # 5. Tabeli read
    y_curr = y_top
    for line in inv.lines:
        y_curr -= row_h
        add("0.478 0.604 0.698 RG")
        add(f"50 {y_curr:.3f} 515 {row_h:.3f} re S")
        text_left(52.0, y_curr + 4.64, line.description, 9.0, bold=False)
        qty_str = f"{int(line.qty)}" if float(line.qty).is_integer() else f"{line.qty}"
        text_right(362.0, y_curr + 4.64, qty_str, 9.0, bold=False)
        if line.unit:
            text_left(366.0, y_curr + 4.64, line.unit, 9.0, bold=False)
        text_right(492.0, y_curr + 4.64, _fmt_eur(line.unit_price), 9.0, bold=False)
        text_right(562.0, y_curr + 4.64, _fmt_eur(line.line_total), 9.0, bold=False)

    # 6. Käibemaksu märkus ja kokkuvõte
    y_vat = y_curr - 11.6
    if inv.seller_kmkr:
        vat_amt = round(inv.total_eur * 0.24, 2)
        text_right(562.0, y_vat, f"Käibemaks 24%: {_fmt_eur(vat_amt)} EUR", 9.0, bold=False)
    else:
        text_right(562.0, y_vat, "Ei ole käibemaksukohustuslane", 9.0, bold=False)

    y_line = y_curr - 16.256
    add("0.478 0.604 0.698 RG")
    add(f"50 {y_line:.3f} m 565 {y_line:.3f} l S")

    y_tot = y_line - 11.62
    text_left(454.98, y_tot, "Arve kokku (EUR)", 9.0, bold=True)
    text_right(562.0, y_tot, _fmt_eur(inv.total_eur), 9.0, bold=True)

    # 7. Lisainfo plokk (Puidujaak spetsiifika: 24/7 Dropoff / Google Maps Pin / 8% agendimudel)
    y_info = y_tot - 28.0
    text_left(52.0, y_info, f"Tellimus #{inv.order_no} · Makseviis: {inv.payment_method}", 8.2, bold=False)
    text_left(52.0, y_info - 11.5, f"Kättesaamine: {inv.delivery_method_title} – {inv.delivery_location}", 8.2, bold=False)
    text_left(52.0, y_info - 23.0, f"Google Maps Pin: {inv.google_maps_pin}", 8.0, bold=False)

    # 8. Jaluse joon ja pangarekvisiidid (y=70)
    add("0.478 0.604 0.698 RG")
    add("50 70 m 566.359 70 l S")
    text_right(562.0, 59.12, inv.seller_bank_swift, 8.31, bold=False)
    text_right(562.0, 47.81, f"IBAN {inv.seller_iban}", 8.31, bold=False)

    add("Q")

    stream_raw = b"\n".join(cmds)
    stream_comp = zlib.compress(stream_raw)

    # Ehita standardne PDF 1.4 fail
    objects: List[bytes] = []

    def add_obj(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    # 1: Catalog
    add_obj(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: Pages
    add_obj(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    # 3: Page (A4 595 x 842)
    add_obj(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F0 4 0 R /F1 5 0 R >> >> "
        b"/Contents 6 0 R >>"
    )
    # 4: Font F0 (Helvetica WinAnsiEncoding)
    add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    # 5: Font F1 (Helvetica-Bold WinAnsiEncoding)
    add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    # 6: Content stream
    add_obj(
        f"<< /Filter /FlateDecode /Length {len(stream_comp)} >>\nstream\n".encode("ascii")
        + stream_comp
        + b"\nendstream"
    )
    # 7: Info dict (märgib PDFsharp / Merit Aktiva ühilduva generaatori)
    add_obj(
        b"<< /Title (Puidujaak OU Arve nr "
        + _pdf_escape_winansi(inv.invoice_no)
        + b") /Author (Puidujaak OU) /Creator (Puidujaak Merit-Style PDF Generator 1.0 / PDFsharp compatible) >>"
    )

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for idx, obj_bytes in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj_bytes)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R /Info 7 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(bytes(pdf))
    return output_path


def generate_transactional_email_html(inv: InvoiceData, email_type: str = "order_received") -> str:
    """
    Genereerib täpselt WooCommerce + Montonio + Merit Aktiva stiilis HTML e-kirja:
    - email_type == 'order_received': Kiri #1 ("Sinu tellimus lehel Puidujaak.ee saadi kätte!")
    - email_type == 'invoice_attached': Kiri #2 ("Arve 2026-00514 sinu tellimusele #2026-00514" koos PDF manuse plokiga)
    """
    is_invoice = email_type == "invoice_attached"
    subject = (
        f"Arve {inv.invoice_no} sinu tellimusele #{inv.order_no}"
        if is_invoice
        else "Sinu tellimus lehel Puidujaak.ee saadi kätte!"
    )
    heading = f"Arve nr {inv.invoice_no}" if is_invoice else "Täname tellimuse eest!"
    intro_text = (
        f"Tere, {inv.buyer_name}! Saadame sinu tellimuse #{inv.order_no} arve nr {inv.invoice_no} (lisatud PDF-failina manusesse). Allpool on tellimuse kokkuvõte:"
        if is_invoice
        else f"Tere, {inv.buyer_name}! Oleme sinu tellimuse kätte saanud ja see on nüüd töötlemisel. Allpool on meeldetuletus selle kohta, mida sa tellisid:"
    )

    prod_line = inv.lines[0]
    attachment_banner = ""
    if is_invoice:
        attachment_banner = f"""
        <div style="margin-top:18px;padding:14px 16px;background:#1e2631;border:1px solid #3b82f6;border-radius:10px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">📄</span>
            <div>
              <div style="font-weight:700;color:#ffffff;font-size:14px;">Puidujaak-OU-Arve-nr-{inv.invoice_no}.pdf</div>
              <div style="font-size:12px;color:#94a3b8;">Merit Aktiva stiilis standardarve · Viitenumber: {inv.reference_number} · Kokku: {_fmt_eur(inv.total_eur)} €</div>
            </div>
          </div>
          <a href="/Puidujaak-OU-Arve-nr-2026-00514.pdf" download="Puidujaak-OU-Arve-nr-{inv.invoice_no}.pdf"
             style="background:#2563eb;color:#ffffff;text-decoration:none;padding:8px 14px;border-radius:7px;font-weight:600;font-size:13px;">
            ⬇ Laadi PDF-arve alla
          </a>
        </div>
        """

    return f"""<!doctype html>
<html lang="et">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{subject}</title>
</head>
<body style="margin:0;padding:24px 12px;background:#121212;color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.5;">
  <div style="max-width:600px;margin:0 auto;background:#18181b;border:1px solid #27272a;border-radius:14px;overflow:hidden;box-shadow:0 12px 32px rgba(0,0,0,0.45);">
    <!-- E-kirja päis -->
    <div style="padding:18px 24px;border-bottom:1px solid #27272a;background:#1f1f23;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
      <div style="font-size:13px;color:#a1a1aa;">
        <b style="color:#ffffff;">Saatja:</b> Puidujaak OÜ &lt;tellimused@puidujaak.ee&gt;<br>
        <b style="color:#ffffff;">Pealkiri:</b> {subject}
      </div>
      <span style="background:#27272a;color:#e4e4e7;font-size:11px;padding:4px 9px;border-radius:99px;font-family:monospace;">
        {"Kiri #2 (09:04:05)" if is_invoice else "Kiri #1 (09:04:03)"}
      </span>
    </div>

    <div style="padding:28px 24px;">
      <!-- Logo rida -->
      <div style="text-align:center;margin-bottom:22px;">
        <div style="display:inline-block;padding:8px 18px;border:1px solid #3f3f46;border-radius:8px;letter-spacing:0.12em;font-weight:800;font-size:16px;color:#f8fafc;">
          🪵 PUIDUJAAK OÜ
        </div>
      </div>

      <h1 style="margin:0 0 14px;font-size:24px;font-weight:800;color:#ffffff;">{heading}</h1>
      <p style="margin:0 0 18px;font-size:15px;color:#d4d4d8;">{intro_text}</p>

      <h2 style="margin:24px 0 6px;font-size:18px;font-weight:700;color:#ffffff;">Tellimuse kokkuvõte</h2>
      <div style="font-size:13px;color:#a1a1aa;margin-bottom:14px;">
        Tellimus #{inv.order_no} ({inv.issue_date})
      </div>

      <!-- Tootetabel (48x48 pisipildiga) -->
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="border-bottom:1px solid #2e2e34;color:#a1a1aa;text-align:left;">
            <th style="padding:10px 8px 10px 0;">Toode</th>
            <th style="padding:10px 8px;text-align:center;">Kogus</th>
            <th style="padding:10px 0 10px 8px;text-align:right;">Hind</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid #2e2e34;">
            <td style="padding:14px 8px 14px 0;">
              <div style="display:flex;align-items:center;gap:12px;">
                <img src="/photos/{inv.photo_id}.webp" alt="{inv.product_id}" width="48" height="48"
                     style="width:48px;height:48px;object-fit:cover;border-radius:6px;border:1px solid #3f3f46;flex-shrink:0;">
                <div>
                  <div style="font-weight:600;color:#ffffff;">{prod_line.description}</div>
                  <div style="font-size:12px;color:#9ca3af;font-family:monospace;">{inv.short_filename}</div>
                </div>
              </div>
            </td>
            <td style="padding:14px 8px;text-align:center;color:#e4e4e7;">×{int(prod_line.qty)}</td>
            <td style="padding:14px 0 14px 8px;text-align:right;font-weight:600;color:#ffffff;white-space:nowrap;">{_fmt_eur(prod_line.line_total)} €</td>
          </tr>
        </tbody>
        <tfoot>
          <tr style="border-bottom:1px solid #27272a;">
            <td colspan="2" style="padding:10px 8px 10px 0;color:#a1a1aa;">Vahesumma:</td>
            <td style="padding:10px 0 10px 8px;text-align:right;color:#e4e4e7;">{_fmt_eur(inv.subtotal_products)} €</td>
          </tr>
          <tr style="border-bottom:1px solid #27272a;">
            <td colspan="2" style="padding:10px 8px 10px 0;color:#a1a1aa;">Transport:</td>
            <td style="padding:10px 0 10px 8px;text-align:right;color:#e4e4e7;">
              {inv.delivery_method_title}, <b>{_fmt_eur(inv.shipping_total)} €</b><br>
              <small class="montonio-shipping-method-info" style="color:#60a5fa;">- {inv.delivery_location}</small>
            </td>
          </tr>
          <tr style="border-bottom:1px solid #27272a;">
            <td colspan="2" style="padding:12px 8px 12px 0;font-weight:700;color:#ffffff;font-size:16px;">Kokku:</td>
            <td style="padding:12px 0 12px 8px;text-align:right;font-weight:800;color:#ffffff;font-size:17px;">{_fmt_eur(inv.total_eur)} €</td>
          </tr>
          <tr>
            <td colspan="2" style="padding:10px 8px 10px 0;color:#a1a1aa;">Makseviis:</td>
            <td style="padding:10px 0 10px 8px;text-align:right;color:#e4e4e7;">Maksa pangas</td>
          </tr>
        </tfoot>
      </table>

      <!-- Kollane eeltellimuse / 24/7 ligipääsu teavituskast (#fff8df / #e0c36e) -->
      <div style="margin:20px 0;padding:14px 16px;background:#262110;border:1px solid #e0c36e;border-radius:8px;color:#fef08a;font-size:14px;">
        <b style="color:#fde047;">Oluline tarne- ja ligipääsuinfo:</b> {inv.access_notice}
        <div style="margin-top:6px;">
          <a href="{inv.google_maps_pin}" target="_blank" rel="noopener" style="color:#60a5fa;text-decoration:underline;font-weight:600;">
            📍 Ava täpne Google Maps Pin
          </a>
        </div>
      </div>

      <!-- Arveaadress -->
      <div style="margin-top:22px;padding-top:16px;border-top:1px solid #27272a;">
        <h3 style="margin:0 0 8px;font-size:15px;color:#ffffff;">Arveaadress</h3>
        <div style="font-size:14px;color:#d4d4d8;line-height:1.6;">
          {inv.buyer_name}<br>
          <a href="tel:{inv.buyer_phone}" style="color:#60a5fa;text-decoration:none;">{inv.buyer_phone}</a><br>
          <a href="mailto:{inv.buyer_email}" style="color:#60a5fa;text-decoration:none;">{inv.buyer_email}</a>
        </div>
      </div>

      <p style="margin:18px 0 0;font-size:14px;color:#e4e4e7;">
        Sinu arve on lisatud selle e-kirja manusesse.
      </p>

      {attachment_banner}

      <div style="margin-top:24px;padding-top:14px;border-top:1px solid #27272a;font-size:12px;color:#71717a;text-align:center;">
        {inv.seller_name} · {inv.seller_addr_1}, {inv.seller_addr_2}, {inv.seller_addr_3}, Eesti · Rg-kood {inv.seller_reg}
      </div>
    </div>
  </div>
</body>
</html>
"""


def write_all_artifacts():
    inv = InvoiceData()
    assert inv.reference_number == "107026", f"Expected 107026, got {inv.reference_number}"
    assert valideeri_viitenumber("107026") is True

    # 1. Genereeri mõlemad PDF failid
    pdf_main = Path("/workspace/puidujaak/Puidujaak-OU-Arve-nr-2026-00514.pdf")
    pdf_deploy = Path("/workspace/puidujaak/veeb_deploy/Puidujaak-OU-Arve-nr-2026-00514.pdf")
    generate_merit_style_pdf(inv, pdf_main)
    generate_merit_style_pdf(inv, pdf_deploy)

    # 2. Genereeri mõlemad HTML e-kirja mallid
    e1_html = generate_transactional_email_html(inv, "order_received")
    e2_html = generate_transactional_email_html(inv, "invoice_attached")

    for base_dir in [Path("/workspace/puidujaak"), Path("/workspace/puidujaak/veeb_deploy")]:
        (base_dir / "email_1_tellimus_kaes.html").write_text(e1_html, encoding="utf-8")
        (base_dir / "email_2_arve_manusega.html").write_text(e2_html, encoding="utf-8")

    # 3. Kirjuta dokumentatsioon /workspace/puidujaak/kliendi_teekond_montonio_merit.md
    doc_md = f"""# Puidujaak OÜ (`puidujaak.ee`) – 0 €/kuus Kliendi Teekond (Montonio + Merit Aktiva stiilis PDF-arve + 2 automaatkirja)

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
3. Klient tasub **„Maksa pangas“** (Montonio pangalink: LHV, Swedbank, SEB, Coop, Luminor). Puidujaak OÜ 8% agendimudelis arvestatakse **8% vahendustasu ({_fmt_eur(inv.marketplace_commission_8pct)} €)** Puidujaak OÜ-le ja **92% ({_fmt_eur(inv.seller_payout_92pct)} €)** müüjale.

### Samm 2: Automaatkiri #1 (1 sekund peale makset)
* **Pealkiri:** `Sinu tellimus lehel Puidujaak.ee saadi kätte!`
* **Sisu:**
  - Tervitus (*„Tere, {inv.buyer_name}! Oleme sinu tellimuse kätte saanud ja see on nüüd töötlemisel.“*)
  - Tellimuse kokkuvõte `Tellimus #{inv.order_no} ({inv.issue_date})` koos `48×48 px` tootefoto, koguse, vahesumma, Montonio pakiautomaadi / 24/7 Dropoff-punkti rea ja kogusummaga (**{_fmt_eur(inv.total_eur)} €**).
  - **Kollane infokast (`border: 1px solid #e0c36e`):** täitmise kuupäev, 24/7 väravakoodi info ja otselink **📍 Ava täpne Google Maps Pin**.

### Samm 3: Automaatkiri #2 (2 sekundit peale makset, koos PDF-arvega manuses)
* **Pealkiri:** `Arve {inv.invoice_no} sinu tellimusele #{inv.order_no}`
* **Sisu:** Tellimuse kokkuvõte + teade *„Sinu arve on lisatud selle e-kirja manusesse.“* + manuses `Puidujaak-OU-Arve-nr-{inv.invoice_no}.pdf`.

### Samm 4: Merit Aktiva stiilis sinise päisega A4 PDF-arve
* Täpsed visuaalsed parameetrid (`Trivium-OU-Arve-nr-2026-00514.pdf` järgi):
  - Helesinine päisekast ja tabelipäis: `RGB(175, 221, 255)` (`#afddff` / `#b8dcff`), raam `RGB(122, 154, 178)` (`#7a9ab2`).
  - Ülal vasakul: `Arve saaja` + kliendi nimi.
  - Ülal paremal: `Arve nr {inv.invoice_no}`, `Kuupäev: {inv.issue_date}`, `Maksetähtpäev: {inv.due_date}`, Eesti 7-3-1 `Viitenumber: {inv.reference_number}`, `Viivis: {inv.late_fee}`.
  - Müüja plokk: **Puidujaak OÜ**, aadress, `Rg-kood {inv.seller_reg}`.
  - Tabel: `Kirjeldus | Kogus | Ühik | Hind | Summa`.
  - Kokkuvõte: `Ei ole käibemaksukohustuslane` (või 24% KM valik) ja **Arve kokku (EUR) {_fmt_eur(inv.total_eur)}**.
  - Jalus: `LHV SWIFT LHVBEE22` ja `IBAN {inv.seller_iban}`.

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
"""
    Path("/workspace/puidujaak/kliendi_teekond_montonio_merit.md").write_text(doc_md, encoding="utf-8")
    print(f"Generated PDF: {pdf_main} ({pdf_main.stat().st_size} bytes)")
    print(f"Generated PDF: {pdf_deploy} ({pdf_deploy.stat().st_size} bytes)")
    print("Generated HTML emails and kliendi_teekond_montonio_merit.md")


if __name__ == "__main__":
    write_all_artifacts()
