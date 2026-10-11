# SilverBullet Libraries

This repository contains various [libraries](https://silverbullet.md/Library) created and shared by me for use with SilverBullet.


## How to Add This Repository to SilverBullet

To add this repository to your SilverBullet instance, use the `Library: Add Repository` command with the following URL:

`https://github.com/justyns/silverbullet-libraries/blob/master/REPO.md`

## Available Libraries

### Terminal and Agent IDE

- [Terminal](https://github.com/justyns/silverbullet-libraries/blob/master/Terminal/Terminal.md): Terminal sessions such as your shell or Claude Code in a modal or panel, served by a small Python bridge through SilverBullet's proxy.
- [Agent IDE](https://github.com/justyns/silverbullet-libraries/blob/master/Agent%20IDE/Agent%20IDE.md): Connects Claude Code and Codex to SilverBullet as their IDE, sharing the current page and selection. Claude Code can also show proposed edits as diffs to accept or reject. Requires Terminal.

### Misc

- [Catppuccin Theme](https://github.com/justyns/silverbullet-libraries/blob/master/Catppuccin%20Theme.md): Catppuccin theme with all four flavors, picked separately for light and dark mode in the Configuration Manager.
- [Date functions](https://github.com/justyns/silverbullet-libraries/blob/master/Date%20functions.md): `getCurrentDateTime()` and `getToday()` Lua functions, plus `/now` and `/currentDateTime` slash commands that insert the current date and time.
- [Forgejo](https://github.com/justyns/silverbullet-libraries/blob/master/Forgejo.md): Read/write support for Forgejo and Gitea git servers.
- [Get GPS Coords](https://github.com/justyns/silverbullet-libraries/blob/master/Get%20GPS%20Coords.md): Lua function to get the current GPS coordinates of the client browser.
- [Markdown Utilities](https://github.com/justyns/silverbullet-libraries/blob/master/Markdown%20Utilities.md): Space Lua helpers for finding headings and list items and inserting text under a heading, built on markdown.parseMarkdown.
- [Move Page to Dated Folder](https://github.com/justyns/silverbullet-libraries/blob/master/Move%20Page%20to%20Dated%20Folder.md): Command that moves the current page into `<folder>/YYYY/` or `<folder>/YYYY/MM-Month/` based on its date, for folders set in config.
- [Open Scratch](https://github.com/justyns/silverbullet-libraries/blob/master/Open%20Scratch.md): Commands to open a scratch page, or show it in the right panel next to the current page.
- [Recurring Tasks](https://github.com/justyns/silverbullet-libraries/blob/master/Recurring%20Tasks.md): Stamps a done date on completed tasks and adds the next occurrence of tasks with a 🔁 rule, using the Obsidian Tasks emoji format.
- [Share to GitHub Repo](https://github.com/justyns/silverbullet-libraries/blob/master/Share%20to%20GitHub%20Repo.md): Commands that push the current page to preconfigured GitHub repos and set its share frontmatter, so `Share: Page` handles later updates.

### silverbullet-ai tools

These libraries provide [tools](https://ai.silverbullet.md/Tools/) for the [silverbullet-ai plug](https://github.com/justyns/silverbullet-ai).

- [SearXNG Web Search Integration](https://github.com/justyns/silverbullet-libraries/blob/master/AI%20Tool%20-%20SearXNG%20search.md): Search the web using a SearXNG instance. Requires API support to be enabled.
- [Silversearch Integration](https://github.com/justyns/silverbullet-libraries/blob/master/AI%20Tool%20-%20Silversearch.md): Integration with the Silversearch plugin, allowing space querying and result retrieval.
- [Web Fetch Tool](https://github.com/justyns/silverbullet-libraries/blob/master/AI%20Tool%20-%20Web%20Fetch.md): Fetch a URL and convert its HTML content to markdown.


