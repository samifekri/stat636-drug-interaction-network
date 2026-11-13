# Drug-Interaction Link Prediction: Label Warnings vs. Patient Reports

**STAT 636 · Fall 2026 · Group 6** — Avneesh Dubey, Sami Fekri, Elliot Manuel

We build a two-layer network over the same ~300 drugs from openFDA. **Layer 1** links drug *i* to
drug *j* when *i*'s label warns about *j* (directed). **Layer 2** links two drugs when patients
report them together more often than expected (undirected, weighted). Pairs that are often
co-reported but never warned about are candidate missing interactions. Details:
[`docs/proposal.docx`](docs/proposal.docx), plan and owners: [`docs/project-plan.md`](docs/project-plan.md).

## Deadlines

| Date | What |
|---|---|
| Sun Nov 8 | Both layers built, reviewed, data frozen |
| Wed Nov 18, 11:59 PM | Recorded presentation (≤ 15 min, ≤ 10 slides) |
| Mon Dec 7, 11:59 PM | Final report |

## Folders

```
├── README.md
├── requirements.txt      Python packages
├── .env.example          template for the openFDA API key
├── data/
│   ├── raw/              openFDA downloads (stay on your machine, not committed)
│   ├── reference/        hand-made tables, e.g. drug_classes.csv (Elliot)
│   └── processed/        the network: nodes + both layers (committed, shared)
├── notebooks/            numbered notebooks, run in order
├── outputs/              figures and tables for the slides and report
└── docs/                 proposal and project plan
```

## Notebooks

| Notebook | Owner | Reads | Writes |
|---|---|---|---|
| `01_node_set.ipynb` | Avneesh | openFDA reports | `data/processed/nodes.csv` |
| `02_layer1_labels.ipynb` | Avneesh | `nodes.csv`, openFDA labels | `data/processed/layer1_edges.csv` |
| `03_layer2_coreports.ipynb` | Sami | `nodes.csv`, openFDA reports | `data/processed/layer2_edges.csv` |
| `04_exploration.ipynb` | Avneesh | `data/processed/` | `outputs/`: layer summary, degrees, reciprocity |
| `05_modeling.ipynb` | Avneesh | `data/processed/` | `outputs/`: block models, candidates, link prediction |

For your own experiments, start the file name with your initials, e.g. `sf_layer2_tests.ipynb`.

`notebooks/openfda_utils.py` holds the shared helpers: cached openFDA and RxNorm requests (`fu.openfda`, `fu.rxnorm_ingredients`), name rules and label mining. Every response is cached in `data/raw/`, so rerunning a notebook makes no new requests; delete `data/raw/openfda/` or `data/raw/rxnav/` to refetch.

## Data files (the hand-off between notebooks)

All in `data/processed/`. `node_id` runs 0 … n−1 and is the row/column of the adjacency matrices.

| File | One row per | Columns |
|---|---|---|
| `nodes.csv` | drug | `node_id`, `rxcui` (RxNorm ingredient), `ingredient` (lower case), `n_reports`, `fda_names` (every openFDA substance name of the drug, `\|`-separated: use all of them in openFDA queries) |
| `name_mapping.csv` | openFDA substance name | `fda_name`, `name_count`, `status` (`single`, `combination`, `non_drug`, `not_found`), `rxcui`, `ingredient` |
| `node_labels.csv` | drug | `node_id`, `has_label`, `label_set_id`, `label_effective_time`, `pharm_class_epc`, `pharm_class_moa` |
| `layer1_edges.csv` | label warning *i* → *j* | `from_id`, `to_id`, `via_name` (named directly), `via_class` (via a class such as "CYP3A4 inhibitors"), `class_terms`, `evidence` (the label sentence) |
| `layer2_edges.csv` | drug pair, `i_id < j_id` | `i_id`, `j_id`, `n_ij`, `n_i`, `n_j`, `e_ij` (expected), `w_ij` (= n_ij / e_ij), `log_w_lcb`, `passes_filter` (n_ij ≥ 5 and log_w_lcb > 0) |

If you change these columns, update this table in the same commit and tell the others.

## Setup

```bash
git clone <repo-url>
cd stat636-drug-interaction-network
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # then paste your openFDA API key into .env
jupyter lab
```

Python 3.12 is recommended.

## Working together

- `git pull` before you start. Work on a branch, open a pull request, and let the other person
  review it (Avneesh ↔ Sami).
- One notebook, one owner. To try something in someone else's notebook, copy it.
- Before committing a notebook: **Kernel → Restart Kernel and Clear All Outputs**. This keeps
  diffs small and avoids merge conflicts.
- Never commit `.env` or anything in `data/raw/`.
