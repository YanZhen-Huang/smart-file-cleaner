# -*- coding: utf-8 -*-
"""
内置定时调度器
在应用内按配置的时间每天自动执行清理（不依赖系统任务计划）
"""

import threading
import time
from datetime import datetime, timedelta


class AutoCleanScheduler:
    """
    每天固定时间自动清理的调度器

    用法:
        scheduler = AutoCleanScheduler("02:00", on_fire)
        scheduler.start()   # 后台线程启动
        scheduler.stop()    # 停止
        scheduler.update_time("06:30")  # 运行中改时间
    """

    def __init__(self, run_time: str = "02:00", callback=None):
        """
        Args:
            run_time (str): 每天执行时间 "HH:MM"
            callback (callable): 到点触发的回调，无参数
        """
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self.callback = callback
        self._set_time(run_time)

    def _set_time(self, run_time: str):
        """解析并保存 HH:MM"""
        try:
            h, m = run_time.strip().split(":")
            self.hour = int(h)
            self.minute = int(m)
        except (ValueError, AttributeError):
            self.hour, self.minute = 2, 0

    @property
    def run_time(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def update_time(self, run_time: str):
        """运行中更新执行时间"""
        with self._lock:
            self._set_time(run_time)

    def start(self):
        """启动调度线程"""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, name="auto-clean-scheduler", daemon=True)
            self._thread.start()
            print(f"✅ 定时调度已启动，每天 {self.run_time} 自动清理")

    def stop(self):
        """停止调度线程"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)
        print("🛑 定时调度已停止")

    def _loop(self):
        """主循环：睡眠到下一个执行点，触发回调"""
        last_run_date = None
        while not self._stop_event.is_set():
            now = datetime.now()
            with self._lock:
                hour, minute = self.hour, self.minute
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            self._stop_event.wait(timeout=wait_seconds)
            if self._stop_event.is_set():
                break

            today = datetime.now().date()
            if today != last_run_date:  # 防止补跑重复
                last_run_date = today
                try:
                    if self.callback:
                        print(f"⏰ 到达定时时间 {self.run_time}，触发自动清理")
                        self.callback()
                except Exception as e:
                    print(f"❌ 定时清理回调异常: {e}")


def is_valid_time(run_time: str) -> bool:
    """校验 HH:MM 格式"""
    try:
        h, m = run_time.strip().split(":")
        return 0 <= int(h) <= 23 and 0 <= int(m) <= 59
    except (ValueError, AttributeError):
        return False
