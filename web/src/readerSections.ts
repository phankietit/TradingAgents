/** Parse only the application-owned localized report heading contract.
 * Unknown structure falls back to the untouched saved Markdown.
 */
export interface ReaderSections {
  summary: string; thesis: string; risks: string; invalidation: string; horizon: string | null;
}

export function readerSections(markdown: string, locale: 'en' | 'vi'): ReaderSections | null {
  const headings = locale === 'vi'
    ? ['Tóm tắt', 'Luận điểm đầu tư', 'Rủi ro', 'Điều kiện mất hiệu lực', 'Khung thời gian nghiên cứu']
    : ['Executive summary', 'Investment thesis', 'Risks', 'Invalidation conditions', 'Research horizon'];
  const matches = [...markdown.matchAll(/^## ([^\n]+)\s*$/gm)];
  if (matches.length < 4 || matches.length > 5
      || matches.some((match, index) => match[1] !== headings[index])
      || markdown.slice(0, matches[0].index).trim()) return null;
  const bodies = matches.map((match, index) => markdown.slice(
    match.index! + match[0].length, matches[index + 1]?.index ?? markdown.length).trim());
  if (bodies.some(body => !body || /^#{1,6}\s/m.test(body))) return null;
  return { summary: bodies[0], thesis: bodies[1], risks: bodies[2],
    invalidation: bodies[3], horizon: bodies[4] ?? null };
}
