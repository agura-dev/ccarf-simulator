#!/usr/bin/env python3
"""Valida data/questions.json y lo embebe en index.html (bloque <script id="ccarf-data">).

Uso, desde la raíz del proyecto:  python3 tools/embed_data.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / 'data' / 'questions.json'
HTML_PATH = ROOT / 'index.html'
BLOCK = re.compile(r'(<script type="application/json" id="ccarf-data">)(.*?)(</script>)', re.S)
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


def main():
    data = json.loads(DATA_PATH.read_text(encoding='utf-8'))
    errors = validate(data)
    if errors:
        print(f'{DATA_PATH.name}: {len(errors)} error(es), index.html no se modificó', file=sys.stderr)
        for e in errors:
            print('  - ' + e, file=sys.stderr)
        sys.exit(1)

    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = HTML_PATH.read_text(encoding='utf-8')
    if len(BLOCK.findall(html)) != 1:
        sys.exit('index.html: no se encontró exactamente un bloque <script id="ccarf-data">')
    HTML_PATH.write_text(BLOCK.sub(lambda m: m.group(1) + payload + m.group(3), html), encoding='utf-8')

    bank = data['bank']
    per_domain = Counter(q['d'] for q in bank)
    per_src = Counter(q.get('src', '—') for q in bank)
    print(f'index.html actualizado: {len(bank)} preguntas, {len(data["samples"])} de ejemplo')
    print('  ' + ' · '.join(f'D{d}: {per_domain[d]}' for d in sorted(per_domain)))
    print('  ' + ' · '.join(f'{s}: {n}' for s, n in sorted(per_src.items())))


if __name__ == '__main__':
    main()
