"""Simple Tkinter GUI for GrandArchiveProxier.

Features:
- Text input for a URL or local file path to use as `source`.
- Output file chooser (Windows Save As dialog) to pick PDF path.
- Indeterminate progress bar while work runs on a background thread.
- Opens the generated PDF (or its folder) when finished.
"""
import threading
import os
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from generate_from_tts import generate_from_source


DEFAULT_OUT = str(Path("./output/cards_printable.pdf"))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GrandArchiveProxier — Generate Printable Cards")
        self.resizable(False, False)

        pad = 8
        frm = ttk.Frame(self, padding=pad)
        frm.grid(row=0, column=0, sticky="nsew")

        # Source entry
        ttk.Label(frm, text="Deck URL or local TTS JSON:").grid(row=0, column=0, sticky="w")
        self.source_var = tk.StringVar()
        self.source_entry = ttk.Entry(frm, width=72, textvariable=self.source_var)
        self.source_entry.grid(row=1, column=0, columnspan=3, sticky="w")
        ttk.Button(frm, text="Browse...", command=self.browse_source).grid(row=1, column=3, sticky="e")

        # Output chooser
        ttk.Label(frm, text="Output PDF path:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.output_var = tk.StringVar(value=DEFAULT_OUT)
        self.output_entry = ttk.Entry(frm, width=58, textvariable=self.output_var)
        self.output_entry.grid(row=3, column=0, columnspan=2, sticky="w")
        ttk.Button(frm, text="Choose...", command=self.choose_output).grid(row=3, column=2, sticky="w")
        ttk.Button(frm, text="Use Default", command=self.use_default_output).grid(row=3, column=3, sticky="e")

        # Progress and controls
        self.progress = ttk.Progressbar(frm, mode="indeterminate", length=400)
        self.progress.grid(row=4, column=0, columnspan=4, pady=(12, 0))
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(frm, textvariable=self.status_var).grid(row=5, column=0, columnspan=3, sticky="w")

        self.generate_btn = ttk.Button(frm, text="Generate", command=self.start_generation)
        self.generate_btn.grid(row=6, column=2, sticky="e", pady=(10, 0))
        self.open_btn = ttk.Button(frm, text="Open Output", command=self.open_output, state="disabled")
        self.open_btn.grid(row=6, column=3, sticky="e", pady=(10, 0))

        self._worker = None
        self._result = None

    def browse_source(self):
        # allow selecting a local file or paste a URL
        fn = filedialog.askopenfilename(title="Select TTS JSON or decklist file", filetypes=[("JSON files", "*.json;*.txt"), ("All files", "*")])
        if fn:
            self.source_var.set(fn)

    def choose_output(self):
        default = self.output_var.get() or DEFAULT_OUT
        initialdir = os.path.dirname(default) if os.path.dirname(default) else os.getcwd()
        fn = filedialog.asksaveasfilename(title="Save PDF as", defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], initialdir=initialdir, initialfile=os.path.basename(default))
        if fn:
            self.output_var.set(fn)

    def use_default_output(self):
        self.output_var.set(DEFAULT_OUT)

    def start_generation(self):
        src = self.source_var.get().strip()
        out = self.output_var.get().strip() or DEFAULT_OUT
        if not src:
            messagebox.showwarning("Missing source", "Please enter a deck URL or a path to a local TTS JSON file.")
            return

        # disable controls
        self.generate_btn.config(state="disabled")
        self.open_btn.config(state="disabled")
        self.source_entry.config(state="disabled")
        self.output_entry.config(state="disabled")

        self.status_var.set("Starting generation...")
        self.progress.start(10)

        # run in background
        self._worker = threading.Thread(target=self._run_generation, args=(src, out), daemon=True)
        self._worker.start()
        self.after(200, self._poll_worker)

    def _run_generation(self, src, out):
        try:
            printer, path = generate_from_source(src, out)
            self._result = (True, path)
        except Exception:
            tb = traceback.format_exc()
            self._result = (False, tb)

    def _poll_worker(self):
        if self._worker and self._worker.is_alive():
            # still running
            self.after(200, self._poll_worker)
            return

        # finished
        self.progress.stop()
        self.source_entry.config(state="normal")
        self.output_entry.config(state="normal")
        self.generate_btn.config(state="normal")

        ok, payload = self._result or (False, "No result")
        if ok and payload:
            outpath = payload
            self.status_var.set(f"Done — {outpath}")
            self.open_btn.config(state="normal")
            messagebox.showinfo("Success", f"PDF generated:\n{outpath}")
        else:
            self.status_var.set("Failed")
            self.open_btn.config(state="disabled")
            err = payload if payload else "Unknown error"
            messagebox.showerror("Generation failed", f"An error occurred:\n{err}")

    def open_output(self):
        out = self.output_var.get().strip() or DEFAULT_OUT
        try:
            if os.path.exists(out):
                os.startfile(out)
            else:
                # open containing folder
                folder = os.path.dirname(out) or os.getcwd()
                os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Open failed", f"Could not open file or folder:\n{e}")


def run():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
