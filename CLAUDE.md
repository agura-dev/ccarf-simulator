# CLAUDE.md

Simulador del examen CCAR-F (Claude Certified Architect – Foundations). La especificación completa y las decisiones de producto están en [context/project_overview.md](context/project_overview.md) (solo en local, no está en el repo): léela antes de cambiar comportamiento.

## Estructura

- `index.html` — la aplicación completa: HTML + CSS + JS + datos en un solo archivo. Se abre directamente en el navegador (`file://`), sin servidor ni build.
- `data/questions.json` — **fuente de verdad** de escenarios, banco (211 preguntas) y preguntas de ejemplo (12). Se edita a mano.
- `data/questions_heavy.json` — `{ bank }` con las mismas 211 preguntas y en el mismo orden que el banco estándar: las 151 `Practice Exam` + `Practice Test` reescritas en estilo "pesado" (más contexto, distractores plausibles, opciones de largo parejo) y las 60 `Purcell Practice Set` copiadas sin cambios (ya tienen ese estilo). Mismos `id`/`d`/`ts`/`sc`/`a`/`src` y mismo formato que el banco; en las reescritas solo cambian `q`, `o` y `w`. Si se edita una pregunta Purcell, actualizarla en los dos archivos. La app lo usa cuando se elige "Heavy" en el inicio. Reglas de estilo en `Preliminaries/heavy_style_guide.md` (local).
- `tools/embed_data.py` — valida `data/questions.json` y `data/questions_heavy.json` y los embebe en `index.html`.
- `README.md` — instrucciones de uso para quienes clonan el repo (en inglés).

Solo en local (en `.gitignore`, no están en el repo):
- `context/project_overview.md` — especificación y decisiones (fuente de verdad).
- `data/CCAR_F_exam_guide_official.pdf` — guía oficial (pesos por dominio en sección 4, objetivos en sección 6, puntaje en sección 10).
- `Preliminaries/` — prompts, borradores y los `.md` históricos de los que salió `questions.json`: `CCAR-F_Practice_Exam_QuestionsDB.md` (banco en tabla), `CCARF_ExamGuide_SampleQuestions_DB.md` (ejemplos de la guía), `Practice_Test_Questions.md` (origen de las preguntas `Practice Test`), `mock exam1.pdf` (origen de las preguntas `Purcell Practice Set`), `Scenarios.md`. La app no los usa.
- `create_repo.md` — pasos para publicar en GitHub.

## Restricciones (no negociables)

- Un único archivo HTML. Sin frameworks, sin CDN, sin recursos externos, sin fetch de archivos locales. `<meta charset="utf-8">`.
- Tema claro/oscuro mediante tokens CSS en `:root` (`data-theme` + `prefers-color-scheme`).
- Accesibilidad: acierto/error con ✓/✕ además del color; todo operable con teclado; foco visible.
- Todo el contenido de la app en inglés: interfaz, preguntas, opciones y explicaciones. Los comentarios del código y la documentación siguen en español.

## Datos embebidos

`data/questions.json` se embebe minificado en `<script type="application/json" id="ccarf-data">` y el banco de `data/questions_heavy.json` en `<script type="application/json" id="ccarf-data-heavy">` (solo `{ bank }`; escenarios y preguntas de ejemplo son comunes), dentro de `index.html` (con `file://` no se puede hacer fetch). Tras editar cualquiera de los dos JSON, correr desde la raíz:

```
python3 tools/embed_data.py
```

El script valida (IDs únicos por grupo, `d`/`ts`/`sc`/`o`/`a`/`w` bien formados, cupo por dominio para el examen Completo), escapa `</` como `<\/` y reemplaza los dos bloques. Al banco pesado le aplica la misma validación y además exige que coincida con el estándar: mismos IDs en el mismo orden y mismos `d`/`ts`/`sc`/`a`/`src`. Si hay errores en cualquiera de los dos no toca `index.html`. Si el bloque `ccarf-data-heavy` no existe, lo crea después de `ccarf-data`. Nunca editar los bloques a mano.

Formato:

```
{ scenarios: [{ n, t, b }],            // número, título, descripción
  bank:      [{ id, d, ts, sc, q, o, a, w, src }],
  samples:   [{ id, d, ts, sc, q, o, a, w }] }
```

`d` dominio 1–5 · `ts` task statement · `sc` escenario 1–6 · `q` pregunta · `o` 4 opciones en orden original · `a` índice de la correcta (0–3) · `w` explicación única ("Why X": por qué es correcta y, si la fuente lo trae, por qué las otras no) · `src` origen (`Practice Exam` | `Practice Test` | `Purcell Practice Set`; la app aún no lo usa). Los IDs de `bank` y `samples` se numeran por separado y pueden coincidir. El texto admite solo `` `código` `` (se renderiza con `fmt()`, que escapa HTML).

### Mapeo de escenarios

En el JSON `sc` es el número oficial. Las fuentes originales usaban nombres cortos; se mapearon así:

| `sc` | Escenario oficial | Nombre en el banco (Practice Exam) | Nombre en Practice Test |
|---|---|---|---|
| 1 | Customer Support Resolution Agent | Customer Support | Customer Support Agent |
| 2 | Code Generation with Claude Code | Code Generation | Code Generation with Claude Code |
| 3 | Multi-Agent Research System | Multi-Agent Research | Multi-agent Research System |
| 4 | Developer Productivity with Claude | Developer Productivity, CI / Developer Productivity | — |
| 5 | Claude Code for Continuous Integration | CI | Claude Code for Continuous Integration |
| 6 | Structured Data Extraction | Structured Data Extraction | — |

Las preguntas de ejemplo de la guía y las del Purcell Practice Set ya usan los nombres y números oficiales.

## Lógica clave (index.html)

- **Reparto por dominio** (`TEST_MODES[*].dist`, D1..D5): pesos oficiales 27/18/20/20/15 con redondeo por mayor resto. Corto 4/3/3/3/2 · Medio 8/5/6/6/5 · Completo 16/11/12/12/9. Knowledge 15 → 4/3/3/3/2 · 10 → 3/2/2/2/1.
- **Escenarios** (`buildItems`): se eligen 4 al azar; cada dominio toma primero de esos 4 y completa con los demás si no alcanza. Con el banco actual el examen Completo siempre termina usando los 6 escenarios; es esperado.
- **Orden**: preguntas agrupadas por escenario, aleatorias dentro del grupo; opciones mezcladas por pregunta (`order[pos] = índice original`). Las respuestas se guardan como índice original.
- **Explicaciones citan letras originales (A–D)**: por eso la revisión y la pregunta de práctica muestran las opciones en orden original. No mostrar explicaciones junto a opciones mezcladas sin resolver esto.
- **Puntaje** (modo Test, `scaledScore`):
  - Se aprueba con ≥ 72% de acierto (`PASS_PCT`).
  - El puntaje escalado (100–1000) es lineal por tramos para que 72% equivalga exactamente a 720: 0% → 100, 72% → 720, 100% → 1000.
    - Si acierto < 72%: `100 + (acierto / 72) × 620`.
    - Si acierto ≥ 72%: `720 + ((acierto − 72) / 28) × 280`.
    - Se redondea al entero.
  - El % mostrado usa `Math.floor` para no mostrar "72%" en un no aprobado.
- **Tiempo**: el reloj usa `endAt` (timestamp), no cuenta ticks. Avisos a 5 min y 1 min; entrega automática en 0. La pregunta de práctica no consume tiempo.
- **Banco de preguntas** (`state.bank`: `standard` | `heavy`, guardado en localStorage con la clave `ccarf-bank`): selector en el inicio, antes de elegir modo; vale para Test y Knowledge. `BANKS[state.bank]` es lo único que lee `pickByDomain`; la pregunta de práctica usa siempre `DATA.samples`. Cada sesión guarda `bank` en `state.exam` / `state.k` y `bankTag()` añade " · heavy" al modo de Knowledge y a los resultados (con Standard no se muestra nada; la pantalla del examen no cambia).
- **Estilo del examen** (`state.examStyle`: `real` | `modern`, guardado en localStorage): `showScreen()` pone la clase `exam-real` en `<body>` solo en `test-sample` y `test-exam`; el CSS de `body.exam-real` redefine los tokens (blanco/negro, Arial, sin radios) y esconde topbar, footer, hints y panel de navegación. Los textos de esas pantallas salen del diccionario `UI` vía `tx()`: los dos estilos están en inglés, pero `real` imita la redacción del examen oficial ("End Exam", "Mark for review") y `modern` usa la del simulador ("Finish exam", "⚐ Flag for review"). Los estáticos usan `data-t="<clave>"` + `applyStaticLabels()`. Al añadir texto a la pantalla de examen, agregarlo a los dos estilos en `UI`.
- **Revisión antes de terminar**: es una vista dentro de `screen-test-exam` (`#exam-review-view`, alterna con `#exam-question-view` vía `showView()`), así comparte barra y reloj. Terminar el examen siempre pasa por ahí (`openReview` → `requestFinish`).
- **`[hidden]` lleva `display: none !important`** global: sin eso, reglas como `.btn { display: inline-flex }` lo anulan.
- **Pantallas**: secciones `.screen` con id `screen-<nombre>`; navegación con `showScreen()` o atributos `data-nav="<nombre>"`. Atajos de teclado centralizados en un único `keydown` por pantalla.

## Estado

- Hecho: pantalla de inicio, modo Test completo (selección + estilo real/moderno, pregunta de práctica, examen, revisión antes de terminar, resultados por dominio, revisión con filtros) y modo Knowledge (configuración, pregunta con feedback inmediato y reloj de 2 min por pregunta, resumen por dominio).
- **Knowledge**: siempre estilo moderno (no usa `tx()`; sus textos están directamente en el código); opciones **sin mezclar** (decisión de producto, por las letras de las explicaciones); estado en `state.k`, reloj propio (`startKTimer`/`kTick`) independiente del del examen. Selección con `pickByDomain(kDist(n, dominio))`, sin regla de escenarios, en orden aleatorio. Filtro por dominio en la configuración (radios `k-domain`, generados desde `DOMAINS`): `'all'` usa `KNOWLEDGE_SIZES`; un dominio pone las n preguntas en él (`state.k.domain`) y el resumen muestra solo esa fila.

## Verificación

No hay tests automatizados. Para verificar:

- Sintaxis: extraer el `<script>` principal y ejecutar `node --check`.
- Flujo: copiar `index.html` al scratchpad con un script de prueba inyectado antes de `</body>` que haga clics/eventos de teclado, y correr Chrome headless (`--headless=new --dump-dom` o `--screenshot`). Para vista móvil, cargar la página en un `<iframe>` de 390 px (Chrome headless no reduce la ventana por debajo de ~500 px).
- No dejar archivos de prueba dentro del proyecto.
