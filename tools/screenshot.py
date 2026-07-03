#!/usr/bin/env python3
"""Genera el screenshot SVG del README con el render real del monitor.

Por defecto usa sesiones DEMO (proyectos ficticios) para no filtrar nombres
de proyectos reales en el repo público. Con --live usa las sesiones vivas
de esta máquina (solo para uso local, no commitear ese output). Uso:

  python3 tools/screenshot.py docs/demo.svg [ancho_cols] [--live]
"""

import html
import os
import re
import sys
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src", "claudios.py")

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

# ── datos demo (ficticios a propósito) ──────────────────────────────────

DEMO_ROWS = [
    {"pid": 41231, "name": "api-payments", "cwd": "/Users/dev/work/api-payments",
     "sessionId": "demo1", "status": "waiting", "bg": False, "age": 254,
     "waitingFor": "permiso para Bash(git push)"},
    {"pid": 38112, "name": "infra-terraform", "cwd": "/Users/dev/work/infra-terraform",
     "sessionId": "demo2", "status": "idle", "bg": False, "age": 7620, "waitingFor": ""},
    {"pid": 44903, "name": "webapp-checkout", "cwd": "/Users/dev/work/webapp-checkout",
     "sessionId": "demo3", "status": "idle", "bg": False, "age": 2700, "waitingFor": ""},
    {"pid": 45120, "name": "blog-engine", "cwd": "/Users/dev/personal/blog-engine",
     "sessionId": "demo4", "status": "idle", "bg": False, "age": 740, "waitingFor": ""},
    {"pid": 46011, "name": "scraper-openlibrary", "cwd": "/Users/dev/personal/scraper-openlibrary",
     "sessionId": "demo5", "status": "idle", "bg": False, "age": 190, "waitingFor": ""},
    {"pid": 39557, "name": "data-pipeline", "cwd": "/Users/dev/work/data-pipeline",
     "sessionId": "demo6", "status": "busy", "bg": True, "age": 1860, "waitingFor": ""},
    {"pid": 47332, "name": "mobile-app", "cwd": "/Users/dev/work/mobile-app",
     "sessionId": "demo7", "status": "busy", "bg": False, "age": 1140, "waitingFor": ""},
    {"pid": 48208, "name": "docs-site", "cwd": "/Users/dev/work/docs-site",
     "sessionId": "demo8", "status": "busy", "bg": False, "age": 65, "waitingFor": ""},
]

DEMO_SNIPPETS = {
    "/Users/dev/work/api-payments":
        "Los 3 tests de reembolsos pasan. Necesito tu ok para pushear el fix — toca el flujo de cobros.",
    "/Users/dev/work/infra-terraform":
        "Plan aplicado en staging: 12 recursos. Prod requiere tu aprobación manual del plan.",
    "/Users/dev/work/webapp-checkout":
        "Migré el carrito a server actions y los e2e pasan. Pendiente decidir si cacheamos el catálogo.",
    "/Users/dev/personal/blog-engine":
        "Listo el post sobre el release. ¿Lo publico o quieres revisar el borrador antes?",
    "/Users/dev/personal/scraper-openlibrary":
        "El rate-limit era el problema: con backoff exponencial ya no se cae. Quedó corriendo el backfill.",
}

DEMO_TTYS = {41231: "s003", 38112: "s007", 44903: "s012", 45120: "s001",
             46011: "s019", 39557: "s005", 47332: "s009", 48208: "s014"}

DEMO_DOCKER = {
    "state": "ok",
    "rows": [
        {"name": "postgres-local", "cpu": 0.3, "mem": 210 * 2**20, "limit": 8 * 2**30},
        {"name": "webapp-dev", "cpu": 1.2, "mem": 182 * 2**20, "limit": 8 * 2**30},
        {"name": "mailhog", "cpu": 0.0, "mem": 41 * 2**20, "limit": 8 * 2**30},
        {"name": "redis-cache", "cpu": 0.1, "mem": 12 * 2**20, "limit": 8 * 2**30},
    ],
}
DEMO_DOCKER["cpu"] = sum(r["cpu"] for r in DEMO_DOCKER["rows"])
DEMO_DOCKER["mem"] = sum(r["mem"] for r in DEMO_DOCKER["rows"])
DEMO_DOCKER["limit"] = 8 * 2**30

# ── ANSI → SVG ──────────────────────────────────────────────────────────


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


def frame_lines(m, cols, live):
    if live:
        m.refresh_slow()
        rows = m.collect()
    else:
        m.SLOW.update({"docker": DEMO_DOCKER, "therm": None,
                       "batt": {"pct": 100, "ac": True, "temp": 30.6}})
        m.ttys_for = lambda pids: DEMO_TTYS
        m.last_assistant_text = (
            lambda cwd, sid, max_len:
            DEMO_SNIPPETS.get(cwd, "")[:max_len])
        m.HOME = "/Users/dev"
        rows = DEMO_ROWS
    frame, _ = m.render(rows, cols, show_keys=True, docker_detail=True)
    return frame


def main():
    args = [a for a in sys.argv[1:] if a != "--live"]
    live = "--live" in sys.argv
    out_path = args[0] if args else "docs/demo.svg"
    cols = int(args[1]) if len(args) > 1 else 100
    m = SourceFileLoader("claudios", SRC).load_module()
    frame = frame_lines(m, cols, live)
    frame += ("\n\n" + m.DIM
              + " refresca cada 3s · tecla = ir a esa sesión · d docker · q salir"
              + m.RESET)
    svg = to_svg(frame, cols, "Claudios — claude-monitor")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as fh:
        fh.write(svg)
    print(f"✓ {out_path} ({len(svg) // 1024}KB, {cols} cols, "
          f"{'LIVE — no commitear' if live else 'demo'})")


if __name__ == "__main__":
    main()
