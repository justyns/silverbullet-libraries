---
name: Library/justyns/AI Tool - Silversearch
tags: meta/library
---

## Silversearch integration

> **note** This is a tool meant to be used by the [Silverbullet-ai plug](https://github.com/justyns/silverbullet-ai) and it’s tool support.  Please see the [tools docs](https://ai.silverbullet.md/Tools/) for more information.

Integration with the [Silversearch](https://github.com/MrMugame/silversearch) plug.  Allows the llm to query your space using silversearch and retrieve results.

```space-lua
ai.tools.search_notes = {
  description = "Search Silverbullet space and return results with excerpts.",
  parameters = {
    type = "object",
    properties = {
      searchQuery = {type = "string", description = "Query terms to search for."}
    },
    required = {"searchQuery"}
  },
  handler = function(args)
    local results = system.invokeFunction("silversearch.search", args.searchQuery, { silent = false })
    if not results or #results == 0 then
      return "No results found for: " .. args.searchQuery
    end
    local resultStr = "Found " .. #results .. " results:\n\n"
    for _, result in ipairs(results) do
      local ref = result.ref or result.path or result.basename or "unknown"
      local score = result.score and tostring(result.score) or "?"
      resultStr = resultStr .. "## " .. ref .. " (score: " .. score .. ")\n"
      if result.excerpts and #result.excerpts > 0 then
        for _, excerpt in ipairs(result.excerpts) do
          resultStr = resultStr .. "  > " .. (excerpt.excerpt or "") .. "\n"
        end
      end
      resultStr = resultStr .. "\n"
    end
    return resultStr
  end
}
```