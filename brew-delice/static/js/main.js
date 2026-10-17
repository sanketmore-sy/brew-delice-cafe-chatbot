/* Brew Delice Café — site interactions (no framework). */
(function () {
  'use strict';
  const CFG = JSON.parse(document.getElementById('cfg').textContent);
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const money = (n) => CFG.currency + n;

  /* ---- session + tracking ---- */
  function gen() { return 's' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36); }
  let memSid = null;
  function sid() {
    try { let s = sessionStorage.getItem('bd_sid'); if (!s) { s = gen(); sessionStorage.setItem('bd_sid', s); } return s; }
    catch (e) { return memSid || (memSid = gen()); }
  }
  function track(event, extra) {
    const body = JSON.stringify(Object.assign({ session_id: sid(), event: event, source: 'web' }, extra || {}));
    try { fetch('/api/track', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body, keepalive: true }).catch(() => {}); } catch (e) {}
  }
  window.Brew = { cfg: CFG, sid: sid, track: track, money: money };
  const itemById = (id) => CFG.items.find((i) => i.id === id);
  const chat = () => window.BrewChat;

  /* ---- nav ---- */
  const nav = $('#nav'), burger = $('#burger'), links = $('#navlinks'), toTop = $('#toTop');
  function onScroll() {
    nav.classList.toggle('scrolled', window.scrollY > 8);
    toTop.classList.toggle('show', window.scrollY > 700);
  }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  burger.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    burger.setAttribute('aria-expanded', String(open));
  });
  links.addEventListener('click', (e) => { if (e.target.closest('a')) { links.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); } });
  toTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  /* ---- reveal + skeleton images ---- */
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.12 });
    $$('.reveal').forEach((el) => io.observe(el));
    const menuSec = $('#menu');
    const mo = new IntersectionObserver((es) => { if (es[0].isIntersecting) { track('menu_view'); mo.disconnect(); } }, { threshold: 0.3 });
    if (menuSec) mo.observe(menuSec);
  } else { $$('.reveal').forEach((el) => el.classList.add('in')); }
  $$('.card-img img').forEach((img) => {
    const done = () => img.parentElement.classList.add('loaded');
    img.complete ? done() : (img.addEventListener('load', done), img.addEventListener('error', done));
  });

  /* ---- menu tabs ---- */
  $$('.tab').forEach((t) => t.addEventListener('click', () => {
    $$('.tab').forEach((x) => x.classList.toggle('active', x === t));
    const cat = t.dataset.cat;
    $$('.grp').forEach((g) => { g.hidden = !(cat === 'all' || g.dataset.cat === cat); });
  }));

  /* ---- modals ---- */
  let lastFocus = null;
  function openModal(m) { lastFocus = document.activeElement; m.hidden = false; document.body.style.overflow = 'hidden'; const x = $('[data-close]', m); x && x.focus(); }
  function closeModals() { $$('.modal').forEach((m) => (m.hidden = true)); document.body.style.overflow = ''; if (lastFocus && lastFocus.focus) lastFocus.focus(); }
  $$('.modal').forEach((m) => m.addEventListener('click', (e) => { if (e.target === m || e.target.closest('[data-close]')) closeModals(); }));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModals(); });

  let currentItem = null;
  function openItem(id) {
    const it = itemById(id); if (!it) return;
    currentItem = it;
    $('#imImg').src = it.image; $('#imImg').alt = it.name + ' illustration';
    $('#imTitle').textContent = it.emoji + ' ' + it.name;
    $('#imPrice').textContent = money(it.price);
    $('#imDesc').textContent = it.description;
    openModal($('#itemModal'));
    track('item_selected', { item: id }); track('item_view', { item: id });
  }
  function openOrder(id) {
    const it = id ? itemById(id) : null;
    $('#omItem').textContent = it ? it.emoji + ' ' + it.name + ' — ' + money(it.price) : '';
    const list = $('#omList'); list.textContent = '';
    if (CFG.platforms.length) {
      $('#omTitle').textContent = 'Choose your ordering platform';
      CFG.platforms.forEach((p) => {
        const a = document.createElement('a');
        a.className = 'plink'; a.href = p.url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = 'Order on ' + p.label;
        a.addEventListener('click', () => track('platform_selected', { platform: p.key, item: id || null }));
        list.appendChild(a);
      });
    } else {
      $('#omTitle').textContent = 'Ordering';
      const note = document.createElement('div'); note.className = 'om-note';
      const b = document.createElement('b'); b.textContent = 'Online ordering platform could not be verified.';
      note.append(b, 'The exact Brew Delice Café listing could not be confirmed, so no direct order link is claimed. Use the search buttons to find us on Zomato / Swiggy, or contact the café / open Google Maps.');
      (CFG.search_platforms || []).forEach((p) => {
        const a = document.createElement('a'); a.className = 'plink'; a.href = p.url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = p.text;
        a.addEventListener('click', () => track('platform_selected', { platform: p.key + '_search', item: id || null }));
        list.appendChild(a);
      });
      const contact = document.createElement('button'); contact.className = 'btn btn-primary'; contact.textContent = '📩 Contact Café';
      contact.addEventListener('click', () => { closeModals(); if (chat()) { chat().open(); chat().sendAction('enquiry_start', id || null, 'Contact Café'); } });
      const maps = document.createElement('a'); maps.className = 'btn btn-ghost'; maps.href = CFG.maps_url; maps.target = '_blank'; maps.rel = 'noopener'; maps.textContent = '📍 Open Google Maps';
      maps.addEventListener('click', () => track('platform_selected', { platform: 'google_maps', item: id || null }));
      list.append(note, contact, maps);
    }
    openModal($('#orderModal'));
    track('order_click', { item: id || null });
  }
  window.Brew.openItem = openItem; window.Brew.openOrder = openOrder;

  document.addEventListener('click', (e) => {
    const v = e.target.closest('[data-view]'); if (v) { e.preventDefault(); openItem(v.dataset.view); return; }
    const o = e.target.closest('[data-order]'); if (o) { e.preventDefault(); openOrder(o.dataset.order || null); return; }
    const c = e.target.closest('[data-open-chat]'); if (c) { e.preventDefault(); links.classList.remove('open'); chat() && chat().open(); return; }
    const t = e.target.closest('[data-track-platform]'); if (t) track('platform_selected', { platform: t.dataset.trackPlatform });
    const card = e.target.closest('#attractions .card'); if (card) track('attraction_click', { item: card.dataset.id });
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.matches('.card')) openItem(e.target.dataset.id); });
  $('#imOrder').addEventListener('click', () => { const id = currentItem && currentItem.id; closeModals(); openOrder(id); });
  $('#imEnq').addEventListener('click', () => {
    const it = currentItem; closeModals();
    if (chat() && it) { chat().open(); chat().sendAction('enquiry_start', it.id, 'Add to enquiry: ' + it.name); }
  });

  /* ---- enquiry form ---- */
  const form = $('#enqForm'), msg = $('#enqMsg');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(form).entries());
    msg.className = 'form-msg'; msg.textContent = 'Sending…';
    try {
      const r = await fetch('/api/enquiry', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.assign(d, { session_id: sid() })) });
      const j = await r.json();
      if (j.ok) { msg.className = 'form-msg ok'; msg.textContent = '✅ ' + j.message; form.reset(); }
      else { msg.className = 'form-msg err'; msg.textContent = Object.values(j.errors || {}).join(' ') || 'Please check your details.'; }
    } catch (err) { msg.className = 'form-msg err'; msg.textContent = 'Could not send right now. Please try again.'; }
  });
})();
