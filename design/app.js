/* ============================================================
   Altars — demo editorial: interações ligadas à API real
   Servidor: FastAPI (app/server.py). Base relativa → funciona
   em qualquer host/porta onde o demo for servido.
   Fluxo: Inbox → Redigir → Rever/aprovar → Compor → Exportar.
   ============================================================ */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const API_BASE = "/api";

/* ---------- Estado ---------- */
const estado = {
  artigoId: null,      // artigo selecionado na Inbox
  formato: "breve",    // formato de geração
  pecaId: null,        // peça aberta no editor
  pecaRevista: false,  // gate humano satisfeito?
};

/* ---------- Toast ---------- */
const toastEl = $("#toast");
let toastTimer = null;
function toast(msg) {
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 3200);
}

/* ---------- Utilitário HTTP ---------- */
async function api(caminho, opcoes = {}) {
  const resp = await fetch(API_BASE + caminho, opcoes);
  if (!resp.ok) {
    let detalhe = resp.statusText;
    try {
      const j = await resp.json();
      detalhe = j.detail || detalhe;
    } catch (_) { /* corpo não-JSON */ }
    throw new Error(`${resp.status} ${detalhe}`);
  }
  return resp;
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
));

const corta = (s, n = 160) => {
  const t = String(s ?? "").trim();
  return t.length > n ? t.slice(0, n) + "…" : t;
};

/* ---------- Tabs (Inbox · Redigir · Alertas · Compor) ---------- */
const tabs = $$('[role="tab"]');
function activateTab(id) {
  tabs.forEach((t) => {
    const on = t.id === id;
    t.setAttribute("aria-selected", on ? "true" : "false");
    t.tabIndex = on ? 0 : -1;
    const view = $("#" + t.getAttribute("aria-controls"));
    if (view) {
      view.classList.toggle("hidden", !on);
      if (on) view.removeAttribute("hidden");
      else view.setAttribute("hidden", "");
    }
  });
}
tabs.forEach((t) => {
  t.addEventListener("click", () => activateTab(t.id));
  t.addEventListener("keydown", (e) => {
    const i = tabs.indexOf(t);
    if (e.key === "ArrowRight") {
      e.preventDefault();
      const n = tabs[(i + 1) % tabs.length];
      n.focus();
      activateTab(n.id);
    }
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      const n = tabs[(i - 1 + tabs.length) % tabs.length];
      n.focus();
      activateTab(n.id);
    }
  });
});

/* ============================================================
   INBOX — recolha e pesquisa (RF-1.x)
   ============================================================ */
async function carregarInbox(q = "") {
  const lista = $("#recolha-lista");
  const vazio = $("#recolha-empty-search");
  if (!lista) return;
  try {
    const resp = await api(`/inbox?limite=100${q ? `&q=${encodeURIComponent(q)}` : ""}`);
    const data = await resp.json();
    renderInbox(data.itens);
    if (vazio) vazio.classList.toggle("hidden", data.itens.length > 0);
  } catch (e) {
    toast("Falha a carregar a Inbox: " + e.message);
  }
}

function renderInbox(itens) {
  const lista = $("#recolha-lista");
  if (!lista) return;
  lista.innerHTML = itens.map((it) => `
    <article class="item" data-id="${it.id}" data-texto="${esc((it.titulo + " " + it.fonte + " " + (it.categoria || "")).toLowerCase())}">
      <div class="item-top">
        <span class="item-source">${esc(it.fonte)}</span>
        <span class="item-meta">${esc(it.data_publicacao || "")}</span>
        ${it.categoria ? `<span class="suggest">Tema sugerido: <strong>${esc(it.categoria)}</strong></span>` : ""}
        <span class="chip chip-neutral"><span class="dot"></span>Arquivado integralmente</span>
      </div>
      <h3>${esc(it.titulo)}</h3>
      <p class="excerpt">${esc(corta(it.corpo_texto || "", 180))}</p>
      <div class="item-foot">
        <a class="btn btn-ghost btn-sm" href="${esc(it.url)}" target="_blank" rel="noopener">Abrir original</a>
        <button class="btn btn-primary btn-sm act-transformar" data-id="${it.id}">Redigir peça</button>
      </div>
    </article>
  `).join("");

  $$(".act-transformar", lista).forEach((b) =>
    b.addEventListener("click", () => {
      estado.artigoId = Number(b.dataset.id);
      activateTab("tab-editor");
      toast("Artigo selecionado. Escolha o formato e redija a peça.");
    })
  );
}

/* Pesquisa local (filtra o que já está renderizado) */
const searchInput = $("#search-input");
if (searchInput) {
  searchInput.addEventListener("input", () => {
    const q = searchInput.value.trim().toLowerCase();
    let vis = 0;
    $$("#recolha-lista .item").forEach((it) => {
      const hit = !q || (it.dataset.texto || "").includes(q);
      it.classList.toggle("hidden", !hit);
      if (hit) vis++;
    });
    const vazio = $("#recolha-empty-search");
    if (vazio) vazio.classList.toggle("hidden", vis > 0);
  });
}
const limpar = $("#limpar-filtros");
if (limpar) limpar.addEventListener("click", (e) => {
  e.preventDefault();
  if (searchInput) {
    searchInput.value = "";
    searchInput.dispatchEvent(new Event("input"));
  }
});

/* ============================================================
   REDIGIR — gerar peça (RF-2.x)
   ============================================================ */
$$(".seg-btn").forEach((b) =>
  b.addEventListener("click", () => {
    $$(".seg-btn").forEach((o) => o.setAttribute("aria-checked", "false"));
    b.setAttribute("aria-checked", "true");
    estado.formato = (b.dataset.formato || "Breve").toLowerCase();
  })
);

const btnGerar = $("#btn-gerar");
if (btnGerar) btnGerar.addEventListener("click", gerarPeca);

async function gerarPeca() {
  if (!estado.artigoId) {
    toast("Escolha primeiro um artigo na Inbox.");
    activateTab("tab-recolha");
    return;
  }
  const gerando = $("#gerando");
  const erro = $("#gerar-erro");
  if (erro) erro.classList.add("hidden");
  if (gerando) gerando.classList.remove("hidden");
  btnGerar.disabled = true;
  try {
    const resp = await api("/gerar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ artigo_id: estado.artigoId, formato: estado.formato }),
    });
    const peca = await resp.json();
    abrirPeca(peca);
    toast("Peça redigida — requer a sua revisão.");
  } catch (e) {
    if (erro) erro.classList.remove("hidden");
    toast("Falha a gerar a peça: " + e.message);
  } finally {
    if (gerando) gerando.classList.add("hidden");
    btnGerar.disabled = false;
  }
}

function abrirPeca(peca) {
  estado.pecaId = peca.peca_id ?? peca.id ?? null;
  estado.pecaRevista = false;
  activateTab("tab-editor");
  const vazio = $("#editor-vazio");
  const bloco = $("#peca");
  if (vazio) vazio.classList.add("hidden");
  if (bloco) bloco.classList.remove("hidden");

  const ant = $(".peca-antetitulo");
  const tit = $(".peca-titulo");
  const lead = $(".peca-lead");
  const corpo = $(".peca-corpo");
  const fecho = $(".peca-fecho");
  if (ant) ant.textContent = peca.antetitulo || "";
  if (tit) tit.textContent = peca.titulo || "";
  if (lead) lead.textContent = peca.lead || "";
  if (corpo) corpo.innerHTML = String(peca.corpo || "")
    .split(/\n{2,}/)
    .map((p) => `<p>${esc(p)}</p>`)
    .join("");
  // O compositor não produz bloco de fecho separado: esconde o placeholder.
  if (fecho) fecho.closest(".bloco").classList.add("hidden");

  const chip = $("#chip-estado");
  if (chip) {
    chip.className = "chip chip-generated";
    chip.classList.remove("hidden");
    const txt = $("#chip-estado-txt");
    if (txt) txt.textContent = "Rascunho — Redigida pela IA. Falta a sua revisão.";
  }
  const aviso = $("#aviso-fontes");
  if (aviso) aviso.classList.remove("hidden");

  const fontes = $(".fontes");
  if (fontes && Array.isArray(peca.fontes)) {
    fontes.innerHTML = '<h3 class="fontes-titulo">Fontes desta peça</h3>' +
      peca.fontes.map((f) => `
        <div class="fonte">
          <span class="fonte-nome">${esc(f.fonte || "")}</span>
          <span class="fonte-meta">${esc(f.data || "")}</span>
          <a class="fonte-link" href="${esc(f.url || "#")}" target="_blank" rel="noopener">Ver original</a>
        </div>`).join("");
  }
  atualizarPalavras();
}

/* Instrução em linguagem natural (demo: aplica aviso, sem reescrita real) */
const btnAplicar = $("#btn-aplicar");
if (btnAplicar) btnAplicar.addEventListener("click", () => {
  const inst = $("#input-instrucao");
  if (!inst || !inst.value.trim()) {
    toast("Escreva a instrução primeiro.");
    return;
  }
  toast("Instrução registada (demo: reescrita assistida requer LLM).");
  inst.value = "";
});

/* Guardar versão / copiar */
const btnGuardar = $("#btn-guardar-versao");
if (btnGuardar) btnGuardar.addEventListener("click", () => toast("Versão guardada (demo)."));
const btnCopiar = $("#btn-copiar");
if (btnCopiar) btnCopiar.addEventListener("click", async () => {
  const alvo = $("#peca");
  const texto = alvo ? alvo.innerText.trim() : "";
  try {
    await navigator.clipboard.writeText(texto);
    toast("Texto copiado.");
  } catch (_) {
    toast("Não foi possível copiar automaticamente.");
  }
});

/* Marcar como revista → aprovação real no servidor */
const btnRevista = $("#btn-marcar-revista");
if (btnRevista) btnRevista.addEventListener("click", async () => {
  if (!estado.pecaId) {
    toast("Gere ou abra uma peça primeiro.");
    return;
  }
  try {
    await api(`/pecas/${estado.pecaId}/aprovar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ revisor: "Demo", nota: "revisto na demo" }),
    });
    estado.pecaRevista = true;
    const chip = $("#chip-estado");
    if (chip) {
      chip.className = "chip chip-reviewed";
      const txt = $("#chip-estado-txt");
      if (txt) txt.textContent = "Revista — pronta a compor.";
    }
    const aviso = $("#aviso-fontes");
    if (aviso) aviso.classList.add("hidden");
    toast("Peça marcada como revista.");
    carregarPecas();
  } catch (e) {
    toast("Falha a marcar como revista: " + e.message);
  }
});

const btnEnviar = $("#btn-enviar-composicao");
if (btnEnviar) btnEnviar.addEventListener("click", () => {
  if (!estado.pecaRevista) {
    toast("Marque a peça como revista antes de compor.");
    return;
  }
  activateTab("tab-composicao");
  carregarPecasRevistas();
  toast("Peça enviada para composição.");
});

/* ============================================================
   ALERTAS — MIREX (RF-3.x)
   ============================================================ */
async function carregarAlertas() {
  const lista = $("#alertas-lista");
  const vazio = $("#alertas-vazio");
  if (!lista) return;
  try {
    const resp = await api("/alertas");
    const data = await resp.json();
    if (!data.alertas.length) {
      lista.innerHTML = "";
      if (vazio) vazio.classList.remove("hidden");
      return;
    }
    if (vazio) vazio.classList.add("hidden");
    lista.innerHTML = data.alertas.map((a) => `
      <article class="alerta" data-urgente="${a.prioridade === "Urgente"}">
        <div class="alerta-top">
          <span class="chip ${a.prioridade === "Urgente" ? "chip-danger" : "chip-generated"}">
            <span class="dot"></span>${esc(a.prioridade || "Relevante")}
          </span>
          <span class="item-meta">${a.latencia_s != null ? a.latencia_s.toFixed(1) + " s" : "—"} · ${esc(a.detetado_em || "")}</span>
        </div>
        <div class="alerta-perfil">
          <span class="avatar" aria-hidden="true">MI</span>
          <div>
            <strong>${esc(a.perfil)}</strong> publicou
            <div class="item-meta">${esc(a.publicado_em || "")}</div>
          </div>
        </div>
        <blockquote class="alerta-post">«${esc(a.titulo)}»</blockquote>
        ${a.peca_proposta ? `
        <div class="alerta-peca">
          <div class="alerta-peca-head">
            <span class="chip chip-generated"><span class="dot"></span>Peça proposta — a rever</span>
            <span class="item-meta">${esc(a.peca_proposta.formato || "")} · ${esc(String(a.peca_proposta.rotulo || ""))}</span>
          </div>
          <h4>${esc(a.peca_proposta.titulo)}</h4>
          <p class="peca-lead">${esc(a.peca_proposta.lead || "")}</p>
          <div class="alerta-acoes">
            <button class="btn btn-secondary btn-sm act-abrir-peca" data-peca="${a.peca_proposta.id}">Abrir peça proposta</button>
          </div>
        </div>` : ""}
        <div class="alerta-acoes">
          <a class="btn btn-ghost btn-sm" href="${esc(a.url)}" target="_blank" rel="noopener">Ver publicação original</a>
        </div>
        <p class="alerta-demo">Alerta simulado nesta demonstração. A fonte é real; a latência é ilustrativa.</p>
      </article>
    `).join("");
    $$(".act-abrir-peca", lista).forEach((b) =>
      b.addEventListener("click", () => {
        const id = Number(b.dataset.peca);
        if (!id) return;
        estado.pecaId = id;
        estado.pecaRevista = false;
        activateTab("tab-editor");
        carregarPreview(id);
        toast("Peça proposta aberta no editor. Reveja antes de compor.");
      })
    );
  } catch (e) {
    toast("Falha a carregar alertas: " + e.message);
  }
}

async function pollAlertas() {
  try {
    const resp = await api("/alertas/poll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ perfil_id: "mirex-demo" }),
    });
    const data = await resp.json();
    if (data.novas && data.novas.length) {
      toast(`${data.novas.length} alerta(s) novo(s).`);
      carregarAlertas();
    }
  } catch (_) { /* polling silencioso */ }
}

/* ============================================================
   COMPOR e EXPORTAR — RF-4.4 / RF-5.3
   ============================================================ */
async function carregarPecasRevistas() {
  const sel = $("#sel-peca");
  if (!sel) return;
  try {
    const resp = await api("/pecas?estado=revista");
    const data = await resp.json();
    const revistas = data.pecas || [];
    sel.innerHTML = revistas.length
      ? revistas.map((p) => `<option value="${p.id}">${esc(corta(p.titulo, 60))} — revista</option>`).join("")
      : '<option value="">(sem peças revistas)</option>';
    if (revistas.length) {
      estado.pecaId = revistas[0].id;
      estado.pecaRevista = true;
      await carregarPreview(revistas[0].id);
    }
  } catch (e) {
    toast("Falha a carregar peças revistas: " + e.message);
  }
}

async function carregarPreview(pecaId) {
  try {
    const resp = await api(`/pecas/${pecaId}/preview`);
    const p = await resp.json();
    const ant = $(".preview-antetitulo");
    const tit = $(".preview-titulo");
    const lead = $(".preview-lead");
    const corpo = $(".preview-corpo");
    if (ant) ant.textContent = p.antetitulo || "";
    if (tit) tit.textContent = p.titulo || "";
    if (lead) lead.textContent = p.lead || "";
    if (corpo) corpo.innerHTML = String(p.corpo || "")
      .split(/\n{2,}/)
      .map((t) => `<p>${esc(t)}</p>`)
      .join("");
    const iAnt = $("#input-antetitulo");
    const iTit = $("#input-titulo");
    if (iAnt) iAnt.value = p.antetitulo || "";
    if (iTit) iTit.value = p.titulo || "";
  } catch (e) {
    toast("Falha a carregar a pré-visualização: " + e.message);
  }
}

const selPeca = $("#sel-peca");
if (selPeca) selPeca.addEventListener("change", () => {
  const id = Number(selPeca.value);
  if (id) {
    estado.pecaId = id;
    estado.pecaRevista = true;
    carregarPreview(id);
  }
});

async function exportar(formato) {
  const bloqueio = $("#export-bloqueio");
  const id = estado.pecaId;
  if (!id) {
    if (bloqueio) bloqueio.classList.remove("hidden");
    toast("Escolha uma peça revista para exportar.");
    return;
  }
  if (bloqueio) bloqueio.classList.add("hidden");
  try {
    const resp = await api(`/pecas/${id}/exportar.${formato}`);
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `altars-${id}.${formato}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    toast(`Exportado: altars-${id}.${formato}`);
  } catch (e) {
    toast("Falha na exportação: " + e.message);
  }
}

const btnPdf = $("#btn-exportar-pdf");
if (btnPdf) btnPdf.addEventListener("click", () => exportar("pdf"));
const btnPng = $("#btn-exportar-png");
if (btnPng) btnPng.addEventListener("click", () => exportar("png"));

/* ============================================================
   Lista de peças no editor (histórico) — opcional
   ============================================================ */
async function carregarPecas() {
  const sel = $("#sel-peca");
  if (!sel) return;
  try {
    const resp = await api("/pecas");
    const data = await resp.json();
    const revistas = (data.pecas || []).filter((p) => p.estado === "revista");
    if (revistas.length) {
      sel.innerHTML = revistas.map((p) => `<option value="${p.id}">${esc(corta(p.titulo, 60))} — revista</option>`).join("");
    }
  } catch (_) { /* silencioso */ }
}

function atualizarPalavras() {
  const el = $("#palavras");
  const alvo = $("#peca");
  if (!el || !alvo) return;
  const n = (alvo.innerText.match(/\w+/g) || []).length;
  el.textContent = `${n} palavras`;
}

/* ---------- Nova peça ---------- */
const btnNova = $("#btn-nova");
if (btnNova) btnNova.addEventListener("click", () => {
  activateTab("tab-recolha");
  toast("Escolha um artigo na Inbox para redigir.");
});

/* ---------- Arranque ---------- */
document.addEventListener("DOMContentLoaded", () => {
  carregarInbox();
  carregarAlertas();
  carregarPecas();
  setInterval(pollAlertas, 60000);
});
