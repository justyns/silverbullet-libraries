---
name: Library/justyns/AI Tool - SearXNG search
tags: meta/library
---

## SearXNG Web Search Integration

> **note** This is a tool meant to be used by the [Silverbullet-ai plug](https://github.com/justyns/silverbullet-ai) and it’s tool support.  Please see the [tools docs](https://ai.silverbullet.md/Tools/) for more information.

Search the web using a [SearXNG](https://docs.searxng.org/) instance.  Requires API support to be enabled.

### Configuration

Set your SearXNG instance URL in Space Lua:

```lua
config.set("searxng.url", "https://searx.my.private.domain.internal")
```

### Tool Definition

```space-lua
ai.tools.web_search = {
  description = "Search the web using SearXNG and return results with titles, URLs, and snippets.",
  parameters = {
    type = "object",
    properties = {
      searchQuery = {type = "string", description = "Search query terms."},
      pageno = {type = "integer", description = "Page number for pagination. Default: 1"}
    },
    required = {"searchQuery"}
  },
  handler = function(args)
    local baseUrl = config.get("searxng.url")
    if not baseUrl then
      return "Error: SearXNG URL not configured. Set it with: config.set('searxng.url', 'https://your-instance.com')"
    end

    local body = "q=" .. js.window.encodeURIComponent(args.searchQuery) .. "&format=json"
    if args.pageno then
      body = body .. "&pageno=" .. tostring(args.pageno)
    end

    local response = net.proxyFetch(baseUrl .. "/search", {
      method = "POST",
      headers = {["Content-Type"] = "application/x-www-form-urlencoded"},
      body = body
    })
    if not response.ok then
      return "Search failed with status: " .. tostring(response.status)
    end

    local data = response.body
    if not data.results or #data.results == 0 then
      return "No results found for: " .. args.searchQuery
    end

    local resultStr = "Found " .. #data.results .. " results for '" .. args.searchQuery .. "':\n\n"
    local count = 0
    for _, result in ipairs(data.results) do
      if count >= 10 then break end
      count = count + 1
      local title = result.title or "No title"
      local resultUrl = result.url or ""
      local content = result.content or ""
      local engine = result.engine or ""

      resultStr = resultStr .. "## " .. title .. "\n"
      resultStr = resultStr .. "**URL:** " .. resultUrl .. "\n"
      if engine ~= "" then
        resultStr = resultStr .. "**Source:** " .. engine .. "\n"
      end
      if content ~= "" then
        resultStr = resultStr .. content .. "\n"
      end
      resultStr = resultStr .. "\n"
    end

    if data.suggestions and #data.suggestions > 0 then
      resultStr = resultStr .. "---\n**Suggestions:** " .. table.concat(data.suggestions, ", ") .. "\n"
    end

    return resultStr
  end
}
```
