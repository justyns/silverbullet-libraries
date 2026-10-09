---
name: Library/justyns/Agent IDE/Agent IDE
author: justyns
tags: meta/library
files:
- ide_server.py
- diff.min.js
---
# Agent IDE

Needs [[^Library/justyns/Terminal/Terminal]] to also be installed.

Claude Code has an IDE integration feature used for IDEs like vscode/neovim.   This library bundles [[Library/justyns/Agent IDE/ide_server.py]] which emulates that protocol and allows claude code to connect to silverbullet for some nicer ux.  

Mainly, it'll send the name of the page you're currently viewing as well as any selected text.

There's also an `openDiff` modal bundled that claude can use to show you a diff to approve before editing pages.

## Claude Code

Configure a terminal session for claude code:

```lua
config.set("terminal.sessions", {
  {name = "shell", title = "Terminal", command = "Terminal: Toggle", run = "bash"},
  {name = "claude", title = "Claude Code", command = "Terminal: Claude Code", run = "CLAUDE_CODE_SSE_PORT=7682 ENABLE_IDE_INTEGRATION=true $HOME/.local/bin/claude --ide"},
})
```

Set `agentIde.server` if the server is not on `localhost:7682`.

Run `/ide` in claude code if it doesn't automatically connect.

When Claude Code asks to edit a file in the space, SilverBullet can show the diff to accept or reject. Auto mode and accept-edits mode don't ask. To review page edits in those modes too, add `ask` rules to `.claude/settings.json` in the space folder:

```json
{
  "permissions": {
    "ask": ["Edit(./**/*.md)", "Write(./**/*.md)"]
  }
}
```

Edits Claude Code makes through shell commands skip these rules.

## Codex

The same server answers Codex's `/ide` command with the current page and selection, through `~/.codex/ipc/ipc.sock`. Codex has no diff or open-file support there. Add a session for it:

```lua
{name = "codex", title = "Codex", command = "Terminal: Codex", run = "codex"},
```

Run `/ide` in Codex to turn it on. If the VS Code Codex extension already owns the socket, the server leaves it alone.


---

## Code

```space-style
.sb-agent-diff {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 16px;
  background: var(--modal-backdrop-color, rgba(0, 0, 0, 0.4));
  --agent-diff-border: 1px solid var(--modal-border-color, rgba(128, 128, 128, 0.3));
}

.sb-agent-diff-dialog {
  display: flex;
  flex-direction: column;
  width: min(1400px, calc(100% - 32px));
  height: calc(100% - 80px);
  min-width: 400px;
  min-height: 200px;
  max-width: calc(100% - 32px);
  max-height: calc(100% - 32px);
  resize: both;
  background: var(--modal-background-color, var(--root-background-color));
  color: var(--modal-color, var(--root-color));
  border: var(--agent-diff-border);
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
  font-family: var(--ui-font);
  overflow: hidden;
  outline: none;
}

.sb-agent-diff-header, .sb-agent-diff-footer {
  display: flex;
  gap: 0.75em;
  align-items: center;
  padding: 0.75em 1em;
}

.sb-agent-diff-header {
  justify-content: space-between;
  border-bottom: var(--agent-diff-border);
}

.sb-agent-diff-title {
  display: flex;
  flex-direction: column;
  gap: 0.15em;
  min-width: 0;
}

.sb-agent-diff-title strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sb-agent-diff-label {
  font-size: 0.8em;
  color: var(--subtle-color);
}

.sb-agent-diff-stats {
  display: flex;
  gap: 0.6em;
  font-family: var(--editor-font, monospace);
  font-size: 0.9em;
}

.sb-agent-diff-footer {
  justify-content: flex-end;
  border-top: var(--agent-diff-border);
}

.sb-agent-diff-footer kbd {
  margin-left: 0.6em;
  font-family: var(--ui-font);
  font-size: 0.75em;
  opacity: 0.7;
}

.sb-agent-diff-body {
  flex: 1;
  overflow: auto;
  padding: 0.4em 0;
  font-family: var(--editor-font, monospace);
  font-size: 0.85em;
  line-height: 1.5;
}

.sb-agent-diff-row {
  display: grid;
  grid-template-columns: 3.5em 3.5em 1.5em 1fr;
}

.sb-agent-diff-no {
  padding-right: 0.75em;
  text-align: right;
  color: var(--subtle-color);
  opacity: 0.7;
  user-select: none;
}

.sb-agent-diff-marker {
  text-align: center;
  user-select: none;
}

.sb-agent-diff-text {
  padding-right: 1em;
  white-space: pre-wrap;
  word-break: break-word;
}

.sb-agent-diff-add { background: rgba(46, 160, 67, 0.15); }
.sb-agent-diff-del { background: rgba(248, 81, 73, 0.15); }
.sb-agent-diff-plus, .sb-agent-diff-add .sb-agent-diff-marker { color: #3fb950; }
.sb-agent-diff-minus, .sb-agent-diff-del .sb-agent-diff-marker { color: #f85149; }

.sb-agent-diff-row mark {
  color: inherit;
  border-radius: 2px;
}

.sb-agent-diff-add mark { background: rgba(46, 160, 67, 0.4); }
.sb-agent-diff-del mark { background: rgba(248, 81, 73, 0.4); }

.sb-agent-diff-gap {
  padding: 0.2em 0 0.2em 7em;
  color: var(--subtle-color);
  user-select: none;
}
```

```space-lua
-- priority: -20
-- Runs after the Terminal library, which defines terminalBridgeToken.
config.define("agentIde", {
  type = "object",
  properties = {
    server = {type = "string", default = "localhost:7682", description = "Host and port of the Agent IDE server, as seen from the SilverBullet server"},
  },
})

-- claudeCode.ideServer is the setting's name before the library was renamed.
local function ideServer()
  return config.get("claudeCode.ideServer") or config.get("agentIde.server")
end

local function serverCommand()
  local port = ideServer():match(":(%d+)$") or "7682"
  return "python3 'Library/justyns/Agent IDE/ide_server.py' --cwd . --port " .. port
end

command.define {
  name = "Agent IDE: Start Server",
  hide = true,
  run = function() terminalStartDetached("Agent IDE server", serverCommand()) end
}

command.define {
  name = "Agent IDE: Restart Server",
  run = function()
    terminalBridgePost(ideServer(), "/shutdown")
    terminalStartDetached("Agent IDE server", serverCommand(), 1)
    editor.flashNotification("Restarting the Agent IDE server")
  end
}

command.define {
  name = "Agent IDE: Open Page",
  hide = true,
  run = function(args)
    local page, startText = args[1], args[2]
    local ok, content = pcall(space.readPage, page)
    local pos = ok and startText and content:find(startText, 1, true)
    editor.navigate(pos and (page .. "@" .. (pos - 1)) or page)
  end
}

-- While connected to the IDE server's events, report the page and selection every second,
-- and open the pages and diffs that Claude Code sends.
js.window.eval([[
  (() => {
    const state = window.sbAgentIde || (window.sbAgentIde = {});
    clearInterval(state.timer);
    state.control?.abort();
    const control = state.control = new AbortController();
    let connected = false, triedStart = false, lastSelection;
    const sb = client.httpSpacePrimitives;
    const base = sb.url.slice(0, -"/.fs".length) + "/.proxy/]] .. ideServer() .. [[";
    const auth = { "X-Proxy-Header-Authorization": "Bearer ]] .. terminalBridgeToken() .. [[" };
    const post = (path, body) => sb.authenticatedFetch(base + path, { method: "POST", headers: auth, body: JSON.stringify(body) }, 0);

    const syncState = (force) => {
      const editorState = client.editorView.state, { from, to } = editorState.selection.main, page = client.currentName();
      const key = `${page}@${from}-${to}`;
      if (key === lastSelection && !force) return;
      lastSelection = key;
      const position = (pos) => {
        const line = editorState.doc.lineAt(pos);
        return [line.number - 1, pos - line.from];
      };
      post("/ide/state", { page, text: editorState.sliceDoc(from, to), start: position(from), end: position(to) }).catch(() => {});
    };
    state.timer = setInterval(() => {
      if (connected && !document.hidden) syncState();
    }, 1000);

    let jsdiff;
    const loadJsdiff = async () => {
      if (jsdiff) return jsdiff;
      const file = await client.space.readDocument("Library/justyns/Agent IDE/diff.min.js");
      const exports = {};
      new Function("exports", "module", new TextDecoder().decode(file.data))(exports, {});
      return jsdiff = exports;
    };

    const diffs = state.diffs || (state.diffs = new Map());
    const closeDiff = (id) => {
      diffs.get(id)?.remove();
      diffs.delete(id);
    };
    const answerDiff = async (id, accepted) => {
      const resp = await post("/ide/diff", { id, accepted });
      if (resp.headers.get("x-proxy-status-code") !== "204") {
        client.ui.flashNotification("Claude Code no longer waits for this diff", "error");
      }
      closeDiff(id);
    };
    const showDiff = async ({ id, page, old, new: proposed }) => {
      if (diffs.has(id)) return;
      const { structuredPatch, diffWordsWithSpace } = await loadJsdiff();
      const patch = structuredPatch(page, page, old, proposed, "", "", { context: 3 });
      const el = (tag, className, text) => Object.assign(document.createElement(tag), { className, textContent: text ?? "" });
      const row = (kind, oldNo, newNo, marker, content) => {
        const r = el("div", "sb-agent-diff-row sb-agent-diff-" + kind);
        const text = el("span", "sb-agent-diff-text");
        text.append(...[content].flat());
        r.append(el("span", "sb-agent-diff-no", oldNo), el("span", "sb-agent-diff-no", newNo),
          el("span", "sb-agent-diff-marker", marker), text);
        return r;
      };
      // Word-level highlights for a deleted line and the added line that replaces it.
      const words = (from, to, side) => diffWordsWithSpace(from, to)
        .filter((part) => !(side === "del" ? part.added : part.removed))
        .map((part) => part.added || part.removed ? el("mark", "", part.value) : part.value);

      const body = el("div", "sb-agent-diff-body");
      let added = 0, removed = 0;
      patch.hunks.forEach((hunk, i) => {
        if (i > 0) body.append(el("div", "sb-agent-diff-gap", "⋯"));
        let oldNo = hunk.oldStart, newNo = hunk.newStart;
        const lines = hunk.lines.filter((line) => "+- ".includes(line.charAt(0)));
        for (let j = 0; j < lines.length;) {
          if (lines[j].charAt(0) === " ") {
            body.append(row("ctx", oldNo++, newNo++, "", lines[j++].slice(1)));
            continue;
          }
          const dels = [], adds = [];
          while (j < lines.length && lines[j].charAt(0) === "-") dels.push(lines[j++].slice(1));
          while (j < lines.length && lines[j].charAt(0) === "+") adds.push(lines[j++].slice(1));
          removed += dels.length;
          added += adds.length;
          const paired = dels.length === adds.length;
          dels.forEach((line, k) => body.append(row("del", oldNo++, null, "−", paired ? words(line, adds[k], "del") : line)));
          adds.forEach((line, k) => body.append(row("add", null, newNo++, "+", paired ? words(dels[k], line, "add") : line)));
        }
      });
      if (!patch.hunks.length) body.append(el("div", "sb-agent-diff-gap", "No changes"));

      const overlay = el("div", "sb-agent-diff");
      const dialog = el("div", "sb-agent-diff-dialog");
      dialog.tabIndex = -1;
      const size = JSON.parse(localStorage.getItem("agentIdeDiffSize"));
      if (size) Object.assign(dialog.style, { width: size.width + "px", height: size.height + "px" });
      dialog.addEventListener("mouseup", () => {
        if (dialog.style.width) {
          localStorage.setItem("agentIdeDiffSize", JSON.stringify({ width: dialog.offsetWidth, height: dialog.offsetHeight }));
        }
      });
      overlay.style.top = (document.getElementById("sb-top")?.getBoundingClientRect().bottom ?? 0) + "px";
      const header = el("div", "sb-agent-diff-header");
      const title = el("div", "sb-agent-diff-title");
      title.append(el("span", "sb-agent-diff-label", "Claude Code wants to edit"), el("strong", "", page));
      const stats = el("div", "sb-agent-diff-stats");
      stats.append(el("span", "sb-agent-diff-plus", "+" + added), el("span", "sb-agent-diff-minus", "−" + removed));
      header.append(title, stats);
      const footer = el("div", "sb-agent-diff-footer");
      const reject = el("button", "sb-button", "Reject");
      const accept = el("button", "sb-button-primary", "Accept");
      reject.append(el("kbd", "", "Esc"));
      accept.append(el("kbd", "", "Ctrl-Enter"));
      reject.onclick = () => answerDiff(id, false);
      accept.onclick = () => answerDiff(id, true);
      footer.append(reject, accept);
      dialog.append(header, body, footer);
      overlay.append(dialog);
      overlay.addEventListener("keydown", (e) => {
        e.stopPropagation();
        if (e.key === "Escape") answerDiff(id, false);
        else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) answerDiff(id, true);
      });
      diffs.set(id, overlay);
      document.body.append(overlay);
      dialog.focus();
    };

    const handleEvent = (event) => {
      if (event.type === "open") {
        client.runCommandByName("Agent IDE: Open Page", [event.page, event.startText]);
      } else if (event.type === "diff") {
        showDiff(event).catch((e) => console.error("Claude Code diff failed", e));
      } else if (event.type === "closeDiff") {
        closeDiff(event.id);
      }
    };

    (async () => {
      while (!control.signal.aborted) {
        try {
          const resp = await sb.authenticatedFetch(base + "/ide/events", { signal: control.signal, headers: auth }, 0);
          if (resp.headers.get("x-proxy-status-code") === "200") {
            connected = true;
            syncState(true);
            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            for (;;) {
              const { done, value } = await reader.read();
              if (done) break;
              buffer += decoder.decode(value, { stream: true });
              const events = buffer.split("\n\n");
              buffer = events.pop();
              for (const event of events) {
                if (event.startsWith("data: ")) handleEvent(JSON.parse(event.slice(6)));
              }
            }
          }
        } catch (e) {
          if (control.signal.aborted) return;
        }
        if (!connected && !triedStart) {
          triedStart = true;
          await client.runCommandByName("Agent IDE: Start Server").catch((e) => console.error(e));
          await new Promise((resolve) => setTimeout(resolve, 1500));
          continue;
        }
        connected = false;
        diffs.forEach((overlay) => overlay.remove());
        diffs.clear();
        await new Promise((resolve) => setTimeout(resolve, 10000));
      }
    })();
  })();
]])
```
