# -*- coding: utf-8 -*-
"""
智能文档清理器 - 桌面 GUI 主窗口
暗色主题 · 脉冲状态灯 · 进度条 · 扫描动画
"""

import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 项目根目录与 src
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    PROJECT_ROOT = Path(sys.executable).parent
    SRC_DIR = Path(sys._MEIPASS) / "src"
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gui.scheduler import AutoCleanScheduler, is_valid_time

CONFIG_PATH = PROJECT_ROOT / "config" / "operation-config.json"

# ── 文件格式大类 ─────────────────────────────────────────────
FORMAT_GROUPS = {
    "文档": [".txt", ".doc", ".docx", ".pdf", ".rtf", ".odt", ".pages",
             ".xls", ".xlsx", ".ppt", ".pptx", ".odp", ".ods",
             ".md", ".markdown", ".rst", ".tex", ".latex"],
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
             ".webp", ".svg", ".ico", ".psd", ".ai", ".eps", ".raw",
             ".cr2", ".nef", ".arw", ".dng", ".heic", ".heif"],
    "临时": [".tmp", ".temp", ".log", ".bak", ".backup", ".old", ".cache",
             ".thumbs.db", ".ds_store", ".desktop.ini", ".dmp", ".crash"],
}

# ── 暗色主题调色板 ──────────────────────────────────────────
BG       = "#1e1e2e"    # 主背景
BG2      = "#282a3a"    # 卡片/框架背景
BG3      = "#313244"    # 输入框/列表框
FG       = "#cdd6f4"    # 主文字
FG2      = "#a6adc8"    # 次要文字
ACCENT   = "#89b4fa"    # 强调色（蓝）
GREEN    = "#a6e3a1"    # 成功
RED      = "#f38ba8"    # 错误
YELLOW   = "#f9e2af"    # 警告
SURFACE  = "#45475a"    # 悬浮/边框

# 扫描动画符号（旋转斜杠）
SCAN_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


# ── 配置读写 ─────────────────────────────────────────────────
def _load_config() -> dict:
    default = {
        "processing_config": {
            "processor_type": "smart_document",
            "cleaning_strategy": "age",
            "target_directories": [str(Path.home() / "Downloads")],
            "max_age_days": 30,
            "use_filename_date": True,
            "target_extensions": [],
            "safety_settings": {
                "create_backup": True, "backup_dir": "backups",
                "use_recycle_bin": True, "require_confirmation": False,
            },
        },
        "report_settings": {"generate_report": True, "output_dir": "reports"},
        "auto_clean": {"enabled": False, "time": "02:00", "start_with_windows": False},
    }
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # 逐层合并默认值
            for k, v in default.items():
                cfg.setdefault(k, v)
            for section in ("processing_config", "report_settings", "auto_clean"):
                for k, v in default[section].items():
                    cfg[section].setdefault(k, v)
            for k, v in default["processing_config"].items():
                cfg["processing_config"].setdefault(k, v)
            for k, v in default["processing_config"]["safety_settings"].items():
                cfg["processing_config"]["safety_settings"].setdefault(k, v)
            return cfg
    except Exception as e:
        print(f"加载配置失败: {e}")
    return default


def _save_config(cfg: dict):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")


# ── 主窗口 ──────────────────────────────────────────────────
class CleanerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = _load_config()
        self.scheduler = None
        self.worker_thread = None
        self._running = False          # 是否有操作在跑
        self._scan_frame = 0           # 动画帧索引
        self._pulse_on = True          # 脉冲开关

        root.title("智能文档清理器")
        root.geometry("880x700")
        root.minsize(740, 580)
        root.configure(bg=BG)

        self._apply_theme()
        self._build_ui()
        self._load_to_ui()
        self._refresh_reports()
        self._apply_auto_clean()
        self._start_clock()

        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── 主题 ──────────────────────────────────────────────
    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG, foreground=FG, fieldbackground=BG3,
                         borderwidth=0, troughcolor=BG3)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TCheckbutton", background=BG, foreground=FG,
                         indicatorcolor=BG3, focuscolor=ACCENT)
        style.map("TCheckbutton", indicatorcolor=[("selected", ACCENT)])
        style.configure("Card.TFrame", background=BG2)
        style.configure("Card.TLabel", background=BG2, foreground=FG)
        style.configure("CardTitle.TLabel", background=BG2, foreground=ACCENT,
                         font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("CardDesc.TLabel", background=BG2, foreground=FG2,
                         font=("Microsoft YaHei UI", 9))
        style.configure("Accent.TButton", background=ACCENT, foreground="#1e1e2e",
                         font=("Microsoft YaHei UI", 10, "bold"), padding=(12, 6))
        style.map("Accent.TButton",
                  background=[("active", "#b4d0fb"), ("disabled", SURFACE)])
        style.configure("Danger.TButton", background=RED, foreground="#1e1e2e",
                         font=("Microsoft YaHei UI", 10, "bold"), padding=(12, 6))
        style.map("Danger.TButton",
                  background=[("active", "#f5a0b8"), ("disabled", SURFACE)])
        style.configure("Flat.TButton", background=BG3, foreground=FG,
                         padding=(10, 4))
        style.map("Flat.TButton",
                  background=[("active", SURFACE), ("disabled", BG3)])
        style.configure("Status.TLabel", background=BG2, foreground=GREEN,
                         font=("Consolas", 11))
        style.configure("Clock.TLabel", background=BG2, foreground=FG2,
                         font=("Consolas", 10))

        # 进度条
        style.configure("Accent.Horizontal.TProgressbar",
                         troughcolor=BG3, background=ACCENT, thickness=6)

    # ── UI 构建 ──────────────────────────────────────────
    def _build_ui(self):
        # 顶部状态栏
        self._build_status_bar()

        # 主容器（可滚动区域其实不需要，880x700 够了）
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        # ── 左右两列 ────────────────────────────────────
        left = tk.Frame(main, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        right = tk.Frame(main, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(7, 0))

        # ── 左列 ────────────────────────────────────────
        self._build_dir_card(left)
        self._build_rule_card(left)
        self._build_format_card(left)

        # ── 右列 ────────────────────────────────────────
        self._build_safe_card(right)
        self._build_auto_card(right)
        self._build_btn_card(right)

        # ── 底部：报告 + 日志 ───────────────────────────
        self._build_bottom(main)

    # ── 状态栏 ──────────────────────────────────────────
    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=BG2, height=36)
        bar.pack(fill="x", padx=14, pady=(6, 4))
        bar.pack_propagate(False)

        self._status_dot = tk.Label(bar, text="●", bg=BG2, fg=GREEN,
                                     font=("Consolas", 12))
        self._status_dot.pack(side="left", padx=(10, 4))

        self._status_text = tk.Label(bar, text="就绪", bg=BG2, fg=FG2,
                                      font=("Microsoft YaHei UI", 10))
        self._status_text.pack(side="left", padx=(0, 8))

        self._progress = ttk.Progressbar(bar, style="Accent.Horizontal.TProgressbar",
                                          orient="horizontal", mode="indeterminate", length=120)
        self._progress.pack(side="right", padx=(0, 10))

        self._clock_label = tk.Label(bar, text="", bg=BG2, fg=FG2,
                                      font=("Consolas", 10))
        self._clock_label.pack(side="right", padx=(0, 12))

    def _start_clock(self):
        """右上角实时时钟"""
        now = time.strftime("%H:%M:%S")
        self._clock_label.config(text=now)
        self.root.after(1000, self._start_clock)

    # ── 目录卡片 ────────────────────────────────────────
    def _build_dir_card(self, parent):
        card = tk.Frame(parent, bg=BG2, highlightbackground=SURFACE,
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 7))

        tk.Label(card, text="📂 目标目录", bg=BG2, fg=ACCENT,
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=10, pady=(8, 2))

        body = tk.Frame(card, bg=BG2)
        body.pack(fill="x", padx=10, pady=(0, 8))

        self.dir_list = tk.Listbox(body, height=3, bg=BG3, fg=FG,
                                    selectbackground=ACCENT, selectforeground="#1e1e2e",
                                    highlightthickness=0, borderwidth=0,
                                    font=("Consolas", 9))
        self.dir_list.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btns = tk.Frame(body, bg=BG2)
        btns.pack(side="right", fill="y")
        ttk.Button(btns, text="＋ 添加", style="Flat.TButton",
                   command=self._add_dir).pack(fill="x", pady=1)
        ttk.Button(btns, text="－ 移除", style="Flat.TButton",
                   command=self._remove_dir).pack(fill="x", pady=1)

    # ── 规则卡片 ────────────────────────────────────────
    def _build_rule_card(self, parent):
        card = tk.Frame(parent, bg=BG2, highlightbackground=SURFACE,
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 7))

        tk.Label(card, text="⏱ 过期规则", bg=BG2, fg=ACCENT,
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=10, pady=(8, 2))

        body = tk.Frame(card, bg=BG2)
        body.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(body, text="超过", bg=BG2, fg=FG).pack(side="left")
        self.age_spin = tk.Spinbox(body, from_=1, to=3650, width=5,
                                    bg=BG3, fg=FG, buttonbackground=SURFACE,
                                    insertbackground=FG, highlightthickness=0,
                                    borderwidth=0, font=("Consolas", 10))
        self.age_spin.pack(side="left", padx=4)
        tk.Label(body, text="天删除", bg=BG2, fg=FG).pack(side="left", padx=(0, 12))

        self.fname_var = tk.BooleanVar(value=True)
        tk.Checkbutton(body, text="优先用文件名日期", variable=self.fname_var,
                        bg=BG2, fg=FG, selectcolor=BG3, activebackground=BG2,
                        font=("Microsoft YaHei UI", 9)).pack(side="left")

    # ── 格式卡片 ────────────────────────────────────────
    def _build_format_card(self, parent):
        card = tk.Frame(parent, bg=BG2, highlightbackground=SURFACE,
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 7))

        tk.Label(card, text="📄 清理文件格式", bg=BG2, fg=ACCENT,
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=10, pady=(8, 2))

        body = tk.Frame(card, bg=BG2)
        body.pack(fill="x", padx=10, pady=(0, 4))

        self.fmt_vars = {}
        for i, (name, exts) in enumerate(FORMAT_GROUPS.items()):
            var = tk.BooleanVar(value=True)
            self.fmt_vars[name] = var
            tk.Checkbutton(body, text=f"{name} ({len(exts)})",
                            variable=var, bg=BG2, fg=FG, selectcolor=BG3,
                            activebackground=BG2,
                            font=("Microsoft YaHei UI", 9)).grid(
                row=0, column=i, sticky="w", padx=6)

        body2 = tk.Frame(card, bg=BG2)
        body2.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(body2, text="自定义:", bg=BG2, fg=FG2,
                  font=("Microsoft YaHei UI", 9)).pack(side="left")
        self.custom_ext = tk.Entry(body2, bg=BG3, fg=FG, insertbackground=FG,
                                    highlightthickness=0, borderwidth=0,
                                    font=("Consolas", 9))
        self.custom_ext.pack(side="left", fill="x", expand=True, padx=6)

    # ── 安全卡片 ────────────────────────────────────────
    def _build_safe_card(self, parent):
        card = tk.Frame(parent, bg=BG2, highlightbackground=SURFACE,
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 7))

        tk.Label(card, text="🛡 删除安全", bg=BG2, fg=ACCENT,
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=10, pady=(8, 2))

        body = tk.Frame(card, bg=BG2)
        body.pack(fill="x", padx=10, pady=(0, 8))

        self.recycle_var = tk.BooleanVar(value=True)
        self.backup_var = tk.BooleanVar(value=True)
        tk.Checkbutton(body, text="移入回收站", variable=self.recycle_var,
                        bg=BG2, fg=FG, selectcolor=BG3, activebackground=BG2,
                        font=("Microsoft YaHei UI", 9)).pack(anchor="w")
        tk.Checkbutton(body, text="删除前备份", variable=self.backup_var,
                        bg=BG2, fg=FG, selectcolor=BG3, activebackground=BG2,
                        font=("Microsoft YaHei UI", 9)).pack(anchor="w")

    # ── 定时卡片 ────────────────────────────────────────
    def _build_auto_card(self, parent):
        card = tk.Frame(parent, bg=BG2, highlightbackground=SURFACE,
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 7))

        tk.Label(card, text="⏰ 定时与自启", bg=BG2, fg=ACCENT,
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=10, pady=(8, 2))

        body = tk.Frame(card, bg=BG2)
        body.pack(fill="x", padx=10, pady=(0, 8))

        self.auto_var = tk.BooleanVar(value=False)
        tk.Checkbutton(body, text="定时清理", variable=self.auto_var,
                        bg=BG2, fg=FG, selectcolor=BG3, activebackground=BG2,
                        font=("Microsoft YaHei UI", 9)).pack(side="left")

        tk.Label(body, text="时间", bg=BG2, fg=FG2,
                  font=("Microsoft YaHei UI", 9)).pack(side="left", padx=(10, 2))
        self.time_entry = tk.Entry(body, width=6, bg=BG3, fg=FG,
                                    insertbackground=FG, highlightthickness=0,
                                    borderwidth=0, font=("Consolas", 10))
        self.time_entry.pack(side="left", padx=(0, 12))

        self.boot_var = tk.BooleanVar(value=False)
        tk.Checkbutton(body, text="开机自启", variable=self.boot_var,
                        command=self._toggle_autostart,
                        bg=BG2, fg=FG, selectcolor=BG3, activebackground=BG2,
                        font=("Microsoft YaHei UI", 9)).pack(side="left")

    # ── 按钮卡片 ────────────────────────────────────────
    def _build_btn_card(self, parent):
        card = tk.Frame(parent, bg=BG2, highlightbackground=SURFACE,
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 7))

        tk.Label(card, text="⚡ 操作", bg=BG2, fg=ACCENT,
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=10, pady=(8, 2))

        body = tk.Frame(card, bg=BG2)
        body.pack(fill="x", padx=10, pady=(0, 8))

        self._btn_save = ttk.Button(body, text="保存设置", style="Flat.TButton",
                                     command=self._save_from_ui)
        self._btn_save.pack(side="left", padx=2)

        self._btn_preview = ttk.Button(body, text="立即预览", style="Accent.TButton",
                                        command=self._run_preview)
        self._btn_preview.pack(side="left", padx=2)

        self._btn_clean = ttk.Button(body, text="立即清理", style="Danger.TButton",
                                      command=self._run_clean)
        self._btn_clean.pack(side="left", padx=2)

    # ── 底部：报告 + 日志 ────────────────────────────────
    def _build_bottom(self, parent):
        bottom = tk.Frame(parent, bg=BG)
        bottom.pack(fill="both", expand=True, pady=(4, 0))

        # 左：报告列表
        left = tk.Frame(bottom, bg=BG2, highlightbackground=SURFACE,
                         highlightthickness=1, width=240)
        left.pack(side="left", fill="y", padx=(0, 7))
        left.pack_propagate(False)

        tk.Label(left, text="📋 清理报告", bg=BG2, fg=ACCENT,
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=8, pady=(8, 4))

        self.report_list = tk.Listbox(left, bg=BG3, fg=FG,
                                       selectbackground=ACCENT, selectforeground="#1e1e2e",
                                       highlightthickness=0, borderwidth=0,
                                       font=("Consolas", 9), height=8)
        self.report_list.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        rpt_btns = tk.Frame(left, bg=BG2)
        rpt_btns.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(rpt_btns, text="查看", style="Flat.TButton",
                   command=self._show_report).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Button(rpt_btns, text="刷新", style="Flat.TButton",
                   command=self._refresh_reports).pack(side="left", expand=True, fill="x", padx=1)

        # 右：日志
        right = tk.Frame(bottom, bg=BG2, highlightbackground=SURFACE,
                          highlightthickness=1)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="📜 执行日志", bg=BG2, fg=ACCENT,
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=8, pady=(8, 4))

        self.log_text = tk.Text(right, bg=BG3, fg=FG, insertbackground=FG,
                                 highlightthickness=0, borderwidth=0,
                                 font=("Consolas", 9), wrap="word",
                                 state="disabled", relief="flat")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ── 配置 ↔ UI ──────────────────────────────────────
    def _load_to_ui(self):
        pc = self.cfg["processing_config"]
        ac = self.cfg["auto_clean"]

        self.dir_list.delete(0, "end")
        for d in pc["target_directories"]:
            self.dir_list.insert("end", d)

        self.age_spin.delete(0, "end")
        self.age_spin.insert(0, str(pc.get("max_age_days", 30)))
        self.fname_var.set(pc.get("use_filename_date", True))

        exts = set(pc.get("target_extensions", []))
        for name, group_exts in FORMAT_GROUPS.items():
            checked = bool(exts) and all(e in exts for e in group_exts)
            self.fmt_vars[name].set(checked)
        known = set()
        for group_exts in FORMAT_GROUPS.values():
            known.update(group_exts)
        custom = [e for e in exts if e not in known]
        self.custom_ext.delete(0, "end")
        self.custom_ext.insert(0, ", ".join(custom))

        ss = pc["safety_settings"]
        self.recycle_var.set(ss.get("use_recycle_bin", True))
        self.backup_var.set(ss.get("create_backup", True))

        self.auto_var.set(ac.get("enabled", False))
        self.time_entry.delete(0, "end")
        self.time_entry.insert(0, ac.get("time", "02:00"))
        self.boot_var.set(ac.get("start_with_windows", False))

    def _save_from_ui(self, silent=False):
        pc = self.cfg["processing_config"]
        ac = self.cfg["auto_clean"]

        dirs = list(self.dir_list.get(0, "end"))
        if not dirs:
            if not silent:
                messagebox.showwarning("提示", "请至少添加一个目标目录")
            return False
        pc["target_directories"] = dirs

        try:
            pc["max_age_days"] = max(1, int(self.age_spin.get()))
        except ValueError:
            if not silent:
                messagebox.showwarning("提示", "过期天数必须是数字")
            return False
        pc["use_filename_date"] = self.fname_var.get()

        exts = []
        for name, group_exts in FORMAT_GROUPS.items():
            if self.fmt_vars[name].get():
                exts.extend(group_exts)
        custom = [e.strip().lower() for e in self.custom_ext.get().split(",") if e.strip()]
        for e in custom:
            if not e.startswith("."):
                e = "." + e
            if e not in exts:
                exts.append(e)
        pc["target_extensions"] = exts

        ss = pc["safety_settings"]
        ss["use_recycle_bin"] = self.recycle_var.get()
        ss["create_backup"] = self.backup_var.get()

        ac["enabled"] = self.auto_var.get()
        ac["time"] = self.time_entry.get().strip()

        _save_config(self.cfg)
        self._apply_auto_clean()
        if not silent:
            self._log("配置已保存")
        return True

    # ── 目录操作 ────────────────────────────────────────
    def _add_dir(self):
        d = filedialog.askdirectory(title="选择要清理的目录")
        if d:
            self.dir_list.insert("end", d.replace("/", "\\"))
            self._log(f"添加目录: {d}")

    def _remove_dir(self):
        sel = self.dir_list.curselection()
        if sel:
            removed = self.dir_list.get(sel[0])
            self.dir_list.delete(sel[0])
            self._log(f"移除目录: {removed}")

    # ── 定时调度 ────────────────────────────────────────
    def _apply_auto_clean(self):
        enabled = self.auto_var.get()
        run_time = self.time_entry.get().strip()
        if not is_valid_time(run_time):
            run_time = "02:00"
            self.time_entry.delete(0, "end")
            self.time_entry.insert(0, run_time)

        if enabled:
            if self.scheduler is None:
                self.scheduler = AutoCleanScheduler(run_time, callback=self._run_clean_bg)
                self.scheduler.start()
            else:
                self.scheduler.update_time(run_time)
            self._set_status(f"定时清理: 每天 {run_time}", "timer")
        else:
            if self.scheduler:
                self.scheduler.stop()
                self.scheduler = None
            self._set_status("定时清理已关闭", "idle")

    def _run_clean_bg(self):
        threading.Thread(target=self._run_clean, daemon=True).start()

    # ── 操作控制 ────────────────────────────────────────
    def _set_running(self, running: bool, label: str = ""):
        """切换运行状态：禁止/启用按钮，启动/停止脉冲动画"""
        self._running = running
        state = "disabled" if running else "normal"
        self._btn_preview.config(state=state)
        self._btn_clean.config(state=state)
        if running:
            self._set_status(label or "运行中...", "running")
            self._progress.start(12)
            self._animate_scan()
        else:
            self._progress.stop()
            self._set_status("就绪", "idle")

    def _set_status(self, text: str, mode: str = "idle"):
        color_map = {"idle": GREEN, "running": YELLOW, "timer": ACCENT, "error": RED}
        dot_map = {"idle": "●", "running": "◉", "timer": "◎", "error": "✖"}
        self._status_dot.config(fg=color_map.get(mode, FG))
        self._status_text.config(text=f" {dot_map.get(mode, '●')} {text}")

    def _animate_scan(self):
        """脉冲动画：旋转符号 + 交替颜色"""
        if not self._running:
            return
        frame = SCAN_FRAMES[self._scan_frame % len(SCAN_FRAMES)]
        self._status_dot.config(text=frame)
        self._scan_frame += 1
        self.root.after(100, self._animate_scan)

    # ── 执行预览 / 清理 ────────────────────────────────
    def _run_preview(self):
        if not self._save_from_ui(silent=True):
            return
        self._set_running(True, "预览扫描中...")
        self.worker_thread = threading.Thread(target=self._run_cli, args=("preview",), daemon=True)
        self.worker_thread.start()

    def _run_clean(self):
        if not self._save_from_ui(silent=True):
            return
        self._set_running(True, "清理执行中...")
        self.worker_thread = threading.Thread(target=self._run_cli, args=("clean",), daemon=True)
        self.worker_thread.start()

    def _run_cli(self, mode: str):
        if IS_FROZEN:
            cmd = [sys.executable, "--" + mode]
        else:
            cmd = [sys.executable, str(PROJECT_ROOT / "main.py"), "--" + mode]
        label = "预览" if mode == "preview" else "清理"
        self.root.after(0, lambda: self._log(f">> 执行{label}..."))
        try:
            proc = subprocess.Popen(
                cmd, cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in proc.stdout:
                if line.strip():
                    self._log(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                self.root.after(0, lambda: self._log("完成"))
            else:
                self.root.after(0, lambda: self._log(f"失败 (退出码 {proc.returncode})"))
            self.root.after(300, self._refresh_reports)
        except Exception as e:
            self.root.after(0, lambda: self._log(f"异常: {e}"))
        finally:
            self.root.after(0, lambda: self._set_running(False))

    def _log(self, msg: str):
        def _append():
            self.log_text.config(state="normal")
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{ts}] {msg}\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(0, _append)

    # ── 报告 ────────────────────────────────────────────
    def _refresh_reports(self):
        report_dir = PROJECT_ROOT / self.cfg.get("report_settings", {}).get("output_dir", "reports")
        self.report_list.delete(0, "end")
        if report_dir.exists():
            for f in sorted(report_dir.glob("cleaning_report_*.json"), reverse=True):
                self.report_list.insert("end", f.name)

    def _show_report(self):
        sel = self.report_list.curselection()
        if not sel:
            return
        name = self.report_list.get(sel[0])
        report_dir = PROJECT_ROOT / self.cfg.get("report_settings", {}).get("output_dir", "reports")
        path = report_dir / name
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lines = [f"=== {name} ==="]
            for d in data.get("directories", []):
                lines.append(f"目录: {d.get('directory', '?')}")
                lines.append(f"  扫描 {d.get('total_files_scanned', 0)} 个，"
                             f"删除 {d.get('files_to_delete', 0)} 个")
                for f_info in d.get("deleted_files", []):
                    lines.append(f"  [删] {f_info.get('path')} "
                                 f"({f_info.get('size_formatted', '?')}) "
                                 f"- {f_info.get('reason', '')}")
            self._log("\n".join(lines))
        except Exception as e:
            self._log(f"读取报告失败: {e}")

    # ── 开机自启 ────────────────────────────────────────
    def _toggle_autostart(self):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            if IS_FROZEN:
                exe = sys.executable
                cmd = f'"{exe}" --tray'
            else:
                pythonw = str(Path(sys.executable).with_name("pythonw.exe"))
                cmd = f'"{pythonw}" "{PROJECT_ROOT / "main.py"}" --tray'
            if self.boot_var.get():
                winreg.SetValueEx(key, "SmartFileCleaner", 0, winreg.REG_SZ, cmd)
                self._log(f"已设置开机自启")
            else:
                try:
                    winreg.DeleteValue(key, "SmartFileCleaner")
                    self._log("已取消开机自启")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self._log(f"开机自启设置失败: {e}")

    # ── 窗口行为 ────────────────────────────────────────
    def _open_report_dir(self):
        report_dir = PROJECT_ROOT / self.cfg.get("report_settings", {}).get("output_dir", "reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(report_dir))

    def _on_close(self):
        self._save_from_ui(silent=True)
        if self.scheduler:
            self.scheduler.stop()
        self.root.destroy()


def run_gui():
    root = tk.Tk()
    CleanerGUI(root)
    root.mainloop()
