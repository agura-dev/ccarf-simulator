#!/usr/bin/env python3
"""Valida data/questions.json y data/questions_heavy.json y los embebe en index.html
(bloques <script id="ccarf-data"> y <script id="ccarf-data-heavy">).

Uso, desde la raíz del proyecto:  python3 tools/embed_data.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / 'data' / 'questions.json'
HEAVY_PATH = ROOT / 'data' / 'questions_heavy.json'
HTML_PATH = ROOT / 'index.html'
BLOCK = re.compile(r'(<script type="application/json" id="ccarf-data">)(.*?)(</script>)', re.S)
HEAVY_BLOCK = re.compile(r'(<script type="application/json" id="ccarf-data-heavy">)(.*?)(</script>)', re.S)
# Preguntas por dominio que pide el examen Completo (TEST_MODES en index.html).
FULL_EXAM = {1: 16, 2: 11, 3: 12, 4: 12, 5: 9}


def validate(data):
    errors = []
    scenarios = {s.get('n') for s in data.get('scenarios', [])}
    if scenarios != set(range(1, 7)):
        errors.append(f'scenarios: se esperan los números 1–6, hay {sorted(scenarios)}')
    for group in ('bank', 'samples'):
        seen = set()  # bank y samples numeran sus IDs por separado
        items = data.get(group)
        if not isinstance(items, list) or not items:
            errors.append(f'{group}: falta o está vacío')
            continue
        for i, q in enumerate(items):
            qid = q.get('id') or f'{group}[{i}]'
            def bad(msg):
                errors.append(f'{group} {qid}: {msg}')
            if qid in seen:
                bad('id repetido')
            seen.add(qid)
            d = q.get('d')
            if d not in range(1, 6):
                bad(f'd={d!r} fuera de 1–5')
            if not str(q.get('ts', '')).startswith(f'{d}.'):
                bad(f'ts={q.get("ts")!r} no corresponde al dominio {d}')
            if q.get('sc') not in scenarios:
                bad(f'sc={q.get("sc")!r} no es un escenario válido')
            o = q.get('o')
            if not (isinstance(o, list) and len(o) == 4 and all(isinstance(t, str) and t.strip() for t in o)):
                bad('o debe tener 4 opciones no vacías')
            if q.get('a') not in range(4):
                bad(f'a={q.get("a")!r} fuera de 0–3')
            for k in ('q', 'w'):
                if not (isinstance(q.get(k), str) and q[k].strip()):
                    bad(f'{k} vacío')
    per_domain = Counter(q.get('d') for q in data.get('bank') or [])
    for d, need in FULL_EXAM.items():
        if per_domain[d] < need:
            errors.append(f'bank: D{d} tiene {per_domain[d]} preguntas; el examen Completo necesita {need}')
    return errors


def consistency(bank, heavy):
    """El banco pesado es una reescritura: mismos IDs, mismo orden y mismos metadatos."""
    errors = []
    if [q.get('id') for q in heavy] != [q.get('id') for q in bank]:
        errors.append('bank: los IDs (o su orden) no coinciden con questions.json')
        return errors
    for q, h in zip(bank, heavy):
        for k in ('d', 'ts', 'sc', 'a', 'src'):
            if q.get(k) != h.get(k):
                errors.append(f'bank {q["id"]}: {k}={h.get(k)!r}, en questions.json es {q.get(k)!r}')
    return errors


def payload(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def summary(name, bank):
    per_domain = Counter(q['d'] for q in bank)
    per_src = Counter(q.get('src', '—') for q in bank)
    print(f'  {name}: {len(bank)} preguntas · ' + ' · '.join(f'D{d}: {per_domain[d]}' for d in sorted(per_domain)))
    print('    ' + ' · '.join(f'{s}: {n}' for s, n in sorted(per_src.items())))


def main():
    data = json.loads(DATA_PATH.read_text(encoding='utf-8'))
    heavy = json.loads(HEAVY_PATH.read_text(encoding='utf-8'))
    # Escenarios y preguntas de ejemplo son comunes: el banco pesado se valida con los de questions.json.
    heavy_errors = validate({**data, 'bank': heavy.get('bank')})
    if isinstance(heavy.get('bank'), list) and isinstance(data.get('bank'), list):
        heavy_errors += consistency(data['bank'], heavy['bank'])
    checks = [(DATA_PATH.name, validate(data)), (HEAVY_PATH.name, heavy_errors)]
    failed = False
    for name, errors in checks:
        if errors:
            failed = True
            print(f'{name}: {len(errors)} error(es)', file=sys.stderr)
            for e in errors:
                print('  - ' + e, file=sys.stderr)
    if failed:
        sys.exit('index.html no se modificó')

    html = HTML_PATH.read_text(encoding='utf-8')
    if len(BLOCK.findall(html)) != 1:
        sys.exit('index.html: no se encontró exactamente un bloque <script id="ccarf-data">')
    if not HEAVY_BLOCK.search(html):  # primera vez: se crea vacío justo después del bloque principal
        html = BLOCK.sub(lambda m: m.group(0) + '\n<script type="application/json" id="ccarf-data-heavy"></script>', html)
    if len(HEAVY_BLOCK.findall(html)) != 1:
        sys.exit('index.html: hay más de un bloque <script id="ccarf-data-heavy">')
    html = BLOCK.sub(lambda m: m.group(1) + payload(data) + m.group(3), html)
    html = HEAVY_BLOCK.sub(lambda m: m.group(1) + payload({'bank': heavy['bank']}) + m.group(3), html)
    HTML_PATH.write_text(html, encoding='utf-8')

    print(f'index.html actualizado ({len(data["samples"])} preguntas de ejemplo, comunes a los dos bancos)')
    summary('standard', data['bank'])
    summary('heavy', heavy['bank'])


if __name__ == '__main__':
    main()
