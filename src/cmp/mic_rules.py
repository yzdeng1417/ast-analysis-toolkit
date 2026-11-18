"""Prediction-only MIC endpoints and an explicit off-scale comparison rule.

No observed outcome is accepted by derive_prediction(). Complete drug context is
resolved upstream; this module receives actual concentrations in ug/mL.
"""
from collections import defaultdict
from dataclasses import dataclass
import math
import re

SIGNS = {'=', '<=', '>', '>='}
MISSING = {'', 'na', 'nan', 'none', 'nr', '—', '-'}


def number(value):
    return '' if value is None else f'{value:g}'


@dataclass(frozen=True)
class MIC:
    raw: str
    operator: str = ''
    raw_value: float | None = None
    value: float | None = None
    conversion: str = ''
    reason: str = ''

    @property
    def valid(self):
        return not self.reason


def parse_mic(token):
    """Retain raw report; normalize the 0.12 dilution display convention."""
    raw = str(token)
    stripped = raw.strip()
    if stripped.lower() in MISSING:
        return MIC(raw, reason='reference_missing')
    match = re.fullmatch(r'(<=|>=|≤|≥|<|>|=)?\s*([+]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)', stripped)
    if not match:
        return MIC(raw, reason='unrecognized_or_ambiguous_report')
    operator = {'≤': '<=', '≥': '>='}.get(match[1], match[1]) or '='
    value = float(match[2])
    if not math.isfinite(value) or value <= 0:
        return MIC(raw, operator, value, reason='nonpositive_or_nonfinite_mic')
    if operator not in SIGNS:
        return MIC(raw, operator, value, reason='unsupported_qualifier')
    # Keep the original parsed token separate from its normalized dilution value.
    normalized = 0.125 if value == 0.12 else value
    return MIC(raw, operator, value, normalized,
               'standard_dilution_display_0.12_to_0.125' if normalized != value else '')


def compare_offscale(test_value, test_sign, reference_value, reference_sign):
    """Off-scale difference and essential agreement, test minus reference.

    Intermediate log2 values are rounded to one decimal. Essential agreement
    is a separate rule, not abs(difference)<=1 (e.g. 8 versus >=2).
    """
    if test_sign not in SIGNS or reference_sign not in SIGNS:
        raise ValueError('Unsupported MIC qualifier')
    if not all(math.isfinite(v) and v > 0 for v in (test_value, reference_value)):
        raise ValueError('MICs must be finite and positive')
    test = test_value * (2 if test_sign == '>' else 1)
    reference = reference_value * (2 if reference_sign == '>' else 1)
    tlog, rlog = round(math.log2(test), 1), round(math.log2(reference), 1)
    zero = (
        (test_sign == '<=' and reference_sign == '<=')
        or (test_sign in {'>', '>='} and reference_sign == '>')
        or (test_sign == '<=' and rlog < tlog)
        or (reference_sign == '<=' and tlog < rlog)
        or (reference_sign in {'>', '>='} and tlog > rlog)
        or (test_sign in {'>', '>='} and rlog > tlog)
    )
    difference = 0.0 if zero else round(tlog - rlog, 1)
    ea = (
        (reference_sign == '>' and test >= reference)
        or (test_sign in {'>', '>='} and reference > test)
        or (reference_sign == '<=' and test < reference)
        or (test_sign == '<=' and reference < test)
        or abs(tlog - rlog) <= 1
    )
    return difference, ea


def aggregate(values, rule):
    if any(v not in (0, 1) for v in values):
        raise ValueError('Expected binary predictions')
    if rule == 'triplicate_majority':
        if len(values) != 3:
            raise ValueError('Triplicate majority requires exactly three predictions per concentration')
        return int(sum(values) >= 2)
    if rule != 'replicate_consensus':
        raise ValueError('Unknown replicate rule')
    if not values:
        return None
    return values[0] if len(set(values)) == 1 else 'mixed'


def classify_sequence(concentrations, calls, control, skip_policy='strict'):
    if skip_policy not in ('strict', 'highest_tested'):
        raise ValueError('Unknown skipped-concentration policy')
    if (not concentrations or len(concentrations) != len(calls)
            or any(not math.isfinite(c) or c <= 0 for c in concentrations)
            or any(a >= b for a, b in zip(concentrations, concentrations[1:]))):
        raise ValueError('Concentrations must be finite, positive, distinct and ascending')
    if any(v not in (0, 1, 'mixed') for v in calls) or control not in (0, 1, None, 'mixed'):
        raise ValueError('Invalid prediction state')
    growth = [i for i, v in enumerate(calls) if v == 1]
    last = growth[-1] if growth else None
    skipped = [c for i, (c, v) in enumerate(zip(concentrations, calls))
               if last is not None and i < last and v == 0]
    reasons = []
    if control != 1:
        reasons.append({None: 'predicted_control_missing', 0: 'predicted_control_no_growth',
                        'mixed': 'predicted_control_replicates_discordant'}[control])
    if 'mixed' in calls:
        reasons.append('predicted_exposed_replicates_discordant')
    if len(skipped) > 1 and skip_policy == 'strict':
        reasons.append('multiple_skipped_concentrations')
    op, value = '', None
    if not reasons:
        if skipped and skip_policy == 'highest_tested':
            op, value = '=', concentrations[-1]
        elif last is None:
            op, value = '<=', concentrations[0]
        elif last == len(concentrations) - 1:
            op, value = '>', concentrations[-1]
        else:
            op, value = '=', concentrations[last + 1]
    rule = ('not_reportable' if reasons else 'skipped_highest_tested' if skipped and skip_policy == 'highest_tested'
            else 'all_exposed_no_growth_lower_limit' if last is None
            else 'highest_tested_growth_upper_limit' if last == len(concentrations)-1
            else 'next_measured_after_highest_growth')
    return {'predicted_reportable': not reasons, 'predicted_mic_operator': op,
            'predicted_mic_value_ug_ml': value if value is not None else '',
            'predicted_mic': ('' if op == '=' else op) + number(value) if not reasons else 'NR',
            'prediction_rule': ('single_skip_' if len(skipped) == 1 and not reasons and skip_policy == 'strict' else '') + rule,
            'prediction_NR_reasons': ';'.join(reasons),
            'prediction_skips': len(skipped) if 'mixed' not in calls else '',
            'skipped_concentrations_ug_ml': ';'.join(map(number, skipped)) if 'mixed' not in calls else ''}


def derive_prediction(wells, rule, skip_policy='strict'):
    """The interface takes only (actual concentration, predicted call) pairs."""
    by_concentration = defaultdict(list)
    for concentration, prediction in wells:
        if not math.isfinite(concentration) or concentration < 0:
            raise ValueError('Invalid actual concentration')
        by_concentration[concentration].append(prediction)
    controls = by_concentration.pop(0.0, [])
    control = aggregate(controls, rule) if controls else None
    concentrations = sorted(by_concentration)
    calls = [aggregate(by_concentration[c], rule) for c in concentrations]
    return {**classify_sequence(concentrations, calls, control, skip_policy),
            'predicted_control_state': 'missing' if control is None else str(control),
            'predicted_control_growth_n': sum(controls), 'n_control_wells': len(controls),
            'tested_concentrations_ug_ml': ';'.join(map(number, concentrations)),
            'exposed_prediction_sequence': ';'.join(map(str, calls)),
            'replicate_counts': ';'.join(str(len(by_concentration[c])) for c in concentrations)}


def reference_from_tokens(tokens):
    """Conflicting values cannot be chosen to improve agreement."""
    parsed = [parse_mic(t) for t in tokens if str(t).strip().lower() not in MISSING]
    if not parsed:
        return MIC('', reason='reference_missing')
    invalid = [p for p in parsed if not p.valid]
    if invalid:
        return MIC(';'.join(sorted(set(p.raw for p in parsed))), reason=invalid[0].reason)
    # Raw numeric equality before normalization: do not silently collapse conflicts.
    if len({(p.operator, p.raw_value) for p in parsed}) != 1:
        return MIC(';'.join(sorted(set(p.raw for p in parsed))), reason='conflicting_reference_values')
    p = parsed[0]
    return MIC(';'.join(sorted(set(x.raw for x in parsed))), p.operator,
               p.raw_value, p.value, p.conversion)
