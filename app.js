/* ============================================================
   Altars — demo editorial: interações
   Tabs acessíveis · pesquisa · gerar · revisão · composição
   ============================================================ */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

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

/* ---------- Tabs (Inbox · Redigir · Alertas · Compor) ---------- */
const tabs = $$('[role="tab"]');
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

/* ---------- Inbox: pesquisa ---------- */
const searchInput = $("#search-input");
if (searchInput) {
  searchInput.addEventListener("input", () => {
    const q = searchInput.value.trim().toLowerCase();
    let vis = 0;
    $$("#recolha-lista .item").forEach(it => {
      const hit = !q || it.textContent.toLowerCase().includes(q);
      it.classList.toggle("hidden", !hit);
      if (hit) vis++;
    });
    const emptySearch = $("#recolha-empty-search");
    if (emptySearch) emptySearch.classList.toggle("hidden", vis > 0);
  });
}
const limpar = $("#limpar-filtros");
if (limpar) limpar.addEventListener("click", e => {
  e.preventDefault();
  if (searchInput) {
    searchInput.value = "";
    searchInput.dispatchEvent(new Event("input"));
  }
});

/* ---------- Inbox: estado vazio ---------- */
const recolhaLista = $("#recolha-lista");
const recolhaEmpty = $("#recolha-empty");
function atualizarVazioInbox() {
  if (!recolhaLista || !recolhaEmpty) return;
  const count = recolhaLista.querySelectorAll(".item:not(.hidden)").length;
  recolhaEmpty.classList.toggle("hidden", count > 0);
}
atualizarVazioInbox();

/* ---------- Inbox: arquivar ---------- */
$$(".act-arquivar").forEach(b => b.addEventListener("click", () => {
  const item = b.closest(".item");
  if (item) item.remove();
  toast("Item guardado no arquivo.");
  if (searchInput) searchInput.dispatchEvent(new Event("input"));
  atualizarVazioInbox();
}));

/* ---------- Inbox: corrigir tema ---------- */
$$(".corrigir").forEach(a => a.addEventListener("click", e => {
  e.preventDefault();
  toast("Tema corrigido (demo).");
}));

/* ---------- Redigir: estado da peça ---------- */
let pecaRevista = false;
function abrirEditor() {
  activateTab("tab-editor");
  const vazio = $("#editor-vazio");
  const peca = $("#peca");
  if (vazio) vazio.classList.add("hidden");
  if (peca) peca.classList.remove("hidden");
  const chip = $("#chip-estado");
  if (chip) {
    chip.className = "chip chip-generated";
    const txt = $("#chip-estado-txt");
    if (txt) txt.textContent = "Rascunho — Redigida pela IA. Falta a sua revisão.";
  }
  pecaRevista = false;
  const aviso = $("#aviso-fontes");
  if (aviso) aviso.classList.remove("hidden");
}

/* ---------- Inbox: abrir peça no Redigir ---------- */
$$(".act-transformar, .act-abrir-peca").forEach(b => b.addEventListener("click", () => {
  abrirEditor();
  toast("Peça aberta no Redigir — requer revisão.");
}));

/* ---------- Redigir: gerar ---------- */
const btnGerar = $("#btn-gerar");
if (btnGerar) btnGerar.addEventListener("click", () => {
  const erro = $("#gerar-erro");
  const gerando = $("#gerando");
  if (erro) erro.classList.add("hidden");
  if (gerando) gerando.classList.remove("hidden");
  btnGerar.disabled = true;
  setTimeout(() => {
    if (gerando) gerando.classList.add("hidden");
    btnGerar.disabled = false;
    abrirEditor();
    toast("Peça redigida — requer revisão.");
  }, 2400);
});

/* ---------- Redigir: instrução em linguagem natural ---------- */
const btnAplicar = $("#btn-aplicar");
if (btnAplicar) btnAplicar.addEventListener("click", () => {
  const inst = $("#input-instrucao");
  if (!inst || !inst.value.trim()) { toast("Escreva a instrução primeiro."); return; }
  toast("Instrução aplicada (demo).");
  inst.value = "";
});

/* ---------- Redigir: marcar como revista ---------- */
const btnRevista = $("#btn-marcar-revista");
if (btnRevista) btnRevista.addEventListener("click", () => {
  pecaRevista = true;
  const chip = $("#chip-estado");
  if (chip) {
    chip.className = "chip chip-reviewed";
    const txt = $("#chip-estado-txt");
    if (txt) txt.textContent = "Revista — pronta a compor.";
  }
  const aviso = $("#aviso-fontes");
  if (aviso) aviso.classList.add("hidden");
  toast("Peça marcada como revista.");
});

/* ---------- Redigir: enviar para composição ---------- */
const btnEnviar = $("#btn-enviar-composicao");
if (btnEnviar) btnEnviar.addEventListener("click", () => {
  if (!pecaRevista) { toast("Marque a peça como revista antes de compor."); return; }
  activateTab("tab-composicao");
  toast("Peça enviada para composição.");
});


/* ---------- Redigir: guardar versão / copiar ---------- */
const btnGuardar = $("#btn-guardar-versao");
if (btnGuardar) btnGuardar.addEventListener("click", () => toast("Versão guardada (demo)."));
const btnCopiar = $("#btn-copiar");
if (btnCopiar) btnCopiar.addEventListener("click", () => toast("Texto copiado (demo)."));

/* ---------- Redigir: upload de fonte ---------- */
const upload = $("#upload");
if (upload) upload.addEventListener("change", () => {
  const erro = $("#upload-erro");
  if (erro) erro.classList.add("hidden");
  toast("Fonte anexada (demo).");
});

/* ---------- Compor: exportação ---------- */
function exportar(tipo) {
  const bloqueio = $("#export-bloqueio");
  if (bloqueio) bloqueio.classList.add("hidden");
  toast("Exportação " + tipo + " (demo).");
}
const btnPdf = $("#btn-exportar-pdf");
if (btnPdf) btnPdf.addEventListener("click", () => exportar("PDF"));
const btnPng = $("#btn-exportar-png");
if (btnPng) btnPng.addEventListener("click", () => exportar("PNG"));

/* ---------- Ação global: Nova peça ---------- */
const btnNova = $("#btn-nova");
if (btnNova) btnNova.addEventListener("click", () => {
  activateTab("tab-editor");
  toast("Defina formato e tom e gere a peça.");
});
