# Demonstration results

These files are recalculated from the bundled full-model demonstration scores and the pseudonymized and numerically perturbed inputs. They are software examples, not research supplementary tables or clinical performance evidence.

Run `ast-reproduce --mode saved --output outputs/demo` to regenerate `classification.tsv`, `mic_series.tsv`, `mic_counts.tsv`, `summary.json` and `provenance.json`. `fit_summary.tsv` records the fresh training run that supplied the scores. Checkpoint files are created by training and are not included in this release.

Discrete comparison MIC values were retained from source records to exercise the comparison functions. Any agreement counts apply only to this demonstration calculation and do not establish independently validated performance.
