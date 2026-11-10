import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from collections import deque
from tkinter import ttk, filedialog, messagebox

# Arrastar e soltar (opcional): pip install tkinterdnd2
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_OK = True
except ImportError:
    DND_OK = False

APP_NAME = "Conversor MP4"
VIDEO_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".flv",
    ".mpeg", ".mpg", ".m4v", ".3gp", ".ts",
}
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # evita janela de console no Windows

COLORS = {"info": "#555555", "ok": "#1a7f37", "error": "#c62828", "warn": "#b26a00"}


# ---------------------------------------------------------------- FFmpeg automático
# Fonte principal (leve, ~30 MB): binário do FFmpeg empacotado no PyPI (imageio-ffmpeg).
PYPI_JSON_URL = "https://pypi.org/pypi/imageio-ffmpeg/json"
# Reserva (pesada, ~100 MB): build completo com ffprobe.
FFMPEG_ZIP_URLS = [
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
]


def app_data_dir():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "ConversorMP4")


def local_ffmpeg_bin():
    return os.path.join(app_data_dir(), "ffmpeg", "bin")


def ffmpeg_available():
    return bool(shutil.which("ffmpeg"))


def use_local_ffmpeg():
    """Se o FFmpeg já foi baixado antes, coloca a pasta dele no PATH deste processo."""
    bin_dir = local_ffmpeg_bin()
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    if os.path.isfile(os.path.join(bin_dir, exe)):
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")


def _download(url, dest, progress_cb, expected_sha256=None):
    import hashlib
    import urllib.request
    sha = hashlib.sha256()
    req = urllib.request.Request(url, headers={"User-Agent": "ConversorMP4"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            out.write(chunk)
            sha.update(chunk)
            done += len(chunk)
            progress_cb(done, total, "Baixando")
    if expected_sha256 and sha.hexdigest().lower() != expected_sha256.lower():
        raise RuntimeError("O arquivo baixado está corrompido (checksum diferente). Tente novamente.")


def _install_from_pypi(tmp, progress_cb):
    import json
    import sys
    import urllib.request
    import zipfile

    req = urllib.request.Request(PYPI_JSON_URL, headers={"User-Agent": "ConversorMP4"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        info = json.load(resp)
    suffix = "-win_amd64.whl" if sys.maxsize > 2**32 else "-win32.whl"
    wheel = next((f for f in info["urls"] if f["filename"].endswith(suffix)), None)
    if wheel is None:
        raise RuntimeError("Pacote do FFmpeg não encontrado no PyPI.")

    _download(wheel["url"], tmp, progress_cb, wheel.get("digests", {}).get("sha256"))
    progress_cb(1, 1, "Extraindo")
    bin_dir = local_ffmpeg_bin()
    os.makedirs(bin_dir, exist_ok=True)
    with zipfile.ZipFile(tmp) as z:
        member = next((m for m in z.namelist()
                       if "/binaries/" in m and os.path.basename(m).lower().startswith("ffmpeg")
                       and m.lower().endswith(".exe")), None)
        if member is None:
            raise RuntimeError("O pacote baixado não contém o ffmpeg.exe.")
        with z.open(member) as src, open(os.path.join(bin_dir, "ffmpeg.exe"), "wb") as dst:
            shutil.copyfileobj(src, dst)


def _install_from_zip(url, tmp, progress_cb):
    import zipfile
    _download(url, tmp, progress_cb)
    progress_cb(1, 1, "Extraindo")
    bin_dir = local_ffmpeg_bin()
    os.makedirs(bin_dir, exist_ok=True)
    wanted, found = {"ffmpeg.exe", "ffprobe.exe"}, set()
    with zipfile.ZipFile(tmp) as z:
        for member in z.namelist():
            base = os.path.basename(member).lower()
            if base in wanted and "/bin/" in member.replace("\\", "/"):
                with z.open(member) as src, open(os.path.join(bin_dir, base), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                found.add(base)
    if "ffmpeg.exe" not in found:
        raise RuntimeError("O arquivo baixado não contém o ffmpeg.exe.")


def download_ffmpeg(progress_cb):
    """Baixa o FFmpeg (Windows) e ativa no PATH deste processo."""
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "conversor_mp4_ffmpeg.tmp")
    attempts = [lambda: _install_from_pypi(tmp, progress_cb)]
    attempts += [(lambda u=u: _install_from_zip(u, tmp, progress_cb)) for u in FFMPEG_ZIP_URLS]
    last_exc = None
    for attempt in attempts:
        try:
            attempt()
            use_local_ffmpeg()
            if not ffmpeg_available():
                raise RuntimeError("FFmpeg extraído, mas não pôde ser executado.")
            return
        except Exception as exc:
            last_exc = exc
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
    raise last_exc


def get_duration(path):
    """Duração do vídeo em segundos (ffprobe, ou o cabeçalho do ffmpeg se não houver ffprobe)."""
    try:
        if shutil.which("ffprobe"):
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=30, creationflags=NO_WINDOW,
            ).stdout.strip()
            value = float(out)
        else:
            import re
            err = subprocess.run(
                ["ffmpeg", "-hide_banner", "-nostdin", "-i", path],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=30, creationflags=NO_WINDOW,
            ).stderr
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
            if not m:
                return None
            value = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        return value if value > 0 else None
    except (ValueError, OSError, subprocess.SubprocessError):
        return None


class FileRow:
    """Uma linha da lista: nome, barra de progresso individual, porcentagem e status."""

    def __init__(self, app, parent, path):
        self.app = app
        self.path = path
        self.state = "waiting"  # waiting | converting | done | error | canceled

        self.frame = ttk.Frame(parent, padding=(6, 5))
        self.frame.columnconfigure(0, weight=1)

        self.name_label = ttk.Label(self.frame, text=os.path.basename(path), font=("Segoe UI", 10, "bold"))
        self.name_label.grid(row=0, column=0, sticky="w")
        self.remove_btn = ttk.Button(self.frame, text="✕", width=3, command=lambda: app.remove_row(self))
        self.remove_btn.grid(row=0, column=1, rowspan=2, padx=(8, 0))

        bar_frame = ttk.Frame(self.frame)
        bar_frame.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        bar_frame.columnconfigure(0, weight=1)
        self.bar = ttk.Progressbar(bar_frame, mode="determinate", maximum=100)
        self.bar.grid(row=0, column=0, sticky="ew")
        self.pct_label = ttk.Label(bar_frame, text="0%", width=5, anchor="e")
        self.pct_label.grid(row=0, column=1, padx=(8, 0))

        self.status_label = ttk.Label(self.frame, text="Aguardando", foreground=COLORS["info"])
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="w")

        ttk.Separator(self.frame, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def set_progress(self, percent):
        self.bar.stop()
        self.bar.configure(mode="determinate")
        self.bar["value"] = percent
        self.pct_label.configure(text=f"{int(percent)}%")

    def set_indeterminate(self):
        self.bar.configure(mode="indeterminate")
        self.bar.start(12)
        self.pct_label.configure(text="…")

    def set_status(self, text, kind="info"):
        self.status_label.configure(text=text, foreground=COLORS[kind])

    def reset(self):
        self.state = "waiting"
        self.set_progress(0)
        self.set_status("Aguardando")


class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("780x620")
        self.root.minsize(660, 520)

        self.rows = []
        self.output_dir = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Videos", "Convertidos"))
        self.quality = tk.StringVar(value="Padrão (boa qualidade)")
        self.status = tk.StringVar(value="Adicione vídeos para começar.")
        self.is_converting = False
        self.cancel_requested = False
        self.current_process = None

        self._build_ui()
        self._setup_drag_and_drop()
        self._check_ffmpeg()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Conversor de vídeos para MP4", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        subtitle = "Arraste vídeos para a janela ou use o botão para adicionar." if DND_OK \
            else "Converta um ou vários vídeos com poucos cliques."
        ttk.Label(outer, text=subtitle, foreground="#555").pack(anchor="w", pady=(2, 12))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Adicionar vídeos…", command=self.add_files).pack(side="left")
        ttk.Button(actions, text="Limpar lista", command=self.clear_files).pack(side="left", padx=7)

        # Área rolável com uma linha (e barra de progresso) por vídeo
        self.list_border = tk.Frame(outer, highlightthickness=2, highlightbackground="#cccccc",
                                    highlightcolor="#cccccc")
        self.list_border.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.list_border, highlightthickness=0, bg="white")
        scrollbar = ttk.Scrollbar(self.list_border, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.rows_frame = ttk.Frame(self.canvas)
        self.rows_window = self.canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.rows_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.rows_window, width=e.width))
        self._bind_mousewheel()

        hint = "Arraste e solte vídeos aqui\nou clique em “Adicionar vídeos…”" if DND_OK \
            else "Nenhum vídeo na lista\nClique em “Adicionar vídeos…”"
        self.empty_hint = tk.Label(self.canvas, text=hint, bg="white", fg="#888", font=("Segoe UI", 12), justify="center")
        self.empty_hint.place(relx=0.5, rely=0.5, anchor="center")

        out_frame = ttk.LabelFrame(outer, text="Destino", padding=8)
        out_frame.pack(fill="x", pady=(10, 6))
        ttk.Entry(out_frame, textvariable=self.output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(out_frame, text="Escolher pasta…", command=self.choose_output).pack(side="left", padx=(8, 0))

        settings = ttk.Frame(outer)
        settings.pack(fill="x", pady=5)
        ttk.Label(settings, text="Qualidade:").pack(side="left")
        quality_box = ttk.Combobox(
            settings, textvariable=self.quality, state="readonly", width=24,
            values=["Alta qualidade", "Padrão (boa qualidade)", "Arquivo menor"]
        )
        quality_box.pack(side="left", padx=8)
        ttk.Label(settings, text="MP4 / H.264 + AAC").pack(side="left", padx=8)

        ttk.Label(outer, textvariable=self.status).pack(anchor="w", pady=(8, 0))

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(10, 0))
        self.convert_btn = ttk.Button(bottom, text="Converter para MP4", command=self.start_conversion)
        self.convert_btn.pack(side="left")
        self.cancel_btn = ttk.Button(bottom, text="Cancelar", command=self.cancel_conversion, state="disabled")
        self.cancel_btn.pack(side="left", padx=8)
        ttk.Button(bottom, text="Abrir pasta de destino", command=self.open_output).pack(side="right")

    def _bind_mousewheel(self):
        def on_wheel(event):
            if self.canvas.winfo_height() >= self.rows_frame.winfo_reqheight():
                return
            delta = -1 if (event.num == 4 or event.delta > 0) else 1
            self.canvas.yview_scroll(delta * 2, "units")
        self.root.bind_all("<MouseWheel>", on_wheel)
        self.root.bind_all("<Button-4>", on_wheel)
        self.root.bind_all("<Button-5>", on_wheel)

    # ------------------------------------------------------- Arrastar e soltar
    def _setup_drag_and_drop(self):
        if not DND_OK:
            return
        for widget in (self.root, self.canvas, self.list_border, self.empty_hint):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._on_drop)
            widget.dnd_bind("<<DropEnter>>", self._on_drag_enter)
            widget.dnd_bind("<<DropLeave>>", self._on_drag_leave)

    def _on_drag_enter(self, event):
        self.list_border.configure(highlightbackground="#2b7de9", highlightcolor="#2b7de9")
        return event.action

    def _on_drag_leave(self, event):
        self.list_border.configure(highlightbackground="#cccccc", highlightcolor="#cccccc")
        return event.action

    def _on_drop(self, event):
        self._on_drag_leave(event)
        paths = self.root.tk.splitlist(event.data)
        self._add_paths(paths)
        return event.action

    def _expand_paths(self, paths):
        """Aceita arquivos e pastas; em pastas, adiciona os vídeos encontrados."""
        found, ignored = [], 0
        for p in paths:
            if os.path.isdir(p):
                for folder, _, names in os.walk(p):
                    for n in sorted(names):
                        if os.path.splitext(n)[1].lower() in VIDEO_EXTS:
                            found.append(os.path.join(folder, n))
            elif os.path.isfile(p):
                if os.path.splitext(p)[1].lower() in VIDEO_EXTS:
                    found.append(p)
                else:
                    ignored += 1
        return found, ignored

    # ----------------------------------------------------------------- Lista
    def _add_paths(self, paths, from_dialog=False):
        if self.is_converting:
            self.status.set("Aguarde o fim da conversão para adicionar novos vídeos.")
            return
        if from_dialog:
            found, ignored = [p for p in paths if os.path.isfile(p)], 0
        else:
            found, ignored = self._expand_paths(paths)
        existing = {r.path for r in self.rows}
        added = 0
        for path in found:
            if path in existing:
                continue
            row = FileRow(self, self.rows_frame, path)
            row.frame.pack(fill="x")
            self.rows.append(row)
            existing.add(path)
            added += 1
        self._refresh_empty_hint()
        msg = f"{len(self.rows)} vídeo(s) na lista."
        if ignored:
            msg += f" {ignored} arquivo(s) ignorado(s) (não são vídeo)."
        if self.rows or ignored:
            self.status.set(msg)

    def _refresh_empty_hint(self):
        if self.rows:
            self.empty_hint.place_forget()
        else:
            self.empty_hint.place(relx=0.5, rely=0.5, anchor="center")

    def add_files(self):
        selected = filedialog.askopenfilenames(
            title="Selecione os vídeos",
            filetypes=[
                ("Arquivos de vídeo", "*.mp4 *.mkv *.avi *.mov *.wmv *.webm *.flv *.mpeg *.mpg *.m4v *.3gp *.ts"),
                ("Todos os arquivos", "*.*")
            ]
        )
        self._add_paths(selected, from_dialog=True)

    def remove_row(self, row):
        if self.is_converting:
            return
        row.frame.destroy()
        self.rows.remove(row)
        self._refresh_empty_hint()
        self.status.set(f"{len(self.rows)} vídeo(s) na lista." if self.rows else "Lista vazia.")

    def clear_files(self):
        if self.is_converting:
            return
        for row in self.rows:
            row.frame.destroy()
        self.rows.clear()
        self._refresh_empty_hint()
        self.status.set("Lista limpa.")

    def choose_output(self):
        path = filedialog.askdirectory(title="Escolha a pasta de destino")
        if path:
            self.output_dir.set(path)

    def open_output(self):
        path = self.output_dir.get().strip()
        if not path:
            messagebox.showinfo("Destino", "Escolha uma pasta de destino primeiro.")
            return
        os.makedirs(path, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.name == "posix":
                subprocess.Popen(["xdg-open", path])
            else:
                messagebox.showinfo("Pasta", path)
        except Exception as exc:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{exc}")

    def _check_ffmpeg(self):
        use_local_ffmpeg()
        if ffmpeg_available():
            return
        if os.name == "nt":
            self._auto_install_ffmpeg()
        else:
            self.status.set("FFmpeg não encontrado. Instale-o pelo gerenciador de pacotes (ex.: sudo apt install ffmpeg).")
            self.root.after(400, lambda: messagebox.showwarning(
                "FFmpeg necessário",
                "O programa precisa do FFmpeg para converter vídeos.\n\n"
                "Instale com o gerenciador de pacotes da sua distribuição "
                "(ex.: sudo apt install ffmpeg) e abra o programa novamente."
            ))

    def _auto_install_ffmpeg(self):
        """Baixa o FFmpeg automaticamente, mostrando uma janela de progresso."""
        self.convert_btn.configure(state="disabled")
        self.status.set("Preparando o FFmpeg (só na primeira vez)…")

        win = tk.Toplevel(self.root)
        win.title("Preparando o conversor")
        win.resizable(False, False)
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        frame = ttk.Frame(win, padding=18)
        frame.pack()
        ttk.Label(frame, text="Baixando o FFmpeg", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Isso é feito uma única vez (cerca de 30 MB).",
                  foreground="#555").pack(anchor="w", pady=(2, 10))
        bar = ttk.Progressbar(frame, mode="determinate", maximum=100, length=360)
        bar.pack(fill="x")
        info = ttk.Label(frame, text="Conectando…")
        info.pack(anchor="w", pady=(6, 0))
        win.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - win.winfo_reqwidth()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - win.winfo_reqheight()) // 2
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        win.grab_set()

        def on_progress(done, total, phase):
            def update():
                if phase == "Extraindo":
                    bar.configure(mode="indeterminate")
                    bar.start(12)
                    info.configure(text="Extraindo arquivos…")
                elif total:
                    bar["value"] = done * 100 / total
                    info.configure(text=f"Baixando… {done / 1_048_576:.0f} de {total / 1_048_576:.0f} MB "
                                        f"({int(done * 100 / total)}%)")
                else:
                    info.configure(text=f"Baixando… {done / 1_048_576:.0f} MB")
            self.root.after(0, update)

        def finish(error):
            bar.stop()
            win.grab_release()
            win.destroy()
            self.convert_btn.configure(state="normal")
            if error is None:
                self.status.set("FFmpeg instalado. Adicione vídeos para começar.")
            else:
                self.status.set("Não foi possível baixar o FFmpeg.")
                messagebox.showerror(
                    "Falha ao baixar o FFmpeg",
                    f"{error}\n\nVerifique sua conexão com a internet e abra o programa novamente.\n"
                    "Se preferir, instale manualmente: https://ffmpeg.org/download.html"
                )

        def worker():
            try:
                download_ffmpeg(on_progress)
                err = None
            except Exception as exc:
                err = exc
            self.root.after(0, lambda: finish(err))

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------- Conversão
    def start_conversion(self):
        if self.is_converting:
            return
        if not self.rows:
            messagebox.showinfo("Nenhum vídeo", "Adicione pelo menos um vídeo à lista.")
            return
        if not shutil.which("ffmpeg"):
            messagebox.showerror("FFmpeg não encontrado", "Instale o FFmpeg e adicione-o ao PATH.")
            return
        output = self.output_dir.get().strip()
        if not output:
            messagebox.showerror("Destino inválido", "Escolha uma pasta de destino.")
            return
        try:
            os.makedirs(output, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Erro no destino", str(exc))
            return

        pending = [r for r in self.rows if r.state != "done"]
        if not pending:
            messagebox.showinfo("Nada a converter", "Todos os vídeos da lista já foram convertidos.")
            return
        for row in pending:
            row.reset()
            row.remove_btn.configure(state="disabled")

        self.is_converting = True
        self.cancel_requested = False
        self.convert_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        threading.Thread(target=self._conversion_worker, args=(pending, output, self.quality.get()), daemon=True).start()

    def _ui(self, func, *args, **kwargs):
        self.root.after(0, lambda: func(*args, **kwargs))

    def _conversion_worker(self, rows, output, quality):
        completed = 0
        errors = []
        total = len(rows)
        crf = {"Alta qualidade": "18", "Padrão (boa qualidade)": "23", "Arquivo menor": "28"}.get(quality, "23")

        for index, row in enumerate(rows, start=1):
            if self.cancel_requested:
                break
            source = row.path
            name = os.path.splitext(os.path.basename(source))[0]
            destination = os.path.join(output, name + ".mp4")
            if os.path.abspath(source) == os.path.abspath(destination):
                destination = os.path.join(output, name + "_convertido.mp4")

            # Evita sobrescrever um arquivo existente.
            if os.path.exists(destination):
                stem, ext = os.path.splitext(destination)
                n = 1
                while os.path.exists(f"{stem}_{n}{ext}"):
                    n += 1
                destination = f"{stem}_{n}{ext}"

            duration = get_duration(source)
            row.state = "converting"
            self._ui(self.status.set, f"Convertendo {index}/{total}: {os.path.basename(source)}")
            self._ui(row.set_status, "Convertendo…", "info")
            if duration is None:
                self._ui(row.set_indeterminate)

            command = [
                "ffmpeg", "-hide_banner", "-y", "-nostdin", "-i", source,
                "-c:v", "libx264", "-preset", "medium", "-crf", crf,
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                "-progress", "pipe:1", "-nostats", destination
            ]
            stderr_tail = deque(maxlen=30)
            try:
                proc = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW
                )
                self.current_process = proc

                # Lê o stderr em paralelo para o buffer não travar o ffmpeg.
                def drain_stderr(stream=proc.stderr, tail=stderr_tail):
                    for line in stream:
                        tail.append(line.rstrip())
                err_thread = threading.Thread(target=drain_stderr, daemon=True)
                err_thread.start()

                last_pct = -1
                for line in proc.stdout:
                    key, _, value = line.strip().partition("=")
                    if key in ("out_time_us", "out_time_ms") and duration:
                        try:
                            seconds = int(value) / 1_000_000
                        except ValueError:
                            continue
                        pct = max(0, min(99, int(seconds / duration * 100)))
                        if pct != last_pct:
                            last_pct = pct
                            self._ui(row.set_progress, pct)
                proc.wait()
                err_thread.join(timeout=2)

                if self.cancel_requested:
                    row.state = "canceled"
                    self._ui(row.set_status, "Cancelado", "warn")
                    try:
                        if os.path.exists(destination):
                            os.remove(destination)  # remove arquivo parcial
                    except OSError:
                        pass
                    break
                if proc.returncode == 0:
                    completed += 1
                    row.state = "done"
                    self._ui(row.set_progress, 100)
                    self._ui(row.set_status, f"Concluído → {os.path.basename(destination)}", "ok")
                else:
                    row.state = "error"
                    errors.append(f"{os.path.basename(source)}: " + "\n".join(list(stderr_tail)[-5:]))
                    self._ui(row.set_status, "Falhou na conversão", "error")
            except Exception as exc:
                row.state = "error"
                errors.append(f"{os.path.basename(source)}: {exc}")
                self._ui(row.set_status, "Falhou na conversão", "error")
            finally:
                self.current_process = None

        # Quem não chegou a rodar por causa do cancelamento
        for row in rows:
            if row.state == "waiting" and self.cancel_requested:
                row.state = "canceled"
                self._ui(row.set_status, "Cancelado", "warn")

        self.root.after(0, lambda: self._finish_conversion(completed, total, errors))

    def cancel_conversion(self):
        self.cancel_requested = True
        proc = self.current_process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
        self.status.set("Cancelando…")

    def _finish_conversion(self, completed, total, errors):
        self.is_converting = False
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        for row in self.rows:
            row.bar.stop()
            row.remove_btn.configure(state="normal")
            if row.state == "canceled":
                row.set_progress(row.bar["value"])
        if self.cancel_requested:
            self.status.set(f"Conversão cancelada. {completed} arquivo(s) concluído(s).")
        else:
            self.status.set(f"Concluído: {completed} de {total} vídeo(s) convertido(s).")
        if errors:
            messagebox.showwarning(
                "Conversão finalizada com avisos",
                f"{completed} arquivo(s) convertido(s).\n\nFalhas ({len(errors)}):\n" +
                "\n\n".join(errors[:5]) +
                ("\n\nOutras falhas foram omitidas." if len(errors) > 5 else "")
            )
        elif not self.cancel_requested:
            messagebox.showinfo("Concluído", f"{completed} vídeo(s) convertido(s) para MP4.")


def resource_path(name):
    """Caminho de um arquivo junto ao programa (funciona também dentro do .exe do PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def main():
    root = TkinterDnD.Tk() if DND_OK else tk.Tk()
    try:
        if os.name == "nt":
            root.iconbitmap(resource_path("icone.ico"))
    except tk.TclError:
        pass
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except tk.TclError:
        pass
    VideoConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
