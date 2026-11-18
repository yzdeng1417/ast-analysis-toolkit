"""Run growth classification and MIC calculations on demonstration data."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

from cmp.evaluation import metrics
from cmp.mic_rules import compare_offscale, derive_prediction

DATA = Path(__file__).parent / "data" / "demo"
SERIES_KEY = ["cohort", "group_id", "drug_context"]


def read_table(name):
    return pd.read_csv(DATA / name, sep="\t", keep_default_na=False, float_precision="round_trip")


def write_table(frame, path):
    frame.to_csv(path, sep="\t", index=False, float_format="%.17g")


def classification(wells):
    results = []
    for (cohort, arm), group in wells.groupby(["cohort", "arm"]):
        control = group.concentration.eq(0)
        for population, subset in [("all", group), ("drug_exposed", group[~control]), ("no_drug_control", group[control])]:
            values = metrics(subset, 0.5)
            values["accuracy"] = (values["tp"] + values["tn"]) / values["n"]
            values["false_positive_rate"] = values["fp"] / values["no_growth"] if values["no_growth"] else None
            results.append({"cohort": cohort, "arm": arm, "population": population, **values})
    return pd.DataFrame(results)


def compare(endpoint, reference, cohort):
    if not endpoint["predicted_reportable"] or not reference.reference_operator:
        return "", "", ""
    value = float(endpoint["predicted_mic_value_ug_ml"])
    comparison = float(reference.comparison_reference_value)
    if cohort == "evaluation":
        delta, ea = compare_offscale(value, endpoint["predicted_mic_operator"], comparison, reference.reference_operator)
        return delta, delta == 0, ea
    ratio = value / comparison
    return math.log2(ratio), value == comparison, 0.5 <= ratio <= 2


def mic_results(wells):
    series = read_table("series.tsv").set_index(SERIES_KEY)
    memberships = read_table("series_wells.tsv")
    linked = memberships.merge(wells[["row_id", "concentration", "call", "arm"]], on="row_id")
    results = []
    for key, group in linked.groupby([*SERIES_KEY, "arm"]):
        cohort, unit, context, arm = key
        ref = series.loc[(cohort, unit, context)]
        rule = "triplicate_majority" if cohort == "evaluation" else "replicate_consensus"
        endpoint = derive_prediction(zip(group.concentration, group.call), rule, skip_policy="highest_tested")
        delta, exact, ea = compare(endpoint, ref, cohort)
        results.append(dict(cohort=cohort, group_id=unit, drug_context=context, arm=arm, **endpoint,
                            reference_operator=ref.reference_operator,
                            comparison_reference_value=ref.comparison_reference_value, difference=delta,
                            exact=exact, essential_agreement=ea))
    return pd.DataFrame(results)


def summarize(table):
    records = []
    for (cohort, arm), series in table.groupby(["cohort", "arm"]):
        evaluated = series.loc[series["difference"] != ""]
        records.append(dict(cohort=cohort, arm=arm, series=len(series), reportable=int(series.predicted_reportable.sum()),
                            evaluated=len(evaluated), exact=int(evaluated.exact.eq(True).sum()),
                            essential_agreement=int(evaluated.essential_agreement.eq(True).sum())))
    return records


def run(output, mode):
    output.mkdir(parents=True, exist_ok=False)
    metadata = read_table("wells.tsv")
    if mode == "train":
        from cmp.retrain import retrain
        scores = retrain(DATA, metadata, output).assign(arm="full")
    else:
        scores = read_table("scores.tsv")
    if (metadata.row_id.duplicated().any() or scores.row_id.duplicated().any()
            or set(scores.arm) != {"full"} or set(scores.row_id) != set(metadata.row_id)
            or not scores.score.between(0, 1).all()):
        raise ValueError("Expected one finite full-model demonstration score per well")
    wells = scores.merge(metadata, on="row_id", validate="one_to_one")
    wells["call"] = (wells.score >= 0.5).astype(int)
    write_table(classification(wells), output / "classification.tsv")
    per_series = mic_results(wells)
    write_table(per_series, output / "mic_series.tsv")
    summary = summarize(per_series)
    write_table(pd.DataFrame(summary), output / "mic_counts.tsv")
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    inputs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(DATA.iterdir()) if p.suffix in {".tsv", ".json"}
              and (mode == "saved" or p.name != "scores.tsv")}
    provenance = {"version": "1.0", "mode": mode,
                  "data_status": "pseudonymized and numerically perturbed demonstration data",
                  "score_source": "fresh full-model training" if mode == "train" else "bundled full-model demonstration scores",
                  "input_sha256": inputs,
                  "interpretation": "software demonstration; not clinical performance or paper reproduction"}
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return [record for record in summary if record["arm"] == "full"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["saved", "train"], default="saved")
    parser.add_argument("--output", type=Path, required=True, help="New directory for computed results")
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.mode), indent=2))


if __name__ == "__main__":
    main()
