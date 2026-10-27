"""Check completed tables against retained paths and cell-level records."""
import json
import math
import pandas as pd
from run import OUT,dataset
from model.routing import walk,latest_departure


def main():
    origins=pd.read_csv(OUT/'origins.csv')
    menus=pd.read_csv(OUT/'menus.csv')
    cells=pd.read_csv(OUT/'menu_test_cells.csv')
    records=json.loads((OUT/'selected_paths.json').read_text())
    checked=0
    for case in ['competition','cad']:
        G,adj,exits,miners,meta=dataset(case)
        lookup={(a.a,a.b):a for aa in adj.values() for a in aa}
        for r in records:
            if r['case']!=case:continue
            path=[lookup[u,v] for u,v in zip(r['nodes'],r['nodes'][1:])]
            assert r['nodes'][-1] in exits
            assert len(set(r['nodes']))==len(r['nodes'])
            assert math.isfinite(walk(path,r['departure_lower_s'])[0])
            assert abs(walk(path,60)[0]-r['arrival_s'])<1e-6
            assert r['departure_upper_s']-r['departure_lower_s']<=.010001
            row=origins[(origins['case']==case)&(origins.origin==r['origin'])].iloc[0]
            assert walk(path,60)[0]-60 <= (1+r['eps'])*row.travel_min*60+1e-6
            checked+=1
        design=json.loads((OUT/f'{case}_menu_design.json').read_text())
        a={x['node'] for x in design['sources'] if x['split']=='train'}
        b={x['node'] for x in design['sources'] if x['split']=='test'}
        assert len(a)==len(b)==8 and not a&b
    for r in menus.itertuples():
        c=cells[(cells['case']==r.case)&(cells.origin==r.origin)&(cells.k==r.k)]
        assert int(c.covered.sum())==r.test_covered
        assert int(c.oracle_feasible.sum())==r.test_possible
        assert int(c.route_exists.sum())==r.test_feasible
    for _,g in menus.groupby(['case','origin']):
        train=list(g.sort_values('k').train_covered)
        assert train==sorted(train)
    assert len(origins)==87
    for r in origins.to_dict('records'):
        values=[r[f'budget{x}_deadline_min'] for x in ['0.0','0.01','0.05','0.1']]
        assert all(b>=a-1/60 for a,b in zip(values,values[1:]))
    print(f'Validated {checked} saved budget routes, {len(menus)} menu rows, {len(cells)} held-out cell records, 87 origins, and disjoint source splits.')


if __name__=='__main__':main()
