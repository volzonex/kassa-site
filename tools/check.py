#!/usr/bin/env python3
"""tools/check.py: проверки сайта Кассы перед сдачей. Код выхода 1, если что-то красное.
   --live  дополнительно сверяет живой адрес и эндпоинт формы."""
import re, sys, os, gzip, html, hashlib, subprocess, pathlib, json
root = pathlib.Path(__file__).resolve().parent.parent
os.chdir(root)
H = open("index.html", encoding="utf-8").read()
fails = []
def ok(name, cond, detail=""):
    print(("OK   " if cond else "FAIL ") + name + (("  " + detail) if detail else ""))
    if not cond: fails.append(name)

body = re.sub(r"<script>.*?</script>", "", H, flags=re.S)
body = re.sub(r"<style>.*?</style>", "", body, flags=re.S)
text = html.unescape(re.sub(r"<[^>]+>", " ", body))
# 1. видимый текст: ни имён клиентов, ни цен, ни длинных тире
names = ["devago", "aselhands", "easy lounge", "friendly", "asel hands", "изи", "френдли", "девago"]
hits = [n for n in names if re.search(r"(?i)(?<![a-zа-яё])" + re.escape(n) + r"(?![a-zа-яё])", text)]
ok("имена клиентов в видимом тексте: ноль", not hits, str(hits))
prices = re.findall(r"(?i)(\$|€|₽|₸|сум|usd|от \d|\d{2,}\s?(руб|долл|тыс))", text)
ok("цены в видимом тексте: ноль", not prices, str(prices[:3]))
ok("длинных тире нет", "—" not in H.replace("—", "—") and "—" not in text, "")
digits = sorted(set(re.findall(r"\d+", text)))
ok("из цифр только 72", digits == ["72"], str(digits))
# 2. языки: у каждого lang=ru есть пара lang=en в том же родителе (грубо: счётчики равны)
B = H[H.index("<body"):]
ok("пар RU/EN поровну (в body)", B.count('lang="ru"') == B.count('lang="en"'), f'{B.count(chr(108)+"ang=%sru%s" % (chr(34),chr(34)))} ru / {B.count(chr(108)+"ang=%sen%s" % (chr(34),chr(34)))} en')
# 3. ассеты на месте и все используются
refs = set(re.findall(r'(?:src|href)=["\']((?:img|fonts|vendor)/[^"\']+)', H)) | set(re.findall(r'url\(((?:img|fonts|vendor)/[^)]+)\)', H)) | set(re.findall(r'(?:import|loadImg)\("((?:img|fonts|vendor)/[^"]+)"', H))
missing = [r for r in refs if not (root / r).exists()]
ok("все ссылки на img/ и fonts/ существуют", not missing, str(missing))
files = {str(p.relative_to(root)) for p in list(root.glob("img/*")) + list(root.glob("fonts/*")) + list(root.glob("vendor/*"))}
unused = sorted(files - refs)
ok("лишних файлов в img/ и fonts/ нет", not unused, str(unused))
big = [f for f in root.glob("img/*.webp") if f.stat().st_size > 150_000]
ok("WebP <= 150 КБ", not big, str([b.name for b in big]))
js = "".join(re.findall(r"<script>(.*?)</script>", H, re.S)).encode()
ok("JS <= 60 КБ gzip", len(gzip.compress(js)) <= 60_000, f"{len(gzip.compress(js))} байт gzip")
ok("внешних скриптов нет", not re.search(r'<script[^>]+src=', H) and "cdn." not in H)
ok("шапка без sticky и blur", not re.search(r"\.top\{[^}]*(sticky|fixed|backdrop)", H))
ok("t.me Тахира стоит", 'var TG="https://t.me/hellotakhir"' in H)
ok("транспорт формы стоит", "hq-live-production.up.railway.app/kassa/lead" in H)
ok("тексты успеха формы", "Получил. Отвечаю сам." in H and "Got it. I reply myself." in H)
if "--live" in sys.argv:
    def curl(*a):
        return subprocess.run(["curl", "-s", "--max-time", "20", *a], capture_output=True, text=True).stdout
    live = os.environ.get("KASSA_LIVE", "https://hq-live-production.up.railway.app/kassa/")
    got = subprocess.run(["curl", "-s", "--max-time", "20", live], capture_output=True).stdout
    ok("живой index = репа (sha256)", hashlib.sha256(got).hexdigest() == hashlib.sha256(open("index.html", "rb").read()).hexdigest())
    for r in sorted(refs):
        code = curl("-o", "/dev/null", "-w", "%{http_code}", live + r)
        if code != "200": ok("живой ассет " + r, False, code)
    ok("живые ассеты отдаются", all(curl("-o", "/dev/null", "-w", "%{http_code}", live + r) == "200" for r in refs))
    lead = "https://hq-live-production.up.railway.app/kassa/lead"
    ok("форма: preflight 204", curl("-o", "/dev/null", "-w", "%{http_code}", "-X", "OPTIONS", "-H", "Origin: https://kassa-site.vercel.app", "-H", "Access-Control-Request-Method: POST", lead) == "204")
    ok("форма: пустое тело 400", curl("-o", "/dev/null", "-w", "%{http_code}", "-X", "POST", "-H", "Content-Type: application/json", "-d", "{}", lead) == "400")
print("\nИТОГ:", "КРАСНОЕ " + str(fails) if fails else "всё зелёное")
sys.exit(1 if fails else 0)
