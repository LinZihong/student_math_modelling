# Flood and escape-routing model

This is the code behind *Escaping a Flooding Mine* (paper: `../yale_supplement/Escaping_a_Flooding_Mine_v2.tex`).

| File | What it does |
|---|---|
| `network.py` | Reads the competition workbooks (sheets 端点 / 巷道, one header row) and inserts points such as inrush points, exits and miners into tunnels at their exact positions |
| `flood.py` | Volume-conserving, event-driven flood model (paper, Section 3, rules R1–R4) |
| `routing.py` | Exact walking times, earliest-arrival Dijkstra, latest start on a fixed route, and the miner's position at a given time |
| `legacy.py` | The competition team's flood algorithm, kept only for comparison |
| `test_model.py` | 10 tests covering every flood rule, conservation with two inrushes, Proposition 1, the exact-traversal counterexample, first-in-first-out, and Dijkstra against brute force |

Run from the project root (Python 3.9+, packages in `../mine_example/requirements.txt`):

```bash
python -m unittest model.test_model -v
python -m competition.run        # Problems 1-4, sensitivity, checks -> competition/results/
python -m competition.figures    # -> competition/figures/
```
