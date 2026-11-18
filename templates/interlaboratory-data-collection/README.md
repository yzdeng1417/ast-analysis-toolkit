# Interlaboratory data collection template

**Version:** 1.0

[Download the blank workbook](collection_template.xlsx).

This template organizes experimental conditions, paired glucose–turbidity measurements and independently measured reference results for future data collection across laboratories. The three data worksheets contain column headers and empty entry rows. Worksheet names and in-workbook instructions are in Chinese; data field names are in English.

| Worksheet | Purpose | One row represents |
| --- | --- | --- |
| 填写说明 (Instructions) | Definitions, units and entry conventions | One instruction |
| 实验条件 (Experimental conditions) | Specimen, drug, concentration, replicate and assay settings | One specimen–drug–concentration–technical-replicate trajectory |
| 逐孔时序 (Per-well time series) | Paired GLU and turbidity readings, actual elapsed time and measurement metadata | One paired measurement at one time point |
| 参考结果 (Reference results) | Independent MIC or growth-reference results and their provenance | One reference result |

## Recording and linking measurements

- Use `lab_id + experiment_id + trajectory_id` to link conditions and time-series rows. Use `reference_id`, together with laboratory and experiment identifiers, to link reference results.
- Use de-identified `specimen_id` values. Each participating centre retains its clinical identity mapping in its controlled records. Reserve `isolate_id` for cultured isolates.
- Record `actual_elapsed_min` from inoculation and preserve the actual reference readout time in `culture_read_elapsed_h`. Use `overnight_yes_no` to record overnight reading when exact elapsed hours are unavailable.
- Enter raw absorbance in `GLU_A620` and `turbidity_A620`; record calibrated glucose concentration separately with its `calibration_id`.
- Record antibiotic concentrations in µg/mL and retain the original value and unit. Preserve MIC inequality operators and the reference method, breakpoint standard and version.
- Keep independently measured MICs, manually assessed growth labels and model predictions distinct. Record technical and biological replicate identifiers separately.
- Leave missing values blank and record a `missing_reason`; reserve zero for a measured zero. Retain controls, exclusion reasons and source-file identifiers.
- Copy the blank entry rows as needed and retain a copy of the template version used.

The blank workbook records new experiments and contains no example drug names, organism names, specimen records or measured values. The command-line workflow uses separate pseudonymized and numerically perturbed demonstration data. Its fields and demonstration settings are documented in the [feature schema](../../src/cmp/feature_schema.yaml) and the [analysis protocol](../../src/cmp/data/demo/protocol.json). Names entered in this blank template are not automatically transformed by the software.

## 中文说明

此空白模板用于后续跨实验室数据采集，包含填写说明、实验条件、逐孔 GLU–NTU 时序和独立参考结果四张工作表。模板采用去标识化的样本编号，临床身份映射由各中心在受控记录中保存。实验条件与逐孔时序通过实验及轨迹标识关联，独立参考结果通过参考标识关联。各项单位、缺失值和参考结果的填写规则见工作簿“填写说明”。

## Version integrity

SHA-256 of the version 1.0 workbook:

```text
c84bfdc2a9ded3c31866a2421b9d2b3ab6e2a419aa4d725817f7b89753674473
```

This template is licensed under the [MIT License](../../LICENSE).
