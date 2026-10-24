import fs from 'fs';
import path from 'path';
import zlib from 'zlib';

const p1 = fs.readFileSync('assets_part1.txt', 'utf8').trim();
const p2 = fs.readFileSync('assets_part2.txt', 'utf8').trim();
const compressed = Buffer.from(p1 + p2, 'base64');
const jsonStr = zlib.inflateSync(compressed).toString('utf8');
const bundle = JSON.parse(jsonStr);

for (const [relPath, b64Data] of Object.entries(bundle)) {
  const fullPath = path.join('public', relPath);
  fs.mkdirSync(path.dirname(fullPath), { recursive: true });
  fs.writeFileSync(fullPath, Buffer.from(b64Data, 'base64'));
}

fs.copyFileSync('index.html', path.join('public', 'index.html'));
console.log('Extracted', Object.keys(bundle).length, 'assets + index.html into public/');
