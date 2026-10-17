/* Brew Delice Café — chat widget. All bot text is inserted with textContent (XSS-safe). */
(function () {
  'use strict';
  const B = window.Brew, CFG = B.cfg;
  const $ = (s) => document.querySelector(s);
  const chat = $('#chat'), fab = $('#chatFab'), body = $('#chatBody'), chips = $('#chatChips'), form = $('#chatForm'), input = $('#chatInput');
  const QUICK = [['🍽 Menu', 'menu'], ['⭐ Main Attractions', 'attractions'], ['💰 Prices', 'prices'], ['📍 Find Us', 'location'],
                 ['🕐 Timings', 'timings'], ['🛵 Order Online', 'order'], ['💬 Enquiry', 'enquiry_start']];
  let opened = false, queue = Promise.resolve();
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function scroll() { body.scrollTo({ top: body.scrollHeight, behavior: 'smooth' }); }
  function add(node) { body.appendChild(node); scroll(); return node; }
  function bubble(role, text) { return add(el('div', 'msg ' + role, text)); }
  function typing() { const t = el('div', 'typing'); t.append(el('i'), el('i'), el('i')); return add(t); }

  function open() {
    chat.hidden = false; fab.classList.add('hide'); fab.setAttribute('aria-expanded', 'true');
    if (!opened) { opened = true; welcome(); B.track('chat_open'); }
    setTimeout(() => input.focus({ preventScroll: true }), 150);
  }
  function close() { chat.hidden = true; fab.classList.remove('hide'); fab.setAttribute('aria-expanded', 'false'); fab.focus(); }

  function welcome() {
    const w = el('div', 'welcome'); const img = el('img'); img.src = CFG.profile; img.alt = CFG.business + ' profile'; img.width = 74; img.height = 74;
    w.append(img, el('b', null, CFG.business), el('small', null, 'Virtual assistant · replies instantly'));
    body.appendChild(w);
    bubble('bot', 'Hi! 👋 Welcome to Brew Delice Café.');
    bubble('bot', 'I can help you explore our menu, prices, offers, location and ordering options.');
    chips.textContent = '';
    QUICK.forEach(([label, action]) => {
      const b = el('button', 'qbtn', label); b.type = 'button';
      b.addEventListener('click', () => sendAction(action, null, label)); chips.appendChild(b);
    });
  }

  /* ---- server calls (queued so replies never interleave) ---- */
  function call(payload) {
    queue = queue.then(async () => {
      const t = typing();
      let res = null;
      try {
        const [r] = await Promise.all([
          fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.assign({ session_id: B.sid() }, payload)) }).then((x) => x.json()),
          wait(550)]);
        res = r;
      } catch (e) { await wait(300); }
      t.remove();
      if (!res || res.error) { bubble('bot', 'Sorry, I couldn\'t reach the server. Please try again.'); return; }
      await render(res);
    });
    return queue;
  }
  function send(text) { text = (text || '').trim(); if (!text) { return call({ message: '' }); } bubble('user', text); return call({ message: text }); }
  function sendAction(action, payload, label) { bubble('user', label || action); return call({ action: action, payload: payload, label: label }); }

  /* ---- rendering ---- */
  async function render(res) {
    document.querySelectorAll('.fbbox').forEach((n) => n.remove());
    for (const m of res.messages) {
      const node = renderMsg(m);
      if (node) { add(node); await wait(220); }
    }
    if (res.buttons && res.buttons.length) add(buttons(res.buttons));
    if (res.ask_feedback) add(feedbackBox());
  }
  function renderMsg(m) {
    if (m.type === 'text') return el('div', 'msg bot', m.text);
    if (m.type === 'menu') {
      const c = el('div', 'mcard'); c.appendChild(el('h4', null, m.title));
      m.items.forEach((it) => {
        const r = el('button', 'mrow'); r.type = 'button';
        r.append(el('span', null, it.emoji), el('span', 'n', it.name), el('span', 'p', it.currency + it.price));
        r.addEventListener('click', () => sendAction('item:' + it.id, null, it.emoji + ' ' + it.name));
        c.appendChild(r);
      });
      return c;
    }
    if (m.type === 'item_card') {
      const it = m.item, c = el('div', 'mcard icard'); const img = el('img'); img.src = it.image; img.alt = it.name + ' illustration';
      const ib = el('div', 'ib'); ib.append(el('b', null, it.emoji + ' ' + it.name), el('span', 'price', it.currency + it.price));
      c.append(img, ib); return c;
    }
    if (m.type === 'platforms') {
      const c = el('div', 'mcard'); c.appendChild(el('h4', null, m.search ? 'Find us on delivery apps' : 'Order online')); const l = el('div', 'plist');
      m.platforms.forEach((p) => {
        const a = el('a', 'plink', p.text || ('Order on ' + p.label)); a.href = p.url; a.target = '_blank'; a.rel = 'noopener';
        a.addEventListener('click', () => B.track('platform_selected', { platform: p.search ? p.key + '_search' : p.key, item: m.item }));
        l.appendChild(a);
      });
      c.appendChild(l); return c;
    }
    if (m.type === 'location') {
      const c = el('div', 'mcard'); c.appendChild(el('h4', null, 'Find us'));
      const s = el('div', 'srows'); const r1 = el('div'); r1.append(el('span', null, 'Café'), el('b', null, m.name));
      const r2 = el('div'); r2.append(el('span', null, 'Address'), el('b', null, m.address)); s.append(r1, r2); c.appendChild(s); return c;
    }
    if (m.type === 'hours') {
      const c = el('div', 'mcard'); const s = el('div', 'srows');
      const rows = typeof m.hours === 'string' ? [['Hours', m.hours]] : Object.entries(m.hours);
      rows.forEach(([k, v]) => { const r = el('div'); r.append(el('span', null, k), el('b', null, String(v))); s.appendChild(r); });
      c.appendChild(s); return c;
    }
    if (m.type === 'summary') {
      const c = el('div', 'mcard'); c.appendChild(el('h4', null, 'Your enquiry')); const s = el('div', 'srows');
      m.rows.forEach(([k, v]) => { const r = el('div'); r.append(el('span', null, k), el('b', null, v)); s.appendChild(r); });
      c.appendChild(s); return c;
    }
    return null; // 'no_platform' is expressed by the text + Contact/Maps buttons
  }
  function buttons(list) {
    const row = el('div', 'qr');
    list.forEach((b) => {
      if (b.url) {
        const a = el('a', 'qbtn', b.label); a.href = b.url; a.target = '_blank'; a.rel = 'noopener';
        a.addEventListener('click', () => B.track('platform_selected', { platform: (b.track && b.track.platform) || 'link' }));
        row.appendChild(a);
      } else {
        const x = el('button', 'qbtn', b.label); x.type = 'button';
        x.addEventListener('click', () => { row.querySelectorAll('button').forEach((q) => (q.disabled = false)); sendAction(b.action, b.payload, b.label); });
        row.appendChild(x);
      }
    });
    return row;
  }
  function feedbackBox() {
    const f = el('div', 'fbbox'); f.appendChild(el('span', null, 'Was this helpful?'));
    [['👍 Yes', 'feedback_yes'], ['👎 No', 'feedback_no']].forEach(([l, a]) => {
      const b = el('button', 'qbtn fb', l); b.type = 'button';
      b.addEventListener('click', () => { f.remove(); sendAction(a, null, l); }); f.appendChild(b);
    });
    return f;
  }

  fab.addEventListener('click', open);
  $('#chatClose').addEventListener('click', close);
  form.addEventListener('submit', (e) => { e.preventDefault(); const v = input.value; input.value = ''; send(v); });
  window.BrewChat = { open: open, close: close, send: send, sendAction: sendAction };
})();
