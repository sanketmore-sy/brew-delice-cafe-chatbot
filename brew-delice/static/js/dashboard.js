/* Brew Delice Café — admin dashboard. Uses Chart.js when available (local vendor file, then CDN);
   otherwise a tiny built-in canvas renderer keeps the charts working offline. */
(function () {
  'use strict';
  const ITEMS = JSON.parse(document.getElementById('items').textContent);
  const $ = (id) => document.getElementById(id);
  const PALETTE = ['#b8571f', '#6b4630', '#d98a3d', '#24160f', '#a8977f', '#8a5a36', '#e2b77a', '#4f3a2b'];
  const label = (k) => ITEMS[k] || ({ google_maps: 'Google Maps', google_search: 'Google Search', link: 'Other link' }[k]) || (k ? k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, ' ') : k);
  let chartLib = null, charts = {};

  function loadScript(src) {
    return new Promise((res) => { const s = document.createElement('script'); s.src = src; s.onload = () => res(!!window.Chart); s.onerror = () => res(false); document.head.appendChild(s); setTimeout(() => res(!!window.Chart), 4000); });
  }
  async function initLib() {
    if (window.Chart) return true;
    if (document.body.dataset.chartLocal === '1' && (await loadScript('/static/vendor/chart.umd.js'))) return true;   // drop chart.umd.js into static/vendor/ for fully-offline Chart.js
    if (navigator.onLine !== false && (await loadScript('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'))) return true;
    return false;                                                                                                      // built-in canvas renderer takes over
  }

  /* ---------- minimal canvas fallback ---------- */
  function prep(cv) {
    const dpr = window.devicePixelRatio || 1, w = cv.clientWidth || 300, h = cv.clientHeight || 230;
    cv.width = w * dpr; cv.height = h * dpr; const g = cv.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h);
    g.font = '12px Inter, system-ui, sans-serif'; return { g, w, h };
  }
  function fbBar(cv, labels, data) {
    const { g, w, h } = prep(cv), pad = { l: 34, r: 10, t: 12, b: 34 }, max = Math.max(1, ...data), step = Math.ceil(max / 4) || 1, top = step * 4;
    g.strokeStyle = 'rgba(36,22,15,.12)'; g.fillStyle = '#6f6258'; g.textAlign = 'right';
    for (let i = 0; i <= 4; i++) { const y = pad.t + (h - pad.t - pad.b) * (1 - i / 4); g.beginPath(); g.moveTo(pad.l, y); g.lineTo(w - pad.r, y); g.stroke(); g.fillText(String(i * step), pad.l - 6, y + 4); }
    const bw = (w - pad.l - pad.r) / data.length;
    data.forEach((v, i) => {
      const bh = (h - pad.t - pad.b) * v / top, x = pad.l + i * bw + bw * 0.18, y = h - pad.b - bh;
      g.fillStyle = PALETTE[0]; g.beginPath(); g.roundRect ? g.roundRect(x, y, bw * 0.64, bh, 5) : g.rect(x, y, bw * 0.64, bh); g.fill();
      g.fillStyle = '#24160f'; g.textAlign = 'center'; if (v) g.fillText(String(v), x + bw * 0.32, y - 4);
      g.fillStyle = '#6f6258'; g.fillText(labels[i].length > 11 ? labels[i].slice(0, 10) + '…' : labels[i], x + bw * 0.32, h - 14);
    });
  }
  function fbLine(cv, labels, data) {
    const { g, w, h } = prep(cv), pad = { l: 34, r: 14, t: 14, b: 34 }, max = Math.max(1, ...data), step = Math.ceil(max / 4), top = step * 4;
    g.strokeStyle = 'rgba(36,22,15,.12)'; g.fillStyle = '#6f6258'; g.textAlign = 'right';
    for (let i = 0; i <= 4; i++) { const y = pad.t + (h - pad.t - pad.b) * (1 - i / 4); g.beginPath(); g.moveTo(pad.l, y); g.lineTo(w - pad.r, y); g.stroke(); g.fillText(String(i * step), pad.l - 6, y + 4); }
    const n = data.length, px = (i) => pad.l + (n === 1 ? (w - pad.l - pad.r) / 2 : i * (w - pad.l - pad.r) / (n - 1)), py = (v) => h - pad.b - (h - pad.t - pad.b) * v / top;
    g.strokeStyle = PALETTE[0]; g.lineWidth = 2.5; g.beginPath(); data.forEach((v, i) => (i ? g.lineTo(px(i), py(v)) : g.moveTo(px(i), py(v)))); g.stroke();
    data.forEach((v, i) => { g.fillStyle = PALETTE[0]; g.beginPath(); g.arc(px(i), py(v), 4, 0, 7); g.fill(); g.fillStyle = '#6f6258'; g.textAlign = 'center'; g.fillText(labels[i].slice(5), px(i), h - 14); g.fillStyle = '#24160f'; g.fillText(String(v), px(i), py(v) - 9); });
  }
  function fbDonut(cv, labels, data) {
    const { g, w, h } = prep(cv), total = data.reduce((a, b) => a + b, 0) || 1, r = Math.min(h - 20, w * 0.5) / 2, cx = r + 12, cy = h / 2; let a0 = -Math.PI / 2;
    data.forEach((v, i) => { const a1 = a0 + 2 * Math.PI * v / total; g.fillStyle = PALETTE[i % PALETTE.length]; g.beginPath(); g.moveTo(cx, cy); g.arc(cx, cy, r, a0, a1); g.closePath(); g.fill(); a0 = a1; });
    g.fillStyle = '#fffaf1'; g.beginPath(); g.arc(cx, cy, r * 0.58, 0, 7); g.fill();
    g.textAlign = 'left'; labels.slice(0, 9).forEach((l, i) => { const y = 16 + i * 20; if (y > h - 6) return; g.fillStyle = PALETTE[i % PALETTE.length]; g.fillRect(cx + r + 16, y - 9, 10, 10); g.fillStyle = '#24160f'; g.fillText(l + ' (' + data[i] + ')', cx + r + 32, y); });
  }

  /* ---------- unified chart API ---------- */
  function draw(id, type, labels, data) {
    const cv = $(id), card = cv.parentElement; let em = card.querySelector('.empty');
    if (charts[id]) { charts[id].destroy(); delete charts[id]; }
    if (!data.length) { cv.style.display = 'none'; if (!em) { em = document.createElement('div'); em.className = 'empty'; em.textContent = 'No data yet — interact with the chatbot to see this chart.'; card.appendChild(em); } return; }
    cv.style.display = ''; if (em) em.remove();
    if (chartLib) {
      const colors = type === 'doughnut' ? labels.map((_, i) => PALETTE[i % PALETTE.length]) : PALETTE[0];
      charts[id] = new window.Chart(cv, { type: type === 'line' ? 'line' : type, data: { labels, datasets: [{ data, backgroundColor: colors, borderColor: PALETTE[0], borderWidth: type === 'line' ? 3 : 0, borderRadius: type === 'bar' ? 6 : 0, tension: .3, fill: false }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: type === 'doughnut', position: 'right' } }, scales: type === 'doughnut' ? {} : { y: { beginAtZero: true, ticks: { precision: 0 } } } } });
    } else (type === 'bar' ? fbBar : type === 'line' ? fbLine : fbDonut)(cv, labels, data);
  }

  /* ---------- data ---------- */
  const set = (id, v) => { $(id).textContent = v; };
  function entries(o, map) { const k = Object.keys(o); return [k.map((x) => (map ? label(x) : x)), k.map((x) => o[x])]; }
  async function refresh() {
    const inc = $('scope').value;
    const [a, e] = await Promise.all([fetch('/api/analytics?include_demo=' + inc).then((r) => r.json()), fetch('/api/enquiries?include_demo=' + inc).then((r) => r.json())]);
    const k = a.kpis;
    set('k-conv', k.conversations); set('k-menu', k.menu_views); set('k-views', k.item_views); set('k-order', k.order_clicks); set('k-enq', k.enquiries);
    set('k-top', k.most_popular_item ? label(k.most_popular_item) : '—'); set('k-msg', k.messages); set('k-fb', k.fallbacks); set('k-plat', k.platform_clicks);
    set('k-feed', k.feedback_yes + ' / ' + k.feedback_no);
    set('r-enq', k.enquiry_conversion_rate + '%'); set('r-ctr', k.order_ctr + '%');
    $('demoCount').textContent = a.demo_rows ? '(' + a.demo_rows + ' seeded demo rows present)' : '';
    const c = a.charts;
    let [l, d] = entries(c.items_selected, true); draw('c-items', 'bar', l, d);
    [l, d] = entries(c.order_clicks_by_item, true); draw('c-orders', 'bar', l, d);
    [l, d] = entries(c.intents, true); draw('c-intents', 'doughnut', l, d);
    [l, d] = entries(c.enquiries_over_time, false); draw('c-enq', 'line', l, d);
    [l, d] = entries(c.platform_clicks, true); draw('c-plat', 'bar', l, d);
    renderEnq(e); renderFb(a.feedback_details);
  }
  function renderEnq(rows) {
    const tb = $('enqBody'); tb.textContent = ''; $('enqEmpty').hidden = rows.length > 0;
    rows.forEach((r) => {
      const tr = document.createElement('tr');
      [r.id, r.name, r.contact, r.message, r.item ? label(r.item) : '—', r.source, r.ts].forEach((v) => { const td = document.createElement('td'); td.textContent = v; tr.appendChild(td); });
      if (r.is_demo) { const p = document.createElement('span'); p.className = 'pill demo'; p.textContent = 'demo'; tr.children[1].append(' ', p); }
      const td = document.createElement('td'); const s = document.createElement('select'); s.setAttribute('aria-label', 'Status');
      ['New', 'Contacted', 'Closed'].forEach((x) => { const o = document.createElement('option'); o.textContent = x; o.value = x; if (x === r.status) o.selected = true; s.appendChild(o); });
      s.addEventListener('change', () => fetch('/api/enquiries/' + r.id, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: s.value }) }));
      td.appendChild(s); tr.appendChild(td); tb.appendChild(tr);
    });
  }
  function renderFb(list) {
    $('fbCard').hidden = !list.length; const ul = $('fbList'); ul.textContent = '';
    list.forEach((f) => { const li = document.createElement('li'); li.textContent = f.ts + ' — ' + f.detail; ul.appendChild(li); });
  }

  $('refresh').addEventListener('click', refresh); $('scope').addEventListener('change', refresh);
  initLib().then((ok) => { chartLib = ok; refresh(); setInterval(refresh, 10000); });
})();
