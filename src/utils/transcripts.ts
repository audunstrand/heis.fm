/**
 * Parse transcript glob results into a record keyed by episode number.
 *
 * Usage with import.meta.glob (which must be called with a literal string):
 *
 *   const files = import.meta.glob<TranscriptModule>('../../content/transcripts/*.md', { eager: true });
 *   const transcripts = parseTranscriptModules(files);
 */

export interface TranscriptModule {
  compiledContent: () => string;
}

export function parseTranscriptModules(
  files: Record<string, TranscriptModule>,
): Record<string, string> {
  const transcripts: Record<string, string> = {};

  for (const [path, mod] of Object.entries(files)) {
    const match = path.match(/\/(\d+)\.md$/);
    if (match) {
      transcripts[match[1]] = mod.compiledContent();
    }
  }

  return transcripts;
}
