import fs from 'fs';
import path from 'path';
import zlib from 'zlib';

const p1 = fs.readFileSync('assets_part1.txt', 'utf8').trim();
const p2 = fs.readFileSync('assets_part2.txt', 'utf8').trim();
const compressed = Buffer.from(p1 + p2, 'base64');
const jsonStr = zlib.inflateSync(compressed).toString('utf8');
const bundle = JSON.parse(jsonStr);

if (fs.existsSync('assets_part3a.txt') && fs.existsSync('assets_part3b.txt')) {
  const p3a = fs.readFileSync('assets_part3a.txt', 'utf8').trim();
  const p3b = fs.readFileSync('assets_part3b.txt', 'utf8').trim();
  const c3 = Buffer.from(p3a + p3b, 'base64');
  const b3 = JSON.parse(zlib.inflateSync(c3).toString('utf8'));
  Object.assign(bundle, b3);
}

if (fs.existsSync('assets_part4.txt')) {
  const p4 = fs.readFileSync('assets_part4.txt', 'utf8').trim();
  const c4 = Buffer.from(p4, 'base64');
  const b4 = JSON.parse(zlib.inflateSync(c4).toString('utf8'));
  Object.assign(bundle, b4);
}

for (const [relPath, b64Data] of Object.entries(bundle)) {
  const fullPath = path.join('public', relPath);
  fs.mkdirSync(path.dirname(fullPath), { recursive: true });
  fs.writeFileSync(fullPath, Buffer.from(b64Data, 'base64'));
}

fs.copyFileSync('index.html', path.join('public', 'index.html'));
if (fs.existsSync('unified.css')) fs.copyFileSync('unified.css', path.join('public', 'unified.css'));
if (fs.existsSync('unified.js')) fs.copyFileSync('unified.js', path.join('public', 'unified.js'));
console.log('Extracted', Object.keys(bundle).length, 'assets + index.html into public/');
