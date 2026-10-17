// Helper for scripts/fashion_illustration_coverage.py.
// Applies the live client matcher (catalog.js selectIllustration) to each look and
// prints the chosen illustration id (or null) per row as a JSON array.
import fs from 'node:fs';
import {selectIllustration} from '../assets/dalha-illustrations/catalog.js';

const rows = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const result = rows.map(row => {
  if (row.error) return null;
  const hit = selectIllustration(row.look);
  return hit ? hit.id : null;
});
process.stdout.write(JSON.stringify(result));
