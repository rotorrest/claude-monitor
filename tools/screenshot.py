#!/usr/bin/env python3
"""Genera el screenshot SVG del README a partir del estado real del monitor.

Corre el render de src/claudes.py contra las sesiones vivas de esta máquina
y convierte la salida ANSI a un SVG con marco de terminal. Uso:

  python3 tools/screenshot.py docs/demo.svg [ancho_cols]
"""

import html
import os
import re
import sys
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src", "claudes.py")

# paleta estilo GitHub dark
BG = "#0d1117"
CHROME = "#161b22"
FG = "#c9d1d9"
COLORS = {31: "#ff7b72", 32: "#7ee787", 33: "#e3b341"}

FONT = "'SF Mono', 'JetBrains Mono', Menlo, Consolas, monospace"
FS = 13          # font-size
CW = 7.8         # ancho de celda (monospace)
LH = 19          # alto de línea
PAD = 16
BAR = 36         # barra de título

SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")


def runs(line):
    """Divide una línea ANSI en tramos (texto, color, bold, dim)."""
    out = []
    color, bold, dim = None, False, False
    pos = 0
    for m in SGR_RE.finditer(line):
        if m.start() > pos:
            out.append((line[pos:m.start()], color, bold, dim))
        for code in (m.group(1) or "0").split(";"):
            c = int(code or 0)
            if c == 0:
                color, bold, dim = None, False, False
            elif c == 1:
                bold = True
            elif c == 2:
                dim = True
            elif c == 22:
                bold = dim = False
            elif c in COLORS:
                color = c
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], color, bold, dim))
    return out


def to_svg(text, cols, title):
    lines = text.splitlines()
    w = PAD * 2 + int(cols * CW)
    h = BAR + PAD + len(lines) * LH + PAD
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}" font-size="{FS}">',
        f'<rect width="{w}" height="{h}" rx="12" fill="{BG}"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h{w - 24}a12 12 0 0 1 12 12'
        f'v{BAR - 12}h-{w}z" fill="{CHROME}"/>',
        f'<circle cx="22" cy="{BAR // 2}" r="6" fill="#ff5f57"/>',
        f'<circle cx="42" cy="{BAR // 2}" r="6" fill="#febc2e"/>',
        f'<circle cx="62" cy="{BAR // 2}" r="6" fill="#28c840"/>',
        f'<text x="{w // 2}" y="{BAR // 2 + 4}" text-anchor="middle" '
        f'fill="#8b949e">{html.escape(title)}</text>',
    ]
    y = BAR + PAD + FS
    for line in lines:
        col = 0
        for chunk, color, bold, dim in runs(line):
            if chunk.strip():
                x = PAD + col * CW
                fill = COLORS.get(color, FG)
                attrs = f'x="{x:.0f}" y="{y}" fill="{fill}"'
                if bold:
                    attrs += ' font-weight="600"'
                if dim:
                    attrs += ' opacity="0.55"'
                attrs += (f' textLength="{len(chunk) * CW:.0f}"'
                          ' lengthAdjust="spacingAndGlyphs" xml:space="preserve"')
                parts.append(f"<text {attrs}>{html.escape(chunk)}</text>")
            col += len(chunk)
        y += LH
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "docs/demo.svg"
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    m = SourceFileLoader("claudes", SRC).load_module()
    m.refresh_slow()
    frame, _ = m.render(m.collect(), cols, show_keys=True, docker_detail=True)
    frame += ("\n\n" + m.DIM
              + " refresca cada 3s · tecla = ir a esa sesión · d docker · q salir"
              + m.RESET)
    svg = to_svg(frame, cols, "claudes — claude-monitor")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as fh:
        fh.write(svg)
    print(f"✓ {out_path} ({len(svg) // 1024}KB, {cols} cols)")


if __name__ == "__main__":
    main()
