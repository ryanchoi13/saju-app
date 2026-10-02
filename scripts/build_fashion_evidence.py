"""Build a self-contained review document and queryable, versioned SQLite archive."""
import argparse
import base64
from collections import Counter
import itertools
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from fashion_v2.evidence_review import DATA, DIMENSIONS, load_archive, validate_archive, context_matches, score_item, evaluate_outfit


def encode(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))


def sparse_scores(archive,ctx):
    pairs={(g,c) for r in archive['rules'] if context_matches(r['scope'],ctx)
           for g in r['garment_ids'] for c in r['color_ids']}
    for g,c in sorted(pairs):
        yield g,c,score_item(archive,g,c,ctx)


def build_database(a,path):
    if path.exists():path.unlink()
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE colors (id TEXT PRIMARY KEY,name TEXT NOT NULL,hex TEXT UNIQUE NOT NULL,pool TEXT NOT NULL,data TEXT NOT NULL);
        CREATE TABLE garments (id TEXT PRIMARY KEY,name TEXT NOT NULL,category TEXT NOT NULL);
        CREATE TABLE sources (id TEXT PRIMARY KEY,title TEXT NOT NULL,url TEXT NOT NULL,data TEXT NOT NULL);
        CREATE TABLE observations (id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(id),style_tier TEXT NOT NULL,data TEXT NOT NULL);
        CREATE TABLE rules (id TEXT PRIMARY KEY,data TEXT NOT NULL);
        CREATE TABLE patterns (id TEXT PRIMARY KEY,data TEXT NOT NULL);
        CREATE TABLE benchmarks (id TEXT PRIMARY KEY,data TEXT NOT NULL);
        CREATE TABLE review_events (id TEXT PRIMARY KEY,data TEXT NOT NULL);
        CREATE TABLE contexts (id TEXT PRIMARY KEY,gender TEXT,age_band TEXT,season TEXT,tpo TEXT);
        CREATE TABLE item_scores (context_id TEXT REFERENCES contexts(id),garment_id TEXT REFERENCES garments(id),color_id TEXT REFERENCES colors(id),score INTEGER CHECK(score BETWEEN 1 AND 5),status TEXT NOT NULL,details TEXT NOT NULL,PRIMARY KEY(context_id,garment_id,color_id));
        CREATE INDEX item_scores_lookup ON item_scores(garment_id,color_id,context_id);
        CREATE VIEW full_matrix AS SELECT x.id context_id,g.id garment_id,c.id color_id,s.score,COALESCE(s.status,'unassessed') status FROM contexts x CROSS JOIN garments g CROSS JOIN colors c LEFT JOIN item_scores s ON s.context_id=x.id AND s.garment_id=g.id AND s.color_id=c.id;
        ''')
        db.execute('INSERT INTO metadata VALUES (?,?)',('manifest',encode(a['manifest'])))
        db.executemany('INSERT INTO colors VALUES (?,?,?,?,?)',[(c['id'],c['name'],c['hex'],c['pool'],encode(c)) for c in a['colors']])
        db.executemany('INSERT INTO garments VALUES (?,?,?)',[(g['id'],g['name'],g['category']) for g in a['garments']])
        db.executemany('INSERT INTO sources VALUES (?,?,?,?)',[(s['id'],s['title'],s['url'],encode(s)) for s in a['sources']])
        db.executemany('INSERT INTO observations VALUES (?,?,?,?)',[(o['id'],o['source_id'],o['style_tier'],encode(o)) for o in a['observations']])
        for name in ('rules','patterns','benchmarks','review_events'):
            db.executemany(f'INSERT INTO {name} VALUES (?,?)',[(x['id'],encode(x)) for x in a[name]])
        scored=0
        for values in itertools.product(*DIMENSIONS.values()):
            ctx=dict(zip(DIMENSIONS,values));cid='-'.join(values)
            db.execute('INSERT INTO contexts VALUES (?,?,?,?,?)',(cid,*values))
            rows=[(cid,g,c,r['score'],r['status'],encode(r)) for g,c,r in sparse_scores(a,ctx)]
            db.executemany('INSERT INTO item_scores VALUES (?,?,?,?,?,?)',rows);scored+=len(rows)
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        return scored


def build(output,reference_images=None):
    a=load_archive();validate_archive(a);output.mkdir(parents=True,exist_ok=True)
    a['benchmark_results']={b['id']:evaluate_outfit(a,b['items'],b['context']) for b in a['benchmarks']}
    refresh=ROOT/'review-output/evidence/source-refresh.json'
    a['source_refresh']=json.loads(refresh.read_text()) if refresh.exists() else []
    svg_path=output/'benchmark-drawings.json'
    subprocess.run(['node',str(ROOT/'scripts/render_fashion_evidence.mjs'),str(svg_path)],check=True,cwd=ROOT)
    svgs=json.loads(svg_path.read_text());photos={}
    if reference_images:
        for oid,filename in [('O03','myq-pink-beige.jpg'),('O01','pink-shirt-denim.jpg')]:
            file=reference_images/filename
            if file.exists():photos[oid]='data:image/jpeg;base64,'+base64.b64encode(file.read_bytes()).decode()
    template=(ROOT/'scripts/fashion_evidence_review.html').read_text()
    for key,value in [('__DATA__',a),('__SVGS__',svgs),('__PHOTOS__',photos)]:
        template=template.replace(key,encode(value).replace('<','\\u003c'))
    html_path=output/'dalha-fashion-evidence-review.html';html_path.write_text(template)
    snapshot=output/'data';snapshot.mkdir(exist_ok=True)
    for p in sorted(DATA.glob('*.json')):shutil.copyfile(p,snapshot/p.name)
    (snapshot/'benchmark-results.json').write_text(json.dumps(a['benchmark_results'],ensure_ascii=False,indent=2)+'\n')
    if refresh.exists():shutil.copyfile(refresh,snapshot/'source-refresh.json')
    db_path=output/'dalha-fashion-evidence.sqlite';scored=build_database(a,db_path)
    report=dict(version=a['manifest']['version'],colors=len(a['colors']),garments=len(a['garments']),sources=len(a['sources']),observations=len(a['observations']),rules=len(a['rules']),patterns=len(a['patterns']),benchmarks=len(a['benchmarks']),contexts=120,possible_matrix_cells=120*len(a['garments'])*len(a['colors']),scored_draft_cells=scored,explicit_age_observations=sum(o['age_band'] is not None for o in a['observations']),whole_outfit_auto_approvals=0,production_enabled=False,source_refresh=dict(Counter(x['status'] for x in a['source_refresh'])))
    (output/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    readme=(ROOT/'docs/fashion-evidence-review-v0.1.md').read_text()
    (output/'README.md').write_text(readme)
    # The zip is the reproducible data bundle; HTML remains the separate viewing artifact.
    zip_path=output/'dalha-fashion-evidence-v0.1.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(snapshot.glob('*.json')):z.write(p,'data/'+p.name)
        for p in (db_path,output/'README.md',output/'build-report.json',svg_path):z.write(p,p.name)
        for rel in ('fashion_v2/evidence_review.py','scripts/collect_fashion_sources.py','scripts/build_fashion_evidence.py','scripts/render_fashion_evidence.mjs','scripts/fashion_evidence_review.html','backend/tests/test_fashion_evidence_review.py'):
            z.write(ROOT/rel,'code/'+rel)
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reference-images',type=Path);args=p.parse_args()
    build(args.output.resolve(),args.reference_images.resolve() if args.reference_images else None)
