/* ============================================================
   Altars — demo editorial: interações com API do servidor
   Integrado com FastAPI (http://localhost:8000)
   IDs iguais aos do index.html real
   ============================================================ */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const API_BASE = "http://localhost:8000/api";

/* ---------- Toast ---------- */
const toastEl = $("#toast");
let toastTimer = null;
function toast(msg) {
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2600);
}

/* ---------- Tabs ---------- */
const tabs = $$("#tab-recolha, #tab-editor, #tab-alertas, #tab-composicao");
function activateTab(id) {
  tabs.forEach(t => {
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
tabs.forEach(t => {
  t.addEventListener("click", () => activateTab(t.id));
  t.addEventListener("keydown", e => {
    const i = tabs.indexOf(t);
    if (e.key === "ArrowRight") { e.preventDefault(); const n = tabs[(i + 1) % tabs.length]; n.focus(); activateTab(n.id); }
    if (e.key === "ArrowLeft") { e.preventDefault(); const n = tabs[(i - 1 + tabs.length) % tabs.length]; n.focus(); activateTab(n.id); }
  });
});

/* ---------- Inbox: pesquisa e listagem ---------- */
let inboxData = [];
async function carregarInbox() {
  const q = $("search-input").value.trim().toLowerCase();
  const resposta = await fetch(`${API_BASE}/inbox?q=${encodeURIComponent(q)}`);
  if (!resposta.ok) {
    toast("Erro ao carregar Inbox: " + resposta.statusText);
    return;
  }
  inboxData = await resposta.json();
  const lista = $("#recolha-lista");
  lista.innerHTML = "";
  inboxData.itens.forEach(item => {
    const el = document.createElement("div");
    el.className = "item";
    el.dataset.titulo = (item.titulo || "").toLowerCase();
    el.innerHTML = `
      <div class="item-header">
        <span class="item-titulo">${item.titulo || "(sem título)"}</span>
        <span class="item-meta">${item.fonte || "?"} · ${item.data_publicacao || ""}</span>
      </div>
      <div class="item-corpo">${(item.corpo_texto || "").substring(0, 150)}...</div>
      <button class="btn btn-sm btn-primary" data-id="${item.id}">Gerar peça</button>
    `;
    lista.appendChild(el);
  });
  if (inboxData.itens.length === 0) {
    $("#recolha-empty-search").classList.remove("hidden");
  }
}

/* ---------- Redigir: gerar peça ---------- */
async function gerarPeca(artigoId, formato) {
  const resposta = await fetch(`${API_BASE}/gerar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ artigo_id: artigoId, formato }),
  });
  if (!resposta.ok) {
    toast("Erro ao gerar peça: " + resposta.statusText);
    return;
  }
  pecaGerada = await resposta.json();
  renderizarRedacao();
}

/* ---------- Redigir: listar peças ---------- */
async function carregarPecas() {
  const resposta = await fetch(`${API_BASE}/pecas`);
  if (!resposta.ok) {
    toast("Erro ao carregar peças: " + resposta.statusText);
    return;
  }
  const data = await resposta.json();
  const lista = $("#peca");
  lista.innerHTML = "";
  data.pecas.slice(0, 10).forEach(peca => {
    const estado = peca.aprovada ? "revista" : "gerada";
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="item-header">
        <span class="item-titulo">${peca.titulo || "(sem título)"}</span>
        <span class="item-meta">${peca.formato || "?"} · ${peca.rotulo || ""}</span>
      </div>
      <div class="item-corpo">${(peca.corpo || "").substring(0, 150)}...</div>
      <div class="item-estado">${estado}</div>
      <button class="btn btn-sm btn-secondary" data-id="${peca.id}" data-estado="${estado}">Rever</button>
    `;
    lista.appendChild(el);
  });
}

/* ---------- Redigir: aprovar ---------- */
async function aprovarPeca(pecaId, revisor, nota) {
  const resposta = await fetch(`${API_BASE}/pecas/${pecaId}/aprovar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ revisor, nota }),
  });
  if (!resposta.ok) {
    toast("Erro ao aprovar: " + resposta.statusText);
    return;
  }
  toast("Peça revista com sucesso");
  carregarPecas();
}

/* ---------- Alertas: listar ---------- */
async function carregarAlertas() {
  const resposta = await fetch(`${API_BASE}/alertas`);
  if (!resposta.ok) {
    toast("Erro ao carregar alertas: " + resposta.statusText);
    return;
  }
  const data = await resposta.json();
  const lista = $("#alertas-lista");
  lista.innerHTML = "";
  data.alertas.slice(0, 10).forEach(alerta => {
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="item-header">
        <span class="item-titulo">${alerta.titulo || "(sem título)"}</span>
        <span class="item-meta">${alerta.prioridade || ""} · ${alerta.latencia_s ? alerta.latencia_s.toFixed(1) + " s" : "?"}</span>
      </div>
      <div class="item-corpo">${alerta.url || ""}</div>
    `;
    lista.appendChild(el);
  });
}

/* ---------- Alertas: poll ---------- */
async function pollAlertas() {
  const resposta = await fetch(`${API_BASE}/alertas/poll`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ perfil_id: "mirex-demo" }),
  });
  if (!resposta.ok) {
    toast("Erro ao poll alertas: " + resposta.statusText);
    return;
  }
  const data = await resposta.json();
  if (data.novas.length > 0) {
    toast(`${data.novas.length} alerta(s) novo(s)`);
    carregarAlertas();
  }
}

/* ---------- Compor: preview ---------- */
async function previewPeca(pecaId) {
  const resposta = await fetch(`${API_BASE}/pecas/${pecaId}/preview`);
  if (!resposta.ok) {
    toast("Erro ao carregar preview: " + resposta.statusText);
    return;
  }
  const peca = await resposta.json();
  const previewDiv = $("#upload");
  previewDiv.innerHTML = `
    <div>
      <h3>${peca.titulo || "(sem título)"}</h3>
      <div class="preview-meta">${peca.formato || "?"} · ${peca.rotulo || ""}</div>
      <div class="preview-corpo">${peca.corpo || ""}</div>
      <div class="preview-fontes">${peca.fontes ? peca.fontes.map(f => `<a href="${f.url}" target="_blank">${f.titulo || f.url}</a>`).join(", ") : ""}</div>
    </div>
  `;
}

/* ---------- Compor: exportar ---------- */
async function exportarPeca(pecaId, formato) {
  const resposta = await fetch(`${API_BASE}/pecas/${pecaId}/exportar.${formato}`);
  if (!resposta.ok) {
    toast("Erro ao exportar: " + resposta.statusText);
    return;
  }
  const blob = new Blob([await resposta.blob()], { type: formato === "pdf" ? "application/pdf" : "image/png" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `altars-${pecaId}.${formato}`;
  a.click();
  URL.revokeObjectURL(url);
  toast(`Exportado como ${formato.toUpperCase()}`);
}

/* ---------- Renderização ---------- */
function renderizarRedacao() {
  if (!pecaGerada) return;
  const previewDiv = $("#upload");
  previewDiv.innerHTML = `
    <div>
      <h3>${pecaGerada.titulo || "(sem título)"}</h3>
      <div class="preview-meta">${pecaGerada.formato || "?"} · ${pecaGerada.rotulo || ""}</div>
      <div class="preview-corpo">${pecaGerada.corpo || ""}</div>
      <div class="preview-fontes">${pecaGerada.fontes ? pecaGerada.fontes.map(f => `<a href="${f.url}" target="_blank">${f.titulo || f.url}</a>`).join(", ") : ""}</div>
      <button class="btn btn-primary" id="btn-aprovar">Rever e aprovar</button>
    </div>
  `;
  $("#btn-aprovar").addEventListener("click", () => {
    const nota = prompt("Nota de revisão (opcional):", "");
    aprovarPeca(pecaGerada.peca_id, "Demo", nota || null);
  });
}

/* ---------- Inicialização ---------- */
document.addEventListener("DOMContentLoaded", () => {
  carregarInbox();
  carregarPecas();
  carregarAlertas();
  setInterval(pollAlertas, 60000); // Poll a cada 1 minuto
});