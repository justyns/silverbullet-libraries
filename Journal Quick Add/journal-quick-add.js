// A modal CodeMirror editor built from the main editor's extensions. open() resolves to the text, or null when cancelled.

function mainExtensions(client) {
  const state = client.editorView.state;
  const [shared, page] = state.config.base;
  const ext = (compartment) => {
    const value = compartment.get(state);
    if (value === undefined) throw new Error("journal-quick-add: editor extension layout changed");
    return value;
  };
  const completion = page.find((x) => Array.isArray(x) && x.some((y) => y?.value?.override));
  if (!completion) throw new Error("journal-quick-add: autocompletion extension not found");
  // Keep page, tag and attribute completion. Slash commands are left out because they apply to the main editor.
  const withoutSlash = completion.map((x) =>
    x?.value?.override ? x.facet.of({ ...x.value, override: [client.editorComplete.bind(client)] }) : x
  );
  return [
    ext(client.markdownLanguageCompartment),
    ext(client.undoHistoryCompartment),
    shared[4], // syntaxHighlighting
    shared[10], // drawSelection
    shared[12], // closeBrackets
    withoutSlash,
  ];
}

export function open(title, hint) {
  const client = globalThis.client;
  const EditorView = client.editorView.constructor;
  const EditorState = client.editorView.state.constructor;

  const dialog = document.createElement("dialog");
  dialog.className = "sb-modal-box sb-journal-quick-add";
  dialog.innerHTML = `
    <div class="sb-prompt">
      <label></label>
      <div class="sb-journal-quick-add-editor"></div>
      <div class="sb-journal-quick-add-hint"></div>
      <div class="sb-prompt-buttons">
        <button class="sb-button" data-action="cancel">Cancel<span class="sb-kbd">esc</span></button>
        <button class="sb-button sb-button-primary" data-action="ok">Add<span class="sb-kbd">⏎</span></button>
      </div>
    </div>`;
  dialog.querySelector("label").textContent = title;
  dialog.querySelector(".sb-journal-quick-add-hint").textContent = hint;
  // Inside #sb-main so the editor's .cm-editor styles apply.
  document.getElementById("sb-main").appendChild(dialog);

  const view = new EditorView({
    parent: dialog.querySelector(".sb-journal-quick-add-editor"),
    state: EditorState.create({ extensions: [...mainExtensions(client), EditorView.lineWrapping] }),
  });

  return new Promise((resolve) => {
    let closed = false;
    const close = (value) => {
      if (closed) return;
      closed = true;
      view.destroy();
      dialog.remove();
      client.focus();
      resolve(value);
    };
    dialog.addEventListener("close", () => close(null));
    // Keep keys away from SilverBullet's global shortcuts.
    dialog.addEventListener("keydown", (e) => e.stopPropagation());
    // Captured ahead of CodeMirror, which handles Escape itself. An open completion list keeps Enter and Escape.
    dialog.addEventListener(
      "keydown",
      (e) => {
        if (dialog.querySelector(".cm-tooltip-autocomplete")) return;
        if (e.key === "Escape") {
          e.preventDefault();
          close(null);
        } else if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          close(view.state.doc.toString());
        }
      },
      true
    );
    // A click on the box's padding or empty scroller would focus the scroller, not the text.
    dialog.querySelector(".sb-journal-quick-add-editor").addEventListener("mousedown", (e) => {
      if (!view.contentDOM.contains(e.target)) {
        e.preventDefault();
        view.focus();
      }
    });
    dialog.querySelector("[data-action=cancel]").onclick = () => close(null);
    dialog.querySelector("[data-action=ok]").onclick = () => close(view.state.doc.toString());
    dialog.showModal();
    view.focus();
  });
}
