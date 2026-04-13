# Stem-Agent

**A Self-Differentiating Python Code QA Agent**

Stem-Agent starts as an undifferentiated harness. Given a class of problems — here, *Python code quality assurance* — it researches how experts solve it, generates a specialized agent, tests it against a labeled dataset, and iterates until the agent reaches a performance threshold. Then it stops evolving and starts executing.

---

## Architecture

```
StemAgent (undifferentiated)
│
├── Explorer      Asks: "How is Python QA typically done?"
│                 Produces a structured PLAN (bug categories, detection strategies)
│
├── Architect     Generates a QAAgent Python class from the plan
│                 On retry: incorporates Evaluator feedback
│
├── Evaluator     Runs QAAgent on labeled dataset (10 files, 37 known bugs)
│                 Measures Recall / Precision / F1 vs ground truth
│                 Produces actionable feedback if score is insufficient
│
└── Loop          Iterates up to 5 times
                  Stops when Recall ≥ 70% AND Precision ≥ 50%
                  (or max attempts reached)
```

The **before/after comparison** uses `pyflakes` as the baseline — a standard static analysis tool that only catches undefined names and unused imports. The Stem-Agent learns to detect a much broader range of issues through its own research and iteration.

---

## Setup

### Prerequisites
- Python 3.10+
- An OpenAI API key

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/Stem-Agent.git
cd Stem-Agent
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_key_here
```

---

## Usage

```bash
# Full differentiation lifecycle (recommended first run)
python main.py

# Re-evaluate an already-generated agent
python main.py --eval-only

# Show baseline metrics only
python main.py --baseline
```

---

## Dataset

10 hand-crafted Python files in `dataset/`:
- `buggy_01.py` — `buggy_09.py`: files with known bugs (37 total across 12 categories)
- `clean_10.py`: a clean file to test false positive rate

Bug categories covered:
`unused_variable`, `unreachable_code`, `mutable_default_argument`, `bare_except`,
`division_by_zero`, `type_error`, `comparison_to_none`, `comparison_to_true`,
`builtin_shadowing`, `resource_leak`, `class_shared_state`, `missing_return`,
`off_by_one`, `logic_error`, `sql_injection`

Ground truth is in `dataset/ground_truth.json`.

---

## Output

After running, `specialized/` contains:
- `plan.json` — the Explorer's research output
- `qa_agent.py` — the final specialized agent
- `qa_agent_v1.py`, `qa_agent_v2.py`, ... — versioned history of each attempt
- `result_v1.json`, ... — per-attempt evaluation results
- `evolution_history.json` — full iteration log
- `final_report.json` — before/after comparison summary

---

## Project Structure

```
Stem-Agent/
├── main.py                    # Entry point
├── requirements.txt
├── dataset/
│   ├── buggy_01.py … buggy_09.py
│   ├── clean_10.py
│   └── ground_truth.json
├── stem_agent/
│   ├── explorer.py            # Phase 1: research
│   ├── architect.py           # Phase 2: code generation
│   ├── evaluator.py           # Phase 3: measurement
│   └── loop.py                # Orchestration
└── specialized/               # Generated at runtime
    ├── plan.json
    ├── qa_agent.py
    └── final_report.json
```
