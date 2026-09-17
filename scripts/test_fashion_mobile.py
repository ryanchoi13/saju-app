"""Actual app modal in Chromium, with explicitly synthetic engine input."""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import os
import shutil
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'fashion-review-artifacts'

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    fixture=json.loads((OUT/'teal-camel.json').read_text())['contexts']
    results=[]; errors=[]
    try:
        with sync_playwright() as p:
            exe=os.environ.get('DALHA_CHROMIUM_EXECUTABLE') or shutil.which('chromium')
            browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
            page=browser.new_page(viewport={'width':390,'height':844})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
            page.goto(base+'/index.html')
            page.wait_for_function('Boolean(window.DalhaGarments)')
            page.wait_for_function("Boolean(document.querySelector('link[data-fashion-layout]')?.sheet)")
            original_overflow=page.evaluate('getComputedStyle(document.body).overflow')
            page.evaluate('''ctx=>{
              currentFortuneData={daily_fortune:{fashion_v2:{[getStyleTpo()]:ctx}}};
              connectFashionV2Summary();openFashionV2Modal();
            }''',fixture['casual'])
            for width,height in [(360,800),(390,844),(430,932),(360,640),(1280,900)]:
                page.set_viewport_size({'width':width,'height':height})
                for n in (0,1):
                    page.evaluate('(n)=>showFashionV2Slide(n,false)',n)
                    page.wait_for_timeout(100)
                    dimensions=page.evaluate('''n=>{
                      const panel=document.querySelectorAll('.fashion-v2-slide')[n];
                      const shoe=panel.querySelector('[data-role="shoes"]');
                      const box=shoe.getBoundingClientRect(),view=panel.getBoundingClientRect();
                      const footer=document.querySelector('.fashion-v2-footer').getBoundingClientRect();
                      return {width:innerWidth,height:innerHeight,number:n+1,
                        horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
                        shoeVisible:box.top>=view.top && box.bottom<=view.bottom+1,
                        shoeInsideSVG:box.bottom<=panel.querySelector('svg').getBoundingClientRect().bottom+1,
                        footerVisible:footer.top>=0 && footer.bottom<=innerHeight+1,
                        shoe:{top:box.top,bottom:box.bottom},panel:{top:view.top,bottom:view.bottom}};
                    }''',n)
                    page.screenshot(path=str(OUT/'latest-mobile-check.png'))
                    assert not dimensions['horizontalOverflow'],dimensions
                    assert dimensions['shoeInsideSVG'],dimensions
                    assert dimensions['footerVisible'],dimensions
                    # On short screens the panel may scroll; the shoes must be reachable.
                    if not dimensions['shoeVisible']:
                        page.locator('.fashion-v2-slide').nth(n).evaluate('(e)=>e.scrollTop=e.scrollHeight')
                        assert page.locator('.fashion-v2-slide').nth(n).evaluate('''e=>{
                          const p=e.getBoundingClientRect(),s=e.querySelector('[data-role="shoes"]').getBoundingClientRect();
                          return s.top>=p.top && s.bottom<=p.bottom+1;
                        }''')
                        dimensions['scrollRequired']=True
                    else: dimensions['scrollRequired']=False
                    results.append(dimensions)
                    if width==390:
                        page.screenshot(path=str(OUT/f'mobile-recommendation-{n+1}.png'))
            page.evaluate('closeFashionV2Modal()')
            page.wait_for_timeout(100)
            assert page.locator('#fashionV2Modal').evaluate("e=>e.classList.contains('hidden')")
            assert page.evaluate('getComputedStyle(document.body).overflow')==original_overflow
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close()
    (OUT/'browser-check.json').write_text(json.dumps({'passed':True,'syntheticInput':True,'realPhone':False,'results':results,'errors':errors},ensure_ascii=False,indent=2))
    print(json.dumps({'passed':True,'viewports':5,'looksPerViewport':2,'errors':errors}))

if __name__=='__main__': main()
