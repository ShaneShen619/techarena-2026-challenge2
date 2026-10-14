"""Inspect frozen outputs without refitting; optionally verify clean remote delivery."""
import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
sys.path[:0] = [str(STUDY / 'src'), str(STUDY / 'stage_3')]
from audit5b import clean_json, dump, neff, physical_charge
from common5b import H
from edata import anchor_curve, ck0_curve
from emodel import OCP, charge_residual, q_c20
from profile_pack import quantities, stoich, voltage, individual_limits
from run_profiles import combinations, simulate_batches
from v2 import anchors_by_checkup

PARAMS = ['Qn', 'Qp', 'QLi', 'theta_n0', 'R', 'h']
BRANCH = 'exp/phase2-r5b-electrode-model-20261014'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def first_commit(path):
    commits = git('log', '--reverse', '--format=%H', '--', str(path.relative_to(ROOT))).splitlines()
    return commits[0] if commits else None


def grids(center, low, high):
    offsets = np.r_[-64., -32., -16., -8., -4., -2., -1., -.5, -.25,
                   .25, .5, 1., 2., 4., 8., 16., 32., 64.]
    a = np.unique(np.r_[np.arange(low, high + .01, 10.), center, center + offsets])
    return a[(a >= low) & (a <= high)]


def equal_grid(actual, expected):
    a = np.sort(np.asarray(actual, float))
    b = np.sort(expected)
    return len(a) == len(b) and np.allclose(a, b, atol=1e-7, rtol=0)


def protocol_order(post):
    evaluations = {
        'stage_1': 'stage_1/outputs/S1_synthetic.csv',
        'stage_2': 'stage_2/outputs/S2_ck0_check.json',
        'independent': 'independent/outputs/audit.json',
        'stage_3': 'stage_3/outputs/S3_exit.json',
        'stage_4': 'stage_4/outputs/S4_exit.json',
        'stage_5': 'stage_5/outputs/S5_completion.json',
        'stage_6': 'FINAL_REPORT.md',
    }
    result = []
    for folder, evaluation in evaluations.items():
        p = STUDY / folder / 'protocol.json'
        sh = p.with_suffix('.sha256')
        assert sh.read_text().split()[0] == hashlib.sha256(p.read_bytes()).hexdigest(), p
        pc, sc = first_commit(p), first_commit(sh)
        ec = first_commit(STUDY / evaluation)
        assert pc and sc and pc == sc, folder
        assert git('show', f'{pc}:{p.relative_to(ROOT)}') == p.read_text().strip()
        assert git('show', f'{sc}:{sh.relative_to(ROOT)}') == sh.read_text().strip()
        if ec:
            assert pc != ec
            assert subprocess.run(['git', 'merge-base', '--is-ancestor', pc, ec], cwd=ROOT).returncode == 0
        else:
            assert folder == 'stage_6' and not post
        result.append({'stage': folder, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                       'protocol_commit': pc, 'evaluation_commit': ec,
                       'evaluation_order': 'verified' if ec else 'pending final evaluation commit'})
    return result


def scientific_audit():
    synthetic = pd.read_csv(STUDY / 'stage_1/outputs/S1_synthetic.csv')
    synth_summary = json.loads((STUDY / 'stage_1/outputs/S1_synthetic_summary.json').read_text())
    assert len(synthetic) == 30 and synthetic.valid.all()
    recovery = {}
    for quantity, prefix in [('Q_C20', 'Q_C20'), ('beta_E', 'beta'), ('Q_fc', 'Q_fc')]:
        assert np.isfinite(synthetic[[prefix + '_fit', prefix + '_true']].to_numpy()).all()
        recovery[quantity] = float(np.median(abs(synthetic[prefix + '_fit'] - synthetic[prefix + '_true'])))
    recovery['LLI'] = float(np.median(abs(synthetic.LLI_fit - synthetic.LLI)))
    recovery['LAM_NE fraction'] = float(np.median(abs(synthetic.LAMNE_fit - synthetic.LAM_NE)) * 100)
    recovery['LAM_PE fraction'] = float(np.median(abs(synthetic.LAMPE_fit - synthetic.LAM_PE)) * 100)
    stored_recovery = pd.read_csv(HERE / 'outputs/synthetic_recovery_all_modes.csv').set_index('Quantity')['Median absolute recovery error']
    for name, value in recovery.items():
        assert np.isclose(stored_recovery[name], value, atol=1e-10)
    assert (recovery['Q_C20'] <= .2 and recovery['beta_E'] <= .1) == synth_summary['pass']
    fits = pd.read_csv(STUDY / 'stage_3/outputs/S3_main_fits.csv')
    profiles = pd.read_csv(STUDY / 'stage_3/outputs/S3_LLI_profile_fits.csv')
    material = pd.read_csv(STUDY / 'stage_5/outputs/S5_material_profiles.csv')
    components = pd.read_csv(STUDY / 'stage_5/outputs/S5_health_component_intervals.csv')
    assert len(fits) == 32 and len(components) == 96
    assert set(map(tuple, fits[['anchor', 'cell']].to_numpy())) == {(j, c) for j in range(8) for c in range(1, 5)}
    ocp = OCP('main')
    for p in (STUDY / 'ocp').glob('*.csv'):
        a = pd.read_csv(p).to_numpy()
        assert a.shape == (1001, 2) and np.isfinite(a).all()
        assert np.allclose(a[:, 0], np.linspace(0, 1, 1001), atol=1e-12, rtol=0)
        assert np.all(np.diff(a[:, 1]) <= 1e-12)
    op = H.full_op()
    anchors = anchors_by_checkup(H.full_charges(op), H.CK)
    grids_checked, physical_checked = 0, 0
    for row in fits.itertuples():
        q, current, volts, _, qt = anchor_curve(op, anchors[row.anchor])
        x = np.array([getattr(row, n) for n in PARAMS])
        assert physical_charge(x, qt, ocp)
        residual = charge_residual(x, q, current, volts[:, row.cell - 1], ocp)[:-1]
        effective, rho = neff(residual)
        assert np.isclose(effective, row.n_eff, atol=1e-6, rtol=1e-6)
        assert np.isclose(np.sqrt(np.mean(residual**2)), row.rms_mV, atol=1e-7)
        assert 1 <= row.n_eff <= row.n
        sub = profiles[(profiles.anchor == row.anchor) & (profiles.cell == row.cell)]
        assert equal_grid(sub.QLi_fixed, grids(row.QLi, 50, 250))
        minimum = min(row.cost, sub.loc[sub.physical_valid, 'cost'].min())
        statistic = np.maximum(0., 2 * (sub.cost - minimum) / max(2., row.rms_mV)**2 * row.n_eff / row.n)
        assert np.allclose(statistic, sub.profile_statistic, atol=1e-8)
        assert np.array_equal(sub.pack95_bonferroni, sub.physical_valid & (statistic <= chi2.ppf(1 - .05 / 4, 1)))
        component = components[(components.anchor == row.anchor) & (components.cell == row.cell) & (components.parameter == 'QLi')].iloc[0]
        accepted = sub[sub.physical_valid & (statistic <= chi2.ppf(.975, 1))].QLi
        assert np.allclose([component.lower, component.upper], [accepted.min(), accepted.max()])
        for r in sub.itertuples():
            assert r.physical_valid == physical_charge(np.array([getattr(r, n) for n in PARAMS]), qt, ocp)
            physical_checked += 1
        assert 2 * (row.cost - minimum) / max(2., row.rms_mV)**2 * row.n_eff / row.n <= chi2.ppf(1 - .05 / 4, 1)
        grids_checked += 1
        for param in ['Qn', 'Qp']:
            sub = material[(material.anchor == row.anchor) & (material.cell == row.cell) & (material.parameter == param)]
            assert equal_grid(sub.fixed_value, grids(getattr(row, param), 60, 200))
            minimum = min(row.cost, sub.loc[sub.physical_valid, 'cost'].min())
            stat = np.maximum(0., 2 * (sub.cost - minimum) / max(2., row.rms_mV)**2 * row.n_eff / row.n)
            assert np.allclose(stat, sub.profile_statistic, atol=1e-8)
            assert np.array_equal(sub.accepted97p5, sub.physical_valid & (stat <= chi2.ppf(.975, 1)))
            for r in sub.itertuples():
                assert r.physical_valid == physical_charge(np.array([getattr(r, n) for n in PARAMS]), qt, ocp)
                physical_checked += 1
            accepted = sub[sub.accepted97p5].fixed_value
            ci = components[(components.anchor == row.anchor) & (components.cell == row.cell) & (components.parameter == param)].iloc[0]
            assert np.allclose([ci.lower, ci.upper], [accepted.min(), accepted.max()])
            grids_checked += 1
    assert grids_checked == 96 and physical_checked == len(profiles) + len(material)
    print('Verified all96 grids and residual-effective statistics; reconstructing capacity witnesses', flush=True)
    ck0 = json.loads((STUDY / 'stage_2/outputs/S2_ck0_check.json').read_text())
    etas = ck0['main_anchor0']['ck0_fit']['eta_dis']
    packs = pd.read_csv(STUDY / 'stage_3/outputs/S3_pack_intervals.csv')
    reference = fits[fits.anchor == 1][PARAMS].to_numpy()
    reference_pools = [profiles[(profiles.anchor == 1) & (profiles.cell == c) & profiles.pack95_bonferroni][PARAMS].to_numpy() for c in range(1, 5)]
    reference_points, _, _ = combinations(reference_pools, reference, 20261016)
    reference_values = simulate_batches(reference_points, ocp, etas, reference)
    ref_depths = reference_values['D_prog'][np.isfinite(reference_values['D_prog'])]
    witnesses = []
    for j in range(8):
        best = fits[fits.anchor == j][PARAMS].to_numpy()
        pools = [profiles[(profiles.anchor == j) & (profiles.cell == c) & profiles.pack95_bonferroni][PARAMS].to_numpy() for c in range(1, 5)]
        points, exact, count = combinations(pools, best, 20261015 + j)
        values = simulate_batches(points, ocp, etas)
        expected = packs[packs.anchor == j].iloc[0]
        assert len(points) == expected.combinations_evaluated and count == expected.combinations_total
        finite = np.flatnonzero(np.isfinite(values['Q_C20']))
        assert (~np.isfinite(values['Q_C20'])).sum() == expected.Q_C20_missing
        health = simulate_batches(points, ocp, etas, reference)
        depths = health['D_prog'][np.isfinite(health['D_prog'])]
        denominator = [depths.min() - ref_depths.max(), depths.max() - ref_depths.min()]
        assert np.allclose(denominator, [expected.denominator_lower, expected.denominator_upper], atol=1e-8)
        assert denominator[0] <= 0 <= denominator[1] and expected.denominator_includes_zero
        charge = values['Q_fc'][np.isfinite(values['Q_fc'])]
        if len(charge):
            assert np.allclose([charge.min() - expected.Q_fc_obs, charge.max() - expected.Q_fc_obs],
                               [expected.Q_fc_error_lower, expected.Q_fc_error_upper], atol=1e-7)
        if j == 0:
            assert not len(finite)
            continue
        low, high = finite[np.argmin(values['Q_C20'][finite])], finite[np.argmax(values['Q_C20'][finite])]
        assert np.allclose([values['Q_C20'][low], values['Q_C20'][high]],
                           [expected.Q_C20_lower_witness, expected.Q_C20_upper_witness], atol=1e-7, rtol=0)
        assert values['Q_C20'][high] - values['Q_C20'][low] > .6
        for label, index in [('lower', low), ('upper', high)]:
            cells = points[index]
            end = values['Q_fc'][index]
            root = values['Q_C20'][index]
            tn0, tp0 = stoich(cells[None], np.array([0.]))
            tn1, tp1 = stoich(cells[None], np.array([end]))
            tnr, tpr = stoich(cells[None], np.array([end - root]))
            assert np.all((np.r_[tn0, tp0, tn1, tp1, tnr, tpr] >= 0) & (np.r_[tn0, tp0, tn1, tp1, tnr, tpr] <= 1))
            pack_v = float((voltage(cells[None], np.array([end - root]), ocp) - np.array(etas)[None]).sum() - .003)
            assert abs(pack_v - 11.2) < 1e-8
            cell_evidence = []
            for c in range(4):
                pool = pools[c]
                assert np.any(np.all(np.isclose(pool, cells[c], atol=1e-7, rtol=0), axis=1)) or np.allclose(cells[c], best[c], atol=1e-7, rtol=0)
                cell_evidence.append({'cell': c + 1, 'parameters': dict(zip(PARAMS, cells[c])),
                                      'theta_n_start_end_root': [tn0[0, c], tn1[0, c], tnr[0, c]],
                                      'theta_p_start_end_root': [tp0[0, c], tp1[0, c], tpr[0, c]]})
            witnesses.append({'anchor': j, 'side': label, 'Q_C20_Ah': root, 'Q_fc_Ah': end,
                              'pack_root_V': pack_v, 'cells': cell_evidence,
                              'status': 'admissible witness; full nominal box not exhaustively bounded'})
    ref = H.load_dataset(H.DATA).reference_discharge
    d, volts, c_pack = ck0_curve(ref)
    assert np.isclose(c_pack, -.003)
    ck0_checks = {}
    for name, result in ck0.items():
        cells = np.asarray(result['ref_fit'])
        starts = np.asarray(result['ck0_fit']['theta_n_start'])
        hp = [tuple(np.r_[cells[c, :3], starts[c]]) for c in range(4)]
        root, _ = q_c20(hp, result['ck0_fit']['eta_dis'], ocp, q_max=125.)
        assert np.isclose(root, result['Q_C20_sim'], atol=1e-8)
        tail = d > 85.412
        rms = [np.sqrt(np.mean((ocp.ocv(-d[tail], hp[c]) - result['ck0_fit']['eta_dis'][c] - volts[tail, c])**2)) * 1000 for c in range(4)]
        assert np.allclose(rms, result['tail_rms_mV'], atol=1e-8)
        credible = abs(root - 100.41) <= .5 and np.max(np.abs(result['step_diff_Ah'])) <= 1
        assert credible == result['credible']
        ck0_checks[name] = {'root_Ah': root, 'tail_rms_mV': rms, 'scalar_credible': credible}
    trajectory = pd.read_csv(STUDY / 'stage_3/outputs/S3_LLI_trajectory.csv')
    correlation = trajectory[trajectory.anchor >= 1][['LLI_point', 'pack_start_V']].corr().iloc[0, 1]
    assert np.isclose(correlation, json.loads((STUDY / 'stage_3/outputs/S3_exit.json').read_text())['LLI_start_voltage_correlation'])
    source = (STUDY / 'stage_2/run_2.py').read_text()
    assert 'WIN = (5.0, D_END - 15.0)' in source and 'dd, vv = d[w][::10], v[w][::10]' in source
    invalid = fits[fits.anchor == 1][PARAMS].to_numpy()[None]
    invalid[:, 0, 3] = 1.2
    assert np.isnan(quantities(invalid, ocp, etas)['Q_fc'][0])
    negative_r = fits[fits.anchor == 0][PARAMS].to_numpy()[None]
    assert negative_r[:, :, 4].sum() < 0 and np.isnan(quantities(negative_r, ocp, etas)['Q_fc'][0])
    modes = pd.read_csv(STUDY / 'stage_5/outputs/S5_modes_per_cell.csv')
    assert len(modes) == 32 and modes.identifiability.str.contains('unidentified').all()
    for r in modes.itertuples():
        main = fits[(fits.anchor == r.anchor) & (fits.cell == r.cell)].iloc[0]
        reference = fits[(fits.anchor == 0) & (fits.cell == r.cell)].iloc[0]
        for mode, param in [('LLI', 'QLi'), ('LAM_NE', 'Qn'), ('LAM_PE', 'Qp')]:
            assert np.isclose(getattr(r, mode + '_point'), reference[param] - main[param])
            ri = components[(components.anchor == 0) & (components.cell == r.cell) & (components.parameter == param)].iloc[0]
            ci = components[(components.anchor == r.anchor) & (components.cell == r.cell) & (components.parameter == param)].iloc[0]
            expected = [0., 0.] if r.anchor == 0 else [ri.lower - ci.upper, ri.upper - ci.lower]
            assert np.allclose([getattr(r, mode + '_lower95'), getattr(r, mode + '_upper95')], expected)
    limits = pd.read_csv(STUDY / 'stage_5/outputs/S5_limiting_cells.csv')
    coverage = pd.read_csv(STUDY / 'stage_5/outputs/S5_recovery_coverage.csv')
    assert list(limits.k) == list(range(8)) and list(coverage.anchor) == list(range(8))
    assert (limits[limits.k > 0].state_anchor == limits[limits.k > 0].k - 1).all()
    assert not coverage.crosses_step_region.any() and (coverage.charge_depth_Ah < 45).all()
    assert not limits.loc[limits.k == 1, 'root_available'].iloc[0]
    for row in limits.itertuples():
        if row.k == 0:
            cells = np.asarray(ck0['main_anchor0']['ref_fit']).copy()
            cells[:, 3] = ck0['main_anchor0']['ck0_fit']['theta_n_start']
            end = 0.
            capacity = ck0['main_anchor0']['Q_C20_sim']
            limiting = ck0['main_anchor0']['limiting_cell_at_root']
        else:
            cells = fits[fits.anchor == row.state_anchor][PARAMS].to_numpy()
            values = quantities(cells[None], ocp, etas)
            end, capacity, limiting = values['Q_fc'][0], values['Q_C20'][0], values['limiting'][0]
        if not np.isfinite(capacity):
            assert not row.root_available
            continue
        assert np.isclose(row.Q_C20_model_Ah, capacity) and row.minimum_voltage_cell_at_pack_root == limiting
        individual, domain = individual_limits(cells, end, etas, ocp)
        finite = np.flatnonzero(np.isfinite(individual))
        order = finite[np.argsort(individual[finite])]
        dorder = np.argsort(domain)
        assert row.first_2p8V_cell == order[0] + 1
        assert np.isclose(row.second_2p8V_gap_Ah, individual[order[1]] - individual[order[0]])
        assert row.first_stoichiometry_end_cell == dorder[0] + 1
        assert np.isclose(row.second_stoichiometry_end_gap_Ah, domain[dorder[1]] - domain[dorder[0]])
    baseline = pd.read_csv(STUDY / 'stage_4/outputs/S4_baseline_reference_long.csv')
    metric = H.metrics(baseline)
    stored = pd.read_csv(STUDY / 'stage_4/outputs/S4_baseline_metrics.csv')
    for col in ['MAE', 'MAX', 'RMSE', 'CK2_7_MAE']:
        assert np.allclose(metric[col], stored[col], atol=1e-10)
    pseudo = baseline[(baseline.delta == .4) & (baseline.scenario != 'real') & (baseline.k >= 3)].groupby(['model', 'scenario']).err_pp.apply(lambda e: e.abs().mean())
    stored_pseudo = pd.read_csv(STUDY / 'stage_4/outputs/S4_baseline_pseudo_decision_scope.csv').set_index(['model', 'scenario']).MAE
    assert np.allclose(pseudo, stored_pseudo)
    baseline0 = json.loads((STUDY / 'stage0/reproduce.json').read_text())
    for model in ['M4', 'V2']:
        row = metric[(metric.model == model) & (metric.scenario == 'real') & (metric.delta == .4)].iloc[0]
        assert np.isclose(row.MAE, baseline0[model]['MAE'], atol=1e-14)
        assert np.isclose(row.MAX, baseline0[model]['MAX'], atol=1e-14)
    provenance = json.loads((HERE / 'outputs/ocp_provenance_verified.json').read_text())
    for name, result in provenance['tables'].items():
        assert hashlib.sha256((STUDY / 'ocp' / name).read_bytes()).hexdigest() == result['csv_sha256']
        assert result['max_tabulation_roundoff_V'] <= 5.1e-9
    assert hashlib.sha256((STUDY / 'ocp/PyBaMM_LICENSE.txt').read_bytes()).hexdigest() == provenance['license_sha256']
    assert (STUDY / 'stage_5/outputs/S5_degradation_modes.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    exit3 = json.loads((STUDY / 'stage_3/outputs/S3_exit.json').read_text())
    exit4 = json.loads((STUDY / 'stage_4/outputs/S4_exit.json').read_text())
    assert not exit3['stage4_proceed'] and exit4['E1'] == 'not evaluated' and exit4['E3'] == 'not produced'
    assert not (STUDY / 'candidate_model').exists()
    for p in STUDY.rglob('*.py'):
        if 'cache' not in p.relative_to(STUDY).parts:
            ast.parse(p.read_text(), filename=str(p))
    return clean_json({'synthetic_states': 30, 'synthetic_recovery_quantities_verified': recovery,
                       'fixed_grids_verified': grids_checked, 'profile_validity_flags_verified': physical_checked,
                       'main_fit_rows_verified': len(fits), 'capacity_witness_endpoints': len(witnesses),
                       'CK0': ck0_checks, 'mode_rows_verified': len(modes), 'nominal_component_intervals': len(components),
                       'limiting_rows': len(limits), 'recovery_rows': len(coverage),
                       'recovery_fit_supported': False, 'baseline_metrics_recomputed': True,
                       'pseudo_decision_scope_excludes_CK2': True,
                       'registered_stage4_exit_verified': True,
                       'original_synthetic_current_replay_requirement': 'deviation; surrogate only, not validated as exact replay',
                       'legacy_hard_domain_rejection': 'deviation in preserved stage1/2; stage3+ helpers reject invalid targets'}), clean_json(witnesses)


def documents_and_isolation():
    changed = git('diff', '--name-only', 'a6bc61f', 'HEAD').splitlines()
    assert all(p.startswith(str(STUDY.relative_to(ROOT)) + '/') for p in changed), changed
    for name in ['FINAL_REPORT.md', 'README.md', 'notes/STATUS.md', 'stage_1/REPORT_VERIFIED.md']:
        text = (STUDY / name).read_text()
        assert text.index('<a id="en"></a>') < text.index('---') < text.index('<a id="zh"></a>')
        assert ('exposed-exploratory' in text or name == 'notes/STATUS.md')
    status = (STUDY / 'notes/STATUS.md').read_text()
    for j in range(7):
        assert f'Stage {j}:' in status
    assert 'Stage 4: skipped' in status and 'Stage 6: complete' in status
    assert (STUDY / 'ocp/PyBaMM_LICENSE.txt').is_file()
    for commit in git('rev-list', 'a6bc61f..HEAD').splitlines():
        assert git('show', '-s', '--format=%B', commit).endswith('Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'), commit
    return {'protected_tracked_paths_unchanged': True, 'bilingual_deliverables_verified': True,
            'all_commit_coauthors_verified': True, 'candidate_not_required_due_registered_exit': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--post-commit', action='store_true')
    args = parser.parse_args()
    assert git('branch', '--show-current') == BRANCH
    order = protocol_order(args.post_commit)
    docs = documents_and_isolation()
    if args.post_commit:
        assert not git('status', '--porcelain', '--', str(STUDY.relative_to(ROOT)))
        remote = git('ls-remote', '--heads', 'origin', BRANCH).split()[0]
        assert remote == git('rev-parse', 'HEAD')
        evidence = json.loads((HERE / 'outputs/completion_evidence.json').read_text())
        assert evidence['scientific']['capacity_witness_endpoints'] == 14
        print(json.dumps({'delivery_complete': True, 'HEAD': remote, 'branch': BRANCH,
                          'clean_study': True, 'protocol_commit_order': order, **docs}, indent=2))
    else:
        scientific, witnesses = scientific_audit()
        dump(HERE / 'outputs/capacity_witnesses.json', witnesses)
        dump(HERE / 'outputs/completion_evidence.json', {'scientific': scientific, 'protocol_commit_order': order,
                                                        'documents_and_isolation': docs,
                                                        'delivery': 'pending final commit/push and --post-commit read-only audit'})
        print(json.dumps(scientific, indent=2))
