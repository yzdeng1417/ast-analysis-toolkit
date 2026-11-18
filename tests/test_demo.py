"""Integration checks for bundled demonstration inputs and calculated outputs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from cmp.dataset import load_cmp_tsv
from cmp.reproduce import DATA, read_table, run
from cmp.retrain import frozen_plan

ROOT = Path(__file__).resolve().parents[1]


class DemonstrationTest(unittest.TestCase):
    def test_features_labels_and_grouped_roles(self):
        wells = read_table('wells.tsv')
        self.assertFalse(wells.row_id.duplicated().any())
        for cohort in ('development', 'evaluation'):
            frame = read_table(f'{cohort}.tsv')
            arr = load_cmp_tsv(DATA / f'{cohort}.tsv')
            meta = wells.loc[wells.cohort.eq(cohort)].sort_values('row_index0')
            self.assertEqual(meta.row_index0.tolist(), list(range(len(frame))))
            np.testing.assert_array_equal(arr.y, meta.growth)
            for (_, row), (_, context) in zip(frame.iterrows(), meta.iterrows()):
                species = {c.removeprefix('species_') for c in frame if c.startswith('species_') and row[c] == 1}
                drugs = {c.removeprefix('antibiotic_') for c in frame if c.startswith('antibiotic_example_') and row[c] == 1}
                self.assertEqual(species, {context.species.lower()})
                self.assertEqual(drugs, {s.lower() for s in context.drug_context.split('+')})
            if cohort == 'development':
                plan = frozen_plan(read_table('split_manifest.tsv'), meta, arr.y)
                self.assertEqual(len(plan), 30)

    def test_series_membership_and_prediction_provenance(self):
        wells = read_table('wells.tsv').set_index('row_id')
        series = read_table('series.tsv')
        links = read_table('series_wells.tsv')
        self.assertFalse(links.duplicated().any())
        self.assertTrue(set(links.row_id).issubset(wells.index))
        # A retained control can be unused by MIC series while still contributing
        # to classification. Every drug-exposed well must have a membership.
        unused = wells.loc[~wells.index.isin(links.row_id)]
        self.assertTrue(unused.concentration.eq(0).all())
        keys = ['cohort', 'group_id', 'drug_context']
        self.assertEqual(set(map(tuple, links[keys].to_numpy())), set(map(tuple, series[keys].to_numpy())))
        for _, row in links.iterrows():
            well = wells.loc[row.row_id]
            self.assertEqual((row.cohort, row.group_id), (well.cohort, well.group_id))
            if well.concentration != 0:
                self.assertEqual(row.drug_context, well.drug_context)
        provenance = json.loads((DATA/'prediction_provenance.json').read_text())
        for name, expected in provenance['input_sha256'].items():
            self.assertEqual(hashlib.sha256((DATA/name).read_bytes()).hexdigest(), expected)
        self.assertEqual(hashlib.sha256((DATA/'scores.tsv').read_bytes()).hexdigest(), provenance['scores_sha256'])
        self.assertEqual(set(read_table('scores.tsv').arm), {'full'})

    def test_saved_calculation_matches_distributed_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'calculated'
            run(output, 'saved')
            for name in ('classification.tsv','mic_series.tsv','mic_counts.tsv','summary.json','provenance.json'):
                self.assertEqual((output/name).read_bytes(), (ROOT/'tables'/name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
