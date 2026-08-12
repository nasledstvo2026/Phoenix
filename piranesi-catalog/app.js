/* Каталог Пиранези — галерея с лайтбоксом */
(function () {
  "use strict";

  const catalogEl = document.getElementById("catalog");
  const searchEl = document.getElementById("search");
  const chipsEl = document.getElementById("chips");
  const totalEl = document.getElementById("total-count");
  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightbox-img");
  const lightboxInfo = document.getElementById("lightbox-info");
  const viewToggle = document.getElementById("view-toggle");

  let DATA = null;
  let activeChip = "all";
  let query = "";
  let currentView = "gallery";

  // Индексы для навигации в лайтбоксе
  let visibleItems = [];
  let lightboxIdx = -1;

  /* ---------- утилиты ---------- */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function itemMatches(item) {
    if (!query) return true;
    const q = query.toLowerCase();
    const hay = [
      item.title,
      item.identifier,
      item.date || "",
      item.description || "",
      (item.titles || []).map(t => t.text || "").join(" ")
    ].join(" ").toLowerCase();
    return hay.includes(q);
  }

  function getTitle(item) {
    if (item.titles && item.titles.length) {
      const ru = item.titles.find(t => t.lang === "ru") || item.titles.find(t => t.lang === "nl");
      if (ru) return ru.text;
      return item.titles[0].text;
    }
    return item.title || "Без названия";
  }

  function fmtMeta(item) {
    const parts = [];
    if (item.date) parts.push(item.date);
    if (item.technique_text) parts.push(item.technique_text);
    else if (item.technique) parts.push(item.technique);
    if (item.dimensions) parts.push(item.dimensions);
    if (item.identifier) parts.push("№ " + item.identifier);
    return parts;
  }

  function hasImage(item) {
    return !!(item.image_thumb || item.image_full);
  }

  function imgThumb(item) {
    return item.image_thumb || item.image_full || "";
  }

  function imgFull(item) {
    return item.image_full || item.image_thumb || "";
  }

  /* ---------- лайтбокс ---------- */
  function openLightbox(idx) {
    if (idx < 0 || idx >= visibleItems.length) return;
    lightboxIdx = idx;
    const item = visibleItems[idx];
    lightboxImg.src = imgFull(item);
    lightboxImg.alt = getTitle(item);
    const meta = fmtMeta(item);
    lightboxInfo.innerHTML = "<strong>" + esc(getTitle(item)) + "</strong>" +
      (meta.length ? "<br>" + meta.map(esc).join(" · ") : "") +
      (item.description ? "<p class=\"desc\">" + esc(item.description.substring(0, 300)) + (item.description.length > 300 ? "…" : "") + "</p>" : "") +
      (item.url ? '<p><a href="' + esc(item.url) + '" target="_blank" rel="noopener">Открыть в Рейксмузеуме →</a></p>' : "");
    lightbox.classList.add("open");
    document.body.style.overflow = "hidden";
    updateLightboxButtons();
  }

  function closeLightbox() {
    lightbox.classList.remove("open");
    document.body.style.overflow = "";
    lightboxImg.src = "";
  }

  function lightboxNext() { if (visibleItems.length) openLightbox((lightboxIdx + 1) % visibleItems.length); }
  function lightboxPrev() { if (visibleItems.length) openLightbox((lightboxIdx - 1 + visibleItems.length) % visibleItems.length); }

  function updateLightboxButtons() {
    document.getElementById("lightbox-prev").style.display = visibleItems.length > 1 ? "" : "none";
    document.getElementById("lightbox-next").style.display = visibleItems.length > 1 ? "" : "none";
  }

  function initLightboxNavigation() {
    // Поиск всех кликабельных миниатюр для навигации
    visibleItems = [];
    document.querySelectorAll(".item-card[data-idx]").forEach(el => {
      const idx = parseInt(el.getAttribute("data-idx"));
      if (idx >= 0 && idx < flatItems.length) {
        visibleItems.push(flatItems[idx]);
      }
    });
    if (visibleItems.length === 0) {
      // fallback: собираем заново
      collectVisible();
    }
  }

  let flatItems = [];

  function collectVisible() {
    flatItems = [];
    visibleItems = [];

    const seriesList = activeChip === "all"
      ? DATA.series
      : DATA.series.filter(s => s.key === activeChip);

    for (const s of seriesList) {
      for (const item of s.items) {
        if (itemMatches(item)) {
          flatItems.push(item);
          if (hasImage(item)) visibleItems.push(item);
        }
      }
    }
  }

  /* ---------- рендеринг ---------- */
  function renderGallery(seriesList) {
    let html = "";
    let shown = 0;
    let cardIdx = 0;
    flatItems = [];
    const visibleImageItems = [];

    for (const s of seriesList) {
      const items = s.items.filter(itemMatches);
      if (!items.length) continue;

      if (activeChip === "all") {
        html += '<div class="series-head"><h2>' + esc(s.name) +
          "</h2><span class=\"count\">" + items.length + "</span></div>";
      }

      html += '<div class="gallery-grid">';
      for (const it of items) {
        flatItems.push(it);
        const hasImg = hasImage(it);
        if (hasImg) visibleImageItems.push(it);

        html += '<div class="item-card' + (hasImg ? ' has-image' : '') + '" data-idx="' + cardIdx + '">';
        if (hasImg) {
          const vi = visibleImageItems.length - 1;
          html += '<div class="item-thumb" data-lightbox="' + vi + '">' +
            '<img src="' + esc(imgThumb(it)) + '" alt="' + esc(getTitle(it)) + '" loading="lazy"' +
            (it.image_width && it.image_height ? ' width="' + it.image_width + '" height="' + it.image_height + '"' : '') +
            '>' +
            (it.image_full ? '<div class="item-zoom">🔍</div>' : '') +
            '</div>';
        } else {
          html += '<div class="item-thumb no-image"><span class="no-img-icon">🖼️</span></div>';
        }
        html += '<div class="item-info">';
        html += '<div class="item-title">' + esc(getTitle(it)) + '</div>';
        const meta = fmtMeta(it);
        if (meta.length) {
          html += '<div class="item-meta">' + meta.map(esc).join(' · ') + '</div>';
        }
        if (it.description) {
          html += '<div class="item-desc">' + esc(it.description.substring(0, 120)) + (it.description.length > 120 ? '…' : '') + '</div>';
        }
        html += '</div></div>';
        cardIdx++;
      }
      html += '</div>';
      shown += items.length;
    }

    if (shown === 0) {
      html = '<div class="empty">Ничего не найдено. Попробуйте другой запрос.</div>';
    }

    // Сохраняем видимые элементы с изображениями для лайтбокса
    visibleItems = visibleImageItems;
    catalogEl.innerHTML = html;

    // Вешаем клики на миниатюры
    catalogEl.querySelectorAll(".item-thumb[data-lightbox]").forEach(el => {
      el.addEventListener("click", () => {
        const vi = parseInt(el.getAttribute("data-lightbox"));
        openLightbox(vi);
      });
    });
  }

  function renderList(seriesList) {
    let html = "";
    let shown = 0;
    flatItems = [];
    cardIdx = 0;
    visibleItems = [];

    for (const s of seriesList) {
      const items = s.items.filter(itemMatches);
      if (!items.length) continue;
      shown += items.length;

      html += '<section class="series"><div class="series-head"><h2>' + esc(s.name) +
        "</h2><span class=\"count\">" + items.length + "</span></div><ul class=\"items\">";

      for (const it of items) {
        flatItems.push(it);
        if (hasImage(it)) visibleItems.push(it);

        html += '<li class="list-item' + (hasImage(it) ? ' has-image' : '') + '" data-idx="' + cardIdx + '">';
        if (it.image_thumb) {
          const vi = visibleItems.length - 1;
          html += '<div class="list-thumb" data-lightbox="' + vi + '">' +
            '<img src="' + esc(it.image_thumb) + '" alt="" loading="lazy" width="60">' +
            '</div>';
        }
        html += '<div class="list-text">';
        html += '<div class="item-title"><a href="' + (it.url || '#') + '" target="_blank" rel="noopener">' +
          esc(getTitle(it)) + '</a></div>';
        const meta = fmtMeta(it);
        if (meta.length) {
          html += '<div class="item-meta">' + meta.map(esc).join(' · ') + '</div>';
        }
        html += '</div></li>';
        cardIdx++;
      }

      html += "</ul></section>";
    }

    if (shown === 0) {
      html = '<div class="empty">Ничего не найдено. Попробуйте другой запрос.</div>';
    }

    catalogEl.innerHTML = html;

    // Клики на миниатюры в списке
    catalogEl.querySelectorAll(".list-thumb[data-lightbox]").forEach(el => {
      el.addEventListener("click", () => {
        const vi = parseInt(el.getAttribute("data-lightbox"));
        openLightbox(vi);
      });
    });
  }

  function render() {
    if (!DATA) return;
    totalEl.textContent = DATA.total;

    // Чипы серий
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

    const seriesList = activeChip === "all"
      ? DATA.series
      : DATA.series.filter(s => s.key === activeChip);

    if (currentView === "gallery") {
      renderGallery(seriesList);
    } else {
      renderList(seriesList);
    }
  }

  /* ---------- события ---------- */
  searchEl.addEventListener("input", () => {
    query = searchEl.value.trim();
    render();
  });

  // Переключатель вида
  viewToggle.addEventListener("click", e => {
    const btn = e.target.closest(".view-btn");
    if (!btn) return;
    currentView = btn.getAttribute("data-view");
    viewToggle.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    render();
  });

  // Лайтбокс: закрытие
  document.getElementById("lightbox-close").addEventListener("click", closeLightbox);
  lightbox.addEventListener("click", e => {
    if (e.target === lightbox) closeLightbox();
  });

  // Лайтбокс: навигация
  document.getElementById("lightbox-prev").addEventListener("click", e => {
    e.stopPropagation();
    lightboxPrev();
  });
  document.getElementById("lightbox-next").addEventListener("click", e => {
    e.stopPropagation();
    lightboxNext();
  });

  // Клавиатура
  document.addEventListener("keydown", e => {
    if (!lightbox.classList.contains("open")) return;
    if (e.key === "Escape") closeLightbox();
    if (e.key === "ArrowLeft") lightboxPrev();
    if (e.key === "ArrowRight") lightboxNext();
  });

  /* ---------- загрузка ---------- */
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
