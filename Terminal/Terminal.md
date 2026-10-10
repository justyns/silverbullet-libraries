---
name: Library/justyns/Terminal/Terminal
author: justyns
tags: meta/library
files:
- bridge.py
- xterm.js
- addon-fit.js
- xterm.css
---
# Terminal

Adds a terminal in a [View](https://docs.silverbullet.md/View) that you can toggle.


## Configuration

Set `terminal.sessions` to configure what you want to launch.  e.g. just "bash" or "zsh" if you want a regular terminal.  If available, screen or tmux would  be a good idea too.


Each session gets a tab in one terminal view, and its command opens that tab.

```lua
config.set("terminal.sessions", {
  {name = "shell", title = "Terminal", command = "Terminal: Toggle", run = "bash"},
  {name = "claude", title = "Claude Code", command = "Terminal: Claude Code", run = "$HOME/.local/bin/claude"},
})
```

For Claude Code and Codex integration, see [[Library/justyns/Agent IDE/Agent IDE]].

Set `terminal.bridge` if the bridge is not on `localhost:7681`.

## Usage

Run the command set in `terminal.sessions` like `Terminal: Toggle`.  It'll start a pty->sse bridge automatically with the `run` command and open a modal or docked view that has [xterm.js](https://xtermjs.org/) embedded and connecting to that bridge.

## Requirements / Caveats

- [shell.run](https://docs.silverbullet.md/API/shell) must be enabled for the space
- python must be available
- This _probably_ works with the PWA, but I've only tested it using the SilverBullet+ Electron/Desktop app so far on linux w/ flatpak.
- Any command you want to run has to be accessible from the SB server, meaning inside the flatpak sandbox for the linux desktop app.  Or the docker image if using docker.
  - For things like claude code, they usually install somewhere under `$HOME` which flatpak allows access to currently.
  - [mise](https://mise.jdx.dev/) is also useful for installing stuff at the user-level.
- This runs a [[Library/justyns/Terminal/bridge.py]] python script in the background that holds a virtual PTY open and xterm.js connects to it.

> **warning** Warning
> **Disclosure**: FWIW, this code was mostly generated using AI.

---

## Code

```space-style
.sb-nav-content:has(> .sb-terminal-tabs) {
  height: 100%;
  padding: 0;
}

.sb-terminal-tabs {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--root-background-color);
}

.sb-terminal-tabbar {
  display: flex;
  gap: 2px;
  padding: 0 8px;
  border-bottom: 1px solid var(--ui-surface-border-color);
}

.sb-terminal-tabbar:has(> :only-child) {
  display: none;
}

.sb-terminal-tab {
  padding: 4px 10px;
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--subtle-color);
  font: inherit;
  font-size: 0.85em;
  cursor: pointer;
}

.sb-terminal-tab:hover {
  color: var(--root-color);
}

.sb-terminal-tab.active {
  color: var(--root-color);
  border-bottom-color: var(--ui-accent-color);
}

.sb-modal:has(.sb-terminal-frame) {
  width: min(1100px, 90%);
  height: calc(100% - 200px);
}

.sb-nav-root-modal:has(.sb-terminal-frame) {
  height: 100%;
}

.sb-nav-root-modal .sb-nav-body:has(.sb-terminal-frame) {
  flex: 1;
  max-height: none;
}

.sb-terminal-frame {
  flex: 1;
  min-height: 0;
  width: 100%;
  border: none;
}

.sb-terminal-frame:not(.active) {
  display: none;
}
```

```space-lua
-- priority: -10
-- Negative priority runs this after CONFIG, so terminal.sessions includes the user's sessions.
config.define("terminal", {
  type = "object",
  properties = {
    bridge = {type = "string", default = "localhost:7681", description = "Host and port of the terminal bridge, as seen from the SilverBullet server"},
    sessions = {
      type = "array",
      description = "Bridge sessions, each shown as a tab in the terminal view with a command that opens it",
      items = {
        type = "object",
        properties = {
          name = schema.string(), title = schema.string(), command = schema.string(), run = schema.string(),
          startupInput = {type = "string", description = "Text to send followed by Enter once per new process"},
          startupDelay = {type = "number", minimum = 0, description = "Milliseconds to wait before sending startupInput (default: 0)"},
        },
        required = {"name", "title", "command", "run"},
      },
      default = {{name = "shell", title = "Terminal", command = "Terminal: Toggle", run = "bash"}},
    },
  },
})

local function shellQuote(s)
  return "'" .. (s:gsub("'", "'\\''")) .. "'"
end

local function jsString(s)
  return '"' .. ((s:gsub("\\", "\\\\")):gsub('"', '\\"')) .. '"'
end

-- The shell command that starts the bridge with every configured session, run from the space folder.
local function bridgeCommand()
  local port = config.get("terminal.bridge"):match(":(%d+)$") or "7681"
  local parts = {"python3 Library/justyns/Terminal/bridge.py --cwd . --port " .. port}
  for _, session in ipairs(config.get("terminal.sessions")) do
    table.insert(parts, "--session " .. shellQuote(session.name .. "=" .. session.run))
    if session.startupInput ~= nil then
      table.insert(parts, "--startup-input " .. shellQuote(session.name .. "=" .. session.startupInput))
      table.insert(parts, "--startup-delay " .. shellQuote(session.name .. "=" .. tostring(session.startupDelay or 0)))
    end
  end
  return table.concat(parts, " ")
end

-- Inside a flatpak (such as SilverBullet Desktop), XDG folders point into the app's sandbox
-- TODO: I'm hardcoding some paths here to make it easier to use things outside of the sandbox
local flatpakEnv = 'if [ -n "$FLATPAK_ID" ]; then'
  .. ' export SB_ELECTRON_DATA="${SB_ELECTRON_DATA:-$XDG_CONFIG_HOME/SilverBullet+ Electron}";'
  .. ' export'
  .. ' XDG_CONFIG_HOME="$HOME/.config" XDG_DATA_HOME="$HOME/.local/share"'
  .. ' XDG_STATE_HOME="$HOME/.local/state" XDG_CACHE_HOME="$HOME/.cache"'
  .. ' PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"; fi; '

local token

-- The bearer token from .bridge-token in the space folder, which the bridge and the Agent IDE
-- server also read. bridge.py creates the file if it's missing.
function terminalBridgeToken()
  if not token then
    local result = shell.run("python3", {"Library/justyns/Terminal/bridge.py", "--cwd", ".", "--print-token"})
    local t = string.trim(result.stdout)
    if result.code ~= 0 or t == "" then
      error("Could not read .bridge-token: " .. result.stderr)
    end
    token = t
  end
  return token
end

-- Runs command detached from the space folder after delay seconds, which a restart uses to let
-- the old process free its port.
function terminalStartDetached(label, command, delay)
  local result = shell.run("sh", {"-c", flatpakEnv .. "(sleep " .. (delay or 0) .. "; setsid "
    .. command .. ") >/dev/null 2>&1 &"})
  if result.code ~= 0 then
    editor.flashNotification("Could not start the " .. label .. ": " .. result.stderr, "error")
  end
end

-- A POST to the bridge or the Agent IDE server, as pcall's ok and response.
function terminalBridgePost(hostPort, path, body)
  return pcall(net.proxyFetch, "http://" .. hostPort .. path, {
    method = "POST",
    headers = {Authorization = "Bearer " .. terminalBridgeToken()},
    body = body,
  })
end

command.define {
  name = "Terminal: Start Bridge",
  hide = true,
  run = function() terminalStartDetached("terminal bridge", bridgeCommand()) end
}

command.define {
  name = "Terminal: Restart Bridge",
  run = function()
    terminalBridgePost(config.get("terminal.bridge"), "/shutdown")
    terminalStartDetached("terminal bridge", bridgeCommand(), 1)
    editor.flashNotification("Restarting the terminal bridge. Press Enter in a terminal to reconnect.")
  end
}

-- TODO: maybe move the html to a separate file to make it easier to read?
local function terminalPage(session)
  local bridge = config.get("terminal.bridge")
  return '<style>html, body { margin: 0; height: 100%; } #term { height: 100%; }</style><div id="term"></div><script>' .. [[
          (async () => {
            const sb = parent.client.httpSpacePrimitives;
            const base = sb.url.slice(0, -"/.fs".length) + "/.proxy/]] .. bridge .. "/" .. session .. [[";
            const auth = { "X-Proxy-Header-Authorization": "Bearer ]] .. terminalBridgeToken() .. [[" };
            const call = (path, options = {}) => sb.authenticatedFetch(base + path, { ...options, headers: auth }, 0);

            const root = getComputedStyle(parent.document.documentElement);
            document.documentElement.style.colorScheme = root.getPropertyValue("color-scheme");
            const read = async (file) =>
              new TextDecoder().decode((await parent.client.space.readDocument("Library/justyns/Terminal/" + file)).data);
            const [css, ...scripts] = await (parent.sbTerminalAssets ??= Promise.all(["xterm.css", "xterm.js", "addon-fit.js"].map(read)));
            document.head.append(Object.assign(document.createElement("style"), { textContent: css }));
            for (const code of scripts) {
              document.head.append(Object.assign(document.createElement("script"), { textContent: code }));
            }
            const { Terminal, FitAddon: { FitAddon } } = window;
            const term = new Terminal({
              cursorBlink: true,
              theme: {
                background: root.getPropertyValue("--root-background-color").trim(),
                foreground: root.getPropertyValue("--root-color").trim(),
              },
            });
            const fit = new FitAddon();
            term.loadAddon(fit);
            term.open(document.getElementById("term"));

            const fromBase64 = (s) => {
              const bin = atob(s), bytes = new Uint8Array(bin.length);
              for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
              return bytes;
            };

            // OSC 52 ("c;BASE64"), which Claude Code and tmux use to copy to the clipboard.
            term.parser.registerOscHandler(52, (data) => {
              const b64 = data.slice(data.indexOf(";") + 1);
              if (b64 === "?") return true;
              const text = new TextDecoder().decode(fromBase64(b64));
              parent.navigator.clipboard.writeText(text).catch((e) => {
                const area = document.createElement("textarea");
                area.value = text;
                document.body.append(area);
                area.select();
                const copied = document.execCommand("copy");
                area.remove();
                term.focus();
                if (!copied) console.error("Terminal copy failed", e);
              });
              return true;
            });

            const sendSize = () => {
              fit.fit();
              call("/resize", { method: "POST", body: JSON.stringify({ cols: term.cols, rows: term.rows }) });
            };
            new ResizeObserver(sendSize).observe(document.getElementById("term"));

            // Keystrokes are sent one request at a time so they arrive in order.
            let pending = "", sending = false, connected = false, triedStart = false;
            const flush = async () => {
              if (sending || !pending) return;
              sending = true;
              const data = pending;
              pending = "";
              await call("/input", { method: "POST", body: data });
              sending = false;
              flush();
            };
            const send = (data) => {
              pending += data;
              flush();
            };
            // While disconnected, Enter retries the connection.
            term.onData((data) => connected ? send(data) : data === "\r" && connect());
            // Shift-Enter sends ESC CR (Alt-Enter), which Claude Code reads as a newline.
            term.attachCustomKeyEventHandler((e) => {
              if (e.key !== "Enter" || !e.shiftKey) return true;
              if (e.type === "keydown" && connected) send("\x1b\r");
              return false;
            });
            term.focus();
            addEventListener("focus", () => term.focus());

            // The stream is fetched through the main window, so it has to be cancelled when the view closes.
            const streamControl = new AbortController();
            addEventListener("pagehide", () => streamControl.abort());
            const help = "\r\nRun Terminal: Restart Bridge, or start it from the space folder:\r\n  "
              + ]] .. jsString(bridgeCommand()) .. [[ + "\r\nPress Enter to retry.\r\n";

            const readStream = async (resp) => {
              const reader = resp.body.getReader();
              const decoder = new TextDecoder();
              let buffer = "";
              for (;;) {
                const { done, value } = await reader.read();
                if (done) return;
                buffer += decoder.decode(value, { stream: true });
                const events = buffer.split("\n\n");
                buffer = events.pop();
                for (const event of events) {
                  if (event.startsWith("event: exit")) {
                    term.write("\r\n[process exited, reopen the terminal to restart]\r\n");
                    continue;
                  }
                  for (const line of event.split("\n")) {
                    if (line.startsWith("data: ")) {
                      term.write(fromBase64(line.slice(6)));
                    }
                  }
                }
              }
            };

            const connect = async () => {
              let resp;
              try {
                resp = await call("/stream", { signal: streamControl.signal });
              } catch (e) {
                if (streamControl.signal.aborted) return;
              }
              const status = resp && (resp.headers.get("x-proxy-status-code") || String(resp.status));
              if (status !== "200") {
                if (!triedStart) {
                  triedStart = true;
                  term.write("[starting the terminal bridge]\r\n");
                  await parent.client.runCommandByName("Terminal: Start Bridge");
                  await new Promise((r) => setTimeout(r, 1500));
                  return connect();
                }
                const reason = status === "404" ? "the bridge has no session named ]] .. session .. [[" : "the terminal bridge is not reachable at ]] .. bridge .. [[";
                term.write("\r\n[" + reason + "]" + help);
                return;
              }
              connected = true;
              sendSize();
              try {
                await readStream(resp);
              } catch (e) {
                if (streamControl.signal.aborted) return;
              }
              connected = false;
              term.write("\r\n[lost the connection to the terminal bridge]" + help);
            };

            connect();
          })();
  ]] .. '</script>'
end

-- The terminal view's tabs. A tab's iframe loads, and its session starts, when the tab is first selected.
js.window.eval([[
  (() => {
    const tabs = window.sbTerminalTabs ??= {};
    tabs.active ??= localStorage.getItem("sbTerminalActiveTab");
    tabs.isOpen = () => !!tabs.root?.isConnected;
    tabs.close = () => tabs.root.closest(".sb-nav-root").querySelector(".sb-nav-close").click();
    tabs.select = (name) => {
      tabs.active = name;
      localStorage.setItem("sbTerminalActiveTab", name);
      for (const el of tabs.root.querySelectorAll("[data-session]")) {
        el.classList.toggle("active", el.dataset.session === name);
      }
      const frame = tabs.root.querySelector(`iframe[data-session="${CSS.escape(name)}"]`);
      frame.srcdoc ||= frame.dataset.srcdoc;
      frame.contentWindow?.focus();
    };
    tabs.mount = (root) => {
      tabs.root = root;
      root.firstChild.addEventListener("click", (e) => {
        const tab = e.target.closest("[data-session]");
        if (tab) tabs.select(tab.dataset.session);
      });
      const names = [...root.firstChild.children].map((tab) => tab.dataset.session);
      tabs.select(names.includes(tabs.active) ? tabs.active : names[0]);
    };
    clearTimeout(tabs.restoreTimer);
    tabs.restoreTimer = setTimeout(() => client.runCommandByName("Terminal: Restore Dock"), 100);
  })();
]])

local sessions = config.get("terminal.sessions")

view.define {
  name = "terminal",
  title = "Terminal",
  dock = "modal",
  supportedDocks = {"modal", "bhs", "rhs", "lhs"},
  content = function()
    local doc = js.window.document
    local root = doc.createElement("div")
    root.className = "sb-terminal-tabs"
    local bar = doc.createElement("div")
    bar.className = "sb-terminal-tabbar"
    root.appendChild(bar)
    for _, session in ipairs(sessions) do
      local tab = doc.createElement("button")
      tab.className = "sb-terminal-tab"
      tab.textContent = session.title
      tab.setAttribute("data-session", session.name)
      bar.appendChild(tab)
      local frame = doc.createElement("iframe")
      frame.className = "sb-terminal-frame"
      frame.allow = "clipboard-read; clipboard-write"
      frame.setAttribute("data-session", session.name)
      frame.setAttribute("data-srcdoc", terminalPage(session.name))
      root.appendChild(frame)
    end
    js.window.sbTerminalTabs.mount(root)
    return root
  end,
}

-- At boot, SilverBullet can restore a docked terminal while a script reload has the view unregistered,
-- which leaves the dock showing "No navigator view named terminal". The timer above runs this after the last script load.
command.define {
  name = "Terminal: Restore Dock",
  hide = true,
  run = function()
    if js.window.sbTerminalTabs.isOpen() then return end
    for _, slot in ipairs({"lhs", "rhs", "bhs"}) do
      if datastore.get({"navigator", "docked", slot}) == "terminal" then
        view.open("terminal")
        return
      end
    end
  end
}

for _, session in ipairs(sessions) do
  command.define {
    name = session.command,
    run = function()
      local tabs = js.window.sbTerminalTabs
      if not tabs.isOpen() then
        tabs.active = session.name
        view.open("terminal")
      elseif tabs.active == session.name then
        tabs.close()
      else
        tabs.select(session.name)
      end
    end,
  }
end
```
