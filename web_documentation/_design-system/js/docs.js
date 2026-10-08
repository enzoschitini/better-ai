/* docs.js — o que o ds.js deliberadamente não faz.
 *
 * O ds.js cuida de ícones, abas de código, copiar, tema, gaveta, --top, TOC e
 * de ABRIR/FECHAR o diálogo de busca (Ctrl K, /, Esc). Ele não faz menu,
 * roteamento, i18n, nem índice/ranking/render da busca.
 *
 * O menu e o i18n são resolvidos no build. Sobram duas coisas para o cliente:
 *   1. navegação de idioma, respondendo ao evento "ds:lang" do ds.js
 *   2. índice, ranking e render dos resultados de busca
 *
 * Config vem do window.DOCS, injetado por página pelo build.
 */
(function () {
  'use strict';

  var C = window.DOCS || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };

  /* ---------- 1. idioma: navega, não troca conteúdo ---------- */
  document.addEventListener('ds:lang', function (e) {
    var to = e.detail;
    if (!to || to === C.lang) return;
    try { localStorage.setItem('betterai-docs-lang', to); } catch (_) {}
    // C.alt é gerado no build (caminho relativo à raiz), e C.root é o
    // prefixo desta página até a raiz — então trocar idioma nunca chuta URL
    var url = (C.root || '') + ((C.alt && C.alt[to]) || (to + '/'));
    location.href = url + location.hash;
  });

  /* ---------- 2. busca ---------- */
  var dlg = $('#search');
  if (!dlg) return;

  var input = $('input', dlg);
  var list = $('.results', dlg);
  var IDX = null, LOADING = null, ROWS = [], sel = -1;

  function load() {
    if (IDX) return Promise.resolve(IDX);
    if (!LOADING) {
      LOADING = fetch(C.index)
        .then(function (r) { return r.json(); })
        .then(function (j) { IDX = j; return j; })
        .catch(function () { LOADING = null; return null; });
    }
    return LOADING;
  }

  // prefetch: quando o diálogo pinta, o fetch normalmente já terminou
  var trigger = $('[data-open-search]');
  if (trigger) {
    ['pointerenter', 'focus'].forEach(function (ev) {
      trigger.addEventListener(ev, load, { once: true });
    });
  }

  // fold() precisa bater com o do build: NFD, sem diacríticos, minúsculas.
  // Preserva o comprimento, então os offsets de <mark> valem nos dois textos.
  function fold(s) {
    return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function mark(text, term) {
    var i = fold(text).indexOf(term);
    if (i < 0) return esc(text);
    return esc(text.slice(0, i)) + '<mark>' + esc(text.slice(i, i + term.length)) +
           '</mark>' + esc(text.slice(i + term.length));
  }

  /* Faixas do protótipo, estendidas para o corpo.
     0 título startsWith · 1 título includes · 2 seção startsWith
     3 seção includes · 4 migalha · 5 corpo
     +0.5 de penalidade para seção, +ordem/1000 como desempate estável */
  function rank(term) {
    // os caminhos do índice são relativos à raiz do site
    var R = C.root || '', out = [], perPage = {}, i, j;
    for (i = 0; i < IDX.p.length; i++) {
      var p = IDX.p[i], t = fold(p[2]), c = fold(p[3]), sc = -1;
      if (t.indexOf(term) === 0) sc = 0;
      else if (t.indexOf(term) >= 0) sc = 1;
      else if (c.indexOf(term) >= 0) sc = 4;
      if (sc >= 0) out.push({ u: R + p[1], t: p[2], c: p[3], s: sc + p[4] / 1000 });
    }
    for (j = 0; j < IDX.s.length; j++) {
      var s = IDX.s[j], pg = IDX.p[s[0]], h = fold(s[2]), sc2 = -1, snip = '';
      if (h.indexOf(term) === 0) sc2 = 2;
      else if (h.indexOf(term) >= 0) sc2 = 3;
      else {
        var k = s[3].indexOf(term);
        if (k >= 0) { sc2 = 5; snip = s[4].slice(Math.max(0, k - 40), k + 80); }
      }
      if (sc2 < 0) continue;
      perPage[s[0]] = (perPage[s[0]] || 0) + 1;
      if (perPage[s[0]] > 3) continue;   // uma página longa não inunda a lista
      out.push({
        u: R + pg[1] + '#' + s[1], t: s[2], c: pg[2] + ' / ' + pg[3],
        snip: snip, s: sc2 + 0.5 + pg[4] / 1000
      });
    }
    return out.sort(function (a, b) { return a.s - b.s; }).slice(0, 12);
  }

  function paint(rows, term) {
    ROWS = rows; sel = rows.length ? 0 : -1;
    if (!rows.length) {
      var msg = (C.i && C.i.noResults ? C.i.noResults : 'Nada encontrado para “%s”.')
        .replace('%s', esc(term));
      list.innerHTML = '<li class="no-results">' + msg + '</li>';
      return;
    }
    list.innerHTML = rows.map(function (r, i) {
      return '<li class="result" role="option" aria-selected="' + (i === 0) + '">' +
        '<a href="' + r.u + '">' +
        '<span class="r-title">' + mark(r.t, term) + '</span>' +
        '<span class="r-path">' + esc(r.c) + '</span>' +
        (r.snip ? '<span class="r-snip">' + mark(r.snip, term) + '</span>' : '') +
        '</a></li>';
    }).join('');
  }

  function suggestions() {
    if (!IDX || !IDX.popular || !IDX.popular.length) { list.innerHTML = ''; return; }
    var R = C.root || '';
    var rows = IDX.popular.map(function (i) {
      var p = IDX.p[i];
      return { u: R + p[1], t: p[2], c: p[3], s: 0 };
    });
    ROWS = rows; sel = 0;
    list.innerHTML = rows.map(function (r, i) {
        return '<li class="result" role="option" aria-selected="' + (i === 0) + '">' +
          '<a href="' + r.u + '"><span class="r-title">' + esc(r.t) + '</span>' +
          '<span class="r-path">' + esc(r.c) + '</span></a></li>';
      }).join('');
  }

  function run() {
    var q = (input.value || '').trim();
    load().then(function (ok) {
      if (!ok) return;
      if (!q) { suggestions(); return; }
      paint(rank(fold(q)), fold(q));
    });
  }

  input.addEventListener('input', run);

  // o ds.js abre o diálogo; aqui só reagimos à abertura para popular a lista
  new MutationObserver(function () {
    if (dlg.open) { input.value = ''; load().then(function (ok) { if (ok) suggestions(); }); }
  }).observe(dlg, { attributes: true, attributeFilter: ['open'] });

  function move(d) {
    if (!ROWS.length) return;
    sel = (sel + d + ROWS.length) % ROWS.length;
    var items = list.querySelectorAll('.result');
    for (var i = 0; i < items.length; i++) {
      items[i].setAttribute('aria-selected', i === sel);
    }
    if (items[sel]) items[sel].scrollIntoView({ block: 'nearest' });
  }

  dlg.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      if (ROWS[sel]) location.href = ROWS[sel].u;   // URL real, não location.hash
    }
  });

  /* ---------- 3. copiar página ---------- */
  var cp = $('[data-copy-page]');
  if (cp) {
    cp.addEventListener('click', function () {
      var prose = $('.prose');
      if (!prose || !navigator.clipboard) return;
      navigator.clipboard.writeText(prose.innerText).then(function () {
        var span = $('span', cp);
        if (!span) return;
        var old = span.textContent;
        span.textContent = '✓';
        setTimeout(function () { span.textContent = old; }, 1200);
      });
    });
  }
})();
