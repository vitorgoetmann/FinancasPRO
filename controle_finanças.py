"""
FinançasPro - controle_financas.py (versão 2.1)
Correções e melhorias:
 - Reintroduzido botão "Excluir Selecionada" para Receitas e Despesas
 - Correção do bug de data (garante que a data escolhida no DateEntry seja preservada corretamente)
 - Modo Escuro aprimorado (paleta mais legível)
 - Estética levemente melhorada (contrastes, hover, botões)
 - Mantém: editar, replicar p/ próx. mês, repetir mensalmente, export/backup, olho na senha
 - Preferência de tema salva em config.json (persistência)
Compatibilidade: substitui seu controle_financas.py atual (mantém formato CSV legacy)
Requisitos:
    pip install tkcalendar matplotlib pandas
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

def fmt_val(valor):
    """Formata um valor monetário."""
    return f"R$ {valor:.2f}"
import os
import locale
import json
from calendar import monthrange
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# tentar configurar locale pt_BR para nomes de mês no sistema
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except Exception:
    try:
        locale.setlocale(locale.LC_TIME, "Portuguese_Brazil.1252")
    except Exception:
        pass

# ---------- Config & paths ----------
APP_DATA_DIR = Path.cwd()
CONFIG_FILE = APP_DATA_DIR / "config.json"
USERS_DIR = APP_DATA_DIR / "usuarios"
CRED_EXT = ".cred.csv"
RECEITAS_EXT = "_receitas.csv"
DESPESAS_EXT = "_despesas.csv"

if not USERS_DIR.exists():
    os.makedirs(USERS_DIR)

# ---------- Paletas (modernas e vibrantes) ----------
PALETTE_LIGHT = {
    "bg": "#f5f7fa",
    "accent": "#6366f1",       # índigo vibrante
    "accent_text": "#ffffff",
    "primary": "#3b82f6",      # azul moderno
    "success": "#10b981",      # verde esmeralda
    "danger": "#ef4444",       # vermelho vibrante
    "card": "#ffffff",
    "muted": "#6b7280",
    "pill": "#e0e7ff",
    "text_on_card": "#1f2937",
    "btn_hover": "#dbeafe",
    "shadow": "#00000015",
    "border": "#e5e7eb"
}

PALETTE_DARK = {
    "bg": "#0f172a",           # azul escuro profundo
    "accent": "#7c3aed",       # roxo vibrante
    "accent_text": "#f8fafc",
    "primary": "#3b82f6",      # azul brilhante
    "success": "#10b981",      # verde esmeralda
    "danger": "#f43f5e",       # rosa-vermelho
    "card": "#1e293b",         # cartão slate
    "muted": "#94a3b8",
    "pill": "#334155",
    "text_on_card": "#f1f5f9",
    "btn_hover": "#475569",
    "shadow": "#00000040",
    "border": "#334155"
}

# default palette (will be set later)
PALETTE = PALETTE_LIGHT.copy()

# ---------- categorias ----------
CATEGORIAS_DESPESAS = ["Alimentação", "Transporte", "Moradia", "Educação", "Lazer", "Saúde", "Fatura", "Outros"]
CATEGORIAS_RECEITAS = ["Salário", "Investimentos", "Freelance", "Outros"]

# Cores modernas para o gráfico de pizza
COLORS_CHART = {
    "Alimentação": "#f59e0b",   # âmbar
    "Transporte": "#3b82f6",    # azul
    "Moradia": "#8b5cf6",       # roxo
    "Educação": "#06b6d4",      # ciano
    "Lazer": "#ec4899",         # rosa
    "Saúde": "#10b981",         # verde
    "Fatura": "#f97316",        # laranja
    "Outros": "#6b7280"         # cinza
}

# ---------- Helpers ----------
def fmt_val(v):
    try:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"R$ {v}"

def hover_effect(widget, color_on=None, color_off=None):
    if color_off is None:
        try:
            color_off = widget["bg"]
        except Exception:
            color_off = PALETTE.get("primary", "#1976d2")
    if color_on is None:
        color_on = PALETTE.get("btn_hover", "#d6eaff")
    def on(e):
        try:
            widget.configure(bg=color_on)
        except Exception:
            pass
    def off(e):
        try:
            widget.configure(bg=color_off)
        except Exception:
            pass
    try:
        widget.bind("<Enter>", on)
        widget.bind("<Leave>", off)
    except Exception:
        pass

def load_config():
    cfg = {"theme": "light"}
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
    except Exception:
        pass
    return cfg

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except Exception:
        pass

def add_months_to_date_str(date_s, months=1):
    """date_s in dd/mm/YYYY -> returns dd/mm/YYYY advanced by months (keeps day or closest valid)"""
    try:
        d = datetime.strptime(date_s, "%d/%m/%Y")
        month = d.month - 1 + months
        year = d.year + month // 12
        month = month % 12 + 1
        day = min(d.day, monthrange(year, month)[1])
        nd = d.replace(year=year, month=month, day=day)
        return nd.strftime("%d/%m/%Y")
    except Exception:
        return date_s

def normalize_value_input(raw_input):
    normalized = raw_input.replace(".", "").replace(",", ".").strip()
    return float(normalized)

def find_matching_index(lst, valor, desc, categoria, data_s):
    """Find index in list of tuples (valor, desc, categoria, data) matching fields closely"""
    for i, t in enumerate(lst):
        try:
            if abs(t[0] - valor) < 1e-6 and t[1] == desc and t[2] == categoria and t[3] == data_s:
                return i
        except Exception:
            continue
    return None

# ---------- App ----------
class FinancasProApp:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.palette_name = self.cfg.get("theme", "light")
        self.set_palette(self.palette_name)

        self.root.title("FinançasPro")
        self.root.configure(bg=PALETTE["bg"])
        self.root.geometry("1240x760")
        self.root.minsize(1024, 680)

        self.usuario = None
        self.receitas = []
        self.despesas = []
        self.ultimo_saldo_animado = None

        self.tela_login()

    def set_palette(self, name):
        global PALETTE
        if name == "dark":
            PALETTE = PALETTE_DARK.copy()
        else:
            PALETTE = PALETTE_LIGHT.copy()
        self.cfg["theme"] = name
        save_config(self.cfg)

    # ---------------- Login / Registro ----------------
    def tela_login(self):
        self.clear_root()
        frm = tk.Frame(self.root, bg=PALETTE["bg"])
        frm.pack(expand=True)

        title = tk.Label(frm, text="💰 FinançasPro", font=("Segoe UI Black", 32), bg=PALETTE["bg"], fg=PALETTE["accent"])
        title.pack(pady=(0,8))
        subtitle = tk.Label(frm, text="Controle suas finanças com inteligência", font=("Segoe UI", 11), bg=PALETTE["bg"], fg=PALETTE["muted"])
        subtitle.pack(pady=(0,20))

        card = tk.Frame(frm, bg=PALETTE["card"], bd=0, relief="flat", highlightbackground=PALETTE["border"], highlightthickness=1)
        card.pack(padx=18, pady=10)

        tk.Label(card, text="Usuário", font=("Segoe UI", 11), bg=PALETTE["card"], fg=PALETTE.get("text_on_card", "#000")).grid(row=0, column=0, sticky="w", padx=12, pady=(12,4))
        entry_user = tk.Entry(card, font=("Segoe UI", 12))
        entry_user.grid(row=1, column=0, padx=12, pady=(0,10), sticky="we")

        tk.Label(card, text="Senha", font=("Segoe UI", 11), bg=PALETTE["card"], fg=PALETTE.get("text_on_card", "#000")).grid(row=2, column=0, sticky="w", padx=12, pady=(6,4))
        entry_pass = tk.Entry(card, font=("Segoe UI", 12), show="*")
        entry_pass.grid(row=3, column=0, padx=12, pady=(0,12), sticky="we")

        # eye button
        eye_btn = tk.Button(card, text="👁️", width=4, command=lambda: self.toggle_password(entry_pass, eye_btn),
                            bg=PALETTE["card"], relief="flat")
        eye_btn.grid(row=3, column=1, padx=(4,12))
        hover_effect(eye_btn)

        btn_frame = tk.Frame(card, bg=PALETTE["card"])
        btn_frame.grid(row=4, column=0, pady=(0,12), padx=12, sticky="we", columnspan=2)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        btn_login = tk.Button(btn_frame, text="Entrar", command=lambda: self._login(entry_user.get().strip(), entry_pass.get().strip()),
                              bg=PALETTE["success"], fg="white", font=("Segoe UI", 11, "bold"), relief="flat", padx=6, pady=6)
        btn_login.grid(row=0, column=0, sticky="we", padx=(0,8))
        hover_effect(btn_login)

        btn_reg = tk.Button(btn_frame, text="Registrar-se", command=self.tela_registro,
                            bg=PALETTE["primary"], fg="white", font=("Segoe UI", 11, "bold"), relief="flat", padx=6, pady=6)
        btn_reg.grid(row=0, column=1, sticky="we", padx=(8,0))
        hover_effect(btn_reg)

        entry_pass.bind("<Return>", lambda e: self._login(entry_user.get().strip(), entry_pass.get().strip()))

    def toggle_password(self, entry_widget, btn_widget):
        try:
            if entry_widget.cget("show") == "":
                entry_widget.configure(show="*")
                btn_widget.configure(text="👁️")
            else:
                entry_widget.configure(show="")
                btn_widget.configure(text="🚫")
        except Exception:
            pass

    def _login(self, usuario, senha):
        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Preencha usuário e senha.")
            return
        cred_file = os.path.join(USERS_DIR, f"{usuario}{CRED_EXT}")
        if not os.path.exists(cred_file):
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return
        try:
            df = pd.read_csv(cred_file, sep=";", dtype=str)
            if df.empty or df.iloc[0].get("Senha", "") != senha:
                messagebox.showerror("Erro", "Usuário ou senha incorretos.")
                return
        except Exception:
            messagebox.showerror("Erro", "Erro ao ler os dados de usuário.")
            return

        self.usuario = usuario
        self.carregar_backups()
        self.tela_principal()

    def tela_registro(self):
        self.clear_root()
        frm = tk.Frame(self.root, bg=PALETTE["bg"])
        frm.pack(expand=True)

        tk.Label(frm, text="📝 Criar Conta FinançasPro", font=("Segoe UI Black", 26), bg=PALETTE["bg"], fg=PALETTE["accent"]).pack(pady=(0,8))
        tk.Label(frm, text="Junte-se e organize suas finanças", font=("Segoe UI", 11), bg=PALETTE["bg"], fg=PALETTE["muted"]).pack(pady=(0,16))

        card = tk.Frame(frm, bg=PALETTE["card"], highlightbackground=PALETTE["border"], highlightthickness=1)
        card.pack(padx=20, pady=10)

        tk.Label(card, text="Usuário", font=("Segoe UI", 11), bg=PALETTE["card"], fg=PALETTE.get("text_on_card", "#000")).grid(row=0, column=0, sticky="w", padx=12, pady=(12,4))
        entry_user = tk.Entry(card, font=("Segoe UI", 12))
        entry_user.grid(row=1, column=0, padx=12, pady=(0,10), sticky="we")

        tk.Label(card, text="Senha", font=("Segoe UI", 11), bg=PALETTE["card"], fg=PALETTE.get("text_on_card", "#000")).grid(row=2, column=0, sticky="w", padx=12, pady=(6,4))
        entry_pass = tk.Entry(card, font=("Segoe UI", 12), show="*")
        entry_pass.grid(row=3, column=0, padx=12, pady=(0,12), sticky="we")

        eye_btn = tk.Button(card, text="👁️", width=4, command=lambda: self.toggle_password(entry_pass, eye_btn),
                            bg=PALETTE["card"], relief="flat")
        eye_btn.grid(row=3, column=1, padx=(4,12))
        hover_effect(eye_btn)

        btn_frame = tk.Frame(card, bg=PALETTE["card"])
        btn_frame.grid(row=4, column=0, pady=(0,12), padx=12, sticky="we", columnspan=2)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        def attempt_register():
            usuario = entry_user.get().strip()
            senha = entry_pass.get().strip()
            if not usuario or not senha:
                messagebox.showwarning("Aviso", "Preencha usuário e senha.")
                return
            cred_file = os.path.join(USERS_DIR, f"{usuario}{CRED_EXT}")
            if os.path.exists(cred_file):
                messagebox.showerror("Erro", "Usuário já existe.")
                return
            try:
                pd.DataFrame([{"Senha": senha}]).to_csv(cred_file, index=False, sep=";")
                pd.DataFrame(columns=["Valor", "Descrição", "Categoria", "Data"]).to_csv(os.path.join(USERS_DIR, f"{usuario}{RECEITAS_EXT}"), index=False, sep=";")
                pd.DataFrame(columns=["Valor", "Descrição", "Categoria", "Data"]).to_csv(os.path.join(USERS_DIR, f"{usuario}{DESPESAS_EXT}"), index=False, sep=";")
                messagebox.showinfo("Sucesso", "Conta criada com sucesso! Faça login.")
                self.tela_login()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao criar conta: {e}")

        tk.Button(btn_frame, text="Criar Conta", command=attempt_register,
                  bg=PALETTE["success"], fg="white", font=("Segoe UI", 11, "bold"), relief="flat").grid(row=0, column=0, sticky="we", padx=(0,6))
        tk.Button(btn_frame, text="Voltar", command=self.tela_login,
                  bg=PALETTE["danger"], fg="white", font=("Segoe UI", 11, "bold"), relief="flat").grid(row=0, column=1, sticky="we", padx=(6,0))

    # ---------------- Tela Principal ----------------
    def tela_principal(self):
        self.clear_root()
        self.root.configure(bg=PALETTE["bg"])

        # Header com espaço para logo (tenta carregar logo.png)
        header = tk.Frame(self.root, bg=PALETTE["accent"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        # espaço pra logo
        logo_frame = tk.Frame(header, bg=PALETTE["accent"], width=56, height=56)
        logo_frame.pack(side="left", padx=16, pady=7)
        logo_frame.pack_propagate(False)
        # tenta carregar logo.png (coloque sua logo como logo.png na mesma pasta)
        try:
            logo_img = tk.PhotoImage(file="logo.png")  # suporta PNG nativo
            logo_label = tk.Label(logo_frame, image=logo_img, bg=PALETTE["accent"])
            logo_label.image = logo_img
            logo_label.pack(expand=True)
        except Exception:
            # Se não houver logo, mostra emoji maior
            tk.Label(logo_frame, text="💰", bg=PALETTE["accent"], font=("Segoe UI", 32)).pack(expand=True)

        tk.Label(header, text="FinançasPro", bg=PALETTE["accent"], fg=PALETTE["accent_text"], font=("Segoe UI Black", 20)).pack(side="left", padx=8)
        tk.Label(header, text=f"👤 {self.usuario}", bg=PALETTE["accent"], fg=PALETTE["accent_text"], font=("Segoe UI", 11)).pack(side="left", padx=12)

        # Botão Sair
        tk.Button(header, text="🚪 Sair", command=self._logout, bg=PALETTE["danger"], fg="white", 
                 relief="flat", font=("Segoe UI", 10, "bold"), padx=16, pady=6, cursor="hand2").pack(side="right", padx=12, pady=15)
        
        # Botão tema
        txt_theme = "💡"
        self.btn_theme = tk.Button(header, text=txt_theme, command=self.toggle_theme, 
                                   bg="white", relief="flat", font=("Segoe UI", 12), 
                                   width=3, cursor="hand2")
        self.btn_theme.pack(side="right", padx=8, pady=15)
        hover_effect(self.btn_theme)

        main = tk.Frame(self.root, bg=PALETTE["bg"])
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # Left column
        left = tk.Frame(main, bg=PALETTE["bg"], width=520)
        left.pack(side="left", fill="y", padx=(0,12))
        left.pack_propagate(False)

        # Receitas
        r_card = tk.Frame(left, bg=PALETTE["card"], bd=0, highlightbackground=PALETTE["border"], highlightthickness=1)
        r_card.pack(fill="both", pady=(0,12), expand=True)
        
        r_header = tk.Frame(r_card, bg=PALETTE["success"], height=45)
        r_header.pack(fill="x")
        r_header.pack_propagate(False)
        tk.Label(r_header, text="📈 Receitas", bg=PALETTE["success"], fg="white", font=("Segoe UI Black", 14)).pack(anchor="w", padx=12, pady=10)

        self.tree_receitas = ttk.Treeview(r_card, columns=("valor", "descricao", "categoria", "data"), show="headings", height=8)
        for col, w, head in (("valor", 14, "Valor"), ("descricao", 30, "Descrição"), ("categoria", 16, "Categoria"), ("data", 10, "Data")):
            self.tree_receitas.heading(col, text=head)
            self.tree_receitas.column(col, width=w*7, anchor="w")
        self.tree_receitas.pack(fill="both", padx=8, pady=(0,8), expand=True)
        self.tree_receitas.bind("<Double-1>", lambda e: self._editar_item_event(e, "receita"))

        btns_r = tk.Frame(r_card, bg=PALETTE["card"])
        btns_r.pack(fill="x", padx=8, pady=(0,10))
        b_add_r = tk.Button(btns_r, text="➕ Nova Receita", command=lambda: self.add_item("receita"),
                  bg=PALETTE["success"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2")
        b_add_r.pack(side="left", padx=(0,6))
        hover_effect(b_add_r)
        b_edit_r = tk.Button(btns_r, text="⚙️ Editar Selecionada", command=lambda: self.edit_selected("receita"),
                             bg=PALETTE["accent"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2")
        b_edit_r.pack(side="left", padx=(6,6))
        hover_effect(b_edit_r)
        b_rep_r = tk.Button(btns_r, text="⏭ Replicar p/ Próx. Mês", command=lambda: self.replicate_selected("receita"),
                             bg=PALETTE["accent"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2")
        b_rep_r.pack(side="left", padx=(6,0))
        hover_effect(b_rep_r)
        # Botão lixeira circular
        b_del_r = tk.Button(btns_r, text="🗑", command=lambda: self.remove_selected("receita"),
                             bg=PALETTE["danger"], fg="white", relief="flat", font=("Segoe UI", 14), 
                             width=2, height=1, cursor="hand2", borderwidth=0)
        b_del_r.pack(side="right", padx=(6,0))
        hover_effect(b_del_r, color_on="#ff7f7f")

        # Despesas
        d_card = tk.Frame(left, bg=PALETTE["card"], bd=0, highlightbackground=PALETTE["border"], highlightthickness=1)
        d_card.pack(fill="both", expand=True)
        
        d_header = tk.Frame(d_card, bg=PALETTE["danger"], height=45)
        d_header.pack(fill="x")
        d_header.pack_propagate(False)
        tk.Label(d_header, text="📉 Despesas", bg=PALETTE["danger"], fg="white", font=("Segoe UI Black", 14)).pack(anchor="w", padx=12, pady=10)

        self.tree_despesas = ttk.Treeview(d_card, columns=("valor", "descricao", "categoria", "data"), show="headings", height=8)
        for col, w, head in (("valor", 14, "Valor"), ("descricao", 30, "Descrição"), ("categoria", 16, "Categoria"), ("data", 10, "Data")):
            self.tree_despesas.heading(col, text=head)
            self.tree_despesas.column(col, width=w*7, anchor="w")
        self.tree_despesas.pack(fill="both", padx=8, pady=(0,8), expand=True)
        self.tree_despesas.bind("<Double-1>", lambda e: self._editar_item_event(e, "despesa"))

        btns_d = tk.Frame(d_card, bg=PALETTE["card"])
        btns_d.pack(fill="x", padx=8, pady=(0,10))
        b_add_d = tk.Button(btns_d, text="➕ Nova Despesa", command=lambda: self.add_item("despesa"),
                  bg=PALETTE["danger"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2")
        b_add_d.pack(side="left", padx=(0,6))
        hover_effect(b_add_d)
        b_edit_d = tk.Button(btns_d, text="⚙️ Editar Selecionada", command=lambda: self.edit_selected("despesa"),
                             bg=PALETTE["accent"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2")
        b_edit_d.pack(side="left", padx=(6,6))
        hover_effect(b_edit_d)
        b_rep_d = tk.Button(btns_d, text="⏭ Replicar p/ Próx. Mês", command=lambda: self.replicate_selected("despesa"),
                             bg=PALETTE["accent"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2")
        b_rep_d.pack(side="left", padx=(6,0))
        hover_effect(b_rep_d)
        # Botão lixeira circular
        b_del_d = tk.Button(btns_d, text="🗑", command=lambda: self.remove_selected("despesa"),
                             bg=PALETTE["danger"], fg="white", relief="flat", font=("Segoe UI", 14), 
                             width=2, height=1, cursor="hand2", borderwidth=0)
        b_del_d.pack(side="right", padx=(6,0))
        hover_effect(b_del_d, color_on="#ff7f7f")

        # Right column
        right = tk.Frame(main, bg=PALETTE["bg"])
        right.pack(side="right", fill="both", expand=True)

        top_controls = tk.Frame(right, bg=PALETTE["bg"])
        top_controls.pack(fill="x", pady=(0,6))

        meses_lista_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        self.cb_mes = ttk.Combobox(top_controls, values=meses_lista_pt, state="readonly", width=12)
        self.cb_mes.current(datetime.now().month - 1)
        self.cb_mes.pack(side="right", padx=(6,12))
        self.cb_mes.bind("<<ComboboxSelected>>", lambda e: self.update_view())

        anos_lista = [str(y) for y in range(datetime.now().year-5, datetime.now().year+6)]
        self.cb_ano = ttk.Combobox(top_controls, values=anos_lista, state="readonly", width=6)
        self.cb_ano.set(str(datetime.now().year))
        self.cb_ano.pack(side="right")
        self.cb_ano.bind("<<ComboboxSelected>>", lambda e: self.update_view())

        tk.Label(top_controls, text="Período:", bg=PALETTE["bg"], fg=PALETTE["muted"], font=("Segoe UI", 10)).pack(side="right", padx=(0,6))

        faixa = tk.Frame(right, bg=PALETTE["accent"])
        faixa.pack(fill="x")
        faixa.pack_propagate(False)
        faixa.configure(height=60)
        tk.Label(faixa, text="📊 Resumo do Mês", bg=PALETTE["accent"], fg=PALETTE["accent_text"], font=("Segoe UI Black", 16)).pack(anchor="w", padx=20, pady=15)

        resumo_card = tk.Frame(right, bg=PALETTE["card"], bd=0, relief="flat", highlightbackground=PALETTE["border"], highlightthickness=1)
        resumo_card.pack(fill="x", pady=(10,14))
        resumo_card.columnconfigure(0, weight=1)
        resumo_card.columnconfigure(1, weight=1)
        resumo_card.columnconfigure(2, weight=1)

        self.lbl_saldo = tk.Label(resumo_card, text="Saldo do mês: R$ 0,00", bg=PALETTE["card"], font=("Segoe UI", 15, "bold"), fg=PALETTE["accent"])
        self.lbl_receitas = tk.Label(resumo_card, text="Total Receitas: R$ 0,00", bg=PALETTE["card"], font=("Segoe UI", 14, "bold"), fg=PALETTE["success"])
        self.lbl_despesas = tk.Label(resumo_card, text="Total Despesas: R$ 0,00", bg=PALETTE["card"], font=("Segoe UI", 14, "bold"), fg=PALETTE["danger"])

        self.lbl_saldo.grid(row=0, column=0, padx=20, pady=16, sticky="w")
        self.lbl_receitas.grid(row=0, column=1, padx=20, pady=16)
        self.lbl_despesas.grid(row=0, column=2, padx=20, pady=16, sticky="e")

        graf_box = tk.Frame(right, bg=PALETTE["bg"])
        graf_box.pack(fill="both", expand=True)

        graf_left = tk.Frame(graf_box, bg=PALETTE["bg"])
        graf_left.pack(side="left", fill="both", expand=True)

        graf_right = tk.Frame(graf_box, bg=PALETTE["bg"], width=260)
        graf_right.pack(side="right", fill="y", padx=(12,0))
        graf_right.pack_propagate(False)

        self.fig, self.ax = plt.subplots(figsize=(6,5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graf_left)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.legend_frame = tk.Frame(graf_right, bg=PALETTE["bg"])
        self.legend_frame.pack(anchor="n", pady=20, padx=6)

        util_box = tk.Frame(right, bg=PALETTE["card"], highlightbackground=PALETTE["border"], highlightthickness=1)
        util_box.pack(fill="x", pady=(8,0))
        
        btn_csv = tk.Button(util_box, text="📄 Exportar CSV", command=self.exportar_mes_csv, 
                           bg=PALETTE["primary"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), 
                           padx=16, pady=8, cursor="hand2")
        btn_csv.pack(side="left", padx=10, pady=10)
        hover_effect(btn_csv)
        
        btn_csv_periodo = tk.Button(util_box, text="📅 CSV Período", command=self.exportar_periodo_csv, 
                           bg=PALETTE["primary"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), 
                           padx=16, pady=8, cursor="hand2")
        btn_csv_periodo.pack(side="left", padx=10, pady=10)
        hover_effect(btn_csv_periodo)
        
        btn_pdf = tk.Button(util_box, text="📑 Exportar PDF", command=self.exportar_pdf, 
                           bg=PALETTE["accent"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), 
                           padx=16, pady=8, cursor="hand2")
        btn_pdf.pack(side="right", padx=10, pady=10)
        hover_effect(btn_pdf)
        
        btn_pdf_periodo = tk.Button(util_box, text="📅 PDF Período", command=self.exportar_periodo_pdf, 
                           bg=PALETTE["accent"], fg="white", relief="flat", font=("Segoe UI", 10, "bold"), 
                           padx=16, pady=8, cursor="hand2")
        btn_pdf_periodo.pack(side="right", padx=10, pady=10)
        hover_effect(btn_pdf_periodo)

        # popular e atualizar painel
        self.popular_tabelas()
        self.update_view()
        self.root.bind("<Configure>", lambda e: self._on_resize())

    def abrir_controle_credito(self):
        # Método removido - funcionalidade de controle de crédito não será mais utilizada
        pass

    def toggle_theme(self):
        new = "dark" if self.cfg.get("theme", "light") == "light" else "light"
        self.cfg["theme"] = new
        save_config(self.cfg)
        self.set_palette(new)
        # rebuild UI to apply palette (simple approach)
        self.tela_principal()

    def _logout(self):
        self.usuario = None
        self.receitas = []
        self.despesas = []
        self.tela_login()

    # ---------------- manipulação itens ----------------
    def add_item(self, tipo, prefill=None, edit_index=None):
        top = tk.Toplevel(self.root)
        top.title("Adicionar " + ("Receita" if tipo == "receita" else "Despesa"))
        top.transient(self.root)
        top.grab_set()
        top.geometry("440x500")
        top.configure(bg=PALETTE["bg"])

        # Header colorido
        header_color = PALETTE["success"] if tipo == "receita" else PALETTE["danger"]
        header = tk.Frame(top, bg=header_color, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        icon = "💰" if tipo == "receita" else "💸"
        title_text = f"{icon} {'Nova Receita' if not edit_index else 'Editar Receita'}" if tipo == "receita" else f"{icon} {'Nova Despesa' if not edit_index else 'Editar Despesa'}"
        tk.Label(header, text=title_text, bg=header_color, fg="white", font=("Segoe UI Black", 16)).pack(pady=16)

        card = tk.Frame(top, bg=PALETTE["card"], highlightbackground=PALETTE["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(card, text="Valor (R$):", bg=PALETTE["card"], font=("Segoe UI", 11, "bold"), fg=PALETTE.get("text_on_card", "#000")).pack(anchor="w", padx=8, pady=(8,2))
        entry_val = tk.Entry(card, font=("Segoe UI", 12))
        entry_val.pack(fill="x", padx=8)

        tk.Label(card, text="Descrição:", bg=PALETTE["card"], font=("Segoe UI", 11, "bold"), fg=PALETTE.get("text_on_card", "#000")).pack(anchor="w", padx=8, pady=(8,2))
        entry_desc = tk.Entry(card, font=("Segoe UI", 12))
        entry_desc.pack(fill="x", padx=8)

        tk.Label(card, text="Categoria:", bg=PALETTE["card"], font=("Segoe UI", 11, "bold"), fg=PALETTE.get("text_on_card", "#000")).pack(anchor="w", padx=8, pady=(8,2))
        categorias = CATEGORIAS_RECEITAS if tipo == "receita" else CATEGORIAS_DESPESAS
        cat_var = tk.StringVar(value=categorias[0])
        combo_cat = ttk.Combobox(card, values=categorias, textvariable=cat_var, state="readonly")
        combo_cat.pack(fill="x", padx=8)

        tk.Label(card, text="Data:", bg=PALETTE["card"], font=("Segoe UI", 11, "bold"), fg=PALETTE.get("text_on_card", "#000")).pack(anchor="w", padx=8, pady=(8,2))
        # Important: DateEntry.get_date() returns a date object — we will always use that (avoids month-shift bugs)
        date_entry = DateEntry(card, date_pattern="dd/mm/yyyy", width=16, locale='pt_BR')
        date_entry.pack(anchor="w", padx=8)
        # Default the picker to the currently selected month/year in the UI (keeps chosen day when possible)
        try:
            sel_mes = (self.cb_mes.current() + 1) if hasattr(self, 'cb_mes') and self.cb_mes.get() else datetime.now().month
            sel_ano = int(self.cb_ano.get()) if hasattr(self, 'cb_ano') and self.cb_ano.get() else datetime.now().year
            today_day = datetime.now().day
            last_day = monthrange(sel_ano, sel_mes)[1]
            set_day = min(today_day, last_day)
            date_entry.set_date(datetime(sel_ano, sel_mes, set_day))
        except Exception:
            # fallback silently; DateEntry already has a default
            pass

        # opção repetir mensalmente (só aparece se NÃO estiver editando)
        frame_repeat = tk.Frame(card, bg=PALETTE["card"])
        if edit_index is None:  # Só mostra se for nova transação
            frame_repeat.pack(fill="x", padx=8, pady=(12,0))
            repeat_var = tk.IntVar(value=0)
            tk.Checkbutton(frame_repeat, text="Repetir mensalmente", variable=repeat_var, 
                          bg=PALETTE["card"], fg=PALETTE.get("text_on_card", "#000"), 
                          selectcolor=PALETTE["card"]).grid(row=0, column=0, sticky="w")
            tk.Label(frame_repeat, text="Qtd meses:", bg=PALETTE["card"], 
                    fg=PALETTE.get("text_on_card", "#000")).grid(row=0, column=1, padx=(12,4))
            spin_qtd = tk.Spinbox(frame_repeat, from_=0, to=36, width=4)
            spin_qtd.grid(row=0, column=2)
        else:
            repeat_var = tk.IntVar(value=0)  # Variável dummy para não quebrar o código

        btn = tk.Button(card, text="💾 Salvar", bg=header_color, fg="white", font=("Segoe UI", 12, "bold"), 
                       relief="flat", cursor="hand2", padx=20, pady=10)
        btn.pack(padx=8, pady=16, fill="x")
        hover_effect(btn)

        # prefill
        if prefill:
            entry_val.insert(0, str(prefill.get("valor", "")))
            entry_desc.insert(0, prefill.get("descricao", ""))
            combo_cat.set(prefill.get("categoria", categorias[0]))
            try:
                d = datetime.strptime(prefill.get("data", datetime.now().strftime("%d/%m/%Y")), "%d/%m/%Y")
                date_entry.set_date(d)
            except Exception:
                pass

        def salvar():
            raw_input = entry_val.get().strip()
            if not raw_input:
                messagebox.showerror("Erro", "Informe um valor.")
                return
            try:
                valor = normalize_value_input(raw_input)
            except Exception:
                messagebox.showerror("Erro", "Valor inválido. Use números (ex: 1200.50 ou 1.200,50).")
                return

            desc = entry_desc.get().strip() or ("Sem descrição")
            categoria = cat_var.get()
            # Use date_entry.get_date() directly so day/month/year is preserved exactly as user picked
            try:
                data_obj = date_entry.get_date()
                data_s = data_obj.strftime("%d/%m/%Y")
            except Exception:
                data_s = datetime.now().strftime("%d/%m/%Y")

            qtd_repeat = 0
            try:
                if edit_index is None and repeat_var.get():
                    qtd_repeat = int(spin_qtd.get())
            except Exception:
                qtd_repeat = 0

            if tipo == "receita":
                if edit_index is not None:
                    if 0 <= edit_index < len(self.receitas):
                        self.receitas[edit_index] = (valor, desc, categoria, data_s)
                else:
                    self.receitas.append((valor, desc, categoria, data_s))
                    # Allow past dates but warn about future repeats if date is in the past
                    if qtd_repeat > 0:
                        data_obj = datetime.strptime(data_s, "%d/%m/%Y")
                        current_date = datetime.now()
                        if data_obj < current_date and not messagebox.askyesno("Confirmação", "A data selecionada está no passado. Deseja criar as repetições a partir do mês atual?"):
                            qtd_repeat = 0
                    
                    # Create copies if repeat is enabled
                    for m in range(1, qtd_repeat + 1):
                        new_date = add_months_to_date_str(data_s, m)
                        self.receitas.append((valor, desc, categoria, new_date))
            else:
                if edit_index is not None:
                    if 0 <= edit_index < len(self.despesas):
                        self.despesas[edit_index] = (valor, desc, categoria, data_s)
                else:
                    self.despesas.append((valor, desc, categoria, data_s))
                    # Allow past dates but warn about future repeats if date is in the past
                    if qtd_repeat > 0:
                        data_obj = datetime.strptime(data_s, "%d/%m/%Y")
                        current_date = datetime.now()
                        if data_obj < current_date and not messagebox.askyesno("Confirmação", "A data selecionada está no passado. Deseja criar as repetições a partir do mês atual?"):
                            qtd_repeat = 0
                            
                    # Create copies if repeat is enabled
                    for m in range(1, qtd_repeat + 1):
                        new_date = add_months_to_date_str(data_s, m)
                        self.despesas.append((valor, desc, categoria, new_date))

            try:
                self.salvar_backups()
            except Exception as e:
                messagebox.showwarning("Aviso", f"Transação salva, mas falha ao salvar backup: {e}")

            # Atualizar para o mês da transação
            try:
                data_trans = datetime.strptime(data_s, "%d/%m/%Y")
                self.cb_mes.current(data_trans.month - 1)
                self.cb_ano.set(str(data_trans.year))
            except Exception:
                pass

            self.popular_tabelas()
            self.update_view()

            orig = btn["bg"]
            btn.configure(bg=PALETTE.get("btn_hover"))
            top.after(120, lambda: btn.configure(bg=orig))
            top.after(220, top.destroy)

        btn.configure(command=salvar)

    def edit_selected(self, tipo):
        # localizar seleção e abrir add_item com prefill e edit index
        tree = self.tree_receitas if tipo == "receita" else self.tree_despesas
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Nenhuma transação selecionada.")
            return
        vals = tree.item(sel[0], "values")
        if not vals:
            return
        try:
            valor_str, desc, categoria, data_s = vals
            valor = normalize_value_input(valor_str.replace("R$", ""))
        except Exception:
            messagebox.showerror("Erro", "Falha ao interpretar item selecionado.")
            return

        # encontrar índice no array completo
        if tipo == "receita":
            idx = find_matching_index(self.receitas, valor, desc, categoria, data_s)
            if idx is None:
                messagebox.showerror("Erro", "Não foi possível localizar a transação para editar.")
                return
            prefill = {"valor": valor, "descricao": desc, "categoria": categoria, "data": data_s}
            self.add_item("receita", prefill=prefill, edit_index=idx)
        else:
            idx = find_matching_index(self.despesas, valor, desc, categoria, data_s)
            if idx is None:
                messagebox.showerror("Erro", "Não foi possível localizar a transação para editar.")
                return
            prefill = {"valor": valor, "descricao": desc, "categoria": categoria, "data": data_s}
            self.add_item("despesa", prefill=prefill, edit_index=idx)

    def replicate_selected(self, tipo):
        tree = self.tree_receitas if tipo == "receita" else self.tree_despesas
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Nenhuma transação selecionada.")
            return
        vals = tree.item(sel[0], "values")
        try:
            valor_str, desc, categoria, data_s = vals
            valor = normalize_value_input(valor_str.replace("R$", ""))
        except Exception:
            messagebox.showerror("Erro", "Falha ao interpretar item selecionado.")
            return

        new_date = add_months_to_date_str(data_s, 1)
        if tipo == "receita":
            self.receitas.append((valor, desc, categoria, new_date))
        else:
            self.despesas.append((valor, desc, categoria, new_date))

        try:
            self.salvar_backups()
        except Exception as e:
            messagebox.showwarning("Aviso", f"Replicada, mas falha ao salvar backup: {e}")

        messagebox.showinfo("Replicar", f"Transação replicada para {new_date}.")
        self.popular_tabelas()
        self.update_view()

    def remove_selected(self, tipo):
        tree = self.tree_receitas if tipo == "receita" else self.tree_despesas
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Nenhuma transação selecionada.")
            return
        # confirmar remoção
        if not messagebox.askyesno("Confirmar", "Confirma remoção das transações selecionadas?"):
            return
        removed_any = False
        for it in sel:
            vals = tree.item(it, "values")
            try:
                valor_str, desc, categoria, data_s = vals
                valor = normalize_value_input(valor_str.replace("R$", ""))
                if tipo == "receita":
                    idx = find_matching_index(self.receitas, valor, desc, categoria, data_s)
                    if idx is not None:
                        self.receitas.pop(idx)
                        removed_any = True
                else:
                    idx = find_matching_index(self.despesas, valor, desc, categoria, data_s)
                    if idx is not None:
                        self.despesas.pop(idx)
                        removed_any = True
            except Exception:
                pass
        if removed_any:
            try:
                self.salvar_backups()
            except Exception as e:
                messagebox.showwarning("Aviso", f"Remoção efetuada, mas falha ao salvar backup: {e}")
            self.popular_tabelas()
            self.update_view()
            messagebox.showinfo("Remoção", "Transações removidas com sucesso.")
        else:
            messagebox.showwarning("Aviso", "Nenhuma transação foi removida (itens possivelmente duplicados ou não encontrados).")

    # ---------------- Backups ----------------
    def salvar_backups(self):
        if not self.usuario:
            return
        rfile = os.path.join(USERS_DIR, f"{self.usuario}{RECEITAS_EXT}")
        dfile = os.path.join(USERS_DIR, f"{self.usuario}{DESPESAS_EXT}")
        pd.DataFrame(self.receitas, columns=["Valor", "Descrição", "Categoria", "Data"]).to_csv(rfile, index=False, sep=";")
        pd.DataFrame(self.despesas, columns=["Valor", "Descrição", "Categoria", "Data"]).to_csv(dfile, index=False, sep=";")

    def carregar_backups(self):
        if not self.usuario:
            return
        rfile = os.path.join(USERS_DIR, f"{self.usuario}{RECEITAS_EXT}")
        dfile = os.path.join(USERS_DIR, f"{self.usuario}{DESPESAS_EXT}")
        try:
            if os.path.exists(rfile):
                df = pd.read_csv(rfile, sep=";")
                self.receitas = [(float(row["Valor"]), str(row["Descrição"]), str(row["Categoria"]), str(row["Data"])) for _, row in df.iterrows()] if not df.empty else []
            else:
                self.receitas = []
            if os.path.exists(dfile):
                df2 = pd.read_csv(dfile, sep=";")
                self.despesas = [(float(row["Valor"]), str(row["Descrição"]), str(row["Categoria"]), str(row["Data"])) for _, row in df2.iterrows()] if not df2.empty else []
            else:
                self.despesas = []
        except Exception:
            # fallback to empty lists on error
            self.receitas = []
            self.despesas = []

    # ---------------- Atualizações UI ----------------
    def popular_tabelas(self):
        # Exibe apenas transações do mês/ano selecionado
        for it in self.tree_receitas.get_children():
            self.tree_receitas.delete(it)
        for it in self.tree_despesas.get_children():
            self.tree_despesas.delete(it)

        try:
            mes = self.cb_mes.current() + 1
            ano = int(self.cb_ano.get())
        except Exception:
            mes = datetime.now().month
            ano = datetime.now().year

        # filtrar
        recs = []
        for r in self.receitas:
            try:
                d = datetime.strptime(r[3], "%d/%m/%Y")
                if d.month == mes and d.year == ano:
                    recs.append(r)
            except Exception:
                continue
        desps = []
        for d in self.despesas:
            try:
                dt = datetime.strptime(d[3], "%d/%m/%Y")
                if dt.month == mes and dt.year == ano:
                    desps.append(d)
            except Exception:
                continue

        for valor, desc, cat, data in recs:
            self.tree_receitas.insert("", "end", values=(fmt_val(valor), desc, cat, data))
        for valor, desc, cat, data in desps:
            self.tree_despesas.insert("", "end", values=(fmt_val(valor), desc, cat, data))

    def update_view(self):
        # atualiza tabelas e dashboard
        self.popular_tabelas()
        self.update_dashboard()

    def update_dashboard(self):
        try:
            mes = self.cb_mes.current() + 1
            ano = int(self.cb_ano.get())
        except Exception:
            mes = datetime.now().month
            ano = datetime.now().year

        recs = []
        for r in self.receitas:
            try:
                d = datetime.strptime(r[3], "%d/%m/%Y")
                if d.month == mes and d.year == ano:
                    recs.append(r)
            except Exception:
                continue
        desps = []
        for d in self.despesas:
            try:
                dt = datetime.strptime(d[3], "%d/%m/%Y")
                if dt.month == mes and dt.year == ano:
                    desps.append(d)
            except Exception:
                continue

        total_receitas = sum([r[0] for r in recs])
        total_despesas = sum([d[0] for d in desps])
        saldo = total_receitas - total_despesas

        self.lbl_saldo.config(text=f"Saldo do mês: {fmt_val(saldo)}")
        self.lbl_receitas.config(text=f"Total Receitas: {fmt_val(total_receitas)}")
        self.lbl_despesas.config(text=f"Total Despesas: {fmt_val(total_despesas)}")

        # anima saldo se mudou
        if self.ultimo_saldo_animado is None or abs(saldo - self.ultimo_saldo_animado) > 0.001:
            self._pulse_label(self.lbl_saldo)
            self.ultimo_saldo_animado = saldo

        # pizza: despesas por categoria
        df_desps = pd.DataFrame(desps, columns=["Valor","Descrição","Categoria","Data"]) if desps else pd.DataFrame(columns=["Valor","Descrição","Categoria","Data"])
        soma_cat = df_desps.groupby("Categoria")["Valor"].sum().sort_values(ascending=False) if not df_desps.empty else pd.Series(dtype=float)

        self.ax.clear()
        if not soma_cat.empty and soma_cat.sum() > 0:
            labels = list(soma_cat.index)
            sizes = list(soma_cat.values)
            colors = [COLORS_CHART.get(l, "#6b7280") for l in labels]
            
            # Criar gráfico de pizza moderno com estilo melhorado
            wedges, texts, autotexts = self.ax.pie(
                sizes, 
                labels=None, 
                autopct="%1.1f%%", 
                startangle=90, 
                colors=colors, 
                wedgeprops=dict(width=0.6, edgecolor='white', linewidth=2),
                textprops=dict(color="white", fontweight="bold", fontsize=10)
            )
            self.ax.axis('equal')
            self.ax.set_title("Despesas por Categoria", fontsize=14, fontweight='bold', pad=15, color=PALETTE.get("text_on_card", "#000"))

            for w in self.legend_frame.winfo_children():
                w.destroy()
            for lbl, col in zip(labels, colors):
                row = tk.Frame(self.legend_frame, bg=PALETTE["bg"])
                row.pack(anchor="w", pady=4)
                # Quadrado colorido maior e com borda
                sw = tk.Canvas(row, width=20, height=20, bg=PALETTE["bg"], highlightthickness=0)
                sw.create_rectangle(2, 2, 18, 18, fill=col, outline="white", width=2)
                sw.pack(side="left", padx=(6,10))
                tk.Label(row, text=lbl, bg=PALETTE["bg"], font=("Segoe UI", 11, "bold"), fg=PALETTE.get("text_on_card")).pack(side="left")
        else:
            for w in self.legend_frame.winfo_children():
                w.destroy()
            self.ax.text(0.5, 0.5, "📊 Sem dados para exibir", horizontalalignment="center", verticalalignment="center", 
                        transform=self.ax.transAxes, fontsize=14, color=PALETTE.get("muted", "#999"), fontweight='bold')
            self.ax.axis('off')

        # Aplicar fundo do gráfico conforme tema
        self.fig.patch.set_facecolor(PALETTE["bg"])
        self.ax.set_facecolor(PALETTE["bg"])
        self.fig.tight_layout()
        self.canvas.draw()

    def _pulse_label(self, label, steps=6, max_increase=2):
        try:
            font_parts = label.cget("font").split()
            size = int([p for p in font_parts if p.isdigit()][0])
        except Exception:
            size = 14
        def step(i):
            if i > steps:
                label.configure(font=("Segoe UI", size, "bold"))
                return
            delta = int((max_increase * (1 - abs((i - steps/2) / (steps/2)))))
            label.configure(font=("Segoe UI", size + delta, "bold"))
            self.root.after(60, lambda: step(i+1))
        step(0)

    def _on_resize(self):
        try:
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception:
            pass

    def clear_root(self):
        for w in self.root.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    # ---------------- Export / Backup ----------------
    def exportar_periodo_pdf(self):
        """Exporta dados de um período personalizado para PDF."""
        self._selecionar_periodo_exportar("pdf")
    
    def exportar_periodo_csv(self):
        """Exporta dados de um período personalizado para CSV."""
        self._selecionar_periodo_exportar("csv")
    
    def _selecionar_periodo_exportar(self, formato):
        """Janela para selecionar período de exportação."""
        top = tk.Toplevel(self.root)
        top.title(f"Exportar {formato.upper()} - Período Personalizado")
        top.transient(self.root)
        top.grab_set()
        top.geometry("480x440")
        top.configure(bg=PALETTE["bg"])
        
        # Header
        header = tk.Frame(top, bg=PALETTE["accent"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"📅 Selecionar Período para {formato.upper()}", bg=PALETTE["accent"], 
                fg="white", font=("Segoe UI Black", 14)).pack(pady=18)
        
        card = tk.Frame(top, bg=PALETTE["card"], highlightbackground=PALETTE["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Opções de período
        tk.Label(card, text="Tipo de Período:", bg=PALETTE["card"], font=("Segoe UI", 11, "bold"), 
                fg=PALETTE.get("text_on_card", "#000")).pack(anchor="w", padx=12, pady=(12,8))
        
        tipo_var = tk.StringVar(value="mes_mes")
        
        rb_frame = tk.Frame(card, bg=PALETTE["card"])
        rb_frame.pack(fill="x", padx=12, pady=(0,12))
        
        tk.Radiobutton(rb_frame, text="Mês a Mês", variable=tipo_var, value="mes_mes", 
                      bg=PALETTE["card"], fg=PALETTE.get("text_on_card", "#000"), 
                      selectcolor=PALETTE["card"], font=("Segoe UI", 10)).pack(anchor="w", pady=2)
        tk.Radiobutton(rb_frame, text="Ano Completo", variable=tipo_var, value="ano_completo", 
                      bg=PALETTE["card"], fg=PALETTE.get("text_on_card", "#000"), 
                      selectcolor=PALETTE["card"], font=("Segoe UI", 10)).pack(anchor="w", pady=2)
        
        # Frame para seleção de período mês a mês
        periodo_frame = tk.Frame(card, bg=PALETTE["card"])
        periodo_frame.pack(fill="x", padx=12, pady=8)
        
        # Mês/Ano Inicial
        tk.Label(periodo_frame, text="De:", bg=PALETTE["card"], font=("Segoe UI", 10, "bold"), 
                fg=PALETTE.get("text_on_card", "#000")).grid(row=0, column=0, sticky="w", pady=4)
        
        meses_lista_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                         "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        anos_lista = [str(y) for y in range(datetime.now().year-5, datetime.now().year+6)]
        
        cb_mes_inicio = ttk.Combobox(periodo_frame, values=meses_lista_pt, state="readonly", width=12)
        cb_mes_inicio.current(0)
        cb_mes_inicio.grid(row=0, column=1, padx=4, pady=4)
        
        cb_ano_inicio = ttk.Combobox(periodo_frame, values=anos_lista, state="readonly", width=8)
        cb_ano_inicio.set(str(datetime.now().year))
        cb_ano_inicio.grid(row=0, column=2, padx=4, pady=4)
        
        # Mês/Ano Final
        tk.Label(periodo_frame, text="Até:", bg=PALETTE["card"], font=("Segoe UI", 10, "bold"), 
                fg=PALETTE.get("text_on_card", "#000")).grid(row=1, column=0, sticky="w", pady=4)
        
        cb_mes_fim = ttk.Combobox(periodo_frame, values=meses_lista_pt, state="readonly", width=12)
        cb_mes_fim.current(datetime.now().month - 1)
        cb_mes_fim.grid(row=1, column=1, padx=4, pady=4)
        
        cb_ano_fim = ttk.Combobox(periodo_frame, values=anos_lista, state="readonly", width=8)
        cb_ano_fim.set(str(datetime.now().year))
        cb_ano_fim.grid(row=1, column=2, padx=4, pady=4)
        
        # Frame para ano completo
        ano_frame = tk.Frame(card, bg=PALETTE["card"])
        ano_frame.pack(fill="x", padx=12, pady=8)
        
        tk.Label(ano_frame, text="Ano:", bg=PALETTE["card"], font=("Segoe UI", 10, "bold"), 
                fg=PALETTE.get("text_on_card", "#000")).grid(row=0, column=0, sticky="w", pady=4)
        
        cb_ano_completo = ttk.Combobox(ano_frame, values=anos_lista, state="readonly", width=8)
        cb_ano_completo.set(str(datetime.now().year))
        cb_ano_completo.grid(row=0, column=1, padx=4, pady=4)
        
        def toggle_inputs():
            if tipo_var.get() == "mes_mes":
                for w in periodo_frame.winfo_children():
                    w.configure(state="normal" if isinstance(w, ttk.Combobox) else "normal")
                for w in ano_frame.winfo_children():
                    if isinstance(w, ttk.Combobox):
                        w.configure(state="disabled")
            else:
                for w in periodo_frame.winfo_children():
                    if isinstance(w, ttk.Combobox):
                        w.configure(state="disabled")
                for w in ano_frame.winfo_children():
                    if isinstance(w, ttk.Combobox):
                        w.configure(state="normal")
        
        for rb in rb_frame.winfo_children():
            if isinstance(rb, tk.Radiobutton):
                rb.configure(command=toggle_inputs)
        
        toggle_inputs()
        
        # Botão exportar
        btn_exportar = tk.Button(card, text=f"📥 Exportar {formato.upper()}", 
                                bg=PALETTE["success"], fg="white", font=("Segoe UI", 12, "bold"), 
                                relief="flat", cursor="hand2", padx=20, pady=10)
        btn_exportar.pack(padx=12, pady=16, fill="x")
        hover_effect(btn_exportar)
        
        def executar_exportacao():
            try:
                if tipo_var.get() == "mes_mes":
                    mes_inicio = cb_mes_inicio.current() + 1
                    ano_inicio = int(cb_ano_inicio.get())
                    mes_fim = cb_mes_fim.current() + 1
                    ano_fim = int(cb_ano_fim.get())
                    
                    # Validar período
                    data_inicio = datetime(ano_inicio, mes_inicio, 1)
                    data_fim = datetime(ano_fim, mes_fim, 1)
                    
                    if data_inicio > data_fim:
                        messagebox.showerror("Erro", "A data inicial deve ser anterior à data final.")
                        return
                    
                    periodo_str = f"{meses_lista_pt[mes_inicio-1]}/{ano_inicio} a {meses_lista_pt[mes_fim-1]}/{ano_fim}"
                    
                else:  # ano_completo
                    ano = int(cb_ano_completo.get())
                    mes_inicio = 1
                    ano_inicio = ano
                    mes_fim = 12
                    ano_fim = ano
                    periodo_str = f"Ano {ano}"
                
                # Filtrar transações do período
                recs = []
                for r in self.receitas:
                    try:
                        d = datetime.strptime(r[3], "%d/%m/%Y")
                        data_inicio = datetime(ano_inicio, mes_inicio, 1)
                        ultimo_dia = monthrange(ano_fim, mes_fim)[1]
                        data_fim = datetime(ano_fim, mes_fim, ultimo_dia)
                        if data_inicio <= d <= data_fim:
                            recs.append(r)
                    except Exception:
                        continue
                
                desps = []
                for d in self.despesas:
                    try:
                        dt = datetime.strptime(d[3], "%d/%m/%Y")
                        data_inicio = datetime(ano_inicio, mes_inicio, 1)
                        ultimo_dia = monthrange(ano_fim, mes_fim)[1]
                        data_fim = datetime(ano_fim, mes_fim, ultimo_dia)
                        if data_inicio <= dt <= data_fim:
                            desps.append(d)
                    except Exception:
                        continue
                
                if not recs and not desps:
                    messagebox.showinfo("Exportar", "Nenhuma transação encontrada no período selecionado.")
                    return
                
                top.destroy()
                
                # Exportar
                if formato == "pdf":
                    self._gerar_pdf_periodo(recs, desps, periodo_str, ano_inicio, mes_inicio, ano_fim, mes_fim)
                else:
                    self._gerar_csv_periodo(recs, desps, periodo_str, ano_inicio, mes_inicio, ano_fim, mes_fim)
                    
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {e}")
        
        btn_exportar.configure(command=executar_exportacao)
    
    def _gerar_pdf_periodo(self, recs, desps, periodo_str, ano_inicio, mes_inicio, ano_fim, mes_fim):
        """Gera PDF para um período de dados."""
        filename = f"financas_{self.usuario}_{ano_inicio}_{mes_inicio:02d}_ate_{ano_fim}_{mes_fim:02d}.pdf"
        dest = filedialog.asksaveasfilename(
            title="Salvar PDF do período",
            defaultextension=".pdf",
            initialfile=filename
        )
        if not dest:
            return
        
        try:
            doc = SimpleDocTemplate(dest, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30
            )
            elements.append(Paragraph(f"Relatório Financeiro - {periodo_str}", title_style))
            elements.append(Spacer(1, 20))
            
            # Tabela de Receitas
            if recs:
                elements.append(Paragraph("Receitas", styles["Heading2"]))
                elements.append(Spacer(1, 10))
                
                data = [["Data", "Valor", "Descrição", "Categoria"]]
                sorted_recs = sorted(recs, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y"))
                
                for valor, desc, cat, data_s in sorted_recs:
                    data.append([data_s, fmt_val(valor), desc, cat])
                
                t = Table(data, colWidths=[1*inch, 1.5*inch, 2.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))
            
            # Tabela de Despesas
            if desps:
                elements.append(Paragraph("Despesas", styles["Heading2"]))
                elements.append(Spacer(1, 10))
                
                data = [["Data", "Valor", "Descrição", "Categoria"]]
                sorted_desps = sorted(desps, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y"))
                
                for valor, desc, cat, data_s in sorted_desps:
                    data.append([data_s, fmt_val(valor), desc, cat])
                
                t = Table(data, colWidths=[1*inch, 1.5*inch, 2.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.salmon),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))
            
            # Resumo
            total_receitas = sum(r[0] for r in recs)
            total_despesas = sum(d[0] for d in desps)
            saldo = total_receitas - total_despesas
            
            elements.append(Paragraph(f"Resumo do Período", styles["Heading2"]))
            elements.append(Spacer(1, 10))
            
            resumo_data = [
                ["Total Receitas:", fmt_val(total_receitas)],
                ["Total Despesas:", fmt_val(total_despesas)],
                ["Saldo:", fmt_val(saldo)]
            ]
            
            t = Table(resumo_data, colWidths=[2*inch, 2*inch])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('TEXTCOLOR', (-1, -1), (-1, -1), colors.green if saldo >= 0 else colors.red)
            ]))
            elements.append(t)
            
            # Gerar PDF
            doc.build(elements)
            messagebox.showinfo("Exportar", f"PDF salvo em:\n{dest}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {str(e)}")
    
    def _gerar_csv_periodo(self, recs, desps, periodo_str, ano_inicio, mes_inicio, ano_fim, mes_fim):
        """Gera CSV para um período de dados."""
        filename = f"financas_{self.usuario}_{ano_inicio}_{mes_inicio:02d}_ate_{ano_fim}_{mes_fim:02d}.csv"
        dest = filedialog.asksaveasfilename(
            title="Salvar CSV do período",
            defaultextension=".csv",
            initialfile=filename
        )
        if not dest:
            return
        
        try:
            with open(dest, "w", encoding="utf-8-sig", newline='') as f:
                # Cabeçalho
                f.write(f"RELATÓRIO FINANCEIRO - {periodo_str.upper()}\n")
                f.write("\n")
                
                # Seção RECEITAS
                f.write("=== RECEITAS ===\n")
                f.write("Data;Valor;Descrição;Categoria\n")
                
                if recs:
                    recs_sorted = sorted(recs, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y"))
                    for valor, desc, cat, data in recs_sorted:
                        f.write(f"{data};{valor:.2f};{desc};{cat}\n")
                else:
                    f.write("Nenhuma receita no período\n")
                
                f.write("\n")
                
                # Seção DESPESAS
                f.write("=== DESPESAS ===\n")
                f.write("Data;Valor;Descrição;Categoria\n")
                
                if desps:
                    desps_sorted = sorted(desps, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y"))
                    for valor, desc, cat, data in desps_sorted:
                        f.write(f"{data};{valor:.2f};{desc};{cat}\n")
                else:
                    f.write("Nenhuma despesa no período\n")
                
                f.write("\n")
                
                # Resumo
                total_receitas = sum(r[0] for r in recs)
                total_despesas = sum(d[0] for d in desps)
                saldo = total_receitas - total_despesas
                
                f.write("=== RESUMO DO PERÍODO ===\n")
                f.write(f"Total Receitas;{total_receitas:.2f}\n")
                f.write(f"Total Despesas;{total_despesas:.2f}\n")
                f.write(f"Saldo;{saldo:.2f}\n")
            
            messagebox.showinfo("Exportar", f"CSV salvo com sucesso em:\n{dest}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar CSV: {str(e)}")

    def exportar_pdf(self):
        """Exporta os dados do mês atual para PDF."""
        try:
            mes = self.cb_mes.current() + 1
            ano = int(self.cb_ano.get())
        except Exception:
            mes = datetime.now().month
            ano = datetime.now().year

        try:
            # Coletar dados do mês
            recs = []
            for r in self.receitas:
                try:
                    d = datetime.strptime(r[3], "%d/%m/%Y")
                    if d.month == mes and d.year == ano:
                        recs.append((*r, "Receita"))
                except Exception:
                    continue

            desps = []
            for d in self.despesas:
                try:
                    dt = datetime.strptime(d[3], "%d/%m/%Y")
                    if dt.month == mes and dt.year == ano:
                        desps.append((*d, "Despesa"))
                except Exception:
                    continue

            if not recs and not desps:
                messagebox.showinfo("Exportar", "Nenhuma transação para exportar neste mês.")
                return

            # Criar PDF
            dest = filedialog.asksaveasfilename(title="Salvar PDF do mês", defaultextension=".pdf", 
                                              initialfile=f"financas_{self.usuario}_{ano}_{mes:02d}.pdf")
            if not dest:
                return

            doc = SimpleDocTemplate(dest, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30
            )
            elements.append(Paragraph(f"Relatório Financeiro - {self.cb_mes.get()} de {ano}", title_style))
            
            # Tabela de Receitas
            if recs:
                elements.append(Paragraph("Receitas", styles["Heading2"]))
                data = [["Data", "Valor", "Descrição", "Categoria"]]
                for valor, desc, cat, data_s, _ in sorted(recs, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y")):
                    data.append([data_s, fmt_val(valor), desc, cat])
                
                t = Table(data, colWidths=[1*inch, 1.5*inch, 2.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

            # Tabela de Despesas
            if desps:
                elements.append(Paragraph("Despesas", styles["Heading2"]))
                data = [["Data", "Valor", "Descrição", "Categoria"]]
                for valor, desc, cat, data_s, _ in sorted(desps, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y")):
                    data.append([data_s, fmt_val(valor), desc, cat])
                
                t = Table(data, colWidths=[1*inch, 1.5*inch, 2.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.salmon),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

            # Resumo
            total_receitas = sum(r[0] for r in recs)
            total_despesas = sum(d[0] for d in desps)
            saldo = total_receitas - total_despesas

            elements.append(Paragraph("Resumo do Mês", styles["Heading2"]))
            resumo_data = [
                ["Total Receitas:", fmt_val(total_receitas)],
                ["Total Despesas:", fmt_val(total_despesas)],
                ["Saldo:", fmt_val(saldo)]
            ]
            t = Table(resumo_data, colWidths=[2*inch, 2*inch])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('TEXTCOLOR', (-1, -1), (-1, -1), colors.green if saldo >= 0 else colors.red)
            ]))
            elements.append(t)

            # Gerar PDF
            doc.build(elements)
            messagebox.showinfo("Exportar", f"PDF salvo em: {dest}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {e}")
        mes = self.cb_mes.current() + 1
        ano = int(self.cb_ano.get())
        try:
            # Coletar dados do mês
            recs = []
            desps = []
            
            # Processar receitas
            for r in self.receitas:
                try:
                    d = datetime.strptime(r[3], "%d/%m/%Y")
                    if d.month == mes and d.year == ano:
                        recs.append((*r, "Receita"))
                except Exception:
                    continue

            # Processar despesas
            for d in self.despesas:
                try:
                    dt = datetime.strptime(d[3], "%d/%m/%Y")
                    if dt.month == mes and dt.year == ano:
                        desps.append((*d, "Despesa"))
                except Exception:
                    continue

            if not recs and not desps:
                messagebox.showinfo("Exportar", "Nenhuma transação para exportar neste mês.")
                return

            # Criar PDF
            dest = filedialog.asksaveasfilename(
                title="Salvar PDF do mês",
                defaultextension=".pdf",
                initialfile=f"financas_{self.usuario}_{ano}_{mes:02d}.pdf"
            )
            if not dest:
                return

            # Configurar documento
            doc = SimpleDocTemplate(dest, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30
            )
            elements.append(Paragraph(f"Relatório Financeiro - {self.cb_mes.get()} de {ano}", title_style))
            elements.append(Spacer(1, 20))
            
            # Tabela de Receitas
            if recs:
                elements.append(Paragraph("Receitas", styles["Heading2"]))
                elements.append(Spacer(1, 10))
                
                data = [["Data", "Valor", "Descrição", "Categoria"]]
                sorted_recs = sorted(recs, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y"))
                
                for valor, desc, cat, data_s, _ in sorted_recs:
                    data.append([data_s, fmt_val(valor), desc, cat])
                
                t = Table(data, colWidths=[1*inch, 1.5*inch, 2.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

            # Tabela de Despesas
            if desps:
                elements.append(Paragraph("Despesas", styles["Heading2"]))
                elements.append(Spacer(1, 10))
                
                data = [["Data", "Valor", "Descrição", "Categoria"]]
                sorted_desps = sorted(desps, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y"))
                
                for valor, desc, cat, data_s, _ in sorted_desps:
                    data.append([data_s, fmt_val(valor), desc, cat])
                
                t = Table(data, colWidths=[1*inch, 1.5*inch, 2.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.salmon),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

            # Resumo
            total_receitas = sum(r[0] for r in recs)
            total_despesas = sum(d[0] for d in desps)
            saldo = total_receitas - total_despesas

            elements.append(Paragraph("Resumo do Mês", styles["Heading2"]))
            elements.append(Spacer(1, 10))
            
            resumo_data = [
                ["Total Receitas:", fmt_val(total_receitas)],
                ["Total Despesas:", fmt_val(total_despesas)],
                ["Saldo:", fmt_val(saldo)]
            ]
            
            t = Table(resumo_data, colWidths=[2*inch, 2*inch])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('TEXTCOLOR', (-1, -1), (-1, -1), colors.green if saldo >= 0 else colors.red)
            ]))
            elements.append(t)

            # Gerar PDF
            doc.build(elements)
            messagebox.showinfo("Exportar", f"PDF salvo em: {dest}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {str(e)}")

    def exportar_mes_csv(self):
        """Exporta os dados do mês atual em CSV organizado com Receitas e Despesas separadas."""
        try:
            mes = self.cb_mes.current() + 1
            ano = int(self.cb_ano.get())
        except Exception:
            mes = datetime.now().month
            ano = datetime.now().year
            
        # Filtrar receitas do mês
        recs = []
        for r in self.receitas:
            try:
                d = datetime.strptime(r[3], "%d/%m/%Y")
                if d.month == mes and d.year == ano:
                    recs.append(r)
            except Exception:
                continue
                
        # Filtrar despesas do mês
        desps = []
        for d in self.despesas:
            try:
                dt = datetime.strptime(d[3], "%d/%m/%Y")
                if dt.month == mes and dt.year == ano:
                    desps.append(d)
            except Exception:
                continue
                
        if not recs and not desps:
            messagebox.showinfo("Exportar", "Nenhuma transação para exportar neste mês.")
            return
        
        dest = filedialog.asksaveasfilename(
            title="Salvar CSV do mês", 
            defaultextension=".csv", 
            initialfile=f"financas_{self.usuario}_{ano}_{mes:02d}.csv"
        )
        if not dest:
            return
            
        try:
            with open(dest, "w", encoding="utf-8-sig", newline='') as f:
                # Cabeçalho do arquivo
                f.write(f"RELATÓRIO FINANCEIRO - {self.cb_mes.get().upper()} DE {ano}\n")
                f.write("\n")
                
                # Seção RECEITAS
                f.write("=== RECEITAS ===\n")
                f.write("Data;Valor;Descrição;Categoria\n")
                
                if recs:
                    # Ordenar por data
                    recs_sorted = sorted(recs, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y"))
                    for valor, desc, cat, data in recs_sorted:
                        f.write(f"{data};{valor:.2f};{desc};{cat}\n")
                else:
                    f.write("Nenhuma receita neste mês\n")
                
                f.write("\n")
                
                # Seção DESPESAS
                f.write("=== DESPESAS ===\n")
                f.write("Data;Valor;Descrição;Categoria\n")
                
                if desps:
                    # Ordenar por data
                    desps_sorted = sorted(desps, key=lambda x: datetime.strptime(x[3], "%d/%m/%Y"))
                    for valor, desc, cat, data in desps_sorted:
                        f.write(f"{data};{valor:.2f};{desc};{cat}\n")
                else:
                    f.write("Nenhuma despesa neste mês\n")
                
                f.write("\n")
                
                # Resumo
                total_receitas = sum(r[0] for r in recs)
                total_despesas = sum(d[0] for d in desps)
                saldo = total_receitas - total_despesas
                
                f.write("=== RESUMO DO MÊS ===\n")
                f.write(f"Total Receitas;{total_receitas:.2f}\n")
                f.write(f"Total Despesas;{total_despesas:.2f}\n")
                f.write(f"Saldo;{saldo:.2f}\n")
                
            messagebox.showinfo("Exportar", f"CSV salvo com sucesso em:\n{dest}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar CSV: {e}")

# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = FinancasProApp(root)
    root.mainloop()
