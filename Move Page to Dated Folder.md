---
tags: meta
---
# Move Page to Dated Folder

Adds a `Page: Move to Dated Folder` command that moves the current page into `<folder>/YYYY/` or `<folder>/YYYY/MM-Month/`.

The date comes from the first of:
1. A `YYYY-MM-DD` prefix on the page name
2. A `dateCreated` frontmatter attribute
3. The page's `created` timestamp

Configure the folders to use in your CONFIG page:

```lua
config.set("movePage.folders", {
  {folder = "Receipts", month = true},
  {folder = "Archived"},
})
```

## Implementation

```space-lua
movePage = {}

config.define("movePage.folders", {
  description = "Folders offered by Page: Move to Dated Folder",
  type = "array",
  items = {
    type = "object",
    properties = {
      folder = schema.string(),
      month = schema.boolean(),
    },
    required = {"folder"},
  },
  default = {},
})

local monthNames = {"January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"}

-- Returns the year and month to file a page under, as strings like "2025", "07".
function movePage.pageDate(name)
  local y, m = name:match("([^/]+)$"):match("^(%d%d%d%d)-(%d%d)")
  if not y then
    local page = (query[[from p = index.pages() where p.name == name]])[1]
    y, m = tostring(page.dateCreated or page.created):match("^(%d%d%d%d)-(%d%d)")
  end
  if not y then
    error("No date found for " .. name)
  end
  return y, m
end

function movePage.toDatedFolder(folder, includeMonth)
  local name = editor.getCurrentPage()
  local y, m = movePage.pageDate(name)
  local prefix = folder .. "/" .. y .. "/"
  if includeMonth then
    prefix = prefix .. m .. "-" .. monthNames[tonumber(m)] .. "/"
  end
  if system.invokeFunction("index.renamePageCommand", {page = prefix .. name:match("([^/]+)$")}) then
    editor.flashNotification("Moved to " .. prefix)
  end
end

command.define {
  name = "Page: Move to Dated Folder",
  requireMode = "rw",
  run = function()
    local folders = config.get("movePage.folders")
    if #folders == 0 then
      editor.flashNotification("Set movePage.folders in your CONFIG page first", "error")
      return
    end
    local options = {}
    for _, f in ipairs(folders) do
      local pattern = f.folder .. (f.month and "/YYYY/MM-Month/" or "/YYYY/")
      table.insert(options, {name = f.folder, description = pattern, month = f.month})
    end
    local choice = editor.filterBox("Move to", options)
    if choice then
      movePage.toDatedFolder(choice.name, choice.month)
    end
  end
}
```
