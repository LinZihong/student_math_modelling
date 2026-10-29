"""Recompute every number quoted in the v9 text from 实验_09 records and confirm it appears in the paper."""
import json,re
from pathlib import Path
P=Path(__file__).resolve().parent;E9=P.parent/'实验_09_水源位置未知时的固定逃生路线'
S=json.loads((E9/'summary.json').read_text());V=json.loads((E9/'verification.json').read_text());RZ=json.loads((E9/'realized.json').read_text())
EX=json.loads((P/'tables/example.json').read_text());TR=json.loads((E9/'timeouts_rerun.json').read_text())
tex=' '.join((P/f).read_text() for f in ['main.tex','sections_model.tex','sections_appendix.tex']);tex=re.sub(r'\s+',' ',tex)
c30={r['region']:r for r in S['delay']['30']['counts']};o={k:v['outside'] for k,v in c30.items()};i={k:v['inside'] for k,v in c30.items()}
pq=S['delay']['30']['pairs'];pp=S['delay']['30']['per_pair'];R=S['resolution'];M=S['mechanism']
pct=lambda x,d=1:f'{x*100:.{d}f}\\%'
def rng(key,k):
 a=[R[f'zones_k{k}_v{v}']['30'][key]*100 for v in [0,1,2] if f'zones_k{k}_v{v}' in R];return f'{min(a):.0f}--{max(a):.0f}\\%'
fails=sum(o[r]['n']-o[r]['shortest'] for r in o);onset=sum(o[r]['shortest_fail_at_onset'] for r in o)
claims={
 # abstract and introduction
 '59\\%':round(pq['shortest']*100)==59,'69\\%':round(pq['avoid']*100)==69,'79\\%':round(pq['robust']*100)==79,'99.8\\%':f"{pp['exact']*100:.1f}"=='99.8',
 '52\\% of pairs':round(R['shaftcut_k2']['30']['robust']*100)==52,'31--36\\% for two zones':rng('robust',2)=='31--36\\%',
 # Section 4
 '720 of the 1,243':(o['NW']['shortest'],o['NW']['n'])==(720,1243),'659 of 1,139':(o['SW']['shortest'],o['SW']['n'])==(659,1139),
 '45 and 63':(o['SE']['n']-o['SE']['shortest'],o['NE']['n']-o['NE']['shortest'])==(45,63),
 '473 would happen':o['NW']['shortest_fail_at_onset']==473 and o['NW']['n']-o['NW']['shortest']==523,'441 of the 480':o['SW']['shortest_fail_at_onset']==441,
 '91\\%':round(onset/fails*100)==91,'130\\,m along':round(M['NW']['cut_median_km_from_shaft']*1000,-1)==130,'508 of the 523':M['NW']['cut_within_1km_of_shaft']==508,
 'the median is 280\\,m':round(M['SW']['cut_median_km_from_shaft']*1000,-1)==280,'58.7\\%':pct(pq['shortest']) in tex,
 'traps 2.8\\%':f"{RZ['shortest']*100:.1f}"=='2.8','13 times':round(RZ['shortest']/(1-pp['exact']))==13,
 # Section 5
 '1,200 of 1,243 (96.5\\%)':o['NW']['robust']==1200,'940 of 1,139':o['SW']['robust']==940,'462 end at':M['NW']['newly_to_other_shaft']==462,'207 of 281':M['SW']['newly_to_other_shaft']==207,
 '1,166 northwest':o['NW']['avoid']==1166,'838 southwest':o['SW']['avoid']==838,'446 of the 480':o['NW']['avoid']-o['NW']['shortest']==446,'179 of the 281':o['SW']['avoid']-o['SW']['shortest']==179,
 '364\\% longer':round(o['NW']['avoid_newly_median_extra']*100)==364,'median of 54\\%':round(o['NW']['robust_on_avoid_newly_median_extra']*100)==54,
 '267\\% extra':round(o['SW']['median_extra_newly']*100)==267,'812 starting points':o['NW']['cap20']==812,'961, against':o['NW']['cap50']==961,
 'from 14 to 97':(i['NW']['shortest'],i['NW']['robust'])==(14,97),'31 to 139':(i['SW']['shortest'],i['SW']['robust'])==(31,139),'25 to 138':(i['SE']['shortest'],i['SE']['robust'])==(25,138),'28 to 179':(i['NE']['shortest'],i['NE']['robust'])==(28,179),
 'to 78.8\\%':pct(pq['robust'])=='78.8\\%','rule to 69.2\\%':pct(pq['avoid'])=='69.2\\%','traps 1.3\\%':f"{RZ['robust_then_avoid']*100:.1f}"=='1.3','1.8\\% for the rule':f"{RZ['avoid']*100:.1f}"=='1.8',
 '6.88\\,km':f"{EX['shortest_km']:.2f}"=='6.88','8.36\\,km':f"{EX['robust_km']:.2f}"=='8.36','22\\% more':round(EX['extra']*100)==22,'130\\,m before the shaft':round(EX['cut_km_from_shaft']*1000,-1)==130,'about four hours':round(EX['robust_deadline_min']/60)==4,
 # Section 6
 '21.2\\%':f"{(1-pq['robust'])*100:.1f}"=='21.2','Only 0.2\\%':f"{(1-pp['exact'])*100:.1f}"=='0.2','other 21.0\\%':pct(pq['information_limited'])=='21.0\\%',
 'only 10\\%':round(R['zones_k1_v0']['30']['robust']*100)==10,'to 51--61\\%':rng('robust',4)=='51--61\\%','82\\% with sixteen':round(sum(R[f'zones_k16_v{v}']['30']['robust'] for v in [0,1,2])/3*100)==82,
 '97\\% with sixty-four':round(sum(R[f'zones_k64_v{v}']['30']['robust'] for v in [0,1,2])/3*100)==97,
 'all 167 junctions':S['shaft_area']['junctions']==167 and all(S['shaft_area']['partitions'][f'zones_k{k}_v{v}']['largest_share']==1 for k in [2,4,8,16] for v in [0,1,2]),
 'only 10--33\\%':f"{min(S['shaft_area']['partitions'][f'zones_k{k}_v{v}']['worst_zone_protected'] for k in [2,4,8,16] for v in [0,1,2])*100:.0f}--{max(S['shaft_area']['partitions'][f'zones_k{k}_v{v}']['worst_zone_protected'] for k in [2,4,8,16] for v in [0,1,2])*100:.0f}\\%"=='10--33\\%',
 '82\\% of starting points protected':round(S['shaft_area']['partitions']['quadrant']['worst_zone_protected']*100)==82,
 '51.7\\%':pct(R['shaftcut_k2']['30']['robust'])=='51.7\\%','69.0\\%':pct(R['shaftcut_k4']['30']['robust'])=='69.0\\%',
 '96.9\\%':pct(S['delay']['0']['pairs']['robust'])=='96.9\\%','84.1\\%':pct(S['delay']['10']['pairs']['robust'])=='84.1\\%','69.4\\%':pct(S['delay']['120']['pairs']['robust'])=='69.4\\%',
 '99.5\\% at two hours':pct(S['delay']['120']['per_pair']['exact'])=='99.5\\%','from 3\\% to 30\\%':(round(S['delay']['0']['pairs']['information_limited']*100),round(S['delay']['120']['pairs']['information_limited']*100))==(3,30),
 '98.9\\%':pct(R['zones_k128_v0']['10']['robust'])=='98.9\\%','97.9\\%':pct(R['zones_k128_v0']['60']['robust'])=='97.9\\%',
 # Section 7
 '56.9\\%':pct(S['inflow']['quadrant']['30']['pairs']['shortest'])=='56.9\\%','66.5\\%':pct(S['inflow']['quadrant']['30']['pairs']['avoid'])=='66.5\\%','71.6\\%':pct(S['inflow']['quadrant']['30']['pairs']['robust'])=='71.6\\%','stays at 99.7\\%':pct(S['inflow']['quadrant']['30']['per_pair']['exact'])=='99.7\\%',
 '211 junctions':S['breadth']['50']['sources']==211,'93.8\\%':pct(S['breadth']['50']['pairs']['shortest'])=='93.8\\%','97.8\\%':pct(S['breadth']['50']['pairs']['robust'])=='97.8\\%','is 2.1\\%':pct(S['breadth']['50']['pairs']['information_limited'])=='2.1\\%','19.0\\%':pct(S['breadth']['1000']['pairs']['information_limited'])=='19.0\\%',
 # Section 3 and appendices
 '2,558,244':S['queries']==2558244==V['record_consistency']['records'],'all but seven finished':len(TR)==7 and all(r['status']!='timeout' for r in TR),'within 18 seconds':max(r['seconds'] for r in TR)<=18 and all(r['status']=='no_common_route' for r in TR),'no common route exists':not S['timeouts'] and V['record_consistency']['timeouts']==0,
 '19,044 queries':V['regression_vs_experiment_07']=={'compared':19044,'mismatches':0},'747 parent':V['nested_zones']=={'parent_child_pairs':747,'violations':0},'23,012':V['forward_walks']=={'checks':23012,'failures':0},
}
bad=[k for k,ok in claims.items() if not ok];missing=[k for k in claims if k not in tex]
print(len(claims),'claims;',len(bad),'wrong;',len(missing),'not found in text')
for k in bad:print('WRONG',k)
for k in missing:print('MISSING',k)
assert V['passed'] and not bad and not missing
(P/'claims-check.json').write_text(json.dumps(dict(claims=len(claims),verification_passed=V['passed']),indent=1))
