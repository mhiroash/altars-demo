#!/usr/bin/env python3
"""Verificação de contraste WCAG 2.1 AA — tokens do design system Altars."""
import sys

def srgb(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lum(hex_color):
    h = hex_color.lstrip('#')
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b)

def ratio(fg, bg):
    l1, l2 = sorted((lum(fg), lum(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

PAIRS = [
    # texto primário/secundário
    ("ink-900/paper",        "#1c1917", "#faf9f7", 4.5),
    ("ink-900/surface",      "#1c1917", "#ffffff", 4.5),
    ("ink-700/paper",        "#44403c", "#faf9f7", 4.5),
    ("ink-700/surface",      "#44403c", "#ffffff", 4.5),
    ("ink-500/paper (meta)", "#57534e", "#faf9f7", 4.5),
    ("ink-500/surface (meta)","#57534e", "#ffffff", 4.5),
    ("ink-500/sunken (meta)","#57534e", "#f3f1ed", 4.5),
    # acento
    ("accent-600/surface (btn)", "#9a3412", "#ffffff", 4.5),
    ("accent-700/surface (hover)", "#7c2d12", "#ffffff", 4.5),
    ("accent-600/accent-50 (link em destaque)", "#9a3412", "#fff7ed", 4.5),
    ("branco/accent-600 (texto do botão primário)", "#ffffff", "#9a3412", 4.5),
    # chips semânticos
    ("generated-fg/generated-bg", "#92400e", "#fffbeb", 4.5),
    ("reviewed-fg/reviewed-bg",   "#166534", "#f0fdf4", 4.5),
    ("danger-fg/danger-bg",       "#991b1b", "#fef2f2", 4.5),
    ("info-fg/info-bg",           "#1e40af", "#eff6ff", 4.5),
    ("danger-fg/surface (nota em cartão)", "#991b1b", "#ffffff", 4.5),
    ("info-fg/surface (nota em cartão)",   "#1e40af", "#ffffff", 4.5),
    ("reviewed-fg/surface (chip em cartão)", "#166534", "#ffffff", 4.5),
    ("generated-fg/surface (chip em cartão)", "#92400e", "#ffffff", 4.5),
    # toast
    ("branco/ink-900 (toast)", "#ffffff", "#1c1917", 4.5),
]

fails = 0
for name, fg, bg, need in PAIRS:
    r = ratio(fg, bg)
    ok = r >= need
    fails += 0 if ok else 1
    print(f"{'OK ' if ok else 'FALHA'}  {r:5.2f}:1  (min {need}:1)  {name}")

print(f"\n{len(PAIRS) - fails}/{len(PAIRS)} pares aprovados" + ("" if fails == 0 else f" — {fails} falha(s)"))
sys.exit(1 if fails else 0)
