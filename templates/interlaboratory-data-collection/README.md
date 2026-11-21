# Interlaboratory data collection template

Version 1.0

[Download the blank workbook](collection_template.xlsx).

Use the template to record experimental conditions, paired glucose and turbidity measurements, and independent reference results. The three data sheets have column headers and blank entry rows.

| Worksheet | Purpose | One row represents |
| --- | --- | --- |
| Instructions | Definitions, units and entry conventions | One instruction |
| Experimental conditions | Specimen, drug, concentration, replicate and assay settings | One technical replicate for a specimen, drug and concentration |
| Per-well time series | Paired glucose and turbidity readings with elapsed time and measurement details | One paired measurement at one time point |
| Reference results | Independent MIC or growth-reference results and their source | One reference result |

## Recording and linking measurements

- Use `lab_id + experiment_id + trajectory_id` to link conditions and time-series rows. Use `reference_id`, together with laboratory and experiment identifiers, to link reference results.
- Use de-identified `specimen_id` values. Each participating centre retains its clinical identity mapping in its controlled records. Reserve `isolate_id` for cultured isolates.
- Record `actual_elapsed_min` from inoculation and preserve the actual reference readout time in `culture_read_elapsed_h`. Use `overnight_yes_no` to record overnight reading when exact elapsed hours are unavailable.
- Enter raw absorbance in `GLU_A620` and `turbidity_A620`; record calibrated glucose concentration separately with its `calibration_id`.
- Record antibiotic concentrations in µg/mL and retain the original value and unit. Preserve MIC inequality operators and the reference method, breakpoint standard and version.
- Keep independently measured MICs, manually assessed growth labels and model predictions distinct. Record technical and biological replicate identifiers separately.
- Leave missing values blank and record a `missing_reason`; reserve zero for a measured zero. Retain controls, exclusion reasons and source-file identifiers.
- Copy the blank entry rows as needed and retain a copy of the template version used.

The command-line workflow uses its own [demonstration data](../../src/cmp/data/demo/).

## Version integrity

Verify the workbook with its SHA-256 checksum.

```text
29f2eb5538a582e8680433c37dc086e9733c35883018b7fb7590980b1198162b
```

This template is licensed under the [MIT License](../../LICENSE).
