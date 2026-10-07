# veraPDF results (UA1)

Checked on 2026-10-07. These are machine checks only. Passing them does not mean a file is accessible: a person still checks reading order, alt text and tables.

## before/council-agenda-2026-03-10.pdf

Failed 7 rules (242 checks)

- No tag structure (rule 7.1-11, 1 check). veraPDF says: The logical structure of the conforming file shall be described by a structure hierarchy rooted in the StructTreeRoot entry of the document catalog dictionary, as described in ISO 32000-1:2008, 14.7
- Some content is not tagged (rule 7.1-3, 118 checks). veraPDF says: Content shall be marked as Artifact or tagged as real content
- Fonts not embedded (rule 7.21.4.1-1, 2 checks). veraPDF says: The font programs for all fonts used for rendering within a conforming file shall be embedded within that file, as defined in ISO 32000-1:2008, 9.9
- No XMP metadata in the file (rule 7.1-8, 1 check). veraPDF says: The Catalog dictionary of a conforming file shall contain the Metadata key whose value is a metadata stream as defined in ISO 32000-1:2008, 14.3.2. The metadata stream dictionary shall contain entry Type with value /Metadata and entry Subtype with value /XML
- Not marked as tagged (rule 6.2-1, 1 check). veraPDF says: The document catalog dictionary shall include a MarkInfo dictionary containing an entry, Marked, whose value shall be true
- Language not set (rule 7.2-34, 118 checks). veraPDF says: Natural language for text in page content shall be determined
- Title bar does not show the document title (rule 7.1-10, 1 check). veraPDF says: The document catalog dictionary shall include a ViewerPreferences dictionary containing a DisplayDocTitle key, whose value shall be true

## after/council-agenda-2026-03-10.pdf

Passed all PDF/UA-1 machine checks

