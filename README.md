# Antimicrobial Susceptibility Analysis Toolkit

Python tools for antimicrobial susceptibility analysis, grouped model evaluation and concentration-series reporting.

Version 1.0 uses demonstration data.

## Install and run

With Python 3.12 or later, run these commands from the source repository.

```sh
python -m pip install .
ast-reproduce --mode saved --output outputs/demo
```

You can also install the wheel from [release 1.0](https://github.com/yzdeng1417/ast-analysis-toolkit/releases/tag/1.0).

```sh
python -m pip install ast_analysis_toolkit-1.0-py3-none-any.whl
ast-reproduce --mode saved --output outputs/demo
```

Choose a new output directory for each run.

| File | Contents |
| --- | --- |
| `classification.tsv` | Growth classification metrics for the demonstration subsets |
| `mic_series.tsv` | Concentration-series endpoint estimates and comparisons |
| `mic_counts.tsv`, `summary.json` | Counts from those demonstration calculations |
| `provenance.json` | Input checksums, execution mode and data status |

Saved mode uses the bundled model scores to reproduce the [example results](tables/).

## Retrain the demonstration model

To repeat the training run, use Python 3.12.11 and install the pinned dependencies in a separate environment. Training runs on the CPU.

```sh
python -m pip install -r requirements-train.txt
python -m pip install .
ast-reproduce --mode train --output outputs/trained-demo
```

For each of the five outer folds, five models predict growth for the held-out groups. Five final models predict growth for the evaluation subset. The supplied splits keep each isolate group together across training, early stopping and validation. Training writes model checkpoints, fitting logs and results.

The demonstration uses a fixed classification threshold of 0.5. Model scores can vary with hardware and numerical libraries. See the [training protocol](src/cmp/data/demo/protocol.json).

## Data and examples

| Resource | Purpose |
| --- | --- |
| [Demonstration inputs](src/cmp/data/demo/) | Paired measurements, growth labels, drug and species codes, and group assignments |
| [Demonstration results](tables/) | Classification and concentration-series results for the full model |
| [Blank collection template](templates/interlaboratory-data-collection/) | Fields for recording new measurements and independent references |
| [Input and result checksums](input_sha256.json) | Integrity checks for this public copy |

`row_index0` links each well to its feature-matrix row. `row_id` links predictions to concentration series. Shared no-drug controls count once in classification. The development subset uses replicate consensus, and the evaluation subset uses a majority of three replicates. See the [endpoint and off-scale comparison rules](src/cmp/mic_rules.py).

## License

The code, software documentation and blank template use the [MIT License](LICENSE). The demonstration data, saved predictions and result tables use [CC BY 4.0](licenses/CC-BY-4.0.txt). Credit **yzdeng1417 and contributors** and indicate any changes. See the [data license and attribution terms](DATA-USE.md). Dependencies retain their own licenses.
