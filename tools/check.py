#!/usr/bin/env python3
"""tools/check.py: проверки сайта Кассы перед сдачей. Код выхода 1, если что-то красное.
   --live  дополнительно сверяет живой адрес (KASSA_LIVE, по умолчанию Vercel), вес двух путей и три состояния.
   У каждого пункта названо красное условие (CDO [nectar76]); подсказки печатаются только при FAIL."""
import re, sys, os, gzip, html, hashlib, subprocess, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
os.chdir(root)
print("# вызов: python3 " + " ".join(sys.argv))
H = open("index.html", encoding="utf-8").read()
fails = []
def ok(name, cond, red, detail=""):
    print(("OK   " if cond else "FAIL ") + name + "  [красное: " + red + "]" + (("  " + detail) if (detail and not cond) else ""))
    if not cond: fails.append(name)

def refs_in(chunk):
    return {m.lstrip("./") for m in re.findall(r'\.?/?((?:img|fonts|vendor)/[^"\'\s)?]+)', chunk)}
scripts = re.findall(r"<script>(.*?)</script>", H, re.S)
style = re.search(r"<style>(.*?)</style>", H, re.S).group(1)
markup = re.sub(r"<style>.*?</style>", "", re.sub(r"<script>.*?</script>", "", H, flags=re.S), flags=re.S)
body = re.sub(r"<script>.*?</script>", "", H, flags=re.S); body = re.sub(r"<style>.*?</style>", "", body, flags=re.S)
text = html.unescape(re.sub(r"<[^>]+>", " ", body))

# 1. видимый текст
names = ["devago", "aselhands", "easy lounge", "friendly", "asel hands", "изи", "френдли", "девago"]
hits = [n for n in names if re.search(r"(?i)(?<![a-zа-яё])" + re.escape(n) + r"(?![a-zа-яё])", text)]
ok("имена клиентов в видимом тексте: ноль", not hits, "имя клиента в тексте или alt", str(hits))
alts = " ".join(re.findall(r'alt="([^"]*)"', H) + re.findall(r'data-alt-\w+="([^"]*)"', H))
ok("имена клиентов в alt: ноль", not [n for n in names if re.search(r"(?i)" + re.escape(n), alts)], "имя клиента внутри alt")
prices = re.findall(r"(?i)(\$|€|₽|₸|сум|usd|от \d|\d{2,}\s?(руб|долл|тыс))", text)
ok("цены в видимом тексте: ноль", not prices, "валюта или «от N» в тексте", str(prices[:3]))
ok("длинных тире нет", "—" not in text, "символ «—» в тексте")
digits = sorted(set(re.findall(r"\d+", text)))
ok("из цифр только 72", digits == ["72"], "любое другое число в тексте", str(digits))
B = H[H.index("<body"):]
ok("пар RU/EN поровну (в body)", B.count('lang="ru"') == B.count('lang="en"'), "у текста нет пары на втором языке", "%d ru / %d en" % (B.count('lang="ru"'), B.count('lang="en"')))
# 2. ассеты
refs = refs_in(H)
missing = [r for r in refs if not (root / r).exists()]
ok("все ссылки на img/, fonts/, vendor/ существуют", not missing, "ссылка на файл, которого нет в репе", str(missing))
files = {str(p.relative_to(root)) for p in list(root.glob("img/*")) + list(root.glob("fonts/*")) + list(root.glob("vendor/*"))}
unused = sorted(files - refs)
ok("лишних файлов в img/, fonts/, vendor/ нет", not unused, "файл в репе, на который нет ссылки", str(unused))
big = [f for f in root.glob("img/*.webp") if f.stat().st_size > 150_000]
ok("WebP <= 150 КБ", not big, "картинка тяжелее 150 000 Б", str([b.name for b in big]))
js = "".join(scripts).encode()
ok("встроенный JS <= 60 КБ gzip", len(gzip.compress(js)) <= 60_000, "gzip встроенных скриптов больше 60 000 Б", "%d" % len(gzip.compress(js)))
ok("внешних скриптов нет", not re.search(r'<script[^>]+src=', H) and "cdn." not in H, "тег script с src или адрес cdn")
ok("шапка без sticky и blur", not re.search(r"\.top\{[^}]*(sticky|fixed|backdrop)", style), "sticky/fixed/backdrop у .top")
tg_btns = re.findall(r'<a class="btn tg"[^>]*href="([^"]*)"', H)
ok("t.me Тахира в разметке обеих a.btn.tg", len(tg_btns) == 2 and all(u == "https://t.me/hellotakhir" for u in tg_btns), "кнопок не две, адрес не t.me/hellotakhir или #form в разметке", str(tg_btns))
ok("подстановки адреса скриптом нет", 'var TG=' not in H and 'a.href=TG' not in H, "адрес телеграма снова живёт в скрипте")
ok("транспорт формы стоит", "hq-live-production.up.railway.app/kassa/lead" in H, "эндпоинт формы изменён")
ok("тексты успеха формы", "Получил. Отвечаю сам." in H and "Got it. I reply myself." in H, "текст успеха формы изменён")
# 3. кремовой версии нет, облик не висит на классе движения (CDO [swallow], [pollen46], [pollen84])
H_noicon = re.sub(r'<link rel="icon"[^>]*>', "", H)
ok("кремовой версии в файле нет", not re.search(r"F4EFE7|\.card\{|\.deck\{|@keyframes fan|scroll\(root\)", H_noicon), "светлый токен #F4EFE7 (кроме favicon), .card/.deck, @keyframes fan или scroll(root) в файле")
rules = re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"@media[^{]*\{", "", style))
bad_rules = []
for sel, decl in rules:
    if "html.pixi" in sel or "html.live" in sel or "html.nowebgl" in sel:
        if "#scene" in sel or ".grain" in sel: continue
        if re.search(r"(^|;)\s*(background|background-color|color|--[\w-]+)\s*:", decl):
            bad_rules.append(sel.strip())
ok("облик не висит на классах pixi/live/nowebgl", not bad_rules, "background/color/--токен в правиле с html.pixi|live|nowebgl (кроме #scene, .grain)", str(bad_rules))
# 4. засечки покрывают текст обоих h1
try:
    from fontTools.ttLib import TTFont
    heads = re.findall(r"<h1[^>]*>(.*?)</h1>", H, re.S)
    htext = html.unescape(re.sub(r"<[^>]+>", "", " ".join(heads)))
    cover = set()
    for f in re.findall(r"font-family:'NotoSD'[^}]*url\(([^)]+)\)", style):
        t = TTFont(f); cover |= set(t.getBestCmap()); t.close()
    miss = sorted({c for c in htext if c.strip() and ord(c) not in cover})
    ok("засечки покрывают весь текст h1 (RU и EN)", not miss, "знак заголовка вне cmap подмножеств", "нет знаков: " + str(miss))
except ImportError:
    ok("засечки покрывают весь текст h1 (RU и EN)", False, "знак вне cmap", "fontTools не установлен: pip3 install fonttools brotli")
# 5. rig собран из текущего index
rig = root / "review" / "rig.html"
if rig.exists():
    m = re.search(r"rig-of-index:([0-9a-f]{16})", rig.read_text(encoding="utf-8"))
    ok("review/rig.html собран из текущего index", bool(m) and m.group(1) == hashlib.sha256(open("index.html","rb").read()).hexdigest()[:16], "хеш в риге не равен хешу index", "пересобери: python3 review/mkrig.py")

if "--live" in sys.argv:
    live = os.environ.get("KASSA_LIVE", "https://kassa-site.vercel.app/")
    def curl(*a):
        return subprocess.run(["curl", "-s", "--max-time", "20", *a], capture_output=True, text=True).stdout
    got = subprocess.run(["curl", "-s", "--max-time", "20", live], capture_output=True).stdout
    ok("живой index = репа (sha256)", hashlib.sha256(got).hexdigest() == hashlib.sha256(open("index.html", "rb").read()).hexdigest(), "прод отдаёт не тот index, что в репе")
    codes = {r: curl("-o", "/dev/null", "-w", "%{http_code}", live + r) for r in sorted(refs)}
    ok("живые ассеты отдаются", all(c == "200" for c in codes.values()), "ассет с прода не 200", str({r: c for r, c in codes.items() if c != "200"}))
    lead = "https://hq-live-production.up.railway.app/kassa/lead"
    ok("форма: preflight 204", curl("-o", "/dev/null", "-w", "%{http_code}", "-X", "OPTIONS", "-H", "Origin: " + live.rstrip("/"), "-H", "Access-Control-Request-Method: POST", lead) == "204", "OPTIONS не 204")
    ok("форма: пустое тело 400", curl("-o", "/dev/null", "-w", "%{http_code}", "-X", "POST", "-H", "Content-Type: application/json", "-d", "{}", lead) == "400", "пустая заявка принята")
    # вес двух путей (CDO [pollen46], [pollen84]): brotli по сети, тела без заголовков, RU и EN отдельно.
    # база = засечки (NotoSD из @font-face) и картинки из <style> (плита); путь с Pixi = база + всё, на что ссылается
    # ветка движения (head после проверки WebGL и последний script) и чего нет ни в базе, ни в разметке.
    BASE_CEILING, PIXI_CEILING = 48000, 250000
    serif = set(re.findall(r"font-family:'NotoSD'[^}]*url\(([^)]+)\)", style))
    base_hero = serif | {r for r in refs_in(style) if r.startswith("img/")}
    head_branch = scripts[0][scripts[0].index("if(gl){"):] if scripts and "if(gl){" in scripts[0] else ""
    pixi_extra = (refs_in(head_branch + scripts[-1]) - base_hero - refs_in(markup))
    ru_only = set()
    for m in re.findall(r'l==="ru"\?\[([^\]]*)\]', scripts[0]): ru_only |= refs_in(m)
    def wire(path):
        out = curl("-o", "/dev/null", "-H", "Accept-Encoding: br", "-w", "%{http_code} %{size_download}", live + path).split()
        return (out[0] if out else "000", int(out[1]) if len(out) > 1 else 0)
    sizes = {a: wire(a) for a in sorted(base_hero | pixi_extra)}
    bad = [a for a, (c, _) in sizes.items() if c != "200"]
    ok("ассеты героя отдаются с прода", not bad, "ассет базы или ветки не 200", str(bad))
    base_ru = sum(sizes[a][1] for a in base_hero); base_en = sum(sizes[a][1] for a in base_hero if a not in ru_only)
    pixi_sz = sum(sizes[a][1] for a in pixi_extra)
    detail = ", ".join("%s %d" % (a, sizes[a][1]) for a in sorted(sizes))
    ok("база без Pixi RU <= %d Б" % BASE_CEILING, base_ru <= BASE_CEILING, "плита + засечки RU по проводу больше потолка", "RU %d: %s" % (base_ru, detail))
    ok("база без Pixi EN <= %d Б" % BASE_CEILING, base_en <= BASE_CEILING, "плита + засечки EN по проводу больше потолка", "EN %d" % base_en)
    ok("путь с Pixi RU <= %d Б" % PIXI_CEILING, base_ru + pixi_sz <= PIXI_CEILING, "база + ветка движения RU больше потолка", "RU %d (ветка: %s)" % (base_ru + pixi_sz, ", ".join(sorted(pixi_extra))))
    ok("путь с Pixi EN <= %d Б" % PIXI_CEILING, base_en + pixi_sz <= PIXI_CEILING, "база + ветка движения EN больше потолка", "EN %d" % (base_en + pixi_sz))
    ok("связь потолков: база %d + измеренный Pixi <= %d" % (BASE_CEILING, PIXI_CEILING), BASE_CEILING + pixi_sz <= PIXI_CEILING, "потолок базы плюс pixi.min.js по проводу больше потолка пути с Pixi", "%d + %d = %d" % (BASE_CEILING, pixi_sz, BASE_CEILING + pixi_sz))
    print("      по проводу: база RU %d / EN %d, с Pixi RU %d / EN %d" % (base_ru, base_en, base_ru + pixi_sz, base_en + pixi_sz))
    # три состояния облика (CDO [ledge39]): A pixi, B без WebGL, C после сторожа
    st = subprocess.run([sys.executable, "tools/states.py"], capture_output=True, text=True)
    last = [l for l in st.stdout.splitlines() if l.startswith("ИТОГ состояний")]
    ok("три состояния облика без расхождений", st.returncode == 0, "точка палитры или типографики разошлась между pixi / без WebGL / после сторожа", (last[0] if last else st.stdout[-300:]))
    for l in st.stdout.splitlines():
        if l.startswith("РАСХОЖДЕНИЕ"): print("      " + l)
print("\nИТОГ:", "КРАСНОЕ " + str(fails) if fails else "всё зелёное")
sys.exit(1 if fails else 0)
