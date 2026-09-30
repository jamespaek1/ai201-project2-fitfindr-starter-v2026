"""Score saved evidence; factual grounding requires explicit reviewed notes.

This script never calls a model or changes the saved runs. Caption facts cannot
be completely judged by word counts: reviewers must inspect the full output.
"""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def score(label, factual_notes=None):
    report = json.loads((ROOT / 'results' / f'unit4_{label}.json').read_text())
    source = {x['id']: x for x in json.loads((ROOT / 'data' / 'listings.json').read_text())}
    scores = []
    for row in report['rows']:
        number = row['scenario']['criterion']
        tries = []
        for r in row['tries']:
            s = r['session'] or {}
            calls = s.get('tool_calls', [])
            names = [c['tool'] for c in calls]
            checks = {'no_crash': not r['crashed']}
            if number == 1:
                checks.update(no_error=s.get('error') is None,
                              fit_card=isinstance(s.get('fit_card'), str) and bool(s['fit_card'].strip()),
                              tool_order=names == ['search_listings', 'suggest_outfit', 'create_fit_card'])
            elif number == 2:
                checks.update(tool_order=names == ['search_listings'],
                              empty_results=s.get('search_results') == [],
                              no_downstream_state=all(s.get(k) is None for k in ['selected_item', 'outfit_suggestion', 'fit_card']),
                              actionable=any(x in (s.get('error') or '') for x in ['broader keywords', 'another size', 'higher budget']),
                              no_model_calls=r['model_calls'] == 0)
            elif number == 3:
                complete = names == ['search_listings', 'suggest_outfit', 'create_fit_card']
                checks['both_downstream_calls'] = complete
                checks['full_item_equal'] = bool(complete and s['search_results'] and
                    s['selected_item'] == s['search_results'][0] == calls[1]['inputs']['new_item'] == calls[2]['inputs']['new_item'])
                checks['outfit_equal'] = bool(complete and calls[2]['inputs']['outfit'] == s['outfit_suggestion'])
            elif number == 4:
                text = r['output'] or ''
                words = len(text.split())
                sentences = len(re.findall(r'[.!?]+(?=\s|$)', text))
                checks.update(words_30_to_80=30 <= words <= 80, sentences_2_to_4=2 <= sentences <= 4,
                    title_once=text.count(r['inputs']['new_item']['title']) == 1,
                    price_once=len(re.findall(r'\$18(?:\.00)?(?!\d|\.\d)', text)) == 1,
                    platform_once=len(re.findall(r'\bdepop\b', text, re.I)) == 1,
                    outfit_piece=bool(re.search(r'\b(?:jeans|sneakers)\b', text, re.I)))
                note = (factual_notes or {}).get(str(r['attempt']))
                checks['reviewed_grounding'] = bool(note and note['pass'])
                tries.append({'try': r['attempt'], 'pass': all(checks.values()), 'checks': checks,
                              'words': words, 'sentences': sentences, 'grounding_review': note,
                              'caption': text})
                continue
            elif number == 5:
                items = r['output'] or []
                args = r['inputs']
                def matches_size(value):
                    label = re.sub(r'\s*\([^)]*\)', '', value).upper().strip()
                    if args['size'] == 'W30':
                        return bool(re.fullmatch(r'W30(?:\s+L\d+)?', label))
                    return args['size'] in [part.strip() for part in label.split('/')]
                checks.update(expected_present=r['expected_id'] in [x['id'] for x in items],
                              source_records=all(x == source.get(x['id']) for x in items),
                              within_budget=all(x['price'] <= args['max_price'] for x in items),
                              whole_size_labels=all(matches_size(x['size']) for x in items),
                              no_model_calls=r['model_calls'] == 0)
            tries.append({'try': r['attempt'], 'pass': all(checks.values()), 'checks': checks})
        passed = sum(t['pass'] for t in tries)
        target = row['scenario']['target']
        scores.append({'criterion': number, 'name': row['scenario']['name'], 'target': target,
                       'passes': passed, 'verdict': 'MET' if passed >= target else 'MISSED', 'tries': tries})
    return scores


if __name__ == '__main__':
    label = sys.argv[1]
    notes_path = ROOT / 'results' / f'unit4_{label}_grounding.json'
    notes = json.loads(notes_path.read_text()) if notes_path.exists() else None
    scores = score(label, notes)
    print(json.dumps(scores, indent=2, ensure_ascii=False))
    if notes:
        (ROOT / 'results' / f'unit4_{label}_scores.json').write_text(
            json.dumps(scores, indent=2, ensure_ascii=False), encoding='utf-8')
