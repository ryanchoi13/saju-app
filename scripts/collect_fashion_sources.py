"""Refresh public source metadata without ingesting arbitrary recommendations.

Only explicitly registered public URLs are fetched. Robots rules, access walls,
HTTP failures and off-host redirects stop collection for that entry. Article
text is not retained; annotations are reviewed separately in the archive.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser

ROOT=Path(__file__).resolve().parents[1]
UA='DALHA-Research/0.1 (public source metadata review)'
MAX_BYTES=3_000_000


class SameHost(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if urlsplit(newurl).hostname != urlsplit(request.full_url).hostname:
            raise ValueError('cross_host_redirect_needs_review')
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def read_url(url):
    if urlsplit(url).scheme!='https':
        raise ValueError('https_required')
    with build_opener(SameHost).open(Request(url,headers={'User-Agent':UA}),timeout=12) as r:
        body=r.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES:raise ValueError('size_limit')
        return body, r.headers.get_content_charset() or 'utf-8'


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__();self.meta={};self.title=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('content'):
            key=a.get('property') or a.get('name')
            if key in ('og:title','og:image','article:published_time','author'):
                self.meta[key]=a['content'][:1000]
        if tag=='title':self.in_title=True
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title.append(data)


def collect(sources):
    robots={}
    for origin in sorted({f'https://{urlsplit(s["url"]).netloc}' for s in sources if s['access']=='public'}):
        parser=RobotFileParser()
        try:
            data,enc=read_url(origin+'/robots.txt');parser.parse(data.decode(enc,errors='replace').splitlines())
            robots[origin]=(parser,'read')
        except HTTPError as e:
            robots[origin]=(None,'absent' if e.code==404 else 'unavailable')
        except (URLError,ValueError,TimeoutError):robots[origin]=(None,'unavailable')
    def one(s):
        row={'source_id':s['id'],'url':s['url'],'checked_at':datetime.now(timezone.utc).isoformat()}
        if s['access']!='public':return dict(row,status='skipped_access_limited')
        parts=urlsplit(s['url']);parser,state=robots[f'https://{parts.netloc}']
        if state=='unavailable':return dict(row,status='robots_unavailable_review_needed')
        if parser and not parser.can_fetch(UA,s['url']):return dict(row,status='robots_disallowed')
        try:
            body,enc=read_url(s['url']);html=body.decode(enc,errors='replace')
            if any(x in html for x in ('전체 페이지를 읽으시려면','captcha-delivery.com','cf-chl-')):
                return dict(row,status='access_wall_detected')
            p=Metadata();p.feed(html)
            return dict(row,status='metadata_fetched',title=p.meta.get('og:title') or ''.join(p.title).strip(),
                        metadata=p.meta,body_sha256=hashlib.sha256(body).hexdigest(),bytes_read=len(body),
                        content_stored=False,score_changed=False)
        except (HTTPError,URLError,ValueError,TimeoutError) as e:
            return dict(row,status='fetch_failed',error=type(e).__name__,http_status=getattr(e,'code',None))
    with ThreadPoolExecutor(max_workers=3) as pool:return list(pool.map(one,sources))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    rows=collect(json.loads((ROOT/'fashion_v2/evidence_data/v1/sources.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    from collections import Counter
    print(json.dumps(dict(Counter(r['status'] for r in rows))))
