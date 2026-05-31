# Gazetteer

DUUI-py migration for the legacy `gazetteer-rs/biofid` DUUI service shape.

The annotator expects a running `gazetteer-rs/biofid` compatible backend via
`backend_url` or `GAZETTEER_RS_URL`. It forwards full document text and emits
`org.texttechnologylab.annotation.type.Taxon` annotations from the backend
`begin`, `end`, `match_strings`, and `match_labels` fields.
