#!/usr/bin/env python3
"""Cross-check every numeric table in the IEEE Access manuscript against published artifacts.

Tables: tab:full (incl. Hit@10 CIs from the fit JSON), tab:meta-full, tab:delta, tab:bm25,
tab:titan-full, tab:titan-delta, tab:exact, tab:titan-endpoints.
Usage: python3 scripts/erb/verify_paper_tables.py   (exit 1 on any mismatch)
"""
import os, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import json, re
A='artifacts/published/'
tex=open('papers/ieee-vector-drift/access/main.tex').read()
def env(label):
    i=tex.index('\\label{%s}'%label); j=tex.index('\\end{tabular}',i); return tex[i:j]
def rows(block):
    out=[]
    for line in block.split('\\\\'):
        line=line.replace('\\midrule','').replace('\\toprule','');cells=[c.strip() for c in line.split('&')]
        if len(cells)>2: out.append(cells)
    return out
def num(s):
    s=s.replace('$','').replace('+','').replace('^\\dagger','').strip()
    try: return float(s)
    except: return None
bad=[]
def chk(name,got,exp,tol=0.0015):
    if exp is None or got is None or abs(got-exp)>tol: bad.append(f"{name}: tex={got} artifact={exp}")
def k(s): return int(float(s.replace('k',''))*1000)
# OpenAI full
sw=json.load(open(A+'erb_full_primary200_to100k.json'))
runs={(r['condition'],r['corpus_scale_size']):r for r in sw['runs']}
for c in rows(env('tab:full'))[1:]:
    cond=c[0].split()[-1]; N=k(c[1]); r=runs[(cond,N)]
    for i,m in [(2,'hit_at_1'),(3,'hit_at_5'),(4,'hit_at_10'),(6,'document_recall'),(7,'mrr')]:
        chk(f'full {cond} {N} {m}',num(c[i]),r[m],0.0006)
fit=json.load(open(A+'erb_full_primary200_to100k_fit.json'))
fci={p['N']:p['hit_at_10_ci95']['ci95'] for p in fit['raw_points']}
for c in rows(env('tab:full'))[1:]:
    if c[0].split()[-1]=='raw':
        lo,hi=[float(x) for x in re.findall(r'[\d.]+',c[5])]
        N=k(c[1]); chk(f'CI lo {N}',lo,fci[N][0],0.0001); chk(f'CI hi {N}',hi,fci[N][1],0.0001)
for c in rows(env('tab:meta-full'))[1:]:
    N=k(c[0]); r=runs[('meta',N)]
    for i,m in [(1,'hit_at_1'),(2,'hit_at_5'),(3,'hit_at_10'),(4,'mrr')]: chk(f'meta {N} {m}',num(c[i]),r[m],0.0006)
for c in rows(env('tab:delta'))[1:]:
    N=k(c[0]); chk(f'delta {N}',num(c[3]),runs[('meta',N)]['hit_at_10']-runs[('raw',N)]['hit_at_10'],0.0006)
# BM25
bm=json.load(open(A+'erb_bm25_baseline_primary200.json'))
br={r.get('corpus_scale_size',r.get('N')):r for r in bm['runs']}
for c in rows(env('tab:bm25'))[1:]:
    N=k(c[0]); r=br[N]
    for i,m in [(1,'hit_at_1'),(2,'hit_at_5'),(3,'hit_at_10'),(4,'mrr')]: chk(f'bm25 {N} {m}',num(c[i]),r[m],0.0006)
# Titan
ti=json.load(open(A+'erb_titan_primary200_to100k.json'))
tr={(r['condition'],r['corpus_scale_size']):r for r in ti['runs']}
for c in rows(env('tab:titan-full'))[1:]:
    cond=c[0].split()[-1]; N=k(c[1]); r=tr[(cond,N)]
    for i,m in [(2,'hit_at_1'),(3,'hit_at_5'),(4,'hit_at_10'),(5,'mrr')]: chk(f'titan {cond} {N} {m}',num(c[i]),r[m],0.0006)
for c in rows(env('tab:titan-delta'))[1:]:
    N=k(c[0])
    chk(f'tdelta raw {N}',num(c[1]),tr[('raw',N)]['hit_at_10']); chk(f'tdelta meta {N}',num(c[2]),tr[('meta',N)]['hit_at_10'])
    chk(f'tdelta T {N}',num(c[3]),tr[('meta',N)]['hit_at_10']-tr[('raw',N)]['hit_at_10'],0.0006)
    chk(f'tdelta O {N}',num(c[4]),runs[('meta',N)]['hit_at_10']-runs[('raw',N)]['hit_at_10'],0.0006)
# exact
for f,emb in [('exact_control_mvp.json','OpenAI'),('exact_control_titan.json','Titan V2')]:
    ex={x['corpus_scale_size']:x for x in json.load(open(A+f))['comparisons']}
    for c in rows(env('tab:exact'))[1:]:
        if not c[0].endswith(emb): continue
        N=k(c[1]); x=ex[N]
        for i,m in [(2,'exact_hit_at_1'),(3,'hnsw_hit_at_1'),(4,'exact_hit_at_10'),(5,'hnsw_hit_at_10'),(6,'delta_hit_at_10_exact_minus_hnsw'),(7,'hit10_disagreements')]:
            chk(f'exact {emb} {N} {m}',num(c[i]),x.get(m),0.0006)
# endpoints
bs=json.load(open(A+'openai_vs_titan_bootstrap.json'))['endpoint']
mm={'Hit@1':'hit_at_1','Hit@10':'hit_at_10','MRR':'mrr'}
for c in rows(env('tab:titan-endpoints'))[1:]:
    s=c[0].split()[-1]; m=mm[c[1]]; e=bs[m]; pre='hnsw' if s=='HNSW' else 'exact'
    chk(f'ep {s} {m} openai drop',num(c[4]),e[f'openai_{pre}_drop']['estimate'],0.0006)
    chk(f'ep {s} {m} titan drop',num(c[7]),e[f'titan_{pre}_drop']['estimate'],0.0006)
    est,lo,hi=[float(x) for x in re.findall(r'-?[\d.]+',c[8].replace('+',''))]
    d=e[f'{pre}_titan_minus_openai_drop']; chk(f'ep {s} {m} diff',est,d['estimate'],0.0006); chk(f'ep {s} {m} lo',lo,d['ci95'][0],0.0006); chk(f'ep {s} {m} hi',hi,d['ci95'][1],0.0006)
# seed / primary-400 robustness
seed0=json.load(open(A+'erb_seed0_endpoints_primary200.json'))
s0={r['corpus_scale_size']:r for r in seed0['runs']}
p400=json.load(open(A+'erb_endpoints_primary400.json'))
p4={r['corpus_scale_size']:r for r in p400['runs']}
for c in rows(env('tab:seed'))[1:]:
    N=k(c[0])
    chk(f'seed42 {N}',num(c[1]),runs[('raw',N)]['hit_at_10'],0.0006)
    chk(f'seed0 {N}',num(c[2]),s0[N]['hit_at_10'],0.0006)
    chk(f'p400 {N}',num(c[3]),p4[N]['hit_at_10'],0.002)  # rounded to 3dp in tex
    chk(f'overlap200 {N}',num(c[4]),runs[('raw',N)]['hit_at_10'],0.0006)
# ef_search ablation
efab=json.load(open(A+'ef_search_ablation_100k.json'))
efc={c['ef_search']:c for c in efab['comparisons']}
for c in rows(env('tab:ef'))[1:]:
    ef=int(c[0].split()[0])
    chk(f'ef {ef} hit1',num(c[1]),efc[ef]['hit_at_1'],0.0006)
    chk(f'ef {ef} hit10',num(c[2]),efc[ef]['hit_at_10'],0.0006)
    chk(f'ef {ef} mrr',num(c[3]),efc[ef]['mrr'],0.0006)
# length-matched BM25 sensitivity check (RQ2 prose + Sec V-H prose, not a table)
bm8191=json.load(open(A+'erb_bm25_baseline_primary200_chars8191.json'))
b8={r['corpus_scale_size']:r for r in bm8191['runs']}
chk('bm25-8191 5k hit10',0.825,b8[5000]['hit_at_10'],0.0006)
chk('bm25-8191 100k hit10',0.705,b8[100000]['hit_at_10'],0.0006)

print("MISMATCHES:" if bad else "ALL TABLES MATCH", *bad, sep='\n  ')
sys.exit(1 if bad else 0)
