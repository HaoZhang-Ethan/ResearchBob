# Intake Rules

- Use the active profile as the default source of retrieval intent.
- Preserve `low-priority` entries in the registry instead of silently discarding them.
- Treat versioned arXiv ids with the same base id as one logical paper and keep the newest update.
- Write one `metadata.json` file per paper directory so later skills can work paper-by-paper.
