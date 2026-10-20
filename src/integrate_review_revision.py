"""Code-to-method factual clarification and measured-data table integration.

Edits existing paragraphs only; no new article argument sections, primary
experiments, statistical families or author approvals are generated. Scientific
novelty and the final argument remain subject to independent author assessment.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from pathlib import Path
from .integrate_engineering_evidence import table

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/engineering_optimization'
OUT = PAPER / 'review_revision'
BASE = 'cfc2b94fa26a9cfdc6b1bcd2996d64da4e620222'
MARKER = '% Review response factual integration; independent author scientific review pending.'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def read_csv(name):
    with (OUT / name).open() as f:
        return list(csv.DictReader(f))

def generate():
    (PAPER / 'integrated_evidence').mkdir(parents=True, exist_ok=True)
    data = json.loads((OUT / 'analysis.json').read_text())
    original = json.loads((PAPER / 'budget_audit/analysis.json').read_text())
    method_rows = [
        ['Frozen state', 'Own 100-label history, fitted kernel, root candidate pool and first-action map', 'No alternative or probe response enters the frozen root fit'],
        ['Continuation', 'Same declared mean or EI rule and candidate-seed stream; each branch updates its own history', 'The first action is the intervention; this target differs from whole-policy runs'],
        ['Horizon', 'h0: first action; h5: five further common-rule actions', 'Six prefix requests per completed branch in this implementation'],
        ['Target / margin', 'Baseline-minus-alternative final incumbent divided by initial incumbent; primary margin 0.001', 'Better/tie/worse refers to the declared conditional h5 target'],
        ['Branch reuse', 'Same history, fitted kernel, action, continuation, context and seed stream', 'A same-point response may be shared more broadly; an equal utility does not merge branches'],
        ['Budget', 'Every branch-step request counts, including cache reads; primary B=18', 'Not the number of additional physical attempts'],
        ['Evidence output', 'Exact alias; measured h5 outcome; h0 proxy; budget-incomplete abstention', 'No partial trajectory certificate or general prediction guarantee'],
    ]
    methods = table('Implementation contract of the independent conditional audit. Values and information boundaries are taken from the frozen collection/replay code. This is a factual specification, not a new convergence result.',
                    'tab:review_contract', ['Object', 'Recorded implementation', 'Evidence boundary'], method_rows, [.16, .47, .37])
    (PAPER / 'integrated_evidence/review_method_records.tex').write_text(r'\Needspace{24\baselineskip}' + '\n' + methods)
    primary_rows = []
    for c in ['mean', 'ei']:
        truth = data['primary_truth_counts'][c]
        for mode in ['calibration', 'immediate', 'fixed_depth', 'adaptive']:
            r = next(x for x in original['primary'] if x['continuation'] == c and x['method'] == mode)
            primary_rows.append([c.upper(), f"{truth['better']}/{truth['tie']}/{truth['worse']}",
                mode.replace('_', ' '), f"{r['classified']}/25", r['classification_error'],
                r['total_audit_requests'], f"{r['mean_selection_regret_percent']:.4f}"])
    caption = ('Independent primary h5 record at margin 0.001. Truth B/T/W counts exclude exact baseline aliases and contain no better cases. '
               'Requests are charged across all 30 dependent states within ten seed blocks; they are not new physical solves. '
               'Completed-target errors are zero by direct measurement. Calibration is the constructed root-EI gate, not a published-method replication. '
               'This table was assembled from the frozen analysis outputs.')
    (PAPER / 'integrated_evidence/review_main_results.tex').write_text(
        r'\Needspace{18\baselineskip}' + '\n' + table(caption, 'tab:review_primary',
        ['Followup', 'Truth B/T/W', 'Rule', 'Classified', 'Errors', 'Requests', 'Selection loss (%)'],
        primary_rows, [.10, .14, .20, .14, .08, .10, .24]))
    seed_rows = []
    truth = read_csv('truth_composition.csv')
    blocks = read_csv('seed_block_results.csv')
    for b in range(10, 20):
        tr = {c: [r for r in truth if int(r['block']) == b and r['continuation'] == c] for c in ['mean', 'ei']}
        counts = {c: '/'.join(str(sum(int(r[k]) for r in tr[c])) for k in ['better', 'tie', 'worse']) for c in tr}
        topology = '/'.join(str(sum(int(r['classes']) == k for r in tr['mean'])) for k in [1, 2, 3])
        fixed = next(r for r in blocks if int(r['block']) == b and r['continuation'] == 'mean' and r['budget'] == '12' and r['method'] == 'fixed_depth')
        adaptive = next(r for r in blocks if int(r['block']) == b and r['continuation'] == 'mean' and r['budget'] == '12' and r['method'] == 'adaptive')
        seed_rows.append([b, fixed['contrasts'], topology, counts['mean'], counts['ei'], fixed['classified'], adaptive['classified']])
    supp = table('Complete seed-block composition. Each block has three dependent source states. K=1/2/3 counts states by exact branch-class count. The B=12 completion counts coincide for mean/EI continuation; blocks with zero contrasts remain in the record. No extra independent samples are introduced.',
                 'tab:review_seedblocks', ['Block', 'Contrasts', 'K=1/2/3', 'Mean B/T/W', 'EI B/T/W', 'Depth B12', 'Adaptive B12'], seed_rows,
                 [.08, .11, .15, .18, .18, .15, .15])
    sensitivity = data['summaries']
    assert all(r['errors'] == 0 and r['mean_state_selection_regret_percent'] == 0 for r in sensitivity)
    rows = [[r['continuation'].upper(), r['budget'], r['margin'], r['method'].replace('_', ' '),
             f"{r['classified']}/{r['contrasts']}", r['requests'], r['new_to_training_points'], r['abstained_worse']]
            for r in sensitivity]
    sensitivity_table = table('Post-review descriptive sensitivity at all previously specified budgets and margins. Fixed-depth-reversed changes only the nonbaseline class order. All displayed cells have zero measured-target errors and zero reported state-selection loss; these are not predictive guarantees. New points sum statewise points absent from that state\'s training archive, not globally unique paid solves. Original fixed-depth/adaptive cells match the published values.',
                  'tab:review_sensitivity', ['Followup', 'B', 'Margin', 'Order / rule', 'Classified', 'Requests', 'New points', 'Worse abstained'], rows,
                  [.10, .06, .10, .22, .12, .10, .10, .20])
    supp += sensitivity_table.replace(r'\fontsize{8.5}{10.5}', r'\fontsize{8.5}{10}')
    order_rows = []
    order = read_csv('order_sensitivity.csv')
    for c in ['mean', 'ei']:
        rr = [r for r in order if r['continuation'] == c and r['budget'] == '12' and float(r['margin']) == .001]
        forward = next(r for r in sensitivity if (r['continuation'], r['budget'], r['margin'], r['method']) == (c, 12, .001, 'fixed_depth'))
        reverse = next(r for r in sensitivity if (r['continuation'], r['budget'], r['margin'], r['method']) == (c, 12, .001, 'fixed_depth_reversed'))
        order_rows.append([c.upper(), sum(r['covered_branch_set_changed'] == 'True' for r in rr),
                           '17/25', f"{sum(int(r['min_abstained_worse']) for r in rr)}--{sum(int(r['max_abstained_worse']) for r in rr)}",
                           forward['new_to_training_points'], reverse['new_to_training_points'],
                           f"{max(float(r['max_selection_regret_percent']) for r in rr):.4f}"])
    supp += table('B=12, margin 0.001: exhaustively permuting the alternatives within each state preserves completion coverage but can change which target remains unmeasured. Both continuations change the covered class set in eight states; none contains a better primary target. This is retrospective replay, not independent confirmation. The capacity of 17 completed nonbaseline comparisons follows from the declared six-request full-branch contract.',
                  'tab:review_order', ['Followup', 'States changed', 'Classified', 'Worse missed range', 'Forward new points', 'Reverse new points', 'Max loss (%)'], order_rows,
                  [.10, .14, .13, .18, .15, .15, .15])
    grid = read_csv('paired_grid_ranges.csv')
    grid_rows = [[r['case'], r['state'].replace('gp_', '').replace('_shared_init', ''), r['control'].upper(),
                  r['original_class'], f"{float(r['min_relative_advantage_percent']):.4f}",
                  f"{float(r['max_relative_advantage_percent']):.4f}"] for r in grid if r['different_endpoints'] == 'True']
    assert len(grid_rows) == 8
    supp += table('Ranges of h5 baseline-minus-alternative paired differences for the eight differing endpoint pairs across six mesh/mapping contexts. Percentages are normalized by each context\'s initial incumbent compliance, not its baseline final endpoint. Six identical-endpoint ties are omitted here and retained in the original case table. These selected records neither add independent optimization samples nor certify a physical error bound.',
                  'tab:review_grid_ranges', ['Case', 'Existing state', 'Control', 'Class', 'Minimum (%)', 'Maximum (%)'], grid_rows,
                  [.08, .33, .12, .13, .17, .17])
    (PAPER / 'integrated_evidence/review_supp_records.tex').write_text(supp)
    inputs = {str((OUT / n).relative_to(ROOT)): sha((OUT / n).read_bytes()) for n in
              ['analysis.json', 'truth_composition.csv', 'seed_block_results.csv', 'order_sensitivity.csv', 'paired_grid_ranges.csv']}
    (OUT / 'table_inputs.json').write_text(json.dumps({'source_hashes': inputs, 'primary_truth_counts': data['primary_truth_counts'],
            'new_primary_experiments': False, 'author_review_pending': True}, indent=2) + '\n')

def apply():
    changes = {}
    backups = ROOT.parent / 'review_revision_before_cfc2b94'
    backups.mkdir(exist_ok=True)
    for name in ['EO_manuscript.tex', 'EO_supplementary.tex']:
        p = PAPER / name
        old = p.read_text()
        if MARKER in old:
            continue
        (backups / name).write_text(old)
        new = old
        edits = []
        def replace(before, after):
            nonlocal new
            assert new.count(before) == 1, (name, before[:70], new.count(before))
            new = new.replace(before, after)
            edits.append({'before': before, 'after': after})
        if name == 'EO_manuscript.tex':
            replace('Independent budget validation on ten new seed blocks finds no adaptive-allocation advantage.',
                    'Independent budget validation on ten new seed blocks finds no adaptive-allocation advantage and no better h5 outcomes at its primary margin.')
            replace('Freeze the surrogate, candidate generator, monitoring signal, management or acquisition rule, expensive objective, budget, and deterministic replay information. Output: protocol and information boundary.',
                    'Freeze the surrogate, candidate generator, monitoring signal, management or acquisition rule, expensive objective context, optimizer budget, audit-request budget, target horizon and margin, and deterministic replay information. In the independent conditional implementation, h0 is the first action and H=5 denotes five further common-rule actions. Output: protocol and information boundary.')
            replace('For exploration, region, restart, or stopping mechanisms, prespecify a delayed-value assessment where needed. Gate: an identifiable decision consequence and sufficient evidence to justify the next diagnostic expenditure; lower one-step improvement alone does not reject exploration.',
                    'For exploration, region, restart, or stopping mechanisms, prespecify a delayed-value assessment where needed. The implemented point-action intervention uses the same frozen training history, fitted kernel and first candidate pool, then the same declared continuation and candidate-seed stream with each branch updating its own history. For positive initial incumbent $m_{\\mathrm{init}}$, the recorded conditional target is $d_j(H)=[m_0(H)-m_j(H)]/m_{\\mathrm{init}}$, where $m_0$ is the baseline-branch incumbent. The primary implementation uses $H=5$ and margin $\\tau=0.001$. Gate: an identifiable decision consequence and sufficient evidence to justify the next diagnostic expenditure; lower one-step improvement alone does not reject exploration.')
            replace('Output: stage-wise audit record.\n\nThe framework can return a positive result.',
                    'Output: stage-wise audit record. The independent replay reports an exact branch alias, a measured target-horizon outcome, an h0 proxy, or an abstention because the target remains incomplete. For nonalias branches, better/tie/worse certification requires both baseline and alternative to reach h5; an immediate tie does not certify a later tie. Table~\\ref{tab:review_contract} maps this implementation to its recorded inputs and outputs.\n\n\\input{integrated_evidence/review_method_records.tex}\n\nThe framework can return a positive result.')
            replace('A comparison of optimizer endpoints at equal budgets does not establish that the audit itself saves evaluations.',
                    'A comparison of optimizer endpoints at equal budgets does not establish that the audit itself saves evaluations. In the independent replay, each branch-step request is charged, including a cache read; a completed branch needs $H+1=6$ requests. Its primary budget18 is per state. For $K$ exact branch classes, full-baseline/full-alternative reporting can complete at most $\\min(K-1,\\max(0,\\lfloor B/(H+1)\\rfloor-1))$ nonbaseline comparisons under this request contract. This elementary capacity does not bound additional physical solves or audits with a justified early certificate.')
            replace('Equivalent first actions do not make later policies equivalent, and labels must not be reused across changed physical conditions or noisy objectives without an additional justification.',
                    'Equivalent first actions do not make later policies equivalent, and labels must not be reused across changed physical conditions or noisy objectives without an additional justification. Whole conditional branches share a record only when the frozen history, fitted kernel, first action, objective context, continuation and deterministic seed stream also coincide; across other states, exact point/context equality permits response reuse only. The reported implementations evaluate point-acquisition rules; conditional restart, region and stopping interventions are not independently validated here.')
            replace('All new comparisons are descriptive and separate from the original prespecified inferential families.\n\n\\input{integrated_evidence/main_records.tex}',
                    'All new comparisons are descriptive and separate from the original prespecified inferential families. The independent conditional record in Table~\\ref{tab:review_primary} has25 distinct nonbaseline-action contrasts per continuation: mean continuation gives0 better,24 tie and1 worse; EI gives0 better,23 tie and2 worse at its primary margin. These30 source states share ten retained seed blocks, six of which contain nonbaseline-action contrasts. The immediate rule uses42 requests and the completed-target rules252 across those states; the immediate rule has0/1 classification errors for mean/EI and zero reported state-selection loss for both. Completed-target zero errors follow from measuring the target. At budget12, fixed depth completes17/25 and adaptive9/25 with204 requests each; reversing alternative order preserves coverage but changes the evaluated class set in eight states and can leave one worse EI contrast unmeasured. Supplementary tables retain all existing budgets/margins, complete seed-block counts and the selected paired-grid ranges.\n\n\\input{integrated_evidence/main_records.tex}\n\\input{integrated_evidence/review_main_results.tex}')
            replace('The independently collected budget record shows no adaptive-allocation advantage, and the two thermal gate/simple disagreements end in a tie and a loss.',
                    'The independently collected budget record shows no adaptive-allocation advantage and contains no better primary h5 outcomes, so it does not validate positive-case diagnosis or avoidance of false rejection. Its completed-target zero errors do not establish predictive reliability or deployment value. The two thermal gate/simple disagreements end in a tie and a loss.')
        else:
            replace('\\input{integrated_evidence/supp_records.tex}',
                    '\\input{integrated_evidence/supp_records.tex}\n\\input{integrated_evidence/review_supp_records.tex}')
        def rows(text):
            blocks = re.findall(r'\\begin\{longtable\}.*?\\end\{longtable\}', text, re.S)
            return [r for b in blocks for r in b.splitlines() if '&' in r and re.search(r'\d', r) and r.strip().endswith(r'\\')]
        assert rows(old) == rows(new)
        # Word/number boundaries in factual additions only; historical prose is preserved.
        from .integrate_engineering_evidence import tidy
        for e in edits:
            revised = re.sub(r'\b(gives|rules|completes|adaptive|with|those|rule|history|better|tie|worse|depth|These|uses)(?=\d)', r'\1 ', tidy(e['after']))
            revised = revised.replace('better,24 tie', 'better, 24 tie').replace('better,23 tie', 'better, 23 tie')
            if revised != e['after']:
                assert new.count(e['after']) == 1
                new = new.replace(e['after'], revised)
                e['after'] = revised
        new = MARKER + '\n' + new
        p.write_text(new)
        changes[name] = {'baseline_commit': BASE, 'before_sha256': sha(old.encode()), 'after_sha256': sha(new.encode()),
                         'historical_numeric_rows_unchanged': True, 'changes': edits}
    main = (PAPER / 'EO_manuscript.tex').read_text()
    abstract = main.split('\\begin{abstract}', 1)[1].split('\\end{abstract}', 1)[0]
    assert len(abstract.split()) < 250
    if changes:
        (OUT / 'factual_edit_audit.json').write_text(json.dumps({'files': changes, 'new_article_argument_sections': False,
            'abstract_words_whitespace': len(abstract.split()), 'author_scientific_review_pending': True}, indent=2) + '\n')
    print(json.dumps({'edited_sources': list(changes), 'abstract_words': len(abstract.split()),
                      'new_primary_experiments': False, 'author_review_pending': True}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    generate()
    if args.apply:
        apply()
