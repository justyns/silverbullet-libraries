---
tags: meta/library
---

## Web Fetch Tool

> **note** This is a tool meant to be used by the [Silverbullet-ai plug](https://github.com/justyns/silverbullet-ai) and it’s tool support.  Please see the [tools docs](https://ai.silverbullet.md/Tools/) for more information.

Fetch a URL and convert its HTML content to markdown.

```space-lua
local TurndownService = js.import("https://esm.sh/turndown@7.2.2?default")

function fetchUrlAsMarkdown(url)
  local response = net.proxyFetch(url, {
    headers = {["Accept"] = "text/html"}
  })
  if not response.ok then
    return nil, "Failed to fetch URL with status: " .. tostring(response.status)
  end

  local content = response.body
  local contentType = type(content)

  -- js.log("Response body type:", contentType)
  -- js.log("Response body:", content)

  local td = js.new(TurndownService)
  return td.turndown(content)
end

ai.tools.web_fetch = {
  description = "Fetch a URL and return its content converted to markdown.",
  parameters = {
    type = "object",
    properties = {
      url = {type = "string", description = "The URL to fetch."}
    },
    required = {"url"}
  },
  handler = function(args)
    return fetchUrlAsMarkdown(args.url)
  end
}
```
