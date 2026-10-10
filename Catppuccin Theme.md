---
tags: meta
---
# Catppuccin Theme

Themes SilverBullet with the Catppuccin palette, with a separate flavor for light and dark mode.

Without configuration, light mode uses Latte and dark mode uses Mocha. To pick other flavors (`latte`, `frappe`, `macchiato` or `mocha`), add this to your CONFIG page and run `System: Reload`:

```lua
config.set("catppuccin", {light = "latte", dark = "macchiato"})
```

Colors are from the [Catppuccin palette](https://catppuccin.com/palette) (MIT) and are assigned following the [Catppuccin style guide](https://github.com/catppuccin/catppuccin/blob/main/docs/style-guide.md).

## Implementation

```space-lua
-- priority: -100
-- Negative priority runs this after CONFIG, so config.get returns the user's flavors.
local flavors = {"latte", "frappe", "macchiato", "mocha"}

config.defineCategory {
  name = "Catppuccin",
  description = "Catppuccin flavors for light and dark mode. Run System: Reload after changing them.",
}

config.define("catppuccin", {
  description = "Catppuccin flavors for light and dark mode",
  type = "object",
  properties = {
    light = {
      type = "string", enum = flavors, default = "latte",
      ui = {category = "Catppuccin", label = "Light mode flavor", priority = 2},
    },
    dark = {
      type = "string", enum = flavors, default = "mocha",
      ui = {category = "Catppuccin", label = "Dark mode flavor", priority = 1},
    },
  },
})

local classes = js.window.document.documentElement.classList
for _, f in ipairs(flavors) do
  classes.remove("ctp-light-" .. f)
  classes.remove("ctp-dark-" .. f)
end
classes.add("ctp-light-" .. config.get("catppuccin.light"))
classes.add("ctp-dark-" .. config.get("catppuccin.dark"))
```

```space-style
html {
  --rosewater: #dc8a78;
  --flamingo: #dd7878;
  --pink: #ea76cb;
  --mauve: #8839ef;
  --red: #d20f39;
  --maroon: #e64553;
  --peach: #fe640b;
  --yellow: #df8e1d;
  --green: #40a02b;
  --teal: #179299;
  --sky: #04a5e5;
  --sapphire: #209fb5;
  --blue: #1e66f5;
  --lavender: #7287fd;
  --text: #4c4f69;
  --subtext1: #5c5f77;
  --subtext0: #6c6f85;
  --overlay2: #7c7f93;
  --overlay1: #8c8fa1;
  --overlay0: #9ca0b0;
  --surface2: #acb0be;
  --surface1: #bcc0cc;
  --surface0: #ccd0da;
  --base: #eff1f5;
  --mantle: #e6e9ef;
  --crust: #dce0e8;
}

html[data-theme="dark"] {
  --rosewater: #f5e0dc;
  --flamingo: #f2cdcd;
  --pink: #f5c2e7;
  --mauve: #cba6f7;
  --red: #f38ba8;
  --maroon: #eba0ac;
  --peach: #fab387;
  --yellow: #f9e2af;
  --green: #a6e3a1;
  --teal: #94e2d5;
  --sky: #89dceb;
  --sapphire: #74c7ec;
  --blue: #89b4fa;
  --lavender: #b4befe;
  --text: #cdd6f4;
  --subtext1: #bac2de;
  --subtext0: #a6adc8;
  --overlay2: #9399b2;
  --overlay1: #7f849c;
  --overlay0: #6c7086;
  --surface2: #585b70;
  --surface1: #45475a;
  --surface0: #313244;
  --base: #1e1e2e;
  --mantle: #181825;
  --crust: #11111b;
}

html.ctp-light-latte[data-theme="light"],
html.ctp-dark-latte[data-theme="dark"] {
  color-scheme: light;
  --rosewater: #dc8a78;
  --flamingo: #dd7878;
  --pink: #ea76cb;
  --mauve: #8839ef;
  --red: #d20f39;
  --maroon: #e64553;
  --peach: #fe640b;
  --yellow: #df8e1d;
  --green: #40a02b;
  --teal: #179299;
  --sky: #04a5e5;
  --sapphire: #209fb5;
  --blue: #1e66f5;
  --lavender: #7287fd;
  --text: #4c4f69;
  --subtext1: #5c5f77;
  --subtext0: #6c6f85;
  --overlay2: #7c7f93;
  --overlay1: #8c8fa1;
  --overlay0: #9ca0b0;
  --surface2: #acb0be;
  --surface1: #bcc0cc;
  --surface0: #ccd0da;
  --base: #eff1f5;
  --mantle: #e6e9ef;
  --crust: #dce0e8;
}

html.ctp-light-frappe[data-theme="light"],
html.ctp-dark-frappe[data-theme="dark"] {
  color-scheme: dark;
  --rosewater: #f2d5cf;
  --flamingo: #eebebe;
  --pink: #f4b8e4;
  --mauve: #ca9ee6;
  --red: #e78284;
  --maroon: #ea999c;
  --peach: #ef9f76;
  --yellow: #e5c890;
  --green: #a6d189;
  --teal: #81c8be;
  --sky: #99d1db;
  --sapphire: #85c1dc;
  --blue: #8caaee;
  --lavender: #babbf1;
  --text: #c6d0f5;
  --subtext1: #b5bfe2;
  --subtext0: #a5adce;
  --overlay2: #949cbb;
  --overlay1: #838ba7;
  --overlay0: #737994;
  --surface2: #626880;
  --surface1: #51576d;
  --surface0: #414559;
  --base: #303446;
  --mantle: #292c3c;
  --crust: #232634;
}

html.ctp-light-macchiato[data-theme="light"],
html.ctp-dark-macchiato[data-theme="dark"] {
  color-scheme: dark;
  --rosewater: #f4dbd6;
  --flamingo: #f0c6c6;
  --pink: #f5bde6;
  --mauve: #c6a0f6;
  --red: #ed8796;
  --maroon: #ee99a0;
  --peach: #f5a97f;
  --yellow: #eed49f;
  --green: #a6da95;
  --teal: #8bd5ca;
  --sky: #91d7e3;
  --sapphire: #7dc4e4;
  --blue: #8aadf4;
  --lavender: #b7bdf8;
  --text: #cad3f5;
  --subtext1: #b8c0e0;
  --subtext0: #a5adcb;
  --overlay2: #939ab7;
  --overlay1: #8087a2;
  --overlay0: #6e738d;
  --surface2: #5b6078;
  --surface1: #494d64;
  --surface0: #363a4f;
  --base: #24273a;
  --mantle: #1e2030;
  --crust: #181926;
}

html.ctp-light-mocha[data-theme="light"],
html.ctp-dark-mocha[data-theme="dark"] {
  color-scheme: dark;
  --rosewater: #f5e0dc;
  --flamingo: #f2cdcd;
  --pink: #f5c2e7;
  --mauve: #cba6f7;
  --red: #f38ba8;
  --maroon: #eba0ac;
  --peach: #fab387;
  --yellow: #f9e2af;
  --green: #a6e3a1;
  --teal: #94e2d5;
  --sky: #89dceb;
  --sapphire: #74c7ec;
  --blue: #89b4fa;
  --lavender: #b4befe;
  --text: #cdd6f4;
  --subtext1: #bac2de;
  --subtext0: #a6adc8;
  --overlay2: #9399b2;
  --overlay1: #7f849c;
  --overlay0: #6c7086;
  --surface2: #585b70;
  --surface1: #45475a;
  --surface0: #313244;
  --base: #1e1e2e;
  --mantle: #181825;
  --crust: #11111b;
}
```

```space-style
html, html[data-theme="dark"] {
  --root-background-color: var(--base);
  --root-color: var(--text);
  --ui-accent-color: var(--lavender);
  --ui-accent-contrast-color: var(--base);
  --ui-surface-border-color: var(--surface0);

  --highlight-color: color-mix(in srgb, var(--yellow) 35%, transparent);
  --link-color: var(--blue);
  --link-missing-color: var(--peach);
  --link-invalid-color: var(--mauve);
  --meta-color: var(--overlay2);
  --meta-subtle-color: var(--overlay1);
  --subtle-color: var(--subtext0);
  --subtle-background-color: color-mix(in srgb, var(--surface0) 60%, transparent);

  --top-color: var(--text);
  --top-background-color: var(--crust);
  --top-border-color: var(--surface0);
  --top-sync-error-color: var(--red);
  --top-sync-error-background-color: color-mix(in srgb, var(--red) 20%, var(--crust));
  --top-saved-color: var(--text);
  --top-unsaved-color: var(--subtext0);
  --top-loading-color: var(--overlay1);

  --panel-background-color: var(--mantle);
  --panel-border-color: var(--surface0);
  --bhs-background-color: var(--base);
  --bhs-border-color: var(--surface0);

  --modal-color: var(--text);
  --modal-background-color: var(--mantle);
  --modal-border-color: var(--surface0);
  --modal-backdrop-color: color-mix(in srgb, var(--crust) 40%, transparent);
  --modal-header-label-color: var(--ui-accent-color);
  --modal-help-background-color: var(--crust);
  --modal-help-color: var(--subtext0);
  --modal-selected-option-background-color: var(--lavender);
  --modal-selected-option-color: var(--base);
  --modal-selected-option-description-color: var(--base);
  --modal-hint-background-color: var(--lavender);
  --modal-hint-color: var(--base);
  --modal-hint-inactive-background-color: var(--surface0);
  --modal-hint-inactive-color: var(--subtext1);
  --modal-description-color: var(--subtext0);

  --notifications-border-color: var(--surface0);
  --notification-info-background-color: color-mix(in srgb, var(--blue) 15%, var(--base));
  --notification-error-background-color: color-mix(in srgb, var(--red) 15%, var(--base));
  --notification-warning-background-color: color-mix(in srgb, var(--yellow) 15%, var(--base));

  --button-background-color: var(--mantle);
  --button-hover-background-color: var(--surface0);
  --button-color: var(--text);
  --button-border-color: var(--surface0);
  --text-field-background-color: var(--base);

  --action-button-color: var(--subtext1);
  --action-button-hover-color: var(--ui-accent-color);

  --progress-background-color: var(--surface0);

  --danger-color: var(--red);
  --danger-contrast-color: var(--base);
  --alert-error-color: var(--red);
  --alert-error-background-color: color-mix(in srgb, var(--red) 10%, var(--base));
  --alert-error-border-color: color-mix(in srgb, var(--red) 35%, var(--base));
  --alert-warning-color: var(--peach);
  --alert-warning-background-color: color-mix(in srgb, var(--yellow) 10%, var(--base));
  --alert-warning-border-color: color-mix(in srgb, var(--yellow) 35%, var(--base));
  --alert-info-color: var(--blue);
  --alert-info-background-color: color-mix(in srgb, var(--blue) 10%, var(--base));
  --alert-info-border-color: color-mix(in srgb, var(--blue) 35%, var(--base));
  --badge-background-color: var(--surface0);
  --badge-color: var(--subtext1);

  --editor-text-color: var(--text);
  --editor-caret-color: var(--rosewater);
  --editor-selection-background-color: color-mix(in srgb, var(--overlay2) 25%, transparent);
  --editor-highlight-background-color: var(--highlight-color);
  --editor-error-color: var(--red);
  --editor-heading-color: var(--text);
  --editor-heading-meta-color: var(--meta-subtle-color);
  --editor-list-bullet-color: var(--overlay2);
  --editor-ruler-color: var(--surface2);
  --editor-meta-color: var(--meta-color);
  --editor-line-meta-color: var(--meta-subtle-color);
  --editor-struct-color: var(--mauve);
  --editor-widget-background-color: var(--mantle);
  --editor-task-marker-color: var(--overlay2);
  --editor-task-state-color: var(--subtext0);
  --editor-completion-detail-color: var(--subtext0);
  --editor-completion-detail-selected-color: var(--base);

  --editor-link-color: var(--link-color);
  --editor-link-url-color: var(--link-color);
  --editor-link-meta-color: var(--meta-subtle-color);
  --editor-naked-url-color: var(--link-color);
  --editor-wiki-link-page-color: var(--link-color);
  --editor-wiki-link-page-background-color: transparent;
  --editor-wiki-link-page-missing-color: var(--link-missing-color);
  --editor-wiki-link-page-invalid-color: var(--link-invalid-color);

  --editor-hashtag-color: var(--base);
  --editor-hashtag-background-color: var(--blue);
  --editor-hashtag-border-color: var(--blue);
  --editor-at-mention-color: var(--sapphire);
  --editor-at-mention-background-color: color-mix(in srgb, var(--sapphire) 15%, transparent);
  --editor-at-mention-border-color: color-mix(in srgb, var(--sapphire) 40%, transparent);
  --editor-at-mention-signature-color: var(--overlay1);

  --editor-blockquote-color: var(--subtext1);
  --editor-blockquote-background-color: var(--subtle-background-color);
  --editor-blockquote-border-color: var(--overlay0);
  --editor-comment-background-color: color-mix(in srgb, var(--surface0) 40%, transparent);
  --editor-comment-border-color: var(--overlay0);

  --editor-table-head-color: var(--text);
  --editor-table-head-background-color: var(--surface0);
  --editor-table-even-background-color: var(--mantle);

  --editor-frontmatter-color: var(--subtext0);
  --editor-frontmatter-background-color: var(--subtle-background-color);
  --editor-frontmatter-marker-color: var(--maroon);
  --editor-directive-color: var(--subtext0);
  --editor-directive-background-color: var(--subtle-background-color);
  --editor-directive-mark-color: var(--maroon);

  --editor-code-color: var(--text);
  --editor-code-background-color: var(--subtle-background-color);
  --editor-code-comment-color: var(--overlay2);
  --editor-code-variable-color: var(--blue);
  --editor-code-typename-color: var(--yellow);
  --editor-code-string-color: var(--green);
  --editor-code-number-color: var(--peach);
  --editor-code-operator-color: var(--sky);
  --editor-code-atom-color: var(--red);
  --editor-code-info-color: var(--subtext0);
  --editor-code-deleted-color: var(--red);
  --editor-code-deleted-bg: color-mix(in srgb, var(--red) 15%, transparent);
  --editor-code-inserted-color: var(--green);
  --editor-code-inserted-bg: color-mix(in srgb, var(--green) 15%, transparent);

  --editor-external-edit-color: color-mix(in srgb, var(--yellow) 25%, transparent);
  --editor-external-caret-color: var(--peach);

  --editor-panels-bottom-color: var(--text);
  --editor-panels-bottom-background-color: var(--mantle);
  --editor-panels-bottom-border-color: var(--surface0);
  --editor-panels-bottom-input-background-color: var(--base);
  --editor-panels-bottom-button-background-image: linear-gradient(var(--surface0), var(--surface1));
  --editor-panels-bottom-button-active-background-image: linear-gradient(var(--surface1), var(--surface2));
}

.sb-admonition[admonition="note" i] { --admonition-color: var(--blue); }
.sb-admonition[admonition="warning" i] { --admonition-color: var(--yellow); }
.sb-admonition[admonition="danger" i] { --admonition-color: var(--red); }
.sb-admonition[admonition="success" i] { --admonition-color: var(--green); }

#sb-editor .cm-editor .cm-tooltip-autocomplete ul li[aria-selected],
#sb-editor .cm-editor .cm-tooltip-autocomplete ul li:hover {
  background: var(--ui-accent-color);
  color: var(--base);
}

/* While the mouse is over another row, only that row is highlighted. */
#sb-editor .cm-editor .cm-tooltip-autocomplete ul:hover li[aria-selected]:not(:hover) {
  background: transparent;
  color: var(--modal-color);
}

#sb-editor .cm-editor .cm-tooltip-autocomplete ul:hover li[aria-selected]:not(:hover) .cm-completionDetail {
  color: var(--editor-completion-detail-color);
}

.sb-footnote-ref {
  background-color: var(--mantle);
}
.sb-footnote-ref.sb-footnote-ref-unresolved {
  background-color: color-mix(in srgb, var(--red) 10%, transparent);
}

/* The stock deadline backgrounds are hardcoded and sit inside higher-specificity selectors. */
.sb-task-deadline,
span.task-deadline {
  background-color: var(--subtle-background-color) !important;
}
```
