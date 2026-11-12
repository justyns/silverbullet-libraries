---
name: Library/justyns/Journal Quick Add/Journal Quick Add
author: justyns
tags: meta/library
files:
- journal-quick-add.js
---
# Journal Quick Add

Adds a `Journal: Add Note` command (Ctrl-q a) that appends a timestamped bullet to today's journal entry without leaving the current page. It opens a modal editor with SilverBullet's markdown highlighting and page, tag and attribute completion. Enter adds the note, Shift-Enter starts a new line, Esc cancels.

Needs [[Library/justyns/Markdown Utilities]].

The entry is `journal.pageName(date)`, which defaults to the `journal.prefix` config followed by the date, the same page [[^Library/Std/Journal/Journal]] opens. To file entries elsewhere, define your own `journal.pageName` in a space-lua block.

The modal builds its editor from the main editor's internal extensions, so a SilverBullet update can break it. Slash commands are left out of its completion because they apply to the main editor.

## Implementation

```space-lua
-- priority: 5
function journal.pageName(dateStr)
  return config.get("journal.prefix") .. dateStr
end

-- Appends "HH:MM text" as a bullet to today's entry, creating it with the journal template's frontmatter if needed.
-- Later lines of a multi-line note are indented under the bullet.
function journal.addNote(text)
  local pageName = journal.pageName(date.today())
  local note = os.date("%H:%M") .. " " .. (text:gsub("\n", "\n  "))
  if editor.getCurrentPage() == pageName then
    editor.setText(mdutil.appendListItem(editor.getText(), note))
    return
  end
  local existing
  if space.pageExists(pageName) then
    existing = space.readPage(pageName)
  else
    local _, fm = template.fromPage(config.get("journal.template"))
    existing = "---\n" .. string.trim(template.new(fm.frontmatter)()) .. "\n---"
  end
  space.writePage(pageName, mdutil.appendListItem(existing, note))
end

command.define {
  name = "Journal: Add Note",
  key = "Ctrl-q a",
  requireMode = "rw",
  run = function()
    local quickAdd = js.importFromSpace("Library/justyns/Journal Quick Add/journal-quick-add.js")
    local text = string.trim(quickAdd.open("Add to today's journal", journal.pageName(date.today())) or "")
    if text ~= "" then
      journal.addNote(text)
      editor.flashNotification("Added to today's journal")
    end
  end
}
```

```space-style
.sb-journal-quick-add-editor {
  margin: 10px 0 4px;
  border: 1px solid var(--modal-border-color, rgba(127, 127, 127, 0.35));
  border-radius: 4px;
}
#sb-main .sb-journal-quick-add-editor .cm-editor {
  font-size: 16px;
  height: auto;
}
#sb-main .sb-journal-quick-add-editor .cm-scroller {
  max-height: 40vh;
  padding-bottom: 0;
}
#sb-main .sb-journal-quick-add-editor .cm-content {
  max-width: none;
  min-height: 5em;
  padding: 6px 10px;
  font-family: var(--editor-font);
}
/* SilverBullet scopes these to #sb-editor. */
.sb-journal-quick-add .cm-selectionBackground {
  background-color: var(--editor-selection-background-color);
}
.sb-journal-quick-add .cm-tooltip-autocomplete {
  background-color: var(--root-background-color);
  color: var(--modal-color);
}
.sb-journal-quick-add .cm-tooltip-autocomplete li .cm-completionDetail {
  color: var(--editor-completion-detail-color);
}
.sb-journal-quick-add .cm-tooltip-autocomplete li[aria-selected] .cm-completionDetail,
.sb-journal-quick-add .cm-tooltip-autocomplete li:hover .cm-completionDetail {
  color: var(--editor-completion-detail-selected-color);
}
.sb-journal-quick-add .cm-tooltip-autocomplete ul:hover li[aria-selected] {
  background: transparent;
  color: var(--modal-color);
}
.sb-journal-quick-add .cm-tooltip-autocomplete ul li:hover,
.sb-journal-quick-add .cm-tooltip-autocomplete ul li[aria-selected]:hover {
  background: #17c;
  color: white;
}
.sb-journal-quick-add-hint {
  font-size: 75%;
  opacity: 0.6;
}
```