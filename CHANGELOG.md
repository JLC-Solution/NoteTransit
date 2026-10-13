# Changelog

All versions are available on the [Releases page](https://github.com/JLC-Solution/NoteTransit/releases).

## 1.1 — 2026-10-13
- **Retry only failed pages**: when the previous run ended with errors, the launcher asks
  "Retry ONLY these pages?" and re-reads only the sections containing them — no full OneNote scan.
  Also works with progress files created by 1.0.
- Quieter output: a full run lists only the sections that still have pages to migrate, plus a summary.
- Better filing when a note's date differs slightly (falls back to a unique title match).
- README / guides: first Microsoft sign-in, how to stop and resume safely, files in the folder, cleanup (EN/FR).

## 1.0 — 2026-10-12
- First public release: OneNote notebooks → Apple Notes folders, with images inline, tables,
  checklists, attachments and original dates. English and French versions.
