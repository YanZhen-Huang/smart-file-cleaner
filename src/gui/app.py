# -*- coding: utf-8 -*-
"""
智能文档清理器 - 桌面 GUI 主窗口
功能：目录/格式选择、过期规则、定时清理、报告查看、开机自启
"""

import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 项目根目录与 src
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    PROJECT_ROOT = Path(sys.executable).parent  # exe 所在目录：配置/报告/备份都放这里
    SRC_DIR = Path(sys._MEIPASS) / "src"        # 打包内的源码目录（只读，供动态加载）
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gui.scheduler import AutoCleanScheduler, is_valid_time

CONFIG_PATH = PROJECT_ROOT / "config" / "operation-config.json"

# 文件格式大类 → 扩展名集合（与 file_types_config 保持一致）
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


def _load_config() -> dict:
    """加载操作配置，缺省给默认值"""
    default = {
        "processing_config": {
            "processor_type": "smart_document",
            "cleaning_strategy": "age",
            "target_directories": [str(Path.home() / "Downloads")],
            "max_age_days": 30,
            "use_filename_date": True,
            "target_extensions": [],
            "safety_settings": {
                "create_backup": True,
                "backup_dir": "backups",
                "use_recycle_bin": True,
                "require_confirmation": False,
            },
        },
        "report_settings": {"generate_report": True, "output_dir": "reports"},
        "auto_clean": {"enabled": False, "time": "02:00", "start_with_windows": False},
    }
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # 合并默认值
            for k, v in default.items():
                cfg.setdefault(k, v)
            pc = cfg["processing_config"]
            for k, v in default["processing_config"].items():
                pc.setdefault(k, v)
            ss = pc["safety_settings"]
            for k, v in default["processing_config"]["safety_settings"].items():
                ss.setdefault(k, v)
            ac = cfg["auto_clean"]
            for k, v in default["auto_clean"].items():
                ac.setdefault(k, v)
            return cfg
    except Exception as e:
        print(f"加载配置失败: {e}")
    return default


def _save_config(cfg: dict):
    """保存操作配置"""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("保存失败", f"无法保存配置: {e}")


class CleanerGUI:
    def __init__(self, root: tk.Tk, start_tray=False):
        self.root = root
        self.cfg = _load_config()
        self.scheduler = None
        self.worker_thread = None
        self.keep_running = True  # 托盘模式下窗口关闭不退出

        root.title("智能文档清理器")
        root.geometry("860x680")
        root.minsize(720, 560)

        self._build_ui()
        self._load_to_ui()
        self._refresh_reports()
        self._apply_auto_clean()

        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------- UI 构建 ----------------
    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        # 顶部：目标目录
        dir_frame = ttk.LabelFrame(main, text="目标目录（可多个）", padding=6)
        dir_frame.pack(fill="x", **pad)
        self.dir_list = tk.Listbox(dir_frame, height=4)
        self.dir_list.pack(side="left", fill="x", expand=True, padx=(0, 6))
        dir_btns = ttk.Frame(dir_frame)
        dir_btns.pack(side="right", fill="y")
        ttk.Button(dir_btns, text="添加目录", command=self._add_dir).pack(fill="x", pady=2)
        ttk.Button(dir_btns, text="移除选中", command=self._remove_dir).pack(fill="x", pady=2)

        # 规则区
        rule_frame = ttk.LabelFrame(main, text="过期规则", padding=6)
        rule_frame.pack(fill="x", **pad)
        ttk.Label(rule_frame, text="过期天数:").grid(row=0, column=0, sticky="w")
        self.age_spin = ttk.Spinbox(rule_frame, from_=1, to=3650, width=6)
        self.age_spin.grid(row=0, column=1, sticky="w", padx=(2, 12))
        self.fname_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rule_frame, text="优先用文件名中的日期判定", variable=self.fname_var).grid(
            row=0, column=2, sticky="w")

        # 文件格式选择
        fmt_frame = ttk.LabelFrame(main, text="清理文件格式", padding=6)
        fmt_frame.pack(fill="x", **pad)
        self.fmt_vars = {}
        for i, (name, exts) in enumerate(FORMAT_GROUPS.items()):
            var = tk.BooleanVar(value=True)
            self.fmt_vars[name] = var
            ttk.Checkbutton(fmt_frame, text=f"{name} ({len(exts)} 种)", variable=var).grid(
                row=0, column=i, sticky="w", padx=6)
        ttk.Label(fmt_frame, text="自定义扩展名（逗号分隔）:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.custom_ext = ttk.Entry(fmt_frame, width=40)
        self.custom_ext.grid(row=1, column=1, columnspan=3, sticky="w", pady=(6, 0))

        # 安全选项
        safe_frame = ttk.LabelFrame(main, text="删除安全", padding=6)
        safe_frame.pack(fill="x", **pad)
        self.recycle_var = tk.BooleanVar(value=True)
        self.backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(safe_frame, text="移入回收站（可恢复）", variable=self.recycle_var).grid(
            row=0, column=0, sticky="w", padx=6)
        ttk.Checkbutton(safe_frame, text="删除前先备份到 backups 目录", variable=self.backup_var).grid(
            row=0, column=1, sticky="w", padx=6)

        # 定时 + 自启
        auto_frame = ttk.LabelFrame(main, text="定时与自启", padding=6)
        auto_frame.pack(fill="x", **pad)
        self.auto_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(auto_frame, text="每天定时自动清理", variable=self.auto_var).grid(
            row=0, column=0, sticky="w", padx=6)
        ttk.Label(auto_frame, text="时间:").grid(row=0, column=1, sticky="w")
        self.time_entry = ttk.Entry(auto_frame, width=6)
        self.time_entry.grid(row=0, column=2, sticky="w", padx=(2, 16))
        self.boot_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(auto_frame, text="开机自启（后台运行）", variable=self.boot_var,
                        command=self._toggle_autostart).grid(row=0, column=3, sticky="w", padx=6)

        # 操作按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", **pad)
        ttk.Button(btn_frame, text="保存设置", command=self._save_from_ui).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="立即预览", command=self._run_preview).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="立即清理", command=self._run_clean).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="打开配置目录", command=self._open_config_dir).pack(side="left", padx=4)

        # 报告区
        report_frame = ttk.LabelFrame(main, text="清理报告", padding=6)
        report_frame.pack(fill="both", expand=True, **pad)
        report_left = ttk.Frame(report_frame)
        report_left.pack(side="left", fill="y")
        ttk.Label(report_left, text="历史报告:").pack(anchor="w")
        self.report_list = tk.Listbox(report_left, width=30, height=8)
        self.report_list.pack(fill="y", padx=(0, 6))
        ttk.Button(report_left, text="查看选中", command=self._show_report).pack(fill="x", pady=2)
        ttk.Button(report_left, text="刷新", command=self._refresh_reports).pack(fill="x")

        # 日志输出
        self.log_text = scrolledtext.ScrolledText(report_frame, height=10, state="disabled", font=("Consolas", 9))
        self.log_text.pack(side="right", fill="both", expand=True)

    # ---------------- 配置读写 ----------------
    def _load_to_ui(self):
        pc = self.cfg["processing_config"]
        ac = self.cfg["auto_clean"]

        self.dir_list.delete(0, "end")
        for d in pc["target_directories"]:
            self.dir_list.insert("end", d)

        self.age_spin.delete(0, "end")
        self.age_spin.insert(0, str(pc.get("max_age_days", 30)))
        self.fname_var.set(pc.get("use_filename_date", True))

        # 文件格式回显：按当前 target_extensions 反推选中状态
        exts = set(pc.get("target_extensions", []))
        for name, group_exts in FORMAT_GROUPS.items():
            checked = bool(exts) and all(e in exts for e in group_exts)
            self.fmt_vars[name].set(checked)
        # 自定义扩展名 = 不属于任何大类的扩展名
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

    def _save_from_ui(self):
        """把界面值写回配置并保存"""
        pc = self.cfg["processing_config"]
        ac = self.cfg["auto_clean"]

        dirs = list(self.dir_list.get(0, "end"))
        if not dirs:
            messagebox.showwarning("提示", "请至少添加一个目标目录")
            return
        pc["target_directories"] = dirs

        try:
            pc["max_age_days"] = max(1, int(self.age_spin.get()))
        except ValueError:
            messagebox.showwarning("提示", "过期天数必须是数字")
            return
        pc["use_filename_date"] = self.fname_var.get()

        # 组装扩展名
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
        self._log("✅ 配置已保存")
        messagebox.showinfo("完成", "配置已保存")

    # ---------------- 目录操作 ----------------
    def _add_dir(self):
        d = filedialog.askdirectory(title="选择要清理的目录")
        if d:
            self.dir_list.insert("end", d.replace("/", "\\"))

    def _remove_dir(self):
        sel = self.dir_list.curselection()
        if sel:
            self.dir_list.delete(sel[0])

    # ---------------- 定时调度 ----------------
    def _apply_auto_clean(self):
        """根据配置启动/停止/更新定时调度"""
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
            self._log(f"⏰ 定时清理已开启：每天 {run_time}")
        else:
            if self.scheduler:
                self.scheduler.stop()
                self.scheduler = None
            self._log("⏸ 定时清理已关闭")

    def _run_clean_bg(self):
        """定时触发的后台清理（不弹窗口）"""
        threading.Thread(target=self._run_clean, daemon=True).start()

    # ---------------- 执行清理 ----------------
    def _run_preview(self):
        self._save_from_ui()
        threading.Thread(target=self._run_cli, args=("preview",), daemon=True).start()

    def _run_clean(self):
        self._save_from_ui()
        threading.Thread(target=self._run_cli, args=("clean",), daemon=True).start()

    def _run_cli(self, mode: str):
        """在后台线程调用 main.py --auto / --preview 并捕获输出"""
        if IS_FROZEN:
            cmd = [sys.executable, "--" + mode]
        else:
            cmd = [sys.executable, str(PROJECT_ROOT / "main.py"), "--" + mode]
        self._log(f"▶ 执行{'预览' if mode == 'preview' else '清理'}...")
        try:
            proc = subprocess.Popen(
                cmd, cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in proc.stdout:
                if line.strip():
                    self._log(line.rstrip())
            proc.wait()
            self._log("🏁 执行完成" if proc.returncode == 0 else f"❌ 执行失败（退出码 {proc.returncode}）")
            self.root.after(300, self._refresh_reports)
        except Exception as e:
            self._log(f"❌ 执行异常: {e}")

    def _log(self, msg: str):
        def _append():
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(0, _append)

    # ---------------- 报告查看 ----------------
    def _refresh_reports(self):
        """列出 reports 目录下的报告文件"""
        report_dir = PROJECT_ROOT / self.cfg.get("report_settings", {}).get("output_dir", "reports")
        self.report_list.delete(0, "end")
        if report_dir.exists():
            for f in sorted(report_dir.glob("cleaning_report_*.json"), reverse=True):
                self.report_list.insert("end", f.name)

    def _show_report(self):
        sel = self.report_list.curselection()
        if not sel:
            messagebox.showinfo("提示", "请先选中一个报告")
            return
        name = self.report_list.get(sel[0])
        report_dir = PROJECT_ROOT / self.cfg.get("report_settings", {}).get("output_dir", "reports")
        path = report_dir / name
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 提取摘要
            lines = [f"报告: {name}", "=" * 50]
            for d in data.get("directories", []):
                lines.append(f"目录: {d.get('directory', '?')}")
                lines.append(f"  扫描 {d.get('total_files_scanned', 0)} 个，标记删除 {d.get('files_to_delete', 0)} 个")
                for f_info in d.get("deleted_files", []):
                    lines.append(f"  [删] {f_info.get('path')} ({f_info.get('size_formatted', '?')}) - {f_info.get('reason', '')}")
            self._log("\n".join(lines))
        except Exception as e:
            self._log(f"❌ 读取报告失败: {e}")

    # ---------------- 开机自启 ----------------
    def _toggle_autostart(self):
        """开机自启：写/删注册表 Run 键（后台模式 --tray）"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if IS_FROZEN:
                # 打包版：直接注册 exe 本身 + --tray（exe 无控制台窗口）
                exe = sys.executable
                cmd = f'"{exe}" --tray'
            else:
                # 源码版：pythonw 后台运行
                pythonw = str(Path(sys.executable).with_name("pythonw.exe"))
                cmd = f'"{pythonw}" "{PROJECT_ROOT / "main.py"}" --tray'
            if self.boot_var.get():
                winreg.SetValueEx(key, "SmartFileCleaner", 0, winreg.REG_SZ, cmd)
                self._log(f"🔛 已设置开机自启: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, "SmartFileCleaner")
                    self._log("🔙 已取消开机自启")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self._log(f"❌ 设置开机自启失败: {e}")
            messagebox.showerror("错误", f"设置开机自启失败: {e}")

    # ---------------- 窗口行为 ----------------
    def _open_config_dir(self):
        report_dir = PROJECT_ROOT / self.cfg.get("report_settings", {}).get("output_dir", "reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(report_dir))

    def _on_close(self):
        """关闭窗口：若开启了后台/托盘则隐藏，否则退出"""
        self._save_from_ui()
        self.root.withdraw()
        # 无托盘图标时（托盘不可用）直接退出
        self.root.destroy()


def run_gui():
    """启动 GUI 主窗口"""
    root = tk.Tk()
    app = CleanerGUI(root)
    root.mainloop()
