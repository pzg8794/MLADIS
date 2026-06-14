export function formatStayName(value: string, separator: ', ' | ' - ' = ', ') {
  const clean = value
    .replace(/^MLADIS\s*[-–]\s*/i, '')
    .replace(/\bBedrooms?\b/gi, 'Beds')
    .replace(/\s+/g, ' ')
    .trim();
  const match = clean.match(/^(\d+)\s+Beds?\s+(.+?)(?:\s+(G-\d+))?$/i);
  if (!match) return clean;

  const bedrooms = match[1];
  const title = match[2].replace(/\s+G-\d+$/i, '').trim();
  const block = match[3] || clean.match(/\bG-\d+\b/i)?.[0] || '';
  return [`${bedrooms} Beds Apt`, title, block].filter(Boolean).join(separator);
}
