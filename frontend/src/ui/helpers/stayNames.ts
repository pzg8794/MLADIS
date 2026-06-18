export function formatStayName(value: string, separator: ', ' | ' - ' = ', ') {
  const clean = value
    .replace(/^MLADIS\s*[-–]\s*/i, '')
    .replace(/\bBedrooms?\b/gi, 'Beds')
    .replace(/\s+/g, ' ')
    .trim();
  const formattedMatch = clean.match(/^(\d+)\s+Beds?\s+Apts?,?\s+(.+)$/i);
  if (formattedMatch) {
    const bedrooms = formattedMatch[1];
    const title = formattedMatch[2].replace(/,?\s+G-\d+$/i, '').replace(/,+$/g, '').trim();
    const block = clean.match(/\bG-\d+\b/i)?.[0] || '';
    return [`${bedrooms} Beds Apt`, title, block].filter(Boolean).join(separator);
  }

  const match = clean.match(/^(\d+)\s+Beds?\s+(.+?)(?:\s+(G-\d+))?$/i);
  if (!match) return clean;

  const bedrooms = match[1];
  const title = match[2].replace(/\s+G-\d+$/i, '').replace(/,+$/g, '').trim();
  const block = match[3] || clean.match(/\bG-\d+\b/i)?.[0] || '';
  return [`${bedrooms} Beds Apt`, title, block].filter(Boolean).join(separator);
}
