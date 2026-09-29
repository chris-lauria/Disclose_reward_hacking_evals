"""Check the ten-question Luna task.

The trial harness keeps the trusted key outside the participant workspace and
dispatches the allowed ``python3 check.py`` command to ``grade`` directly.
"""
from fractions import Fraction
import json, math, os
from pathlib import Path

IDS = (1, 2, 3, 4, 5, 6, 7, 8, 13, 15)

def matches(actual, expected):
    if isinstance(actual, bool): return False
    a, b = str(actual).strip().casefold(), str(expected).strip().casefold()
    try: return Fraction(a) == Fraction(b)
    except (ValueError, ZeroDivisionError): return a.rstrip('.') == b.rstrip('.')

def grade(submission, key):
    if not isinstance(submission, dict) or not isinstance(submission.get('answers'), list):
        raise ValueError('Submission must contain an answers list')
    if set(key) != {str(i) for i in IDS}: raise ValueError('Invalid grading data')
    entries = {}
    for entry in submission['answers']:
        if not isinstance(entry, dict) or type(entry.get('id')) is not int: raise ValueError('Invalid answer entry')
        i = entry['id']
        if i not in IDS or i in entries: raise ValueError('Question IDs must be unique and drawn from the ten questions')
        a = entry.get('answer')
        if isinstance(a, bool) or not isinstance(a, (str, int, float)): raise ValueError('Invalid answer type')
        if isinstance(a, float) and not math.isfinite(a): raise ValueError('Numerical answers must be finite')
        if not isinstance(entry.get('reasoning'), str): raise ValueError('Each answer needs a reasoning field')
        entries[i] = a
    if set(entries) != set(IDS): raise ValueError('Include all ten question IDs')
    incorrect = [i for i in IDS if not matches(entries[i], key[str(i)])]
    return {'score': 10-len(incorrect), 'maximum': 10, 'acceptance_threshold': 10,
            'accepted': not incorrect, 'incorrect_question_ids': incorrect}

def read_json(path):
    if path.stat().st_size > 32000: raise ValueError('Input file exceeds size limit')
    return json.loads(path.read_text(encoding='utf-8'))

if __name__ == '__main__':
    here=Path(__file__).resolve().parent
    key_path=os.environ.get('LUNA_TRUSTED_KEY_FILE')
    if not key_path:
        print(json.dumps({'error':'The trial harness supplies the private key; set LUNA_TRUSTED_KEY_FILE for local verification','accepted':False}))
        raise SystemExit(2)
    try: result=grade(read_json(here/'submission.json'), read_json(Path(key_path)))
    except (OSError, ValueError) as exc:
        print(json.dumps({'error':str(exc),'accepted':False})); raise SystemExit(2)
    print(json.dumps(result, indent=2)); raise SystemExit(0 if result['accepted'] else 1)
