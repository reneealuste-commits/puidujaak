import fs from 'fs';
import path from 'path';

const TMP_DB = '/tmp/puidujaak_measurements.json';

function readDb() {
  try {
    if (fs.existsSync(TMP_DB)) {
      return JSON.parse(fs.readFileSync(TMP_DB, 'utf8'));
    }
  } catch (e) {}
  return [];
}

function writeDb(rows) {
  try {
    fs.writeFileSync(TMP_DB, JSON.stringify(rows, null, 2), 'utf8');
  } catch (e) {}
}

function calcVolumeM3(d1, d2, L) {
  if (!d1 || !L || d1 <= 0 || L <= 0) return null;
  const area = d => Math.PI * Math.pow(d / 200, 2);
  const a = (d2 && d2 > 0) ? (area(d1) + area(d2)) / 2 : area(d1);
  return Number((a * (L / 100)).toFixed(5));
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    const rows = readDb();
    return res.status(200).json(rows);
  }

  if (req.method === 'POST') {
    try {
      const body = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
      const d1 = parseFloat(body.diameter_cm) || null;
      const d2 = parseFloat(body.diameter2_cm) || null;
      const L = parseFloat(body.length_cm) || null;
      if (!d1 && !L) {
        return res.status(400).json({ error: 'need at least diameter or length' });
      }
      const vol = calcVolumeM3(d1, d2, L);
      const rows = readDb();
      const newId = rows.length ? Math.max(...rows.map(r => r.id || 0)) + 1 : 1;
      const item = {
        id: newId,
        created_at: new Date().toLocaleString('et-EE', { timeZone: 'Europe/Tallinn' }),
        product_id: body.product_id || '',
        photo_id: body.photo_id || '',
        piece_type: body.piece_type || 'log',
        reference: body.reference || '',
        px_per_mm: parseFloat(body.px_per_mm) || null,
        diameter_cm: d1,
        diameter2_cm: d2,
        length_cm: L,
        volume_m3: vol,
        notes: String(body.notes || '').slice(0, 2000),
        image: body.image || null
      };
      rows.unshift(item);
      writeDb(rows);
      return res.status(201).json({ id: item.id, volume_m3: vol, item });
    } catch (err) {
      return res.status(500).json({ error: String(err && err.message ? err.message : err) });
    }
  }

  if (req.method === 'DELETE') {
    const id = parseInt(req.query?.id || (req.url.split('/').pop()), 10);
    const rows = readDb().filter(r => r.id !== id);
    writeDb(rows);
    return res.status(200).json({ ok: true });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
