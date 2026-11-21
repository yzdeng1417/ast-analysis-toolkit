# Demonstration inputs

These files contain the toolkit’s demonstration data. See the [data license](../../../../DATA-USE.md).

| File | Meaning |
| --- | --- |
| `development.tsv`, `evaluation.tsv` | Paired time-series measurements, categorical features and binary growth labels |
| `wells.tsv` | Example identifiers, per-cohort matrix row positions, categories and dilution concentrations |
| `split_manifest.tsv` | Training, early-stopping and validation assignments by group |
| `series.tsv` | Group and drug identifiers with comparison endpoints for each concentration series |
| `series_wells.tsv` | Membership links, including shared control wells |
| `scores.tsv` | Growth predictions from the full-model ensemble |
| `protocol.json` | Model settings, data splits and classification threshold |
| `prediction_provenance.json` | Training-input and score checksums for the distributed predictions |

`Example_Strain_A` identifies an isolate group and `Example_Specimen_A` identifies a specimen group. Combination drugs join their component codes with `+`.

The `growth` column records the binary endpoint label. Concentrations and comparison endpoints use discrete dilution values. A blank comparator means that no reference value is available.
