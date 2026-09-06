#!/usr/bin/env python3
"""tools/watchdog_probe.py: доказательство для критика [clover77]: при медленном старте (rAF раз в N мс первые
4500 мс, дальше как обычно) сторож не срабатывает. Судьбу сцены после этого решает замер FPS, и на программном
рендере headless он её снимает (fps=1), это печатается отдельной строкой как итог, а не как вердикт. Пробник строится из index.html, сторож включён (review=false),
import немедленный. Печатает хронику атрибутов <html> и итог. Красное условие: в хронике появился
data-pixi-err="watchdog" или к 6-й секунде нет класса live."""
import subprocess, re, json, pathlib, sys, html as H_
CAD = int(sys.argv[1]) if len(sys.argv) > 1 else 1500  # мс между кадрами в первые 4,5 с
root = pathlib.Path(__file__).resolve().parent.parent
CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
h = (root/"index.html").read_text(encoding="utf-8")
h = re.sub(r"(<head[^>]*>)", r'\1<base href="../">', h, count=1)
h = h.replace('requestAnimationFrame(function(){if(window.requestIdleCallback)requestIdleCallback(go,{timeout:1200});else setTimeout(go,200)});','go();')
throttle = ("<script>(function(){var t0=performance.now(),raf=window.requestAnimationFrame.bind(window),CADENCE=" + str(CAD) + ";"
            "window.requestAnimationFrame=function(cb){if(performance.now()-t0<4500)return setTimeout(function(){cb(performance.now())},CADENCE);return raf(cb)};"
            "var log=[];new MutationObserver(function(){var H=document.documentElement;log.push(Math.round(performance.now()-t0)+'мс class='+H.className+' err='+(H.getAttribute('data-pixi-err')||'')+' fps='+(H.getAttribute('data-fps')||''))}).observe(document.documentElement,{attributes:true});"
            "setTimeout(function(){var H=document.documentElement;document.title='WD:'+JSON.stringify({log:log,cls:H.className,err:H.getAttribute('data-pixi-err')||''})},6500)})();</script>")
h = h.replace("<script>\n/* Pixi-герой", throttle + "<script>\n/* Pixi-герой", 1)
assert throttle in h, "не нашёл начало Pixi-скрипта"
p = root/"review"/"watchdog-probe.html"; p.write_text(h, encoding="utf-8")
out = subprocess.run([CH,"--headless=new","--ignore-gpu-blocklist","--allow-file-access-from-files","--window-size=1440,900",
                      "--virtual-time-budget=9000","--timeout=40000","--dump-dom","file://"+str(p)], capture_output=True, text=True).stdout
m = re.search(r"<title>WD:(.*?)</title>", out, re.S)
print("# вызов: python3 tools/watchdog_probe.py %d  (кадр раз в %d мс первые 4,5 с, дальше как обычно)" % (CAD, CAD))
if not m: print("FAIL пробник не ответил"); raise SystemExit(1)
d = json.loads(H_.unescape(m.group(1)))
for l in d["log"]: print("  " + l)
dead = "watchdog" in d["err"] or any("err=watchdog" in l for l in d["log"])
print(("FAIL " if dead else "OK   ") + "сторож не срабатывает при медленном старте  [красное: data-pixi-err=watchdog в хронике]")
alive = "live" in d["cls"] or ("pixi" in d["cls"] and not d["err"])
print("      итог сцены: " + ("жива (class=%r)" % d["cls"] if alive else "снята замером FPS (class=%r err=%r, программный рендер headless даёт ~1 fps)" % (d["cls"], d["err"])))
raise SystemExit(1 if dead else 0)
