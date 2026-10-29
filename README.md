# CCAR-F Exam Simulator

A practice simulator for the **Claude Certified Architect – Foundations (CCAR-F)** exam.

> Unofficial. This project is not affiliated with or endorsed by Anthropic.

## Getting started

The whole app is a single file, `index.html`. You don't need a server, an internet connection or any installation.

1. Get the files using either option:
   - Clone the repository: `git clone <repository URL>`.
   - On the repository page, use **Code → Download ZIP** and unzip it.
2. Open `index.html` in your browser, for example by double-clicking it.

To get updates, run `git pull` inside the folder, or download the ZIP again.

## Modes

### Test

Simulates the real exam.

| Length | Questions | Time |
|---|---|---|
| Short | 15 | 30 min |
| Medium | 30 | 60 min |
| Full | 60 | 120 min |

- Questions are distributed across the 5 domains using the official weights (27 / 18 / 20 / 20 / 15 %) and drawn mostly from 4 randomly chosen scenarios.
- A practice question (not scored) comes before the exam.
- During the exam you can flag questions and check your progress on a review screen before finishing.
- The result is a score from 100 to 1000; you pass with **720**, which equals 72% correct. You also get a breakdown by domain and a full question review with explanations.
- Two visual styles:
  - **Real exam:** a plain interface like the official exam.
  - **Modern:** the simulator interface, with a light/dark theme.

### Knowledge

Practice question by question, with the correct answer and its explanation shown right after you answer.

- 10 or 15 questions.
- Timed (2 minutes per question) or untimed.

## Keyboard shortcuts

Everything works with the keyboard:

| Action | Keys |
|---|---|
| Answer | `1`–`4` or `A`–`D` |
| Move between questions | `←` / `→` |
| Flag a question | `M` |
| Open the review screen | `R` |
| Go back or exit | `Esc` |

Each screen lists its own shortcuts at the bottom.

## Question bank

- 151 questions covering the 5 domains and the 6 official scenarios.
- 12 sample questions from the official exam guide, used as the practice question in Test mode.

### Editing questions

The questions live in `data/questions.json`. The app can't read that file directly when opened from disk, so a copy is embedded inside `index.html`. After editing the JSON, run this from the project root (requires Python 3):

```bash
python3 tools/embed_data.py
```

The script checks the data first. If it finds errors, it lists them and leaves `index.html` unchanged.

Each question in `bank` has these fields:

| Field | Meaning |
|---|---|
| `id` | Unique ID, e.g. `D1_TS11_Q1` |
| `d` | Domain, 1–5 |
| `ts` | Task statement from the exam guide, e.g. `"1.1"` |
| `sc` | Scenario, 1–6 (defined in `scenarios`) |
| `q` | Question text |
| `o` | The 4 options, in order A–D |
| `a` | Index of the correct option (0 = A … 3 = D) |
| `w` | Explanation ("Why X") |
| `src` | Source: `Practice Exam` or `Practice Test` |

Questions in `samples` use the same fields, without `src`.

Text supports inline `` `code` `` only.

## Reference

The authoritative source for the exam's content and format is Anthropic's official CCAR-F exam guide.
