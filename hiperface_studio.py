# -*- coding: utf-8 -*-
"""
HIPERFACE Studio - GUI terminal for SICK HIPERFACE(R) encoders over RS-485.
English / Persian UI, dark / light theme, built-in help and about window.
Pure Python 3.8+ (Windows 7 SP1 .. 11) + tkinter + pyserial.
"""
import sys
import os
import json
import queue
import datetime
import math
import platform
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from hiperface_core import (serial, APP_NAME, APP_VERSION, DEMO_PORT, HiperfaceEncoder, SimulatedEncoderSerial,
                            Worker, parse_int, parse_hex_bytes, hex_spaced, resource_dir, settings_path,
                            enable_dpi_awareness, fault_text, describe_uart, find_pdf, open_path_or_url,
                            uart_to_port, load_private_fonts, PERSIAN_FONTS, FONT_FALLBACK_FA,
                            PDF_ONLINE, PDF_NAME, PDF_FALLBACK_DIR, REPO_URL, ISSUES_URL, VAZIR_URL,
                            AUTHOR, AUTHOR_FA, AUTHOR_EMAIL)
from hiperface_i18n import tr, bidi, card_text, LANGS
import hiperface_help as HELP

# =============================================================================
#  Themes
# =============================================================================
THEMES = {
    "dark": {
        "bg": "#16141c", "panel": "#1d1a25", "card": "#25212f", "card_hi": "#2e2939",
        "border": "#3a3449", "text": "#ece9f3", "muted": "#a29cb2", "faint": "#6f6982",
        "accent": "#8b6cf0", "accent_hi": "#a088f6", "accent_dim": "#3a2e66", "on_accent": "#ffffff",
        "ok": "#4cc38a", "warn": "#f0b44c", "err": "#ef6a5b", "err_hi": "#f4847a",
        "danger_bg": "#5a2a2b", "danger_hover": "#73332f", "danger_border": "#5a2a2b", "danger_badge": "#4a2324",
        "tx": "#8fb3ff", "rx": "#5fd39b", "log_bg": "#100e15", "link": "#a99af7",
    },
    "light": {
        "bg": "#f3f1f7", "panel": "#e9e5f1", "card": "#ffffff", "card_hi": "#f0edf6",
        "border": "#d8d2e4", "text": "#221d2e", "muted": "#625b77", "faint": "#9890aa",
        "accent": "#6847d6", "accent_hi": "#7b5ee3", "accent_dim": "#e6dffb", "on_accent": "#ffffff",
        "ok": "#17885a", "warn": "#a8660f", "err": "#c93a2d", "err_hi": "#b83226",
        "danger_bg": "#fbe4e1", "danger_hover": "#f6cfc9", "danger_border": "#efc4bd", "danger_badge": "#fbe4e1",
        "tx": "#2f5fc4", "rx": "#17885a", "log_bg": "#fcfbff", "link": "#5a3cc8",
    },
}
C = dict(THEMES["dark"])


def pick_font(root, candidates, fallback="TkDefaultFont"):
    import tkinter.font as tkfont
    fams = set(f.lower() for f in tkfont.families(root))
    for c in candidates:
        if c.lower() in fams:
            return c
    return fallback


# =============================================================================
#  Small widgets: drawn icon buttons + tooltips
# =============================================================================
class Tooltip(object):
    def __init__(self, widget, text_fn, font):
        self.w = widget
        self.text_fn = text_fn
        self.font = font
        self.tip = None
        self.job = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _e=None):
        self._cancel()
        self.job = self.w.after(450, self._show)

    def _cancel(self):
        if self.job:
            self.w.after_cancel(self.job)
            self.job = None

    def _show(self):
        if self.tip:
            return
        x = self.w.winfo_rootx() + self.w.winfo_width() // 2
        y = self.w.winfo_rooty() + self.w.winfo_height() + 6
        self.tip = tk.Toplevel(self.w)
        self.tip.wm_overrideredirect(True)
        lb = tk.Label(self.tip, text=self.text_fn(), bg=C["text"], fg=C["bg"], font=(self.font, 9), padx=8, pady=3)
        lb.pack()
        self.tip.update_idletasks()
        self.tip.wm_geometry("+%d+%d" % (x - self.tip.winfo_width() // 2, y))

    def _hide(self, _e=None):
        self._cancel()
        if self.tip:
            self.tip.destroy()
            self.tip = None


class IconButton(tk.Canvas):
    def __init__(self, parent, kind, command, bg, size=32):
        tk.Canvas.__init__(self, parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.kind = kind
        self.command = command
        self.size = size
        self.base_bg = bg
        self.hover = False
        self.enabled = True
        self.draw()
        self.bind("<Enter>", lambda e: self._hov(True))
        self.bind("<Leave>", lambda e: self._hov(False))
        self.bind("<ButtonRelease-1>", lambda e: self.enabled and self.command(self))

    def set_enabled(self, on):
        self.enabled = on
        self.configure(cursor="hand2" if on else "arrow")
        self.draw()

    def _hov(self, h):
        self.hover = h and self.enabled
        self.draw()

    def set_kind(self, kind):
        self.kind = kind
        self.draw()

    def draw(self):
        self.delete("all")
        s = self.size
        m = s / 2.0
        bgc = C["card_hi"] if self.hover else self.base_bg
        if self.hover:
            self.create_oval(1, 1, s - 1, s - 1, fill=bgc, outline="")
        col = (C["text"] if self.hover else C["muted"]) if self.enabled else C["faint"]
        k = self.kind
        if k in ("help", "about"):
            self.create_oval(m - 10, m - 10, m + 10, m + 10, outline=col, width=2)
            self.create_text(m, m + (0 if k == "help" else 1), text="?" if k == "help" else "i", fill=col,
                             font=("Segoe UI", 11, "bold"))
        elif k == "globe":
            r = 10
            self.create_oval(m - r, m - r, m + r, m + r, outline=col, width=2)
            self.create_oval(m - 4.5, m - r, m + 4.5, m + r, outline=col, width=1.5)
            self.create_line(m - r, m, m + r, m, fill=col, width=1.5)
            self.create_line(m - 8.4, m - 5, m + 8.4, m - 5, fill=col, width=1.2)
            self.create_line(m - 8.4, m + 5, m + 8.4, m + 5, fill=col, width=1.2)
        elif k == "sun":
            self.create_oval(m - 4.5, m - 4.5, m + 4.5, m + 4.5, fill=col, outline="")
            for i in range(8):
                a = math.radians(i * 45)
                self.create_line(m + 7 * math.cos(a), m + 7 * math.sin(a), m + 10 * math.cos(a), m + 10 * math.sin(a),
                                 fill=col, width=2, capstyle="round")
        elif k == "moon":
            self.create_oval(m - 8, m - 8, m + 8, m + 8, fill=col, outline="")
            self.create_oval(m - 3, m - 12, m + 11, m + 2, fill=bgc, outline="")
        elif k == "refresh":
            self.create_arc(m - 8, m - 8, m + 8, m + 8, start=60, extent=290, style="arc", outline=col, width=2)
            a = math.radians(-60)
            x, y = m + 8 * math.cos(a), m + 8 * math.sin(a)
            self.create_polygon(x - 1, y - 6, x + 5, y + 1, x - 5, y + 2, fill=col, outline="")


# =============================================================================
#  Application
# =============================================================================
class App(object):
    def __init__(self, root):
        self.root = root
        self.ser = None
        self.enc = None
        self.ui_q = queue.Queue()
        self.worker = Worker(self.ui_q)
        self.worker.start()
        self.tx_count = self.rx_count = self.err_count = 0
        self.polling = False
        self.poll_busy = False
        self.warn_flag = False
        self.settings = self._load_settings()
        self.lang = self.settings.get("lang", "en") if self.settings.get("lang") in ("en", "fa") else "en"
        self.theme = self.settings.get("theme", "dark") if self.settings.get("theme") in THEMES else "dark"
        self.log_entries = []
        self.dash = {}
        self.field_vars = {}
        self.help_win = None
        self.about_win = None
        self.cur_tab = "tab_pos"
        self.f_latin = pick_font(root, ["Segoe UI", "Tahoma", "DejaVu Sans"])
        self.f_fa = pick_font(root, PERSIAN_FONTS + FONT_FALLBACK_FA, self.f_latin)
        self.fa_is_vazir = self.f_fa in PERSIAN_FONTS
        self.f_mono = pick_font(root, ["Consolas", "Cascadia Mono", "Lucida Console", "DejaVu Sans Mono"])
        self.f_ui = self.f_fa if self.lang == "fa" else self.f_latin
        self._init_vars()

        root.title("%s  %s" % (APP_NAME, APP_VERSION))
        root.geometry(self.settings.get("geometry", "1360x860"))
        root.minsize(1300, 740)
        self._set_icon()
        self.build_all()
        self.log("info", self.t("ready", APP_NAME))
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(40, self._drain_ui_queue)

    # ------------------------------------------------------------ i18n helpers
    @property
    def rtl(self):
        return self.lang == "fa"

    def t(self, key, *args):
        return bidi(tr(self.lang, key, *args), self.lang)

    def raw_t(self, key, *args):
        return tr(self.lang, key, *args)

    def card(self, key):
        title, desc = card_text(self.lang, key)
        return bidi(title, self.lang), bidi(desc, self.lang)

    @property
    def S(self):   # "start" side
        return "right" if self.rtl else "left"

    @property
    def E(self):   # "end" side
        return "left" if self.rtl else "right"

    @property
    def A(self):   # anchor at start
        return "e" if self.rtl else "w"

    # ------------------------------------------------------------ settings
    def _init_vars(self):
        s = self.settings
        sv = lambda k, d: tk.StringVar(value=s.get(k, d))
        self.v_port = sv("port", "")
        self.v_baud = sv("baud", "9600")
        self.v_parity = sv("parity", "Even")
        self.v_addr = sv("addr", "40")
        self.v_code0 = sv("code0", "55")
        self.v_timeout = sv("timeout", "150")
        self.v_cpr = sv("cpr", "32768")
        self.v_interval = sv("interval", "200")
        self.v_log_poll = tk.BooleanVar(value=False)
        self.v_autoscroll = tk.BooleanVar(value=True)
        self.v_show_txrx = tk.BooleanVar(value=True)
        self.v_raw_crc = tk.BooleanVar(value=True)
        self.v_lang = tk.StringVar(value=self.lang)
        self.pdf_path = s.get("pdf_path", "")

    def _load_settings(self):
        try:
            with open(settings_path(), "r") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _save_settings(self):
        s = {"geometry": self.root.geometry(), "port": self.v_port.get(), "baud": self.v_baud.get(),
             "parity": self.v_parity.get(), "addr": self.v_addr.get(), "code0": self.v_code0.get(),
             "timeout": self.v_timeout.get(), "cpr": self.v_cpr.get(), "interval": self.v_interval.get(),
             "lang": self.lang, "theme": self.theme, "pdf_path": self.pdf_path}
        try:
            with open(settings_path(), "w") as fh:
                json.dump(s, fh, indent=2)
        except Exception:
            pass

    def _set_icon(self):
        ico = os.path.join(resource_dir(), "app.ico")
        try:
            if os.path.exists(ico) and sys.platform == "win32":
                self.root.iconbitmap(default=ico)
        except Exception:
            pass

    # ------------------------------------------------------------ (re)build
    def build_all(self):
        C.clear()
        C.update(THEMES[self.theme])
        self.f_ui = self.f_fa if self.rtl else self.f_latin
        help_open = bool(self.help_win and self.help_win.winfo_exists())
        about_open = bool(self.about_win and self.about_win.winfo_exists())
        for w in self.root.winfo_children():
            w.destroy()
        self.help_win = self.about_win = None
        self.root.configure(bg=C["bg"])
        self.cmd_buttons = []
        self._style()
        self._build()
        self._bind_keys()
        self.refresh_ports(quiet=True)
        self._render_log()
        self._restore_dash()
        self._set_connected(self.enc is not None)
        self._update_poll_btn()
        if help_open:
            self.open_help()
        if about_open:
            self.open_about()

    def set_lang(self, lang):
        if lang == self.lang:
            return
        self.lang = lang
        self.v_lang.set(lang)
        self.build_all()
        self.log("info", self.t("lang_changed"))
        self._save_settings()

    def toggle_theme(self, _w=None):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.build_all()
        self.log("info", self.t("theme_changed", self.raw_t("theme_" + self.theme)))
        self._save_settings()

    def _style(self):
        st = ttk.Style(self.root)
        st.theme_use("clam")
        F = self.f_ui
        st.configure(".", background=C["bg"], foreground=C["text"], fieldbackground=C["card_hi"],
                     bordercolor=C["border"], lightcolor=C["border"], darkcolor=C["border"],
                     troughcolor=C["panel"], focuscolor=C["accent"], font=(F, 10),
                     selectbackground=C["accent"], selectforeground=C["on_accent"], insertcolor=C["text"])
        st.configure("TFrame", background=C["bg"])
        st.configure("Panel.TFrame", background=C["panel"])
        st.configure("Card.TFrame", background=C["card"])
        st.configure("TLabel", background=C["bg"], foreground=C["text"])
        st.configure("Panel.TLabel", background=C["panel"])
        st.configure("PanelMuted.TLabel", background=C["panel"], foreground=C["muted"], font=(F, 9))
        st.configure("Card.TLabel", background=C["card"])
        st.configure("CardTitle.TLabel", background=C["card"], font=(F, 11, "bold"))
        st.configure("CardDesc.TLabel", background=C["card"], foreground=C["muted"], font=(F, 9))
        st.configure("CardField.TLabel", background=C["card"], foreground=C["muted"], font=(F, 9))
        st.configure("Badge.TLabel", background=C["accent_dim"], foreground=C["accent"] if self.theme == "light"
                     else C["accent_hi"], font=(self.f_mono, 9, "bold"), padding=(6, 1))
        st.configure("Danger.Badge.TLabel", background=C["danger_badge"], foreground=C["err_hi"],
                     font=(F, 9, "bold"))
        st.configure("DangerOp.Badge.TLabel", background=C["danger_badge"], foreground=C["err_hi"])
        st.configure("Brand.TLabel", background=C["panel"], font=(F, 15, "bold"))
        st.configure("BrandSub.TLabel", background=C["panel"], foreground=C["muted"], font=(F, 9))
        st.configure("Section.TLabel", background=C["bg"], foreground=C["muted"], font=(F, 9, "bold"))

        st.configure("TButton", background=C["card_hi"], foreground=C["text"], borderwidth=0,
                     padding=(12, 6), relief="flat", font=(F, 10))
        st.map("TButton", background=[("disabled", C["card"]), ("pressed", C["border"]), ("active", C["border"])],
               foreground=[("disabled", C["faint"])])
        st.configure("Accent.TButton", background=C["accent"], foreground=C["on_accent"], font=(F, 10, "bold"))
        st.map("Accent.TButton", background=[("disabled", C["accent_dim"]), ("pressed", C["accent"]),
                                             ("active", C["accent_hi"])],
               foreground=[("disabled", C["muted"])])
        st.configure("Danger.TButton", background=C["danger_bg"], foreground=C["err_hi"], font=(F, 10, "bold"))
        st.map("Danger.TButton", background=[("disabled", C["card"]), ("active", C["danger_hover"])],
               foreground=[("disabled", C["faint"])])
        st.configure("Small.TButton", padding=(8, 3), font=(F, 9))

        st.configure("TEntry", fieldbackground=C["card_hi"], foreground=C["text"], borderwidth=1,
                     padding=(6, 4), insertcolor=C["text"])
        st.map("TEntry", bordercolor=[("focus", C["accent"])], lightcolor=[("focus", C["accent"])],
               fieldbackground=[("disabled", C["card"])], foreground=[("disabled", C["faint"])])
        st.configure("TCombobox", fieldbackground=C["card_hi"], background=C["card_hi"], foreground=C["text"],
                     arrowcolor=C["muted"], padding=(6, 3))
        st.map("TCombobox", fieldbackground=[("readonly", C["card_hi"]), ("disabled", C["card"])],
               foreground=[("readonly", C["text"]), ("disabled", C["faint"])],
               bordercolor=[("focus", C["accent"])], arrowcolor=[("active", C["accent_hi"])])
        self.root.option_add("*TCombobox*Listbox.background", C["card_hi"])
        self.root.option_add("*TCombobox*Listbox.foreground", C["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", C["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", C["on_accent"])
        self.root.option_add("*TCombobox*Listbox.font", (F, 10))
        st.configure("TSpinbox", fieldbackground=C["card_hi"], foreground=C["text"], arrowcolor=C["muted"],
                     padding=(4, 3), background=C["card_hi"])
        st.configure("TCheckbutton", background=C["panel"], foreground=C["text"], font=(F, 9))
        st.map("TCheckbutton", background=[("active", C["panel"])],
               indicatorcolor=[("selected", C["accent"]), ("!selected", C["card_hi"])])
        st.configure("Bg.TCheckbutton", background=C["bg"])
        st.map("Bg.TCheckbutton", background=[("active", C["bg"])])
        st.configure("Card.TCheckbutton", background=C["card"])
        st.map("Card.TCheckbutton", background=[("active", C["card"])])
        st.configure("TNotebook", background=C["bg"], borderwidth=0, tabmargins=(0, 0, 0, 0))
        st.configure("TNotebook.Tab", background=C["bg"], foreground=C["muted"], padding=(16, 8),
                     borderwidth=0, font=(F, 10, "bold"))
        st.map("TNotebook.Tab", background=[("selected", C["card"]), ("active", C["panel"])],
               foreground=[("selected", C["text"]), ("active", C["text"])])
        st.configure("Vertical.TScrollbar", background=C["card_hi"], troughcolor=C["log_bg"],
                     arrowcolor=C["muted"], borderwidth=0)
        st.configure("TPanedwindow", background=C["bg"])
        st.configure("Sash", sashthickness=6, background=C["bg"])

    # ------------------------------------------------------------ layout
    def _build(self):
        r = self.root
        S, E = self.S, self.E
        top = ttk.Frame(r, style="Panel.TFrame", padding=(16, 10))
        top.pack(side="top", fill="x")
        brand = ttk.Frame(top, style="Panel.TFrame")
        brand.pack(side=S)
        self.led = tk.Canvas(brand, width=14, height=14, bg=C["panel"], highlightthickness=0)
        self.led_dot = self.led.create_oval(2, 2, 12, 12, fill=C["faint"], outline="")
        c0, c1 = (1, 0) if self.rtl else (0, 1)
        self.led.grid(row=0, column=c0, rowspan=2, padx=(10, 0) if self.rtl else (0, 10))
        ttk.Label(brand, text="HIPERFACE Studio", style="Brand.TLabel").grid(row=0, column=c1, sticky=self.A)
        self.lbl_conn = ttk.Label(brand, text="", style="BrandSub.TLabel")
        self.lbl_conn.grid(row=1, column=c1, sticky=self.A)

        icons = ttk.Frame(top, style="Panel.TFrame")
        icons.pack(side=E, padx=(0, 0))
        self.icon_btns = {}
        for kind, cmd, tip in [("help", lambda w: self.open_help(), "tip_help"),
                               ("about", lambda w: self.open_about(), "tip_about"),
                               ("globe", self.show_lang_menu, "tip_lang"),
                               ("sun" if self.theme == "dark" else "moon", self.toggle_theme, "tip_theme")]:
            b = IconButton(icons, kind, cmd, C["panel"])
            b.pack(side=S, padx=1)
            Tooltip(b, lambda tip=tip: self.t(tip), self.f_ui)
            self.icon_btns[kind] = b
            if kind == "globe":
                lb = tk.Label(icons, text="FA" if self.rtl else "EN", bg=C["panel"], fg=C["accent_hi"]
                              if self.theme == "dark" else C["accent"], font=(self.f_latin, 8, "bold"),
                              cursor="hand2")
                lb.pack(side=S, padx=(0, 4))
                lb.bind("<Button-1>", lambda e, b=b: self.show_lang_menu(b))
                Tooltip(lb, lambda: self.t("tip_lang"), self.f_ui)
        sep = tk.Frame(top, bg=C["border"], width=1, height=34)
        sep.pack(side=E, padx=12)

        bar = ttk.Frame(top, style="Panel.TFrame")
        bar.pack(side=E)
        n = 8
        col = (lambda i: n - 1 - i) if self.rtl else (lambda i: i)
        padx = (0, 10) if self.rtl else (10, 0)

        def lab(key, i):
            ttk.Label(bar, text=self.t(key), style="PanelMuted.TLabel").grid(row=0, column=col(i), sticky=self.A,
                                                                              padx=padx)
        lab("port", 0)
        self.cb_port = ttk.Combobox(bar, textvariable=self.v_port, width=21, state="readonly")
        self.cb_port.grid(row=1, column=col(0), padx=padx)
        self.btn_refresh = IconButton(bar, "refresh", lambda w: self.refresh_ports(), C["panel"], size=30)
        self.btn_refresh.grid(row=1, column=col(1), padx=(0, 2) if self.rtl else (2, 0))
        Tooltip(self.btn_refresh, lambda: self.t("tip_refresh"), self.f_ui)
        lab("baud", 2)
        self.cb_baud = ttk.Combobox(bar, textvariable=self.v_baud, width=7, state="readonly",
                                    values=["600", "1200", "2400", "4800", "9600", "19200", "38400"])
        self.cb_baud.grid(row=1, column=col(2), padx=padx)
        lab("parity", 3)
        self.cb_par = ttk.Combobox(bar, textvariable=self.v_parity, width=6, state="readonly",
                                   values=["Even", "Odd", "None"])
        self.cb_par.grid(row=1, column=col(3), padx=padx)
        lab("addr", 4)
        self.e_addr = ttk.Entry(bar, textvariable=self.v_addr, width=5, font=(self.f_mono, 10))
        self.e_addr.grid(row=1, column=col(4), padx=padx)
        lab("code0", 5)
        self.e_code0 = ttk.Entry(bar, textvariable=self.v_code0, width=5, font=(self.f_mono, 10))
        self.e_code0.grid(row=1, column=col(5), padx=padx)
        lab("timeout", 6)
        self.e_tmo = ttk.Entry(bar, textvariable=self.v_timeout, width=5, font=(self.f_mono, 10))
        self.e_tmo.grid(row=1, column=col(6), padx=padx)
        self.btn_connect = ttk.Button(bar, text=self.t("connect"), style="Accent.TButton", width=11,
                                      command=self.toggle_connection)
        self.btn_connect.grid(row=0, column=col(7), rowspan=2, padx=(0, 16) if self.rtl else (16, 0), sticky="ns")

        sb = ttk.Frame(r, style="Panel.TFrame", padding=(16, 5))
        sb.pack(side="bottom", fill="x")
        self.lbl_status = ttk.Label(sb, text="", style="PanelMuted.TLabel")
        self.lbl_status.pack(side=S)
        self.lbl_counts = ttk.Label(sb, text="", style="PanelMuted.TLabel")
        self.lbl_counts.pack(side=E)

        body = ttk.Frame(r, padding=(16, 14, 16, 10))
        body.pack(side="top", fill="both", expand=True)
        dcol, mcol = (1, 0) if self.rtl else (0, 1)
        body.columnconfigure(mcol, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_dashboard(body, dcol)

        pw = ttk.PanedWindow(body, orient="vertical")
        pw.grid(row=0, column=mcol, sticky="nsew", padx=(0, 14) if self.rtl else (14, 0))
        nbwrap = ttk.Frame(pw)
        logwrap = ttk.Frame(pw)
        pw.add(nbwrap, weight=3)
        pw.add(logwrap, weight=2)
        self.nb = ttk.Notebook(nbwrap)
        self.nb.pack(fill="both", expand=True)
        self.tabs = []
        self._tab_position()
        self._tab_counter()
        self._tab_data()
        self._tab_info()
        self._tab_config()
        self._tab_raw()
        for key, holder in (reversed(self.tabs) if self.rtl else self.tabs):
            self.nb.add(holder, text="  %s  " % self.t(key))
        for key, holder in self.tabs:
            if key == self.cur_tab:
                self.nb.select(holder)
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab)
        self._build_log(logwrap)
        self._update_counts()

    def _on_tab(self, _e=None):
        try:
            cur = self.nb.select()
            for key, holder in self.tabs:
                if str(holder) == cur:
                    self.cur_tab = key
        except Exception:
            pass

    # ------------------------------------------------------------ dashboard
    def _build_dashboard(self, parent, column):
        d = tk.Frame(parent, bg=C["panel"], width=300)
        d.grid(row=0, column=column, sticky="ns")
        d.grid_propagate(False)
        d.pack_propagate(False)
        inner = tk.Frame(d, bg=C["panel"])
        inner.pack(fill="both", expand=True, padx=18, pady=12)
        tk.Label(inner, text=self.t("live_position"), bg=C["panel"], fg=C["muted"],
                 font=(self.f_ui, 9, "bold")).pack(anchor=self.A)
        self.dial = tk.Canvas(inner, width=210, height=210, bg=C["panel"], highlightthickness=0)
        self.dial.pack(pady=(6, 2))
        self._draw_dial()
        self.lbl_angle = tk.Label(inner, text="---.--\u00b0", bg=C["panel"], fg=C["text"],
                                  font=(self.f_mono, 28, "bold"))
        self.lbl_angle.pack()
        self.lbl_raw = tk.Label(inner, text=self.t("raw_none"), bg=C["panel"], fg=C["muted"], font=(self.f_mono, 10))
        self.lbl_raw.pack()
        self.lbl_turns = tk.Label(inner, text=self.t("turns_none"), bg=C["panel"], fg=C["muted"],
                                  font=(self.f_mono, 10))
        self.lbl_turns.pack(pady=(0, 6))

        grid = tk.Frame(inner, bg=C["panel"])
        grid.pack(fill="x", pady=(4, 8))
        lc, vc = (1, 0) if self.rtl else (0, 1)
        grid.columnconfigure(vc, weight=1)
        self.kv = {}
        for i, k in enumerate(["status", "temp", "counter", "serial"]):
            tk.Label(grid, text=self.t("k_" + k), bg=C["panel"], fg=C["muted"], font=(self.f_ui, 9)).grid(
                row=i, column=lc, sticky=self.A, pady=2)
            v = tk.Label(grid, text="--", bg=C["panel"], fg=C["text"], font=(self.f_mono, 10))
            v.grid(row=i, column=vc, sticky="w" if self.rtl else "e", pady=2)
            self.kv[k] = v

        ctl = ttk.Frame(inner, style="Panel.TFrame")
        ctl.pack(fill="x", pady=(6, 0))
        a, b = (1, 0) if self.rtl else (0, 1)
        px = (0, 10) if self.rtl else (10, 0)
        ttk.Label(ctl, text=self.t("cpr"), style="PanelMuted.TLabel").grid(row=0, column=a, sticky=self.A)
        ttk.Entry(ctl, textvariable=self.v_cpr, width=8, font=(self.f_mono, 10)).grid(row=1, column=a, sticky=self.A)
        ttk.Label(ctl, text=self.t("interval"), style="PanelMuted.TLabel").grid(row=0, column=b, sticky=self.A, padx=px)
        ttk.Spinbox(ctl, from_=50, to=5000, increment=50, textvariable=self.v_interval, width=6,
                    font=(self.f_mono, 10)).grid(row=1, column=b, sticky=self.A, padx=px)
        if self.rtl:
            ctl.columnconfigure(0, weight=1)

        row = ttk.Frame(inner, style="Panel.TFrame")
        row.pack(fill="x", pady=(10, 4))
        pc, sc = (1, 0) if self.rtl else (0, 1)
        row.columnconfigure(pc, weight=3)
        row.columnconfigure(sc, weight=2)
        self.btn_poll = ttk.Button(row, text=self.t("live"), style="Accent.TButton", command=self.toggle_poll)
        self.btn_poll.grid(row=0, column=pc, sticky="ew")
        self.cmd_buttons.append(self.btn_poll)
        bs = ttk.Button(row, text=self.t("snapshot"), command=self.snapshot)
        bs.grid(row=0, column=sc, sticky="ew", padx=(0, 6) if self.rtl else (6, 0))
        self.cmd_buttons.append(bs)
        ttk.Checkbutton(inner, text=self.t("log_poll"), variable=self.v_log_poll).pack(anchor=self.A)

    def _draw_dial(self):
        cv = self.dial
        cx = cy = 105
        R = 92
        cv.create_oval(cx - R, cy - R, cx + R, cy + R, outline=C["border"], width=2)
        cv.create_oval(cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14, outline=C["card_hi"], width=1)
        for deg in range(0, 360, 10):
            a = math.radians(deg - 90)
            major = deg % 90 == 0
            mid = deg % 30 == 0
            r1 = R - (16 if major else (10 if mid else 6))
            cv.create_line(cx + r1 * math.cos(a), cy + r1 * math.sin(a), cx + R * math.cos(a), cy + R * math.sin(a),
                           fill=C["muted"] if (major or mid) else C["faint"], width=2 if major else 1)
            if major:
                tr_ = R - 30
                cv.create_text(cx + tr_ * math.cos(a), cy + tr_ * math.sin(a), text=str(deg),
                               fill=C["faint"], font=(self.f_mono, 8))
        self.arc = cv.create_arc(cx - R + 4, cy - R + 4, cx + R - 4, cy + R - 4, start=90, extent=0,
                                 style="arc", outline=C["accent"], width=5)
        self.needle = cv.create_line(cx, cy, cx, cy - R + 20, fill=C["accent_hi"], width=3, capstyle="round")
        cv.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=C["accent"], outline=C["panel"], width=2)

    def _set_dial(self, angle):
        cx = cy = 105
        L = 72
        a = math.radians(angle - 90)
        self.dial.coords(self.needle, cx, cy, cx + L * math.cos(a), cy + L * math.sin(a))
        self.dial.itemconfigure(self.arc, extent=-angle if angle < 359.99 else -359.99)

    # ------------------------------------------------------------ cards
    def _tab(self, key):
        holder = ttk.Frame(self.nb, style="Card.TFrame")
        self.tabs.append((key, holder))
        cv = tk.Canvas(holder, bg=C["card"], highlightthickness=0, borderwidth=0)
        sb = ttk.Scrollbar(holder, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True)
        outer = ttk.Frame(cv, style="Card.TFrame", padding=(14, 14))
        win = cv.create_window(0, 0, window=outer, anchor="nw")
        outer.columnconfigure(0, weight=1, uniform="c")
        outer.columnconfigure(1, weight=1, uniform="c")
        outer._next = 0

        def sync(_e=None):
            cv.configure(scrollregion=(0, 0, outer.winfo_reqwidth(), outer.winfo_reqheight()))
            need = outer.winfo_reqheight() > cv.winfo_height() + 2
            if need and not sb.winfo_ismapped():
                sb.pack(side="right", fill="y", before=cv)
            elif not need and sb.winfo_ismapped():
                sb.pack_forget()
                cv.yview_moveto(0)
        outer.bind("<Configure>", sync)
        cv.bind("<Configure>", lambda e: (cv.itemconfigure(win, width=e.width), sync()))

        def wheel(e):
            if sb.winfo_ismapped():
                step = -1 if (getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0) else 1
                cv.yview_scroll(step * 2, "units")
        holder.bind("<Enter>", lambda e: (self.root.bind_all("<MouseWheel>", wheel),
                                          self.root.bind_all("<Button-4>", wheel),
                                          self.root.bind_all("<Button-5>", wheel)))
        holder.bind("<Leave>", lambda e: (self.root.unbind_all("<MouseWheel>"),
                                          self.root.unbind_all("<Button-4>"),
                                          self.root.unbind_all("<Button-5>")))
        return outer

    def _fv(self, card, idx, default):
        k = (card, idx)
        if k not in self.field_vars:
            self.field_vars[k] = tk.StringVar(value=default)
        return self.field_vars[k]

    def _card(self, tab, key, opcode, fields=(), buttons=(), danger=False, span=1):
        row, col = divmod(tab._next, 2)
        if span == 2 and col == 1:
            row, col = row + 1, 0
        tab._next = row * 2 + col + span
        if self.rtl and span == 1:
            col = 1 - col
        S, E = self.S, self.E
        title, desc = self.card(key)
        border = tk.Frame(tab, bg=C["danger_border"] if danger else C["border"], padx=1, pady=1)
        border.grid(row=row, column=col, columnspan=span, sticky="nsew", padx=6, pady=6)
        f = ttk.Frame(border, style="Card.TFrame", padding=(14, 10))
        f.pack(fill="both", expand=True)
        f.columnconfigure(0, weight=1)
        head = ttk.Frame(f, style="Card.TFrame")
        head.grid(row=0, column=0, sticky="ew")
        ttk.Label(head, text=title, style="CardTitle.TLabel").pack(side=S)
        if opcode is not None:
            ttk.Label(head, text=("0x%02X" % opcode) if isinstance(opcode, int) else opcode,
                      style="DangerOp.Badge.TLabel" if danger else "Badge.TLabel").pack(side=E)
        if danger:
            ttk.Label(head, text=self.t("caution"), style="Danger.Badge.TLabel").pack(
                side=E, padx=(6, 0) if self.rtl else (0, 6))
        dl = ttk.Label(f, text=desc, style="CardDesc.TLabel", wraplength=420,
                       justify="right" if self.rtl else "left")
        dl.grid(row=1, column=0, sticky=self.A, pady=(2, 8))
        f.bind("<Configure>", lambda e, dl=dl: dl.configure(wraplength=max(200, e.width - 40)))
        line = ttk.Frame(f, style="Card.TFrame")
        line.grid(row=2, column=0, sticky="ew")
        vars_ = []
        for i, fd in enumerate(fields):
            label, default = fd[0], fd[1]
            width = fd[2] if len(fd) > 2 else 8
            choices = fd[3] if len(fd) > 3 else None
            box = ttk.Frame(line, style="Card.TFrame")
            box.pack(side=S, padx=(10, 0) if self.rtl else (0, 10))
            ttk.Label(box, text=self.t(label), style="CardField.TLabel").pack(anchor=self.A)
            v = self._fv(key, i, default)
            if choices:
                w = ttk.Combobox(box, textvariable=v, values=choices, width=width, state="readonly",
                                 font=(self.f_mono, 10))
            else:
                w = ttk.Entry(box, textvariable=v, width=width, font=(self.f_mono, 10))
            w.pack(anchor=self.A)
            vars_.append(v)
        for text, cmd, style in reversed(list(buttons)):
            b = ttk.Button(line, text=self.t(text), command=cmd,
                           style=style or ("Danger.TButton" if danger else "Accent.TButton"))
            b.pack(side=E, anchor="s", padx=(0, 6) if self.rtl else (6, 0))
            self.cmd_buttons.append(b)
        return vars_

    def _tab_position(self):
        t = self._tab("tab_pos")
        self._card(t, "readpos", 0x42, buttons=[("b_read", self.do_read_pos, None)])
        self.v_setpos = self._card(t, "setpos", 0x43, fields=[("f_value", "0", 10), ("f_unit", "deg", 5, ["deg", "raw"])],
                                   buttons=[("b_set", self.do_set_pos, None)], danger=True)
        self.v_setsync = self._card(t, "setsync", 0x6A,
                                    fields=[("f_value", "0", 10), ("f_unit", "deg", 5, ["deg", "raw"])],
                                    buttons=[("b_set", self.do_set_pos_sync, None)], danger=True)
        self._card(t, "syncoff", 0x6C, buttons=[("b_read", self.do_sync_offset, None)])
        self.v_analog = self._card(t, "analog", 0x44, fields=[("f_channel", "48", 8)],
                                   buttons=[("b_read", self.do_analog, None)])
        self._card(t, "temp", 0x44, buttons=[("b_read", self.do_temp, None)])

    def _tab_counter(self):
        t = self._tab("tab_cnt")
        self._card(t, "counter", 0x46, buttons=[("b_read", self.do_counter, None)])
        self._card(t, "inc", 0x47, buttons=[("b_inc", self.do_inc_counter, None)])
        self._card(t, "clr", 0x49, buttons=[("b_reset", self.do_clr_counter, None)], danger=True)

    def _tab_data(self):
        t = self._tab("tab_data")
        yn = lambda: [self.raw_t("yes"), self.raw_t("no")]
        self.v_read = self._card(t, "rdata", 0x4A,
                                 fields=[("f_field", "0", 5), ("f_offset", "0", 5), ("f_length", "16", 5),
                                         ("f_access", "55", 5)],
                                 buttons=[("b_read", self.do_read_data, None)])
        self.v_save = self._card(t, "sdata", 0x4B,
                                 fields=[("f_field", "0", 5), ("f_offset", "0", 5), ("f_data", "01 02 03 04", 16),
                                         ("f_access", "55", 5)],
                                 buttons=[("b_store", self.do_save_data, None)], danger=True)
        self.v_dstat = self._card(t, "dstat", 0x4C, fields=[("f_field", "0", 6)],
                                  buttons=[("b_read", self.do_data_status, None)])
        self._card(t, "mem", 0x4E, buttons=[("b_read", self.do_free_mem, None)])
        self.v_create = self._card(t, "create", 0x4D,
                                   fields=[("f_field", "1", 5),
                                           ("f_size", "32", 4, ["16", "32", "48", "64", "80", "96", "112", "128"]),
                                           ("f_codeidx", "0", 3, ["0", "1", "2", "3"]),
                                           ("f_codeon", self.raw_t("yes"), 5, yn()),
                                           ("f_write", self.raw_t("yes"), 5, yn()),
                                           ("f_access", "55", 5)],
                                   buttons=[("b_create", self.do_create_field, None)], danger=True, span=2)
        self.v_delete = self._card(t, "delete", 0x4D, fields=[("f_field", "1", 5), ("f_access", "55", 5)],
                                   buttons=[("b_delete", self.do_delete_field, None)], danger=True)
        self.v_key = self._card(t, "key", 0x4F, fields=[("f_codeno", "0", 3, ["0", "1", "2", "3"]),
                                                       ("f_old", "55", 5), ("f_new", "55", 5)],
                                buttons=[("b_change", self.do_change_key, None)], danger=True)

    def _tab_info(self):
        t = self._tab("tab_info")
        self._card(t, "status", 0x50, buttons=[("b_read", self.do_status, None),
                                               ("b_stack", self.do_status_stack, "TButton")])
        self._card(t, "type", 0x52, buttons=[("b_read", self.do_type_label, None)])
        self._card(t, "ext", "4Ah FF", buttons=[("b_read", self.do_ext_label, None)])
        self._card(t, "serial", 0x56, buttons=[("b_read", self.do_serial_ver, None)])
        self._card(t, "all", "ALL", buttons=[("b_run", self.do_read_all, None)])

    def _tab_config(self):
        t = self._tab("tab_cfg")
        self._card(t, "reset", 0x53, buttons=[("b_reset", self.do_reset, None)], danger=True)
        self.v_newaddr = self._card(t, "addr", 0x55, fields=[("f_newaddr", "40", 6)],
                                    buttons=[("b_apply", self.do_set_addr, None)], danger=True)
        self.v_uart = self._card(t, "uart", "BUILD",
                                 fields=[("f_baud", "9600", 6, ["600", "1200", "2400", "4800", "9600", "19200", "38400"]),
                                         ("f_parity", "Even", 5, ["Even", "Odd", "None"]),
                                         ("f_timeout", "5x", 3, ["2x", "5x"]),
                                         ("f_mode", "Standard", 8, ["Standard", "Bus"])],
                                 buttons=[("b_build", self.do_build_uart, "TButton")], span=2)
        self.v_cfg = self._card(t, "cfg", 0x57, fields=[("f_settings", "E4", 6), ("f_code0", "55", 5)],
                                buttons=[("b_write", self.do_config_serial, None)], danger=True)
        self.v_tmp = self._card(t, "tmp", 0x67, fields=[("f_settings", "E4", 6)],
                                buttons=[("b_apply", self.do_temp_serial, None)], danger=True)
        self.v_adj = self._card(t, "adj", 0x6B, fields=[("f_option", "00", 6)],
                                buttons=[("b_run", self.do_sensor_adjust, None)], danger=True)

    def _tab_raw(self):
        t = self._tab("tab_raw")
        self.v_raw = self._card(t, "raw", "RAW", fields=[("f_frame", "40 42", 30), ("f_readbytes", "0", 5)],
                                buttons=[("b_send", self.do_raw, None)], span=2)
        box = ttk.Frame(t, style="Card.TFrame")
        box.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6)
        ttk.Checkbutton(box, text=self.t("raw_crc"), variable=self.v_raw_crc,
                        style="Card.TCheckbutton").pack(side=self.S)
        self.lbl_crc = ttk.Label(box, text="", style="CardField.TLabel", font=(self.f_mono, 10))
        self.lbl_crc.pack(side=self.S, padx=16)
        self._crc_traces = getattr(self, "_crc_traces", None)
        if not self._crc_traces:
            self.v_raw[0].trace_add("write", lambda *a: self._update_crc_preview())
            self.v_raw_crc.trace_add("write", lambda *a: self._update_crc_preview())
            self._crc_traces = True
        self._update_crc_preview()
        ttk.Label(t, text=self.t("quick"), style="CardField.TLabel").grid(row=2, column=0, columnspan=2,
                                                                          sticky=self.A, padx=6, pady=(16, 4))
        q = ttk.Frame(t, style="Card.TFrame")
        q.grid(row=3, column=0, columnspan=2, sticky=self.A, padx=6)
        for name, fr in [("q_pos", "40 42"), ("q_status", "40 50"), ("q_type", "40 52"),
                         ("q_ver", "40 56"), ("q_temp", "40 44 48"), ("q_cnt", "40 46")]:
            ttk.Button(q, text=self.t(name), style="Small.TButton",
                       command=lambda fr=fr: self.v_raw[0].set(fr)).pack(side=self.S, padx=(0, 6))

    def _update_crc_preview(self):
        try:
            if not self.lbl_crc.winfo_exists():
                return
        except Exception:
            return
        try:
            b = parse_hex_bytes(self.v_raw[0].get())
            if self.v_raw_crc.get():
                b = b + bytes([HiperfaceEncoder.crc(b)])
            self.lbl_crc.configure(text="TX \u2192 " + hex_spaced(b), foreground=C["tx"])
        except Exception:
            self.lbl_crc.configure(text=self.t("invalid_hex"), foreground=C["err"])

    # ------------------------------------------------------------ log
    def _build_log(self, parent):
        head = ttk.Frame(parent)
        head.pack(fill="x", pady=(10, 6))
        ttk.Label(head, text=self.t("log_head"), style="Section.TLabel").pack(side=self.S)
        for key, cmd in [("save", self.save_log), ("copy", self.copy_log), ("clear", self.clear_log)]:
            ttk.Button(head, text=self.t(key), style="Small.TButton", command=cmd).pack(
                side=self.E, padx=(0, 6) if self.rtl else (6, 0))
        ttk.Checkbutton(head, text=self.t("autoscroll"), variable=self.v_autoscroll,
                        style="Bg.TCheckbutton").pack(side=self.E, padx=(6, 10) if self.rtl else (10, 6))
        ttk.Checkbutton(head, text=self.t("show_txrx"), variable=self.v_show_txrx,
                        style="Bg.TCheckbutton").pack(side=self.E, padx=(0, 10) if self.rtl else (10, 0))
        wrap = tk.Frame(parent, bg=C["border"], padx=1, pady=1)
        wrap.pack(fill="both", expand=True)
        self.txt = tk.Text(wrap, bg=C["log_bg"], fg=C["text"], insertbackground=C["text"], relief="flat",
                           font=(self.f_mono, 10), wrap="word", padx=12, pady=8, borderwidth=0,
                           selectbackground=C["accent_dim"], selectforeground=C["text"], height=10,
                           spacing1=1, spacing3=1)
        sc = ttk.Scrollbar(wrap, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        self.txt.pack(side="left", fill="both", expand=True)
        for tag, color in [("time", "faint"), ("tx", "tx"), ("rx", "rx"), ("ok", "text"), ("okbadge", "ok"),
                           ("err", "err"), ("warn", "warn"), ("info", "muted"), ("cmd", "link")]:
            self.txt.tag_configure(tag, foreground=C[color])
        if self.rtl:
            for tag in ("ok", "err", "warn", "info", "cmd"):
                self.txt.tag_configure(tag, font=(self.f_ui, 10))
        self.txt.configure(state="disabled")

    BADGES = {"tx": "TX ", "rx": "RX ", "ok": " \u2713 ", "err": " \u2717 ", "warn": " ! ",
              "info": " \u00b7 ", "cmd": " \u25b8 "}

    def _insert_log(self, ts, kind, msg):
        self.txt.insert("end", ts + "  ", "time")
        self.txt.insert("end", self.BADGES.get(kind, "   ") + " ", "okbadge" if kind == "ok" else kind)
        self.txt.insert("end", msg + "\n", kind)

    def log(self, kind, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_entries.append((ts, kind, msg))
        if len(self.log_entries) > 5000:
            del self.log_entries[:1000]
        self.txt.configure(state="normal")
        self._insert_log(ts, kind, msg)
        lines = int(self.txt.index("end-1c").split(".")[0])
        if lines > 5000:
            self.txt.delete("1.0", "%d.0" % (lines - 4000))
        self.txt.configure(state="disabled")
        if self.v_autoscroll.get():
            self.txt.see("end")

    def _render_log(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        for ts, kind, msg in self.log_entries[-3000:]:
            self._insert_log(ts, kind, msg)
        self.txt.configure(state="disabled")
        self.txt.see("end")

    def clear_log(self):
        self.log_entries = []
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")

    def _plain_log(self):
        return "\n".join("%s  %s %s" % (ts, self.BADGES.get(k, "   "), m.replace("\u202b", "").replace("\u202c", ""))
                         for ts, k, m in self.log_entries)

    def copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self._plain_log())
        self.set_status(self.t("copied"))

    def save_log(self):
        name = "hiperface_log_%s.txt" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        p = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=name,
                                         filetypes=[("Text", "*.txt"), ("All files", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8-sig") as fh:
                fh.write(self._plain_log())
            self.set_status(self.t("saved", p))

    # ------------------------------------------------------------ misc ui
    def _bind_keys(self):
        self.root.bind("<F1>", lambda e: self.open_help())
        self.root.bind("<F5>", lambda e: self.snapshot())
        self.root.bind("<Control-l>", lambda e: self.clear_log())
        self.root.bind("<Control-s>", lambda e: self.save_log())

    def set_status(self, text):
        self.lbl_status.configure(text=text)

    def _update_counts(self):
        self.lbl_counts.configure(text=self.t("counts", self.tx_count, self.rx_count, self.err_count))

    def _set_connected(self, on):
        st = "!disabled" if on else "disabled"
        for b in self.cmd_buttons:
            b.state([st])
        for w in (self.cb_port, self.cb_baud, self.cb_par, self.e_tmo):
            w.state(["disabled"] if on else ["!disabled"])
        self.btn_refresh.set_enabled(not on)
        if not on:
            for w in (self.cb_port, self.cb_baud, self.cb_par):
                w.state(["readonly"])
        self.btn_connect.configure(text=self.t("disconnect") if on else self.t("connect"),
                                   style="Danger.TButton" if on else "Accent.TButton")
        self.led.itemconfigure(self.led_dot, fill=C["ok"] if on else C["faint"])
        if on and self.ser is not None:
            self.lbl_conn.configure(text=self.t("connected_sub", self.ser.port, self.v_baud.get(),
                                                self.v_parity.get()[0], self.enc.addr))
        else:
            self.lbl_conn.configure(text=self.t("disconnected"))

    def refresh_ports(self, quiet=False):
        items = []
        if serial is not None:
            try:
                for p in serial.tools.list_ports.comports():
                    items.append("%s  \u2014  %s" % (p.device, p.description))
            except Exception:
                pass
        items.append(DEMO_PORT)
        self.cb_port.configure(values=items)
        if self.v_port.get() not in items:
            self.v_port.set(items[0])
        self.set_status(self.t("ports_found", len(items) - 1))

    def show_lang_menu(self, w):
        m = tk.Menu(self.root, tearoff=0, bg=C["card"], fg=C["text"], activebackground=C["accent"],
                    activeforeground=C["on_accent"], bd=0, font=(self.f_ui, 10))
        for code, name in LANGS:
            m.add_radiobutton(label=bidi(name, code), value=code, variable=self.v_lang,
                              command=lambda c=code: self.set_lang(c))
        try:
            m.tk_popup(w.winfo_rootx(), w.winfo_rooty() + w.winfo_height() + 2)
        finally:
            m.grab_release()

    # ------------------------------------------------------------ connection
    def toggle_connection(self):
        if self.enc:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        try:
            addr = parse_int(self.v_addr.get(), True)
            code0 = parse_int(self.v_code0.get(), True)
            tmo = max(20, int(self.v_timeout.get())) / 1000.0
            if not ((0x40 <= addr <= 0x5F or addr == 0xFF) and 0 <= code0 <= 0xFF):
                raise ValueError(self.raw_t("e_range"))
        except Exception as e:
            messagebox.showerror(APP_NAME, self.t("bad_conn", e))
            return
        sel = self.v_port.get()
        try:
            if sel == DEMO_PORT:
                self.ser = SimulatedEncoderSerial(int(self.v_baud.get()), self.v_parity.get()[0])
                self.ser.addr = addr if addr != 0xFF else 0x40
            else:
                if serial is None:
                    raise RuntimeError("pyserial is not installed")
                port = sel.split("  ")[0].strip()
                parity = {"Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD,
                          "None": serial.PARITY_NONE}[self.v_parity.get()]
                self.ser = serial.Serial(port=port, baudrate=int(self.v_baud.get()), bytesize=serial.EIGHTBITS,
                                         parity=parity, stopbits=serial.STOPBITS_ONE, timeout=0.05,
                                         write_timeout=max(0.5, tmo))
            self.enc = HiperfaceEncoder(self.ser, addr, code0, on_frame=self._on_frame,
                                        on_warning=self._on_warning, margin_ms=int(tmo * 1000))
        except Exception as e:
            self.ser = None
            self.enc = None
            self.log("err", self.t("open_fail", sel, e))
            txt = str(e)
            if "PermissionError" in txt or "31" in txt or "not functioning" in txt or "Access is denied" in txt:
                self.log("warn", self.t("port_busy"))
            return
        self._set_connected(True)
        self.log("info", self.t("connected_log", self.ser.port, self.v_baud.get(), self.v_parity.get()[0], addr, code0))
        self._save_settings()

    def disconnect(self):
        self.stop_poll()
        ser = self.ser
        self.enc = None
        self.ser = None
        try:
            if ser is not None:
                ser.close()
        except Exception:
            pass
        self._set_connected(False)
        self.log("info", self.t("closed"))

    def on_close(self):
        self._save_settings()
        self.disconnect()
        self.worker.jobs.put(None)
        self.root.destroy()

    # ------------------------------------------------------------ plumbing
    def _on_frame(self, direction, data):   # worker thread
        self.ui_q.put(("frame", direction, data, None, self.worker.quiet))

    def _on_warning(self, cmd):              # worker thread: response had bit 7 (warning) set
        self.ui_q.put(("warnbit", cmd, None, None, self.worker.quiet))

    def _err_text(self, e):
        code = getattr(e, "code", None)
        if code is not None and self.rtl:
            return "خطای انکودر 0x%02X: %s" % (code, fault_text(code, "fa"))
        return str(e)

    def _drain_ui_queue(self):
        try:
            for _i in range(200):
                kind, a, b, cb, quiet = self.ui_q.get_nowait()
                if kind == "frame":
                    if a == "TX":
                        self.tx_count += 1
                    else:
                        self.rx_count += 1
                    if self.v_show_txrx.get() and (not quiet or self.v_log_poll.get()):
                        self.log("tx" if a == "TX" else "rx", "%s  (%d B)" % (hex_spaced(b), len(b)))
                elif kind == "ok":
                    if cb:
                        try:
                            cb(b)
                        except Exception as e:
                            self.log("err", "%s: %s" % (a, e))
                elif kind == "warnbit":
                    if not self.warn_flag:
                        self.warn_flag = True
                        self.log("warn", self.t("warn_bit", a))
                    self._show_warn_dash()
                elif kind == "err":
                    self.err_count += 1
                    msg = self._err_text(b)
                    if not quiet or self.v_log_poll.get():
                        self.log("err", self.t("failed", a, msg))
                    self.set_status(self.t("last_error", msg))
                    if a == "__poll__":
                        self.poll_busy = False
                self._update_counts()
        except queue.Empty:
            pass
        self.root.after(30, self._drain_ui_queue)

    def run(self, label, fn, on_ok, quiet=False):
        if not self.enc:
            messagebox.showwarning(APP_NAME, self.t("need_conn"))
            return
        if not quiet:
            self.log("cmd", label)
        self.worker.submit(label, fn, on_ok, quiet)

    def label(self, key, op):
        return self.card(key)[0] + "  (" + op + ")"

    def confirm(self, msg):
        return messagebox.askyesno(APP_NAME, msg, icon="warning")

    def _bad_input(self, e):
        messagebox.showerror(APP_NAME, self.t("bad_input", e))

    def _cpr(self):
        try:
            return max(1, int(self.v_cpr.get()))
        except Exception:
            return 32768

    # ------------------------------------------------------------ dashboard state
    def _show_position(self, raw):
        self.dash["pos"] = raw
        cpr = self._cpr()
        ang = (raw % cpr) * 360.0 / cpr
        self.lbl_angle.configure(text="%7.2f\u00b0" % ang)
        self.lbl_raw.configure(text=self.t("raw_lbl", raw, raw))
        self.lbl_turns.configure(text=self.t("turns", raw // cpr))
        self._set_dial(ang)
        return ang

    def _show_status(self, code):
        self.dash["status"] = code
        word = self.raw_t("ok") if code == 0 else self.raw_t("fault")
        self.kv["status"].configure(text=bidi("0x%02X %s" % (code, word), self.lang),
                                    fg=C["ok"] if code == 0 else (C["warn"] if code >= 0x1C else C["err"]))
        return fault_text(code, self.lang)

    def _show_warn_dash(self):
        self.kv["status"].configure(text=bidi(self.raw_t("warn_pending"), self.lang), fg=C["warn"])

    def _show_kv(self, k, text):
        self.dash[k] = text
        self.kv[k].configure(text=text)

    def _restore_dash(self):
        if "pos" in self.dash:
            self._show_position(self.dash["pos"])
        if "status" in self.dash:
            self._show_status(self.dash["status"])
        for k in ("temp", "counter", "serial"):
            if k in self.dash:
                self.kv[k].configure(text=self.dash[k])

    def _value_to_raw(self, value_text, unit):
        if unit == "deg":
            deg = float(value_text)
            cpr = self._cpr()
            return max(0, min(cpr - 1, int(round(deg * cpr / 360.0)))), deg
        raw = parse_int(value_text)
        return raw & 0xFFFFFFFF, raw * 360.0 / self._cpr()

    # ------------------------------------------------------------ polling
    def _update_poll_btn(self):
        if self.polling:
            self.btn_poll.configure(text=self.t("stop"), style="Danger.TButton")
        else:
            self.btn_poll.configure(text=self.t("live"), style="Accent.TButton")

    def toggle_poll(self):
        if self.polling:
            self.stop_poll()
        else:
            self.polling = True
            self._update_poll_btn()
            self.log("info", self.t("live_started"))
            self._poll_tick()

    def stop_poll(self):
        if self.polling:
            self.polling = False
            self._update_poll_btn()
            self.log("info", self.t("live_stopped"))

    def _poll_tick(self):
        if not self.polling or not self.enc:
            return
        if not self.poll_busy:
            self.poll_busy = True
            enc = self.enc

            def done(raw):
                self.poll_busy = False
                self._show_position(raw)
            self.worker.submit("__poll__", enc.read_position, done, quiet=True)
        try:
            iv = max(50, int(self.v_interval.get()))
        except Exception:
            iv = 200
        self.root.after(iv, self._poll_tick)

    # ------------------------------------------------------------ commands
    def snapshot(self):
        if not self.enc:
            return
        enc = self.enc

        def job():
            out = {"pos": enc.read_position(), "status": enc.read_status()}
            try:
                out["temp"] = enc.read_temperature()[0]
            except Exception:
                out["temp"] = None
            return out

        def ok(r):
            ang = self._show_position(r["pos"])
            self._show_status(r["status"])
            if r["temp"] is not None:
                self._show_kv("temp", "%d \u00b0C" % r["temp"])
            self.log("ok", self.t("snap", ang, r["pos"], r["status"],
                                  "%d \u00b0C" % r["temp"] if r["temp"] is not None else "n/a"))
        self.run(self.t("snap_cmd"), job, ok)

    def do_read_pos(self):
        enc = self.enc

        def ok(raw):
            ang = self._show_position(raw)
            self.log("ok", self.t("r_pos", raw, raw, ang, raw // self._cpr()))
        self.run(self.label("readpos", "42h"), lambda: enc.read_position(), ok)

    def do_set_pos(self, sync=False):
        vals = self.v_setsync if sync else self.v_setpos
        try:
            raw, deg = self._value_to_raw(vals[0].get(), vals[1].get())
        except Exception as e:
            return self._bad_input(e)
        code = "6Ah" if sync else "43h"
        if not self.confirm(self.t("cf_setpos", deg, raw, raw, code)):
            return
        enc = self.enc
        if sync:
            def ok(actual):
                if actual is None:
                    self.log("ok", self.t("r_setpos"))
                    return
                self.log("ok", self.t("r_setsync", actual, actual, (actual % self._cpr()) * 360.0 / self._cpr()))
            self.run(self.label("setsync", "6Ah") + " \u2192 %d" % raw, lambda: enc.set_position_sync(raw), ok)
        else:
            self.run(self.label("setpos", "43h") + " \u2192 %d" % raw, lambda: enc.set_position(raw),
                     lambda r: self.log("ok", self.t("r_setpos")))

    def do_set_pos_sync(self):
        self.do_set_pos(sync=True)

    def do_sync_offset(self):
        enc = self.enc
        def ok(d):
            if d:
                self.log("ok", self.t("r_syncoff", d[0], hex_spaced(d)))
            else:
                self.log("ok", self.t("r_nodata"))
        self.run(self.label("syncoff", "6Ch"), lambda: enc.read_sync_offset(), ok)

    def do_analog(self):
        try:
            ch = parse_int(self.v_analog[0].get(), True)
        except Exception as e:
            return self._bad_input(e)
        enc = self.enc
        self.run(self.label("analog", "44h") + " 0x%02X" % ch, lambda: enc.read_analog(ch),
                 lambda v: self.log("ok", self.t("r_analog", ch, v, v)))

    def do_temp(self):
        enc = self.enc

        def ok(r):
            self._show_kv("temp", "%d \u00b0C" % r[0])
            self.log("ok", self.t("r_temp", r[0], r[1]))
        self.run(self.label("temp", "44h"), lambda: enc.read_temperature(), ok)

    def do_counter(self):
        enc = self.enc

        def ok(v):
            self._show_kv("counter", str(v))
            self.log("ok", self.t("r_counter", v))
        self.run(self.label("counter", "46h"), lambda: enc.read_counter(), ok)

    def do_inc_counter(self):
        enc = self.enc

        def job():
            enc.increment_counter()
            return enc.read_counter()

        def ok(v):
            self._show_kv("counter", str(v))
            self.log("ok", self.t("r_inc", v))
        self.run(self.label("inc", "47h"), job, ok)

    def do_clr_counter(self):
        if not self.confirm(self.t("cf_clr")):
            return
        enc = self.enc

        def job():
            enc.clear_counter()
            return enc.read_counter()

        def ok(v):
            self._show_kv("counter", str(v))
            self.log("ok", self.t("r_clr", v))
        self.run(self.label("clr", "49h"), job, ok)

    def _yes(self, v):
        return v.get() == self.raw_t("yes")

    def do_read_data(self):
        try:
            fid = parse_int(self.v_read[0].get(), True)
            off = parse_int(self.v_read[1].get())
            ln = parse_int(self.v_read[2].get())
            ac = parse_int(self.v_read[3].get(), True)
            if not (1 <= ln <= 128):
                raise ValueError(self.raw_t("e_len"))
        except Exception as e:
            return self._bad_input(e)
        enc = self.enc

        def ok(d):
            asc = "".join(chr(c) if 32 <= c < 127 else "." for c in bytearray(d))
            self.log("ok", self.t("r_rdata", fid, off, ln, hex_spaced(d), asc))
        self.run(self.label("rdata", "4Ah") + " 0x%02X @%d [%d]" % (fid, off, ln),
                 lambda: enc.read_data(fid, off, ln, ac), ok)

    def do_save_data(self):
        try:
            fid = parse_int(self.v_save[0].get(), True)
            off = parse_int(self.v_save[1].get())
            data = parse_hex_bytes(self.v_save[2].get())
            ac = parse_int(self.v_save[3].get(), True)
            if not (1 <= len(data) <= 128):
                raise ValueError(self.raw_t("e_data"))
        except Exception as e:
            return self._bad_input(e)
        if not self.confirm(self.t("cf_sdata", len(data), hex_spaced(data), fid, off)):
            return
        enc = self.enc
        self.run(self.label("sdata", "4Bh") + " 0x%02X" % fid, lambda: enc.save_data(fid, off, data, ac),
                 lambda r: self.log("ok", self.t("r_sdata")))

    def _field_text(self, st):
        f = HiperfaceEncoder.decode_field_status(st)
        code = ("Code%d" % f["code_idx"]) + ("" if f["code_enabled"] else " (" + self.raw_t("disabled") + ")")
        return f["size"], code, self.raw_t("writable") if f["writable"] else self.raw_t("readonly"), \
            self.raw_t("exists") if f["exists"] else self.raw_t("notdef")

    def do_data_status(self):
        try:
            fid = parse_int(self.v_dstat[0].get(), True)
        except Exception as e:
            return self._bad_input(e)
        enc = self.enc

        def ok(st):
            size, code, wr, ex = self._field_text(st)
            self.log("ok", self.t("r_dstat", fid, st, size, code, wr, ex))
        self.run(self.label("dstat", "4Ch") + " 0x%02X" % fid, lambda: enc.data_status(fid), ok)

    def do_create_field(self):
        v = self.v_create
        try:
            fid = parse_int(v[0].get(), True)
            size = int(v[1].get())
            idx = int(v[2].get())
            code_on = self._yes(v[3])
            write_on = self._yes(v[4])
            ac = parse_int(v[5].get(), True)
        except Exception as e:
            return self._bad_input(e)
        if not self.confirm(self.t("cf_create", fid, size, idx)):
            return
        enc = self.enc

        def ok(st):
            size_, code, wr, ex = self._field_text(st)
            self.log("ok", self.t("r_create", st, size_, code, wr))
        self.run(self.label("create", "4Dh") + " 0x%02X" % fid,
                 lambda: enc.create_field(fid, size, idx, write_on, code_on, ac), ok)

    def do_delete_field(self):
        try:
            fid = parse_int(self.v_delete[0].get(), True)
            ac = parse_int(self.v_delete[1].get(), True)
        except Exception as e:
            return self._bad_input(e)
        if not self.confirm(self.t("cf_delete", fid)):
            return
        enc = self.enc
        self.run(self.label("delete", "4Dh") + " 0x%02X" % fid, lambda: enc.delete_field(fid, ac),
                 lambda st: self.log("ok", self.t("r_delete", fid, st)))

    def do_free_mem(self):
        enc = self.enc
        self.run(self.label("mem", "4Eh"), lambda: enc.read_memory(),
                 lambda r: self.log("ok", self.t("r_mem", r[0], r[1])))

    def do_change_key(self):
        try:
            num = int(self.v_key[0].get())
            old = parse_int(self.v_key[1].get(), True)
            new = parse_int(self.v_key[2].get(), True)
        except Exception as e:
            return self._bad_input(e)
        if not self.confirm(self.t("cf_key", num, old, new)):
            return
        enc = self.enc

        def ok(r):
            self.log("ok", self.t("r_key", num, new))
            if num == 0:
                self.v_code0.set("%02X" % new)
                enc.code0 = new
                self.log("info", self.t("r_code0_upd", new))
        self.run(self.label("key", "4Fh"), lambda: enc.change_access_key(num, old, new), ok)

    def do_status(self):
        enc = self.enc

        def ok(code):
            desc = self._show_status(code)
            if not enc.warning:
                self.warn_flag = False
            self.log("ok" if code == 0 else ("warn" if code >= 0x1C else "err"), self.t("r_status", code, desc))
        self.run(self.label("status", "50h"), lambda: enc.read_status(), ok)

    def do_status_stack(self):
        enc = self.enc

        def ok(codes):
            self.warn_flag = False
            if not codes:
                self._show_status(0)
                self.log("ok", self.t("r_status", 0, fault_text(0, self.lang)))
                return
            for c in codes:
                self.log("warn" if c >= 0x1C else "err", self.t("r_status", c, fault_text(c, self.lang)))
            self._show_status(codes[0])
            self.log("info", self.t("r_stack", len(codes)))
        self.run(self.label("status", "50h") + " \u00d7n", lambda: enc.read_status_stack(), ok)

    def do_ext_label(self):
        enc = self.enc

        def ok(x):
            if "resolution" not in x:
                self.log("warn", self.t("r_ext_short", hex_spaced(x["raw"])))
                return
            unit = self.raw_t("ext_linear") if x["linear"] else self.raw_t("ext_rotary")
            self.log("ok", self.t("r_ext", x["designation"] or "-", unit, x["resolution"], x["range"],
                                  x["selector"], x["checksum"],
                                  "OK" if x["checksum"] == x["checksum_calc"] else self.raw_t("bad")))
        self.run(self.label("ext", "4Ah FFh"), lambda: enc.read_extended_type_label(), ok)

    def _type_text(self, t):
        ty = self.raw_t("ext_type") if t["type"] == 0xFF else "0x%02X" % t["type"]
        return ty

    def do_type_label(self):
        enc = self.enc

        def ok(t):
            self.log("ok", self.t("r_type", t["uart"], describe_uart(t["uart"], self.lang), self._type_text(t),
                                  t["mem_bytes"], t["option"]))
        self.run(self.label("type", "52h"), lambda: enc.read_type_label(), ok)

    def do_serial_ver(self):
        enc = self.enc

        def ok(r):
            self._show_kv("serial", r[0] or "--")
            self.log("ok", self.t("r_serial", r[0], r[1], r[2]))
        self.run(self.label("serial", "56h"), lambda: enc.read_serial_version(), ok)

    def do_read_all(self):
        enc = self.enc
        names = [("k_status", enc.read_status), ("rep_type", enc.read_type_label),
                 ("rep_serial", enc.read_serial_version), ("rep_mem", enc.read_memory),
                 ("k_counter", enc.read_counter), ("k_temp", enc.read_temperature), ("rep_pos", enc.read_position)]

        def job():
            res = []
            for name, fn in names:
                try:
                    res.append((name, True, fn()))
                except Exception as e:
                    res.append((name, False, e))
            return res

        def ok(res):
            self.log("info", "\u2500" * 18 + " " + self.t("report") + " " + "\u2500" * 18)
            for name, good, v in res:
                title = self.raw_t(name)
                if not good:
                    self.log("err", bidi("%s: %s" % (title, v), self.lang))
                    continue
                if name == "k_status":
                    txt = "0x%02X %s" % (v, self._show_status(v))
                elif name == "rep_type":
                    txt = "UART 0x%02X (%s), %s, %d B, opt 0x%02X" % (
                        v["uart"], describe_uart(v["uart"], self.lang), self._type_text(v), v["mem_bytes"], v["option"])
                elif name == "rep_serial":
                    self._show_kv("serial", v[0] or "--")
                    txt = "%s | %s | %s" % v
                elif name == "rep_mem":
                    txt = self.raw_t("rep_mem_val", v[0], v[1])
                elif name == "k_counter":
                    self._show_kv("counter", str(v))
                    txt = str(v)
                elif name == "k_temp":
                    self._show_kv("temp", "%d \u00b0C" % v[0])
                    txt = "%d \u00b0C" % v[0]
                else:
                    txt = "%d  (%.2f\u00b0)" % (v, self._show_position(v))
                if self.rtl:
                    self.log("ok", bidi("%s: %s" % (title, txt), self.lang))
                else:
                    self.log("ok", "%-15s %s" % (title, txt))
        self.run(self.card("all")[0], job, ok)

    def do_reset(self):
        if not self.confirm(self.t("cf_reset")):
            return
        enc = self.enc
        def ok(target):
            self.warn_flag = False
            self.log("ok", self.t("r_reset"))
            if target is not None:
                self._port_vars_from_uart(target)
                self.log("info", self.t("r_port_switched", describe_uart(target, self.lang)))
        self.run(self.label("reset", "53h"), lambda: enc.reset(), ok)

    def _port_vars_from_uart(self, b):
        try:
            baud, par = uart_to_port(b)
        except Exception:
            return
        self.v_baud.set(str(baud))
        self.v_parity.set({"E": "Even", "O": "Odd", "N": "None"}[par])
        self._set_connected(self.enc is not None)
        self._save_settings()

    def do_set_addr(self):
        try:
            new = parse_int(self.v_newaddr[0].get(), True)
            if not (0x40 <= new <= 0x5F):
                raise ValueError(self.raw_t("e_addr"))
        except Exception as e:
            return self._bad_input(e)
        enc = self.enc
        if not self.confirm(self.t("cf_addr", enc.addr, new)):
            return

        def ok(r):
            self.v_addr.set("%02X" % new)
            self._set_connected(True)
            self.log("ok", self.t("r_addr", new))
        self.run(self.label("addr", "55h") + " \u2192 0x%02X" % new, lambda: enc.allocate_address(new), ok)

    def do_build_uart(self):
        v = self.v_uart
        bmap = {"600": 0, "1200": 1, "2400": 2, "4800": 3, "9600": 4, "19200": 5, "38400": 6}
        b = bmap[v[0].get()]
        b |= {"None": 0, "Even": 2, "Odd": 3}[v[1].get()] << 4
        if v[2].get() == "5x":
            b |= 0x40
        if v[3].get() == "Standard":
            b |= 0x80
        self.v_cfg[0].set("%02X" % b)
        self.v_tmp[0].set("%02X" % b)
        self.log("info", self.t("r_uart", b, describe_uart(b, self.lang)))

    def do_config_serial(self):
        try:
            sb = parse_int(self.v_cfg[0].get(), True)
            ac = parse_int(self.v_cfg[1].get(), True)
            uart_to_port(sb)
        except Exception as e:
            return self._bad_input(e)
        if not self.confirm(self.t("cf_cfg", sb, describe_uart(sb, self.lang))):
            return
        enc = self.enc
        self.run(self.label("cfg", "57h") + " \u2192 0x%02X" % sb, lambda: enc.config_serial(sb, ac),
                 lambda e: self.log("ok", self.t("r_cfg", e)))

    def do_temp_serial(self):
        try:
            sb = parse_int(self.v_tmp[0].get(), True)
            uart_to_port(sb)
        except Exception as e:
            return self._bad_input(e)
        if not self.confirm(self.t("cf_tmp", sb, describe_uart(sb, self.lang))):
            return
        enc = self.enc
        def ok(e):
            self._port_vars_from_uart(sb)
            self.log("ok", self.t("r_tmp", e, describe_uart(sb, self.lang)))
        self.run(self.label("tmp", "67h") + " \u2192 0x%02X" % sb, lambda: enc.temp_config_serial(sb), ok)

    def do_sensor_adjust(self):
        try:
            opt = parse_int(self.v_adj[0].get(), True)
        except Exception as e:
            return self._bad_input(e)
        if not self.confirm(self.t("cf_adj", opt)):
            return
        enc = self.enc
        self.run(self.label("adj", "6Bh") + " 0x%02X" % opt, lambda: enc.sensor_adjustment(opt),
                 lambda r: self.log("ok", self.t("r_adj", hex_spaced(r) or "-")))

    def do_raw(self):
        try:
            payload = parse_hex_bytes(self.v_raw[0].get())
            n = int(self.v_raw[1].get())
            if not payload:
                raise ValueError(self.raw_t("e_empty"))
        except Exception as e:
            return self._bad_input(e)
        enc = self.enc
        add = self.v_raw_crc.get()

        def ok(r):
            if not r:
                self.log("warn", self.t("r_noreply"))
                return
            good = HiperfaceEncoder.crc(r[:-1]) == r[-1] if len(r) > 1 else False
            self.log("ok" if good else "warn", self.t("r_reply", len(r), "OK" if good else self.raw_t("bad")))
        self.run(self.card("raw")[0], lambda: enc.send_raw(payload, add, n), ok)

    # ============================================================ Help window
    def open_pdf(self):
        p = find_pdf(self.pdf_path)
        if p:
            try:
                open_path_or_url(p)
                return
            except Exception:
                pass
        if messagebox.askyesno(APP_NAME, self.t("pdf_missing", PDF_NAME, PDF_FALLBACK_DIR)):
            webbrowser.open(PDF_ONLINE)

    def browse_pdf(self):
        p = filedialog.askopenfilename(title=self.raw_t("browse_pdf"),
                                       filetypes=[("PDF", "*.pdf"), ("All files", "*.*")])
        if p:
            self.pdf_path = p
            self._save_settings()
            self.set_status(self.t("pdf_found", p))
            if self.help_win and self.help_win.winfo_exists():
                self.help_win.destroy()
                self.open_help()

    def _link(self, parent, text, cmd, bg, size=10):
        import tkinter.font as tkfont
        f = tkfont.Font(family=self.f_ui, size=size, underline=True)
        lb = tk.Label(parent, text=text, fg=C["link"], bg=bg, cursor="hand2", font=f)
        lb.bind("<Button-1>", lambda e: cmd())
        lb.bind("<Enter>", lambda e: lb.configure(fg=C["accent_hi"]))
        lb.bind("<Leave>", lambda e: lb.configure(fg=C["link"]))
        lb._font = f
        return lb

    def open_help(self):
        if self.help_win and self.help_win.winfo_exists():
            self.help_win.deiconify()
            self.help_win.lift()
            return
        w = tk.Toplevel(self.root)
        self.help_win = w
        w.title("%s  \u00b7  %s" % (self.raw_t("help_title"), APP_NAME))
        w.configure(bg=C["bg"])
        w.geometry("1040x740")
        w.minsize(820, 520)
        w.bind("<Escape>", lambda e: w.destroy())
        S, E = self.S, self.E

        head = tk.Frame(w, bg=C["panel"], padx=20, pady=14)
        head.pack(fill="x")
        left = tk.Frame(head, bg=C["panel"])
        left.pack(side=S)
        tk.Label(left, text=self.t("help_title"), bg=C["panel"], fg=C["text"],
                 font=(self.f_ui, 18, "bold")).pack(anchor=self.A)
        tk.Label(left, text="HIPERFACE Studio %s" % APP_VERSION, bg=C["panel"], fg=C["muted"],
                 font=(self.f_ui, 9)).pack(anchor=self.A)
        right = tk.Frame(head, bg=C["panel"])
        right.pack(side=E)
        ttk.Button(right, text=self.t("open_pdf"), style="Accent.TButton", command=self.open_pdf).pack(
            side=S, padx=(0, 0))
        self._link(right, self.t("open_online"), lambda: webbrowser.open(PDF_ONLINE), C["panel"]).pack(
            side=S, padx=14)
        pdf = find_pdf(self.pdf_path)
        info = tk.Frame(w, bg=C["bg"])
        info.pack(fill="x", padx=22, pady=(8, 0))
        if pdf:
            tk.Label(info, text=self.t("pdf_local"), bg=C["bg"], fg=C["ok"], font=(self.f_ui, 9)).pack(side=S)
            self._link(info, pdf, self.open_pdf, C["bg"], size=9).pack(side=S, padx=6)
        else:
            tk.Label(info, text=self.t("pdf_notfound"), bg=C["bg"], fg=C["warn"], font=(self.f_ui, 9)).pack(side=S)
        self._link(info, self.t("browse_pdf"), self.browse_pdf, C["bg"], size=9).pack(side=E)

        body = tk.Frame(w, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=12)
        side = tk.Frame(body, bg=C["panel"], width=230, padx=14, pady=12)
        side.pack(side=S, fill="y")
        side.pack_propagate(False)
        tk.Label(side, text=self.t("contents"), bg=C["panel"], fg=C["muted"],
                 font=(self.f_ui, 9, "bold")).pack(anchor=self.A, pady=(0, 6))

        wrap = tk.Frame(body, bg=C["border"], padx=1, pady=1)
        wrap.pack(side=S, fill="both", expand=True, padx=(0, 12) if self.rtl else (12, 0))
        txt = tk.Text(wrap, bg=C["card"], fg=C["text"], relief="flat", wrap="word", padx=26, pady=18,
                      font=(self.f_ui, 11), borderwidth=0, cursor="arrow", spacing1=2, spacing3=4,
                      selectbackground=C["accent_dim"], selectforeground=C["text"])
        sc = ttk.Scrollbar(wrap, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        j = "right" if self.rtl else "left"
        F = self.f_ui
        txt.tag_configure("h1", font=(F, 15, "bold"), spacing1=20, spacing3=8, foreground=C["text"], justify=j)
        txt.tag_configure("h2", font=(F, 11, "bold"), spacing1=12, spacing3=4, foreground=C["accent"], justify=j)
        txt.tag_configure("p", font=(F, 11), spacing3=8, foreground=C["text"], justify=j)
        if self.rtl:
            txt.tag_configure("li", font=(F, 11), rmargin=6, spacing3=4, foreground=C["text"], justify=j)
            txt.tag_configure("desc", font=(F, 10), rmargin=0, spacing3=8, foreground=C["muted"], justify=j)
        else:
            txt.tag_configure("li", font=(F, 11), lmargin1=6, lmargin2=30, spacing3=4, foreground=C["text"])
            txt.tag_configure("desc", font=(F, 10), lmargin1=64, lmargin2=64, spacing3=8, foreground=C["muted"])
        txt.tag_configure("code", font=(self.f_mono, 10), background=C["card_hi"], lmargin1=10, lmargin2=10,
                          spacing3=0, foreground=C["text"])
        txt.tag_configure("op", font=(self.f_mono, 10, "bold"), foreground=C["accent"])
        txt.tag_configure("optitle", font=(F, 11, "bold"), foreground=C["text"])
        txt.tag_configure("caution", font=(F, 9, "bold"), foreground=C["err"])
        txt.tag_configure("fcode", font=(self.f_mono, 10, "bold"), foreground=C["warn"])
        txt.tag_configure("ftext", font=(F, 10), foreground=C["text"])
        txt.tag_configure("line", justify=j, spacing3=2)
        txt.tag_configure("plabel", font=(F, 10, "bold"), foreground=C["muted"], justify=j)
        self._hl = 0

        def put_link(label, text, action):
            self._hl += 1
            tag = "hl%d" % self._hl
            txt.tag_configure(tag, foreground=C["link"], underline=True, font=(F, 10))
            txt.tag_bind(tag, "<Button-1>", lambda e: action())
            txt.tag_bind(tag, "<Enter>", lambda e: txt.configure(cursor="hand2"))
            txt.tag_bind(tag, "<Leave>", lambda e: txt.configure(cursor="arrow"))
            put_line([(label + "  ", "plabel"), (text, tag)])

        def put_line(parts):   # parts: [(text, tag)], logical order; reversed for RTL rendering
            seq = list(reversed(parts)) if self.rtl else parts
            for text, tag in seq:
                txt.insert("end", text, (tag, "line"))
            txt.insert("end", "\n", "line")

        sec = 0
        for kind, text in HELP.blocks(self.lang):
            if kind == "h1":
                mark = "sec%d" % sec
                sec += 1
                txt.mark_set(mark, "end-1c")
                txt.mark_gravity(mark, "left")
                txt.insert("end", bidi(text, self.lang) + "\n", "h1")
                lk = self._link(side, bidi(text, self.lang), lambda m=mark: txt.yview(m), C["panel"], size=10)
                lk.configure(anchor=self.A, justify="right" if self.rtl else "left")
                lk.pack(anchor=self.A, pady=2, fill="x")
            elif kind == "p":
                txt.insert("end", bidi(text, self.lang) + "\n", "p")
            elif kind == "li":
                bullet = text if text[:1].isdigit() else "\u2022  " + text
                txt.insert("end", bidi(bullet, self.lang) + "\n", "li")
            elif kind == "code":
                txt.insert("end", text + "\n", "code")
                txt.insert("end", "\n", "p")
            elif kind == "cmd":
                for tabkey, items in HELP.OPCODES:
                    txt.insert("end", self.t(tabkey) + "\n", "h2")
                    for ck, op in items:
                        title, desc = self.card(ck)
                        parts = [(op.ljust(6), "op"), (title, "optitle")]
                        if ck in HELP.CAUTION:
                            parts.append(("   " + self.t("caution"), "caution"))
                        put_line(parts)
                        txt.insert("end", desc + "\n", "desc")
            elif kind == "pdf":
                if pdf:
                    put_link(self.t("pdf_local"), pdf, self.open_pdf)
                else:
                    put_line([(self.t("pdf_notfound"), "caution")])
                put_link(self.t("pdf_expected"), os.path.join(PDF_FALLBACK_DIR, PDF_NAME), self.open_pdf)
                put_link(self.t("open_online"), PDF_ONLINE, lambda: webbrowser.open(PDF_ONLINE))
                put_link(self.t("browse_pdf"), "\u2026", self.browse_pdf)
                txt.insert("end", "\n", "p")
            elif kind == "links":
                put_link(self.t("a_repo"), REPO_URL, lambda: webbrowser.open(REPO_URL))
                put_link(self.t("a_issues"), ISSUES_URL, lambda: webbrowser.open(ISSUES_URL))
                put_link(self.t("a_email"), AUTHOR_EMAIL, lambda: webbrowser.open("mailto:" + AUTHOR_EMAIL))
                put_link(self.t("a_font_src"), VAZIR_URL, lambda: webbrowser.open(VAZIR_URL))
                txt.insert("end", "\n", "p")
            elif kind == "fault":
                for code in sorted(HiperfaceEncoder.FAULT_CODES):
                    put_line([("0x%02X    " % code, "fcode"), (bidi(fault_text(code, self.lang), self.lang), "ftext")])
                txt.insert("end", "\n", "p")
        txt.configure(state="disabled")

        def wheel(e):
            step = -1 if (getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0) else 1
            txt.yview_scroll(step * 3, "units")
        txt.bind("<Button-4>", wheel)
        txt.bind("<Button-5>", wheel)
        foot = tk.Frame(w, bg=C["bg"])
        foot.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(foot, text=self.t("b_close"), command=w.destroy).pack(side=E)
        self.help_txt = txt

    # ============================================================ About window
    def _logo(self, parent, bg, size=72):
        cv = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0)
        s = size
        m = s / 2.0
        r = s * 0.36
        cv.create_oval(m - r, m - r, m + r, m + r, outline=C["border"], width=4)
        cv.create_arc(m - r, m - r, m + r, m + r, start=90, extent=-130, style="arc", outline=C["accent"], width=6)
        a = math.radians(40)
        cv.create_line(m, m, m + r * 0.78 * math.cos(a), m + r * 0.78 * math.sin(a), fill=C["accent_hi"], width=4,
                       capstyle="round")
        cv.create_oval(m - 5, m - 5, m + 5, m + 5, fill=C["accent"], outline="")
        return cv

    def _about_info(self):
        sv = getattr(serial, "__version__", "n/a") if serial else "n/a"
        return [
            ("a_version", APP_VERSION, None),
            ("a_author", (AUTHOR_FA + "  (" + AUTHOR + ")") if self.rtl else AUTHOR, None),
            ("a_email", AUTHOR_EMAIL, lambda: webbrowser.open("mailto:" + AUTHOR_EMAIL)),
            ("a_repo", REPO_URL, lambda: webbrowser.open(REPO_URL)),
            ("a_issues", ISSUES_URL.replace("https://", ""), lambda: webbrowser.open(ISSUES_URL)),
            ("a_protocol", self.raw_t("a_protocol_val"), self.open_pdf),
            ("a_pdf", find_pdf(self.pdf_path) or self.raw_t("a_pdf_online"), self.open_pdf),
            ("a_font", (self.f_fa if self.fa_is_vazir else self.raw_t("a_font_missing", self.f_fa)),
             None if self.fa_is_vazir else (lambda: webbrowser.open(VAZIR_URL))),
            ("a_built", "Python %s \u00b7 Tk %s \u00b7 pyserial %s" % (platform.python_version(),
                                                                       tk.TkVersion, sv), None),
            ("a_platform", "%s %s (%s)" % (platform.system(), platform.release(), platform.machine()), None),
        ]

    def open_about(self):
        if self.about_win and self.about_win.winfo_exists():
            self.about_win.deiconify()
            self.about_win.lift()
            return
        w = tk.Toplevel(self.root)
        self.about_win = w
        w.title("%s  \u00b7  %s" % (self.raw_t("about_title"), APP_NAME))
        w.configure(bg=C["card"])
        w.resizable(False, False)
        w.bind("<Escape>", lambda e: w.destroy())
        S, E = self.S, self.E
        bg = C["card"]
        top = tk.Frame(w, bg=C["panel"], padx=28, pady=22)
        top.pack(fill="x")
        self._logo(top, C["panel"]).pack(side=S)
        nm = tk.Frame(top, bg=C["panel"])
        nm.pack(side=S, padx=16)
        tk.Label(nm, text="HIPERFACE Studio", bg=C["panel"], fg=C["text"], font=(self.f_ui, 20, "bold")).pack(
            anchor=self.A)
        tk.Label(nm, text=bidi("%s %s" % (self.raw_t("a_version"), APP_VERSION), self.lang), bg=C["panel"],
                 fg=C["muted"], font=(self.f_ui, 10)).pack(anchor=self.A)

        mid = tk.Frame(w, bg=bg, padx=28, pady=18)
        mid.pack(fill="both")
        tk.Label(mid, text=self.t("about_desc"), bg=bg, fg=C["text"], font=(self.f_ui, 10), wraplength=520,
                 justify="right" if self.rtl else "left").pack(anchor=self.A, pady=(0, 14))
        grid = tk.Frame(mid, bg=bg)
        grid.pack(fill="x")
        lc, vc = (1, 0) if self.rtl else (0, 1)
        grid.columnconfigure(vc, weight=1)
        for i, (key, val, action) in enumerate(self._about_info()):
            tk.Label(grid, text=self.t(key), bg=bg, fg=C["muted"], font=(self.f_ui, 10)).grid(
                row=i, column=lc, sticky=self.A, pady=3, padx=(16, 0) if self.rtl else (0, 16))
            if action:
                v = self._link(grid, bidi(val, self.lang), action, bg)
                if key in ("a_pdf",):
                    v.configure(wraplength=430, justify="right" if self.rtl else "left")
            else:
                v = tk.Label(grid, text=bidi(val, self.lang), bg=bg, fg=C["text"], font=(self.f_ui, 10))
            v.grid(row=i, column=vc, sticky=self.A, pady=3)
        tk.Label(mid, text=self.t("a_tm"), bg=bg, fg=C["faint"], font=(self.f_ui, 9), wraplength=520,
                 justify="right" if self.rtl else "left").pack(anchor=self.A, pady=(16, 0))
        foot = tk.Frame(w, bg=bg, padx=28, pady=16)
        foot.pack(fill="x")
        ttk.Button(foot, text=self.t("b_close"), style="Accent.TButton", command=w.destroy).pack(side=E)

        def copy_info():
            lines = ["HIPERFACE Studio %s" % APP_VERSION] + ["%s: %s" % (tr("en", k), v)
                                                            for k, v, _a in self._about_info()]
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(lines))
            self.set_status(self.t("info_copied"))
        ttk.Button(foot, text=self.t("b_copy_info"), command=copy_info).pack(side=E, padx=8)
        w.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - w.winfo_reqwidth()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - w.winfo_reqheight()) // 3
        w.geometry("+%d+%d" % (max(0, x), max(0, y)))
        w.transient(self.root)


def main():
    enable_dpi_awareness()
    load_private_fonts()          # Vazirmatn / Vazir from ./fonts, before Tk enumerates font families
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
