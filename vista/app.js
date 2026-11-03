/* Cerebro Orlando · v2 · toda cifra sale del lago incrustado en <script id="datos">; nada se escribe a mano. */
(() => {
"use strict";
const D = JSON.parse(document.getElementById("datos").textContent);
const L = D.lago, M = D.mapa;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const ic = (id, cls = "i") => `<svg class="${cls}" aria-hidden="true"><use href="#i-${id}"/></svg>`;
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

/* ---------- formato en español ---------- */
const nf = (v, d = 0) => new Intl.NumberFormat("es-CO", {minimumFractionDigits: d, maximumFractionDigits: d}).format(v);
const NB = " ";
const pct = (v, d = 1) => (v > 0 ? "+" : v < 0 ? "−" : "") + nf(Math.abs(v), d) + NB + "%";
const pp = (v, d = 1) => (v > 0 ? "+" : v < 0 ? "−" : "") + nf(Math.abs(v), d) + NB + "puntos";
const usd = v => "US$" + NB + nf(v);
const millones = miles => miles >= 1000 ? nf(miles / 1000, 2) + NB + "millones" : nf(miles) + NB + "mil";
const MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESL = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const DIA = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
const fDia = s => { const [y, m, d] = s.slice(0, 10).split("-").map(Number); return `${d} ${MES[m - 1]} ${y}`; };
const fMes = (s, largo) => { const [y, m] = s.split("-").map(Number); return largo ? `${MESL[m - 1]} de ${y}` : `${MES[m - 1]} ${y}`; };
const fTrim = s => { const y = s.slice(0, 4), q = +s.slice(-1); return `${MES[(q - 1) * 3]}–${MES[(q - 1) * 3 + 2]} ${y}`; };
const fVig = s => !s ? "" : /^\d{4}-Q\d$/.test(s) ? fTrim(s) : /^\d{4}-\d{2}$/.test(s) ? fMes(s) : /^\d{4}-\d{2}-\d{2}/.test(s) ? fDia(s) : s.replace("-", "–");
const aC = f => Math.round((f - 32) * 5 / 9);
const cap = s => s ? s[0].toUpperCase() + s.slice(1) : s;
// Espacio duro entre la cifra y su unidad: «25 %» nunca se parte en dos líneas
const nb = s => String(s).replace(/(\d) (?=%|°|puntos\b|millones\b|mil\b|veces\b|días\b|casos\b|permisos\b)/g, "$1\u00a0");
// Nombres que la capa trae en mayúsculas («ORLANDO INTERNATIONAL AIRPORT») se muestran como título
const bonito = s => s && s === s.toUpperCase() && /[A-Z]{3}/.test(s) ? s.toLowerCase().replace(/(^|[\s/-])(\p{L})/gu, (m, a, b) => a + b.toUpperCase()) : s;

/* ---------- acceso al lago ---------- */
const C = (tema, k) => L[tema].cifras[k];
const S = (tema, k) => L[tema].series[k] ? L[tema].series[k].puntos : [];
const ult = arr => arr[arr.length - 1];
function tendencia(v, umbral = 1, modo = "normal", fmt = pct) {
  // modo: normal (subir es bueno), inverso (subir es malo) o neutro (sin juicio)
  const t = Math.abs(v) < umbral ? "igual" : v > 0 ? "sube" : "baja";
  const txt = {igual: "Estable", sube: "Sube", baja: "Baja"}[t];
  const cls = t === "igual" || modo === "neutro" ? "igual" : modo === "inverso" ? (t === "sube" ? "baja" : "sube") : t;
  return `<span class="tend ${cls}">${ic(t === "igual" ? "igual" : t)}${txt} ${fmt(v)}</span>`;
}

/* ---------- trazabilidad ---------- */
const FUENTES = Object.fromEntries(D.fuentes_lago.map(f => [f.id, f]));
const TEMA_DE = {};
for (const [tema, o] of Object.entries(L)) for (const f of o.fuentes) if (!TEMA_DE[f.id]) TEMA_DE[f.id] = tema;
const CORTO = {indeed_hiring_lab: "Indeed Hiring Lab · CC BY 4.0", fred_ihv_orlando: "FHFA vía FRED", fred_ihv_pares: "FHFA vía FRED",
  fred_laus: "BLS vía FRED", fred_ces: "BLS vía FRED", fred_realtor: "Realtor.com vía FRED", fred_bps: "Census vía FRED",
  fred_poblacion: "Census vía FRED", fred_saipe: "Census vía FRED", wikimedia_pageviews: "Wikimedia", nws_api: "Servicio Meteorológico (NWS)",
  noaa_gsoy: "NOAA NCEI", orlando_permisos: "Datos abiertos de Orlando", orlando_barrios: "Datos abiertos de Orlando",
  orlando_distritos: "Datos abiertos de Orlando", orlando_limites: "Datos abiertos de Orlando", orlando_lagos: "Datos abiertos de Orlando",
  orlando_codigo: "Datos abiertos de Orlando", orlando_negocios: "Datos abiertos de Orlando", orlando_alquiler_corto: "Datos abiertos de Orlando",
  opd_casos: "Policía de Orlando (mapa público)", censo_acs: "Census ACS (vía Census Reporter)", censo_tiger: "Census TIGER",
  fema_nri: "FEMA · Índice Nacional de Riesgo", orlando_sig: "SIG de la Ciudad de Orlando", orlando_planeacion: "Datos abiertos de Orlando",
  orlando_anexiones: "Datos abiertos de Orlando", fred_salarios: "BLS vía FRED", fred_bfs: "Census vía FRED", fred_bea: "BEA vía FRED",
  fred_ipc: "BLS vía FRED", zillow_research: "Zillow Research"};
function chip(fuente, campo, vigencia, etiqueta) {
  const v = vigencia ? ` · ${fVig(String(vigencia))}` : "";
  return `<button type="button" class="fuente" data-fuente="${fuente}" data-campo="${campo || ""}" aria-label="Ver de dónde sale este dato">${ic("fuente")}<span>${etiqueta ? esc(etiqueta) + " · " : ""}${esc(CORTO[fuente] || fuente)}${esc(v)}</span></button>`;
}
function filaDic(ficha, campo) {
  if (!campo) return null;
  const base = campo.replace(/_(20\d\d)$/, "_<AAAA>").replace(/_(orlando|tampa|miami|jacksonville|florida|eeuu|orange|hillsborough|duval|miami_dade)$/, "");
  return D.diccionario.find(r => r.fuente === ficha && r.campo === campo)
      || D.diccionario.find(r => r.fuente === ficha && (r.campo || "").split(" / ").some(x => x === campo || x === base || x.replace(/<[^>]+>/g, "").replace(/_$/, "") === base.replace(/<[^>]+>/g, "").replace(/_$/, "")))
      || D.diccionario.find(r => r.fuente === ficha && (r.campo || "").includes(base.split("_")[0]));
}
function abrirTraza(fuente, campo) {
  const f = FUENTES[fuente]; if (!f) return;
  const tema = TEMA_DE[fuente], lago = L[tema] || {};
  const enLago = (lago.fuentes || []).find(x => x.id === fuente) || {};
  const ficha = D.catalogo.find(c => c.id === f.ficha_excel) || {};
  let dato = "";
  if (campo) {
    const r = filaDic(f.ficha_excel, campo);
    const cl = campo.replace("<AAAA>", "");
    const c = (lago.cifras || {})[campo] || (lago.series || {})[campo] || Object.entries(lago.series || {}).find(([k]) => k.startsWith(cl))?.[1];
    if (r || c) dato = `<div class="campo"><p class="eyebrow">Este dato</p><dl>
      <div><dt>Campo en el lago</dt><dd class="mono">${esc(r ? r.archivo : `lago/raw/${tema}/${tema}.json`)} → ${esc(campo)}</dd></div>
      ${r ? `<div><dt>Qué significa</dt><dd>${esc(r.significado)}</dd></div>` : ""}
      ${c && c.unidad ? `<div><dt>Unidad</dt><dd>${esc(c.unidad)}</dd></div>` : ""}
      ${c && c.vigencia ? `<div><dt>A qué fecha corresponde</dt><dd>${esc(fVig(c.vigencia))}</dd></div>` : ""}
      ${r && r.transformacion ? `<div><dt>Qué le hicimos</dt><dd>${esc(r.transformacion)}</dd></div>` : ""}
      ${r ? `<div><dt>Clasificación</dt><dd>${esc(r.clasificacion)}</dd></div>` : ""}</dl></div>`;
  }
  const lic = f.licencia === "no declara" ? "No declara licencia. La ficha del portal tiene el campo vacío; la usamos con esa advertencia anotada." : esc(f.licencia);
  $("#trazaIn").innerHTML = `<button class="btn cerrar" type="button" id="cerrarTraza">${ic("cerrar")}Cerrar</button>
    <div><p class="eyebrow">${esc(f.ficha_excel)} · fuente en uso</p><h2 id="trazaT" style="font-size:1.4rem;margin-top:6px">${esc(f.nombre)}</h2></div>
    ${dato}<dl>
      <div><dt>Quién la publica</dt><dd>${esc(f.entidad)}</dd></div>
      <div><dt>Licencia, tal como aparece</dt><dd>${lic}</dd></div>
      <div><dt>Para qué la usamos</dt><dd>${esc(f.uso)}</dd></div>
      <div><dt>¿Trae datos de personas?</dt><dd>${esc(f.personas)}${f.proteccion ? ` · protección: ${esc(f.proteccion)}` : ""}</dd></div>
      <div><dt>Comprobada el</dt><dd>${esc(fDia(lago.probado || D.generado))} (día en que la fuente respondió y se escribió el lago)</dd></div>
      ${enLago.url ? `<div><dt>Enlace exacto que consultó el script</dt><dd class="mono"><a href="${esc(enLago.url)}" target="_blank" rel="noopener">${esc(enLago.url)}</a></dd></div>` : ""}
      ${ficha.frecuencia ? `<div><dt>Cada cuánto se actualiza</dt><dd>${esc(ficha.frecuencia)}</dd></div>` : ""}
      ${f.nota ? `<div><dt>Nota del equipo</dt><dd>${esc(f.nota)}</dd></div>` : ""}</dl>`;
  const dlg = $("#traza"); dlg.showModal ? dlg.showModal() : dlg.setAttribute("open", ""); $("#cerrarTraza").focus();
}
document.addEventListener("click", e => {
  const b = e.target.closest(".fuente[data-fuente]");
  if (b) { e.preventDefault(); e.stopPropagation(); abrirTraza(b.dataset.fuente, b.dataset.campo); }
  if (e.target.closest("#cerrarTraza")) $("#traza").close();
});
$("#traza").addEventListener("click", e => { if (e.target.id === "traza") $("#traza").close(); });

/* ---------- glosario y globo ---------- */
const GLOSARIO = {
  indice100: "Un índice compara contra un momento de referencia. Aquí 100 es el nivel de avisos del 1 de febrero de 2020, antes de la pandemia: 110 sería 10 % más avisos que entonces. Está ajustado por estacionalidad.",
  indice1995: "100 es el precio promedio de la vivienda de cada área en enero–marzo de 1995. Para comparar ciudades lo re-escalamos a 2015 = 100: así se ve cuánto subió cada una desde el mismo punto.",
  vistas: "Visitas hechas por personas al artículo de cada ciudad en Wikipedia en español. La fuente separa y no cuenta a los robots.",
  umbral: "Si un barrio tuvo menos de 5 casos en el año no lo mostramos: con tan pocos casos se podría saber a quién se refiere.",
  distrito: "Orlando elige su concejo en 6 distritos de comisionado. Aquí solo usamos el número del distrito, no el nombre de quien lo representa.",
  derivado: "Lo calculamos nosotros a partir del lago (por ejemplo, el área del barrio o su distrito). No viene así de la fuente.",
  km2: "Total dividido por el área del barrio. Sirve para comparar barrios grandes con barrios pequeños. El área es aproximada (la calculamos del mapa).",
  indice: "Lo calculamos nosotros: cada señal se convierte en un puntaje de 0 a 100 según el puesto del barrio, y se promedian con los pesos que elijas. No es un dato oficial ni mide riesgo; ordena dónde mirar primero.",
  pp: "Puntos porcentuales: la diferencia entre dos porcentajes. Pasar de 4 % a 5 % es subir 1 punto (y un 25 %).",
  estimacion: "El censo publica sus cifras por sector censal, no por barrio. Repartimos cada sector entre los barrios según cuánta superficie comparten (sin contar lagos). Es una aproximación: sirve para comparar, no para citar un barrio al detalle.",
  percentil: "El puesto de un barrio expresado de 0 a 100. 80 quiere decir que está por encima del 80 % de los barrios en esa medida.",
  rentabilidad: "Arriendo de un año dividido por el valor de la vivienda. Es bruta: no descuenta impuestos, seguro, mantenimiento ni meses vacíos.",
  carga: "Hogares que arriendan y gastan 30 % o más de su ingreso en el arriendo. Es la medida estándar de vivienda «no asequible» en EE. UU.",
  zona: "Zonas de Oportunidad: áreas de bajos ingresos donde invertir da beneficios tributarios federales. Main Street y CRA son programas de la ciudad para revitalizar corredores comerciales y el centro.",
  por1000: "Total dividido por los habitantes estimados del barrio, por 1.000. Solo se calcula en barrios con 200 habitantes o más; donde trabaja o compra mucha gente que no vive allí, la tasa se infla."
};
const globo = $("#globo");
function mostrarGlobo(html, x, y) {
  globo.innerHTML = html; globo.classList.add("on");
  const r = globo.getBoundingClientRect();
  let gx = x + 14, gy = y + 14;
  if (gx + r.width > innerWidth - 8) gx = x - r.width - 14;
  if (gy + r.height > innerHeight - 8) gy = y - r.height - 14;
  globo.style.left = Math.max(8, gx) + "px"; globo.style.top = Math.max(8, gy) + "px";
}
const ocultarGlobo = () => globo.classList.remove("on");
const termGlobo = t => { const r = t.getBoundingClientRect(); mostrarGlobo(esc(GLOSARIO[t.dataset.term] || ""), r.left, r.bottom - 6); };
document.addEventListener("pointerover", e => { const t = e.target.closest(".term"); if (t) termGlobo(t); });
document.addEventListener("pointerout", e => { if (e.target.closest(".term")) ocultarGlobo(); });
document.addEventListener("focusin", e => { const t = e.target.closest(".term"); if (t) termGlobo(t); });
document.addEventListener("focusout", e => { if (e.target.closest(".term")) ocultarGlobo(); });
document.addEventListener("click", e => { const t = e.target.closest(".term"); if (t) termGlobo(t); });
addEventListener("scroll", ocultarGlobo, {passive: true});
function aviso(txt) { const t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); t.textContent = txt; document.body.append(t); setTimeout(() => t.remove(), 2200); }
async function copiar(texto, ok = "Copiado") {
  try { await navigator.clipboard.writeText(texto); aviso(ok); }
  catch { const t = document.createElement("textarea"); t.value = texto; document.body.append(t); t.select(); try { document.execCommand("copy"); aviso(ok); } catch { aviso("Selecciona y copia el texto"); } t.remove(); }
}

/* ================= GRÁFICOS (SVG propio, un solo eje) ================= */
function tiempo(s) {
  s = String(s);
  if (/^\d{4}-Q\d$/.test(s)) return Date.UTC(+s.slice(0, 4), (+s.slice(-1) - 1) * 3 + 1, 15);
  if (/^\d{4}-\d{2}$/.test(s)) return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, 15);
  if (/^\d{4}$/.test(s)) return Date.UTC(+s, 6, 1);
  const [f, h] = s.split("T"); const [y, m, d] = f.split("-").map(Number); const [hh, mm] = (h || "00:00").split(":").map(Number);
  return Date.UTC(y, m - 1, d, hh, mm);
}
function ticksY(min, max, n = 5) {
  const span = max - min || 1, paso0 = span / n, mag = 10 ** Math.floor(Math.log10(paso0));
  const paso = [1, 2, 5, 10].map(k => k * mag).find(k => k >= paso0);
  const t = [], fin = Math.ceil(max / paso - 1e-9) * paso;
  for (let v = Math.floor(min / paso) * paso; v <= fin + 1e-9; v += paso) t.push(+v.toFixed(6));
  t.dec = Math.max(0, -Math.floor(Math.log10(paso) + 1e-9));
  return t;
}
const graficos = [];
function observar(el, fn) { if (!el) return; const ro = new ResizeObserver(() => { if (el.clientWidth > 0) fn(); }); ro.observe(el); graficos.push({el, fn}); }
function redibujar() { graficos.forEach(g => g.el.clientWidth && g.fn()); }

function lineas(el, cfg) {
  // cfg.series: [{nombre, puntos, color, resaltar}] · fmtX, fmtY, fmtTick, ref, refs, notas, alto, cero, area, etiquetas (directas al final)
  const W = el.clientWidth, H = cfg.alto || 260;
  const series = cfg.series.filter(s => s.puntos && s.puntos.length);
  const m = {t: 18, r: cfg.etiquetas ? 98 : 18, b: 28, l: 48};
  if (W < 420 && cfg.etiquetas) m.r = 74;
  const todas = series.flatMap(s => s.puntos);
  const ys = todas.map(p => p[1]);
  let y0 = Math.min(...ys), y1 = Math.max(...ys);
  for (const r of [cfg.ref, ...(cfg.refs || [])].filter(Boolean)) { y0 = Math.min(y0, r.y); y1 = Math.max(y1, r.y); }
  if (cfg.cero) y0 = 0;
  const pad = (y1 - y0) * .08 || 1; if (!cfg.cero) y0 -= pad; y1 += pad;
  const ty = ticksY(y0, y1, cfg.nTicks || 5); y0 = Math.min(y0, ty[0]); y1 = Math.max(y1, ty[ty.length - 1]);
  if (W < m.l + m.r + 60) return;
  const xsUnicos = [...new Set(todas.map(p => tiempo(p[0])))].sort((a, b) => a - b);
  const x0 = xsUnicos[0], x1 = ult(xsUnicos);
  const X = t => m.l + (t - x0) / (x1 - x0 || 1) * (W - m.l - m.r);
  const Y = v => m.t + (1 - (v - y0) / (y1 - y0)) * (H - m.t - m.b);
  const anios = (x1 - x0) / 3.15e10, tx = [];
  if (cfg.ticksX) tx.push(...cfg.ticksX(x0, x1));
  else if (anios > 4) { const paso = anios > 40 ? 10 : anios > 18 ? 5 : anios > 8 ? 2 : 1; for (let y = new Date(x0).getUTCFullYear() + 1; y <= new Date(x1).getUTCFullYear(); y++) if (y % paso === 0) tx.push([Date.UTC(y, 0, 1), String(y)]); }
  else { const paso = anios > 2 ? 6 : anios > 1 ? 3 : 2; const d = new Date(x0); for (let y = d.getUTCFullYear(), mm = d.getUTCMonth() + 1; Date.UTC(y, mm, 1) <= x1; mm++) { if (mm > 11) { mm = 0; y++; } if (mm % paso === 0) tx.push([Date.UTC(y, mm, 1), `${MES[mm]} ${String(y).slice(2)}`]); } }
  let s = `<svg viewBox="0 0 ${W} ${H}" height="${H}" role="img" aria-label="${esc(cfg.aria || "")}">`;
  s += `<g class="grid">${ty.map(v => `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}"/>`).join("")}</g>`;
  s += ty.map(v => `<text x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end">${(cfg.fmtTick || ((v, d) => nf(v, d)))(v, ty.dec)}</text>`).join("");
  let ultX = -1e9;
  s += tx.filter(t => cfg.ticksX ? X(t[0]) >= m.l - 1 && X(t[0]) <= W - m.r + 1 : X(t[0]) > m.l + 10 && X(t[0]) < W - m.r - 6).filter(t => { const ok = X(t[0]) - ultX >= 56; if (ok) ultX = X(t[0]); return ok; })
    .map(t => `<text x="${X(t[0])}" y="${H - 8}" text-anchor="middle">${t[1]}</text>`).join("");
  for (const r of [cfg.ref, ...(cfg.refs || [])].filter(Boolean)) {
    const x2 = r.hasta ? X(tiempo(r.hasta)) : W - m.r, xa = r.desde ? X(tiempo(r.desde)) : m.l;
    s += `<line class="ref" x1="${xa}" x2="${x2}" y1="${Y(r.y)}" y2="${Y(r.y)}"/>`;
    if (r.texto) s += `<text class="ref-t" x="${r.desde ? xa + 4 : x2}" y="${Y(r.y) - 7}" text-anchor="${r.desde ? "start" : "end"}">${esc(r.texto)}</text>`;
  }
  const orden = [...series].sort((a, b) => (a.resaltar ? 1 : 0) - (b.resaltar ? 1 : 0));
  for (const se of orden) {
    // Un hueco en la serie (años sin dato) corta la línea en vez de unir los extremos
    const ts = se.puntos.map(p => tiempo(p[0])), pasos = ts.slice(1).map((t, i) => t - ts[i]).sort((a, b) => a - b), tipico = pasos[pasos.length >> 1] || 1;
    const d = se.puntos.map((p, i) => `${!i || ts[i] - ts[i - 1] > tipico * 1.8 ? "M" : "L"}${X(ts[i]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join("");
    if (cfg.area && (se.resaltar || series.length === 1)) s += `<path d="${d}L${X(tiempo(ult(se.puntos)[0]))},${Y(y0)}L${X(tiempo(se.puntos[0][0]))},${Y(y0)}Z" style="fill:${se.color};opacity:.12"/>`;
    s += `<path d="${d}" fill="none" style="stroke:${se.color}" stroke-width="${se.resaltar || series.length === 1 ? 2.4 : 1.6}" stroke-linejoin="round" stroke-linecap="round"/>`;
    const u = ult(se.puntos);
    s += `<circle cx="${X(tiempo(u[0]))}" cy="${Y(u[1])}" r="${se.resaltar || series.length === 1 ? 4.5 : 3}" style="fill:${se.color};stroke:var(--surface)" stroke-width="2"/>`;
  }
  if (cfg.etiquetas && series.length > 1) {
    const etq = series.map(se => ({se, y: Y(ult(se.puntos)[1]), x: X(tiempo(ult(se.puntos)[0]))})).sort((a, b) => a.y - b.y);
    for (let i = 1; i < etq.length; i++) if (etq[i].y - etq[i - 1].y < 14) etq[i].y = etq[i - 1].y + 14;
    for (const e of etq) s += `<text class="etq" x="${e.x + 8}" y="${e.y + 4}" style="fill:${e.se.resaltar ? "var(--ink)" : "var(--ink-2)"};font-weight:${e.se.resaltar ? 700 : 500}">${esc(e.se.nombre)}</text>`;
  }
  (cfg.notas || []).forEach(n => {
    const p = series[0].puntos.find(q => q[0] === n.x); if (!p) return;
    const cx = X(tiempo(p[0])), cy = Y(p[1]), arriba = n.pos !== "abajo";
    const anc = cx > W - 120 ? "end" : cx < m.l + 80 ? "start" : "middle";
    s += `<circle cx="${cx}" cy="${cy}" r="3.5" style="fill:var(--surface);stroke:var(--ink-2)" stroke-width="1.5"/><text class="anot" x="${cx}" y="${arriba ? cy - 12 : cy + 20}" text-anchor="${anc}">${esc(n.texto)}</text>`;
  });
  s += `<line class="cruz" x1="0" x2="0" y1="${m.t}" y2="${H - m.b}" visibility="hidden"/>`;
  series.forEach((se, k) => s += `<circle class="pz" data-k="${k}" r="5" style="fill:${se.color};stroke:var(--surface)" stroke-width="2" visibility="hidden"/>`);
  s += `<rect x="${m.l}" y="0" width="${W - m.l - m.r}" height="${H}" fill="transparent"/></svg>`;
  el.innerHTML = s;
  const svg = el.querySelector("svg"), cz = svg.querySelector(".cruz");
  const mapas = series.map(se => new Map(se.puntos.map(p => [tiempo(p[0]), p])));
  const bx = xsUnicos.map(X);
  const mover = e => {
    const r = svg.getBoundingClientRect(), x = (e.clientX - r.left) * (W / r.width);
    let lo = 0, hi = bx.length - 1; while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (bx[mid] < x) lo = mid; else hi = mid; }
    const i = Math.abs(bx[lo] - x) < Math.abs(bx[hi] - x) ? lo : hi, t = xsUnicos[i];
    cz.setAttribute("x1", bx[i]); cz.setAttribute("x2", bx[i]); cz.setAttribute("visibility", "visible");
    let html = "", etiqueta = null;
    const filas = [];
    series.forEach((se, k) => {
      const p = mapas[k].get(t), c = svg.querySelector(`.pz[data-k="${k}"]`);
      if (!p) { c.setAttribute("visibility", "hidden"); return; }
      etiqueta = etiqueta || p[0];
      c.setAttribute("cx", X(t)); c.setAttribute("cy", Y(p[1])); c.setAttribute("visibility", "visible");
      filas.push([se, p]);
    });
    filas.sort((a, b) => b[1][1] - a[1][1]);
    html = `<b>${esc(cfg.fmtX(etiqueta))}</b>` + filas.map(([se, p]) => `<br>${series.length > 1 ? esc(se.nombre) + ": " : ""}<b>${cfg.fmtY(p[1], p, se)}</b>`).join("");
    if (cfg.extra) html += cfg.extra(etiqueta);
    mostrarGlobo(html, e.clientX, e.clientY);
  };
  svg.addEventListener("pointermove", mover);
  svg.addEventListener("pointerdown", mover);
  svg.addEventListener("pointerleave", () => { ocultarGlobo(); cz.setAttribute("visibility", "hidden"); $$(".pz", svg).forEach(c => c.setAttribute("visibility", "hidden")); });
}

function barras(el, cfg) {
  const W = el.clientWidth, H = cfg.alto || 230, m = {t: 22, r: 8, b: 28, l: 48};
  const pts = cfg.puntos, n = pts.length, max = Math.max(...pts.map(p => p[1] ?? 0));
  if (W < m.l + m.r + 60) return;
  const ty = ticksY(0, max, 4), y1 = ult(ty);
  const bw = (W - m.l - m.r) / n, Y = v => m.t + (1 - v / y1) * (H - m.t - m.b);
  const res = cfg.resaltar ?? n - 1;
  let s = `<svg viewBox="0 0 ${W} ${H}" height="${H}" role="img" aria-label="${esc(cfg.aria || "")}"><g class="grid">${ty.map(v => `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}"/>`).join("")}</g>`;
  s += ty.map(v => `<text x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end">${(cfg.fmtTick || nf)(v)}</text>`).join("");
  const cada = Math.ceil(n / Math.max(3, Math.floor((W - m.l) / 58)));
  pts.forEach((p, i) => {
    if ((n - 1 - i) % cada === 0) s += `<text x="${m.l + i * bw + bw / 2}" y="${H - 8}" text-anchor="middle">${esc(cfg.fmtEje ? cfg.fmtEje(p[0]) : p[0])}</text>`;
    if (p[1] == null) return;
    const x = m.l + i * bw + 1, w = Math.max(1, bw - 2), y = Y(p[1]), r = Math.min(4, w / 2, Math.max(0, Y(0) - y));
    const col = cfg.color ? cfg.color(p, i) : i === res ? "var(--accent)" : "var(--seq-2)";
    s += `<path class="br" data-i="${i}" d="M${x},${Y(0)}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${Y(0)}Z" style="fill:${col}"/>`;
  });
  const u = pts[res];
  if (u) s += `<text x="${Math.min(m.l + res * bw + bw / 2, W - 28)}" y="${Y(u[1]) - 7}" text-anchor="middle" style="fill:var(--ink);font-weight:500">${(cfg.fmtTick || nf)(u[1])}</text>`;
  s += `</svg>`;
  el.innerHTML = s;
  const svg = el.querySelector("svg");
  svg.addEventListener("pointermove", e => {
    const r = svg.getBoundingClientRect(), x = (e.clientX - r.left) * (W / r.width);
    const i = Math.max(0, Math.min(n - 1, Math.floor((x - m.l) / bw)));
    $$(".br", svg).forEach(b => b.style.opacity = +b.dataset.i === i ? 1 : .55);
    mostrarGlobo(`<b>${esc(cfg.fmtX(pts[i][0]))}</b><br>${pts[i][1] == null ? "Sin dato completo ese año" : cfg.fmtY(pts[i][1], i)}`, e.clientX, e.clientY);
  });
  svg.addEventListener("pointerleave", () => { ocultarGlobo(); $$(".br", svg).forEach(b => b.style.opacity = 1); });
}

function spark(puntos, color = "var(--accent)", alto = 52) {
  const W = 300, H = alto, ys = puntos.map(p => p[1]), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const X = i => 2 + i / (puntos.length - 1) * (W - 8), Y = v => 6 + (1 - (v - y0) / (y1 - y0 || 1)) * (H - 12);
  const d = puntos.map((p, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(p[1]).toFixed(1)}`).join("");
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true"><path d="${d}L${X(puntos.length - 1)},${H}L2,${H}Z" style="fill:${color};opacity:.12"/><path d="${d}" fill="none" style="stroke:${color}" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>`;
}

function listaBarras(ol, filas, cfg = {}) {
  // filas: [{nombre, valor, i?, yo?, par?, fmt?}] · cfg.onClick(fila), cfg.max, cfg.fmt, cfg.pos (mostrar puesto)
  const max = cfg.max || Math.max(...filas.map(f => f.valor || 0), 1);
  ol.innerHTML = filas.map((f, k) => {
    const cls = [f.yo ? "yo" : "", f.par ? "par" : ""].join(" ");
    const tag = cfg.onClick ? "button" : "div";
    return `<li class="${cls}"><${tag} ${tag === "button" ? `type="button" data-k="${k}" aria-pressed="${!!f.sel}"` : 'class="fila"'}><span class="pos">${cfg.pos === false ? "" : f.pos ?? k + 1}</span><span class="nom">${esc(f.nombre)}</span><span class="val">${(f.fmt || cfg.fmt || nf)(f.valor)}</span><span class="bar"><i style="width:${Math.max(0, f.valor) / max * 100}%"></i></span></${tag}></li>`;
  }).join("");
  if (cfg.onClick) ol.onclick = e => { const b = e.target.closest("button[data-k]"); if (b) cfg.onClick(filas[+b.dataset.k]); };
}

function barrasSimples(el, filas, fmt = nf) {
  const max = Math.max(...filas.map(f => f[1]), 1);
  el.innerHTML = filas.map(([k, n]) => `<div class="f"><span>${esc(k)}</span><b class="num">${fmt(n)}</b><span class="bar"><i style="width:${n / max * 100}%"></i></span></div>`).join("");
}

/* ================= BARRIOS: un solo modelo para todas las vistas ================= */
const norm = s => String(s || "").trim().toLowerCase();
const IDX = new Map(M.barrios.map((b, i) => [norm(b.nombre), i]));
const B = M.barrios.map(b => ({...b, nombre: bonito(b.nombre), permisos: {}, delitos: {}, codigo: {}}));
const anioFin = (tema, pref) => Object.keys(L[tema].series).filter(k => k.startsWith(pref)).map(k => +k.slice(-4)).filter(Boolean).sort();
const A_PERM = anioFin("permisos", "permisos_barrio_"), A_DEL = anioFin("seguridad", "delitos_barrio_"), A_COD = anioFin("codigo", "casos_barrio_");
const U_PERM = ult(A_PERM), U_DEL = ult(A_DEL), U_COD = ult(A_COD);
function cargar(tema, serie, fn) { for (const [n, v] of S(tema, serie)) { const i = IDX.get(norm(n)); if (i != null) fn(B[i], v); } }
A_PERM.forEach(a => cargar("permisos", `permisos_barrio_${a}`, (b, v) => b.permisos[a] = v));
A_DEL.forEach(a => cargar("seguridad", `delitos_barrio_${a}`, (b, v) => b.delitos[a] = v));
A_COD.forEach(a => cargar("codigo", `casos_barrio_${a}`, (b, v) => b.codigo[a] = v));
for (const g of ["hurtos", "violencia", "drogas"]) cargar("seguridad", `${g}_barrio_${U_DEL}`, (b, v) => b[g] = v);
cargar("codigo", `quejas_barrio_${U_COD}`, (b, v) => b.quejas = v);
cargar("negocios", "negocios_barrio", (b, v) => b.negocios = v);
cargar("negocios", "restaurantes_barrio", (b, v) => b.restaurantes = v);
cargar("negocios", "hospedajes_barrio", (b, v) => b.hospedajes = v);
const VIG_NEG = C("negocios", "negocios_vigentes").vigencia;
// v3: quién vive (censo, estimado por barrio), riesgo (FEMA), servicios, futuro (proyección 2045) e incentivos
const U_AP = +Object.keys(L.negocios.series).find(k => k.startsWith("aperturas_barrio_")).slice(-4);
for (const [serie, campo] of [["poblacion", "pob"], ["ingreso_mediano", "ingreso"], ["arriendo_mediano", "arriendo"], ["valor_vivienda", "valor"],
  ["pct_carga_arriendo", "carga"], ["pct_arrendatarios", "arrend"], ["pct_sin_carro", "sinCarro"], ["pct_espanol", "espanol"], ["pct_pobreza", "pobreza"],
  ["pct_universitarios", "univ"], ["edad_mediana", "edad"], ["minutos_al_trabajo", "minutos"], ["pct_vacantes", "vacantes"]])
  cargar("censo", `${serie}_barrio`, (b, v) => b[campo] = v);
for (const [serie, campo] of [["riesgo_total", "rTotal"], ["riesgo_huracan", "rHuracan"], ["riesgo_inundacion", "rInund"], ["riesgo_calor", "rCalor"],
  ["riesgo_tornado", "rTornado"], ["vulnerabilidad_social", "rVulner"], ["perdida_anual_esperada", "perdida"]])
  cargar("riesgo", `${serie}_barrio`, (b, v) => b[campo] = v);
for (const [serie, campo] of [["parques", "parques"], ["parques_km2", "parquesKm2"], ["colegios", "colegios"], ["charter", "charter"], ["sunrail", "sunrail"], ["ciclovias_km", "ciclo"]])
  cargar("servicios", `${serie}_barrio`, (b, v) => b[campo] = v);
for (const [serie, campo] of [["poblacion_2017", "pob17"], ["poblacion_2045", "pob45"], ["crecimiento_poblacion_2045", "crec45"], ["empleo_2017", "emp17"],
  ["empleo_2045", "emp45"], ["crecimiento_empleo_2045", "crecEmp45"], ["zona_oportunidad", "zo"], ["main_street", "mainSt"], ["cra", "cra"],
  ["proyectos_grandes", "grandes"], ["solicitudes_abiertas", "abiertas"], [`solicitudes_barrio_${U_PERM}`, "solicitudes"]])
  cargar("planeacion", serie.includes("solicitudes_barrio") ? serie : `${serie}_barrio`, (b, v) => b[campo] = v);
for (const g of ["comercio", "belleza", "profesionales", "automotor"]) cargar("negocios", `${g}_barrio`, (b, v) => b[g] = v);
cargar("negocios", `aperturas_barrio_${U_AP}`, (b, v) => b.aperturas = v);
const MIN_HAB = C("censo", "minimo_habitantes_por_barrio").valor;
const VIG_CEN = C("censo", "poblacion_ciudad").vigencia, VIG_NRI = C("riesgo", "riesgo_total_promedio_barrios").vigencia;

// Una métrica se define una vez: nombre, unidad, de dónde sale y cómo se lee de un barrio
const METRICAS = {
  permisos: {frase: "permisos", nombre: "Permisos de construcción", corto: "Permisos", unidad: "permisos", anios: A_PERM, v: (b, a = U_PERM) => b.permisos[a], fuente: "orlando_permisos", campo: "permisos_barrio_<AAAA>", icono: "grua"},
  delitos: {frase: "casos de policía", nombre: "Casos de policía", corto: "Casos policía", unidad: "casos", anios: A_DEL, v: (b, a = U_DEL) => b.delitos[a], fuente: "opd_casos", campo: "delitos_barrio_<AAAA>", icono: "sirena", nota: "hurtos, violencia y drogas"},
  hurtos: {frase: "hurtos", nombre: "Hurtos y robos a la propiedad", corto: "Hurtos", unidad: "casos", anios: [U_DEL], v: b => b.hurtos, fuente: "opd_casos", campo: `hurtos_barrio_${U_DEL}`},
  violencia: {frase: "casos de violencia", nombre: "Violencia contra personas", corto: "Violencia", unidad: "casos", anios: [U_DEL], v: b => b.violencia, fuente: "opd_casos", campo: `violencia_barrio_${U_DEL}`},
  drogas: {frase: "casos de drogas", nombre: "Casos de drogas", corto: "Drogas", unidad: "casos", anios: [U_DEL], v: b => b.drogas, fuente: "opd_casos", campo: `drogas_barrio_${U_DEL}`},
  quejas: {frase: "quejas ciudadanas", nombre: "Quejas ciudadanas de código", corto: "Quejas", unidad: "quejas", anios: [U_COD], v: b => b.quejas, fuente: "orlando_codigo", campo: `quejas_barrio_${U_COD}`, icono: "alerta"},
  codigo: {frase: "casos de código", nombre: "Casos de código urbano", corto: "Casos de código", unidad: "casos", anios: A_COD, v: (b, a = U_COD) => b.codigo[a], fuente: "orlando_codigo", campo: "casos_barrio_<AAAA>"},
  negocios: {frase: "negocios", nombre: "Negocios con licencia vigente", corto: "Negocios", unidad: "licencias", anios: [VIG_NEG.slice(0, 4)], v: b => b.negocios, fuente: "orlando_negocios", campo: "negocios_barrio", icono: "empleo"},
  restaurantes: {frase: "restaurantes", nombre: "Restaurantes con licencia", corto: "Restaurantes", unidad: "licencias", anios: [VIG_NEG.slice(0, 4)], v: b => b.restaurantes, fuente: "orlando_negocios", campo: "restaurantes_barrio"},
  hospedajes: {frase: "hospedajes", nombre: "Hospedajes con licencia", corto: "Hospedajes", unidad: "licencias", anios: [VIG_NEG.slice(0, 4)], v: b => b.hospedajes, fuente: "orlando_negocios", campo: "hospedajes_barrio", icono: "maleta"},
};
const usdF = v => "US$" + NB + nf(v), pctF = v => nf(v, 1) + NB + "%", pctF0 = v => nf(v, 0) + NB + "%", ptsF = v => nf(v, 0);
const crecF = v => (v > 0 ? "+" : v < 0 ? "\u2212" : "") + nf(Math.abs(v), 0) + NB + "%";
const CEN = (campo, nombre, corto, unidad, dir, fmt, extra = {}) => ({tipo: "tasa", frase: corto.toLowerCase(), nombre, corto, unidad, anios: [VIG_CEN],
  v: b => b[campo], fuente: "censo_acs", campo: extra.campo, dir, fmt, grupo: "Quién vive", ...extra});
const NRI = (campo, nombre, corto, serie, extra = {}) => ({tipo: "tasa", frase: `riesgo de ${corto.toLowerCase()}`, nombre, corto, unidad: "puntaje de 0 a 100 (percentil nacional)",
  anios: [VIG_NRI], v: b => b[campo], fuente: "fema_nri", campo: serie, dir: -1, fmt: ptsF, grupo: "Riesgo", ...extra});
const SIG = (campo, nombre, corto, unidad, serie, extra = {}) => ({tipo: "conteo", cero: true, frase: corto.toLowerCase(), nombre, corto, unidad, anios: [L.servicios.probado.slice(0, 4)],
  v: b => b[campo] ?? 0, fuente: "orlando_sig", campo: serie, dir: 1, grupo: "Qué tiene cerca", ...extra});
Object.assign(METRICAS, {
  poblacion: {tipo: "poblacion", frase: "habitantes", nombre: "Población (estimada)", corto: "Población", unidad: "habitantes", anios: [VIG_CEN], v: b => b.pob,
    fuente: "censo_acs", campo: "poblacion_barrio", dir: 0, grupo: "Quién vive", icono: "gente"},
  ingreso: CEN("ingreso", "Ingreso mediano de los hogares (aprox.)", "Ingreso", "dólares al año", 1, usdF, {campo: "ingreso_mediano_barrio", icono: "empleo"}),
  arriendo: CEN("arriendo", "Arriendo mediano (aprox.)", "Arriendo", "dólares al mes", -1, usdF, {campo: "arriendo_mediano_barrio", icono: "casa"}),
  valorViv: CEN("valor", "Valor de la vivienda propia (aprox.)", "Valor vivienda", "dólares", 0, usdF, {campo: "valor_vivienda_barrio"}),
  carga: CEN("carga", "Arrendatarios que gastan 30 % o más del ingreso en arriendo", "Carga de arriendo", "% de los hogares arrendatarios", -1, pctF, {campo: "pct_carga_arriendo_barrio"}),
  arrend: CEN("arrend", "Hogares que arriendan", "Arriendan", "% de los hogares", 0, pctF, {campo: "pct_arrendatarios_barrio"}),
  sinCarro: CEN("sinCarro", "Hogares sin carro", "Sin carro", "% de los hogares", 0, pctF, {campo: "pct_sin_carro_barrio", icono: "tren"}),
  espanol: CEN("espanol", "Hablan español en casa", "Español", "% de los mayores de 5 años", 0, pctF, {campo: "pct_espanol_barrio"}),
  pobreza: CEN("pobreza", "Personas en pobreza", "Pobreza", "% de las personas", -1, pctF, {campo: "pct_pobreza_barrio"}),
  univ: CEN("univ", "Con título universitario", "Universitarios", "% de los mayores de 25", 1, pctF, {campo: "pct_universitarios_barrio"}),
  edad: CEN("edad", "Edad mediana", "Edad", "años", 0, v => nf(v, 1), {campo: "edad_mediana_barrio"}),
  minutos: CEN("minutos", "Viaje al trabajo (promedio)", "Viaje al trabajo", "minutos", -1, v => nf(v, 0) + NB + "min", {campo: "minutos_al_trabajo_barrio"}),
  rInund: NRI("rInund", "Riesgo de inundación (FEMA)", "Inundación", "riesgo_inundacion_barrio", {icono: "gota"}),
  rHuracan: NRI("rHuracan", "Riesgo de huracán (FEMA)", "Huracán", "riesgo_huracan_barrio", {icono: "viento"}),
  rCalor: NRI("rCalor", "Riesgo por olas de calor (FEMA)", "Calor", "riesgo_calor_barrio", {icono: "sol"}),
  rTornado: NRI("rTornado", "Riesgo de tornado (FEMA)", "Tornado", "riesgo_tornado_barrio"),
  rVulner: NRI("rVulner", "Vulnerabilidad social (FEMA)", "Vulnerabilidad", "vulnerabilidad_social_barrio", {frase: "vulnerabilidad social"}),
  parques: SIG("parques", "Parques de la ciudad", "Parques", "parques", "parques_barrio", {icono: "arbol"}),
  colegios: SIG("colegios", "Colegios públicos", "Colegios", "colegios", "colegios_barrio", {icono: "escuela"}),
  ciclo: SIG("ciclo", "Ciclovías existentes", "Ciclovías", "km", "ciclovias_km_barrio", {fmt: v => nf(v, 1) + NB + "km"}),
  sunrail: SIG("sunrail", "Estaciones de SunRail", "SunRail", "estaciones", "sunrail_barrio", {icono: "tren"}),
  crec45: {tipo: "tasa", frase: "crecimiento proyectado", nombre: "Residentes proyectados 2017 → 2045", corto: "Crecimiento 2045", unidad: "% de cambio (proyección de la ciudad)",
    anios: ["2045"], v: b => b.crec45, fuente: "orlando_sig", campo: "crecimiento_poblacion_2045_barrio", dir: 0, fmt: crecF, grupo: "Hacia dónde va", icono: "futuro"},
  crecEmp45: {tipo: "tasa", frase: "crecimiento del empleo", nombre: "Empleos proyectados 2017 → 2045", corto: "Empleo 2045", unidad: "% de cambio (proyección de la ciudad)",
    anios: ["2045"], v: b => b.crecEmp45, fuente: "orlando_sig", campo: "crecimiento_empleo_2045_barrio", dir: 0, fmt: crecF, grupo: "Hacia dónde va"},
  zo: {tipo: "tasa", cero: true, frase: "zona de oportunidad", nombre: "Dentro de una Zona de Oportunidad federal", corto: "Zona de oportunidad", unidad: "% del barrio",
    anios: [L.planeacion.probado.slice(0, 4)], v: b => b.zo ?? 0, fuente: "orlando_sig", campo: "zona_oportunidad_barrio", dir: 0, fmt: pctF0, grupo: "Hacia dónde va"},
  grandes: {tipo: "conteo", frase: "solicitudes de proyectos grandes", nombre: "Solicitudes de proyectos grandes (2 años)", corto: "Proyectos grandes", unidad: "solicitudes",
    anios: [String(U_PERM)], v: b => b.grandes, fuente: "orlando_planeacion", campo: "proyectos_grandes_barrio", dir: 0, grupo: "Hacia dónde va", icono: "grua"},
  abiertas: {tipo: "conteo", frase: "solicitudes abiertas", nombre: "Solicitudes de planeación abiertas hoy", corto: "Solicitudes abiertas", unidad: "solicitudes",
    anios: [L.planeacion.probado.slice(0, 4)], v: b => b.abiertas, fuente: "orlando_planeacion", campo: "solicitudes_abiertas_barrio", dir: 0, grupo: "Hacia dónde va"},
  aperturas: {tipo: "conteo", frase: `negocios abiertos en ${U_AP}`, nombre: `Negocios que abrieron en ${U_AP}`, corto: `Aperturas ${U_AP}`, unidad: "licencias",
    anios: [String(U_AP)], v: b => b.aperturas, fuente: "orlando_negocios", campo: `aperturas_barrio_${U_AP}`, dir: 0, grupo: "Qué pasa", icono: "tienda"},
  comercio: {tipo: "conteo", frase: "tiendas y comercios", nombre: "Comercios con licencia", corto: "Comercios", unidad: "licencias", anios: [VIG_NEG.slice(0, 4)], v: b => b.comercio, fuente: "orlando_negocios", campo: "comercio_barrio", dir: 0},
  belleza: {tipo: "conteo", frase: "salones de belleza", nombre: "Salones de belleza con licencia", corto: "Belleza", unidad: "licencias", anios: [VIG_NEG.slice(0, 4)], v: b => b.belleza, fuente: "orlando_negocios", campo: "belleza_barrio", dir: 0},
  profesionales: {tipo: "conteo", frase: "servicios profesionales", nombre: "Servicios profesionales con licencia", corto: "Profesionales", unidad: "licencias", anios: [VIG_NEG.slice(0, 4)], v: b => b.profesionales, fuente: "orlando_negocios", campo: "profesionales_barrio", dir: 0},
});
for (const k of ["permisos", "delitos", "hurtos", "violencia", "drogas", "quejas", "codigo", "negocios", "restaurantes", "hospedajes"]) {
  METRICAS[k].tipo = "conteo"; METRICAS[k].grupo = "Qué pasa";
  METRICAS[k].dir = ["delitos", "hurtos", "violencia", "drogas", "quejas", "codigo"].includes(k) ? -1 : 0;
}
const porKm2 = (v, b) => v == null || !b.km2 ? null : v / b.km2;
const porHab = (v, b) => v == null || !(b.pob >= MIN_HAB) ? null : v / b.pob * 1000;
// modo: "total", "km2" o "hab" (por 1.000 habitantes). Una tasa (porcentaje, mediana, puntaje) no se divide por área ni por gente.
const aplica = (met, modo) => !modo || modo === "total" || METRICAS[met].tipo === "conteo" || (METRICAS[met].tipo === "poblacion" && modo === "km2");
function valorDe(met, b, a, modo) {
  if (modo === true) modo = "km2";
  const v = METRICAS[met].v(b, a) ?? null;
  if (!modo || modo === "total" || !aplica(met, modo)) return v;
  return modo === "km2" ? porKm2(v, b) : porHab(v, b);
}
const sufijo = modo => modo === "km2" ? " por km²" : modo === "hab" ? " por 1.000 hab." : "";
const fmtV = (v, modo, met) => v == null ? "sin dato" : modo === true || modo === "km2" || modo === "hab" ? nf(v, v < 10 ? 1 : 0) : met && METRICAS[met] && METRICAS[met].fmt ? METRICAS[met].fmt(v) : nf(v);
function cortesQ(vals, n = 5) {
  const o = vals.filter(v => v != null).sort((a, b) => a - b);
  if (!o.length) return [];
  return Array.from({length: n - 1}, (_, k) => o[Math.min(o.length - 1, Math.floor((k + 1) / n * o.length))]);
}
const mediana = arr => { const o = arr.filter(v => v != null).sort((a, b) => a - b); return o.length ? (o.length % 2 ? o[o.length >> 1] : (o[o.length / 2 - 1] + o[o.length / 2]) / 2) : null; };
const binDe = (v, cortes) => v == null ? -1 : (cortes.findIndex(c => v < c) + 1 || cortes.length + 1) - 1;
const colorBin = i => i < 0 ? css("--nodata") : css(`--seq-${i + 1}`);
const colorBinVar = i => i < 0 ? "url(#rayado)" : `var(--seq-${i + 1})`;

// Índice derivado: cuatro señales por km², puntaje de 0 a 100 según el puesto (percentil); sin dato = el valor más bajo
const DIMS = [
  {k: "permisos", nombre: "Construcción", desc: "permisos por km²"},
  {k: "delitos", nombre: "Seguridad", desc: "casos de policía por km²"},
  {k: "quejas", nombre: "Convivencia", desc: "quejas ciudadanas por km²"},
  {k: "negocios", nombre: "Actividad", desc: "negocios por km²"},
];
const PRESETS = {"Equilibrio": [1, 1, 1, 1], "Crecimiento": [3, 1, 1, 1], "Seguridad": [1, 3, 1, 1], "Convivencia": [1, 1, 3, 1]};
const percentil = DIMS.map(d => {
  const vals = B.map(b => valorDe(d.k, b, undefined, true) ?? 0);
  const ord = [...vals].sort((a, b) => a - b);
  return vals.map(v => { let lo = 0; while (lo < ord.length && ord[lo] < v) lo++; let hi = lo; while (hi < ord.length && ord[hi] === v) hi++; return ((lo + hi - 1) / 2) / (ord.length - 1) * 100; });
});
let pesos = [...PRESETS.Equilibrio];
function indice(p = pesos) { const t = p.reduce((a, b) => a + b, 0) || 1; return B.map((b, i) => DIMS.reduce((s, d, k) => s + percentil[k][i] * p[k], 0) / t); }
let IND = indice();
METRICAS.indice = {frase: "puntaje en el índice", nombre: "Índice de atención (derivado)", corto: "Índice", unidad: "puntos de 0 a 100", anios: [String(U_PERM)], v: b => IND[M.barrios.indexOf(M.barrios.find(x => x.id === b.id))], icono: "pesas", sinKm2: true};
B.forEach((b, i) => b._i = i);
METRICAS.indice.v = b => IND[b._i];

/* ================= MAPA PLANO (SVG) ================= */
function mapaPlano(svg, cfg) {
  // cfg: valores(i) -> número|null, onClick(i), globo(i) -> html, ley (elemento), titulo
  svg.setAttribute("viewBox", `0 0 ${M.ancho} ${M.alto}`);
  svg.innerHTML = `<defs><pattern id="${svg.id}-r" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)"><rect width="7" height="7" style="fill:var(--nodata)"/><line x1="0" y1="0" x2="0" y2="7" style="stroke:var(--hatch)" stroke-width="2.4"/></pattern></defs>
    ${M.barrios.map((b, i) => `<path class="b" data-i="${i}" d="${b.d}"/>`).join("")}
    <path class="lago" d="${M.lagos}"/>${M.distritos.map(d => `<path class="dist" d="${d.d}"/>`).join("")}<path class="lim" d="${M.limite}"/>`;
  const pintar = () => {
    const vals = M.barrios.map((_, i) => cfg.valores(i));
    const cortes = cfg.cortes || cortesQ(vals);
    $$(".b", svg).forEach(p => { const k = binDe(vals[+p.dataset.i], cortes); p.style.fill = k < 0 ? `url(#${svg.id}-r)` : `var(--seq-${k + 1})`; });
    if (cfg.ley) {
      const o = vals.filter(v => v != null).sort((a, b) => a - b), lim = [o[0], ...cortes, ult(o)], f = cfg.fmt || nf;
      cfg.ley.innerHTML = (cfg.titulo ? `<b>${esc(cfg.titulo())}</b>` : "") + [0, 1, 2, 3, 4].map(k => `<span class="sw"><i style="background:var(--seq-${k + 1})"></i>${cfg.etiquetas ? esc(cfg.etiquetas[k]) : k < 4 ? `${f(lim[k])}–${f(lim[k + 1])}` : `${f(lim[4])} o más`}</span>`).join("") + `<span class="sw"><i class="nd"></i>Sin dato publicable</span>`;
    }
  };
  svg.addEventListener("pointermove", e => { const p = e.target.closest(".b"); if (!p) return ocultarGlobo(); mostrarGlobo(cfg.globo(+p.dataset.i), e.clientX, e.clientY); });
  svg.addEventListener("pointerleave", ocultarGlobo);
  svg.addEventListener("click", e => { const p = e.target.closest(".b"); if (p && cfg.onClick) cfg.onClick(+p.dataset.i); });
  pintar();
  return {pintar};
}

/* ================= MAPA 3D (MapLibre GL, sin teselas ni llaves: solo las capas del lago) ================= */
// Lentes del mapa. «modo» fija la medida (la densidad siempre es por km²); «grupo» arma el selector de la vista Barrios
const LENTES = [
  {k: "permisos", nombre: "Construcción", icono: "grua", grupo: "Qué pasa"},
  {k: "delitos", nombre: "Seguridad", icono: "sirena", grupo: "Qué pasa"},
  {k: "quejas", nombre: "Quejas", icono: "alerta", grupo: "Qué pasa"},
  {k: "negocios", nombre: "Negocios", icono: "empleo", grupo: "Qué pasa"},
  {k: "aperturas", nombre: "Negocios nuevos", icono: "tienda", grupo: "Qué pasa"},
  {k: "hospedajes", nombre: "Hospedaje", icono: "maleta", grupo: "Qué pasa"},
  {k: "poblacion", nombre: "Población", icono: "gente", grupo: "Quién vive", modo: "km2", nombreLargo: "Densidad de población"},
  {k: "ingreso", nombre: "Ingreso", icono: "empleo", grupo: "Quién vive"},
  {k: "arriendo", nombre: "Arriendo", icono: "casa", grupo: "Quién vive"},
  {k: "carga", nombre: "Carga de arriendo", icono: "casa", grupo: "Quién vive"},
  {k: "sinCarro", nombre: "Sin carro", icono: "tren", grupo: "Quién vive"},
  {k: "espanol", nombre: "Español", icono: "gente", grupo: "Quién vive"},
  {k: "parques", nombre: "Parques", icono: "arbol", grupo: "Qué tiene cerca"},
  {k: "ciclo", nombre: "Ciclovías", icono: "ruta", grupo: "Qué tiene cerca"},
  {k: "rInund", nombre: "Inundación", icono: "gota", grupo: "Riesgo"},
  {k: "rHuracan", nombre: "Huracán", icono: "viento", grupo: "Riesgo"},
  {k: "rVulner", nombre: "Vulnerabilidad", icono: "alerta", grupo: "Riesgo"},
  {k: "crec45", nombre: "Futuro 2045", icono: "futuro", grupo: "Hacia dónde va"},
  {k: "grandes", nombre: "Proyectos grandes", icono: "grua", grupo: "Hacia dónde va"},
  {k: "zo", nombre: "Zona de oportunidad", icono: "tienda", grupo: "Hacia dónde va"},
  {k: "indice", nombre: "Índice", icono: "pesas", grupo: "Índice"},
];
const lenteDe = k => LENTES.find(l => l.k === k) || {k, nombre: METRICAS[k].corto};
const hay3D = () => { try { return !!(window.maplibregl && (maplibregl.supported ? maplibregl.supported() : true)); } catch { return false; } };
function crearAtlas(el, cfg) {
  // cfg: lentes (lista de claves), estado {lente, anio, km2}, onSelect(i), compacto
  const st = Object.assign({lente: "permisos", anio: null, modo: "total", sel: null}, cfg.estado || {});
  const lentes = cfg.lentes ? cfg.lentes.map(lenteDe) : LENTES;
  const grupos = [...new Set(lentes.map(l => l.grupo))];
  const selector = cfg.selector ? `<label class="sr" for="${el.id}-lente">Qué mostrar en el mapa</label><select class="lente-sel" id="${el.id}-lente">${grupos.map(g => `<optgroup label="${esc(g)}">${lentes.filter(l => l.grupo === g).map(l => `<option value="${l.k}" ${l.k === st.lente ? "selected" : ""}>${esc(l.nombreLargo || METRICAS[l.k].nombre)}</option>`).join("")}</optgroup>`).join("")}</select>`
    : `<div class="lentes" role="group" aria-label="Qué mostrar en el mapa">${lentes.map(l => `<button type="button" data-l="${l.k}" aria-pressed="${l.k === st.lente}">${ic(l.icono)}${l.nombre}</button>`).join("")}</div>`;
  el.innerHTML = `<div class="lienzo3d"></div>
    <div class="superior">${selector}</div>
    <div class="controles"><button type="button" data-z="mas" aria-label="Acercar">${ic("mas")}</button><button type="button" data-z="menos" aria-label="Alejar">${ic("menos")}</button><button type="button" data-z="3d" aria-label="Cambiar entre vista 3D y plana">2D</button><button type="button" data-z="todo" aria-label="Ver toda la ciudad">${ic("centrar")}</button></div>
    <div class="ley3d"></div>`;
  const lienzo = $(".lienzo3d", el), ley = $(".ley3d", el);
  let map = null, listo = false, svgFallback = null;
  const datos = () => {
    const met = METRICAS[st.lente], a = st.anio && met.anios.map(Number).includes(+st.anio) ? +st.anio : undefined;
    const fijo = lenteDe(st.lente).modo, modo = fijo || (aplica(st.lente, st.modo) ? st.modo : "total");
    const vals = B.map(b => valorDe(st.lente, b, a, modo));
    const pos = vals.filter(v => v != null), min = Math.min(0, ...pos), max = Math.max(...pos, 1);
    return {met, a: a ?? ult(met.anios), modo, km2: modo !== "total", vals, cortes: cortesQ(vals), min, max};
  };
  const leyenda = d => {
    const o = d.vals.filter(v => v != null).sort((a, b) => a - b);
    const t = `${lenteDe(st.lente).nombreLargo || d.met.nombre}${lenteDe(st.lente).modo ? "" : sufijo(d.modo)}${d.met.anios.length > 1 ? ` · ${d.a}` : ""}`;
    ley.innerHTML = `<b>${esc(t)}</b><span class="ex">Color y altura: más alto, más ${esc(d.met.unidad)}${lenteDe(st.lente).modo ? " por km²" : ""}</span><div class="esc">${[1, 2, 3, 4, 5].map(k => `<i style="background:var(--seq-${k})"></i>`).join("")}</div><div class="esc-t"><span>${fmtV(o[0], d.modo, st.lente)}</span><span>${fmtV(ult(o), d.modo, st.lente)}</span></div><span class="ex">${d.met.cero ? "Sin color: cero" : "Gris plano: sin dato publicable"}</span>${chip(d.met.fuente || "orlando_barrios", d.met.campo, d.met.fuente === "orlando_negocios" ? VIG_NEG : String(d.a))}`;
  };
  const geoBarrios = d => ({type: "FeatureCollection", features: M.geo.barrios.features.map((f, i) => {
    const v = d.vals[i], k = binDe(v, d.cortes);
    return {...f, properties: {i, nombre: B[i].nombre, color: colorBin(k), h: v == null ? 0 : 30 + (v - d.min) / (d.max - d.min || 1) * 1200}};
  })});
  function pintar() {
    const d = datos(); leyenda(d);
    if (svgFallback) return svgFallback.pintar();
    if (!listo) return;
    map.getSource("barrios").setData(geoBarrios(d));
    map.setPaintProperty("fondo", "background-color", css("--surface"));
    map.setPaintProperty("lagos", "fill-color", css("--water"));
    map.setPaintProperty("distritos", "line-color", css("--ink"));
    map.setPaintProperty("limite", "line-color", css("--ink"));
    map.setPaintProperty("sel", "line-color", css("--sun"));
    map.setPaintProperty("barrios-3d", "fill-extrusion-color", ["case", ["boolean", ["feature-state", "hover"], false], css("--sun"), ["get", "color"]]);
  }
  // Encuadre de un barrio: su caja con margen, sin acercarse tanto que las columnas tapen la vista
  const CAJAS = M.geo.barrios.features.map(f => { let x0 = 180, y0 = 90, x1 = -180, y1 = -90; JSON.stringify(f.geometry.coordinates).replace(/\[(-?[\d.]+),(-?[\d.]+)\]/g, (_, x, y) => { x = +x; y = +y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; return ""; }); return [x0, y0, x1, y1]; });
  const PAD = () => el.clientWidth < 560 ? {top: 64, bottom: 64, left: 6, right: 54} : {top: 70, bottom: 50, left: 40, right: 80};
  function enfocar(i, animar = true) { if (!map) return; const angosto = el.clientWidth < 560; map.fitBounds(CAJAS[i], {padding: {top: angosto ? 90 : 140, bottom: $(".relato", el) ? Math.min(el.clientHeight * .55, 300) : angosto ? 110 : 140, left: angosto ? 60 : 140, right: angosto ? 80 : 160}, maxZoom: 11.3, pitch: map.getPitch(), bearing: map.getBearing(), duration: animar && !matchMedia("(prefers-reduced-motion: reduce)").matches ? 1500 : 0}); }
  function seleccionar(i, volar = true) {
    st.sel = i;
    if (svgFallback) { if (cfg.onSelect) cfg.onSelect(i); return; }
    if (listo) map.setFilter("sel", ["==", ["get", "i"], i == null ? -1 : i]);
    if (i != null && volar && map) enfocar(i);
    if (cfg.onSelect) cfg.onSelect(i);
  }
  function verTodo(animar = true) { if (map) map.fitBounds(M.caja, {padding: PAD(), pitch: map.getPitch(), bearing: map.getBearing(), duration: animar ? 1200 : 0}); }
  if (!hay3D()) {
    lienzo.innerHTML = `<svg class="svgmapa" id="${el.id}-svg" role="img" aria-label="Mapa de barrios" style="padding:70px 12px 90px"></svg>`;
    svgFallback = mapaPlano($("svg", lienzo), {valores: i => datos().vals[i], onClick: i => seleccionar(i, false),
      globo: i => { const d = datos(); return `<b>${esc(B[i].nombre)}</b><br>${fmtV(d.vals[i], d.modo, st.lente)} ${d.met.fmt && d.modo === "total" ? "" : esc(d.met.unidad) + sufijo(d.modo)}`; }});
    $(".controles", el).hidden = true;
  } else {
    try {
      map = new maplibregl.Map({container: lienzo, style: {version: 8, sources: {}, layers: [{id: "fondo", type: "background", paint: {"background-color": css("--surface")}}]},
        bounds: M.caja, fitBoundsOptions: {padding: PAD()}, pitch: 52, bearing: -17, maxPitch: 72,
        attributionControl: false, cooperativeGestures: matchMedia("(pointer: coarse)").matches, locale: {"CooperativeGesturesHandler.WindowsHelpText": "Usa Ctrl + rueda para acercar el mapa", "CooperativeGesturesHandler.MacHelpText": "Usa ⌘ + rueda para acercar el mapa", "CooperativeGesturesHandler.MobileHelpText": "Usa dos dedos para mover el mapa"}});
    } catch (e) { map = null; }
    if (!map) { el.innerHTML = `<div class="aviso3d">Tu navegador no pudo abrir el mapa 3D. La misma información está en la tabla de barrios.</div>`; return {pintar() {}, seleccionar() {}, st}; }
    map.on("load", () => {
      const d = datos();
      map.addSource("lagos", {type: "geojson", data: M.geo.lagos});
      map.addSource("barrios", {type: "geojson", data: geoBarrios(d), promoteId: "i"});
      map.addSource("distritos", {type: "geojson", data: M.geo.distritos});
      map.addSource("limite", {type: "geojson", data: M.geo.limite});
      map.addLayer({id: "lagos", type: "fill", source: "lagos", paint: {"fill-color": css("--water")}});
      map.addLayer({id: "barrios-3d", type: "fill-extrusion", source: "barrios", paint: {"fill-extrusion-color": ["get", "color"], "fill-extrusion-height": ["get", "h"], "fill-extrusion-opacity": .93, "fill-extrusion-vertical-gradient": true}});
      map.addLayer({id: "distritos", type: "line", source: "distritos", paint: {"line-color": css("--ink"), "line-width": 1, "line-opacity": .45}});
      map.addLayer({id: "limite", type: "line", source: "limite", paint: {"line-color": css("--ink"), "line-width": 1.4, "line-opacity": .8}});
      map.addLayer({id: "sel", type: "line", source: "barrios", filter: ["==", ["get", "i"], -1], paint: {"line-color": css("--sun"), "line-width": 3.5}});
      for (const dd of M.distritos) { const e = document.createElement("div"); e.className = "et-dist"; e.textContent = "D" + dd.distrito; new maplibregl.Marker({element: e}).setLngLat([dd.lon, dd.lat]).addTo(map); }
      listo = true; pintar();
      if (st.sel != null) map.setFilter("sel", ["==", ["get", "i"], st.sel]);
      if (girando) requestAnimationFrame(girar);
    });
    let girando = !!cfg.girar && !matchMedia("(prefers-reduced-motion: reduce)").matches, visible = true;
    const girar = () => { if (!girando || !listo) return; if (visible && !document.hidden && !map.isMoving()) map.setBearing(map.getBearing() - 0.035); requestAnimationFrame(girar); };
    const parar = () => { girando = false; };
    ["mousedown", "touchstart", "wheel", "dragstart"].forEach(ev => map.on(ev, parar));
    el.addEventListener("pointerdown", parar);
    new IntersectionObserver(es => { visible = es[0].isIntersecting; }).observe(el);
    let hoverId = null;
    map.on("mousemove", "barrios-3d", e => {
      const f = e.features[0]; if (!f) return;
      if (hoverId !== null) map.setFeatureState({source: "barrios", id: hoverId}, {hover: false});
      hoverId = f.id; map.setFeatureState({source: "barrios", id: hoverId}, {hover: true});
      const d = datos(), i = f.properties.i;
      mostrarGlobo(`<b>${esc(B[i].nombre)}</b><br>${fmtV(d.vals[i], d.modo, st.lente)} ${d.met.fmt && d.modo === "total" ? "" : esc(d.met.unidad) + sufijo(d.modo)}<br><span class="s">Distrito ${B[i].distrito}${B[i].pob != null ? ` · ${nf(B[i].pob)} habitantes (estimado)` : ""} · toca para ver su ficha</span>`, e.originalEvent.clientX, e.originalEvent.clientY);
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "barrios-3d", () => { if (hoverId !== null) map.setFeatureState({source: "barrios", id: hoverId}, {hover: false}); hoverId = null; ocultarGlobo(); map.getCanvas().style.cursor = ""; });
    map.on("click", "barrios-3d", e => { const f = e.features[0]; if (f) seleccionar(f.properties.i, false); });
    $(".controles", el).addEventListener("click", e => {
      const b = e.target.closest("button"); if (!b) return;
      if (b.dataset.z === "mas") map.zoomIn(); else if (b.dataset.z === "menos") map.zoomOut();
      else if (b.dataset.z === "todo") verTodo();
      else { const plano = map.getPitch() > 10; map.easeTo({pitch: plano ? 0 : 55, bearing: plano ? 0 : -17, duration: 800}); b.textContent = plano ? "3D" : "2D"; }
    });
    // Si el mapa nació en una vista oculta (0×0), encuadra la ciudad la primera vez que tiene tamaño
    // Un mapa que estuvo oculto (0×0) pierde el encuadre: al volver a tener tamaño, se encuadra de nuevo
    let anchoPrevio = el.clientWidth;
    new ResizeObserver(() => { if (!map) return; map.resize(); const w = el.clientWidth; if (anchoPrevio === 0 && w > 0) st.sel == null ? verTodo(false) : enfocar(st.sel, false); anchoPrevio = w; }).observe(el);
  }
  const lentesEl = $(".lentes", el), selEl = $(".lente-sel", el);
  if (lentesEl) lentesEl.addEventListener("click", e => {
    const b = e.target.closest("button[data-l]"); if (!b) return;
    st.lente = b.dataset.l; $$(".lentes button", el).forEach(x => x.setAttribute("aria-pressed", x === b)); pintar(); if (cfg.onLente) cfg.onLente(st.lente);
  });
  if (selEl) selEl.addEventListener("change", () => { st.lente = selEl.value; pintar(); if (cfg.onLente) cfg.onLente(st.lente); });
  const marcar = k => { $$(".lentes button", el).forEach(x => x.setAttribute("aria-pressed", x.dataset.l === k)); if (selEl && [...selEl.options].some(o => o.value === k)) selEl.value = k; };
  return {st, pintar, seleccionar, verTodo, get map() { return map; }, setLente(k) { st.lente = k; marcar(k); pintar(); }};
}

/* ================= CIFRAS Y FRASES (se escriben solas desde el lago) ================= */
const pobC = C("gente", "poblacion_condado_ultimo_anio"), pobM = C("gente", "poblacion_area_metro_ultimo_anio"), crec = C("gente", "crecimiento_condado_10_anios");
const ing = C("gente", "ingreso_mediano_condado"), ingFl = C("gente", "ingreso_frente_a_florida"), pob = C("gente", "pobreza_condado"), pIng = C("gente", "puesto_ingreso_entre_pares");
$("#notaEscala").innerHTML = `<b>Escala:</b> la ciudad de Orlando tiene ${nf(C("censo", "poblacion_ciudad").valor)} habitantes según el censo (promedio ${VIG_CEN.replace("-", "–")}), pero no una serie anual abierta y sin llave. El condado de Orange la contiene; el área metropolitana suma además los condados de Osceola, Seminole y Lake.`;
const fraseGente = nb(`En el condado de Orange viven ${millones(pobC.valor)} de personas (${pobC.vigencia}), ${nf(crec.valor, 0)} % más que hace diez años. El ingreso mediano de sus hogares es ${usd(ing.valor)} al año, ${ingFl.valor >= 0 ? nf(ingFl.valor, 0) + " % más" : nf(-ingFl.valor, 0) + " % menos"} que el de Florida, y ${nf(pob.valor, 1).replace(",0", "")} de cada 100 personas viven en pobreza.`);

const des = C("economia", "desempleo_ultimo_mes"), desAnt = C("economia", "desempleo_hace_un_anio"), desFl = C("economia", "diferencia_con_florida"), pDes = C("economia", "puesto_desempleo_entre_pares");
const difDes = des.valor - desAnt.valor;
const fraseDes = nb(`El desempleo del área está en ${nf(des.valor, 1)} % (${fMes(des.vigencia)}), ${Math.abs(difDes) < .15 ? "igual que" : difDes > 0 ? nf(difDes, 1) + " puntos más que" : nf(-difDes, 1) + " puntos menos que"} hace un año, y ${Math.abs(desFl.valor) < .15 ? "igual al de Florida" : desFl.valor > 0 ? "por encima del de Florida" : "por debajo del de Florida"}. Entre las cuatro áreas grandes del estado es la ${["", "de menor", "segunda de menor", "tercera de menor", "de mayor"][pDes.valor]} desempleo.`);
const e12 = C("empleo", "variacion_12_meses").valor, eUlt = C("empleo", "indice_ultimo_dia"), pEmp = C("empleo", "puesto_entre_pares");
const fraseEmpleo = nb((Math.abs(e12) < 2 ? "Los avisos de empleo están casi igual que hace un año" : e12 > 0 ? `Hay más avisos de empleo que hace un año (${pct(e12)})` : `Hay menos avisos de empleo que hace un año (${pct(e12)})`)
  + (eUlt.valor >= 97 && eUlt.valor <= 103 ? ", al nivel de antes de la pandemia" : eUlt.valor > 103 ? ", por encima del nivel de antes de la pandemia" : ", por debajo del nivel de antes de la pandemia")
  + (pEmp ? `; pero Tampa, Miami y Jacksonville se recuperaron más: Orlando es ${pEmp.valor === 4 ? "la última" : "la " + ["", "primera", "segunda", "tercera"][pEmp.valor]} de las cuatro.` : "."));
const viv = S("vivienda", "indice_trimestral"), vUlt = C("vivienda", "indice_ultimo_trimestre"), v4 = C("vivienda", "variacion_4_trimestres").valor;
const yoy = viv.map((p, i) => i >= 4 ? [p[0], (p[1] / viv[i - 4][1] - 1) * 100] : null).filter(Boolean);
const maxYoy = yoy.filter(p => +p[0].slice(0, 4) >= +vUlt.vigencia.slice(0, 4) - 6).reduce((a, b) => b[1] > a[1] ? b : a);
const lista = C("vivienda", "precio_mediano_lista_ultimo_mes"), vLista = C("vivienda", "variacion_precio_lista_12_meses").valor;
const fraseViv = nb((Math.abs(v4) < 2 ? `El precio de la vivienda casi no se movió en el último año (${pct(v4)})` : v4 > 0 ? `El precio de la vivienda sigue subiendo: ${pct(v4)} en un año` : `El precio de la vivienda bajó ${pct(-v4)} en un año`)
  + (maxYoy[1] > 8 ? `, después de subir hasta ${nf(maxYoy[1], 0)} % al año en ${maxYoy[0].slice(0, 4)}` : "") + `. Una vivienda en venta pide hoy ${usd(lista.valor)} (mediana, ${fMes(lista.vigencia)}).`);
const fraseEco = `${fraseDes.split(".")[0]}. ${fraseViv}`;

const tot = C("permisos", "permisos_emitidos_ultimo_anio_completo"), vPer = C("permisos", "variacion_ultimo_anio").valor;
const topPerm = S("permisos", "permisos_por_barrio_ultimo_anio").slice(0, 2).map(p => [bonito(p[0]), p[1]]), partTop = (topPerm[0][1] + topPerm[1][1]) / tot.valor * 100;
const frasePer = nb(`En ${tot.vigencia} la ciudad emitió ${nf(tot.valor)} permisos de construcción, ${Math.abs(vPer) < 1 ? "casi los mismos que" : vPer > 0 ? nf(vPer, 0) + " % más que" : nf(-vPer, 0) + " % menos que"} el año anterior. ${topPerm[0][0]} y ${topPerm[1][0]} se llevan ${nf(partTop, 0)} de cada 100.`);

const del = C("seguridad", "delitos_ultimo_anio"), vDel = C("seguridad", "variacion_ultimo_anio").valor;
const topDel = S("seguridad", `delitos_barrio_${U_DEL}`).slice(0, 2).map(p => [bonito(p[0]), p[1]]);
const fraseSeg = nb(`En ${del.vigencia} la policía abrió ${nf(del.valor)} casos de hurtos, violencia y drogas, ${Math.abs(vDel) < 1 ? "casi los mismos que" : vDel > 0 ? nf(vDel, 0) + " % más que" : nf(-vDel, 0) + " % menos que"} el año anterior. ${topDel[0][0]} y ${topDel[1][0]} son los barrios con más casos.`);

const ocio = C("turismo", "participacion_ocio_ultimo_mes"), ocioN = C("turismo", "empleo_ocio_ultimo_mes"), vOcio = C("turismo", "variacion_empleo_ocio_12_meses").valor;
const fraseTur = nb(`${ocio.valor >= 18 && ocio.valor <= 22 ? "Uno de cada cinco" : nf(ocio.valor, 0) + " de cada 100"} empleos del área es de ocio y hotelería: ${nf(ocioN.valor, 0)} mil (${fMes(ocioN.vigencia)}), ${Math.abs(vOcio) < 1 ? "casi los mismos que" : vOcio > 0 ? nf(vOcio, 1) + " % más que" : nf(-vOcio, 1) + " % menos que"} hace un año.`);

const tAct = C("clima", "temperatura_actual"), alertas = C("clima", "alertas_activas").valor;
const difCal = C("clima_historico", "diferencia_entre_periodos"), p1 = C("clima_historico", "promedio_primeros_30"), p2 = C("clima_historico", "promedio_ultimos_30"), caliente = C("clima_historico", "anio_mas_caliente");
const fraseClima = nb(`Al correr la ingesta hacía ${nf(tAct.valor, 0)} °F (${aC(tAct.valor)} °C) y ${alertas ? `había ${alertas} alerta${alertas > 1 ? "s" : ""} vigente${alertas > 1 ? "s" : ""}` : "no había alertas vigentes"}. En el largo plazo, los últimos 30 años fueron ${nf(difCal.valor, 1)} °F (${nf(difCal.valor * 5 / 9, 1)} °C) más calientes que los primeros 30 del registro; el año más caliente fue ${caliente.valor}.`);

/* ================= RESUMEN ================= */
const ver = D.verificacion, verOk = typeof ver === "object";
$("#estadoTxt").innerHTML = `<span class="largo">Datos comprobados el </span>${fDia(D.generado)}`;
$("#estadoLago").addEventListener("click", () => { location.hash = "fuentes"; setTimeout(() => $("#notaVerif").scrollIntoView({behavior: "smooth", block: "center"}), 80); });
const enUso = D.catalogo.filter(f => f.estado === "integrado").length;
$("#lineaInicio").innerHTML = `<span>${ic("ok")}${verOk ? `${ver.pasan} comprobaciones, 0 fallos` : "Sin verificar"}</span><span>${ic("fuente")}${enUso} fuentes en uso de ${D.catalogo.length} revisadas</span><span>${ic("escudo")}Nadie aparece con nombre</span>`;
$("#linkRepo").href = D.repo;

function tarjeta({icono, tema, pregunta, cifra, unidad, vig, tend, frase, graf, vista, fuente}) {
  return `<article class="card resp"><div class="tema"><span class="ic">${ic(icono)}</span>${tema}</div>
    <p class="pregunta">${pregunta}</p>
    <div class="cifra"><b>${cifra}</b><span>${unidad}</span></div>
    <div class="cifra" style="gap:8px">${tend || ""}<span class="vig">${esc(vig)}</span></div>
    <p class="frase">${frase}</p>${graf || ""}
    <div class="pie"><a class="ver" href="#${vista}">Ver la evidencia ${ic("flecha")}</a>${fuente}</div></article>`;
}
const mini = (valores) => { const vals = M.barrios.map((_, i) => valores(i)); const c = cortesQ(vals);
  return `<svg class="minimapa" viewBox="0 0 ${M.ancho} ${M.alto}" aria-hidden="true">${M.barrios.map((b, i) => `<path d="${b.d}" style="fill:${vals[i] == null ? "var(--nodata)" : colorBinVar(binDe(vals[i], c))}"/>`).join("")}<path d="${M.lagos}" style="fill:var(--water);stroke:none"/></svg>`; };
const temps = S("clima_historico", "temperatura_anual");
// Una franja por año calendario: los años sin dato completo quedan en gris rayado, en su lugar (no se juntan los vecinos)
const A0 = +temps[0][0], A1 = +ult(temps)[0], TEMP_ANIO = new Map(temps.map(p => [+p[0], p[1]]));
const ANIOS_T = Array.from({length: A1 - A0 + 1}, (_, k) => A0 + k), FALTAN_T = ANIOS_T.filter(y => !TEMP_ANIO.has(y));
const MEDIA_T = temps.reduce((a, p) => a + p[1], 0) / temps.length, DEV_T = Math.max(...temps.map(p => Math.abs(p[1] - MEDIA_T)));
function franjasSVG(alto = 40) {
  return `<svg viewBox="0 0 ${ANIOS_T.length} 1" preserveAspectRatio="none" style="width:100%;height:${alto}px;display:block;border-radius:8px" aria-hidden="true">${ANIOS_T.map((y, k) => `<rect x="${k}" y="0" width="1.04" height="1" style="fill:${TEMP_ANIO.has(y) ? colorAnomalia((TEMP_ANIO.get(y) - MEDIA_T) / DEV_T) : "var(--nodata)"}"/>`).join("")}</svg>`;
}
function colorAnomalia(t) {   // −1 (frío) … 0 (neutro) … +1 (calor): escala divergente continua azul ↔ rojo
  const a = Math.min(1, Math.abs(t)), [c1, c2, c3] = t < 0 ? ["--cold-1", "--cold-2", "--cold-3"] : ["--warm-1", "--warm-2", "--warm-3"];
  if (a < .34) return `color-mix(in oklab, var(${c1}) ${Math.round(a / .34 * 100)}%, var(--mid))`;
  if (a < .67) return `color-mix(in oklab, var(${c2}) ${Math.round((a - .34) / .33 * 100)}%, var(${c1}))`;
  return `color-mix(in oklab, var(${c3}) ${Math.round((a - .67) / .33 * 100)}%, var(${c2}))`;
}
$("#tarjetas").innerHTML = [
  tarjeta({icono: "gente", tema: "Gente", pregunta: "¿Cuánta gente vive aquí?", cifra: millones(pobC.valor).replace(NB + "millones", ""), unidad: "millones de personas en el condado de Orange", vig: `${pobC.vigencia}`,
    tend: tendencia(crec.valor, 1, "neutro").replace("Sube", "Creció").replace("</span>", " en 10 años</span>"), frase: `Ingreso mediano por hogar: ${usd(ing.valor)} (${ing.vigencia}), ${pct(ingFl.valor, 0)} frente a Florida.`,
    graf: spark(S("gente", "poblacion_condado").slice(-30)), vista: "gente", fuente: chip("fred_poblacion", "poblacion_condado_ultimo_anio", pobC.vigencia)}),
  tarjeta({icono: "empleo", tema: "Economía y vivienda", pregunta: "¿Cómo va el empleo y cuánto cuesta vivir aquí?", cifra: nf(des.valor, 1) + NB + "%", unidad: "de desempleo en el área", vig: fMes(des.vigencia),
    tend: tendencia(difDes, .15, "inverso", v => pp(v)), frase: `Una vivienda en venta pide ${usd(lista.valor)} (mediana, ${fMes(lista.vigencia)}), ${pct(vLista)} en un año.`,
    graf: spark(S("economia", "desempleo_orlando").slice(-60)), vista: "economia", fuente: chip("fred_laus", "desempleo_ultimo_mes", des.vigencia)}),
  tarjeta({icono: "grua", tema: "Barrios", pregunta: "¿Dónde se construye?", cifra: nf(tot.valor), unidad: `permisos emitidos en ${tot.vigencia}`, vig: tot.vigencia,
    tend: tendencia(vPer, 1, "neutro"), frase: `${topPerm[0][0]} y ${topPerm[1][0]} se llevan ${nf(partTop, 0)} de cada 100.`,
    graf: mini(i => B[i].permisos[U_PERM] ?? null), vista: "barrios", fuente: chip("orlando_permisos", "permisos_emitidos_ultimo_anio_completo", tot.vigencia)}),
  tarjeta({icono: "sirena", tema: "Seguridad", pregunta: "¿Qué pasa con la seguridad?", cifra: nf(del.valor), unidad: `casos de hurtos, violencia y drogas en ${del.vigencia}`, vig: del.vigencia,
    tend: tendencia(vDel, 1, "inverso"), frase: `Los barrios con más casos: ${topDel[0][0]} y ${topDel[1][0]}. Nadie aparece con nombre ni dirección.`,
    graf: mini(i => porKm2(B[i].delitos[U_DEL], B[i])), vista: "seguridad", fuente: chip("opd_casos", "delitos_ultimo_anio", del.vigencia)}),
  tarjeta({icono: "maleta", tema: "Turismo", pregunta: "¿Cuánto pesa el turismo?", cifra: nf(ocio.valor, 1) + NB + "%", unidad: "del empleo es de ocio y hotelería", vig: fMes(ocio.vigencia),
    tend: tendencia(vOcio, 1, "normal"), frase: `${nf(ocioN.valor, 0)} mil empleos. ${nf(C("negocios", "hospedajes_vigentes").valor)} hospedajes y ${nf(C("negocios", "restaurantes_vigentes").valor)} restaurantes con licencia en la ciudad.`,
    graf: spark(S("turismo", "empleo_ocio_hoteleria").slice(-84)), vista: "turismo", fuente: chip("fred_ces", "participacion_ocio_ultimo_mes", ocio.vigencia)}),
  tarjeta({icono: "sol", tema: "Clima", pregunta: "¿Cómo está cambiando el clima?", cifra: "+" + nf(difCal.valor, 1) + NB + "°F", unidad: "más calientes los últimos 30 años que los primeros 30", vig: `${p1.vigencia.replace("-", "–")} → ${p2.vigencia.replace("-", "–")}`,
    tend: "", frase: `Hoy: ${nf(tAct.valor, 0)} °F (${aC(tAct.valor)} °C), ${alertas ? alertas + " alertas" : "sin alertas"}. El año más caliente del registro fue ${caliente.valor}.`,
    graf: franjasSVG(44), vista: "clima", fuente: chip("noaa_gsoy", "diferencia_entre_periodos", p2.vigencia)}),
].join("");

// Contra qué: Orlando frente a sus pares en cuatro medidas
function contraCard(titulo, filas, fmt, fuente, campo, vig, nota) {
  const id = "c" + Math.random().toString(36).slice(2, 8);
  setTimeout(() => listaBarras($("#" + id), filas, {fmt, pos: false}));
  return `<div class="card"><h3>${titulo}</h3><ol class="ranking sinpos" id="${id}"></ol><p class="vig">${esc(nota)}</p>${chip(fuente, campo, vig)}</div>`;
}
const desU = des.vigencia;
const val = (tema, k, et) => (S(tema, k).find(p => p[0] === et) || ult(S(tema, k)))[1];
const empMes = S("empleo", "indice_mensual"), empU = ult(empMes)[0];
const visDoce = k => S("escucha", k).slice(-12).reduce((a, p) => a + p[1], 0);
$("#contra").innerHTML = [
  contraCard("Desempleo (menos es mejor)", [["Orlando", "orlando", true], ["Tampa", "tampa"], ["Miami", "miami"], ["Jacksonville", "jacksonville"], ["Florida", "florida"]]
    .map(([n, k, yo]) => ({nombre: n, valor: val("economia", `desempleo_${k}`, desU), yo, par: !yo})).sort((a, b) => a.valor - b.valor), v => nf(v, 1) + NB + "%", "fred_laus", "desempleo_<área>", desU, `Áreas metropolitanas, ${fMes(desU)}`),
  contraCard("Avisos de empleo (feb 2020 = 100)", [["Orlando", "indice_mensual", true], ["Tampa", "indice_mensual_tampa"], ["Miami", "indice_mensual_miami"], ["Jacksonville", "indice_mensual_jacksonville"]]
    .map(([n, k, yo]) => ({nombre: n, valor: val("empleo", k, empU), yo, par: !yo})).sort((a, b) => b.valor - a.valor), v => nf(v, 1), "indeed_hiring_lab", "indice_mensual_<ciudad>", empU, `Índice, 100 = feb 2020 · ${fMes(empU)}`),
  contraCard("Ingreso mediano de los hogares", [["Orange", "orange", true], ["Hillsborough", "hillsborough"], ["Duval", "duval"], ["Miami-Dade", "miami_dade"], ["Florida", "florida"]]
    .map(([n, k, yo]) => ({nombre: n, valor: ult(S("gente", `ingreso_mediano_${k}`))[1], yo, par: !yo})).sort((a, b) => b.valor - a.valor), usd, "fred_saipe", "ingreso_mediano_<condado>", ing.vigencia, `Condados, ${ing.vigencia}. Orange es el de Orlando; Hillsborough, el de Tampa; Duval, el de Jacksonville`),
  contraCard("Interés en Wikipedia en español", [["Orlando", "vistas_mensuales", true], ["Tampa", "vistas_mensuales_tampa"], ["Miami", "vistas_mensuales_miami"], ["Jacksonville", "vistas_mensuales_jacksonville"]]
    .map(([n, k, yo]) => ({nombre: n, valor: visDoce(k), yo, par: !yo})).sort((a, b) => b.valor - a.valor), v => nf(v), "wikimedia_pageviews", "vistas_mensuales_<ciudad>", C("escucha", "vistas_ultimo_mes").vigencia, "Visitas en los últimos 12 meses"),
  contraCard("Salario por hora, sector privado", [["Orlando", "orlando", true], ["Tampa", "tampa"], ["Miami", "miami"], ["Jacksonville", "jacksonville"]]
    .map(([n, k, yo]) => ({nombre: n, valor: ult(S("economia", `salario_hora_${k}`))[1], yo, par: !yo})).sort((a, b) => b.valor - a.valor), v => "US$" + NB + nf(v, 2), "fred_salarios", "salario_hora_<área>", C("economia", "salario_hora_ultimo_mes").vigencia, `Áreas metropolitanas, ${fMes(C("economia", "salario_hora_ultimo_mes").vigencia)}`),
  contraCard("Arriendo típico al mes (menos es mejor)", [["Orlando", "orlando", true], ["Tampa", "tampa"], ["Miami", "miami"], ["Jacksonville", "jacksonville"], ["EE. UU.", "eeuu"]]
    .map(([n, k, yo]) => ({nombre: n, valor: ult(S("vivienda", `arriendo_tipico_${k}`))[1], yo, par: !yo})).sort((a, b) => a.valor - b.valor), usd, "zillow_research", "arriendo_tipico_<área>", C("vivienda", "arriendo_tipico_ultimo_mes").vigencia, `Zillow, áreas metropolitanas, ${fMes(C("vivienda", "arriendo_tipico_ultimo_mes").vigencia)}`),
].join("");

const PENDIENTES = [
  {t: "¿Qué reclaman los vecinos al 311?", p: "Las solicitudes al 311 no están publicadas. Las quejas de código urbano son lo más cercano, pero solo cubren el estado de los predios."},
  {t: "¿Qué predios están en zona de inundación?", p: "El servidor de mapas de inundación de FEMA (F61) no respondió. Usamos el Índice Nacional de Riesgo de FEMA por sector censal, que mide riesgo pero no traza la zona inundable de cada predio."},
  {t: "¿Dónde hay supermercados y farmacias?", p: "OpenStreetMap (F74) rechazó las consultas automáticas del navegador que usamos. No lo saltamos con espejos: queda como pendiente para saber qué barrios no tienen comercio básico cerca."},
  {t: "¿Cuánto produce la economía del área?", p: "El PIB del área está descontinuado en FRED. No lo reemplazamos por un número viejo."},
  {t: "¿Qué cargos se buscan y cuánto pagan?", p: "Las ofertas de Indeed (F19) prohíben la extracción. El índice que usamos dice si los avisos suben o bajan, no cuáles son."},
  {t: "¿Cuántos turistas llegan?", p: "Visitantes y pasajeros del aeropuerto vienen en PDF y notas de prensa (F23, F51); la ocupación hotelera es de plataformas privadas."},
];
$("#pendientes").innerHTML = PENDIENTES.map(x => `<div class="pend">${ic("hueco")}<b>${esc(x.t)}</b><p>${esc(x.p)}</p></div>`).join("");
$("#copiarResumen").addEventListener("click", () => copiar([
  `Cerebro Orlando · resumen con datos comprobados el ${fDia(D.generado)}`,
  `1. Gente: ${fraseGente} Fuente: U.S. Census Bureau vía FRED.`,
  `2. Economía y vivienda: ${fraseDes} ${fraseViv} Fuentes: BLS, FHFA y Realtor.com vía FRED.`,
  `3. Barrios: ${frasePer} Fuente: City of Orlando Open Data.`,
  `4. Seguridad: ${fraseSeg} Fuente: Policía de Orlando (agregado por barrio).`,
  `5. Turismo: ${fraseTur} Fuente: BLS vía FRED.`,
  `6. Clima: ${fraseClima} Fuentes: NWS y NOAA NCEI.`,
  `7. Quién vive: ${$("#r-quien").textContent} Fuente: Census ACS 5 años, estimado por barrio.`,
  `8. Decidir: ${fraseDecidir()}`].join("\n"), "Resumen copiado"));

// Mapa 3D de la portada, con recorrido guiado
const atlasInicio = crearAtlas($("#atlasInicio"), {lentes: ["poblacion", "permisos", "delitos", "quejas", "negocios", "crec45"], estado: {lente: "poblacion"}, girar: true,
  onSelect: i => { if (i != null && !recorridoActivo) { irABarrio(i); } }});
let recorridoActivo = false;
function paradas() {
  const mejor = (f, filtro = () => true) => B.map((b, i) => [i, f(b)]).filter(([i, v]) => v != null && filtro(B[i])).sort((a, b) => b[1] - a[1])[0][0];
  const p1 = mejor(b => b.permisos[U_PERM]);
  const a0 = A_PERM[0], baja = B.map((b, i) => [i, (b.permisos[a0] ?? 0) - (b.permisos[U_PERM] ?? 0)]).sort((a, b) => b[1] - a[1])[0][0];
  const p3 = mejor(b => porKm2(b.delitos[U_DEL], b), b => b.km2 > .3);
  const p4 = mejor(b => b.quejas);
  const p5 = mejor(b => b.negocios);
  const p6 = mejor(b => b.crec45, b => (b.pob17 || 0) >= 1000);
  const r = (i, lente, titulo, texto) => ({i, lente, titulo, texto});
  return [
    r(p1, "permisos", `Donde más se construye: ${B[p1].nombre}`, `${nf(B[p1].permisos[U_PERM])} permisos emitidos en ${U_PERM}, el primer puesto de la ciudad. Está en el distrito ${B[p1].distrito}, en el sureste, donde Orlando crece hacia el aeropuerto y Lake Nona.`),
    r(baja, "permisos", `Donde la construcción se frenó: ${B[baja].nombre}`, `Pasó de ${nf(B[baja].permisos[a0] ?? 0)} permisos en ${a0} a ${nf(B[baja].permisos[U_PERM] ?? 0)} en ${U_PERM}. Fue el barrio que más construyó al comienzo del periodo.`),
    r(p3, "delitos", `Más casos de policía por km²: ${B[p3].nombre}`, `${nf(porKm2(B[p3].delitos[U_DEL], B[p3]), 0)} casos por km² en ${U_DEL} (${nf(B[p3].delitos[U_DEL])} en total). ${porHab(B[p3].delitos[U_DEL], B[p3]) != null ? `Por habitante serían ${nf(porHab(B[p3].delitos[U_DEL], B[p3]), 0)} por cada 1.000 vecinos estimados, pero mucha de esa actividad la genera gente de paso: quien trabaja, compra o sale de noche allí.` : "Vive poca gente: casi toda esa actividad es de gente de paso."}`),
    r(p4, "quejas", `Más quejas ciudadanas: ${B[p4].nombre}`, `${nf(B[p4].quejas)} casos de código abiertos por queja de vecinos en ${U_COD}: lotes, viviendas y avisos. Lo más cercano a «qué reclaman los vecinos» que hay abierto.`),
    r(p5, "negocios", `Más negocios: ${B[p5].nombre}`, `${nf(B[p5].negocios)} licencias de negocio vigentes. El centro concentra oficinas, comercio y servicios, y por eso aparece alto en casi todas las medidas.`),
    r(p6, "crec45", `Donde más va a crecer: ${B[p6].nombre}`, `La proyección de la ciudad lo lleva de ${nf(B[p6].pob17)} residentes en 2017 a ${nf(B[p6].pob45)} en 2045 (${crecF(B[p6].crec45)}). Ahí se van a necesitar vías, colegios y parques.`),
  ];
}
function recorrido(el, atlas) {
  const pasos = paradas(); let k = 0;
  recorridoActivo = true;
  const caja = document.createElement("div"); caja.className = "relato"; el.append(caja);
  const ir = () => {
    const p = pasos[k];
    atlas.setLente(p.lente); atlas.seleccionar(p.i, true);
    caja.innerHTML = `<p class="eyebrow">Parada ${k + 1} de ${pasos.length}</p><h3>${esc(p.titulo)}</h3><p class="peq">${esc(p.texto)}</p>
      <div class="pasos"><button class="btn" type="button" data-p="ant" ${k ? "" : "disabled"}>${ic("atras")}Anterior</button><button class="btn" type="button" data-p="fin">Terminar</button><button class="btn prim" type="button" data-p="sig">${k < pasos.length - 1 ? "Siguiente" : "Ver la ficha"}${ic("flecha")}</button></div>`;
  };
  caja.addEventListener("click", e => {
    const b = e.target.closest("button[data-p]"); if (!b) return;
    if (b.dataset.p === "ant") { k--; ir(); }
    else if (b.dataset.p === "sig") { if (k < pasos.length - 1) { k++; ir(); } else { const i = pasos[k].i; fin(); irABarrio(i); } }
    else fin();
  });
  const fin = () => { caja.remove(); recorridoActivo = false; atlas.seleccionar(null, false); atlas.verTodo(); };
  ir();
}
$("#recorridoBtn").addEventListener("click", () => { $("#atlasInicio").scrollIntoView({behavior: "smooth", block: "center"}); if (!$(".relato", $("#atlasInicio"))) recorrido($("#atlasInicio"), atlasInicio); });

/* ================= GENTE ================= */
$("#r-gente").textContent = fraseGente;
$("#k-poblacion").innerHTML = `<div class="kpi"><small>Condado de Orange</small><b>${millones(pobC.valor)}</b><span class="vig">${pobC.vigencia}</span></div>
  <div class="kpi"><small>En 10 años</small><b>${pct(crec.valor)}</b><span class="vig">${+pobC.vigencia - 10}–${pobC.vigencia}</span></div>
  <div class="kpi"><small>Área metropolitana</small><b>${millones(pobM.valor)}</b><span class="vig">${pobM.vigencia}</span></div>`;
$("#f-poblacion").innerHTML = chip("fred_poblacion", "poblacion_condado", pobC.vigencia);
$("#ley-poblacion").innerHTML = `<span><i style="background:var(--accent)"></i>Condado de Orange</span><span><i style="background:var(--peer)"></i>Área metropolitana</span>`;
observar($("#g-poblacion"), () => lineas($("#g-poblacion"), {series: [
  {nombre: "Condado", puntos: S("gente", "poblacion_condado").map(p => [p[0], p[1] / 1000]), color: "var(--accent)", resaltar: true},
  {nombre: "Área metro", puntos: S("gente", "poblacion_area_metro").map(p => [p[0], p[1] / 1000]), color: "var(--peer)"}],
  fmtX: s => s, fmtY: v => nf(v, 2) + " millones", fmtTick: (v, d) => nf(v, d), cero: true, etiquetas: true, area: true, aria: "Población del condado de Orange y del área metropolitana"}));
const PARES_C = [["orange", "Orange (Orlando)", true], ["hillsborough", "Hillsborough (Tampa)"], ["duval", "Duval (Jacksonville)"], ["miami_dade", "Miami-Dade"], ["florida", "Florida"]];
const COL_PAR = {hillsborough: "var(--c1)", duval: "var(--c3)", miami_dade: "var(--c2)", florida: "var(--peer)"};
function seriesPares(pref, desde) {
  return PARES_C.map(([k, n, yo]) => ({nombre: n.split(" (")[0], puntos: S("gente", `${pref}_${k}`).filter(p => !desde || p[0] >= desde), color: yo ? "var(--ink)" : COL_PAR[k], resaltar: yo}));
}
const ingU = Object.fromEntries(PARES_C.map(([k]) => [k, ult(S("gente", `ingreso_mediano_${k}`))[1]]));
$("#r-ingreso").textContent = `Orange es el ${["", "primero", "segundo", "tercero", "cuarto"][pIng.valor]} de los cuatro condados por ingreso (${ing.vigencia}). En dólares corrientes: no descuenta la inflación.`;
$("#f-ingreso").innerHTML = chip("fred_saipe", "ingreso_mediano_<condado>", ing.vigencia);
observar($("#g-ingreso"), () => lineas($("#g-ingreso"), {series: seriesPares("ingreso_mediano", "2005"), fmtX: s => s, fmtY: v => usd(v), fmtTick: v => nf(v / 1000) + " mil", etiquetas: true, aria: "Ingreso mediano por condado"}));
const pobU = Object.fromEntries(PARES_C.map(([k]) => [k, ult(S("gente", `pobreza_${k}`))[1]]));
$("#r-pobreza").textContent = `En ${pob.vigencia}, ${nf(pobU.orange, 1)} % en Orange, frente a ${nf(pobU.florida, 1)} % en Florida y ${nf(pobU.miami_dade, 1)} % en Miami-Dade.`;
$("#f-pobreza").innerHTML = chip("fred_saipe", "pobreza_condado", pob.vigencia);
observar($("#g-pobreza"), () => lineas($("#g-pobreza"), {series: seriesPares("pobreza", "2005"), fmtX: s => s, fmtY: v => nf(v, 1) + " %", fmtTick: (v, d) => nf(v, d) + NB + "%", etiquetas: true, aria: "Pobreza por condado"}));

// ---------- v3: ingreso por persona, crecimiento comparado e ingreso real ----------
const PCPI = [["orange", "Orange", "var(--ink)", true], ["hillsborough", "Hillsborough", "var(--c1)"], ["miami_dade", "Miami-Dade", "var(--c2)"], ["duval", "Duval", "var(--c3)"], ["florida", "Florida", "var(--peer)"]];
const ppc = C("gente", "ingreso_por_persona_condado"), pPpc = C("gente", "puesto_ingreso_por_persona").valor;
$("#r-pcpi").textContent = `Todo el ingreso del condado (salarios, negocios, rentas, ayudas) dividido por su gente: ${usd(ppc.valor)} por persona en ${ppc.vigencia}, ${["", "el más alto", "el segundo", "el tercero", "el más bajo"][pPpc]} de los cuatro condados. Miami-Dade va muy arriba; Orange y Duval casi empatan.`;
$("#f-pcpi").innerHTML = chip("fred_bea", "ingreso_por_persona_<condado>", ppc.vigencia);
observar($("#g-pcpi"), () => lineas($("#g-pcpi"), {series: PCPI.map(([k, n, c, yo]) => ({nombre: n, puntos: S("gente", `ingreso_por_persona_${k}`).filter(p => p[0] >= "2005"), color: c, resaltar: yo})),
  fmtX: s => s, fmtY: v => usd(v), fmtTick: v => nf(v / 1000) + NB + "mil", etiquetas: true, aria: "Ingreso por persona por condado"}));
const NOMC = {orange: "Orange (Orlando)", hillsborough: "Hillsborough (Tampa)", duval: "Duval (Jacksonville)", miami_dade: "Miami-Dade", florida: "Florida"};
const crecP = S("gente", "crecimiento_10_anios_condados"), pCrec = C("gente", "puesto_crecimiento_entre_pares").valor;
$("#r-crec").textContent = `Orange ganó ${nf(crecP.find(p => p[0] === "orange")[1], 1)} % de población en diez años (${+pobC.vigencia - 10}–${pobC.vigencia}): ${pCrec === 1 ? "el que más creció" : "puesto " + pCrec} de los cuatro condados. Crecer rápido presiona la vivienda, las vías y los servicios.`;
listaBarras($("#rankCrec"), crecP.map(([k, v]) => ({nombre: NOMC[k], valor: v, yo: k === "orange", par: k !== "orange"})).sort((a, b) => b.valor - a.valor), {fmt: v => pct(v, 1), pos: false});
$("#f-crec").innerHTML = chip("fred_poblacion", "crecimiento_10_anios_condados", pobC.vigencia);
const realI = L.gente.cifras.ingreso_real_10_anios;
if (realI) $("#k-real").innerHTML = `<div class="kpi"><small>Ingreso de los hogares de Orange en 10 años, descontada la inflación</small><div class="fila"><b>${pct(realI.valor, 0)}</b>${tendencia(realI.valor, 1, "normal")}</div><span class="vig">${realI.vigencia.replace("-", "–")} · inflación de la región Sur (BLS)</span>${chip("fred_ipc", "ingreso_real_10_anios", realI.vigencia)}</div>`;

// ---------- v3: ciudad contra ciudad (censo, mismas preguntas para las cuatro ciudades) ----------
const CIUD = {orlando: "Orlando", tampa: "Tampa", miami: "Miami", jacksonville: "Jacksonville", florida: "Florida", eeuu: "EE. UU."};
const ACS_C = [["ingreso_mediano", "Ingreso mediano de los hogares", usdF, 1], ["pct_pobreza", "Personas en pobreza", pctF, -1], ["arriendo_mediano", "Arriendo mediano al mes", usdF, -1],
  ["pct_carga_arriendo", "Arrendatarios que gastan 30 % o más del ingreso en arriendo", pctF, -1], ["pct_arrendatarios", "Hogares que arriendan", pctF, 0], ["pct_sin_carro", "Hogares sin carro", pctF, 0],
  ["minutos_al_trabajo", "Minutos de viaje al trabajo", v => nf(v, 1) + NB + "min", -1], ["pct_universitarios", "Mayores de 25 con título universitario", pctF, 1],
  ["pct_espanol", "Hablan español en casa", pctF, 0], ["edad_mediana", "Edad mediana", v => nf(v, 1) + NB + "años", 0]];
const acsC = k => Object.fromEntries(S("censo", `${k}_ciudades`));
const puestoCiudad = (k, dir) => { const v = acsC(k), cs = ["orlando", "tampa", "miami", "jacksonville"].filter(c => v[c] != null); return [...cs].sort((a, b) => dir >= 0 ? v[b] - v[a] : v[a] - v[b]).indexOf("orlando") + 1; };
const ARR_C = acsC("arriendo_mediano"), CARGA_C = acsC("pct_carga_arriendo");
$("#r-ciudades").textContent = nb(`Las mismas preguntas del censo para las ciudades (no sus áreas metropolitanas), promedio ${VIG_CEN.replace("-", "–")}. Orlando paga ${usd(ARR_C.orlando)} de arriendo mediano, ${puestoCiudad("arriendo_mediano", 1) === 1 ? "el más alto" : puestoCiudad("arriendo_mediano", 1) === 2 ? "el segundo más alto" : "puesto " + puestoCiudad("arriendo_mediano", 1)} de las cuatro ciudades, y ${nf(CARGA_C.orlando, 0)} de cada 100 hogares que arriendan gastan 30 % o más de su ingreso en arriendo (en EE. UU., ${nf(CARGA_C.eeuu, 0)}).`);
$("#f-ciudades").innerHTML = chip("censo_acs", "<medida>_ciudades", VIG_CEN);
$("#ciudadesACS").innerHTML = ACS_C.map(([k, t, f, dir], j) => `<div class="card"><h3>${esc(t)}</h3><span class="vig">${dir > 0 ? "Más es mejor" : dir < 0 ? "Menos es mejor" : "Ni mejor ni peor: describe la ciudad"}</span><ol class="ranking sinpos" id="ac${j}"></ol></div>`).join("");
ACS_C.forEach(([k, t, f, dir], j) => listaBarras($("#ac" + j), S("censo", `${k}_ciudades`).map(([c, v]) => ({nombre: CIUD[c], valor: v, yo: c === "orlando", par: c !== "orlando"})).sort((a, b) => b.valor - a.valor), {fmt: f, pos: false}));

// ---------- v3: quién vive en cada barrio ----------
const QUIEN = [["poblacion", "Densidad"], ["ingreso", "Ingreso"], ["arriendo", "Arriendo"], ["carga", "Carga de arriendo"], ["espanol", "Español"], ["sinCarro", "Sin carro"], ["univ", "Universitarios"], ["edad", "Edad"]];
let quien = "poblacion";
const modoQuien = () => quien === "poblacion" ? "km2" : "total";
$("#segGente").innerHTML = QUIEN.map(([k, n]) => `<button type="button" data-k="${k}" aria-pressed="${k === quien}">${n}</button>`).join("");
const mapaGente = mapaPlano($("#mapaGente"), {valores: i => valorDe(quien, B[i], undefined, modoQuien()), ley: $("#leyGente"), fmt: v => quien === "poblacion" ? nf(v) : fmtV(v, "total", quien),
  titulo: () => quien === "poblacion" ? "Habitantes por km² (estimado)" : METRICAS[quien].nombre, onClick: i => irABarrio(i),
  globo: i => { const v = valorDe(quien, B[i], undefined, modoQuien()); return `<b>${esc(B[i].nombre)}</b><br>${v == null ? "Sin estimación (menos de " + MIN_HAB + " habitantes)" : quien === "poblacion" ? nf(v) + " habitantes por km²" : esc(METRICAS[quien].corto) + ": " + fmtV(v, "total", quien)}<br><span class="s">${B[i].pob != null ? nf(B[i].pob) + " habitantes (estimado) · " : ""}toca para ver su ficha</span>`; }});
function pintarQuien() {
  mapaGente.pintar();
  const filas = B.map((b, i) => ({nombre: b.nombre, valor: valorDe(quien, b, undefined, modoQuien()), i})).filter(f => f.valor != null).sort((a, b) => b.valor - a.valor);
  listaBarras($("#rankGente"), filas.slice(0, 10), {fmt: v => quien === "poblacion" ? nf(v) : fmtV(v, "total", quien), onClick: f => irABarrio(f.i)});
  const med = mediana(filas.map(f => f.valor));
  $("#r-quien").textContent = nb(`${quien === "poblacion" ? "Habitantes por km²" : METRICAS[quien].nombre}: los más altos son ${filas.slice(0, 3).map(f => f.nombre).join(", ")}; la mediana de los barrios es ${quien === "poblacion" ? nf(med) : fmtV(med, "total", quien)}.`);
}
$("#segGente").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; quien = b.dataset.k; $$("#segGente button").forEach(x => x.setAttribute("aria-pressed", x === b)); pintarQuien(); });
pintarQuien();
$("#notaGente").innerHTML = nb(`<b>Cómo se estima.</b> El censo publica estas cifras por sector censal, no por barrio. Cubrimos la ciudad con una rejilla de puntos cada 150 m (sin lagos) y repartimos cada sector entre los barrios según qué parte de su tierra cae en cada uno. Las medianas se promedian ponderando por hogares: por eso se llaman «aproximadas». La suma de los barrios da ${nf(C("censo", "poblacion_estimada_en_barrios").valor)} habitantes, ${pct(C("censo", "diferencia_con_cifra_oficial").valor)} frente a la cifra oficial de la ciudad. Los ${B.filter(b => b.pob != null && b.pob < MIN_HAB).length} barrios con menos de ${MIN_HAB} habitantes estimados no tienen porcentajes ni medianas.`) + " " + chip("censo_acs", "poblacion_barrio", VIG_CEN) + " " + chip("censo_tiger", "", L.censo.probado, "Contornos");

/* ================= ECONOMÍA Y VIVIENDA ================= */
$("#r-eco").textContent = fraseEco;
$("#r-desempleo").textContent = fraseDes;
$("#k-desempleo").innerHTML = `<div class="kpi"><small>Orlando</small><b>${nf(des.valor, 1)} %</b><span class="vig">${fMes(des.vigencia)}</span></div><div class="kpi"><small>Frente a un año antes</small><b>${pp(difDes)}</b><span class="vig">${fMes(desAnt.vigencia)}: ${nf(desAnt.valor, 1)} %</span></div>`;
$("#f-desempleo").innerHTML = chip("fred_laus", "desempleo_<área>", des.vigencia);
const DES = [["orlando", "Orlando", "var(--ink)", true], ["tampa", "Tampa", "var(--c1)"], ["miami", "Miami", "var(--c2)"], ["jacksonville", "Jacksonville", "var(--c3)"], ["florida", "Florida", "var(--peer)"], ["eeuu", "EE. UU.", "var(--muted)"]];
let rDes = 10, ocultosDes = new Set(["eeuu"]);
const leyToggle = (el, items, ocultos, cb) => { el.innerHTML = items.map(([k, n, c]) => `<button type="button" data-k="${k}" aria-pressed="${!ocultos.has(k)}"><i style="background:${c}"></i>${n}</button>`).join(""); el.onclick = e => { const b = e.target.closest("button"); if (!b) return; ocultos.has(b.dataset.k) ? ocultos.delete(b.dataset.k) : ocultos.add(b.dataset.k); b.setAttribute("aria-pressed", !ocultos.has(b.dataset.k)); cb(); }; };
const dibDes = () => { const desde = rDes ? `${+des.vigencia.slice(0, 4) - rDes}${des.vigencia.slice(4)}` : "";
  lineas($("#g-desempleo"), {series: DES.filter(([k]) => !ocultosDes.has(k) || k === "orlando").map(([k, n, c, yo]) => ({nombre: n, puntos: S("economia", `desempleo_${k}`).filter(p => p[0] >= desde), color: c, resaltar: yo})),
    fmtX: s => fMes(s, true), fmtY: v => nf(v, 1) + " %", fmtTick: (v, d) => nf(v, d) + NB + "%", etiquetas: true, cero: true, aria: "Desempleo de Orlando y de sus pares"}); };
leyToggle($("#ley-desempleo"), DES.slice(1), ocultosDes, dibDes);
observar($("#g-desempleo"), dibDes);
$("#r-empleo").textContent = fraseEmpleo;
$("#k-empleo").innerHTML = `<div class="kpi"><small>Índice al ${fDia(eUlt.vigencia)}</small><b>${nf(eUlt.valor, 1)}</b></div><div class="kpi"><small>En 12 meses</small><b>${pct(e12)}</b></div>`;
$("#f-empleo").innerHTML = chip("indeed_hiring_lab", "indice_mensual_<ciudad>", eUlt.vigencia);
const EMP = [["", "Orlando", "var(--ink)", true], ["_tampa", "Tampa", "var(--c1)"], ["_miami", "Miami", "var(--c2)"], ["_jacksonville", "Jacksonville", "var(--c3)"]];
const ocultosEmp = new Set();
const dibEmp = () => lineas($("#g-empleo"), {series: EMP.filter(([k]) => !ocultosEmp.has(k) || !k).map(([k, n, c, yo]) => ({nombre: n, puntos: S("empleo", `indice_mensual${k}`), color: c, resaltar: yo})),
  fmtX: s => fMes(s, true), fmtY: v => nf(v, 1), ref: {y: 100}, etiquetas: true, aria: "Índice de avisos de empleo de Orlando y sus pares"});
leyToggle($("#ley-empleo"), EMP.slice(1), ocultosEmp, dibEmp);
observar($("#g-empleo"), dibEmp);
const hace5 = viv[viv.length - 21];
$("#r-vivienda").textContent = fraseViv;
$("#k-vivienda").innerHTML = `<div class="kpi"><small>En un año</small><b>${pct(v4)}</b><span class="vig">${fTrim(vUlt.vigencia)}</span></div><div class="kpi"><small>En 5 años</small><b>${pct((vUlt.valor / hace5[1] - 1) * 100, 0)}</b><span class="vig">desde ${fTrim(hace5[0])}</span></div><div class="kpi"><small>Desde 1995</small><b>× ${nf(vUlt.valor / 100, 1)}</b><span class="vig">sin descontar inflación</span></div>`;
$("#f-vivienda").innerHTML = chip("fred_ihv_orlando", "indice_trimestral", vUlt.vigencia);
let modoViv = "pares";
const rebase = (pts, base) => { const b = pts.find(p => p[0] === base); return b ? pts.filter(p => p[0] >= base).map(p => [p[0], p[1] / b[1] * 100]) : []; };
const VIVP = [["", "Orlando", "var(--ink)", true], ["_tampa", "Tampa", "var(--c1)"], ["_miami", "Miami", "var(--c2)"], ["_jacksonville", "Jacksonville", "var(--c3)"]];
const picoViv = viv.filter(p => p[0] < "2010").reduce((a, b) => b[1] > a[1] ? b : a), fondoViv = viv.filter(p => p[0] > picoViv[0] && p[0] < "2016").reduce((a, b) => b[1] < a[1] ? b : a);
const dibViv = () => {
  if (modoViv === "pares") {
    $("#t-vivienda").innerHTML = `Precio de la vivienda, re-escalado a 2015 = 100 (<button class="term" data-term="indice1995">derivado</button>)`;
    $("#ley-vivienda").innerHTML = `<span>La serie de Tampa termina en ${fTrim(ult(S("vivienda", "indice_trimestral_tampa"))[0])}</span>`;
    lineas($("#g-vivienda"), {series: VIVP.map(([k, n, c, yo]) => ({nombre: n, puntos: rebase(S("vivienda", `indice_trimestral${k}`), "2015-Q1"), color: c, resaltar: yo})),
      fmtX: fTrim, fmtY: v => nf(v, 0) + " (2015 = 100)", ref: {y: 100, texto: "2015 = 100"}, etiquetas: true, aria: "Precio de la vivienda de Orlando y sus pares desde 2015"});
  } else {
    $("#t-vivienda").innerHTML = `Precio de la vivienda en Orlando, <button class="term" data-term="indice1995">índice 1995 = 100</button>`;
    $("#ley-vivienda").innerHTML = "";
    lineas($("#g-vivienda"), {series: [{nombre: "Orlando", puntos: viv, color: "var(--accent)"}], fmtX: fTrim, fmtY: v => nf(v, 1), ref: {y: 100, texto: "1995 = 100"}, area: true,
      extra: et => { const j = viv.findIndex(x => x[0] === et); return j >= 4 ? `<br><span class="s">${pct((viv[j][1] / viv[j - 4][1] - 1) * 100)} en un año</span>` : ""; },
      notas: [{x: picoViv[0], texto: `Pico de ${picoViv[0].slice(0, 4)}`}, {x: fondoViv[0], texto: `Fondo de ${fondoViv[0].slice(0, 4)}`, pos: "abajo"}], aria: "Precio de la vivienda en Orlando desde 1978"});
  }
};
observar($("#g-vivienda"), dibViv);
const inv = C("vivienda", "casas_en_venta_ultimo_mes"), vInv = C("vivienda", "variacion_casas_en_venta_12_meses").valor, dias = C("vivienda", "dias_en_mercado_ultimo_mes");
$("#r-mercado").textContent = `En ${fMes(lista.vigencia, true)} había ${nf(inv.valor)} viviendas en venta en el área (${pct(vInv)} en un año), con un precio mediano de lista de ${usd(lista.valor)} (${pct(vLista)}). Una vivienda tarda ${nf(dias.valor)} días en venderse (mediana).`;
$("#f-realtor").innerHTML = chip("fred_realtor", "precio_mediano_lista_ultimo_mes", lista.vigencia);
observar($("#g-lista"), () => lineas($("#g-lista"), {series: [{nombre: "Precio", puntos: S("vivienda", "precio_mediano_lista"), color: "var(--accent)"}], alto: 170, fmtX: s => fMes(s, true), fmtY: usd, fmtTick: v => nf(v / 1000) + " mil", area: true, aria: "Precio mediano de lista"}));
observar($("#g-inventario"), () => lineas($("#g-inventario"), {series: [{nombre: "En venta", puntos: S("vivienda", "casas_en_venta"), color: "var(--accent)"}], alto: 170, fmtX: s => fMes(s, true), fmtY: v => nf(v) + " viviendas", fmtTick: v => nf(v / 1000) + " mil", cero: true, area: true, aria: "Viviendas en venta"}));
observar($("#g-dias"), () => lineas($("#g-dias"), {series: [{nombre: "Días", puntos: S("vivienda", "dias_en_mercado"), color: "var(--accent)"}], alto: 170, fmtX: s => fMes(s, true), fmtY: v => nf(v) + " días", cero: true, area: true, aria: "Días en el mercado"}));
const aut = S("vivienda", "viviendas_autorizadas"), autAnio = {};
aut.forEach(([m, v]) => { const y = m.slice(0, 4); (autAnio[y] = autAnio[y] || []).push(v); });
const autPts = Object.entries(autAnio).filter(([, v]) => v.length === 12).map(([y, v]) => [y, Math.round(v.reduce((a, b) => a + b, 0))]);
const a12 = C("vivienda", "viviendas_autorizadas_12_meses"), vA12 = C("vivienda", "variacion_viviendas_autorizadas").valor;
$("#r-autorizadas").textContent = `En los 12 meses a ${fMes(a12.vigencia)} se autorizaron ${nf(a12.valor)} viviendas nuevas en el área, ${pct(vA12, 0)} frente a los 12 meses anteriores. Suma anual de la serie mensual ajustada.`;
$("#f-autorizadas").innerHTML = chip("fred_bps", "viviendas_autorizadas", a12.vigencia);
observar($("#g-autorizadas"), () => barras($("#g-autorizadas"), {puntos: autPts, fmtX: s => s, fmtY: v => nf(v) + " viviendas", aria: "Viviendas nuevas autorizadas por año"}));
const perAnio = S("permisos", "permisos_por_anio"), enCurso = C("permisos", "permisos_emitidos_anio_en_curso");
$("#r-permisosanio").innerHTML = `${frasePer} El año en curso va en <b>${nf(enCurso.valor)}</b> al ${fDia(enCurso.vigencia)} (no se grafica: está incompleto).`;
$("#f-permisosanio").innerHTML = chip("orlando_permisos", "permisos_por_anio", tot.vigencia);
observar($("#g-permisosanio"), () => barras($("#g-permisosanio"), {puntos: perAnio, fmtX: s => s, fmtY: (v, i) => `${nf(v)} permisos${i > 0 ? `<br><span class="s">${pct((v / perAnio[i - 1][1] - 1) * 100)} frente a ${perAnio[i - 1][0]}</span>` : ""}`, aria: "Permisos emitidos por año"}));
const empT = S("economia", "empleo_total"), eT = C("economia", "empleo_total_ultimo_mes"), vET = C("economia", "variacion_empleo_12_meses").valor;
$("#r-empleototal").textContent = `El área tiene ${millones(eT.valor)} de empleos (${fMes(eT.vigencia)}), ${pct(vET)} en un año. En 1990 eran ${nf(empT[0][1] / 1000, 2)} millones.`;
$("#f-empleototal").innerHTML = chip("fred_ces", "empleo_total", eT.vigencia);
const pand = empT.filter(p => p[0] >= "2020-01" && p[0] <= "2020-12").reduce((a, b) => b[1] < a[1] ? b : a);
observar($("#g-empleototal"), () => lineas($("#g-empleototal"), {series: [{nombre: "Empleos", puntos: empT, color: "var(--accent)"}], fmtX: s => fMes(s, true), fmtY: v => nf(v, 0) + " mil", area: true, cero: true, notas: [{x: pand[0], texto: "Pandemia", pos: "abajo"}], aria: "Empleo total del área"}));
$$(".seg[data-rango]").forEach(g => g.addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  $$("button", g).forEach(x => x.setAttribute("aria-pressed", x === b));
  const r = b.dataset.r;
  if (g.dataset.rango === "desempleo") { rDes = +r; dibDes(); }
  else if (g.dataset.rango === "vivienda") { modoViv = r; dibViv(); }
  else if (g.dataset.rango === "ocio") { modoOcio = r; dibOcio(); }
}));
$$(".seg[data-rango] button").forEach(b => { if (!b.hasAttribute("aria-pressed")) b.setAttribute("aria-pressed", "false"); });

// ---------- v3: salarios por hora contra las áreas pares ----------
const sal = C("economia", "salario_hora_ultimo_mes"), pSal = C("economia", "puesto_salario_entre_pares").valor, salP = C("economia", "salario_frente_a_pares").valor, vSal = C("economia", "variacion_salario_12_meses").valor;
$("#r-salario").textContent = nb(`En ${fMes(sal.vigencia, true)} el sector privado del área pagó en promedio US$${NB}${nf(sal.valor, 2)} la hora, ${salP < 0 ? nf(-salP, 0) + " % menos" : nf(salP, 0) + " % más"} que el promedio de Tampa, Miami y Jacksonville: ${pSal === 4 ? "el más bajo de los cuatro" : pSal === 1 ? "el más alto de los cuatro" : "puesto " + pSal + " de 4"}. Para quien contrata es un costo menor; para quien trabaja, menos poder de compra.`);
$("#k-salario").innerHTML = `<div class="kpi"><small>Por hora, sector privado</small><b>US$${NB}${nf(sal.valor, 2)}</b><span class="vig">${fMes(sal.vigencia)}</span></div><div class="kpi"><small>En 12 meses</small><div class="fila"><b>${pct(vSal)}</b></div><span class="vig">sin ajuste estacional</span></div>`;
$("#f-salario").innerHTML = chip("fred_salarios", "salario_hora_<área>", sal.vigencia);
const SAL = [["orlando", "Orlando", "var(--ink)", true], ["tampa", "Tampa", "var(--c1)"], ["miami", "Miami", "var(--c2)"], ["jacksonville", "Jacksonville", "var(--c3)"]];
const ocultosSal = new Set();
const dibSal = () => lineas($("#g-salario"), {series: SAL.filter(([k]) => !ocultosSal.has(k) || k === "orlando").map(([k, n, c, yo]) => ({nombre: n, puntos: S("economia", `salario_hora_${k}`).filter(p => p[0] >= "2015"), color: c, resaltar: yo})),
  fmtX: s => fMes(s, true), fmtY: v => "US$" + NB + nf(v, 2), fmtTick: (v, d) => nf(v, d), etiquetas: true, aria: "Salario por hora en Orlando y sus pares"});
leyToggle($("#ley-salario"), SAL.slice(1), ocultosSal, dibSal);
observar($("#g-salario"), dibSal);

// ---------- v3: arriendo típico (Zillow) contra pares ----------
const zori = C("vivienda", "arriendo_tipico_ultimo_mes"), vZori = C("vivienda", "variacion_arriendo_12_meses").valor;
const ZOR = [["orlando", "Orlando", "var(--ink)", true], ["tampa", "Tampa", "var(--c1)"], ["miami", "Miami", "var(--c2)"], ["jacksonville", "Jacksonville", "var(--c3)"], ["eeuu", "EE. UU.", "var(--muted)"]];
const zUlt = Object.fromEntries(ZOR.map(([k]) => [k, ult(S("vivienda", `arriendo_tipico_${k}`))[1]]));
$("#r-zori").textContent = nb(`Un arriendo típico en el área cuesta ${usd(zori.valor)} al mes (${fMes(zori.vigencia)}), ${Math.abs(vZori) < 1 ? "casi igual que" : vZori > 0 ? pct(vZori) + " frente a" : pct(vZori) + " frente a"} hace un año. Es casi el promedio del país (${usd(zUlt.eeuu)}); Miami está muy arriba (${usd(zUlt.miami)}) y Jacksonville abajo (${usd(zUlt.jacksonville)}).`);
$("#f-zori").innerHTML = chip("zillow_research", "arriendo_tipico_<área>", zori.vigencia);
const ocultosZ = new Set();
const dibZ = () => lineas($("#g-zori"), {series: ZOR.filter(([k]) => !ocultosZ.has(k) || k === "orlando").map(([k, n, c, yo]) => ({nombre: n, puntos: S("vivienda", `arriendo_tipico_${k}`), color: c, resaltar: yo})),
  fmtX: s => fMes(s, true), fmtY: v => usd(v), fmtTick: v => nf(v), etiquetas: true, aria: "Arriendo típico por área"});
leyToggle($("#ley-zori"), ZOR.slice(1), ocultosZ, dibZ);
observar($("#g-zori"), dibZ);

// ---------- v3: ¿mercado de compradores o de vendedores? (regla a la vista) ----------
const METROS_V = [["orlando", "Orlando"], ["tampa", "Tampa"], ["miami", "Miami"], ["jacksonville", "Jacksonville"]];
const serieV = (base, c) => S("vivienda", c === "orlando" ? (base === "rebajas" ? "rebajas" : base) : `${base}_${c}`);
function senalesMercado(c) {
  const lista = serieV("precio_mediano_lista", c), dias = serieV("dias_en_mercado", c), inv = serieV("casas_en_venta", c), reb = serieV("rebajas", c);
  const u = lista.length - 1, var12 = (s_, i) => (s_[i][1] / s_[i - 12][1] - 1) * 100;
  const s = {precio: var12(lista, u), dias: dias[u][1], diasAntes: dias[u - 12][1], inventario: var12(inv, u), rebaja: reb[u][1] / inv[u][1] * 100, mes: lista[u][0], precioNivel: lista[u][1]};
  const aFavor = [s.precio <= 0, s.dias >= 60 || s.dias > s.diasAntes * 1.1, s.inventario >= 10, s.rebaja >= 30];
  const n = aFavor.filter(Boolean).length;
  s.veredicto = n >= 3 ? "Favorece al comprador" : n <= 1 ? "Favorece al vendedor" : "Equilibrado";
  s.nivel = n >= 3 ? "comprador" : n <= 1 ? "vendedor" : "equilibrio"; s.n = n;
  return s;
}
const SM = Object.fromEntries(METROS_V.map(([c]) => [c, senalesMercado(c)]));
$("#tablaMercado thead").innerHTML = `<tr><th>Área</th><th class="n">Precio de lista</th><th class="n">En un año</th><th class="n">Días para vender</th><th class="n">Con rebaja</th><th class="n">Inventario en un año</th><th>Lectura</th></tr>`;
$("#tablaMercado tbody").innerHTML = METROS_V.map(([c, n]) => { const x = SM[c]; return `<tr${c === "orlando" ? ' style="font-weight:700"' : ""}><td>${n}</td><td class="n">${usd(x.precioNivel)}</td><td class="n">${pct(x.precio)}</td><td class="n">${nf(x.dias)} <span class="vig">(${nf(x.diasAntes)})</span></td><td class="n">${nf(x.rebaja, 0)}${NB}%</td><td class="n">${pct(x.inventario)}</td><td>${x.veredicto}</td></tr>`; }).join("");
$("#r-mercado2").textContent = nb(`Orlando, ${fMes(SM.orlando.mes, true)}: ${SM.orlando.veredicto.toLowerCase()}. Contamos cuatro señales a favor de quien compra: precio de lista que baja, más de 60 días para vender (o 10 % más que hace un año), inventario que sube 10 % o más y 30 % o más de viviendas con rebaja. Orlando cumple ${SM.orlando.n} de 4. Entre paréntesis, los días de hace un año.`);
$("#f-mercado2").innerHTML = chip("fred_realtor", "rebajas / casas_en_venta / dias_en_mercado", SM.orlando.mes);

// ---------- v3: solicitudes de nuevos negocios en Florida ----------
const bfs12 = C("economia", "solicitudes_negocio_florida_12_meses"), vBfs = C("economia", "variacion_solicitudes_negocio_florida").valor, shBfs = C("economia", "participacion_florida_en_negocios_eeuu").valor;
$("#r-bfs").textContent = nb(`En los 12 meses a ${fMes(bfs12.vigencia, true)} se pidieron ${nf(bfs12.valor)} registros de negocio nuevos en Florida (${pct(vBfs)} frente a los 12 anteriores): ${nf(shBfs, 1)} de cada 100 del país, con apenas 7 de cada 100 habitantes. No hay dato mensual por condado.`);
$("#f-bfs").innerHTML = chip("fred_bfs", "solicitudes_negocio_florida", bfs12.vigencia);
observar($("#g-bfs"), () => lineas($("#g-bfs"), {series: [{nombre: "Florida", puntos: S("economia", "solicitudes_negocio_florida"), color: "var(--accent)"}], fmtX: s => fMes(s, true), fmtY: v => nf(v) + " solicitudes", fmtTick: v => nf(v / 1000) + NB + "mil", area: true, cero: true, aria: "Solicitudes de nuevos negocios en Florida"}));

/* ================= BARRIOS ================= */
$("#r-barrios").textContent = `${frasePer.split(". ")[0]}. ${topDel[0][0]} tiene más casos de policía y ${bonito(S("negocios", "negocios_barrio")[0][0])} más negocios. Elige qué mirar en el mapa y toca un barrio para ver su ficha.`;
$("#listaBarrios").innerHTML = B.map(b => `<option value="${esc(b.nombre)}"></option>`).join("");
let selB = null, compB = null;
const atlasB = crearAtlas($("#atlasBarrios"), {selector: true, estado: {lente: "permisos", anio: U_PERM}, onSelect: i => { selB = i; fichaBarrio(); rankingBarrios(); }, onLente: () => { ajustarAnio(); rankingBarrios(); }});
function ajustarAnio() {
  const met = METRICAS[atlasB.st.lente], anios = met.anios.map(Number), r = $("#anioRango");
  r.min = anios[0]; r.max = ult(anios); r.disabled = anios.length < 2; $("#anioPlay").disabled = anios.length < 2;
  if (!anios.includes(+atlasB.st.anio)) atlasB.st.anio = ult(anios);
  r.value = atlasB.st.anio; $("#anioTxt").textContent = met.fuente === "orlando_negocios" && atlasB.st.lente !== "aperturas" ? "hoy" : String(met.anios.length > 1 ? atlasB.st.anio : met.anios[0]).replace("-", "–");
  // Por km² y por 1.000 hab. solo valen para conteos; una tasa (%, mediana, puntaje) se muestra tal cual
  $$("#segMedida button").forEach(b => { const ok = aplica(atlasB.st.lente, b.dataset.m) && !lenteDe(atlasB.st.lente).modo; b.disabled = !ok; b.title = ok ? "" : "Esta medida ya es una tasa: no se divide por área ni por población"; });
  atlasB.pintar();
}
$("#anioRango").addEventListener("input", e => { atlasB.st.anio = +e.target.value; $("#anioTxt").textContent = e.target.value; atlasB.pintar(); rankingBarrios(); });
let animAnio = null;
$("#anioPlay").addEventListener("click", () => {
  if (animAnio) { clearInterval(animAnio); animAnio = null; $("#anioPlay").innerHTML = ic("play"); return; }
  const r = $("#anioRango"); $("#anioPlay").innerHTML = ic("pausa");
  r.value = r.min; r.dispatchEvent(new Event("input"));
  animAnio = setInterval(() => { if (+r.value >= +r.max) { clearInterval(animAnio); animAnio = null; $("#anioPlay").innerHTML = ic("play"); return; } r.value = +r.value + 1; r.dispatchEvent(new Event("input")); }, 1300);
});
$("#segMedida").addEventListener("click", e => { const b = e.target.closest("button"); if (!b || b.disabled) return; atlasB.st.modo = b.dataset.m; $$("#segMedida button").forEach(x => x.setAttribute("aria-pressed", x === b)); atlasB.pintar(); rankingBarrios(); });
$("#buscarBarrio").addEventListener("change", e => {
  const t = norm(e.target.value); if (!t) return;
  const j = IDX.has(t) ? IDX.get(t) : B.findIndex(b => norm(b.nombre).includes(t));
  if (j >= 0) { atlasB.seleccionar(j, true); e.target.value = ""; } else aviso("No encontramos ese barrio");
});
function rankingBarrios() {
  const st = atlasB.st, met = METRICAS[st.lente], a = met.anios.map(Number).includes(+st.anio) ? +st.anio : undefined;
  const modo = lenteDe(st.lente).modo || (aplica(st.lente, st.modo) ? st.modo : "total");
  const filas = B.map((b, i) => ({nombre: b.nombre, valor: valorDe(st.lente, b, a, modo), i, sel: i === selB})).filter(f => f.valor != null && (f.valor > 0 || !met.cero)).sort((x, y) => y.valor - x.valor).slice(0, 10);
  const que = st.lente === "indice" ? "mayor puntaje en el índice" : met.tipo === "tasa" ? `mayor ${met.corto.toLowerCase()}` : st.lente === "poblacion" ? "más habitantes por km²" : `más ${met.frase}${sufijo(modo)}`;
  $("#tRanking").textContent = `Los 10 barrios con ${que}`;
  listaBarras($("#ranking"), filas, {fmt: v => fmtV(v, modo, st.lente), onClick: f => atlasB.seleccionar(f.i, true)});
}
const GRUPOS_FICHA = [
  ["Qué pasa (último año)", ["permisos", "delitos", "quejas", "negocios", "aperturas", "restaurantes", "hospedajes"]],
  ["Quién vive (censo 2020–2024, estimado)", ["poblacion", "ingreso", "arriendo", "carga", "arrend", "sinCarro", "espanol", "pobreza", "univ", "edad"]],
  ["Qué tiene cerca", ["parques", "colegios", "ciclo", "sunrail"]],
  ["Riesgo (FEMA)", ["rInund", "rHuracan", "rCalor", "rVulner"]],
  ["Hacia dónde va", ["crec45", "crecEmp45", "grandes", "abiertas", "zo"]],
  ["Índice", ["indice"]],
];
const MEDIDAS_FICHA = GRUPOS_FICHA.flatMap(g => g[1]);
const MEDIANA = Object.fromEntries(Object.keys(METRICAS).map(k => [k, mediana(B.map(b => METRICAS[k].v(b)))]));
const rango = (met, i) => { const vals = B.map(b => METRICAS[met].v(b)).map((v, k) => [k, v]).filter(x => x[1] != null).sort((a, b) => b[1] - a[1]); const p = vals.findIndex(x => x[0] === i); return {p: p + 1, n: vals.length, max: vals[0] ? vals[0][1] : 1}; };
const vtxt = (k, v) => v == null ? "—" : METRICAS[k].fmt ? METRICAS[k].fmt(v) : k === "indice" ? nf(v, 0) : nf(v);
let grupoAbierto = 0;
function fichaBarrio() {
  const el = $("#fichaSel");
  if (selB == null) {
    el.innerHTML = `<p class="eyebrow">${ic("info")}Cómo usar el mapa</p><h3 style="font-size:1.25rem">Toca un barrio para ver su ficha</h3>
      <p class="peq">Arriba eliges qué mirar: qué pasa (construcción, seguridad, negocios), quién vive (población, ingreso, arriendo), qué tiene cerca, riesgo y hacia dónde va. Arrastra para mover, usa dos dedos o la rueda para acercar y el botón 2D/3D para inclinar. «Por km²» y «Por 1.000 hab.» comparan barrios de distinto tamaño; la barra del año muestra cómo cambió.</p>
      <div class="medidas">${["poblacion", "permisos", "delitos", "negocios"].map(k => { const met = METRICAS[k], t = B.reduce((s, b) => s + (met.v(b) || 0), 0); return `<div class="medida"><span class="n">${met.nombre} (suma de barrios)</span><span class="v">${nf(t)}</span><span></span></div>`; }).join("")}</div>`;
    return;
  }
  const b = B[selB], c = compB != null ? B[compB] : null;
  const fila = k => {
    const met = METRICAS[k], v = met.v(b), r = rango(k, selB), v2 = c ? met.v(c) : undefined, med = MEDIANA[k];
    const tasa = met.tipo === "conteo" && b.pob >= MIN_HAB && v != null ? porHab(v, b) : null;
    const serie = met.anios.length > 2 && met.anios.every(a => met.v(b, a) != null) ? `<span style="grid-column:1/-1;display:grid;gap:2px">${spark(met.anios.map(a => [String(a), met.v(b, a)]), "var(--accent)", 24)}<span class="r"><span>${met.anios[0]}</span><span>${ult(met.anios)}</span></span></span>` : "";
    const ancho = x => Math.max(0, Math.min(100, (x - Math.min(0, ...B.map(bb => met.v(bb) ?? 0))) / (r.max - Math.min(0, ...B.map(bb => met.v(bb) ?? 0)) || 1) * 100));
    return `<div class="medida"><span class="n">${esc(met.nombre)}${met.anios.length > 1 ? ` (${ult(met.anios)})` : ""}</span><span class="v">${vtxt(k, v)}</span>${c ? `<span class="v2">${vtxt(k, v2)}</span>` : "<span></span>"}
      ${v == null ? `<span class="r"><span>${met.tipo === "tasa" && met.fuente === "censo_acs" ? "Sin estimación (menos de " + MIN_HAB + " habitantes)" : "Sin dato publicable (menos de 5 o ninguno)"}</span></span>` : `<span class="rb"><i style="width:${ancho(v)}%"></i>${med != null ? `<u class="med" title="Mediana de los barrios: ${vtxt(k, med)}" style="left:calc(${ancho(med)}% - 1px)"></u>` : ""}${c && v2 != null ? `<u style="left:calc(${ancho(v2)}% - 1px)"></u>` : ""}</span><span class="r"><span>Puesto ${r.p} de ${r.n} · mediana ${vtxt(k, med)}</span><span>${tasa != null ? fmtV(tasa, "hab") + " por 1.000 hab." : ""}</span></span>`}
      ${serie}</div>`;
  };
  el.innerHTML = `<div class="titulo"><div><p class="eyebrow">Barrio · distrito ${b.distrito} · ${nf(b.km2, 2)} km²${b.pob != null ? ` · ${nf(b.pob)} hab.` : ""}</p><h3>${esc(b.nombre)}</h3></div><button class="btn" type="button" id="limpiarSel" aria-label="Quitar selección">${ic("cerrar")}</button></div>
    <div class="etiquetas-b">${[b.zo >= 5 ? "Zona de Oportunidad federal" : "", b.mainSt >= 5 ? "Área de Main Street" : "", b.cra >= 5 ? "Área de Redesarrollo (CRA)" : "", b.sunrail ? "Estación de SunRail" : ""].filter(Boolean).map(t => `<span class="etq-z">${esc(t)}</span>`).join("")}</div>
    <div class="filtros"><label class="peq" for="compSel">Comparar con</label><select class="sel" id="compSel"><option value="">— ningún barrio —</option>${B.map((x, i) => i === selB ? "" : `<option value="${i}" ${i === compB ? "selected" : ""}>${esc(x.nombre)}</option>`).join("")}</select></div>
    ${c ? `<p class="peq"><b style="color:var(--ink)">${esc(b.nombre)}</b> en negro · <b style="color:var(--sun)">${esc(c.nombre)}</b> en amarillo · la raya gris es la mediana de los barrios</p>` : `<p class="peq">La raya gris en cada barra es la mediana de los 125 barrios.</p>`}
    ${GRUPOS_FICHA.map(([t, ks], gi) => `<details class="grupo-ficha" ${gi === grupoAbierto ? "open" : ""} data-g="${gi}"><summary>${esc(t)}</summary><div class="medidas">${ks.map(fila).join("")}</div></details>`).join("")}
    <div class="filtros"><button class="btn" type="button" id="copiarFicha">${ic("copiar")}Copiar ficha</button><a class="btn" href="#comparar/barrios/${selB}">${ic("comparar")}Comparar en detalle</a>${chip("orlando_barrios", "properties.nombre", C("territorio", "poligonos_barrios").vigencia)}</div>`;
  $$("#fichaSel details.grupo-ficha").forEach(d => d.addEventListener("toggle", () => { if (d.open) grupoAbierto = +d.dataset.g; }));
  $("#compSel").onchange = e => { compB = e.target.value === "" ? null : +e.target.value; fichaBarrio(); };
  $("#copiarFicha").onclick = () => copiar([`${b.nombre} (distrito ${b.distrito}, ${nf(b.km2, 2)} km²) · Cerebro Orlando, datos al ${fDia(D.generado)}`,
    ...MEDIDAS_FICHA.map(k => { const v = METRICAS[k].v(b); return `- ${METRICAS[k].nombre}: ${v == null ? "sin dato publicable" : vtxt(k, v)}`; })].join("\n"), "Ficha copiada");
}
document.addEventListener("click", e => { if (e.target.closest("#limpiarSel")) { selB = null; compB = null; atlasB.seleccionar(null, false); atlasB.verTodo(); } });
function irABarrio(i) { location.hash = "barrios"; setTimeout(() => { atlasB.seleccionar(i, true); $("#atlasBarrios").scrollIntoView({behavior: "smooth", block: "center"}); }, 120); }
const umbrales = ["permisos", "seguridad", "codigo", "negocios"].map(t => C(t, "umbral_minimo_por_barrio").valor);
$("#notaPrivBarrios").innerHTML = `<b>Cuidamos a las personas.</b> Los permisos traen el nombre del propietario y el contratista; los casos de policía, el número de caso y el punto exacto; los negocios, el dueño y su teléfono. Nada de eso se descarga: los servidores de la ciudad devuelven conteos por barrio, y los barrios con menos de ${Math.min(...umbrales)} casos en el año salen en gris, igual que los que no tuvieron ninguno, para no revelar cuáles son. Distrito, área, «por km²» y «por 1.000 habitantes» son <button class="term" data-term="derivado">derivados</button>; los habitantes de cada barrio son una <button class="term" data-term="estimacion">estimación</button> a partir del censo.`;

// Índice con pesos movibles
$("#pesos").innerHTML = `<div class="filtros">${Object.keys(PRESETS).map(n => `<button type="button" class="chip" data-p="${n}" aria-pressed="${n === "Equilibrio"}">${n}</button>`).join("")}</div>` +
  DIMS.map((d, k) => `<div class="peso"><label for="peso${k}">${d.nombre}<span class="peq" style="font-weight:400"> · ${d.desc}</span></label><output id="o-peso${k}">${pesos[k]}</output><input type="range" id="peso${k}" min="0" max="3" step="1" value="${pesos[k]}"></div>`).join("");
const mapaIdx = mapaPlano($("#mapaIndice"), {valores: i => IND[i], onClick: i => irABarrio(i), ley: $("#leyIndice"), titulo: () => "Índice de atención (0 a 100)", fmt: v => nf(v, 0),
  globo: i => `<b>${esc(B[i].nombre)}</b><br>Índice: <b>${nf(IND[i], 0)}</b> de 100<br><span class="s">${DIMS.map((d, k) => `${d.nombre} ${nf(percentil[k][i], 0)}`).join(" · ")}</span>`});
function actualizarIndice() {
  IND = indice(); mapaIdx.pintar();
  const top = B.map((b, i) => [i, IND[i]]).sort((a, b) => b[1] - a[1]).slice(0, 10);
  const tops = Object.values(PRESETS).map(p => new Set(indice(p).map((v, i) => [i, v]).sort((a, b) => b[1] - a[1]).slice(0, 10).map(x => x[0])));
  const firmes = top.filter(([i]) => tops.every(s => s.has(i))).length;
  $("#r-indice").textContent = `${B[top[0][0]].nombre} encabeza con estos pesos. ${firmes} de los 10 primeros siguen en el top 10 con cualquiera de los cuatro enfoques: ${firmes >= 7 ? "la conclusión se sostiene" : firmes >= 4 ? "la conclusión se sostiene a medias" : "la conclusión depende mucho de los pesos"}.`;
  listaBarras($("#rankIndice"), top.map(([i, v]) => ({nombre: B[i].nombre, valor: v, i})), {fmt: v => nf(v, 0), max: 100, onClick: f => irABarrio(f.i)});
  if (atlasB.st.lente === "indice") { atlasB.pintar(); rankingBarrios(); }
}
$("#pesos").addEventListener("input", e => { const k = +e.target.id.replace("peso", ""); pesos[k] = +e.target.value; $("#o-peso" + k).textContent = e.target.value; $$("#pesos .chip").forEach(c => c.setAttribute("aria-pressed", "false")); actualizarIndice(); });
$("#pesos").addEventListener("click", e => { const c = e.target.closest(".chip"); if (!c) return; pesos = [...PRESETS[c.dataset.p]]; pesos.forEach((v, k) => { $("#peso" + k).value = v; $("#o-peso" + k).textContent = v; }); $$("#pesos .chip").forEach(x => x.setAttribute("aria-pressed", x === c)); actualizarIndice(); });
actualizarIndice();

// Correlaciones
// Los conteos se comparan por 1.000 habitantes (si el barrio tiene población estimada) y las tasas, tal cual
const OPC = ["delitos", "quejas", "permisos", "negocios", "restaurantes", "aperturas", "ingreso", "arriendo", "carga", "sinCarro", "espanol", "pobreza", "univ", "rInund", "rVulner", "crec45"];
const modoCorr = k => METRICAS[k].tipo === "conteo" ? "hab" : "total";
const nomCorr = k => METRICAS[k].nombre + sufijo(modoCorr(k));
$("#corrX").innerHTML = OPC.map(k => `<option value="${k}" ${k === "ingreso" ? "selected" : ""}>${esc(nomCorr(k))}</option>`).join("");
$("#corrY").innerHTML = OPC.map(k => `<option value="${k}" ${k === "delitos" ? "selected" : ""}>${esc(nomCorr(k))}</option>`).join("");
function rangos(v) { const o = v.map((x, i) => [x, i]).sort((a, b) => a[0] - b[0]), r = Array(v.length); for (let i = 0; i < o.length;) { let j = i; while (j < o.length && o[j][0] === o[i][0]) j++; for (let k = i; k < j; k++) r[o[k][1]] = (i + j - 1) / 2; i = j; } return r; }
function spearman(x, y) { const rx = rangos(x), ry = rangos(y), n = x.length, mx = rx.reduce((a, b) => a + b) / n, my = ry.reduce((a, b) => a + b) / n; let s = 0, sx = 0, sy = 0; for (let i = 0; i < n; i++) { s += (rx[i] - mx) * (ry[i] - my); sx += (rx[i] - mx) ** 2; sy += (ry[i] - my) ** 2; } return s / Math.sqrt(sx * sy); }
function dispersion() {
  const kx = $("#corrX").value, ky = $("#corrY").value, el = $("#g-corr");
  const pts = B.map((b, i) => [valorDe(kx, b, undefined, modoCorr(kx)), valorDe(ky, b, undefined, modoCorr(ky)), i]).filter(p => p[0] > 0 && p[1] > 0);
  const rho = spearman(pts.map(p => p[0]), pts.map(p => p[1]));
  const fuerza = Math.abs(rho) < .2 ? "casi ninguna relación" : Math.abs(rho) < .4 ? "una relación débil" : Math.abs(rho) < .6 ? "una relación moderada" : Math.abs(rho) < .8 ? "una relación fuerte" : "una relación muy fuerte";
  $("#r-corr").textContent = kx === ky ? "Elige dos medidas distintas." : `Entre los ${pts.length} barrios con ambos datos hay ${fuerza} ${rho > 0 ? "positiva" : "negativa"} (ρ de Spearman = ${nf(rho, 2)}): ${rho > .2 ? "donde hay más " + METRICAS[kx].frase + " tiende a haber más " + METRICAS[ky].frase : rho < -.2 ? "donde hay más " + METRICAS[kx].frase + " tiende a haber menos " + METRICAS[ky].frase : "saber una no ayuda a adivinar la otra"}.`;
  const W = el.clientWidth, H = W < 500 ? 320 : 380, m = {t: 30, r: 28, b: 40, l: 54};
  const lx = pts.map(p => Math.log10(p[0])), ly = pts.map(p => Math.log10(p[1]));
  const ex = [Math.floor(Math.min(...lx)), Math.ceil(Math.max(...lx))], ey = [Math.floor(Math.min(...ly)), Math.ceil(Math.max(...ly))];
  const X = v => m.l + (Math.log10(v) - ex[0]) / (ex[1] - ex[0] || 1) * (W - m.l - m.r), Y = v => m.t + (1 - (Math.log10(v) - ey[0]) / (ey[1] - ey[0] || 1)) * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" height="${H}" role="img" aria-label="Dispersión de barrios">`;
  for (let e = ex[0]; e <= ex[1]; e++) s += `<line x1="${X(10 ** e)}" x2="${X(10 ** e)}" y1="${m.t}" y2="${H - m.b}" style="stroke:var(--line)"/><text x="${X(10 ** e)}" y="${H - m.b + 16}" text-anchor="middle">${nf(10 ** e, e < 0 ? -e : 0)}</text>`;
  for (let e = ey[0]; e <= ey[1]; e++) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(10 ** e)}" y2="${Y(10 ** e)}" style="stroke:var(--line)"/><text x="${m.l - 8}" y="${Y(10 ** e) + 4}" text-anchor="end">${nf(10 ** e, e < 0 ? -e : 0)}</text>`;
  s += `<text x="${W - m.r}" y="${H - 4}" text-anchor="end" class="etq" style="fill:var(--ink-2)">${esc(METRICAS[kx].corto + sufijo(modoCorr(kx)))} →</text><text x="${m.l - 46}" y="${m.t - 14}" class="etq" style="fill:var(--ink-2)">↑ ${esc(METRICAS[ky].corto + sufijo(modoCorr(ky)))}</text>`;
  pts.forEach(([x, y, i]) => s += `<circle class="pt" data-i="${i}" cx="${X(x)}" cy="${Y(y)}" r="${i === selB ? 7 : 5}" style="fill:${i === selB ? "var(--sun)" : "var(--accent)"};fill-opacity:.75;stroke:var(--surface)" stroke-width="1.5"/>`);
  s += `</svg>`;
  el.innerHTML = s;
  const svg = el.querySelector("svg");
  svg.addEventListener("pointermove", e => { const c = e.target.closest(".pt"); if (!c) return ocultarGlobo(); const i = +c.dataset.i; mostrarGlobo(`<b>${esc(B[i].nombre)}</b><br>${esc(METRICAS[kx].corto)}: ${fmtV(valorDe(kx, B[i], undefined, modoCorr(kx)), modoCorr(kx), kx)}${sufijo(modoCorr(kx))}<br>${esc(METRICAS[ky].corto)}: ${fmtV(valorDe(ky, B[i], undefined, modoCorr(ky)), modoCorr(ky), ky)}${sufijo(modoCorr(ky))}<br><span class="s">Toca para ver su ficha</span>`, e.clientX, e.clientY); });
  svg.addEventListener("pointerleave", ocultarGlobo);
  svg.addEventListener("click", e => { const c = e.target.closest(".pt"); if (c) irABarrio(+c.dataset.i); });
}
$("#corrX").onchange = dispersion; $("#corrY").onchange = dispersion;
observar($("#g-corr"), dispersion);

// Tabla accesible
const COLS = [["nombre", "Barrio"], ["distrito", "Distrito"], ["km2", "Área km²"], ["poblacion", "Habitantes (est.)"], ["ingreso", "Ingreso (aprox.)"], ["arriendo", "Arriendo (aprox.)"], ["permisos", `Permisos ${U_PERM}`], ["delitos", `Casos policía ${U_DEL}`], ["quejas", `Quejas ${U_COD}`], ["negocios", "Negocios"], ["rInund", "Riesgo inundación"], ["crec45", "Crecimiento 2045"], ["indice", "Índice"]];
let ordenK = "indice", ordenAsc = false;
const celda = (b, k) => k === "nombre" ? b.nombre : k === "distrito" ? +b.distrito : k === "km2" ? b.km2 : METRICAS[k].v(b);
function tabla() {
  $("#tablaBarrios thead").innerHTML = `<tr>${COLS.map(([k, t]) => `<th class="${k === "nombre" ? "" : "n"}" aria-sort="${k === ordenK ? (ordenAsc ? "ascending" : "descending") : "none"}"><button type="button" data-k="${k}">${t}</button></th>`).join("")}</tr>`;
  const filas = [...B].sort((a, b) => { const x = celda(a, ordenK), y = celda(b, ordenK); if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1; const r = typeof x === "string" ? x.localeCompare(y, "es") : x - y; return ordenAsc ? r : -r; });
  $("#tablaBarrios tbody").innerHTML = filas.map(b => `<tr>${COLS.map(([k]) => { const v = celda(b, k); return `<td class="${k === "nombre" ? "" : "n"}">${k === "nombre" ? esc(v) : v == null ? "—" : k === "km2" ? nf(v, 2) : METRICAS[k] && METRICAS[k].fmt ? METRICAS[k].fmt(v) : nf(v, k === "indice" ? 0 : 0)}</td>`; }).join("")}</tr>`).join("");
}
$("#tablaBarrios thead").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; if (ordenK === b.dataset.k) ordenAsc = !ordenAsc; else { ordenK = b.dataset.k; ordenAsc = ordenK === "nombre"; } tabla(); });
$("#sumTabla").textContent = `Ver los ${B.length} barrios en una tabla (— = sin dato publicable)`;
tabla(); ajustarAnio(); rankingBarrios(); fichaBarrio();

/* ================= SEGURIDAD ================= */
$("#r-seg").textContent = fraseSeg;
const GRUPOS = [["hurtos", "Hurtos y robos a la propiedad", "var(--c1)"], ["violencia", "Violencia contra personas", "var(--c2)"], ["drogas", "Drogas", "var(--c3)"]];
$("#k-seg").innerHTML = GRUPOS.map(([k, n]) => { const c = C("seguridad", `${k}_ultimo_anio`), s = S("seguridad", `${k}_por_anio`), prev = s[s.length - 2][1];
  return `<div class="kpi"><small>${n}</small><div class="fila"><b>${nf(c.valor)}</b>${tendencia((c.valor / prev - 1) * 100, 1, "inverso")}</div><span class="vig">${c.vigencia} · frente a ${s[s.length - 2][0]}</span></div>`; }).join("");
$("#ley-seg").innerHTML = GRUPOS.map(([, n, c]) => `<span><i style="background:${c}"></i>${n}</span>`).join("");
$("#f-seg").innerHTML = chip("opd_casos", "hurtos_por_anio", del.vigencia);
observar($("#g-seg"), () => lineas($("#g-seg"), {series: GRUPOS.map(([k, n, c]) => ({nombre: n.split(" ")[0], puntos: S("seguridad", `${k}_por_anio`), color: c, resaltar: true})), fmtX: s => s, fmtY: v => nf(v) + " casos", cero: true, etiquetas: true,
  ticksX: (x0, x1) => S("seguridad", "hurtos_por_anio").map(p => [tiempo(p[0]), p[0]]), aria: "Casos de policía por año y grupo"}));
let grupoSeg = "delitos", medidaSeg = "km2";
$("#segGrupo").innerHTML = [["delitos", "Todos"], ["hurtos", "Hurtos"], ["violencia", "Violencia"], ["drogas", "Drogas"]].map(([k, n]) => `<button type="button" data-g="${k}" aria-pressed="${k === "delitos"}">${n}</button>`).join("");
const mapaSeg = mapaPlano($("#mapaSeg"), {valores: i => valorDe(grupoSeg, B[i], undefined, medidaSeg), ley: $("#leySeg"), fmt: v => nf(v, v < 10 ? 1 : 0), titulo: () => `Casos${sufijo(medidaSeg)} en ${U_DEL}`, onClick: i => { atlasB.setLente("delitos"); ajustarAnio(); irABarrio(i); },
  globo: i => { const v = METRICAS[grupoSeg].v(B[i]); return `<b>${esc(B[i].nombre)}</b><br>${v == null ? "Sin dato publicable" : `${nf(v)} casos · ${fmtV(porKm2(v, B[i]), "km2")} por km²${porHab(v, B[i]) != null ? ` · ${fmtV(porHab(v, B[i]), "hab")} por 1.000 hab.` : ""}`}<br><span class="s">Toca para verlo en el mapa 3D</span>`; }});
function rankSeg() {
  const met = METRICAS[grupoSeg];
  $("#t-rankseg").textContent = `Barrios con más ${met.frase}${sufijo(medidaSeg)} en ${U_DEL}`;
  $("#t-mapaseg").textContent = `Casos${sufijo(medidaSeg)} en cada barrio`;
  listaBarras($("#rankSeg"), B.map((b, i) => ({nombre: b.nombre, valor: valorDe(grupoSeg, b, undefined, medidaSeg), i})).filter(f => f.valor != null).sort((a, b) => b.valor - a.valor).slice(0, 12),
    {fmt: v => fmtV(v, medidaSeg), onClick: f => irABarrio(f.i)});
}
$("#segGrupo").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; grupoSeg = b.dataset.g; $$("#segGrupo button").forEach(x => x.setAttribute("aria-pressed", x === b)); mapaSeg.pintar(); rankSeg(); });
$("#segMedidaSeg").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; medidaSeg = b.dataset.m; $$("#segMedidaSeg button").forEach(x => x.setAttribute("aria-pressed", x === b)); mapaSeg.pintar(); rankSeg(); });
rankSeg();
$("#verSeg3d").addEventListener("click", () => { atlasB.setLente("delitos"); ajustarAnio(); });
barrasSimples($("#tiposSeg"), S("seguridad", `tipos_${U_DEL}`).slice(0, 12));
$("#f-tipos").innerHTML = chip("opd_casos", `tipos_${U_DEL}`, U_DEL);
const supSeg = C("seguridad", "barrios_suprimidos_ultimo_anio").valor, sinSeg = C("seguridad", "casos_sin_barrio_ultimo_anio").valor;
$("#notaPrivSeg").innerHTML = `<b>Qué decidimos no mostrar.</b> La capa de la policía trae número de caso, fecha y punto exacto: aquí no hay ninguno de esos datos, solo conteos que el servidor calcula por barrio y año. No entran los casos de salud mental (Baker Act), suicidios, muertes, personas desaparecidas, disputas de custodia ni órdenes de alejamiento: no son delitos y señalarían a personas vulnerables. ${supSeg} barrios con menos de ${C("seguridad", "umbral_minimo_por_barrio").valor} casos en ${U_DEL} salen sin dato, y ${nf(sinSeg)} casos no traen barrio. <span class="vig">verificar.py falla si aparece una categoría excluida o una celda bajo el umbral.</span>`;
const cod = C("codigo", "casos_ultimo_anio"), quej = C("codigo", "quejas_ultimo_anio"), vCod = C("codigo", "variacion_ultimo_anio").valor;
const topQ = S("codigo", `quejas_barrio_${U_COD}`).slice(0, 2).map(p => [bonito(p[0]), p[1]]);
$("#r-codigo").textContent = `En ${cod.vigencia} se abrieron ${nf(cod.valor)} casos de código urbano (${pct(vCod, 0)}); ${nf(quej.valor)} nacieron de una queja de vecinos. ${topQ[0][0]} y ${topQ[1][0]} encabezan las quejas.`;
$("#ley-codigo").innerHTML = `<span><i style="background:var(--accent)"></i>Todos los casos</span><span><i style="background:var(--sun)"></i>Por queja ciudadana</span>`;
$("#f-codigo").innerHTML = chip("orlando_codigo", "casos_por_anio", cod.vigencia);
observar($("#g-codigo"), () => lineas($("#g-codigo"), {series: [{nombre: "Todos", puntos: S("codigo", "casos_por_anio"), color: "var(--accent)", resaltar: true}, {nombre: "Por queja", puntos: S("codigo", "quejas_por_anio"), color: "var(--sun)", resaltar: true}],
  fmtX: s => s, fmtY: v => nf(v) + " casos", cero: true, etiquetas: true, aria: "Casos de código urbano por año"}));
listaBarras($("#rankQuejas"), B.map((b, i) => ({nombre: b.nombre, valor: b.quejas, i})).filter(f => f.valor != null).sort((a, b) => b.valor - a.valor).slice(0, 8), {onClick: f => { atlasB.setLente("quejas"); ajustarAnio(); irABarrio(f.i); }});
barrasSimples($("#tiposCodigo"), S("codigo", `tipos_${U_COD}`).slice(0, 10));
$("#notaCodigo").innerHTML = `<b>No es el 311.</b> Las solicitudes al 311 no están publicadas. Las quejas de código son lo más cercano, pero solo cubren el estado de los predios, no baches, ruido ni basuras en la vía. ${nf(C("codigo", "casos_sin_barrio_ultimo_anio").valor)} casos de ${U_COD} (${nf(C("codigo", "casos_sin_barrio_ultimo_anio").valor / cod.valor * 100, 0)} de cada 100) no traen barrio. El origen de la queja solo se anota desde 2020.`;

/* ================= TURISMO ================= */
$("#r-tur").textContent = fraseTur;
const strA = C("turismo", "alquiler_corto_activas"), strT = C("turismo", "alquiler_corto_total_historico");
$("#k-tur").innerHTML = `<div class="kpi"><small>Del empleo total</small><b>${nf(ocio.valor, 1)} %</b><span class="vig">${fMes(ocio.vigencia)}</span></div><div class="kpi"><small>Empleos en ocio y hotelería</small><div class="fila"><b>${nf(ocioN.valor, 0)}${NB}mil</b>${tendencia(vOcio, 1, "normal")}</div><span class="vig">${fMes(ocioN.vigencia)} · en 12 meses</span></div><div class="kpi"><small>Hospedajes con licencia</small><b>${nf(C("negocios", "hospedajes_vigentes").valor)}</b><span class="vig">${fDia(VIG_NEG)}</span></div>`;
$("#f-ocio").innerHTML = chip("fred_ces", "empleo_ocio_hoteleria", ocioN.vigencia);
let modoOcio = "empleos";
const ocioS = S("turismo", "empleo_ocio_hoteleria"), pandO = ocioS.filter(p => p[0] >= "2020-01" && p[0] <= "2020-12").reduce((a, b) => b[1] < a[1] ? b : a);
const dibOcio = () => { $("#t-ocio").textContent = modoOcio === "empleos" ? "Empleos en ocio y hotelería en el área (miles)" : "Ocio y hotelería como % del empleo total";
  lineas($("#g-ocio"), {series: [{nombre: "Ocio", puntos: modoOcio === "empleos" ? ocioS : S("turismo", "participacion_ocio_en_empleo"), color: "var(--accent)"}], fmtX: s => fMes(s, true), fmtY: v => modoOcio === "empleos" ? nf(v, 1) + " mil empleos" : nf(v, 1) + " % del empleo", area: true, cero: modoOcio === "empleos",
    notas: [{x: pandO[0], texto: "Pandemia", pos: "abajo"}], aria: "Empleo en ocio y hotelería"}); };
observar($("#g-ocio"), dibOcio);
mapaPlano($("#mapaHosp"), {valores: i => B[i].hospedajes ?? null, ley: $("#leyHosp"), titulo: () => "Licencias de hospedaje vigentes", onClick: i => { atlasB.setLente("hospedajes"); ajustarAnio(); irABarrio(i); },
  globo: i => `<b>${esc(B[i].nombre)}</b><br>${B[i].hospedajes == null ? "Sin dato publicable" : nf(B[i].hospedajes) + " hospedajes con licencia"}`});
$("#f-hosp").innerHTML = chip("orlando_negocios", "hospedajes_barrio", VIG_NEG);
$("#f-rest").innerHTML = chip("orlando_negocios", "restaurantes_barrio", VIG_NEG);
listaBarras($("#rankHosp"), B.map((b, i) => ({nombre: b.nombre, valor: b.hospedajes, i})).filter(f => f.valor != null).sort((a, b) => b.valor - a.valor).slice(0, 6), {onClick: f => irABarrio(f.i)});
listaBarras($("#rankRest"), B.map((b, i) => ({nombre: b.nombre, valor: b.restaurantes, i})).filter(f => f.valor != null).sort((a, b) => b.valor - a.valor).slice(0, 12), {onClick: f => irABarrio(f.i)});
$("#notaNegocios").innerHTML = `Cuenta licencias de negocio vigentes (Business Tax Receipts), no empresas ni habitaciones. ${C("negocios", "barrios_suprimidos_hospedajes").valor} barrios tienen menos de ${C("negocios", "umbral_minimo_por_barrio").valor} hospedajes y salen sin dato. La mayor parte de los parques temáticos y hoteles de Disney y Universal están fuera de la ciudad de Orlando: no aparecen aquí.`;
$("#r-str").textContent = `Orlando solo tiene ${nf(strA.valor)} alquileres de corto plazo con licencia activa (${nf(strT.valor)} registrados en total, ${fDia(strA.vigencia)}). Las licencias emitidas por año:`;
$("#f-str").innerHTML = chip("orlando_alquiler_corto", "alquiler_corto_activas", strA.vigencia);
observar($("#g-str"), () => barras($("#g-str"), {puntos: S("turismo", "alquiler_corto_emitidas_por_anio"), fmtX: s => s, fmtY: v => nf(v) + " licencias", alto: 200, aria: "Licencias de alquiler de corto plazo por año"}));
const at = C("escucha", "atencion_frente_a_pares");
$("#r-escucha").textContent = `En los últimos 12 meses Orlando recibió ${nf(at.valor, 2)} veces las visitas promedio de Tampa, Miami y Jacksonville en Wikipedia en español; Miami atrae mucho más. ${C("escucha", "variacion_anual").valor < 0 ? `Las visitas a Orlando bajaron ${nf(-C("escucha", "variacion_anual").valor, 0)} % frente al mismo mes del año pasado.` : ""}`;
$("#f-escucha").innerHTML = chip("wikimedia_pageviews", "vistas_mensuales_<ciudad>", C("escucha", "vistas_ultimo_mes").vigencia);
const ESC = [["", "Orlando", "var(--ink)", true], ["_tampa", "Tampa", "var(--c1)"], ["_miami", "Miami", "var(--c2)"], ["_jacksonville", "Jacksonville", "var(--c3)"]];
const ocultosEsc = new Set();
const dibEsc = () => lineas($("#g-escucha"), {series: ESC.filter(([k]) => !ocultosEsc.has(k) || !k).map(([k, n, c, yo]) => ({nombre: n, puntos: S("escucha", `vistas_mensuales${k}`), color: c, resaltar: yo})), fmtX: s => fMes(s, true), fmtY: v => nf(v) + " visitas", fmtTick: v => nf(v / 1000) + " mil", cero: true, etiquetas: true, aria: "Visitas mensuales en Wikipedia por ciudad"});
leyToggle($("#ley-escucha"), ESC.slice(1), ocultosEsc, dibEsc);
observar($("#g-escucha"), dibEsc);

// ---------- v3: el peso del ocio contra las áreas pares, y Wikipedia en inglés ----------
const OCP = [["orlando", "Orlando", "var(--ink)", true], ["tampa", "Tampa", "var(--c1)"], ["miami", "Miami", "var(--c2)"], ["jacksonville", "Jacksonville", "var(--c3)"]];
const ocUlt = Object.fromEntries(OCP.map(([k]) => [k, ult(S("turismo", k === "orlando" ? "participacion_ocio_en_empleo" : `participacion_ocio_${k}`))[1]]));
$("#r-ociopares").textContent = nb(`Orlando es ${C("turismo", "puesto_ocio_entre_pares").valor === 1 ? "el área que más depende" : "una de las áreas que más dependen"} del ocio y la hotelería: ${nf(ocUlt.orlando, 1)} % del empleo, frente a ${nf(ocUlt.miami, 1)} % en Miami, ${nf(ocUlt.tampa, 1)} % en Tampa y ${nf(ocUlt.jacksonville, 1)} % en Jacksonville. Por eso un golpe al turismo (como en 2020) pega más aquí.`);
$("#f-ociopares").innerHTML = chip("fred_ces", "participacion_ocio_<área>", ocio.vigencia);
const ocultosOc = new Set();
const dibOcP = () => lineas($("#g-ociopares"), {series: OCP.filter(([k]) => !ocultosOc.has(k) || k === "orlando").map(([k, n, c, yo]) => ({nombre: n, puntos: S("turismo", k === "orlando" ? "participacion_ocio_en_empleo" : `participacion_ocio_${k}`).filter(p => p[0] >= "2000"), color: c, resaltar: yo})),
  fmtX: s => fMes(s, true), fmtY: v => nf(v, 1) + NB + "%", fmtTick: (v, d) => nf(v, d) + NB + "%", etiquetas: true, aria: "Peso del ocio en el empleo por área"});
leyToggle($("#ley-ociopares"), OCP.slice(1), ocultosOc, dibOcP);
observar($("#g-ociopares"), dibOcP);
const ven = C("escucha", "vistas_ingles_12_meses"), pVen = C("escucha", "puesto_ingles_entre_pares").valor;
$("#r-escuchaen").textContent = nb(`En inglés, el idioma de la mayoría de visitantes, el artículo de Orlando tuvo ${nf(ven.valor)} visitas en 12 meses: ${pVen === 1 ? "el primero" : pVen === 2 ? "el segundo" : "puesto " + pVen} de las cuatro ciudades. En español queda por detrás de Miami.`);
$("#f-escuchaen").innerHTML = chip("wikimedia_pageviews", "vistas_ingles_<ciudad>", ven.vigencia);
const ESCEN = [["orlando", "Orlando", "var(--ink)", true], ["tampa", "Tampa", "var(--c1)"], ["miami", "Miami", "var(--c2)"], ["jacksonville", "Jacksonville", "var(--c3)"]];
const ocultosEn = new Set();
const dibEn = () => lineas($("#g-escuchaen"), {series: ESCEN.filter(([k]) => !ocultosEn.has(k) || k === "orlando").map(([k, n, c, yo]) => ({nombre: n, puntos: S("escucha", `vistas_ingles_${k}`), color: c, resaltar: yo})),
  fmtX: s => fMes(s, true), fmtY: v => nf(v) + " visitas", fmtTick: v => nf(v / 1000) + NB + "mil", cero: true, etiquetas: true, aria: "Visitas en Wikipedia en inglés"});
leyToggle($("#ley-escuchaen"), ESCEN.slice(1), ocultosEn, dibEn);
observar($("#g-escuchaen"), dibEn);

/* ================= CLIMA ================= */
$("#r-clima").textContent = fraseClima;
const diaDe = s => DIA[new Date(tiempo(s.slice(0, 10))).getUTCDay()];
function agruparDias() {
  const t = S("clima", "pronostico_temperatura"), ll = Object.fromEntries(S("clima", "pronostico_lluvia")), porDia = new Map();
  t.forEach(([h, temp]) => { const dia = h.slice(0, 10), hora = +h.slice(11, 13), deDia = hora >= 6 && hora < 18;
    if (!porDia.has(dia)) porDia.set(dia, {fecha: dia, nombre: diaDe(dia), max: null, min: null, lluvia: 0});
    const o = porDia.get(dia); if (deDia) o.max = temp; else o.min = temp; o.lluvia = Math.max(o.lluvia, ll[h] ?? 0); });
  return [...porDia.values()];
}
const diasC = agruparDias();
$("#ahora").innerHTML = `<div class="t">${nf(tAct.valor, 0)}<sup>°F</sup></div>
  <div style="display:grid;gap:8px;min-width:0;flex:1 1 260px"><p style="font-size:1.12rem"><b>${aC(tAct.valor)} °C</b> en Orlando el ${fDia(tAct.vigencia)}, según la estación cercana más reciente.</p>
  <span class="alerta ${alertas ? "mal" : "ok"}">${ic(alertas ? "alerta" : "ok")}${alertas ? `${alertas} alerta${alertas > 1 ? "s" : ""} vigente${alertas > 1 ? "s" : ""}` : "Sin alertas vigentes"}</span></div>
  <div style="display:flex;gap:8px;flex-direction:column">${chip("nws_api", "temperatura_actual", tAct.vigencia, "Temperatura")}${chip("nws_api", "alertas_activas", C("clima", "alertas_activas").vigencia, "Alertas")}</div>`;
$("#dias").innerHTML = diasC.map((d, i) => { const icono = d.lluvia >= 50 ? "lluvia" : d.lluvia >= 20 ? "nube-sol" : "sol", txt = d.lluvia >= 50 ? "Lluvia probable" : d.lluvia >= 20 ? "Posible lluvia" : "Poca lluvia", [, m, dd] = d.fecha.split("-").map(Number);
  return `<div class="card dia"><span class="nombre">${cap(d.nombre)}</span><span class="fecha">${dd} ${MES[m - 1]}${i === 0 ? " · día de la prueba" : ""}</span>${ic(icono, "ico i")}<span class="tt">${d.max ?? "–"}° <span>/ ${d.min ?? "–"}°</span></span><span class="c">${d.max != null ? aC(d.max) + "°" : "–"} / ${d.min != null ? aC(d.min) + "°" : "–"} C</span><span class="c">${txt}: ${d.lluvia} %</span><span class="lluvia" aria-hidden="true"><i style="width:${d.lluvia}%"></i></span></div>`; }).join("");
$("#f-clima2").innerHTML = chip("nws_api", "pronostico_lluvia", L.clima.probado, "Pronóstico");
$("#t-franjas").textContent = `${A0}–${A1}: cada año, un color`;
$("#r-franjas").textContent = `Cada franja es un año: azul si fue más frío que el promedio de todo el registro, rojo si fue más caliente. Los últimos 30 años promedian ${nf(p2.valor, 1)} °F, frente a ${nf(p1.valor, 1)} °F de los primeros 30 (${nf(difCal.valor, 1)} °F más).`;
$("#f-franjas").innerHTML = chip("noaa_gsoy", "temperatura_anual", ult(temps)[0]);
$("#vig-franjas").textContent = `De ${A0} (izquierda) a ${A1} (derecha) · estación Orlando International Airport${FALTAN_T.length ? ` · en gris, años sin dato completo (${FALTAN_T[0]}–${ult(FALTAN_T)})` : ""}`;
$("#ley-franjas").innerHTML = `<span><i style="background:var(--cold-3);height:10px"></i>Más frío</span><span><i style="background:var(--mid);height:10px"></i>Promedio</span><span><i style="background:var(--warm-3);height:10px"></i>Más caliente</span>`;
const fr = $("#franjas"); fr.setAttribute("viewBox", `0 0 ${ANIOS_T.length} 1`); fr.setAttribute("preserveAspectRatio", "none"); fr.style.height = "120px"; fr.setAttribute("aria-label", "Franjas de temperatura media anual de Orlando desde " + temps[0][0]);
fr.innerHTML = franjasSVG(120).replace(/^<svg[^>]*>|<\/svg>$/g, "");
fr.addEventListener("pointermove", e => { const r = fr.getBoundingClientRect(), y = ANIOS_T[Math.max(0, Math.min(ANIOS_T.length - 1, Math.floor((e.clientX - r.left) / r.width * ANIOS_T.length)))], v = TEMP_ANIO.get(y);
  mostrarGlobo(`<b>${y}</b><br>${v == null ? "Sin dato completo ese año" : `${nf(v, 1)} °F (${nf((v - 32) * 5 / 9, 1)} °C)<br><span class="s">${v >= MEDIA_T ? "+" : "\u2212"}${nf(Math.abs(v - MEDIA_T), 1)} °F frente al promedio del registro</span>`}`, e.clientX, e.clientY); });
fr.addEventListener("pointerleave", ocultarGlobo);
$("#ley-temp").innerHTML = `<span><i style="background:var(--accent)"></i>Media del año</span><span><i style="background:transparent;height:0;border-top:2px dashed var(--muted)"></i>Promedio ${p1.vigencia.replace("-", "–")}: ${nf(p1.valor, 1)}${NB}°F · ${p2.vigencia.replace("-", "–")}: ${nf(p2.valor, 1)}${NB}°F</span>`;
$("#f-temp").innerHTML = chip("noaa_gsoy", "temperatura_anual", ult(temps)[0]);
const [pa, pb] = p1.vigencia.split("-"), [pc, pd] = p2.vigencia.split("-");
observar($("#g-temp"), () => lineas($("#g-temp"), {series: [{nombre: "Media", puntos: temps, color: "var(--accent)"}], fmtX: s => s, fmtY: v => `${nf(v, 1)} °F (${nf((v - 32) * 5 / 9, 1)} °C)`, fmtTick: (v, d) => nf(v, d) + "°",
  refs: [{y: p1.valor, desde: pa, hasta: pb}, {y: p2.valor, desde: pc, hasta: pd}],
  notas: [{x: String(caliente.valor), texto: `${caliente.valor}`}], aria: "Temperatura media anual"}));
$("#f-lluvia").innerHTML = chip("noaa_gsoy", "lluvia_anual", ult(S("clima_historico", "lluvia_anual"))[0]);
const LLUVIA = new Map(S("clima_historico", "lluvia_anual").map(p => [+p[0], p[1]]));
observar($("#g-lluvia"), () => barras($("#g-lluvia"), {puntos: ANIOS_T.map(y => [String(y), LLUVIA.get(y) ?? null]), fmtX: s => s, fmtY: v => nf(v, 1) + " pulgadas (" + nf(v * 25.4) + " mm)", aria: "Lluvia anual"}));
$("#notaClima").innerHTML = `<b>Dos fuentes, dos tiempos.</b> El clima de hoy es una foto del ${fDia(L.clima.probado)} (Servicio Meteorológico, en tiempo real). La historia sale de NOAA, año por año desde ${temps[0][0]}; los años sin dato completo quedan fuera. La diferencia entre periodos es de promedios, no una tendencia ajustada.`;

// ---------- v3: qué barrios están más expuestos (FEMA, Índice Nacional de Riesgo) ----------
const RIESGOS_V = [["rInund", "Inundación"], ["rHuracan", "Huracán"], ["rCalor", "Calor"], ["rTornado", "Tornado"], ["rVulner", "Vulnerabilidad social"]];
let riesgoSel = "rInund";
$("#segRiesgo").innerHTML = RIESGOS_V.map(([k, n]) => `<button type="button" data-k="${k}" aria-pressed="${k === riesgoSel}">${n}</button>`).join("");
const mapaRiesgo = mapaPlano($("#mapaRiesgo"), {valores: i => METRICAS[riesgoSel].v(B[i]) ?? null, ley: $("#leyRiesgo"), fmt: v => nf(v, 0), titulo: () => `${METRICAS[riesgoSel].nombre}, 0 a 100`, onClick: i => irABarrio(i),
  globo: i => `<b>${esc(B[i].nombre)}</b><br>${esc(METRICAS[riesgoSel].corto)}: ${nf(METRICAS[riesgoSel].v(B[i]) ?? 0, 0)} de 100<br><span class="s">Pérdida anual esperada (todos los peligros): ${usd(B[i].perdida ?? 0)}</span>`});
function pintarRiesgo() {
  mapaRiesgo.pintar();
  const filas = B.map((b, i) => ({nombre: b.nombre, valor: METRICAS[riesgoSel].v(b), i})).filter(f => f.valor != null).sort((a, b) => b.valor - a.valor);
  listaBarras($("#rankRiesgo"), filas.slice(0, 10), {fmt: v => nf(v, 0), max: 100, onClick: f => irABarrio(f.i)});
  const prom = C("riesgo", `${{rInund: "riesgo_inundacion", rHuracan: "riesgo_huracan", rCalor: "riesgo_calor", rTornado: "riesgo_tornado", rVulner: "vulnerabilidad_social"}[riesgoSel]}_promedio_barrios`).valor;
  $("#r-riesgo").textContent = nb(riesgoSel === "rVulner"
    ? `La vulnerabilidad social mide qué tan difícil le queda a la gente de un lugar prepararse y recuperarse (ingreso, edad, idioma, vivienda). La más alta: ${filas.slice(0, 3).map(f => f.nombre).join(", ")}. Donde coinciden mucho riesgo y mucha vulnerabilidad es donde un desastre pega más fuerte.`
    : `En ${METRICAS[riesgoSel].corto.toLowerCase()}, el barrio promedio de Orlando está en el puntaje ${nf(prom, 0)} de 100 (más alto que ${nf(prom, 0)} de cada 100 sectores del país). Los más expuestos: ${filas.slice(0, 3).map(f => f.nombre).join(", ")}.`);
}
$("#segRiesgo").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; riesgoSel = b.dataset.k; $$("#segRiesgo button").forEach(x => x.setAttribute("aria-pressed", x === b)); pintarRiesgo(); });
pintarRiesgo();
$("#notaRiesgo").innerHTML = nb(`<b>Qué es este puntaje.</b> El Índice Nacional de Riesgo de FEMA (versión ${esc(VIG_NRI)}) da a cada sector censal un percentil de 0 a 100 frente a todo el país. Lo llevamos a barrios promediando los sectores que lo tocan, ponderados por su población. FEMA estima además una pérdida anual esperada de ${usd(C("riesgo", "perdida_anual_esperada_ciudad").valor)} para los barrios de Orlando por todos los peligros. No es el mapa de zonas inundables de FEMA: su servidor no respondió y no lo reemplazamos por otra cosa.`) + " " + chip("fema_nri", "riesgo_<peligro>_barrio", VIG_NRI);

/* ================= FUENTES ================= */
const EST = {integrado: "En uso", candidato: "Candidata", excluido: "Descartada", caido: "No responde", inexistente: "No existe"};
const cuenta = {}; D.catalogo.forEach(f => cuenta[f.estado] = (cuenta[f.estado] || 0) + 1);
const ordenEst = ["integrado", "candidato", "excluido", "caido", "inexistente"].filter(k => cuenta[k]);
$("#r-fuentes").textContent = `Revisamos ${D.catalogo.length} fuentes sobre Orlando y ${cuenta.integrado} alimentan el tablero. Las demás no tienen licencia clara, no responden, piden llave o quedan como candidatas; lo que trae personas entra solo como conteos.`;
$("#embudo").setAttribute("aria-label", ordenEst.map(k => `${cuenta[k]} ${EST[k].toLowerCase()}`).join(", "));
$("#embudo").innerHTML = ordenEst.map(k => `<div class="e-${k}" style="flex:${cuenta[k]} 1 0" data-e="${k}" title="${EST[k]}: ${cuenta[k]}">${cuenta[k] >= 6 ? cuenta[k] : ""}</div>`).join("");
$("#leyEmbudo").innerHTML = ordenEst.map(k => `<span><i class="e-${k}"></i>${EST[k]}: <b>${cuenta[k]}</b></span>`).join("");
$("#embudo").addEventListener("click", e => { const d = e.target.closest("[data-e]"); if (d) { filtroEst = d.dataset.e; chipsEst(); fichas(); $("#fichas").scrollIntoView({behavior: "smooth", block: "start"}); } });
$("#notaVerif p").innerHTML = verOk ? `<b>Verificación automática:</b> antes de construir esta página, <span class="mono">verificar.py</span> pasó ${ver.pasan} comprobaciones con 0 fallos: fechas, licencias, rangos de cada tema, que no haya correos ni teléfonos, que ninguna celda por barrio esté bajo el umbral y que no aparezca ninguna categoría de la policía que decidimos excluir. Dejó ${ver.avisos} avisos: las fuentes de la ciudad no declaran licencia.` : `<b>Atención:</b> esta página se construyó ${esc(ver)}.`;
const porFicha = {}; D.fuentes_lago.forEach(f => (porFicha[f.ficha_excel] = porFicha[f.ficha_excel] || []).push(f));
$("#usadas").innerHTML = Object.entries(porFicha).sort((a, b) => a[0].localeCompare(b[0], "es", {numeric: true})).map(([fid, fs]) => { const fc = D.catalogo.find(c => c.id === fid) || {};
  const TN = {economia: "economía", codigo: "código urbano", clima_historico: "clima histórico", escucha: "interés en la web", empleo: "avisos de empleo"};
  const temas = fs.map(f => TN[TEMA_DE[f.id]] || TEMA_DE[f.id]).filter((v, i, a) => v && a.indexOf(v) === i).join(", "), lic = [...new Set(fs.map(f => f.licencia))].join(" · ");
  const probado = f => L[TEMA_DE[f.id]] ? L[TEMA_DE[f.id]].probado : "";
  // Una ficha con varias series (FRED) lista cada uso con su propia etiqueta de fuente; una ficha simple, un párrafo y una etiqueta
  const cuerpo = fs.length > 1 ? `<ul>${fs.map(f => `<li>${esc(cap(f.uso.split(" (")[0]))}${chip(f.id, "", probado(f))}</li>`).join("")}</ul>`
    : `<p>${esc(fs[0].uso.split(" (")[0])}</p><div class="chips">${chip(fs[0].id, "", probado(fs[0]))}</div>`;
  return `<article class="card usada${fs.length > 1 ? " varias" : ""}"><span class="id">${esc(fid)} · ${esc(temas)}${fs.length > 1 ? ` · ${fs.length} series` : ""}</span><h3>${esc(fc.nombre || fs[0].nombre)}</h3><p><b style="color:var(--ink)">Licencia:</b> ${esc(lic)}</p>${cuerpo}</article>`; }).join("");
const desc = D.catalogo.filter(f => f.estado === "excluido"), mot = {};
desc.forEach(f => mot[f.licencia || "no declara"] = (mot[f.licencia || "no declara"] || 0) + 1);
$("#txtDescarte").textContent = `Las ${desc.length} fuentes descartadas, según lo que declara cada una sobre su licencia. Casi todas son plataformas privadas que no dejan reutilizar sus datos.`;
barrasSimples($("#motivos"), Object.entries(mot).sort((a, b) => b[1] - a[1]).map(([k, n]) => [cap(k), n]));
const per = {}; D.catalogo.forEach(f => per[f.personas || "no declara"] = (per[f.personas || "no declara"] || 0) + 1);
barrasSimples($("#personas"), Object.entries(per).sort((a, b) => b[1] - a[1]).map(([k, n]) => [cap(k), n]));
let filtroEst = "todas", textoFicha = "", verTodas = false;
function chipsEst() { $("#chipsEstado").innerHTML = [["todas", "Todas", D.catalogo.length], ...ordenEst.map(k => [k, EST[k], cuenta[k]])].map(([k, t, n]) => `<button type="button" class="chip" data-e="${k}" aria-pressed="${filtroEst === k}">${t} · ${n}</button>`).join(""); }
function fichas() {
  const t = textoFicha.toLowerCase(), lista = D.catalogo.filter(f => (filtroEst === "todas" || f.estado === filtroEst) && (!t || `${f.id} ${f.nombre} ${f.entidad}`.toLowerCase().includes(t)));
  const LIM = 12, cortar = !verTodas && lista.length > LIM + 3;
  $("#cuentaFichas").textContent = `${lista.length} ${lista.length === 1 ? "ficha" : "fichas"}${cortar ? `, se ven las primeras ${LIM}` : ""}. Toca una para ver su licencia, cuándo la probamos y la nota del equipo.`;
  $("#fichas").innerHTML = (cortar ? lista.slice(0, LIM) : lista).map(f => `<details class="ficha"><summary><span class="fid">${esc(f.id)}</span><span class="fnom">${esc(f.nombre)}</span><span class="pill e-${f.estado}">${EST[f.estado] || esc(f.estado)}</span><span class="fent">${esc(f.entidad)}</span></summary>
    <div class="cuerpo"><dl><div><dt>Licencia</dt><dd>${esc(f.licencia || "no declara")}</dd></div><div><dt>Formato · acceso</dt><dd>${esc(f.formato)} · ${esc(f.como_se_obtiene)}</dd></div><div><dt>¿Datos de personas?</dt><dd>${esc(f.personas)}</dd></div><div><dt>Cobertura</dt><dd>${esc(f.cobertura)}</dd></div><div><dt>Periodo · frecuencia</dt><dd>${esc(f.vigencia)} · ${esc(f.frecuencia)}</dd></div><div><dt>Probada el</dt><dd>${esc(f.probado || "—")}</dd></div></dl>
    ${f.url ? `<p class="mono" style="overflow-wrap:anywhere"><a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.url)}</a></p>` : ""}${f.nota ? `<p class="obs">${esc(f.nota)}</p>` : ""}</div></details>`).join("")
    + (cortar ? `<button type="button" class="btn" id="verTodas" style="justify-self:start">Mostrar las ${lista.length - LIM} restantes</button>` : "");
}
$("#chipsEstado").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; filtroEst = b.dataset.e; verTodas = false; chipsEst(); fichas(); });
$("#fichas").addEventListener("click", e => { if (e.target.closest("#verTodas")) { verTodas = true; fichas(); } });
$("#buscarFicha").addEventListener("input", e => { textoFicha = e.target.value; fichas(); });
chipsEst(); fichas();
$("#bitacora").innerHTML = D.bitacora.map(b => `<details><summary><span class="mono" style="color:var(--muted)">${esc(b.n)}</span><span>${esc(b.encargo)}</span><span class="r-${esc(b.resultado)}" style="font-size:.85rem">${esc(b.resultado || "—")}</span></summary>
  <div class="det"><p><b style="color:var(--ink)">Qué respondió:</b> ${esc(b.respuesta)}</p><p><b style="color:var(--ink)">Cómo lo comprobamos:</b> ${esc(b.comprobacion)}</p><p><b style="color:var(--ink)">Qué aprendimos:</b> ${esc(b.aprendizaje)}</p>${b.fuentes ? `<p class="mono">Fichas: ${esc(b.fuentes)}</p>` : ""}</div></details>`).join("");
$("#tablaDic tbody").innerHTML = D.diccionario.map(r => `<tr><td class="mono">${esc(r.fuente)}</td><td class="mono" style="overflow-wrap:anywhere">${esc(r.campo)}</td><td>${esc(r.significado)}</td><td>${esc(r.clasificacion)}</td></tr>`).join("");
$("#sumDic").textContent = `Ver los ${D.diccionario.length} campos`;

/* ================= DECIDIR: cuatro perfiles, cada uno con su regla a la vista ================= */
// Percentil de 0 a 100 de cada valor dentro de una lista (empates al medio); null queda null
function percentiles(vals) {
  const ord = vals.filter(v => v != null).sort((a, b) => a - b), n = ord.length;
  return vals.map(v => { if (v == null || n < 2) return v == null ? null : 50; let lo = 0; while (lo < n && ord[lo] < v) lo++; let hi = lo; while (hi < n && ord[hi] === v) hi++; return ((lo + hi - 1) / 2) / (n - 1) * 100; });
}
const sumaB = (lista, f) => lista.reduce((s, b) => s + (f(b) || 0), 0);
const promPond = (lista, f, w) => { let a = 0, t = 0; for (const b of lista) { const v = f(b), p = w(b); if (v != null && p) { a += v * p; t += p; } } return t ? a / t : null; };
const personasCerca = b => (b.pob || 0) + (b.emp17 || 0);
const conIncentivo = b => (b.zo || 0) >= 5 || (b.mainSt || 0) >= 5 || (b.cra || 0) >= 5;
const etiquetasIncentivo = b => [(b.zo || 0) >= 5 ? "Zona de Oportunidad" : "", (b.mainSt || 0) >= 5 ? "Main Street" : "", (b.cra || 0) >= 5 ? "CRA" : ""].filter(Boolean);
const CIUDAD = {
  pob: sumaB(B, b => b.pob), personas: sumaB(B, personasCerca), delitos: sumaB(B, b => b.delitos[U_DEL]), quejas: sumaB(B, b => b.quejas),
  ingreso: C("censo", "ingreso_mediano_ciudad").valor, arriendo: C("censo", "arriendo_mediano_ciudad").valor,
};
const ZORI_HOY = C("vivienda", "arriendo_tipico_ultimo_mes").valor;
const FACTOR_ARRIENDO = ZORI_HOY / CIUDAD.arriendo;        // del promedio del censo (2020-2024) al arriendo típico de hoy
const pesoCtrl = (id, f, v) => `<div class="prioridad"><label for="${id}">${esc(f.n)}<span class="peq" style="font-weight:400"> · ${esc(f.desc)}</span></label><output id="o-${id}">${["no importa", "poco", "importa", "mucho"][v]}</output><input type="range" id="${id}" min="0" max="3" step="1" value="${v}" data-f="${f.k}"></div>`;
const recoHTML = (k, i, puntaje, bullets, extra = "") => `<div class="reco"><span class="n">${k}</span><div><h4>${esc(B[i].nombre)}</h4><span class="vig">Distrito ${B[i].distrito}${B[i].pob != null ? ` · ${nf(B[i].pob)} habitantes (est.)` : ""}</span>
  ${etiquetasIncentivo(B[i]).length ? `<div class="etiquetas-b" style="margin-top:4px">${etiquetasIncentivo(B[i]).map(t => `<span class="etq-z">${t}</span>`).join("")}</div>` : ""}
  <ul>${bullets.filter(Boolean).map(t => `<li>${t}</li>`).join("")}</ul></div><span class="puntaje"><b>${nf(puntaje, 0)}</b>de 100</span>
  <div class="acciones-r"><button class="btn" type="button" data-ir="${i}">${ic("mapa")}Ver en el mapa</button><a class="btn" href="#comparar/barrios/${i}">${ic("comparar")}Comparar</a>${extra}</div></div>`;
function puntuar(lista, factores, pesos) {
  // factores: {k: [valor por barrio de la lista, sentido (+1 más es mejor, −1 menos es mejor)]}
  const p = {};
  for (const [k, [vals, dir]] of Object.entries(factores)) p[k] = percentiles(vals).map(x => x == null ? 50 : dir > 0 ? x : 100 - x);
  const tot = Object.keys(factores).reduce((s, k) => s + (pesos[k] || 0), 0) || 1;
  return lista.map((_, j) => Object.keys(factores).reduce((s, k) => s + p[k][j] * (pesos[k] || 0), 0) / tot);
}

// ---------- perfil 1: emprender ----------
const GIROS = [{k: "restaurantes", n: "Restaurante", un: "un restaurante"}, {k: "comercio", n: "Tienda o comercio", un: "una tienda o comercio"}, {k: "belleza", n: "Salón de belleza", un: "un salón de belleza"},
  {k: "profesionales", n: "Oficina de servicios", un: "una oficina de servicios"}, {k: "hospedajes", n: "Hospedaje", un: "un hospedaje"}];
const FACT_EMP = [{k: "demanda", n: "Mucha gente cerca", desc: "residentes y empleos"}, {k: "competencia", n: "Poca competencia", desc: "del mismo tipo por cada 10.000 personas"},
  {k: "ingreso", n: "Clientes con buen ingreso", desc: "ingreso mediano"}, {k: "futuro", n: "Zona que va a crecer", desc: "residentes y empleos a 2045"},
  {k: "seguridad", n: "Seguridad", desc: "casos de policía por cada 1.000 personas"}];
const stEmp = {giro: "restaurantes", pesos: {demanda: 3, competencia: 3, ingreso: 2, futuro: 1, seguridad: 2}, incentivos: false};
function evaluarEmprender() {
  const lista = B.filter(b => personasCerca(b) >= 1500 && (!stEmp.incentivos || conIncentivo(b)));
  const comp = b => ((b[stEmp.giro] ?? 2) / personasCerca(b)) * 10000;            // «sin dato» = menos de 5: se cuenta como 2
  const fut = b => (b.pob17 || 0) + (b.emp17 || 0) >= 500 ? ((b.pob45 || 0) + (b.emp45 || 0)) / ((b.pob17 || 0) + (b.emp17 || 0)) - 1 : null;
  const seg = b => ((b.delitos[U_DEL] ?? 2) / personasCerca(b)) * 1000;
  const fact = {demanda: [lista.map(personasCerca), 1], competencia: [lista.map(comp), -1], ingreso: [lista.map(b => b.ingreso ?? null), 1],
    futuro: [lista.map(fut), 1], seguridad: [lista.map(seg), -1]};
  const pts = puntuar(lista, fact, stEmp.pesos);
  const giroTot = sumaB(B, b => b[stEmp.giro]);
  return {lista: lista.map((b, j) => ({i: b._i, p: pts[j], comp: comp(b), fut: fut(b), seg: seg(b)})).sort((a, b) => b.p - a.p),
    compCiudad: giroTot / CIUDAD.personas * 10000, segCiudad: CIUDAD.delitos / CIUDAD.personas * 1000, giroTot};
}
function panelEmprender(el) {
  const giro = GIROS.find(g => g.k === stEmp.giro), r = evaluarEmprender(), top = r.lista.slice(0, 5);
  const ap = sumaB(B, b => b.aperturas);
  el.innerHTML = `<div class="decidir-top">
    <div class="card controles-dec">
      <div class="grupo"><b>¿Qué negocio?</b><div class="chips">${GIROS.map(g => `<button type="button" class="chip" data-giro="${g.k}" aria-pressed="${g.k === stEmp.giro}">${g.n}</button>`).join("")}</div></div>
      <div class="grupo"><b>¿Qué te importa?</b>${FACT_EMP.map(f => pesoCtrl("pe-" + f.k, f, stEmp.pesos[f.k])).join("")}</div>
      <label class="casilla"><input type="checkbox" id="pe-inc" ${stEmp.incentivos ? "checked" : ""}><span>Solo barrios con incentivos: <button class="term" type="button" data-term="zona">Zona de Oportunidad</button>, Main Street o Área de Redesarrollo (CRA)</span></label>
      <details class="como-calc"><summary>Cómo se calcula</summary><ul>
        <li>Entran los barrios con al menos 1.500 personas cerca (residentes estimados por el censo más empleos de la proyección de la ciudad).</li>
        <li>Cada factor se vuelve un puntaje de 0 a 100 según el puesto del barrio; «poca competencia» y «seguridad» se invierten (menos es mejor).</li>
        <li>El puntaje final es el promedio ponderado con tus prioridades. Un barrio con menos de 5 ${esc(METRICAS[stEmp.giro].frase)} cuenta como 2.</li></ul></details>
    </div>
    <div class="panel">
      <div class="barra-graf"><h3>Dónde abrir ${esc(giro.un)}: los 5 barrios que mejor encajan</h3><span class="vig">${r.lista.length} barrios evaluados</span></div>
      <div class="recos">${top.map((x, k) => { const b = B[x.i]; const nGiro = b[stEmp.giro];
        return recoHTML(k + 1, x.i, x.p, [
          `${nf(b.pob || 0)} residentes y ${nf(b.emp17 || 0)} empleos cerca (estimados)`,
          nGiro == null ? `Menos de 5 ${esc(METRICAS[stEmp.giro].frase)} con licencia: casi sin competencia directa` : `${nf(nGiro)} ${esc(METRICAS[stEmp.giro].frase)} con licencia: ${nf(x.comp, 1)} por cada 10.000 personas (ciudad: ${nf(r.compCiudad, 1)})`,
          b.ingreso != null ? `Ingreso mediano de los hogares ≈ ${usd(b.ingreso)} (ciudad: ${usd(CIUDAD.ingreso)})` : "",
          x.fut != null ? `Personas proyectadas a 2045: ${crecF(x.fut * 100)} frente a 2017` : "",
          `${nf(x.seg, 1)} casos de policía por cada 1.000 personas (ciudad: ${nf(r.segCiudad, 1)})`]); }).join("")}</div>
    </div></div>
    <div class="grid-2"><article class="card panel"><div class="barra-graf"><h3>Puntaje de cada barrio para ${esc(giro.un)}</h3></div><svg class="svgmapa" id="mapaEmp" role="img" aria-label="Mapa del puntaje para emprender"></svg><div class="ley-mapa" id="leyEmp"></div></article>
      <article class="card panel"><h3>El contexto para emprender</h3><div class="senales">
        <div class="senal"><span class="t">Solicitudes de negocio en Florida (12 meses)</span><span class="v">${nf(C("economia", "solicitudes_negocio_florida_12_meses").valor)}</span><span class="c">${pct(C("economia", "variacion_solicitudes_negocio_florida").valor)} frente al año anterior</span></div>
        <div class="senal"><span class="t">Negocios que abrieron en Orlando en ${U_AP}</span><span class="v">${nf(ap)}</span><span class="c">en barrios con 5 o más aperturas</span></div>
        <div class="senal"><span class="t">Salario por hora (costo laboral)</span><span class="v">US$${NB}${nf(C("economia", "salario_hora_ultimo_mes").valor, 2)}</span><span class="c">${pct(C("economia", "salario_frente_a_pares").valor, 0)} frente a Tampa, Miami y Jacksonville</span></div>
        <div class="senal"><span class="t">Empleo en ocio y hotelería</span><span class="v">${nf(ocio.valor, 1)}${NB}%</span><span class="c">${C("turismo", "puesto_ocio_entre_pares").valor === 1 ? "el área más turística de las cuatro que comparamos" : "puesto " + C("turismo", "puesto_ocio_entre_pares").valor + " de 4 áreas"}</span></div></div>
        <div class="chips-f">${chip("fred_bfs", "solicitudes_negocio_florida", C("economia", "solicitudes_negocio_florida_12_meses").vigencia)}${chip("orlando_negocios", `${stEmp.giro}_barrio`, VIG_NEG)}${chip("orlando_sig", "empleo_2017_barrio", L.planeacion.probado)}</div></article></div>
    <div class="limites"><b>Lo que esto no sabe</b><ul><li>El arriendo de locales comerciales y el tráfico de gente frente al local: no hay datos abiertos.</li><li>La competencia que está fuera de la ciudad (Disney, Universal y gran parte de International Drive están en el condado, no en Orlando).</li><li>Una licencia no es un local: un negocio puede tener varias, y las de menos de 5 por barrio no se publican.</li>${stEmp.giro === "hospedajes" ? "<li>Para hospedaje, la demanda la ponen los turistas, no los vecinos: mira también la cercanía a parques temáticos y al aeropuerto.</li>" : ""}</ul></div>`;
  const mapa = new Map(r.lista.map(x => [x.i, x.p]));
  mapaPlano($("#mapaEmp"), {valores: i => mapa.get(i) ?? null, ley: $("#leyEmp"), fmt: v => nf(v, 0), titulo: () => "Puntaje (0 a 100)", onClick: i => irABarrio(i),
    globo: i => `<b>${esc(B[i].nombre)}</b><br>${mapa.has(i) ? "Puntaje: " + nf(mapa.get(i), 0) + " de 100" : "No evaluado (menos de 1.500 personas cerca o sin incentivo)"}`});
  el.querySelectorAll("[data-giro]").forEach(b => b.onclick = () => { stEmp.giro = b.dataset.giro; panelEmprender(el); });
  el.querySelectorAll(".prioridad input[type=range]").forEach(inp => inp.oninput = () => { stEmp.pesos[inp.dataset.f] = +inp.value; panelEmprender(el); requestAnimationFrame(() => { const n = $("#" + inp.id); if (n) n.focus(); }); });
  $("#pe-inc").onchange = e => { stEmp.incentivos = e.target.checked; panelEmprender(el); };
}

// ---------- perfil 2: vivir ----------
const FACT_VIV = [{k: "seguridad", n: "Seguridad", desc: "casos por cada 1.000 habitantes"}, {k: "tranquilidad", n: "Tranquilidad", desc: "quejas de vecinos por 1.000 hab."},
  {k: "parques", n: "Parques", desc: "parte del barrio que es parque"}, {k: "colegios", n: "Colegios públicos", desc: "dentro del barrio"},
  {k: "sinCarro", n: "Moverse sin carro", desc: "ciclovías y SunRail"}, {k: "inundacion", n: "Poco riesgo de inundación", desc: "índice de FEMA"},
  {k: "espanol", n: "Comunidad hispanohablante", desc: "hablan español en casa"}];
const stViv = {presupuesto: Math.round(ZORI_HOY / 50) * 50, pesos: {seguridad: 3, tranquilidad: 2, parques: 1, colegios: 1, sinCarro: 0, inundacion: 2, espanol: 0}};
function evaluarVivir() {
  const base = B.filter(b => b.pob >= MIN_HAB && b.arriendo != null);
  const fact = {seguridad: [base.map(b => porHab(b.delitos[U_DEL] ?? 2, b)), -1], tranquilidad: [base.map(b => porHab(b.quejas ?? 2, b)), -1],
    parques: [base.map(b => (b.parquesKm2 || 0) / b.km2), 1], colegios: [base.map(b => b.colegios || 0), 1],
    sinCarro: [base.map(b => (b.ciclo || 0) / b.km2 + (b.sunrail || 0) * 2), 1], inundacion: [base.map(b => b.rInund ?? null), -1], espanol: [base.map(b => b.espanol ?? null), 1]};
  const pts = puntuar(base, fact, stViv.pesos);
  const todos = base.map((b, j) => ({i: b._i, p: pts[j], hoy: b.arriendo * FACTOR_ARRIENDO}));
  return {todos, caben: todos.filter(x => x.hoy <= stViv.presupuesto).sort((a, b) => b.p - a.p)};
}
function panelVivir(el) {
  const r = evaluarVivir(), top = r.caben.slice(0, 6), anual = stViv.presupuesto * 12 / .3, hora = anual / 2080, salH = C("economia", "salario_hora_ultimo_mes").valor;
  el.innerHTML = `<div class="decidir-top">
    <div class="card controles-dec">
      <div class="grupo rango"><label for="pv-pres"><b>¿Cuánto puedes pagar de arriendo al mes?</b></label><output id="o-pv-pres">${usd(stViv.presupuesto)}</output><input type="range" id="pv-pres" min="800" max="4000" step="50" value="${stViv.presupuesto}"></div>
      <div class="senal"><span class="t">Para que el arriendo no pase del 30 % de tu ingreso necesitas ganar</span><span class="v">${usd(Math.round(anual / 100) * 100)} al año</span>
        <span class="c">≈ US$${NB}${nf(hora, 2)} la hora a tiempo completo: ${Math.abs(hora / salH - 1) < .03 ? "casi lo mismo que" : hora > salH ? nf((hora / salH - 1) * 100, 0) + " % más que" : nf((1 - hora / salH) * 100, 0) + " % menos que"} el salario promedio del sector privado en el área (US$${NB}${nf(salH, 2)}).</span></div>
      <div class="grupo"><b>¿Qué te importa?</b>${FACT_VIV.map(f => pesoCtrl("pv-" + f.k, f, stViv.pesos[f.k])).join("")}</div>
      <details class="como-calc"><summary>Cómo se calcula</summary><ul>
        <li>El arriendo de cada barrio es la mediana del censo 2020–2024, llevada a hoy con el arriendo típico de Zillow: × ${nf(FACTOR_ARRIENDO, 2)} (${usd(ZORI_HOY)} hoy frente a ${usd(CIUDAD.arriendo)} en el censo). Es una aproximación.</li>
        <li>Entran los barrios con ${MIN_HAB} habitantes o más y arriendo estimado igual o menor a tu presupuesto.</li>
        <li>Cada prioridad es un puntaje de 0 a 100 según el puesto del barrio entre todos; se promedian con tus pesos.</li></ul></details>
    </div>
    <div class="panel">
      <div class="barra-graf"><h3>${r.caben.length > 1 ? `${r.caben.length} barrios caben en ${usd(stViv.presupuesto)}: ${r.caben.length > 6 ? "estos encajan mejor contigo" : "así encajan contigo"}` : r.caben.length ? `Solo 1 barrio cabe en ${usd(stViv.presupuesto)}` : "Con ese presupuesto no cabe ningún barrio"}</h3><span class="vig">${r.todos.length} barrios con estimación</span></div>
      ${r.caben.length ? `<div class="recos">${top.map((x, k) => { const b = B[x.i];
        return recoHTML(k + 1, x.i, x.p, [
          `Arriendo estimado hoy ≈ ${usd(Math.round(x.hoy / 10) * 10)} al mes (mediana del censo: ${usd(b.arriendo)})`,
          b.delitos[U_DEL] != null ? `${nf(porHab(b.delitos[U_DEL], b), 1)} casos de policía por 1.000 habitantes (ciudad: ${nf(CIUDAD.delitos / CIUDAD.pob * 1000, 1)})` : "Menos de 5 casos de policía en el año",
          b.quejas != null ? `${nf(porHab(b.quejas, b), 1)} quejas de vecinos por 1.000 habitantes` : "Menos de 5 quejas de vecinos en el año",
          `${b.parques ? nf(b.parques) + " parque" + (b.parques > 1 ? "s" : "") : "Sin parque de la ciudad adentro"}${b.colegios ? " · " + nf(b.colegios) + " colegio" + (b.colegios > 1 ? "s" : "") + " público" + (b.colegios > 1 ? "s" : "") : ""}${b.sunrail ? " · estación de SunRail" : ""}`,
          b.rInund != null ? `Riesgo de inundación: ${nf(b.rInund, 0)} de 100 (FEMA)` : "",
          b.espanol != null && stViv.pesos.espanol ? `${nf(b.espanol, 0)} % habla español en casa` : ""]); }).join("")}</div>`
        : `<div class="limites"><b>Sube el presupuesto.</b> El barrio más barato con estimación arrienda hoy por ≈ ${usd(Math.round(Math.min(...r.todos.map(x => x.hoy)) / 10) * 10)} al mes.</div>`}
    </div></div>
    <div class="limites"><b>Lo que esto no sabe</b><ul><li>El arriendo de un apartamento concreto: la mediana del barrio mezcla todo tipo de vivienda.</li><li>Ruido, tráfico, estado de las calles o qué tan bonito es: no hay datos abiertos por barrio.</li><li>La calidad de los colegios (solo sabemos dónde están).</li><li>Los casos de policía cuentan reportes, no delitos comprobados; en zonas comerciales los genera también quien no vive allí.</li></ul></div>`;
  $("#pv-pres").oninput = e => { stViv.presupuesto = +e.target.value; panelVivir(el); requestAnimationFrame(() => $("#pv-pres") && $("#pv-pres").focus()); };
  el.querySelectorAll(".prioridad input[type=range]").forEach(inp => inp.oninput = () => { stViv.pesos[inp.dataset.f] = +inp.value; panelVivir(el); requestAnimationFrame(() => { const n = $("#" + inp.id); if (n) n.focus(); }); });
}

// ---------- perfil 3: comprar o invertir ----------
const CONDADO_DE = {orlando: "orange", tampa: "hillsborough", miami: "miami_dade", jacksonville: "duval"};
const zUltimo = c => ult(S("vivienda", `valor_tipico_${c}`))[1], rUltimo = c => ult(S("vivienda", `arriendo_tipico_${c}`))[1];
const aniosIngreso = c => zUltimo(c) / ult(S("gente", `ingreso_mediano_${CONDADO_DE[c]}`))[1];
const rentab = c => rUltimo(c) * 12 / zUltimo(c) * 100;
const FACT_INV = [{k: "crecimiento", n: "Crecimiento proyectado", desc: "residentes y empleos a 2045"}, {k: "proyectos", n: "Proyectos en camino", desc: "planes maestros, subdivisiones, rezonificaciones"},
  {k: "precio", n: "Precio de entrada bajo", desc: "valor de vivienda del censo"}, {k: "riesgo", n: "Poco riesgo", desc: "inundación y huracán (FEMA)"}];
const stInv = {pesos: {crecimiento: 3, proyectos: 2, precio: 2, riesgo: 2}};
function panelInvertir(el) {
  const m = SM.orlando, color = m.nivel === "comprador" ? "var(--good)" : m.nivel === "vendedor" ? "var(--bad)" : "var(--warn)";
  const base = B.filter(b => b.pob >= MIN_HAB && b.valor != null);
  const fact = {crecimiento: [base.map(b => (b.pob17 || 0) + (b.emp17 || 0) >= 500 ? ((b.pob45 || 0) + (b.emp45 || 0)) / ((b.pob17 || 0) + (b.emp17 || 0)) : null), 1],
    proyectos: [base.map(b => (b.grandes || 0) + (b.permisos[U_PERM] || 0) / 100), 1], precio: [base.map(b => b.valor), -1],
    riesgo: [base.map(b => b.rInund != null ? Math.max(b.rInund, b.rHuracan ?? 0) : null), -1]};
  const pts = puntuar(base, fact, stInv.pesos), lista = base.map((b, j) => ({i: b._i, p: pts[j]})).sort((a, b) => b.p - a.p).slice(0, 6);
  const METROS4 = ["orlando", "tampa", "miami", "jacksonville"], NOM = {orlando: "Orlando", tampa: "Tampa", miami: "Miami", jacksonville: "Jacksonville"};
  el.innerHTML = `<div class="veredicto"><span class="bola" style="background:${color}">${ic(m.nivel === "vendedor" ? "sube" : m.nivel === "comprador" ? "baja" : "igual")}</span><div><span class="vig">Mercado de vivienda del área de Orlando · ${fMes(m.mes, true)}</span><br><b>${m.veredicto}: cumple ${m.n} de 4 señales a favor de quien compra</b></div></div>
    <div class="senales">
      <div class="senal"><span class="t">Precio de lista (mediana)</span><span class="v">${usd(m.precioNivel)}</span><span class="c">${pct(m.precio)} en un año</span></div>
      <div class="senal"><span class="t">Días para vender (mediana)</span><span class="v">${nf(m.dias)}</span><span class="c">hace un año: ${nf(m.diasAntes)}</span></div>
      <div class="senal"><span class="t">Viviendas en venta con rebaja</span><span class="v">${nf(m.rebaja, 0)}${NB}%</span><span class="c">el mes pasado bajaron de precio</span></div>
      <div class="senal"><span class="t">Años de ingreso para comprar</span><span class="v">${nf(aniosIngreso("orlando"), 1)}</span><span class="c">valor típico ÷ ingreso mediano de un hogar de Orange</span></div>
      <div class="senal"><span class="t">Rentabilidad bruta del arriendo</span><span class="v">${nf(rentab("orlando"), 1)}${NB}%</span><span class="c">al año, antes de impuestos, seguro y mantenimiento</span></div></div>
    <div class="tabla-wrap card"><table><thead><tr><th>Área</th><th class="n">Valor típico</th><th class="n">Arriendo típico</th><th class="n">Años de ingreso</th><th class="n">Rentabilidad bruta</th><th>Mercado</th></tr></thead><tbody>
      ${METROS4.map(c => `<tr${c === "orlando" ? ' style="font-weight:700"' : ""}><td>${NOM[c]}</td><td class="n">${usd(zUltimo(c))}</td><td class="n">${usd(rUltimo(c))}</td><td class="n">${nf(aniosIngreso(c), 1)}</td><td class="n">${nf(rentab(c), 1)}${NB}%</td><td>${SM[c].veredicto}</td></tr>`).join("")}
    </tbody></table><p class="vig" style="margin-top:6px">Valor y arriendo típicos: Zillow (área metropolitana). Ingreso: mediana de los hogares del condado principal de cada área (Census, ${ult(S("gente", "ingreso_mediano_orange"))[0]}).</p>${chip("zillow_research", "valor_tipico_<área>", C("vivienda", "valor_tipico_ultimo_mes").vigencia)} ${chip("fred_realtor", "rebajas", m.mes)}</div>
    <div class="decidir-top">
      <div class="card controles-dec"><div class="grupo"><b>¿Qué buscas en un barrio para comprar?</b>${FACT_INV.map(f => pesoCtrl("pi-" + f.k, f, stInv.pesos[f.k])).join("")}</div>
        <details class="como-calc"><summary>Cómo se calcula</summary><ul><li>Crecimiento: personas (residentes y empleos) proyectadas por la ciudad a 2045 sobre las de 2017.</li><li>Proyectos: solicitudes grandes de los dos últimos años más los permisos emitidos (cada 100 permisos cuentan como una solicitud).</li><li>Precio: valor declarado por los dueños en el censo (más bajo, mejor puntaje).</li><li>Riesgo: el mayor entre inundación y huracán del índice de FEMA.</li></ul></details></div>
      <div class="panel"><div class="barra-graf"><h3>Barrios para mirar si piensas comprar</h3><span class="vig">${base.length} barrios con estimación</span></div>
        <div class="recos">${lista.map((x, k) => { const b = B[x.i]; return recoHTML(k + 1, x.i, x.p, [
          `Valor de la vivienda propia ≈ ${usd(b.valor)} (censo, aprox.)`,
          b.crec45 != null ? `Residentes proyectados a 2045: ${crecF(b.crec45)}` : "",
          b.grandes ? `${nf(b.grandes)} solicitudes de proyectos grandes en dos años` : "",
          b.permisos[U_PERM] ? `${nf(b.permisos[U_PERM])} permisos de construcción en ${U_PERM}` : "",
          b.rInund != null ? `Riesgo FEMA: inundación ${nf(b.rInund, 0)}, huracán ${nf(b.rHuracan, 0)} (de 100)` : ""]); }).join("")}</div></div></div>
    <div class="limites"><b>Esto no es asesoría financiera.</b><ul><li>No sabemos el precio de una casa concreta, su estado, los impuestos (HOA, predial) ni el costo del seguro, que en Florida pesa mucho.</li><li>Las proyecciones a 2045 son de la ciudad y pueden cambiar.</li><li>La rentabilidad bruta no descuenta vacancia, mantenimiento, seguro ni impuestos.</li></ul></div>`;
  el.querySelectorAll(".prioridad input[type=range]").forEach(inp => inp.oninput = () => { stInv.pesos[inp.dataset.f] = +inp.value; panelInvertir(el); requestAnimationFrame(() => { const n = $("#" + inp.id); if (n) n.focus(); }); });
}

// ---------- perfil 4: gobernar y planear ----------
const DISTRITOS = M.distritos.map(d => String(d.distrito)).sort((x, y) => x - y);
function agregado(lista) {
  const pob = sumaB(lista, b => b.pob), w = b => b.pob || 0;
  return {n: lista.length, pob, km2: sumaB(lista, b => b.km2), delitos: sumaB(lista, b => b.delitos[U_DEL]), delitosAntes: sumaB(lista, b => b.delitos[U_DEL - 1]),
    quejas: sumaB(lista, b => b.quejas), permisos: sumaB(lista, b => b.permisos[U_PERM]), negocios: sumaB(lista, b => b.negocios),
    pob17: sumaB(lista, b => b.pob17), pob45: sumaB(lista, b => b.pob45), parques: sumaB(lista, b => b.parques), colegios: sumaB(lista, b => b.colegios),
    ciclo: sumaB(lista, b => b.ciclo), abiertas: sumaB(lista, b => b.abiertas), zo: lista.filter(b => (b.zo || 0) >= 5).length,
    carga: promPond(lista, b => b.carga, w), sinCarro: promPond(lista, b => b.sinCarro, w), pobreza: promPond(lista, b => b.pobreza, w),
    ingreso: promPond(lista, b => b.ingreso, b => b.pob || 0), rInund: promPond(lista, b => b.rInund, w), rVulner: promPond(lista, b => b.rVulner, w), espanol: promPond(lista, b => b.espanol, w)};
}
const AG_CIUDAD = agregado(B);
const REGLAS = [
  {k: "seg", t: "Los casos de policía subieron", icono: "sirena", regla: `subieron 20 % o más entre ${U_DEL - 1} y ${U_DEL}, con al menos 50 casos`,
    f: b => { const a = b.delitos[U_DEL - 1], n = b.delitos[U_DEL]; return a && n && n >= 50 && n / a - 1 >= .2 ? `${b.nombre} (${pct((n / a - 1) * 100, 0)})` : null; }},
  {k: "arr", t: "Arriendo que ahoga", icono: "casa", regla: "65 % o más de los hogares que arriendan gastan 30 % o más de su ingreso en arriendo, en barrios de 1.000 habitantes o más",
    f: b => b.carga >= 65 && b.pob >= 1000 ? `${b.nombre} (${nf(b.carga, 0)}${NB}%)` : null},
  {k: "mov", t: "Sin carro y sin alternativas", icono: "tren", regla: "15 % o más de hogares sin carro, sin estación de SunRail y con menos de 1 km de ciclovía",
    f: b => b.sinCarro >= 15 && !b.sunrail && (b.ciclo || 0) < 1 ? `${b.nombre} (${nf(b.sinCarro, 0)}${NB}% sin carro)` : null},
  {k: "par", t: "Mucha gente y ningún parque", icono: "arbol", regla: "2.000 habitantes o más y ningún parque de la ciudad dentro del barrio",
    f: b => b.pob >= 2000 && !b.parques ? `${b.nombre} (${nf(b.pob)} hab.)` : null},
  {k: "rie", t: "Riesgo alto y gente vulnerable", icono: "gota", regla: "riesgo de inundación de 80 o más y vulnerabilidad social de 70 o más (FEMA, de 0 a 100)",
    f: b => b.rInund >= 80 && b.rVulner >= 70 ? `${b.nombre} (inundación ${nf(b.rInund, 0)}, vulnerabilidad ${nf(b.rVulner, 0)})` : null},
  {k: "cre", t: "Crecimiento que va a presionar los servicios", icono: "futuro", regla: "residentes proyectados a 2045 crecen 50 % o más sobre una base de 1.000 o más",
    f: b => b.crec45 >= 50 && (b.pob17 || 0) >= 1000 ? `${b.nombre} (${crecF(b.crec45)})` : null},
];
const alertasDe = lista => REGLAS.map(r => ({...r, barrios: lista.map(b => [b._i, r.f(b)]).filter(x => x[1])})).filter(r => r.barrios.length);
const stGob = {d: "todos"};
function panelGobernar(el) {
  const lista = stGob.d === "todos" ? B : B.filter(b => String(b.distrito) === stGob.d), a = agregado(lista), c = AG_CIUDAD, al = alertasDe(lista);
  const cmp = (v, ref, dir, f) => { if (v == null || ref == null || stGob.d === "todos") return ""; const d = (v / ref - 1) * 100; if (Math.abs(d) < 5 || !dir) return `<span class="c">ciudad: ${f(ref)}</span>`; const mejor = dir > 0 ? d > 0 : d < 0; return `<span class="c" style="color:${mejor ? "var(--good)" : "var(--bad)"}">${mejor ? "mejor" : "peor"} que la ciudad (${f(ref)})</span>`; };
  const tasa = (n, p) => p ? n / p * 1000 : null;
  const tarj = [
    ["Habitantes (estimado)", nf(a.pob), stGob.d === "todos" ? `<span class="c">${a.n} barrios</span>` : `<span class="c">${nf(a.pob / c.pob * 100, 0)} % de la ciudad · ${a.n} barrios</span>`],
    ["Crecimiento proyectado a 2045", crecF((a.pob45 / a.pob17 - 1) * 100), cmp((a.pob45 / a.pob17 - 1) * 100 + 100, (c.pob45 / c.pob17 - 1) * 100 + 100, 0, v => crecF(v - 100))],
    [`Casos de policía por 1.000 hab. (${U_DEL})`, nf(tasa(a.delitos, a.pob), 1), cmp(tasa(a.delitos, a.pob), tasa(c.delitos, c.pob), -1, v => nf(v, 1))],
    [`Cambio de casos ${U_DEL - 1} → ${U_DEL}`, pct((a.delitos / a.delitosAntes - 1) * 100, 0), cmp(a.delitos / a.delitosAntes, c.delitos / c.delitosAntes, -1, v => pct((v - 1) * 100, 0))],
    ["Quejas de vecinos por 1.000 hab.", nf(tasa(a.quejas, a.pob), 1), cmp(tasa(a.quejas, a.pob), tasa(c.quejas, c.pob), -1, v => nf(v, 1))],
    ["Carga de arriendo", nf(a.carga, 0) + NB + "%", cmp(a.carga, c.carga, -1, v => nf(v, 0) + NB + "%")],
    ["Hogares sin carro", nf(a.sinCarro, 1) + NB + "%", cmp(a.sinCarro, c.sinCarro, 0, v => nf(v, 1) + NB + "%")],
    ["Personas en pobreza", nf(a.pobreza, 1) + NB + "%", cmp(a.pobreza, c.pobreza, -1, v => nf(v, 1) + NB + "%")],
    ["Parques por 10.000 hab.", nf(a.parques / a.pob * 10000, 1), cmp(a.parques / a.pob, c.parques / c.pob, 1, v => nf(v * 10000, 1))],
    ["Solicitudes de planeación abiertas", nf(a.abiertas), `<span class="c">${a.zo} barrio${a.zo === 1 ? "" : "s"} en Zona de Oportunidad</span>`],
  ];
  el.innerHTML = `<div class="barra-graf"><div class="seg grande" id="segDistrito" role="group" aria-label="Distrito">${["todos", ...DISTRITOS].map(d => `<button type="button" data-d="${d}" aria-pressed="${d === stGob.d}">${d === "todos" ? "Toda la ciudad" : "Distrito " + d}</button>`).join("")}</div>
      <a class="btn" href="#comparar/distritos">${ic("comparar")}Comparar los 6 distritos</a></div>
    <div class="senales">${tarj.map(([t, v, c_]) => `<div class="senal"><span class="t">${t}</span><span class="v">${v}</span>${c_}</div>`).join("")}</div>
    <div class="barra-graf"><h3>${al.length ? `${al.length} alerta${al.length > 1 ? "s" : ""} ${stGob.d === "todos" ? "en la ciudad" : "en el distrito " + stGob.d}, ordenadas por cuántos barrios tocan` : "Sin alertas con estas reglas"}</h3><span class="vig">Cada alerta es una regla escrita: puedes discutirla</span></div>
    <div class="alertas">${al.sort((x, y) => y.barrios.length - x.barrios.length).map(r => `<div class="alerta-item"><h4>${ic(r.icono)}${esc(r.t)} · ${r.barrios.length}</h4><p>Regla: ${esc(r.regla)}.</p><div class="barrios-a">${r.barrios.slice(0, 8).map(([i, t]) => `<button type="button" data-ir="${i}">${esc(t)}</button>`).join("")}${r.barrios.length > 8 ? `<span class="vig">y ${r.barrios.length - 8} más</span>` : ""}</div></div>`).join("") || `<div class="alerta-item ok"><h4>${ic("ok")}Ningún barrio cumple las reglas</h4><p>Eso no quiere decir que no haya problemas: solo que no superan los umbrales escritos.</p></div>`}</div>
    <div class="grid-2"><article class="card panel"><div class="barra-graf"><h3>Dónde se concentran las alertas</h3></div><svg class="svgmapa" id="mapaAlertas" role="img" aria-label="Mapa de alertas por barrio"></svg><div class="ley-mapa" id="leyAlertas"></div></article>
      <article class="card panel"><h3>Qué usar para priorizar</h3><p class="peq">Las alertas mezclan seguridad (Policía de Orlando, ${U_DEL}), vivienda y movilidad (censo ${VIG_CEN.replace("-", "–")}, estimado por barrio), parques y SunRail (SIG de la ciudad), riesgo (FEMA) y crecimiento (proyección de la ciudad a 2045). Un barrio con varias alertas a la vez es candidato a mirar primero.</p>
        <div class="limites"><b>Lo que esto no sabe</b><ul><li>Las solicitudes al 311 y los baches, alumbrado o basuras: no están publicados.</li><li>El presupuesto y la inversión ya comprometida en cada barrio.</li><li>Las estimaciones por barrio del censo tienen margen de error, mayor en barrios pequeños.</li></ul></div></article></div>`;
  const cuenta = new Map(); for (const r of al) for (const [i] of r.barrios) cuenta.set(i, (cuenta.get(i) || 0) + 1);
  mapaPlano($("#mapaAlertas"), {valores: i => lista.includes(B[i]) ? (cuenta.get(i) || 0) : null, ley: $("#leyAlertas"), cortes: [1, 2, 3, 4], etiquetas: ["Ninguna", "1", "2", "3", "4 o más"], titulo: () => "Alertas por barrio", onClick: i => irABarrio(i),
    globo: i => `<b>${esc(B[i].nombre)}</b><br>${cuenta.get(i) ? cuenta.get(i) + " alerta" + (cuenta.get(i) > 1 ? "s" : "") + ": " + al.filter(r => r.barrios.some(x => x[0] === i)).map(r => r.t.toLowerCase()).join("; ") : "Sin alertas"}`});
  $("#segDistrito").onclick = e => { const b = e.target.closest("button"); if (b) { stGob.d = b.dataset.d; panelGobernar(el); } };
}

const PERFILES = [
  {k: "emprender", n: "Emprender", d: "Dónde abrir un negocio", icono: "tienda", fn: panelEmprender},
  {k: "vivir", n: "Vivir", d: "Qué barrio me conviene", icono: "casa", fn: panelVivir},
  {k: "invertir", n: "Comprar o invertir", d: "Cómo está el mercado", icono: "llave", fn: panelInvertir},
  {k: "gobernar", n: "Gobernar", d: "Qué atender primero", icono: "capitolio", fn: panelGobernar},
];
let perfil = "emprender";
function mostrarPerfil(k) {
  perfil = PERFILES.some(p => p.k === k) ? k : "emprender";
  $$("#perfiles button").forEach(b => b.setAttribute("aria-selected", b.dataset.p === perfil));
  PERFILES.find(p => p.k === perfil).fn($("#panelDecidir"));
}
$("#perfiles").innerHTML = PERFILES.map(p => `<button type="button" role="tab" data-p="${p.k}" aria-selected="${p.k === perfil}">${ic(p.icono)}<span>${p.n}<small>${p.d}</small></span></button>`).join("");
$("#perfiles").addEventListener("click", e => { const b = e.target.closest("button[data-p]"); if (b) history.replaceState(null, "", "#decidir/" + b.dataset.p), mostrarPerfil(b.dataset.p); });
$("#panelDecidir").addEventListener("click", e => { const b = e.target.closest("[data-ir]"); if (b) irABarrio(+b.dataset.ir); });
$("#r-decidir").textContent = "Elige qué quieres hacer. Cada perfil cruza las mismas fuentes del tablero con una regla escrita a la vista, y te dice también lo que no sabe.";

/* ================= COMPARAR: ciudades, distritos y barrios ================= */
const RIVALES = [["tampa", "Tampa"], ["miami", "Miami"], ["jacksonville", "Jacksonville"], ["florida", "Florida"], ["eeuu", "EE. UU."]];
const CONDADO_RIVAL = {orlando: "orange", tampa: "hillsborough", miami: "miami_dade", jacksonville: "duval", florida: "florida"};
const ultDe = (tema, k) => { const s_ = S(tema, k); return s_.length ? ult(s_)[1] : null; };
const enMes = (tema, k, mes) => { const s_ = S(tema, k); const p = s_.find(x => x[0] === mes); return p ? p[1] : null; };
const sufC = c => c === "orlando" ? "orlando" : c;
const FILAS_C = [
  {n: "Desempleo", ambito: "área metropolitana", dir: -1, f: v => nf(v, 1) + NB + "%", v: c => enMes("economia", `desempleo_${c}`, des.vigencia), fuente: "fred_laus", vig: des.vigencia},
  {n: "Salario por hora, sector privado", ambito: "área metropolitana", dir: 1, f: v => "US$" + NB + nf(v, 2), v: c => ultDe("economia", `salario_hora_${c}`), fuente: "fred_salarios", vig: sal.vigencia},
  {n: "Avisos de empleo (feb 2020 = 100)", ambito: "área metropolitana", dir: 1, f: v => nf(v, 1), v: c => c === "orlando" ? enMes("empleo", "indice_mensual", empU) : enMes("empleo", `indice_mensual_${c}`, empU), fuente: "indeed_hiring_lab", vig: empU},
  {n: "Ingreso mediano de los hogares", ambito: "ciudad", dir: 1, f: usdF, v: c => acsC("ingreso_mediano")[c], fuente: "censo_acs", vig: VIG_CEN},
  {n: "Ingreso por persona", ambito: "condado", dir: 1, f: usdF, v: c => CONDADO_RIVAL[c] ? ultDe("gente", `ingreso_por_persona_${CONDADO_RIVAL[c]}`) : null, fuente: "fred_bea", vig: ppc.vigencia},
  {n: "Personas en pobreza", ambito: "ciudad", dir: -1, f: pctF, v: c => acsC("pct_pobreza")[c], fuente: "censo_acs", vig: VIG_CEN},
  {n: "Arriendo típico hoy", ambito: "área metropolitana", dir: -1, f: usdF, v: c => ["florida"].includes(c) ? null : ultDe("vivienda", `arriendo_tipico_${c}`), fuente: "zillow_research", vig: zori.vigencia},
  {n: "Carga de arriendo (30 % o más del ingreso)", ambito: "ciudad", dir: -1, f: pctF, v: c => acsC("pct_carga_arriendo")[c], fuente: "censo_acs", vig: VIG_CEN},
  {n: "Valor típico de vivienda", ambito: "área metropolitana", dir: 0, f: usdF, v: c => ["florida"].includes(c) ? null : ultDe("vivienda", `valor_tipico_${c}`), fuente: "zillow_research", vig: zori.vigencia},
  {n: "Años de ingreso para comprar", ambito: "área y condado", dir: -1, f: v => nf(v, 1), v: c => CONDADO_DE[c] ? aniosIngreso(c) : null, fuente: "zillow_research", vig: zori.vigencia},
  {n: "Rentabilidad bruta del arriendo", ambito: "área metropolitana", dir: 0, f: pctF, v: c => ["florida"].includes(c) ? null : rentab(c), fuente: "zillow_research", vig: zori.vigencia},
  {n: "Días para vender una vivienda", ambito: "área metropolitana", dir: 0, f: v => nf(v) + NB + "días", v: c => SM[c] ? SM[c].dias : null, fuente: "fred_realtor", vig: SM.orlando.mes},
  {n: "Minutos de viaje al trabajo", ambito: "ciudad", dir: -1, f: v => nf(v, 1), v: c => acsC("minutos_al_trabajo")[c], fuente: "censo_acs", vig: VIG_CEN},
  {n: "Con título universitario", ambito: "ciudad", dir: 1, f: pctF, v: c => acsC("pct_universitarios")[c], fuente: "censo_acs", vig: VIG_CEN},
  {n: "Hogares sin carro", ambito: "ciudad", dir: 0, f: pctF, v: c => acsC("pct_sin_carro")[c], fuente: "censo_acs", vig: VIG_CEN},
  {n: "Hablan español en casa", ambito: "ciudad", dir: 0, f: pctF, v: c => acsC("pct_espanol")[c], fuente: "censo_acs", vig: VIG_CEN},
  {n: "Edad mediana", ambito: "ciudad", dir: 0, f: v => nf(v, 1), v: c => acsC("edad_mediana")[c], fuente: "censo_acs", vig: VIG_CEN},
  {n: "Crecimiento de la población en 10 años", ambito: "condado", dir: 0, f: v => pct(v, 1), v: c => CONDADO_RIVAL[c] ? Object.fromEntries(S("gente", "crecimiento_10_anios_condados"))[CONDADO_RIVAL[c]] : null, fuente: "fred_poblacion", vig: pobC.vigencia},
  {n: "Peso del ocio y la hotelería en el empleo", ambito: "área metropolitana", dir: 0, f: pctF, v: c => c === "orlando" ? ocUlt.orlando : ocUlt[c] ?? null, fuente: "fred_ces", vig: ocio.vigencia},
  {n: "Visitas en Wikipedia en inglés (12 meses)", ambito: "artículo de la ciudad", dir: 1, f: v => nf(v), v: c => ["florida", "eeuu"].includes(c) ? null : S("escucha", `vistas_ingles_${c}`).slice(-12).reduce((a, p) => a + p[1], 0), fuente: "wikimedia_pageviews", vig: ven.vigencia},
];
let rival = "tampa", modoComp = "ciudades", selComp = [];
function compCiudades(el) {
  const filas = FILAS_C.map(f => ({...f, a: f.v("orlando"), b: f.v(rival)})).filter(f => f.a != null && f.b != null);
  const dirig = filas.filter(f => f.dir), gana = dirig.filter(f => Math.abs(f.a / f.b - 1) >= .02 && (f.dir > 0 ? f.a > f.b : f.a < f.b)), pierde = dirig.filter(f => Math.abs(f.a / f.b - 1) >= .02 && !(f.dir > 0 ? f.a > f.b : f.a < f.b));
  const nomR = RIVALES.find(r => r[0] === rival)[1];
  $("#r-comparar").textContent = nb(`Orlando contra ${nomR}: mejor en ${gana.length} y peor en ${pierde.length} de ${dirig.length} medidas donde «mejor» tiene sentido; ${dirig.length - gana.length - pierde.length} casi empatan (menos de 2 % de diferencia).`);
  el.innerHTML = `<div class="barra-graf"><div class="seg" id="segRival" role="group" aria-label="Contra quién">${RIVALES.map(([k, n]) => `<button type="button" data-r="${k}" aria-pressed="${k === rival}">${n}</button>`).join("")}</div>
      <span class="leyenda-sel"><span><i style="background:var(--accent)"></i>Orlando</span><span><i style="background:var(--peer)"></i>${nomR}</span></span></div>
    <div class="marcador card" style="padding:16px"><span class="big" style="color:var(--good)">${gana.length}</span> mejor · <span class="big" style="color:var(--bad)">${pierde.length}</span> peor · <span class="big" style="color:var(--muted)">${dirig.length - gana.length - pierde.length}</span> empate <span class="peq" style="font:400 .9rem var(--font-body)">y ${filas.length - dirig.length} medidas que describen sin juzgar</span></div>
    <div class="card tabla-wrap"><table class="tabla-comp"><thead><tr><th>Medida</th><th class="n">Orlando</th><th class="n">${nomR}</th><th></th><th>¿Quién sale mejor?</th></tr></thead><tbody>
    ${filas.map(f => { const max = Math.max(f.a, f.b) || 1, d = f.a / f.b - 1, emp_ = Math.abs(d) < .02, mejor = f.dir > 0 ? f.a > f.b : f.a < f.b;
      return `<tr><td class="med">${esc(f.n)}<small>${esc(f.ambito)} · ${esc(fVig(String(f.vig)))} ${chip(f.fuente, "", f.vig)}</small></td><td class="v" data-l="Orlando">${f.f(f.a)}</td><td class="v" data-l="${esc(nomR)}" style="color:var(--ink-2)">${f.f(f.b)}</td>
        <td class="barra"><div class="duo"><i style="width:${f.a / max * 100}%;background:var(--accent)"></i><i style="width:${f.b / max * 100}%;background:var(--peer)"></i></div></td>
        <td class="gana">${!f.dir ? '<span class="igual">describe</span>' : emp_ ? '<span class="igual">empate</span>' : mejor ? '<span class="si">Orlando</span>' : `<span class="no">${nomR}</span>`}</td></tr>`; }).join("")}
    </tbody></table></div>
    <div class="nota"><svg class="i"><use href="#i-info"/></svg><p><b>Cuidado con el ámbito.</b> Algunas medidas son de la ciudad (censo), otras del área metropolitana (empleo, vivienda) y otras del condado: cada fila lo dice. «Mejor» es una lectura nuestra (por ejemplo, menos desempleo es mejor); donde no hay una lectura obvia, la fila solo describe.</p></div>`;
  $("#segRival").onclick = e => { const b = e.target.closest("button"); if (b) { rival = b.dataset.r; compCiudades(el); } };
}
const COLS_D = [["pob", "Habitantes", v => nf(v), 0], ["crec", "Crecimiento 2045", v => crecF(v), 0], ["seg", `Casos policía / 1.000 hab.`, v => nf(v, 1), -1],
  ["queja", "Quejas / 1.000 hab.", v => nf(v, 1), -1], ["ingreso", "Ingreso (aprox.)", usdF, 1], ["carga", "Carga de arriendo", v => nf(v, 0) + NB + "%", -1],
  ["sinCarro", "Sin carro", v => nf(v, 1) + NB + "%", 0], ["parques", "Parques / 10.000 hab.", v => nf(v, 1), 1], ["rInund", "Riesgo inundación", v => nf(v, 0), -1],
  ["abiertas", "Solicitudes abiertas", v => nf(v), 0], ["alertas", "Alertas", v => nf(v), -1]];
function filaDistrito(lista) {
  const a = agregado(lista);
  return {pob: a.pob, crec: (a.pob45 / a.pob17 - 1) * 100, seg: a.delitos / a.pob * 1000, queja: a.quejas / a.pob * 1000, ingreso: a.ingreso, carga: a.carga, sinCarro: a.sinCarro,
    parques: a.parques / a.pob * 10000, rInund: a.rInund, abiertas: a.abiertas, alertas: alertasDe(lista).reduce((s, r) => s + r.barrios.length, 0)};
}
function compDistritos(el) {
  const filas = DISTRITOS.map(d => [d, filaDistrito(B.filter(b => String(b.distrito) === d))]), ciudad = filaDistrito(B);
  $("#r-comparar").textContent = "Los seis distritos de comisionado lado a lado. Verde: mejor que los otros distritos en esa columna; rojo: peor. Donde no hay mejor ni peor, el azul solo dice más alto. Toca un distrito para ver sus alertas.";
  const color = (k, v, dir) => { if (v == null) return "transparent"; const vals = filas.map(f => f[1][k]).filter(x => x != null).sort((a, b) => a - b), pos = vals.indexOf(v) / Math.max(1, vals.length - 1);
    if (!dir) return `color-mix(in srgb, var(--seq-${1 + Math.round(pos * 4)}) 50%, transparent)`;
    const bien = dir > 0 ? pos : 1 - pos, fuerza = Math.round(Math.abs(bien - .5) * 2 * 38);
    return fuerza < 8 ? "transparent" : `color-mix(in srgb, ${bien > .5 ? "var(--good)" : "var(--bad)"} ${fuerza}%, transparent)`; };
  el.innerHTML = `<div class="card tabla-wrap"><table class="heat"><thead><tr><th>Distrito</th>${COLS_D.map(c => `<th class="n">${c[1]}</th>`).join("")}</tr></thead><tbody>
    ${filas.map(([d, f]) => `<tr><td><button type="button" class="btn" data-d="${d}" aria-label="Distrito ${d}: ver sus alertas">D${d}</button></td>${COLS_D.map(([k, , fmt, dir]) => `<td class="v" style="background:${color(k, f[k], dir)}">${f[k] == null ? "—" : fmt(f[k])}</td>`).join("")}</tr>`).join("")}
    <tr style="font-weight:700"><td>Toda la ciudad</td>${COLS_D.map(([k, , fmt]) => `<td class="v">${ciudad[k] == null ? "—" : fmt(ciudad[k])}</td>`).join("")}</tr></tbody></table></div>
    <div class="nota"><svg class="i"><use href="#i-info"/></svg><p>Cada barrio se asigna al distrito que contiene su centro (derivado). Habitantes, ingreso, carga de arriendo y hogares sin carro son estimaciones del censo ${VIG_CEN.replace("-", "–")} por barrio; casos de ${U_DEL}; crecimiento según la proyección de la ciudad a 2045. ${chip("orlando_distritos", "", L.territorio.probado)}</p></div>`;
  el.querySelectorAll("[data-d]").forEach(b => b.onclick = () => { stGob.d = b.dataset.d; location.hash = "decidir/gobernar"; });
}
const GRUPOS_COMP = GRUPOS_FICHA.filter(g => g[0] !== "Índice");
const compDefecto = () => [...new Set([B.reduce((a, b) => (b.pob || 0) > (a.pob || 0) ? b : a)._i, IDX.get(norm("Central Business District")) ?? 0, IDX.get(norm("Lake Nona South")) ?? 1])];
function compBarrios(el) {
  if (!selComp.length) selComp = compDefecto();
  const colores = ["var(--accent)", "var(--sun)", "var(--c2)"];
  $("#r-comparar").textContent = "Elige hasta tres barrios. Cada barra se mide contra el barrio más alto de la ciudad en esa medida; la raya gris es la mediana de los 125 barrios.";
  const sel = selComp.map(i => B[i]);
  el.innerHTML = `<div class="lado-a-lado"><div class="card panel">
      <div class="selector-b">${[0, 1, 2].map(k => `<label class="sr" for="cb${k}">Barrio ${k + 1}</label><select class="sel" id="cb${k}"><option value="">— ninguno —</option>${B.map((b, i) => `<option value="${i}" ${selComp[k] === i ? "selected" : ""}>${esc(b.nombre)}</option>`).join("")}</select>`).join("")}</div>
      <div class="fila-b cab" style="--n:${sel.length}"><span>Medida</span>${sel.map((b, k) => `<span style="color:${colores[k]}">${esc(b.nombre)}</span>`).join("")}</div>
      ${GRUPOS_COMP.map(([t, ks]) => `<div class="grupo-med"><h4>${esc(t)}</h4>${ks.map(k => { const met = METRICAS[k], max = Math.max(...B.map(b => met.v(b) ?? 0), 1), med = MEDIANA[k];
        return `<div class="fila-b" style="--n:${sel.length}"><span>${esc(met.corto)}</span>${sel.map((b, j) => { const v = met.v(b); return `<span class="val"><b>${vtxt(k, v)}</b><span>${v != null ? `<i style="width:${Math.max(0, v) / max * 100}%;background:${colores[j]}"></i>` : ""}${med != null ? `<u style="left:${Math.max(0, med) / max * 100}%"></u>` : ""}</span></span>`; }).join("")}</div>`; }).join("")}</div>`).join("")}
    </div>
    <div class="card panel"><h3>Dónde quedan</h3><svg class="svgmapa" id="mapaComp" role="img" aria-label="Mapa de los barrios comparados"></svg>
      <p class="peq">Los barrios comparados, en su color. Toca uno en el mapa para cambiar el primero.</p>
      <div class="limites"><b>Ojo al comparar</b><ul><li>Población, ingreso y arriendo son estimaciones del censo por barrio (${VIG_CEN.replace("-", "–")}).</li><li>Un barrio pequeño puede tener pocos casos y aun así una tasa alta.</li><li>«—» es sin dato publicable: menos de 5 casos o menos de ${MIN_HAB} habitantes.</li></ul></div></div></div>`;
  const svg = $("#mapaComp"); svg.setAttribute("viewBox", `0 0 ${M.ancho} ${M.alto}`);
  svg.innerHTML = M.barrios.map((b, i) => { const k = selComp.indexOf(i); return `<path class="b" data-i="${i}" d="${b.d}" style="fill:${k >= 0 ? colores[k] : "var(--surface-2)"}"/>`; }).join("") + `<path class="lago" d="${M.lagos}"/><path class="lim" d="${M.limite}"/>`;
  svg.onclick = e => { const p = e.target.closest(".b"); if (p) { selComp[0] = +p.dataset.i; compBarrios(el); } };
  svg.onpointermove = e => { const p = e.target.closest(".b"); if (p) mostrarGlobo(`<b>${esc(B[+p.dataset.i].nombre)}</b>`, e.clientX, e.clientY); else ocultarGlobo(); };
  svg.onpointerleave = ocultarGlobo;
  [0, 1, 2].forEach(k => $("#cb" + k).onchange = e => { const v = e.target.value; if (v === "") selComp.splice(k, 1); else selComp[k] = +v; selComp = selComp.filter(x => x != null); compBarrios(el); });
}
function mostrarComparar(m, extra) {
  modoComp = ["ciudades", "distritos", "barrios"].includes(m) ? m : "ciudades";
  if (modoComp === "barrios" && extra != null && B[+extra]) { selComp = [+extra, ...(selComp.length > 1 ? selComp : compDefecto()).filter(i => i !== +extra)].slice(0, 3); }
  $$("#modoComparar button").forEach(b => b.setAttribute("aria-pressed", b.dataset.m === modoComp));
  ({ciudades: compCiudades, distritos: compDistritos, barrios: compBarrios})[modoComp]($("#panelComparar"));
}
$("#modoComparar").addEventListener("click", e => { const b = e.target.closest("button"); if (b) location.hash = "comparar/" + b.dataset.m; });

// Portada: una tarjeta por perfil con su dato principal
const _emp0 = evaluarEmprender(), _viv0 = evaluarVivir(), _al0 = alertasDe(B);
const fraseDecidir = () => nb(`para un restaurante, el barrio que mejor encaja con las prioridades por defecto es ${B[_emp0.lista[0].i].nombre}; con un arriendo de ${usd(stViv.presupuesto)} (el típico hoy es ${usd(ZORI_HOY)}) caben ${_viv0.caben.length} barrios; el mercado de vivienda está «${SM.orlando.veredicto.toLowerCase()}» y hay ${_al0.reduce((s_, r) => s_ + r.barrios.length, 0)} alertas de barrio con reglas escritas.`);
$("#perfilesInicio").innerHTML = [
  ["emprender", "tienda", "Emprender", "Dónde abrir un negocio según la gente cerca, la competencia, el ingreso y la seguridad.", `${B[_emp0.lista[0].i].nombre}<small>encaja mejor para un restaurante (puedes cambiar el negocio y las prioridades)</small>`],
  ["vivir", "casa", "Vivir", "Qué barrios caben en tu arriendo y cuáles encajan con lo que te importa.", `${_viv0.caben.length} barrios<small>caben en ${usd(stViv.presupuesto)} al mes, casi el arriendo típico de hoy (${usd(ZORI_HOY)})</small>`],
  ["invertir", "llave", "Comprar o invertir", "Si el mercado favorece a quien compra, cuánto rinde arrendar y qué barrios mirar.", `${SM.orlando.veredicto}<small>${SM.orlando.n} de 4 señales a favor de quien compra · ${fMes(SM.orlando.mes, true)}</small>`],
  ["gobernar", "capitolio", "Gobernar", "Qué atender primero en cada distrito, con alertas que siguen reglas escritas.", `${_al0.reduce((s_, r) => s_ + r.barrios.length, 0)} alertas<small>en ${new Set(_al0.flatMap(r => r.barrios.map(x => x[0]))).size} barrios, ${_al0.length} tipos de problema</small>`],
].map(([k, icono, n, d, dato]) => `<a class="perfil-card" href="#decidir/${k}"><span class="ic">${ic(icono)}</span><b>${n}</b><p>${d}</p><span class="dato">${dato}</span></a>`).join("");

/* ================= MODO PRESENTACIÓN ================= */
const LAMINAS = [
  () => ({html: `<div class="contenido dos"><div style="display:grid;gap:18px"><p class="eyebrow">Orlando, Florida · Taller de datos · EAFIT</p><p class="q">Cerebro Orlando</p><p class="lead">Un sistema de información para el equipo de planeación de la ciudad: seis preguntas respondidas con datos abiertos, cuatro perfiles para decidir y comparaciones contra ciudades, distritos y barrios. Cada cifra con su fuente, su vigencia y su fecha de prueba.</p><p class="peq">Juan Esteban Alzate · Nicolás Saldarriaga · Mateo Villada</p></div>
      <ol class="ranking" style="font-size:1.05rem">${["¿Cuánta gente vive aquí?", "¿Cómo va el empleo y cuánto cuesta vivir aquí?", "¿Dónde se construye?", "¿Qué pasa con la seguridad?", "¿Cuánto pesa el turismo?", "¿Cómo está cambiando el clima?", "¿Qué decido con esto?", "¿Contra quién nos medimos?"].map((q, k) => `<li><div class="fila"><span class="pos">${k + 1}</span><span class="nom" style="white-space:normal">${q}</span><span></span></div></li>`).join("")}</ol></div>`}),
  () => ({html: `<div class="contenido dos"><div style="display:grid;gap:14px"><p class="eyebrow">1 · Gente</p><p class="q">¿Cuánta gente vive aquí?</p><p class="grande">${millones(pobC.valor).replace(NB + "millones", "")} <span style="font-size:.35em">millones</span></p><p class="lead">${esc(fraseGente)}</p>${chip("fred_poblacion", "poblacion_condado_ultimo_anio", pobC.vigencia)}</div><div style="display:grid;gap:8px;align-content:center"><p class="peq"><b style="color:var(--ink)">Ingreso mediano de los hogares, frente a condados parecidos</b> (dólares al año)</p><div class="chart" id="pg1"></div></div></div>`,
    despues: () => lineas($("#pg1"), {series: seriesPares("ingreso_mediano", "2005"), alto: 340, fmtX: s => s, fmtY: usd, fmtTick: v => nf(v / 1000) + " mil", etiquetas: true, aria: "Ingreso mediano por condado"})}),
  () => ({html: `<div class="contenido dos"><div style="display:grid;gap:14px"><p class="eyebrow">2 · Economía y vivienda</p><p class="q">¿Cómo va el empleo y cuánto cuesta vivir aquí?</p><p class="grande">${nf(des.valor, 1)} %</p><p class="lead">${esc(fraseDes)} ${esc(fraseViv.split(". ").slice(-1)[0])}</p>${chip("fred_laus", "desempleo_ultimo_mes", des.vigencia)}</div><div style="display:grid;gap:8px;align-content:center"><p class="peq"><b style="color:var(--ink)">Desempleo de Orlando frente a sus pares</b> (%, desde 2016)</p><div class="chart" id="pg2"></div></div></div>`,
    despues: () => lineas($("#pg2"), {series: DES.slice(0, 5).map(([k, n, c, yo]) => ({nombre: n, puntos: S("economia", `desempleo_${k}`).filter(p => p[0] >= "2016"), color: c, resaltar: yo})), alto: 340, fmtX: s => fMes(s, true), fmtY: v => nf(v, 1) + " %", fmtTick: (v, d) => nf(v, d) + NB + "%", cero: true, etiquetas: true, aria: "Desempleo"})}),
  () => ({html: `<div class="contenido dos"><div style="display:grid;gap:14px"><p class="eyebrow">3 · Barrios</p><p class="q">¿Dónde se construye?</p><p class="grande">${nf(tot.valor)}</p><p class="lead">${esc(frasePer)}</p>${chip("orlando_permisos", "permisos_por_barrio_ultimo_anio", tot.vigencia)}</div><div><svg class="svgmapa" id="pg3"></svg><div class="ley-mapa" id="pg3l"></div></div></div>`,
    despues: () => mapaPlano($("#pg3"), {valores: i => B[i].permisos[U_PERM] ?? null, ley: $("#pg3l"), titulo: () => `Permisos emitidos en ${U_PERM}`, globo: i => `<b>${esc(B[i].nombre)}</b><br>${fmtV(B[i].permisos[U_PERM])} permisos`})}),
  () => ({html: `<div class="contenido dos"><div style="display:grid;gap:14px"><p class="eyebrow">4 · Seguridad</p><p class="q">¿Qué pasa con la seguridad?</p><p class="grande">${pct(vDel, 0)}</p><p class="lead">${esc(fraseSeg)} Solo conteos por barrio: sin número de caso, sin punto exacto, sin categorías de salud mental.</p>${chip("opd_casos", "delitos_ultimo_anio", del.vigencia)}</div><div><svg class="svgmapa" id="pg4"></svg><div class="ley-mapa" id="pg4l"></div></div></div>`,
    despues: () => mapaPlano($("#pg4"), {valores: i => porKm2(B[i].delitos[U_DEL], B[i]), ley: $("#pg4l"), fmt: v => nf(v, 0), titulo: () => `Casos por km² en ${U_DEL}`, globo: i => `<b>${esc(B[i].nombre)}</b><br>${fmtV(porKm2(B[i].delitos[U_DEL], B[i]), true)} por km²`})}),
  () => ({html: `<div class="contenido dos"><div style="display:grid;gap:14px"><p class="eyebrow">5 · Turismo</p><p class="q">¿Cuánto pesa el turismo?</p><p class="grande">${nf(ocio.valor, 1)} %</p><p class="lead">${esc(fraseTur)}</p>${chip("fred_ces", "participacion_ocio_ultimo_mes", ocio.vigencia)}</div><div style="display:grid;gap:8px;align-content:center"><p class="peq"><b style="color:var(--ink)">Empleos en ocio y hotelería en el área</b> (miles)</p><div class="chart" id="pg5"></div></div></div>`,
    despues: () => lineas($("#pg5"), {series: [{nombre: "Ocio", puntos: ocioS, color: "var(--accent)"}], alto: 340, fmtX: s => fMes(s, true), fmtY: v => nf(v, 1) + " mil empleos", area: true, cero: true, notas: [{x: pandO[0], texto: "Pandemia", pos: "abajo"}], aria: "Empleo en ocio y hotelería"})}),
  () => ({html: `<div class="contenido"><div style="display:grid;gap:14px"><p class="eyebrow">6 · Clima</p><p class="q">¿Cómo está cambiando el clima?</p><p class="grande">+${nf(difCal.valor, 1)} °F</p><p class="lead">${esc(fraseClima)}</p>${franjasSVG(150)}<p class="vig">Cada franja es un año, de ${temps[0][0]} a ${ult(temps)[0]}. Azul: más frío que el promedio; rojo: más caliente.</p>${chip("noaa_gsoy", "temperatura_anual", ult(temps)[0])}</div></div>`}),
  () => ({html: `<div class="contenido"><div style="display:grid;gap:16px"><p class="eyebrow">7 · Decidir</p><p class="q">Los mismos datos, cuatro decisiones</p><p class="lead">Cada perfil cruza las fuentes con una regla escrita a la vista y dice también lo que no sabe. No es asesoría: ordena dónde mirar primero.</p><div class="perfiles-inicio">${$("#perfilesInicio").innerHTML}</div></div></div>`}),
  () => { const f = FILAS_C.map(x => ({...x, a: x.v("orlando"), b: x.v("tampa")})).filter(x => x.a != null && x.b != null && x.dir), g = f.filter(x => Math.abs(x.a / x.b - 1) >= .02 && (x.dir > 0 ? x.a > x.b : x.a < x.b)), p = f.filter(x => Math.abs(x.a / x.b - 1) >= .02 && !(x.dir > 0 ? x.a > x.b : x.a < x.b));
    return {html: `<div class="contenido dos"><div style="display:grid;gap:14px"><p class="eyebrow">8 · Comparar</p><p class="q">Orlando contra Tampa</p><p class="grande">${g.length} <span style="font-size:.35em">mejor</span> · ${p.length} <span style="font-size:.35em">peor</span></p><p class="lead">De ${f.length} medidas donde «mejor» tiene sentido. En el tablero se puede cambiar el rival (Miami, Jacksonville, Florida, EE. UU.), comparar los 6 distritos o hasta 3 barrios.</p></div>
      <div class="card tabla-wrap"><table class="tabla-comp"><thead><tr><th>Medida</th><th class="n">Orlando</th><th class="n">Tampa</th><th>Mejor</th></tr></thead><tbody>${f.slice(0, 9).map(x => { const m = x.dir > 0 ? x.a > x.b : x.a < x.b, e = Math.abs(x.a / x.b - 1) < .02; return `<tr><td class="med">${esc(x.n)}<small>${esc(x.ambito)}</small></td><td class="v">${x.f(x.a)}</td><td class="v" style="color:var(--ink-2)">${x.f(x.b)}</td><td class="gana">${e ? '<span class="igual">empate</span>' : m ? '<span class="si">Orlando</span>' : '<span class="no">Tampa</span>'}</td></tr>`; }).join("")}</tbody></table></div></div>`}; },
  () => ({html: `<div class="contenido"><div style="display:grid;gap:16px"><p class="eyebrow">Lo que el cerebro no sabe, lo dice</p><p class="q">Preguntas sin respuesta abierta</p><div class="pendientes">${PENDIENTES.map(x => `<div class="pend">${ic("hueco")}<b>${esc(x.t)}</b><p>${esc(x.p)}</p></div>`).join("")}</div></div></div>`}),
  () => ({html: `<div class="contenido dos"><div style="display:grid;gap:14px"><p class="eyebrow">De dónde sale todo</p><p class="q">${D.catalogo.length} fuentes revisadas, ${cuenta.integrado} en uso</p><p class="lead">${verOk ? `${ver.pasan} comprobaciones automáticas antes de publicar, 0 fallos.` : ""} Si una cifra no tiene fuente, vigencia y fecha de prueba, no se publica. Lo que trae personas entra solo como conteos por barrio, con umbral.</p></div><div class="card panel"><div class="embudo">${$("#embudo").innerHTML}</div><div class="ley-embudo">${$("#leyEmbudo").innerHTML}</div><div class="barras-simples">${$("#motivos").innerHTML}</div></div></div>`}),
];
let lam = 0;
function mostrarLamina(k) {
  lam = Math.max(0, Math.min(LAMINAS.length - 1, k));
  const l = LAMINAS[lam](); $("#pres-lamina").innerHTML = l.html; $("#pres-lamina").scrollTop = 0;
  $("#pres-n").textContent = `${lam + 1} de ${LAMINAS.length}`;
  $("#pres-puntos").innerHTML = LAMINAS.map((_, i) => `<button type="button" data-k="${i}" aria-label="Lámina ${i + 1}" aria-current="${i === lam}"></button>`).join("");
  $("#pres-ant").disabled = lam === 0; $("#pres-sig").disabled = lam === LAMINAS.length - 1;
  if (l.despues) requestAnimationFrame(l.despues);
}
function abrirPresentacion() { $("#presentacion").hidden = false; document.body.style.overflow = "hidden"; mostrarLamina(0); $("#pres-sig").focus(); try { document.documentElement.requestFullscreen?.().catch(() => {}); } catch {} }
function cerrarPresentacion() { $("#presentacion").hidden = true; document.body.style.overflow = ""; try { if (document.fullscreenElement) document.exitFullscreen(); } catch {} }
$("#presentarBtn").addEventListener("click", abrirPresentacion); $("#presentarBtn2").addEventListener("click", abrirPresentacion);
$("#pres-cerrar").addEventListener("click", cerrarPresentacion);
$("#pres-ant").addEventListener("click", () => mostrarLamina(lam - 1)); $("#pres-sig").addEventListener("click", () => mostrarLamina(lam + 1));
$("#pres-puntos").addEventListener("click", e => { const b = e.target.closest("button"); if (b) mostrarLamina(+b.dataset.k); });
addEventListener("keydown", e => { if ($("#presentacion").hidden) return; if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") { e.preventDefault(); mostrarLamina(lam + 1); } else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); mostrarLamina(lam - 1); } else if (e.key === "Escape") cerrarPresentacion(); });

/* ================= NAVEGACIÓN Y TEMA ================= */
const VISTAS = ["inicio", "decidir", "comparar", "gente", "economia", "barrios", "seguridad", "turismo", "clima", "fuentes"];
function mostrar(ruta, desplazar = true) {
  let [nombre, sub, extra] = decodeURIComponent(ruta || "").split("/");
  if (!VISTAS.includes(nombre)) nombre = "inicio";
  if (nombre === "decidir") mostrarPerfil(sub || perfil);
  if (nombre === "comparar") mostrarComparar(sub || modoComp, extra);
  $$(".vista").forEach(s => s.hidden = s.dataset.vista !== nombre);
  $$("nav.preguntas a").forEach(a => a.dataset.v === nombre ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current"));
  const act = $(`nav.preguntas a[data-v="${nombre}"]`); if (act && act.scrollIntoView) act.scrollIntoView({block: "nearest", inline: "center"});
  ocultarGlobo(); if (desplazar) scrollTo({top: 0});
  requestAnimationFrame(() => [atlasInicio, atlasB].forEach(a => a.map && a.map.resize()));
}
addEventListener("hashchange", () => mostrar(location.hash.slice(1)));
mostrar(location.hash.slice(1), false);
const raiz = document.documentElement;
try { const g = localStorage.getItem("cerebro-tema"); if (g) raiz.dataset.theme = g; } catch {}
$("#temaBtn").addEventListener("click", () => {
  const oscuro = raiz.dataset.theme ? raiz.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  raiz.dataset.theme = oscuro ? "light" : "dark";
  try { localStorage.setItem("cerebro-tema", raiz.dataset.theme); } catch {}
  redibujar(); atlasInicio.pintar(); atlasB.pintar();
});
matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", () => { redibujar(); atlasInicio.pintar(); atlasB.pintar(); });
new MutationObserver(() => { atlasInicio.pintar(); atlasB.pintar(); }).observe(raiz, {attributes: true, attributeFilter: ["data-theme"]});
// Espacios duros en todo texto que se pinte, ahora o después (tarjetas, globos, láminas): «0 %» no se parte nunca
function arreglarTexto(raiz) {
  if (raiz.nodeType === 3) { const t = nb(raiz.data); if (t !== raiz.data) raiz.data = t; return; }
  if (raiz.nodeType !== 1 || /^(SCRIPT|STYLE|TEXTAREA|INPUT)$/.test(raiz.nodeName)) return;
  const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, {acceptNode: n => /^(SCRIPT|STYLE|TEXTAREA)$/.test(n.parentNode.nodeName) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  for (let n = w.nextNode(); n; n = w.nextNode()) { const t = nb(n.data); if (t !== n.data) n.data = t; }
}
arreglarTexto(document.body);
new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(arreglarTexto))).observe(document.body, {childList: true, subtree: true});
window.cerebro = {atlasInicio, atlasB, B, METRICAS};   // para revisar desde la consola del navegador
})();
