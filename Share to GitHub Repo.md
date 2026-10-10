---
tags: meta
---
# Share to GitHub Repo

Adds a `Share: to GitHub Repo` command that pushes the current page to a preconfigured GitHub repo and sets its `share.*` frontmatter, so `Share: Page` handles later updates.

Requires the `github.token`, `github.name` and `github.email` config from the standard GitHub integration. Configure the repos to offer in your CONFIG page:

```lua
config.set("githubShare.repos", {
  {repo = "justyns/silverbullet-libraries", branch = "master", command = "Share: to silverbullet-libraries"},
  {repo = "someone/notes"},
})
```

`branch` defaults to `main`. Set `command` to also add a command that shares straight to that repo.

```space-lua
githubShare = {}

config.define("githubShare.repos", {
  description = "Repos for Share: to GitHub Repo",
  type = "array",
  items = {
    type = "object",
    properties = {
      repo = schema.string(),
      branch = schema.string(),
      command = schema.string(),
    },
    required = {"repo"},
  },
  default = {},
})

function githubShare.shareTo(repo, branch)
  local ok, err = pcall(github.checkConfig)
  if not ok then
    editor.flashNotification(err, "error")
    return
  end
  branch = branch or "main"

  local pageName = editor.getCurrentPage()
  local path = editor.prompt("File path:", pageName:match("([^/]+)$") .. ".md")
  if not path then return end
  local message = editor.prompt("Commit message:", "Update " .. path)
  if not message then return end

  local text = editor.getText()
  local body = {
    message = message,
    branch = branch,
    content = encoding.base64Encode(share.cleanFrontmatter(text)),
    committer = {
      name = config.get("github.name"),
      email = config.get("github.email")
    }
  }
  local existing = github.request(github.buildAPIURLWithBranch(repo, branch, path), "GET")
  if existing.ok then
    body.sha = existing.body.sha
  end

  local resp = github.request(github.buildAPIURL(repo, path), "PUT", body)
  if not resp.ok then
    js.log("GitHub error", resp)
    error("Failed: " .. tostring(resp.status))
  end
  local m = { uri = github.buildURI(repo, branch, path), hash = share.contentHash(text), mode = "push" }
  editor.setText(share.setFrontmatter(m, text))
  editor.flashNotification("Shared to " .. repo)
end
```

```space-lua
-- priority: -1
command.define {
  name = "Share: to GitHub Repo",
  run = function()
    local repos = config.get("githubShare.repos")
    if #repos == 0 then
      editor.flashNotification("Set githubShare.repos in your CONFIG page first", "error")
      return
    end
    local choice = repos[1]
    if #repos > 1 then
      local options = {}
      for _, r in ipairs(repos) do
        table.insert(options, {name = r.repo, description = r.branch or "main", repo = r.repo, branch = r.branch})
      end
      choice = editor.filterBox("Share to", options)
      if not choice then return end
    end
    githubShare.shareTo(choice.repo, choice.branch)
  end
}

for _, r in ipairs(config.get("githubShare.repos")) do
  if r.command then
    command.define {
      name = r.command,
      run = function()
        githubShare.shareTo(r.repo, r.branch)
      end
    }
  end
end
```