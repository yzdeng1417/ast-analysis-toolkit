"""Full-model training adapted from the MIT-licensed 1.0 implementation."""
import importlib.metadata
import json
import platform
import time
import numpy as np
import pandas as pd
from cmp.representations import load_representation

SEEDS = (42, 43, 44, 45, 46)


def save_table(frame, path):
    frame.to_csv(path, sep="\t", index=False, float_format="%.17g")


def environment():
    versions = {name: importlib.metadata.version(package) for name, package in
                (("numpy", "numpy"), ("pandas", "pandas"), ("sklearn", "scikit-learn"))}
    versions["python"] = platform.python_version()
    try:
        versions["torch"] = importlib.metadata.version("torch").split("+")[0]
    except importlib.metadata.PackageNotFoundError:
        versions["torch"] = None
    return versions


def train(bundle, output):
    import torch
    from cmp.training import fit_member, predict, subset

    actual = environment()
    expected = bundle["protocol"]["environment"]
    if actual != expected:
        raise ValueError(f"Strict training requires the reference environment: {expected}; found {actual}. See requirements-train.txt")
    torch.set_num_threads(bundle["protocol"]["training"]["torch_threads"])
    torch.use_deterministic_algorithms(True)
    development = bundle["cohorts"]["development"]["arrays"]
    evaluation_arrays = bundle["cohorts"]["evaluation"]["arrays"]
    (output / "models").mkdir()
    scores = {name: np.full((len(c["metadata"]), len(SEEDS)), np.nan) for name, c in bundle["cohorts"].items()}
    folds = np.zeros(len(development.y), dtype=int)
    records = []
    for fold, seed, fit, stop, evaluation in bundle["plan"]:
        started = time.monotonic()
        name = f"outer_{fold}_seed_{seed}" if fold else f"final_seed_{seed}"
        model, stats, record = fit_member(development, fit, stop, seed, bundle["protocol"],
                                          output / "models" / f"{name}.pt")
        cohort = "development" if fold else "evaluation"
        target = subset(development, evaluation) if fold else evaluation_arrays
        score = predict(model, stats, target, bundle["protocol"]["training"]["batch_size"])
        row_indices = evaluation if fold else np.arange(len(evaluation_arrays.y))
        scores[cohort][row_indices, SEEDS.index(seed)] = score
        if fold:
            folds[evaluation] = fold
        record.update(stage="outer" if fold else "final", fold=fold, seconds=time.monotonic() - started)
        records.append(record)
        save_table(pd.DataFrame(records), output / "fit_summary.tsv")
        print(f"{name}: best epoch {record['best_epoch']}, {record['epochs_run']} epochs ({record['seconds']:.1f}s)", flush=True)
    predictions = {}
    for cohort, matrix in scores.items():
        if not np.isfinite(matrix).all():
            raise ValueError("Incomplete predictions")
        c = bundle["cohorts"][cohort]
        frame = c["metadata"][["row_index0", "row_id", "group_id"]].copy()
        frame["growth"] = c["arrays"].y
        # Each predict() casts the sigmoid float32 scores to float64 before averaging.
        frame["score"] = matrix.mean(axis=1)
        for i, seed in enumerate(SEEDS):
            frame[f"member_score_{seed}"] = matrix[:, i]
        frame["threshold"], frame["prediction"] = .5, (frame.score >= .5).astype(int)
        if cohort == "development":
            frame["outer_fold"] = folds
        predictions[cohort] = frame
    return predictions, pd.DataFrame(records)


def frozen_plan(splits, metadata, labels):
    """Consume row roles verbatim; group names must never drive re-splitting."""
    expected = {(fold, seed) for fold in range(6) for seed in SEEDS}
    if (len(splits) != len(metadata) * 30 or splits.duplicated(["outer_fold", "member_seed", "row_index0"]).any()
            or set(zip(splits.outer_fold, splits.member_seed)) != expected):
        raise ValueError("Incomplete or duplicate frozen split roles")
    plan, outer_membership = [], {}
    for fold in (1, 2, 3, 4, 5, 0):
        for seed in SEEDS:
            frame = splits.loc[splits.outer_fold.eq(fold) & splits.member_seed.eq(seed)].sort_values("row_index0")
            roles = {"optimizer", "early_stop", "outer_validation"} if fold else {"optimizer", "early_stop"}
            if (frame.row_index0.tolist() != list(range(len(metadata))) or set(frame.role) != roles
                    or not np.array_equal(frame.group_id, metadata.group_id)
                    or frame.groupby("group_id").role.nunique().max() != 1):
                raise ValueError(f"Invalid grouped role assignment: fold {fold}, seed {seed}")
            indices = {role: frame.loc[frame.role.eq(role), "row_index0"].to_numpy(dtype=int) for role in roles}
            if any(len(np.unique(labels[idx])) != 2 for idx in indices.values()):
                raise ValueError("Each optimizer, stopping and validation partition requires both classes")
            evaluation = indices.get("outer_validation")
            if fold:
                if seed == SEEDS[0]:
                    outer_membership[fold] = evaluation
                elif not np.array_equal(evaluation, outer_membership[fold]):
                    raise ValueError("Outer validation changed across members")
            plan.append((fold, seed, indices["optimizer"], indices["early_stop"], evaluation))
    if sorted(np.concatenate(list(outer_membership.values())).tolist()) != list(range(len(metadata))):
        raise ValueError("Every development row must be evaluated in exactly one fold")
    return plan


def retrain(data, metadata, output):
    protocol = json.loads((data / "protocol.json").read_text())
    cohorts = {}
    for name, cohort in [("development", "development"), ("evaluation", "evaluation")]:
        rows = metadata.loc[metadata.cohort.eq(cohort)].sort_values("row_index0")
        arrays = load_representation(data / f"{name}.tsv", "centered", time_step=15.0)
        cohorts[name] = {"arrays": arrays, "metadata": rows}
    dev = cohorts["development"]
    splits = pd.read_csv(data / "split_manifest.tsv", sep="\t")
    plan = frozen_plan(splits, dev["metadata"], dev["arrays"].y)
    predictions, fits = train({"protocol": protocol, "cohorts": cohorts, "plan": plan}, output)
    save_table(fits, output / "fit_summary.tsv")
    for name, frame in predictions.items():
        save_table(frame, output / f"{name}_trained_scores.tsv")
    return pd.concat([frame[["row_id", "score"]] for frame in predictions.values()], ignore_index=True)
