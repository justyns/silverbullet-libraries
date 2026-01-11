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

# Custom Share Commands

You can create shortcuts for frequently used repos using `forgejo.shareTo()`. Add commands like this to a separate Space Lua page:

```
forgejo.shareTo(host, repo, branch, pathTransform, extraFrontmatter)
```

* `host` - Forgejo/Gitea hostname (must have a token configured)
* `repo` - Repository in `owner/repo` format
* `branch` - Branch name
* `pathTransform` - Optional function `(pageName) -> path` to transform page names to file paths
* `extraFrontmatter` - Optional table of `{key = value}` pairs to add to the file's frontmatter

Example:

```lua
-- Share to a docs repo with path mapping and extra frontmatter
command.define {
  name = "Share: My Docs",
  run = function()
    forgejo.shareTo("forgejo.example.com", "user/docs", "main", function(page)
      -- Notes/Changelog/2025/foo -> docs/notes/changelog/2025/foo.md
      local rest = page:match("^Notes/Changelog/(.+)$")
      if rest then
        return "docs/notes/changelog/" .. rest:lower() .. ".md"
      end

      -- Notes/foo -> docs/notes/foo.md
      rest = page:match("^Notes/(.+)$")
      if rest then
        return "docs/notes/" .. rest:lower() .. ".md"
      end

      -- No match - use page name as-is
      return page .. ".md"
    end, {
      sync_source = "silverbullet"
    })
  end
}
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

function forgejo.getDirCacheKey(host, repo, branch)
  return {"forgejo", "dirCache", host .. "/" .. repo .. "@" .. branch}
end

function forgejo.listDirs(host, repo, branch, path, maxDepth, forceRefresh)
  path = path or ""
  maxDepth = maxDepth or 5
  cachettl = 30 * 60 * 1000

  -- Check cache first
  local cacheKey = forgejo.getDirCacheKey(host, repo, branch)
  if not forceRefresh then
    local cached = datastore.get(cacheKey)
    if cached and (os.time() * 1000 - cached.timestamp) < cachettl then
      return cached.dirs
    end
  end

  -- Not cached, so call the api and g et a recursive list
  local dirs = {{name = "/", path = ""}}

  local function fetchDirs(currentPath, depth)
    if depth > maxDepth then return end
    local url = forgejo.buildAPIURL(host, repo, currentPath) .. "?ref=" .. branch
    local resp = forgejo.request(host, url, "GET")
    if resp.status ~= 200 then return end

    for _, item in ipairs(resp.body) do
      if item.type == "dir" then
        table.insert(dirs, {name = item.path, path = item.path})
        fetchDirs(item.path, depth + 1)
      end
    end
  end

  fetchDirs(path, 1)

  -- Save to local datastore to make sharing to the same repo faster
  datastore.set(cacheKey, {dirs = dirs, timestamp = os.time() * 1000})

  return dirs
end

function forgejo.clearDirCache(host, repo, branch)
  datastore.del(forgejo.getDirCacheKey(host, repo, branch))
end

-- Remember repos we've shared to
function forgejo.getRecentRepos()
  return datastore.get({"forgejo", "recentRepos"}) or {}
end

function forgejo.addRecentRepo(host, repo, branch)
  local key = host .. "/" .. repo .. "@" .. branch
  local recent = forgejo.getRecentRepos()

  -- Remove if already exists (to move to top)
  for i, r in ipairs(recent) do
    if r.key == key then
      table.remove(recent, i)
      break
    end
  end

  -- Add to top
  table.insert(recent, 1, {
    key = key,
    host = host,
    repo = repo,
    branch = branch,
    name = repo .. "@" .. branch
  })

  -- Keep only last 10
  while #recent > 10 do
    table.remove(recent)
  end

  datastore.set({"forgejo", "recentRepos"}, recent)
end

function forgejo.pickRepo()
  local recent = forgejo.getRecentRepos()
  local options = {}

  for _, r in ipairs(recent) do
    table.insert(options, {name = r.name, host = r.host, repo = r.repo, branch = r.branch})
  end
  table.insert(options, {name = "+ New repo...", isNew = true})

  local choice = editor.filterBox("Select repo", options, "Pick a repo or add new")
  if not choice then return nil end

  if choice.isNew then
    local host = editor.prompt("Host (e.g. forgejo.example.com):")
    if not host then return nil end
    local repo = editor.prompt("Repository (owner/repo):")
    if not repo then return nil end
    local branch = editor.prompt("Branch:", "main")
    if not branch then return nil end
    return {host = host, repo = repo, branch = branch}
  end

  return choice
end

function forgejo.pickDir(host, repo, branch)
  local dirs = forgejo.listDirs(host, repo, branch)
  table.insert(dirs, {name = "↻ Refresh directories...", isRefresh = true})

  local choice = editor.filterBox("Select directory", dirs, "Pick where to save")
  if not choice then return nil end

  if choice.isRefresh then
    forgejo.clearDirCache(host, repo, branch)
    return forgejo.pickDir(host, repo, branch) -- Recurse with fresh data
  end

  return choice.path
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
    -- Pick repo first
    local r = forgejo.pickRepo()
    if not r then return end

    local ok, err = pcall(forgejo.checkWriteConfig, r.host)
    if not ok then
      editor.flashNotification(err, "error")
      return
    end

    -- Pick directory
    local dir = forgejo.pickDir(r.host, r.repo, r.branch)
    if not dir then return end

    local filename = data.name .. ".md"
    local path = dir == "" and filename or (dir .. "/" .. filename)

    path = editor.prompt("File path:", path)
    if not path then return end

    local message = editor.prompt("Commit message:", "Add " .. path)
    if not message then return end

    local resp = forgejo.request(r.host, forgejo.buildAPIURL(r.host, r.repo, path), "POST", {
      message = message,
      branch = r.branch,
      content = encoding.base64Encode(data.text),
      committer = {
        name = config.get("forgejo.name"),
        email = config.get("forgejo.email")
      }
    })

    if resp.status == 200 or resp.status == 201 then
      forgejo.addRecentRepo(r.host, r.repo, r.branch)
      return {
        uri = "forgejo:" .. r.host .. "/" .. r.repo .. "@" .. r.branch .. "/" .. path,
        hash = share.contentHash(data.text),
        mode = "push"
      }
    end
    -- js.log("Forgejo error", resp)
    error("Failed to create file")
  end
}
```

## shareTo Helper

```space-lua
-- Helper to share current page to a specific repo
-- pathTransform: optional function(pageName) -> repoPath (used as default)
-- extraFrontmatter: optional table of {key = value} to add to frontmatter
function forgejo.shareTo(host, repo, branch, pathTransform, extraFrontmatter)
  local ok, err = pcall(forgejo.checkWriteConfig, host)
  if not ok then
    editor.flashNotification(err, "error")
    return
  end

  local pageName = editor.getCurrentPage()
  local text = editor.getText()

  local suggestedPath
  if pathTransform then
    suggestedPath = pathTransform(pageName)
  end
  if not suggestedPath then
    suggestedPath = pageName .. ".md"
  end

  -- Extract directory and filename from suggested path
  local suggestedDir, suggestedFilename = suggestedPath:match("^(.+)/([^/]+)$")
  if not suggestedDir then
    suggestedDir = ""
    suggestedFilename = suggestedPath
  end

  -- Get directories and put suggested dir first
  local forceRefresh = false
  local dir
  while true do
    local dirs = forgejo.listDirs(host, repo, branch, "", nil, forceRefresh)
    local options = {}

    if suggestedDir ~= "" then
      table.insert(options, {name = suggestedDir, path = suggestedDir})
    end

    for _, d in ipairs(dirs) do
      if d.path ~= suggestedDir then
        table.insert(options, d)
      end
    end

    table.insert(options, {name = "↻ Refresh directories...", isRefresh = true})

    local choice = editor.filterBox("Select directory", options, "Pick where to save")
    if not choice then return end

    if choice.isRefresh then
      forceRefresh = true
    else
      dir = choice.path
      break
    end
  end
  local filename = editor.prompt("Filename:", suggestedFilename)
  if not filename then return end

  local path = dir == "" and filename or (dir .. "/" .. filename)
  if not path then return end

  local message = editor.prompt("Commit message:", "Update " .. path)
  if not message then return end

  if extraFrontmatter then
    local patches = {}
    for key, value in pairs(extraFrontmatter) do
      table.insert(patches, {op = "set-key", path = key, value = value})
    end
    text = index.patchFrontmatter(text, patches)
  end

  local existing = forgejo.request(host, forgejo.buildAPIURL(host, repo, path) .. "?ref=" .. branch, "GET")
  local body = {
    message = message,
    branch = branch,
    content = encoding.base64Encode(text),
    committer = {
      name = config.get("forgejo.name"),
      email = config.get("forgejo.email")
    }
  }
  if existing.status == 200 then
    body.sha = existing.body.sha
  end

  local method = existing.status == 404 and "POST" or "PUT"
  local resp = forgejo.request(host, forgejo.buildAPIURL(host, repo, path), method, body)

  if resp.status == 200 or resp.status == 201 then
    local uri = "forgejo:" .. host .. "/" .. repo .. "@" .. branch .. "/" .. path
    local m = { uri = uri, hash = share.contentHash(text), mode = "push" }
    editor.setText(share.setFrontmatter(m, text))
    editor.flashNotification("Shared to " .. repo)
  else
    js.log("Forgejo error", resp)
    error("Failed: " .. tostring(resp.status))
  end
end
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
