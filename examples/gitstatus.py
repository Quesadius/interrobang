"""A git staging helper: see changes, stage/unstage, and commit — like a tiny
lazygit. Run it inside a git repository:

    python examples/gitstatus.py

↑/↓ move · space (or s) stage/unstage the file · a stage all · u unstage all ·
c commit staged changes (type a message, Enter) · r refresh · q quit.
"""

import subprocess

from interrobang import KeyMsg, get_theme, quit
from interrobang.components import TextInput
from interrobang.style import Style


def git(*args):
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True
        )
    except FileNotFoundError:
        return None


class GitStatus:
    def __init__(self):
        self.entries: list[dict] = []
        self.branch = ""
        self.cursor = 0
        self.error = ""
        self.status_line = ""
        self.committing = False
        self.message = TextInput()
        self.message.prompt = "message › "
        self.message.blur()
        self._refresh()

    def init(self):
        return None

    # -- git plumbing ------------------------------------------------------

    def _refresh(self):
        self.error = ""
        res = git("status", "--porcelain")
        if res is None:
            self.error = "git is not installed"
            self.entries = []
            return
        if res.returncode != 0:
            self.error = res.stderr.strip() or "not a git repository"
            self.entries = []
            return
        entries = []
        for line in res.stdout.splitlines():
            if len(line) < 4:
                continue
            x, y, path = line[0], line[1], line[3:]
            if " -> " in path:  # rename: keep the new name
                path = path.split(" -> ", 1)[1]
            entries.append({"x": x, "y": y, "path": path})
        self.entries = entries
        self.cursor = min(self.cursor, max(0, len(entries) - 1))
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
        self.branch = branch.stdout.strip() if branch and branch.returncode == 0 else ""

    def _staged(self, entry):
        return entry["x"] not in (" ", "?")

    def _toggle_stage(self):
        if not self.entries:
            return
        entry = self.entries[self.cursor]
        if self._staged(entry):
            git("reset", "-q", "--", entry["path"])
        else:
            git("add", "--", entry["path"])
        self._refresh()

    # -- update ------------------------------------------------------------

    def update(self, msg):
        if self.committing:
            return self._commit_key(msg)
        if isinstance(msg, KeyMsg):
            key = msg.key
            if key in ("q", "ctrl+c"):
                return self, quit
            if key in ("up", "k"):
                self.cursor = max(0, self.cursor - 1)
            elif key in ("down", "j"):
                self.cursor = min(len(self.entries) - 1, self.cursor + 1) if self.entries else 0
            elif key in ("space", "enter", "s"):
                self._toggle_stage()
            elif key == "a":
                git("add", "-A")
                self._refresh()
            elif key == "u":
                git("reset", "-q")
                self._refresh()
            elif key == "r":
                self._refresh()
            elif key == "c":
                if any(self._staged(e) for e in self.entries):
                    self.committing = True
                    self.message.reset()
                    self.message.focus()
                else:
                    self.status_line = "nothing staged to commit"
        return self, None

    def _commit_key(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key == "enter":
                text = self.message.value.strip()
                if text:
                    res = git("commit", "-m", text)
                    ok = res is not None and res.returncode == 0
                    self.status_line = "committed ✓" if ok else "commit failed"
                self.committing = False
                self.message.blur()
                self._refresh()
                return self, None
            if msg.key == "esc":
                self.committing = False
                self.message.blur()
                return self, None
        self.message.update(msg)
        return self, None

    # -- view --------------------------------------------------------------

    def view(self):
        t = get_theme()
        head = f"Git · {self.branch}" if self.branch else "Git"
        header = Style().bold().foreground(t.primary).render(head)

        if self.error:
            return f"{header}\n\n{Style().foreground(t.selection).render(self.error)}"

        lines = []
        if not self.entries:
            lines.append(Style().foreground(t.gradient_end).render("  working tree clean ✓"))
        for i, e in enumerate(self.entries):
            staged = self._staged(e)
            if staged:
                color, mark = t.gradient_end, "●"
            elif e["x"] == "?":
                color, mark = t.muted, "?"
            else:
                color, mark = t.selection, "○"
            code = Style().faint().render(f"{e['x']}{e['y']} ")
            path = Style().foreground(color).render(f"{mark} {e['path']}")
            prefix = Style().foreground(t.selection).bold().render("> ") if i == self.cursor else "  "
            lines.append(prefix + code + path)

        if self.committing:
            footer = "commit staged changes:\n\n  " + self.message.view()
        else:
            hint = self.status_line or "space stage · a all · u reset · c commit · r refresh · q quit"
            footer = Style().foreground(t.muted).render(hint)
        return f"{header}\n\n" + "\n".join(lines) + f"\n\n{footer}"


if __name__ == "__main__":
    from _shared import run_example

    run_example(GitStatus())
