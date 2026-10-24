export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
    const {
      product_id = 'PUIDUJAK-???',
      photo_id = 'ID???',
      short_title = '',
      product_title = '',
      category = '',
      dimension_cm = '',
      dimension_class = '',
      buyer_name = '',
      buyer_contact = '',
      buyer_note = '',
      mode = 'instant_click'
    } = body;

    const timestamp = new Date().toLocaleString('et-EE', { timeZone: 'Europe/Tallinn' });
    const isContactUpdate = mode === 'contact_details' && (buyer_name || buyer_contact || buyer_note);
    const subjectPrefix = isContactUpdate ? '[Puidujaak.ee EELTELLIMUS + KONTAKT]' : '[Puidujaak.ee OLEN HUVITATUD]';
    const subject = `${subjectPrefix} ${product_id} / ${photo_id} (${short_title || product_title})`;

    const payload = {
      _subject: subject,
      _template: 'table',
      _captcha: 'false',
      Sündmus: isContactUpdate
        ? 'Huviline lisas oma kontaktandmed / eeltellimuse täpsustuse'
        : 'Keegi vajutas turuplatsil nuppu "Olen huvitatud"',
      Toote_ID: product_id,
      Foto_ID: photo_id,
      Faili_lühinimi: short_title,
      Toote_nimetus: product_title,
      Kategooria: category,
      Mõõt_cm: dimension_cm ? `${dimension_cm} cm` : 'Müüja täpsustamisel (väli tühi)',
      Mõõduklass: dimension_class || 'Täpsustamisel',
      Huvilise_nimi: buyer_name || '(1-kliki kiirhuviteade – nime ei sisestatud)',
      Huvilise_kontakt: buyer_contact || '(1-kliki kiirhuviteade – kontakti ei sisestatud)',
      Märkus_või_soov: buyer_note || 'Soovib lisainfot / broneerida antud puidutüki.',
      Kuupäev_ja_kellaaeg: timestamp,
      Turuplatsi_link: `https://puidujaak.vercel.app/#${product_id}`
    };

    if (buyer_contact && buyer_contact.includes('@')) {
      payload._replyto = buyer_contact.trim();
    }

    const response = await fetch('https://formsubmit.co/ajax/78c3a12c74aa756d1d5e36e3c5f0168b', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': 'https://puidujaak.vercel.app',
        'Referer': 'https://puidujaak.vercel.app/',
        'User-Agent': 'Mozilla/5.0 (compatible; PuidujaakMarketplace/1.0; +https://puidujaak.vercel.app)'
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));
    if (response.ok && (data.success === 'true' || data.success === true)) {
      return res.status(200).json({
        ok: true,
        delivered_to: 'reneealuste@gmail.com',
        subject,
        timestamp,
        formsubmit: data
      });
    }

    return res.status(200).json({
      ok: true,
      fallback_needed: true,
      delivered_to: 'reneealuste@gmail.com',
      subject,
      timestamp,
      details: data
    });
  } catch (err) {
    return res.status(500).json({
      ok: false,
      error: String(err && err.message ? err.message : err)
    });
  }
}
