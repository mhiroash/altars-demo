/* ============================================================
   Altars — demo editorial: interações
   Tabs acessíveis · pesquisa · gerar · revisão · composição
   ============================================================ */
"use strict";

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

/* ---------- Toast ---------- */
let toastTimer;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 4000);
}

/* ---------- Separadores (tabs acessíveis) ---------- */
const TABS = $$(".appbar .tab");
const VIEWS = {
  "tab-recolha": "view-recolha",
  "tab-editor": "view-editor",
  "tab-alertas": "view-alertas",
  "tab-composicao": "view-composicao"
};

function activateTab(id) {
  TABS.forEach(t => {
    const on = t.id === id;
    t.setAttribute("aria-selected", on ? "true" : "false");
    t.tabIndex = on ? 0 : -1;
  });
  Object.entries(VIEWS).forEach(([tab, view]) => {
    const v = document.getElementById(view);
    const on = tab === id;
    v.hidden = !on;
    v.classList.toggle("hidden", !on);
  });
}

TABS.forEach((t, i) => {
  t.addEventListener("click", () => activateTab(t.id));
  t.addEventListener("keydown", e => {
    let j = null;
    if (e.key === "ArrowRight") j = (i + 1) % TABS.length;
    if (e.key === "ArrowLeft")  j = (i - 1 + TABS.length) % TABS.length;
    if (e.key === "Home") j = 0;
    if (e.key === "End")  j = TABS.length - 1;
    if (j !== null) { e.preventDefault(); TABS[j].focus(); activateTab(TABS[j].id); }
  });
});

/* ---------- Pesquisa na Inbox ---------- */
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
    $("#recolha-empty-search").classList.toggle("hidden", vis > 0);
  });
}
const limpar = $("#limpar-filtros");
if (limpar) limpar.addEventListener("click", e => {
  e.preventDefault();
  searchInput.value = "";
  searchInput.dispatchEvent(new Event("input"));
});

/* ---------- Inbox: arquivar e redigir ---------- */
$$(".act-arquivar").forEach(b => b.addEventListener("click", () => {
  b.closest(".item").remove();
  toast("Item guardado no arquivo.");
  if (searchInput) searchInput.dispatchEvent(new Event("input"));
}));

let pecaRevista = false;

function abrirEditor() {
  activateTab("tab-editor");
  $("#editor-vazio").classList.add("hidden");
  $("#peca").classList.remove("hidden");
  const chip = $("#chip-estado");
  chip.className = "chip chip-generated";
  $("#chip-estado-txt").textContent = "Rascunho — Redigida pela IA. Falta a sua revisão.";
  pecaRevista = false;
  $("#aviso-fontes").classList.remove("hidden");
  contarPalavras();
}

$$(".act-transformar").forEach(b => b.addEventListener("click", () => {
  abrirEditor();
  toast("Peça aberta no Redigir — requer revisão.");
}));
$$(".corrigir").forEach(a => a.addEventListener("click", e => {
  e.preventDefault();
  toast("Tema corrigido (demo).");
}));

/* ---------- Ação global: Nova peça ---------- */
const btnNova = $("#btn-nova");
if (btnNova) btnNova.addEventListener("click", () => {
  activateTab("tab-editor");
  toast("Defina formato e tom e gere a peça.");
});

/* ---------- Redigir: redação ---------- */
const btnGerar = $("#btn-gerar");
if (btnGerar) btnGerar.addEventListener("click", () => {
  $("#gerar-erro").classList.add("hidden");
  $("#gerando").classList.remove("hidden");
  btnGerar.disabled = true;
  setTimeout(() => {
    $("#gerando").classList.add("hidden");
    btnGerar.disabled = false;
    abrirEditor();
    toast("Peça redigida — requer revisão.");
  }, 2400);
});

/* ---------- Redigir: instrução em linguagem natural ---------- */
const btnAplicar = $("#btn-aplicar");
if (btnAplicar) btnAplicar.addEventListener("click", () => {
  const v = $("#input-instrucao").value.trim();
  if (!v) { toast("Escreva primeiro o que quer mudar."); return; }
  $("#input-instrucao").value = "";
  toast(`Aplicado: “${v}” (demo — sem reescrita real).`);
});

/* ---------- Redigir: revisão e envio ---------- */
const btnRevista = $("#btn-marcar-revista");
if (btnRevista) btnRevista.addEventListener("click", () => {
  pecaRevista = true;
  const chip = $("#chip-estado");
  chip.className = "chip chip-reviewed";
  $("#chip-estado-txt").textContent = "Revista — Revista por [nome] às 14:32. Pronta a exportar.";
  $("#aviso-fontes").classList.add("hidden");
  toast("Peça revista — pode ir para composição.");
});

const btnEnviar = $("#btn-enviar-composicao");
if (btnEnviar) btnEnviar.addEventListener("click", () => {
  if (!pecaRevista) {
    $("#export-bloqueio").classList.remove("hidden");
    toast("Só peças revistas vão para composição.");
    return;
  }
  activateTab("tab-composicao");
  toast("Peça revista carregada em Compor.");
});

const btnVersao = $("#btn-guardar-versao");
if (btnVersao) btnVersao.addEventListener("click", () => toast("Versão guardada no histórico."));

/* ---------- Redigir: contagem de palavras ---------- */
function contarPalavras() {
  const txt = $("#peca").innerText.trim();
  $("#palavras").textContent = txt ? `${txt.split(/\s+/).length} palavras` : "";
}
$$("#peca [contenteditable]").forEach(el =>
  el.addEventListener("input", contarPalavras));

/* ---------- Alertas: abrir peça proposta ---------- */
$$(".act-abrir-peca").forEach(b => b.addEventListener("click", () => {
  abrirEditor();
  toast("Peça proposta aberta no Redigir.");
}));

/* ---------- Compor ---------- */
const selPeca = $("#sel-peca");
if (selPeca) selPeca.addEventListener("change", () => toast("Peça trocada (demo)."));

const inputAnt = $("#input-antetitulo");
const inputTit = $("#input-titulo");
const previewAnt = $(".preview-antetitulo");
const previewTit = $(".preview-titulo");
if (inputAnt && previewAnt) inputAnt.addEventListener("input", () => previewAnt.textContent = inputAnt.value);
if (inputTit && previewTit) inputTit.addEventListener("input", () => previewTit.textContent = inputTit.value);

/* Imagem: arrastar ou escolher ficheiro */
const upload = $("#upload");
const uploadLink = $("#upload-link");
const uploadErro = $("#upload-erro");
const previewImg = $(".preview-img");
let temImagem = false;

function aplicarImagem(file) {
  if (!file) return;
  if (!/image\/(jpeg|png)/.test(file.type)) {
    uploadErro.classList.remove("hidden");
    return;
  }
  uploadErro.classList.add("hidden");
  temImagem = true;
  const url = URL.createObjectURL(file);
  previewImg.style.backgroundImage = `url(${url})`;
  previewImg.classList.add("com-imagem");
}

if (upload) {
  ["dragover", "dragenter"].forEach(ev =>
    upload.addEventListener(ev, e => { e.preventDefault(); upload.classList.add("drag"); }));
  ["dragleave", "drop"].forEach(ev =>
    upload.addEventListener(ev, e => { e.preventDefault(); upload.classList.remove("drag"); }));
  upload.addEventListener("drop", e => aplicarImagem(e.dataTransfer.files[0]));
  upload.addEventListener("click", () => {
    const inp = document.createElement("input");
    inp.type = "file";
    inp.accept = "image/jpeg,image/png";
    inp.onchange = () => aplicarImagem(inp.files[0]);
    inp.click();
  });
}
if (uploadLink) uploadLink.addEventListener("click", e => e.preventDefault());

/* Exportação: bloqueada sem peça revista */
const exportBloqueio = $("#export-bloqueio");
function bloquearExportacao() {
  exportBloqueio.classList.remove("hidden");
  toast("Só peças revistas podem ser exportadas.");
}
["btn-exportar-pdf", "btn-exportar-png", "btn-copiar"].forEach(id => {
  const b = document.getElementById(id);
  if (b) b.addEventListener("click", () => {
    if (!pecaRevista) { bloquearExportacao(); return; }
    if (id === "btn-copiar") {
      navigator.clipboard?.writeText($("#peca") ? $("#peca").innerText : "")
        .then(() => toast("Texto copiado."))
        .catch(() => toast("Não foi possível copiar."));
    } else {
      toast("Ficheiro gerado (demo) — em produção, sai em PNG/JPG sem cortes de texto.");
    }
  });
});
if (exportBloqueio) exportBloqueio.classList.add("hidden");
