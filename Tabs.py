import os
import json
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser


chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
notepadpp_candidates = [
    r"C:\Program Files\Notepad++\notepad++.exe",
    r"C:\Program Files (x86)\Notepad++\notepad++.exe",
]


def open_default(site_list):
    """
    Open the given URL with the system default browser (new tab).
    Falls back to os.startfile on Windows if webbrowser fails.
    """
    for url in site_list:
        try:
            webbrowser.open(url, new=2)
        except Exception:
            try:
                if os.name == 'nt':
                    os.startfile(url)
                else:
                    subprocess.Popen(['xdg-open', url])
            except Exception:
                pass


def open_chrome(site_list, incognito=False):
    """
    Open the given site_list using the Chrome executable defined by chrome_path.
    If Chrome is not found, fall back to the default browser.
    """
    if not os.path.exists(chrome_path):
        open_default(site_list)
        return

    cmd = [chrome_path]
    if incognito:
        cmd.append('--incognito')
    cmd.extend(site_list)
    try:
        subprocess.Popen(cmd)
    except Exception:
        open_default(site_list)


def open_sites(site_list, incognito=False, browser='default'):
    """
    Open an iterable of URLs.
    browser: 'chrome' or 'default' (case-insensitive).
    incognito: boolean, effective only when browser == 'chrome'.
    """
    if not site_list:
        return

    browser_key = (browser or 'default').lower()
    if browser_key == 'chrome':
        open_chrome(site_list, incognito)
    else:
        open_default(site_list)


def show_group_editor(site_list, title=None, parent=None):
    """
    Open a popup editor that lists all URLs for a group.
    The user can edit the text; 'Apply' will update the in-memory list.
    A checkbox toggles whether each line becomes a clickable link
    (opens in system default browser; missing scheme will get 'http://' added).
    Undo/Redo via Ctrl+Z / Ctrl+Y (Ctrl+Shift+Z) is enabled.

    If parent is provided (a Tk or Toplevel), the popup will position itself
    so its right edge aligns with the parent's right edge.
    """
    top = tk.Toplevel()
    top.title(f"URLs - {title}" if title else "URLs")
    # initial geometry; will reposition later if parent provided
    top.geometry("640x460")

    # Top: clickable toggle
    opts_frame = ttk.Frame(top)
    opts_frame.pack(fill='x', padx=8, pady=(8,0))
    clickable_var = tk.BooleanVar(value=False)
    clickable_cb = ttk.Checkbutton(opts_frame, text="Enable clickable links", variable=clickable_var)
    clickable_cb.pack(side='left')

    # Text widget with vertical scrollbar (undo enabled)
    text_frame = ttk.Frame(top)
    text_frame.pack(fill='both', expand=True, padx=8, pady=8)

    txt = tk.Text(text_frame, wrap='none', undo=True, autoseparators=True, maxundo=-1)
    vscroll = ttk.Scrollbar(text_frame, orient='vertical', command=txt.yview)
    hscroll = ttk.Scrollbar(text_frame, orient='horizontal', command=txt.xview)
    txt.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

    vscroll.pack(side='right', fill='y')
    hscroll.pack(side='bottom', fill='x')
    txt.pack(fill='both', expand=True, side='left')

    # Insert URLs, one per line
    lines = [s.strip() for s in site_list if s and s.strip()]
    txt.insert('1.0', '\n'.join(lines))

    # Important: reset undo/redo stack so initial insertion won't be undone by Ctrl+Z
    try:
        txt.edit_reset()
    except Exception:
        # older Tk versions may not support edit_reset; fall back to adding a separator
        try:
            txt.edit_separator()
        except Exception:
            pass
    txt.edit_modified(False)

    def _normalize_url(u):
        u = u.strip()
        if not u:
            return u
        if not u.lower().startswith(('http://', 'https://', 'ftp://')):
            return 'http://' + u
        return u

    def _open_url(url):
        try:
            webbrowser.open(_normalize_url(url), new=2)
        except Exception:
            pass

    def apply_link_tags(enabled: bool):
        # remove existing link tags
        for tag in list(txt.tag_names()):
            if tag.startswith("link_"):
                try:
                    txt.tag_delete(tag)
                except Exception:
                    pass
        txt.tag_remove("sel", "1.0", "end")  # clear selection visuals

        if not enabled:
            txt.config(cursor="")
            return

        # create tags for each current line
        content_lines = [ln for ln in txt.get('1.0', 'end').splitlines()]
        for i, line in enumerate(content_lines):
            tag = f"link_{i}"
            start = f"{i+1}.0"
            end = f"{i+1}.end"
            txt.tag_add(tag, start, end)
            txt.tag_config(tag, foreground='blue', underline=1)
            # bind click and hover
            def make_handler(u):
                return lambda e: _open_url(u)
            txt.tag_bind(tag, "<Button-1>", make_handler(line))
            txt.tag_bind(tag, "<Enter>", lambda e, t=tag: txt.config(cursor="hand2"))
            txt.tag_bind(tag, "<Leave>", lambda e: txt.config(cursor=""))

    # reapply tags on toggle and when text modified
    def on_toggle():
        apply_link_tags(clickable_var.get())

    def on_modified(event=None):
        if txt.edit_modified():
            # reapply tags only if clickable enabled
            if clickable_var.get():
                apply_link_tags(True)
            txt.edit_modified(False)

    clickable_cb.config(command=on_toggle)
    txt.bind("<<Modified>>", on_modified)
    txt.edit_modified(False)

    # enable keyboard undo/redo handlers
    def _do_undo(event=None):
        try:
            txt.edit_undo()
        except Exception:
            pass
        return "break"

    def _do_redo(event=None):
        try:
            txt.edit_redo()
        except Exception:
            pass
        return "break"

    # common Windows/Linux keybindings
    txt.bind("<Control-z>", _do_undo)
    txt.bind("<Control-Z>", _do_undo)
    txt.bind("<Control-y>", _do_redo)
    txt.bind("<Control-Y>", _do_redo)
    txt.bind("<Control-Shift-Z>", _do_redo)  # some apps use Ctrl+Shift+Z for redo

    # Buttons: Apply, Copy (no Close button; user can use window close)
    btn_frame = ttk.Frame(top)
    btn_frame.pack(fill='x', padx=8, pady=(0,8))

    def apply_changes():
        content = txt.get('1.0', 'end').strip()
        new_lines = [line.strip() for line in content.splitlines() if line.strip()]
        site_list[:] = new_lines
        messagebox.showinfo("Applied", "Changes applied to the group in memory.")
        top.destroy()

    def copy_to_clipboard():
        content = txt.get('1.0', 'end').strip()
        if content:
            top.clipboard_clear()
            top.clipboard_append(content)

    apply_btn = ttk.Button(btn_frame, text="Apply & Close", command=apply_changes)
    copy_btn = ttk.Button(btn_frame, text="Copy", command=copy_to_clipboard)

    apply_btn.pack(side='right', padx=4)
    copy_btn.pack(side='right', padx=4)

    # initial state: no clickable links until user enables
    apply_link_tags(clickable_var.get())

    # Position the popup so its left edge aligns with parent's right edge (if parent provided)
    if parent is not None:
        try:
            # Ensure geometry info is up to date
            top.update_idletasks()
            parent.update_idletasks()
            top_w = top.winfo_width()
            top_h = top.winfo_height()
            p_x = parent.winfo_rootx()
            p_y = parent.winfo_rooty()
            p_w = parent.winfo_width()

            # desired position: place popup to the right of parent
            x = p_x + p_w
            y = p_y

            # screen size checks
            screen_w = top.winfo_screenwidth()
            screen_h = top.winfo_screenheight()

            # if popup would go off the right edge, shift it left so it fits
            if x + top_w > screen_w:
                x = screen_w - top_w

            # if popup would go off the bottom edge, shift it up
            if y + top_h > screen_h:
                y = max(0, screen_h - top_h)

            # clamp to non-negative coordinates
            if x < 0:
                x = 0
            if y < 0:
                y = 0

            top.geometry(f"+{x}+{y}")
        except Exception:
            pass


def find_notepadpp_exe():
    """Return path to Notepad++ executable if found, else None."""
    for p in notepadpp_candidates:
        if os.path.exists(p):
            return p
    return None


def open_file_in_notepadpp(path):
    """
    Try to open the given file with Notepad++.
    If Notepad++ is not found, fall back to the system default opener.
    """
    if not path:
        return
    npp = find_notepadpp_exe()
    try:
        if npp:
            subprocess.Popen([npp, path])
        else:
            # fallback: use the system default (e.g., Notepad or associated editor)
            if os.name == 'nt':
                os.startfile(path)
            else:
                subprocess.Popen(['xdg-open', path])
    except Exception:
        pass


def make_gui():
    root = tk.Tk()
    root.title("Grouped URL Opener")
    root.geometry("520x520")

    # state
    current_file = {'path': None}
    site_dict = {}

    # Top controls: file select + open in Notepad++ + save as
    top_frame = ttk.Frame(root)
    top_frame.pack(fill='x', padx=10, pady=8)

    def populate_groups(data):
        # clear existing group frames
        for child in groups_container.winfo_children():
            child.destroy()

        # create rows for each group
        for group, site_list in data.items():
            frame = ttk.Frame(groups_container)
            frame.pack(fill='x', padx=6, pady=4)
            label = ttk.Label(frame, text=group)
            label.pack(side='left', padx=(4,0))

            # Open button
            open_btn = ttk.Button(
                frame,
                text="Open this group",
                command=lambda s=site_list: open_sites(s, incognito_var.get(), browser_var.get())
            )
            open_btn.pack(side='right', padx=(4,0))

            # Edit button to show popup editor; pass parent so editor can align to main window's right edge
            edit_btn = ttk.Button(
                frame,
                text="Edit URLs",
                command=lambda s=site_list, g=group: show_group_editor(s, title=g, parent=root)
            )
            edit_btn.pack(side='right', padx=(0,4))

    def select_file():
        path = filedialog.askopenfilename(
            title="Select sessions file (JSON)",
            filetypes=[("JSON or text", ("*.json", "*.txt", "*.jsonl", "*.ndjson")), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                messagebox.showerror("Invalid file", "Selected file does not contain a JSON object mapping group->urls.")
                return
        except Exception as e:
            messagebox.showerror("Error loading file", f"Failed to load JSON: {e}")
            return

        # update state and UI
        current_file['path'] = path
        file_label.config(text=os.path.basename(path))
        notepad_btn.config(state='normal')
        save_btn.config(state='normal')
        # update in-memory dict and populate groups
        site_dict.clear()
        site_dict.update(data)
        populate_groups(site_dict)

    def open_selected_in_npp():
        if current_file['path']:
            open_file_in_notepadpp(current_file['path'])

    def save_sessions_as():
        if not site_dict:
            messagebox.showwarning("No data", "No session data to save.")
            return
        initial = os.path.basename(current_file['path']) if current_file.get('path') else "sessions.json"
        path = filedialog.asksaveasfilename(
            title="Save sessions as",
            defaultextension=".json",
            initialfile=initial,
            filetypes=[("JSON or text", ("*.json", "*.txt", "*.jsonl", "*.ndjson")), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(site_dict, f, ensure_ascii=False, indent=2)
                f.write("\n")
            messagebox.showinfo("Saved", f"Sessions saved to {path}")
        except Exception as e:
            messagebox.showerror("Save failed", f"Failed to save file: {e}")

    select_btn = ttk.Button(top_frame, text="Select sessions file...", command=select_file)
    select_btn.pack(side='left')
    root.after(0, select_btn.focus_set)  # Focus on select button initially

    notepad_btn = ttk.Button(top_frame, text="Open with Notepad++", command=open_selected_in_npp, state='disabled')
    notepad_btn.pack(side='left')

    save_btn = ttk.Button(top_frame, text="Save sessions as...", command=save_sessions_as, state='disabled')
    save_btn.pack(side='left')

    # file label placed on the next row for clearer layout
    file_frame = ttk.Frame(root)
    file_frame.pack(fill='x', padx=10)  # new row under the buttons
    file_label = ttk.Label(file_frame, text="No file selected", width=50)
    file_label.pack(side='left', padx=(1,8), pady=(4,0))

    # Options: incognito and browser
    opts_frame = ttk.Frame(root)
    opts_frame.pack(fill='x', padx=10, pady=(0,6))

    incognito_var = tk.BooleanVar(value=True)
    incognito_check = ttk.Checkbutton(opts_frame, text="Use incognito mode (Chrome only)", variable=incognito_var)
    incognito_check.pack(side='left', padx=(0,8))

    browser_var = tk.StringVar(value='chrome')
    browser_label = ttk.Label(opts_frame, text="Browser:")
    browser_combo = ttk.Combobox(opts_frame, textvariable=browser_var, values=['default', 'chrome'], state='readonly', width=12)
    browser_combo.pack(side='right', padx=(6,0))
    browser_label.pack(side='right')

    # Container for group rows (will be populated after file selection)
    groups_container = ttk.Frame(root)
    groups_container.pack(fill='both', expand=True, padx=10, pady=6)

    root.mainloop()


if __name__ == "__main__":
    make_gui()