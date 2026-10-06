---
tags: meta
---
# Markdown Utilities

Helpers shared by [[Library/justyns/Refile]] and other scripts.

### Code

```space-lua
mdutil = {}

-- ATX headings in text, in order, as {from, line}.
function mdutil.headings(text)
  local out = {}
  local function walk(node)
    for _, child in ipairs(node.children or {}) do
      if child.type and child.type:startsWith("ATXHeading") then
        table.insert(out, {from = child.from, line = text:sub(child.from + 1, child.to)})
      else
        walk(child)
      end
    end
  end
  walk(markdown.parseMarkdown(text))
  return out
end

-- Inserts block at the end of the section under heading (an entry from mdutil.headings(text)),
-- before any blank lines that end the section. Returns the new text.
function mdutil.insertUnder(text, heading, block)
  local sectionEnd = #text
  for _, h in ipairs(mdutil.headings(text)) do
    if h.from > heading.from then
      sectionEnd = h.from
      break
    end
  end
  local section = text:sub(1, sectionEnd)
  local body = string.trimEnd(section)
  return body .. "\n" .. block .. section:sub(#body + 1) .. text:sub(sectionEnd + 1)
end

-- Adds content as the last list item of text, filling an empty bullet at the end instead of
-- adding a new one. Returns the new text.
function mdutil.appendListItem(text, content)
  local body = string.trimEnd(text)
  local lastLine = body:match("[^\n]*$")
  local marker = lastLine:match("^(%s*[-*+])$")
  if marker then
    return body:sub(1, #body - #lastLine) .. marker .. " " .. content .. "\n"
  end
  return body .. "\n* " .. content .. "\n"
end

-- The whole lines covered by a ListItem node, as {from, to, block}: to includes the
-- trailing newline, and block is the item's text with its indent removed.
function mdutil.listItem(text, node)
  local from = node.from
  while from > 0 and text:sub(from, from) ~= "\n" do
    from = from - 1
  end
  local indent = node.from - from
  local lines = {}
  for _, line in ipairs(string.split(text:sub(from + 1, node.to), "\n")) do
    table.insert(lines, line:sub(math.min(#line:match("^%s*"), indent) + 1))
  end
  local to = text:sub(node.to + 1, node.to + 1) == "\n" and node.to + 1 or node.to
  return {from = from, to = to, block = table.concat(lines, "\n")}
end

-- The innermost list item containing pos, as returned by mdutil.listItem, or nil.
function mdutil.listItemAt(text, pos)
  local found
  local function walk(node)
    for _, child in ipairs(node.children or {}) do
      if child.from and child.from <= pos and pos <= child.to then
        if child.type == "ListItem" then
          found = child
        end
        walk(child)
      end
    end
  end
  walk(markdown.parseMarkdown(text))
  return found and mdutil.listItem(text, found)
end
```
