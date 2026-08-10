/* Каталог Пиранези — клиентская логика */
(function () {
  "use strict";

  const catalogEl = document.getElementById("catalog");
  const searchEl = document.getElementById("search");
  const chipsEl = document.getElementById("chips");
  const totalEl = document.getElementById("total-count");

  let DATA = null;        // { series: [{name, items}], ungrouped: [...] }
  let activeChip = "all";
  let query = "";

  function fmt(item) {
    const parts = [];
    if (item.date) parts.push(item.date);
    if (item.technique) parts.push(item.technique);
    if (item.identifier) parts.push("№ " + item.identifier);
    return parts;
  }

  function itemMatches(item) {
    if (!query) return true;
    const q = query.toLowerCase();
    const hay = [item.title, item.identifier, (item.date || "")].join(" ").toLowerCase();
    return hay.includes(q);
  }

  function render() {
    if (!DATA) return;
    totalEl.textContent = DATA.total;

    // чипы серий
    const chips = [{ key: "all", label: "Все", n: DATA.total }]
      .concat(DATA.series.map(s => ({ key: s.key, label: s.name, n: s.items.length })));
    chipsEl.innerHTML = "";
    for (const c of chips) {
      const el = document.createElement("button");
      el.className = "chip" + (c.key === activeChip ? " active" : "");
      el.innerHTML = c.label + '<span class="n">' + c.n + "</span>";
      el.addEventListener("click", () => {
        activeChip = c.key;
        render();
      });
      chipsEl.appendChild(el);
    }

    // контент
    let html = "";
    let shown = 0;
    const seriesList = activeChip === "all"
      ? DATA.series
      : DATA.series.filter(s => s.key === activeChip);

    for (const s of seriesList) {
      const items = s.items.filter(itemMatches);
      if (!items.length) continue;
      shown += items.length;
      html += '<section class="series"><div class="series-head"><h2>' + s.name +
        "</h2><span class=\"count\">" + items.length + "</span></div><ul class=\"items\">";
      for (const it of items) {
        const meta = fmt(it);
        html += "<li><div class=\"item-title\"><a href=\"" + it.url + '" target="_blank" rel="noopener">' +
          esc(it.title) + "</a></div>";
        if (meta.length) {
          html += '<div class="item-meta">' + meta.map(esc).join('<span class="sep">·</span>') + "</div>";
        }
        html += "</li>";
      }
      html += "</ul></section>";
    }

    if (shown === 0) {
      html = '<div class="empty">Ничего не найдено. Попробуйте другой запрос.</div>';
    }
    catalogEl.innerHTML = html;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  searchEl.addEventListener("input", () => {
    query = searchEl.value.trim();
    render();
  });

  const inline = window.__DATA__;
  if (inline) {
    DATA = inline;
    render();
  } else {
    fetch("data/catalog.json")
      .then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(d => { DATA = d; render(); })
      .catch(e => {
        catalogEl.innerHTML = '<div class="empty">Не удалось загрузить каталог: ' + esc(e.message) + "</div>";
      });
  }
})();
