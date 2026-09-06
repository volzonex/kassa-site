# КАССА: сайт венчура Тахира «сайт и лендинг за 72 часа»

Один файл `index.html`, шрифты и картинки рядом, репа `volzonex/kassa-site`,
Vercel деплоит из неё (импорт проекта делается вручную в дашборде, см. память
штаба). Спека CDO: письмо [wave] 06.09, тексты CCO: `warroom/kassa/CONTENT-EN-RU.md`
(формулировки не трогать без сверки с CCO), стенд колоды: `warroom/cdo/kassa/hero-deck.html`.

## Как устроено

- **Языки.** Оба текста в DOM: `<span lang="ru">` / `<span lang="en">` (или `<p lang>`),
  показ по `data-lang` на `html`. Скрипт в `<head>` ставит язык до первой отрисовки:
  `?lang=` > `localStorage.kassa-lang` > `navigator.language` (ru* -> ru, иначе en).
  Кнопки RU | EN в шапке и подвале, атрибут `lang` на html и `<title>` переключаются.
- **Колода в hero.** CSS из стенда CDO дословно: `.hero` 170vh, sticky-сцена 100vh,
  `.card` со scroll-driven `animation-timeline: scroll(root)`, `animation-range: 0 70vh`,
  позы c1..c4 нарисованы руками. Единственное отличие от стенда: ширина карты
  `--cw: min(62vw, 760px, calc((100vh - 470px) * 1.6))`, чтобы на низких экранах карта
  не уходила за сцену. Мобила <=640: сцена статична, столбик с rotateX(10deg).
  Без поддержки scroll-driven (старый WebView) скрипт ведёт те же transform по
  скроллу сам (30 строк), GSAP не подключён: нечего качать ради fallback.
- **Pixi-герой (спека CDO [sunset], 06.09).** Решение в `<head>`: нет reduced-motion и есть
  WebGL-контекст, значит `html.pixi` до первой отрисовки (без вспышки светлого героя). Второй
  скрипт внизу грузит `vendor/pixi.min.js` (ESM-сборка pixi.js 8.15.0, 200 КБ gzip) через
  `import()` только при `html.pixi`. Сцена в той же sticky героя: `#scene` (канвас, z 0),
  `.grain` (SVG feTurbulence, z 3), текст `.hd` (z 2). Слои снизу вверх: плита комнаты
  `img/room.webp` (Higgsfield по смете f671, комната, не работа) с параллаксом от курсора,
  вуаль `#0A0B0D` .42, три плиты кропов (рамка 52..86% высоты, тень, кромка латунью, блюр и
  тинт дальних), световой проход blend add, DisplacementFilter с процедурной картой 512.
  Прогресс от `getBoundingClientRect()` секции: 0 стопка (смещения x0.25, displacement 26),
  0.5 и дальше разложено. На узких (<900) плиты по x `w*.52 - i*14`, по y `h*.42` (у стенда .70,
  там текст перекрывал плиты). Страховка: любой сбой `import`/`init`/картинок снимает
  `html.pixi` и ставит `html.nowebgl`, остаётся CSS-колода; первые 2 с меряется FPS (в
  `html[data-fps]`): ниже 40 снимается displacement, ниже 28 канвас уничтожается;
  IntersectionObserver останавливает ticker вне экрана; DPR `min(dpr,2)`, на узких 1.5.
  `?end=1` форсирует разложенную позу для кадров. `PIXI.Assets.load` в headless виснет,
  поэтому картинки через `new Image()` + `Texture.from`.
- **Картинки.** `img/*.webp` 1280x800, кроп без названий компаний: devago это hero
  без верхней навигации, для трёх лендингов секция под hero (полоса цифр + следующая
  секция). Снимались из локальных исходников `сайты/<name>/index.html` со сдвигом
  документа `html{margin-top:-Y}` при окне 1280x800 и скрытыми fixed-элементами
  (скролл через `scrollTo` headless-скриншот не видит).
- **Вход по кадру.** `.rv` + IntersectionObserver -> `.in` один раз; анимация 400 мс,
  только transform/opacity, задержки `--d` 0/80/160/240 мс. Галочки оффера рисуются
  `stroke-dashoffset`, экраны портфолио выравниваются из rotateY(±6deg).
  `prefers-reduced-motion`: всё в конечном состоянии. Без JS (`html` без класса `js`)
  всё видно сразу.
- **72.** Набегает 0 -> 72 за 700 мс при 50% видимости, один раз; без JS и при
  reduced-motion стоит 72.
- **Форма.** `POST https://hq-live-production.up.railway.app/kassa/lead` (CTO, письмо
  [violet] 06.09): `{name, contact, kind: лендинг|сайт|бот, message, lang}`, CORS *,
  400 без name/contact. Заявка уходит Тахиру в телеграм от Адъютанта и в JSONL на томе
  hq-live. Успех: форма прячется, на её месте «Получил. Отвечаю сам.». Ошибка: моно-текст
  рядом с кнопкой, поля не чистятся. Ханипот `website`.
- **t.me Тахира:** `https://t.me/hellotakhir` (CTO взял через Bot API). Ссылки «бот ->
  Pronto» ведут на форму с чипом «бот»: у Pronto пока нет своего адреса.

## Где живёт

- **Прод (с 06.09 16:46):** `https://kassa-site.vercel.app`, проект `takhir-llc/kassa-site`
  связан с GitHub, пуш в `main` деплоит сам (CTO поднял с Air через Vercel CLI, ручной
  импорт больше не нужен). Заголовки и кэш из `vercel.json`, `tools/`, `review/` и
  `CLAUDE.md` не уезжают (`.vercelignore`). После пуша сверять sha256 отданного index с
  репой: `curl -s https://kassa-site.vercel.app/ | shasum -a 256`.
- **Запасной адрес:** `https://hq-live-production.up.railway.app/kassa/` (`/kassa` без
  слэша даёт 301). Заливка: `PUT …/kassa/<путь>` с `Authorization: Bearer
  <KASSA_DEPLOY_SECRET>`, тело = сырые байты; секрет в письме CTO [topaz37] в архиве почты
  craftsman за 2026-09, в репу не класть. Прокси отдаёт без gzip и с no-store, это его
  свойство, не дефект сборки.
- **Домен:** пока только `kassa-site.vercel.app`, свой домен выбирает Тахир; og:url и
  canonical ставить, когда решит.
- **Стандарт Тахира с 06.09 (CTO [valley73]):** боевые анимации только Pixi.js, CSS-анимации
  допустимы для демок. Эта сборка на CSS scroll-driven оставлена как рабочий fallback по
  слову COO до спеки CDO с подтверждённым сроком.

## Проверки перед сдачей

```bash
python3 tools/check.py --live      # текст без имён и цен, пары языков, ассеты, веса, живой адрес, эндпоинт формы
bash review/shoot.sh 1440 900 d && bash review/shoot.sh 390 844 m   # кадры в оба языка
```
`tools/`, `review/` и `CLAUDE.md` в `.vercelignore`, на прод не уезжают.
Pixi-герой: `bash review/shoot-pixi.sh desk` (стопка, веер, без WebGL через `--disable-3d-apis`,
reduced-motion через `--force-prefers-reduced-motion`) и `bash review/shoot-pixi.sh mob` (390
через iframe). Кадр с живого телефона в Telegram остаётся за Тахиром.
`review/` в .gitignore. Кадры секций снимаются через `review/rig.html` (копия index
со `<base>` и сдвигом документа `?sel=`/`?y=`), веер через `review/shot.html` (iframe,
`?end=1`). Headless Chrome не даёт окно уже 500px, поэтому 390 всегда через
iframe (`shot.html` грузит `rig.html` внутрь, сдвиг делает сам rig, IntersectionObserver
так срабатывает; скролл iframe снаружи его не будит). В iframe rAF под virtual-time
не идёт, цифра 72 на мобильных кадрах может стоять «0», это артефакт рига. Грепом: ноль имён клиентов и ноль цен в видимом тексте, длинных
тире нет. Запасной путь колоды (старый WebView) проверяется копией рига с
`window.CSS={supports:()=>false}` перед скриптом и `.card{animation:none!important}`:
`shot.html?rig=rig-nosda.html&y=300` должен дать полувеер только от скрипта
(`review/d-ru-fan-jsonly-300.png`, проверено 06.09). Копия кадров приёмки для CDO
лежит в `warroom/kassa/review/` (у CDO нет дерева `сайты/`).
