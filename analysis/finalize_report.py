"""Apply final author-approved annotation metadata and rebuild report presentation.

This post-freeze reporting step consumes saved predictions only. It does not change
the inference implementation, prompts, cohort membership, or controlled truth values.
"""
import json
from pathlib import Path

from leakage.common import ROOT, digest, write_json
from leakage.evaluate import compare


def read(name):
    return json.loads((ROOT / name).read_text())


def main():
    decisions = read('docs/student_decisions.json')
    assert decisions['final_review_status'] == 'student_approved'
    annotations = read('data/annotations/real-reviewed.json')
    labels = {r['sample_id']: r['label'] for r in annotations if r['label'] is not None}
    predictions = read('runs/formal-real-neural-v1/predictions.json')
    selected = [r for r in predictions if r['sample_id'] in labels]
    metrics = compare(selected, labels)
    ids = {r['sample_id'] for r in selected}
    positives = sum(labels[sid] for sid in ids)
    write_json(ROOT / 'results/study/reviewed-real.json', {
        'selection': 'Reserved real candidates with author-approved binary program labels; event-only and scope-limited judgments excluded from binary metrics',
        'sample_ids': sorted(ids), 'known_positives': positives,
        'known_negatives': len(ids) - positives,
        'annotation_sha256': digest((ROOT / 'data/annotations/real-reviewed.json').read_bytes()),
        'predictions_sha256': digest((ROOT / 'runs/formal-real-neural-v1/predictions.json').read_bytes()),
        'metrics': metrics,
    })
    lines = [r'\begin{table}[t]',
             r'\caption{Reserved real subjects with binary program labels: five positive and six negative. Counts are conditional on binary analysis outcomes. Binary/11 excludes unknown/error/timeout; $R_{\rm all+}$ includes all five known positives. The five other reserved subjects retain nonbinary judgments.}',
             r'\label{tab:real-reviewed}', r'\centering\small',
             r'\begin{tabular}{lrrrrrr}',
             r'\toprule Method & TP & FP & FN & TN & Binary/11 & $R_{\rm all+}$\\\midrule']
    for method in ('S0', 'S1', 'N0', 'N1'):
        m = metrics['primary_scope_projection'][method]
        lines.append('%s & %d & %d & %d & %d & %d/11 & %.3f' % (
            method, m['TP'], m['FP'], m['FN'], m['TN'], m['success'],
            m['full_set_detection_recall']) + r'\\')
    lines += [r'\bottomrule\end{tabular}', r'\end{table}']
    (ROOT / 'report/reviewed-real.tex').write_text('\n'.join(lines) + '\n')

    for cohort in ('development', 'controlled', 'variants', 'real-development', 'real'):
        path = ROOT / 'results/study' / (cohort + '.json')
        data = json.loads(path.read_text())
        data['label_status'] = (
            'Author-approved program/event/scope judgments; nonbinary program labels excluded from confusion counts'
            if cohort.startswith('real') else
            'Author-approved controlled labels; inherited labels for semantics-preserving variants')
        write_json(path, data)
    path = ROOT / 'report/generated-all.tex'
    text = path.read_text().splitlines()
    text[1] = (r'\caption{Program-level results under the training-affecting definition. '
               r'Controlled labels are author-confirmed. Real rows report full-cohort execution '
               r'coverage; binary-labelled real counts are in Table~\ref{tab:real-reviewed}. '
               r'F1 is conditional on successful labelled outcomes.}')
    path.write_text('\n'.join(text) + '\n')
    path = ROOT / 'report/generated-integrity.tex'
    path.write_text(path.read_text().replace(' Labels are provisional.', ''))
    path = ROOT / 'report/generated.tex'
    if path.exists():
        path.write_text(path.read_text().replace(
            'Labels are provisional;', 'Labels are author-confirmed;'))

    # Same saved confusion counts, with final terminology and consistent method order.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cohorts = ('development', 'controlled', 'variants')
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.7))
    colors = {'TP': '#1b9e77', 'TN': '#66a61e', 'FP': '#d95f02', 'FN': '#7570b3',
              'unknown': '#999999', 'error': '#444444', 'timeout': '#e6ab02'}
    methods = ('S0', 'S1', 'N0', 'N1')
    for ax, cohort in zip(axes, cohorts):
        counts = read('results/study/' + cohort + '.json')['primary_scope_projection']
        left = [0] * len(methods)
        for key, color in colors.items():
            values = [counts[m][key] for m in methods]
            ax.barh(methods, values, left=left, color=color, label=key)
            left = [a + b for a, b in zip(left, values)]
        ax.set_title(cohort)
        ax.set_xlabel('Programs')
        ax.spines[['top', 'right']].set_visible(False)
    handles, names = axes[0].get_legend_handles_labels()
    fig.legend(handles, names, ncol=7, loc='upper center', fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, .88))
    fig.savefig(ROOT / 'results/study/counts.pdf', bbox_inches='tight')
    plt.close(fig)
    write_json(ROOT / 'results/final-review-provenance.json', {
        'stage': 'Final author confirmation and reporting, after frozen inference',
        'review_date': decisions['final_review_date'], 'model_requests_made': 0,
        'annotations': {name: digest((ROOT / 'data/annotations' / (name + '.json')).read_bytes())
                        for name in ('controlled', 'variants', 'real-reviewed')},
        'source_predictions': {name: digest((ROOT / 'runs' / folder / 'predictions.json').read_bytes())
                               for name, folder in [('controlled', 'formal-controlled-neural-v1'),
                                                    ('real', 'formal-real-neural-v1'),
                                                    ('variants', 'formal-variants-neural-v1')]},
        'judgment_scope': 'Approval retains event-only and scope-limited null labels; it does not supply an independent second annotation or a human audit of all model summaries',
    })
    print('Final annotation metadata and figures rebuilt; real binary subset:', len(ids),
          'programs,', positives, 'positive; no model requests.')


if __name__ == '__main__':
    main()
