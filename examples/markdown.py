"""A scrolling Markdown reader that styles a useful subset: headings, bold,
italics, inline code, links, bullet lists, blockquotes, code fences, and rules.

    python examples/markdown.py README.md
    python examples/markdown.py            # a built-in sample

Scroll with ↑/↓/PgUp/PgDn/g/G (or j/k); q quits.
"""

import re
import sys

from interrobang import KeyMsg, WindowSizeMsg, get_theme, quit, wrap
from interrobang.components import Viewport
from interrobang.style import Style

SAMPLE = """\
# interrobang ‽

A **pure-Python** toolkit for building *terminal* user interfaces, with an
Elm-style runtime and a fluent styling engine.

## Why

- zero dependencies — just the standard library
- a chainable `Style` engine with `join`/`place` layout
- ready-made components and a few [themes](styling.md)

> Punctuation deserves better tools.

---

## Quick start

```
import interrobang as irb
irb.run(App(), alt_screen=True)
```

That's the whole idea: a *model*, an `update`, and a `view`.
"""

_INLINE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))")
_RULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")


class Markdown:
    def __init__(self, text: str | None = None, title: str = "markdown"):
        self.raw = SAMPLE if text is None else text
        self.title = title
        self.viewport = Viewport(width=80, height=20)
        self._reflow()

    def init(self):
        return None

    def _reflow(self):
        self.viewport.set_content(self._render(self.raw, self.viewport.width))

    # -- rendering ---------------------------------------------------------

    def _inline(self, text):
        t = get_theme()
        out = []
        for seg in _INLINE.split(text):
            if not seg:
                continue
            if seg.startswith("`") and seg.endswith("`"):
                out.append(Style().foreground(t.gradient_end).render(seg[1:-1]))
            elif seg.startswith("**") and seg.endswith("**"):
                out.append(Style().bold().render(seg[2:-2]))
            elif (seg.startswith("*") and seg.endswith("*")) or (seg.startswith("_") and seg.endswith("_")):
                out.append(Style().italic().render(seg[1:-1]))
            elif seg.startswith("[") and "](" in seg:
                out.append(Style().underline().foreground(t.primary).render(seg[1 : seg.index("]")]))
            else:
                out.append(seg)
        return "".join(out)

    def _render(self, md, width):
        t = get_theme()
        out = []
        in_code = False
        for line in md.split("\n"):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                out.append(Style().foreground(t.muted).render("  " + line))
                continue
            s = line.rstrip()
            if not s:
                out.append("")
            elif _RULE.match(s):
                out.append(Style().foreground(t.muted).render("─" * min(width, 60)))
            elif s.startswith("### "):
                out.append(Style().bold().foreground(t.secondary).render(s[4:]))
            elif s.startswith("## "):
                out.append(Style().bold().foreground(t.primary).render(s[3:]))
            elif s.startswith("# "):
                out.append(Style().bold().underline().foreground(t.primary).render(s[2:]))
            elif s.startswith("> "):
                bar = Style().foreground(t.muted).render("│ ")
                for piece in wrap(s[2:], max(1, width - 2)).split("\n"):
                    out.append(bar + self._inline(piece))
            elif re.match(r"^\s*[-*]\s+", s):
                m = re.match(r"^(\s*)[-*]\s+(.*)", s)
                indent, rest = m.group(1), m.group(2)
                pieces = wrap(rest, max(1, width - 2 - len(indent))).split("\n")
                out.append(indent + Style().foreground(t.selection).render("• ") + self._inline(pieces[0]))
                out.extend(indent + "  " + self._inline(p) for p in pieces[1:])
            else:
                out.extend(self._inline(piece) for piece in wrap(s, max(1, width)).split("\n"))
        return "\n".join(out)

    # -- update / view -----------------------------------------------------

    def update(self, msg):
        if isinstance(msg, WindowSizeMsg):
            self.viewport.width = max(20, msg.width)
            self.viewport.height = max(3, msg.height - 2)
            self._reflow()
            return self, None
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        self.viewport, _ = self.viewport.update(msg)
        return self, None

    def view(self):
        t = get_theme()
        header = (
            Style().bold().foreground(t.on_primary).background(t.primary)
            .width(self.viewport.width).render(f" {self.title}")
        )
        pct = int(self.viewport.scroll_percent() * 100)
        footer = Style().foreground(t.muted).render(f"{pct:>3}%  ·  ↑/↓ scroll · q quit")
        return f"{header}\n{self.viewport.view()}\n{footer}"


if __name__ == "__main__":
    from _shared import run_example

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        with open(args[0], encoding="utf-8", errors="replace") as f:
            run_example(Markdown(f.read(), title=args[0]), tty=True)
    elif not sys.stdin.isatty():
        run_example(Markdown(sys.stdin.read(), title="stdin"), tty=True)
    else:
        run_example(Markdown(), tty=True)
