#!/usr/bin/env python3
"""tools/states.py: облик героя в трёх состояниях по вычисленным стилям в фиксированных точках
(CDO [ledge39]). A: html.pixi, живая сцена. B: WebGL выключен. C: после срабатывания сторожа.
Требование: ноль расхождений по палитре и типографике, разница только в движении (канвас, зерно).
Красное условие: любая точка облика разошлась между состояниями. Код выхода 1 при расхождениях.
Пробник строится из index.html с <base> на корень сайта; для A сторож выключен (review=true),
чтобы headless на программном рендере не снял сцену до замера."""
import subprocess, json, re, sys, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
POINTS = [("body","background-color"),("body","color"),(".top","background-color"),(".top","color"),
          ("h1","color"),("h1","font-family"),(".cta .btn","background-color"),(".cta .btn","color"),
          (".sub","color"),(".s72","background-color"),(".num","color"),(".kard","background-color"),
          (".kard","color"),(".checks","color"),("input[type=text]","background-color"),
          ("input[type=text]","color"),(".foot","color"),(".hero .sticky","background-color")]
MOTION = {"#scene canvas","html.class","data-pixi-err"}
def probe(mode):
    h = (root/"index.html").read_text(encoding="utf-8")
    h = re.sub(r"(<head[^>]*>)", r'\1<base href="../">', h, count=1)
    h = h.replace('requestAnimationFrame(function(){if(window.requestIdleCallback)requestIdleCallback(go,{timeout:1200});else setTimeout(go,200)});','go();')
    if mode == "A":
        h = h.replace('var forceQ=null,review=false;','var forceQ=null,review=true;')
    js = ("<script>(function(){var P=%s;function samp(){var o={};P.forEach(function(p){var el=document.querySelector(p[0]);"
          "o[p[0]+' / '+p[1]]=el?getComputedStyle(el).getPropertyValue(p[1]).trim():'нет элемента'});"
          "o['#scene canvas']=!!document.querySelector('#scene canvas');o['html.class']=document.documentElement.className;"
          "o['data-pixi-err']=document.documentElement.getAttribute('data-pixi-err')||'';document.title='STATE:'+JSON.stringify(o)}"
          "var mode=%s,t0=Date.now();(function tick(){var H=document.documentElement,err=H.getAttribute('data-pixi-err'),el=Date.now()-t0;"
          "if(mode==='A'&&document.querySelector('#scene canvas')&&el>1500)return samp();"
          "if(mode==='B'&&el>1500)return samp();"
          "if(mode==='C'&&err)return setTimeout(samp,300);"
          "if(el>13000)return samp();setTimeout(tick,100)})()})();</script>") % (json.dumps(POINTS), json.dumps(mode))
    h = h.replace("</body>", js + "</body>")
    p = root/"review"/("state-probe-%s.html" % mode); p.write_text(h, encoding="utf-8")
    flags = ["--disable-3d-apis"] if mode == "B" else []
    out = subprocess.run([CH,"--headless=new","--ignore-gpu-blocklist","--allow-file-access-from-files","--window-size=1440,900",
                          "--virtual-time-budget=16000","--timeout=45000",*flags,"--dump-dom","file://"+str(p)], capture_output=True, text=True).stdout
    m = re.search(r"<title>STATE:(.*?)</title>", out, re.S)
    if not m: return None
    import html as H_; return json.loads(H_.unescape(m.group(1)))
def main():
    S = {m: probe(m) for m in ("A","B","C")}
    bad = [m for m in S if S[m] is None]
    if bad: print("FAIL пробник не отдал состояние:", bad); sys.exit(1)
    for m in S: print("%s: класс=%r канвас=%s err=%r" % (m, S[m]["html.class"], S[m]["#scene canvas"], S[m]["data-pixi-err"]))
    keys = [k for k in S["A"] if k not in MOTION]
    N = len(POINTS)  # ожидаемое число точек: константа, не длина словаря (критик [fern70])
    measured = [k for k in keys if all(S[m].get(k) not in (None, "", "нет элемента") for m in S)]
    diffs = [(k, S["A"][k], S["B"][k], S["C"][k]) for k in keys if not (S["A"][k] == S["B"][k] == S["C"][k])]
    for k,a,b,c in diffs: print("РАСХОЖДЕНИЕ %-40s A=%s | B=%s | C=%s" % (k,a,b,c))
    print("измерилось точек: %d из %d (красное: селектор не нашёлся хотя бы в одном состоянии)" % (len(measured), N))
    print("ИТОГ состояний: %d расхождений из %d точек, измерилось %d из %d (красное: расхождение или недоизмер)" % (len(diffs), N, len(measured), N))
    sys.exit(1 if (diffs or len(measured) < N) else 0)
if __name__ == "__main__": main()
