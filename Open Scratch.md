---
tags: meta
---
# Open Scratch

Shortcuts to open up a scratch “buffer” page.  Similar to the scratch buffer in emacs/vim, except I guess it is persistent in this case.

```space-lua
local scratchPage = "scratch"
local panelOpen = false

command.define {
  name = "Open Scratch Note",
  run = function()
    editor.navigate(scratchPage)
  end
}

-- Shows the scratch page in the right panel, with SilverBullet's top bar and the
-- SilverBullet+ Desktop title bar hidden.
command.define {
  name = "Toggle Scratch Buffer",
  run = function()
    if panelOpen then
      editor.hidePanel("rhs")
    else
      editor.showPanel("rhs", 2,
        '<style>html, body { margin: 0; height: 100%; } iframe { display: block; width: 100%; height: 100%; border: none; }</style>'
          .. '<iframe src="/' .. scratchPage .. '"></iframe>',
        [[
          const frame = document.querySelector("iframe");
          frame.addEventListener("load", () => {
            const style = frame.contentDocument.createElement("style");
            style.textContent = "#sb-top, #sb-titlebar { display: none !important; } "
              + ":root, .sb-linux, .sb-windows { --sb-titlebar-height: 0px !important; }";
            frame.contentDocument.head.appendChild(style);
          });
        ]])
    end
    panelOpen = not panelOpen
  end
}
```
