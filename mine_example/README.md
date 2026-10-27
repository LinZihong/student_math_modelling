# Worked example: an anonymized real mine plan

This folder applies the 论文_02_洪水传播与动态逃生_Claude稿's method (volume-conserving flood model + time-dependent Dijkstra escape routing, code in `../model/`) to the mining plan of a working longwall coal mine.

> **Anonymization.**
> - The published files contain no names.
> - The plan is rotated, mirrored and shifted by a random transform, and elevations are given relative to a hidden reference level.
> - The transform key and the original drawing live in `raw/`, which is git-ignored and must never be published.
> - Before publishing anything derived from the drawing, confirm that its provider agrees to use in this anonymized form.

## Pipeline (run from the project root)

```bash
brew install libredwg                      # DWG reader (provides dwgread)
python3 -m venv .venv && .venv/bin/pip install -r mine_example/requirements.txt
dwgread -O JSON -o mine_example/raw/plan.json mine_example/raw/plan.dwg
.venv/bin/python -I mine_example/scripts/extract_network.py mine_example/raw/plan.json mine_example/data/
.venv/bin/python -m mine_example.scripts.simulate
.venv/bin/python -m mine_example.scripts.figures
```

| Step | Script | Output |
|---|---|---|
| DWG → anonymized graph | `scripts/extract_network.py` | `data/mine_network.xlsx`, in the same layout as the competition data (sheets 端点 / 巷道), so the same code reads it. `data/mine_features.json` holds the shafts, water-zone outlines and tunnel width |
| Flood + routing | `scripts/simulate.py` | `results/summary.json`: flood extent over time, comparison with the competition algorithm, the Proposition 1 check, routes, latest alert times and the alert sweep |
| Figures | `scripts/figures.py` | `figures/mine_network.png`, `figures/mine_flood_routes.png` |

## How the network is built
- **Tunnels:** taken from the centerline layer. Gaps under 8 m between a line end and another line are bridged, lines are split at every intersection, and the largest connected network is kept. The result has 1,591 nodes, 2,083 tunnels and 248 km of roadway.
- **Elevation:** taken from the 2,347 roof-elevation labels at survey stations, interpolated by inverse distance within 300 m.
- **Width:** 5.0 m, the median distance between the drawn walls.
- **Exits:** the four shafts, each joined to the nearest node by a 10–66 m connector.

## Scenario
- **Inrush:** from the water-accumulation zone closest (by tunnel distance) to the shafts, into the roadway that touches it.
- **Parameters:** Q = 30 m³/min and the other competition parameters. The tunnel height of 3 m is assumed.
- **Miners:** three at faces whose way out passes the inrush (0.3, 0.8 and 1.9 km from it), plus one control 4.3 km away.

## Known limitations
- The topology is generated automatically and was checked by eye only.
- Seals and doors are not modelled.
- Elevations are interpolated between survey stations.
