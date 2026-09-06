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

## Проверки перед сдачей

```bash
bash review/shoot.sh 1440 900 d && bash review/shoot.sh 390 844 m   # кадры в оба языка
```
`review/` в .gitignore. Кадры секций снимаются через `review/rig.html` (копия index
со `<base>` и сдвигом документа `?sel=`/`?y=`), веер через `review/shot.html` (iframe,
`?end=1`). В iframe IntersectionObserver в headless не срабатывает, поэтому секции
только через rig. Грепом: ноль имён клиентов и ноль цен в видимом тексте, длинных
тире нет.
