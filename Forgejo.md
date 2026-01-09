---
name: Library/justyns/Forgejo
description: Integration with Forgejo/Gitea repositories.
tags: meta/library
author: justyns
---

Support for [SilverBullet Share](https://silverbullet.md/Share) and [URI](https://silverbullet.md/URIs) (read and write) for Forgejo and (probably) Gitea instances.  I’ve only really tested this with a self hosted Forgejo instance.

Supported URI schemes:
* `forgejo:host/owner/repo@branch/path/to/file.md`
* `forgejo:host/owner/repo/path/to/file.md` (defaults to `main` branch)

# Configuration

Reading from public repositories requires no configuration.

To write, configure a personal access token (with repo permissions) per instance:

```lua
config.set("forgejo.tokens", {
  ["forgejo.example.com"] = "your-token",
  ["gitea.other.org"] = "other-token"
})
config.set("forgejo.name", "Your Name")
config.set("forgejo.email", "you@example.com")
```

# Implementation

```space-lua
-- priority: 50
forgejo = {}

-- Parse forgejo:host/owner/repo@branch/path/to/file
-- Returns: host, repo (owner/repo), branch, path
function forgejo.parseURI(uri)
  local s = uri:sub(#"forgejo:" + 1)
  -- Try with explicit branch first: host/owner/repo@branch/path
  local host, owner, repo, branch, path = s:match("^([^/]+)/([^/]+)/([^/@]+)@([^/]+)/(.+)$")
  if host then
    return host, owner .. "/" .. repo, branch, path
  end
  -- Without branch: host/owner/repo/path (default to main)
  host, owner, repo, path = s:match("^([^/]+)/([^/]+)/([^/]+)/(.+)$")
  if host then
    return host, owner .. "/" .. repo, "main", path
  end
  return nil
end

function forgejo.buildRawURL(host, repo, branch, path)
  return "https://" .. host .. "/" .. repo .. "/raw/branch/" .. branch .. "/" .. path
end

function forgejo.buildAPIURL(host, repo, path)
  return "https://" .. host .. "/api/v1/repos/" .. repo .. "/contents/" .. path
end

function forgejo.getToken(host)
  local tokens = config.get("forgejo.tokens")
  return tokens and tokens[host]
end

function forgejo.request(host, url, method, body)
  local token = forgejo.getToken(host)
  if not token then
    error("No token for " .. host)
  end
  return net.proxyFetch(url, {
    method = method,
    headers = {
      Authorization = "token " .. token,
      Accept = "application/json",
      ["Content-Type"] = "application/json"
    },
    body = body
  })
end

function forgejo.checkWriteConfig(host)
  if not forgejo.getToken(host) then
    error("forgejo.tokens." .. host .. " not set")
  end
  if not config.get("forgejo.name") then
    error("forgejo.name not set")
  end
  if not config.get("forgejo.email") then
    error("forgejo.email not set")
  end
end
```

## Share Onboarding

```space-lua
service.define {
  selector = "share:onboard",
  match = {
    name = "Forgejo/Gitea",
    description = "Share as a file on a Forgejo/Gitea repo"
  },
  run = function(data)
    local host = editor.prompt("Host (e.g. forgejo.example.com):")
    if not host then return end

    local ok, err = pcall(forgejo.checkWriteConfig, host)
    if not ok then
      editor.flashNotification(err, "error")
      return
    end

    local repo = editor.prompt("Repository (owner/repo):")
    if not repo then return end

    local branch = editor.prompt("Branch:", "main")
    if not branch then return end

    local path = editor.prompt("File path:", data.name .. ".md")
    if not path then return end

    local message = editor.prompt("Commit message:", "Add " .. path)
    if not message then return end

    local resp = forgejo.request(host, forgejo.buildAPIURL(host, repo, path), "POST", {
      message = message,
      branch = branch,
      content = encoding.base64Encode(data.text),
      committer = {
        name = config.get("forgejo.name"),
        email = config.get("forgejo.email")
      }
    })

    if resp.ok then
      return {
        uri = "forgejo:" .. host .. "/" .. repo .. "@" .. branch .. "/" .. path,
        hash = share.contentHash(data.text),
        mode = "push"
      }
    end
    js.log("Forgejo error", resp)
    error("Failed to create file")
  end
}
```

## Read URI

```space-lua
service.define {
  selector = "net.readURI:forgejo:*",
  match = {priority = 10},
  run = function(data)
    local host, repo, branch, path = forgejo.parseURI(data.uri)
    if not host then return nil end

    local res = net.proxyFetch(forgejo.buildRawURL(host, repo, branch, path))
    if res.status ~= 200 then return nil end
    return res.body
  end
}
```

## Write URI

```space-lua
service.define {
  selector = "net.writeURI:forgejo:*",
  match = {priority = 10},
  run = function(data)
    local host, repo, branch, path = forgejo.parseURI(data.uri)
    if not host then
      error("Invalid forgejo URI")
    end

    local ok, err = pcall(forgejo.checkWriteConfig, host)
    if not ok then
      editor.flashNotification(err, "error")
      return
    end

    -- Get existing file SHA (if it exists)
    local existing = forgejo.request(host, forgejo.buildAPIURL(host, repo, path) .. "?ref=" .. branch, "GET")
    local sha = nil
    local isNew = existing.status == 404
    if existing.status == 200 then
      sha = existing.body.sha
    elseif existing.status ~= 404 then
      error("Could not fetch file: " .. tostring(existing.status))
    end

    local defaultMsg = isNew and ("Add " .. path) or ("Update " .. path)
    local message = editor.prompt("Commit message:", defaultMsg)
    if not message then return end

    local body = {
      message = message,
      branch = branch,
      content = encoding.base64Encode(data.content),
      committer = {
        name = config.get("forgejo.name"),
        email = config.get("forgejo.email")
      }
    }
    if sha then
      body.sha = sha
    end

    local method = isNew and "POST" or "PUT"
    local resp = forgejo.request(host, forgejo.buildAPIURL(host, repo, path), method, body)

    if resp.status ~= 200 and resp.status ~= 201 then
      js.log("Forgejo error", resp)
      error("Failed to " .. (isNew and "create" or "update") .. " file: " .. tostring(resp.status))
    end
  end
}
```
