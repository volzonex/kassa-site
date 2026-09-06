// Заявка с формы Кассы: телеграм Тахира + таблица.
// Переменные окружения проекта на Vercel (ставит CTO):
//   TG_BOT_TOKEN  токен бота, который пишет Тахиру
//   TG_CHAT_ID    chat_id Тахира
//   SHEET_WEBHOOK (необязательно) URL Apps Script / вебхука таблицы, принимает JSON
// Без TG_BOT_TOKEN и TG_CHAT_ID функция честно отвечает 503, форма показывает ошибку и не чистит поля.
module.exports = async function (req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") { res.statusCode = 405; return res.end(); }
  let b = req.body;
  if (typeof b === "string") { try { b = JSON.parse(b); } catch (e) { b = {}; } }
  b = b || {};
  const clean = (v, n) => String(v || "").replace(/\s+/g, " ").trim().slice(0, n || 300);
  const name = clean(b.name), contact = clean(b.contact), kind = clean(b.kind, 20);
  const message = String(b.message || "").trim().slice(0, 2000), lang = clean(b.lang, 2), page = clean(b.page, 300);
  if (!name || !contact) { res.statusCode = 400; return res.end(JSON.stringify({ error: "name and contact required" })); }
  const token = process.env.TG_BOT_TOKEN, chat = process.env.TG_CHAT_ID, sheet = process.env.SHEET_WEBHOOK;
  if (!token || !chat) { res.statusCode = 503; return res.end(JSON.stringify({ error: "transport not configured" })); }
  const KIND = { landing: "лендинг", site: "сайт", bot: "бот" };
  const text = ["Заявка с сайта Касса", "Имя: " + name, "Контакт: " + contact,
    kind ? "Что строит: " + (KIND[kind] || kind) : "", message ? "Сообщение: " + message : "",
    "Язык: " + (lang || "ru"), page].filter(Boolean).join("\n");
  const r = await fetch("https://api.telegram.org/bot" + token + "/sendMessage", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chat, text: text, disable_web_page_preview: true })
  });
  if (!r.ok) { res.statusCode = 502; return res.end(JSON.stringify({ error: "telegram failed" })); }
  if (sheet) {
    try {
      await fetch(sheet, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ts: new Date().toISOString(), name, contact, kind, message, lang, page }) });
    } catch (e) { /* таблица не должна ронять заявку, телеграм уже ушёл */ }
  }
  res.statusCode = 200; res.setHeader("Content-Type", "application/json"); res.end(JSON.stringify({ ok: true }));
};
