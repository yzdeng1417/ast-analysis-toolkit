# Demonstration inputs

**Pseudonymized and numerically perturbed demonstration data.** These are adapted source records, not original measurements or independently generated synthetic data. They do not support paper reproduction, clinical claims or an anonymity guarantee. See [data terms](../../../../DATA-USE.md).

| File | Meaning |
| --- | --- |
| `development.tsv`, `evaluation.tsv` | Paired time-series inputs, example categorical features and retained binary endpoint-growth labels |
| `wells.tsv` | Example identifiers, per-cohort matrix row positions, categories and dilution concentrations |
| `split_manifest.tsv` | Retained grouped optimizer, early-stop and validation roles |
| `series.tsv` | Example group/drug contexts and retained discrete comparator values |
| `series_wells.tsv` | Membership links, including shared control wells |
| `scores.tsv` | Fresh full-model ensemble predictions on these transformed inputs |
| `protocol.json` | Model settings and interpretation boundaries |
| `prediction_provenance.json` | Training-input and score checksums for the distributed predictions |

`Example_Drug_A` means 示例药 A. `Example_Species_A` means 示例菌种 A. `Example_Strain_A` and `Example_Specimen_A` distinguish an isolate group from a specimen group. The letters have no clinical meaning and no public reverse mapping. Combination contexts retain component membership with `+`.

`growth` is a retained source endpoint label, not a label inferred from the perturbed early readings. Concentrations and comparison endpoints are discrete dilution values and were not numerically perturbed. Missing comparator values remain missing. The evaluation subset has been examined previously; it is a demonstration subset, not untouched validation.
