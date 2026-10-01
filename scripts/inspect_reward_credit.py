"""Independent Decimal arithmetic over the fixed saved bank; no project imports."""
import hashlib
import json
from decimal import Decimal as D
from decimal import getcontext
from pathlib import Path

getcontext().prec = 60
root = Path(__file__).resolve().parents[1]
pins = {
    'financial_training_v1.json': '5cb85943a209183492df813cb63f372f05c9257bba254382957d41183a69cf17',
    'financial_linkage_training_v1.json': 'e9143fb33680317cc8312410b7b078a849a9d26d7824e7770f29b7230fd3c80d',
}
sources = {}
for name, digest in pins.items():
    raw = (root / 'results' / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    sources[name] = json.loads(raw, parse_float=D)
result_raw = (root / 'results/reward_credit_v1.json').read_bytes()
result = json.loads(result_raw, parse_float=D)
assert result['status'] == 'verified_saved_reward_credit'
assert result['input_bytes_verified'] is True
assert len(result['runs']) == 4
checks = 0
maximum_error = D(0)


def same(actual, expected):
    global checks, maximum_error
    a, e = D(actual), D(expected)
    assert a.is_finite() and e.is_finite()
    error = abs(a - e)
    assert error <= max(D('1e-12'), D('1e-12') * max(abs(a), abs(e))), (actual, expected)
    maximum_error = max(maximum_error, error)
    checks += 1


def direct_loo(values):
    return [value - sum(values[:i] + values[i + 1:]) / D(3) for i, value in enumerate(values)]


summaries = []
for run_out, (name, role) in zip(result['runs'], [
    ('financial-rloo23-v1', 'correct'), ('financial-rloo29-v1', 'correct'),
    ('financial-placebo23-v1', 'placebo'), ('financial-placebo29-v1', 'placebo')
]):
    assert run_out['run_id'] == name and run_out['role'] == role
    original = role == 'correct'
    document = sources['financial_training_v1.json' if original else 'financial_linkage_training_v1.json']
    report = document['runs'][name]['training-report.json' if original else 'training_report']
    groups = report['groups']
    assert len(groups) == len(run_out['groups']) == 16
    summary = {'groups': 16, 'samples': 64, 'usable_samples': 0, 'active_validity_groups': 0,
               'all_usable_groups': 0, 'all_failed_groups': 0, 'optimizer_step_groups': 0,
               'constant_reward_groups': 0, 'ic_credit_groups_strict': 0}
    absent_validity_updates = 0
    l1_sums = {c: D(0) for c in 'RVC'}
    squared_sums = {c: D(0) for c in ('R', 'V', 'C', 'cross_2VC')}
    surrogate_sums = {c: D(0) for c in 'RVC'}
    for index, (group, saved) in enumerate(zip(groups, run_out['groups'])):
        assert group['group'] == saved['group'] == index
        assert saved['task_id'] == group['task']['task_id']
        samples = group['samples']
        assert len(samples) == 4
        true = {'R': [D(s['outcome']['reward']) for s in samples],
                'V': [D(int(s['outcome']['status'] == 'ok')) for s in samples],
                'C': [D(s['outcome']['oriented_future_ic']) if s['outcome']['status'] == 'ok' else D(0)
                      for s in samples]}
        p = list(range(4)) if original else group['permutation']
        assert saved['permutation'] == p
        assigned = {c: [v[i] for i in p] for c, v in true.items()}
        advantages = {c: direct_loo(v) for c, v in assigned.items()}
        logps = [D(s['recomputed_preupdate_completion_logp']) for s in samples]
        for i in range(4):
            same(true['R'][i], D('-1.01') + true['V'][i] + true['C'][i])
            same(group['advantages'][i], advantages['R'][i])
            same(saved['samples'][i]['preupdate_logp'], logps[i])
        for c in 'RVC':
            for i in range(4):
                same(saved['true_components'][c][i], true[c][i])
                same(saved['assigned_components'][c][i], assigned[c][i])
                same(saved['advantages'][c][i], advantages[c][i])
            l1 = sum(abs(v) for v in advantages[c])
            squared = sum(v * v for v in advantages[c])
            surrogate = -sum(a * lp for a, lp in zip(advantages[c], logps)) / D(4)
            same(saved['coefficient_l1'][c], l1)
            same(saved['coefficient_squared'][c], squared)
            same(saved['surrogate'][c], surrogate)
            l1_sums[c] += l1
            squared_sums[c] += squared
            surrogate_sums[c] += surrogate
        cross = 2 * sum(v * c for v, c in zip(advantages['V'], advantages['C']))
        same(saved['coefficient_squared']['cross_2VC'], cross)
        squared_sums['cross_2VC'] += cross
        validity_active = len(set(true['V'])) > 1
        summary['usable_samples'] += int(sum(true['V']))
        summary['active_validity_groups'] += validity_active
        summary['all_usable_groups'] += all(true['V'])
        summary['all_failed_groups'] += not any(true['V'])
        summary['optimizer_step_groups'] += group['optimizer_step']
        summary['constant_reward_groups'] += len(set(assigned['R'])) == 1
        summary['ic_credit_groups_strict'] += any(v != 0 for v in advantages['C'])
        absent_validity_updates += group['optimizer_step'] and not validity_active
        assert saved['active_validity_credit'] == validity_active
        assert saved['optimizer_step'] == group['optimizer_step']
        for first in ('R', 'V'):
            # The display contract uses strict signs of retained floating values.
            # Their arithmetic was checked above against direct Decimal means;
            # do not replace a tiny retained sign with a rounded exact-zero claim.
            pairs = list(zip(saved['advantages'][first], saved['advantages']['C']))
            opposite = sum((a < 0 < c) or (c < 0 < a) for a, c in pairs)
            zeros = sum(a == 0 or c == 0 for a, c in pairs)
            assert saved['sign_opposition'][f'{first}_versus_C_strict'] == opposite
            assert saved['sign_opposition'][f'{first}_versus_C_zero_cases'] == zeros
    for key, value in summary.items():
        assert run_out['summary'][key] == value, (name, key)
    for key, values in [('coefficient_l1_sums', l1_sums), ('coefficient_squared_sums', squared_sums),
                        ('surrogate_sums', surrogate_sums)]:
        for c, value in values.items():
            same(run_out['summary'][key][c], value)
    summaries.append({'run_id': name, **summary, 'updates_without_direct_validity_credit': absent_validity_updates})
print(json.dumps({'result': 'PASS', 'method': '60-digit Decimal, direct other-three mean; no project imports',
                  'numeric_comparisons': checks, 'maximum_absolute_error': str(maximum_error),
                  'result_sha256': hashlib.sha256(result_raw).hexdigest(),
                  'summaries': summaries}, indent=2))
