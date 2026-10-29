const FIELDS = ["division", "store_id", "code", "name", "website_id", "store_url",
    "website_name", "website_code", "website_url", "has_active_store",
    "iata_code", "country", "region"];
let editingId = null;

// Multi-select filter state.
const selected = { division: new Set(), region: new Set(), country: new Set(), language: new Set() };
let countryOptions = [];
let statusVal = "all";  // all | 1 (active) | 0 (no activo)

const $ = s => document.querySelector(s);
function esc(v) { return v == null ? "" : String(v).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

// Outline (monochrome) theme icons; stroke follows the header text color.
const ICON_MOON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
const ICON_SUN = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>`;

// Theme toggle with persistence.
function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    const btn = $("#theme-toggle");
    if (btn) {
        btn.innerHTML = theme === "dark" ? ICON_SUN : ICON_MOON;
        btn.title = theme === "dark" ? "Tema claro" : "Tema oscuro";
    }
    localStorage.setItem("theme", theme);
}
function toggleTheme() {
    const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";

    // No View Transitions support (or reduced motion): switch instantly.
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!document.startViewTransition || reduce) {
        applyTheme(next);
        return;
    }

    // Feed the reveal circle (center + radius) to the CSS keyframes.
    const rect = $("#theme-toggle").getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    const root = document.documentElement;
    root.style.setProperty("--vt-x", x + "px");
    root.style.setProperty("--vt-y", y + "px");
    root.style.setProperty("--vt-r", r + "px");

    document.startViewTransition(() => applyTheme(next));
}

// Language code -> flag emoji (built from regional-indicator letters).
const LANG_FLAG = {
    en: "gb", es: "es", fr: "fr", pt: "pt", el: "gr", zh: "cn", sv: "se", ru: "ru",
    it: "it", de: "de", fi: "fi", hk: "hk", uk: "gb", ch: "ch", ca: "es", mo: "mo",
    br: "br", mx: "mx", usa: "us", ci: "ci"
};
function flagEmoji(cc) {
    if (!cc || cc.length !== 2) return "";
    return String.fromCodePoint(...[...cc.toUpperCase()].map(c => 0x1F1E6 + c.charCodeAt(0) - 65));
}
function langCell(lang) {
    if (!lang) return "";
    const flag = flagEmoji(LANG_FLAG[lang] || lang);
    return `<span class="lang-cell">${flag ? `<span class="flag">${flag}</span>` : ""}${esc(lang.toUpperCase())}</span>`;
}

let toastTimer;
function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 1200);
}
async function copyText(text) {
    if (text == null || text === "") return;
    try {
        await navigator.clipboard.writeText(String(text));
    } catch {
        const ta = document.createElement("textarea");
        ta.value = String(text); document.body.appendChild(ta); ta.select();
        document.execCommand("copy"); ta.remove();
    }
    toast("Copiado");
}

function statusBadge(v) {
    if (v == null || v === "") return "";
    const s = String(v).toLowerCase();
    const active = s.includes("active") && !s.includes("inactive");
    return `<span class="badge ${active ? 'active' : 'inactive'}">${esc(v)}</span>`;
}
function link(url) {
    if (!url) return "";
    return `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(url)}</a>`;
}

function renderPills(field, containerId, values) {
    const box = document.getElementById(containerId);
    box.innerHTML = "";
    for (const v of values) {
        const el = document.createElement("span");
        el.className = "pill" + (selected[field].has(String(v)) ? " active" : "");
        el.textContent = v;
        el.addEventListener("click", () => {
            const key = String(v);
            if (selected[field].has(key)) selected[field].delete(key);
            else selected[field].add(key);
            el.classList.toggle("active");
            loadRows();
        });
        box.appendChild(el);
    }
}

function renderLanguagePills(values) {
    const box = document.getElementById("pills-language");
    box.innerHTML = "";
    for (const v of values) {
        const key = String(v);
        const el = document.createElement("span");
        el.className = "pill" + (selected.language.has(key) ? " active" : "");
        const flag = flagEmoji(LANG_FLAG[key] || key);
        el.innerHTML = `${flag ? flag + " " : ""}${esc(key.toUpperCase())}`;
        el.addEventListener("click", () => {
            if (selected.language.has(key)) selected.language.delete(key);
            else selected.language.add(key);
            el.classList.toggle("active");
            loadRows();
        });
        box.appendChild(el);
    }
}

function renderCountryOptions(filter = "") {
    const box = $("#ms-country-options");
    const f = filter.trim().toLowerCase();
    box.innerHTML = "";
    for (const c of countryOptions) {
        if (f && !String(c).toLowerCase().includes(f)) continue;
        const row = document.createElement("label");
        row.className = "ms-opt";
        const checked = selected.country.has(String(c)) ? "checked" : "";
        row.innerHTML = `<input type="checkbox" value="${esc(c)}" ${checked}> ${esc(c)}`;
        row.querySelector("input").addEventListener("change", e => {
            const key = String(c);
            if (e.target.checked) selected.country.add(key);
            else selected.country.delete(key);
            updateCountryLabel();
            loadRows();
        });
        box.appendChild(row);
    }
}
function updateCountryLabel() {
    const n = selected.country.size;
    $("#ms-country-toggle").innerHTML = n ? `País <span class="ms-count">${n}</span>` : "País: todos";
}

async function loadFilters() {
    const data = await (await fetch("/api/filters")).json();
    renderPills("division", "pills-division", data.division);
    renderPills("region", "pills-region", data.region);
    renderLanguagePills(data.language);
    countryOptions = data.country;
    renderCountryOptions();
}

async function loadRows() {
    const params = new URLSearchParams();
    const s = $("#search").value.trim();
    if (s) params.set("search", s);
    for (const field of ["division", "region", "country", "language"])
        for (const v of selected[field]) params.append(field, v);
    if (statusVal !== "all") params.set("active", statusVal);

    const data = await (await fetch("/api/stores?" + params)).json();
    $("#count").textContent = data.length + " registros";
    $("#rows").innerHTML = data.map(r => `
    <tr>
      <td>${esc(r.division)}</td>
      <td class="copyable" data-copy="${esc(r.store_id)}">${esc(r.store_id)}</td>
      <td>${esc(r.code)}</td>
      <td class="copyable" data-copy="${esc(r.name)}">${esc(r.name)}</td>
      <td class="copyable" data-copy="${esc(r.website_id)}">${esc(r.website_id)}</td>
      <td>${link(r.store_url)}</td><td>${esc(r.website_name)}</td>
      <td>${esc(r.website_code)}</td><td>${link(r.website_url)}</td>
      <td>${statusBadge(r.has_active_store)}</td>
      <td class="copyable" data-copy="${esc(r.iata_code)}">${esc(r.iata_code)}</td>
      <td>${langCell(r.language)}</td>
      <td>${esc(r.country)}</td><td>${esc(r.region)}</td>
      <td class="actions">
        <button onclick='openEdit(${JSON.stringify(r)})'>Editar</button>
        <button class="danger" onclick="del(${r.id})">Borrar</button>
      </td>
    </tr>`).join("");
}

function openModal(title) { $("#modal-title").textContent = title; $("#modal-bg").classList.add("open"); }
function closeModal() { $("#modal-bg").classList.remove("open"); }
function buildForm(rec) {
    $("#form").innerHTML = FIELDS.map(f => `
    <div class="field">
      <label>${f}</label>
      <input id="in-${f}" value="${esc(rec ? rec[f] : "")}">
    </div>`).join("");
}
function openEdit(rec) { editingId = rec.id; buildForm(rec); openModal("Editar registro #" + rec.id); }
function openNew() { editingId = null; buildForm(null); openModal("Nuevo registro"); }

async function save() {
    const body = {};
    for (const f of FIELDS) body[f] = $("#in-" + f).value;
    if (editingId == null) {
        await fetch("/api/stores", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    } else {
        await fetch("/api/stores/" + editingId, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    }
    closeModal();
    loadRows();
}
async function del(id) {
    if (!confirm("¿Borrar el registro #" + id + "?")) return;
    await fetch("/api/stores/" + id, { method: "DELETE" });
    loadRows();
}

// Country searchable multiselect wiring.
$("#ms-country-toggle").addEventListener("click", e => {
    e.stopPropagation();
    $("#ms-country").classList.toggle("open");
});
$("#ms-country-search").addEventListener("input", e => renderCountryOptions(e.target.value));
document.addEventListener("click", e => {
    if (!$("#ms-country").contains(e.target)) $("#ms-country").classList.remove("open");
});

$("#theme-toggle").addEventListener("click", toggleTheme);
$("#search").addEventListener("input", debounce(loadRows, 250));
$("#seg-status").querySelectorAll("button").forEach(btn =>
    btn.addEventListener("click", () => {
        statusVal = btn.dataset.val;
        $("#seg-status").querySelectorAll("button").forEach(b => b.classList.toggle("active", b === btn));
        loadRows();
    }));
$("#clear").addEventListener("click", () => {
    $("#search").value = "";
    statusVal = "all";
    $("#seg-status").querySelectorAll("button").forEach(b => b.classList.toggle("active", b.dataset.val === "all"));
    for (const f of ["division", "region", "country", "language"]) selected[f].clear();
    document.querySelectorAll(".pill.active").forEach(p => p.classList.remove("active"));
    updateCountryLabel();
    renderCountryOptions();
    loadRows();
});
$("#new").addEventListener("click", openNew);
$("#cancel").addEventListener("click", closeModal);
$("#save").addEventListener("click", save);
$("#modal-bg").addEventListener("click", e => { if (e.target.id === "modal-bg") closeModal(); });

// Click a copyable cell to copy its value to the clipboard.
$("#rows").addEventListener("click", e => {
    const cell = e.target.closest("td.copyable");
    if (cell) copyText(cell.dataset.copy);
});

applyTheme(localStorage.getItem("theme") || "dark");
loadFilters();
loadRows();