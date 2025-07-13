# SETTINGS START

BINARIES_LIST = [
    {
        "BUILD_CMD": ["go", "build", "-o", "./bin1.exe", "./bin1.go"],
        "BINARY_PATH": "./bin1.exe"
    },
    {
        "BUILD_CMD": ["go", "build", "-o", "./bin2.exe", "./1/bin2.go"],
        "BINARY_PATH": "./bin2.exe"
    },
]

TARGETS_LIST = [
    "./target/target123", 
    "./target/222.txt",
]

DURATION = 1

# SETTINGS END

import signal
import subprocess
import time
from datetime import datetime
from types import FrameType
from pathlib import Path
import sys

def hide_control_chars() -> None:
    if sys.platform != "win32":
        import termios
        fd = sys.stdin.fileno()
        # termios.tcgetattr(fd) считывает текущие атрибуты терминала в attrs
        attrs = termios.tcgetattr(fd)
        # attrs[3] соответствует локальным флагам (c_lflag в структуре termios)
        # ECHOCTL — это флаг, который управляет отображением управляющих символов (например, ^C для Ctrl+C).
        # ~termios.ECHOCTL инвертирует битовую маску, а &= применяет побитовое И, чтобы сбросить этот флаг
        attrs[3] &= ~termios.ECHOCTL
        termios.tcsetattr(fd, termios.TCSANOW, attrs)

def enable_windows_ansi() -> None:
    if sys.platform == "win32":
        try:
            # ctypes позволяет вызывать функции из динамических библиотек (DLL) Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Получение дескриптора стандартного вывода
            hStdOut = kernel32.GetStdHandle(-11)
            # mode = ctypes.c_ulong() — создаёт переменную типа unsigned long, куда запишется текущий режим консоли
            mode = ctypes.c_ulong()
            # ctypes.byref(mode) передаёт указатель на mode
            kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode))
            # 0x0004 — это константа ENABLE_VIRTUAL_TERMINAL_PROCESSING, которая включает:
            ## Обработку ANSI-последовательностей (\033[...m)
            ## Поддержку цветов, стилей (жирный, курсив), перемещения курсора и т. д.
            # |= — побитовое ИЛИ, добавляет флаг к текущему режиму
            mode.value |= 0x0004
            kernel32.SetConsoleMode(hStdOut, mode)
        except Exception as e:
            # Создаётся новое исключение типа RuntimeError с описанием "Failed to enable ANSI colors"
            # Это заменяет оригинальное низкоуровневое исключение (например, из ctypes) на более понятное
            raise RuntimeError("Failed to enable ANSI colors") from e

def blue(message: str) -> None:
    color_print(message, "\033[1;34m")

def pink(message: str) -> None:
    color_print(message, "\033[1;35m")

def color_print(message: str, ansi_color: str) -> None:
    current_time = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"{current_time} - EYE | {message}"
    
    try: 
        enable_windows_ansi()
        print(f"{ansi_color}{formatted_message}\033[0m")
    except Exception: 
        print(formatted_message)

def mtime(path: Path) -> float:
    return max(
        p.stat().st_mtime 
        for p in [path, *path.rglob('*')]
    )

class Target:
    def __init__(self, target_path):
        self._path = Path(target_path)
        self._mtime = 0.0
        
    @property
    def mtime(self) -> float: return self._mtime

    @property
    def path(self) -> Path: return self._path
    
    @mtime.setter
    def mtime(self, timestamp: float) -> None:
        self._mtime = timestamp

class Binary:
    def __init__(self, build_cmd: list[str], binary_path: str):
        self._path = Path(binary_path)
        self._build_cmd = build_cmd
        self._process = None

    def build_and_run(self) -> bool:
        blue(f"building '{self._path}'...")    
        try:
            subprocess.run(self._build_cmd, check=True)
            blue(f"file '{self._path}' was built")
        except subprocess.CalledProcessError as e:
            pink(f"build '{self._path}' error '{e}'")
            return False

        if not self._path.exists():
            pink(f"file '{self._path}' not found")
            return False
        
        blue(f"starting '{self._path}'...")
        try:
            self._process = subprocess.Popen([self._path.absolute()])
            blue(f"process '{self._path}' started with pid '{self._process.pid}'")
            return True
        except FileNotFoundError:
            pink(f"file '{self._path}' not found")
            return False
        except Exception as e:
            pink(f"start '{self._path}' error '{e}'")
            return False

    def stop_and_delete(self) -> None:
        if self._process:
            blue(f"killing process '{self._path}' with pid '{self._process.pid}'...")
            try:
                self._process.kill()
                tcode = self._process.wait(timeout=5)
                blue(f"process '{self._path}' exited with code '{tcode:#X}'")
            except Exception as e:
                pink(f"process '{self._path}' with pid '{self._process.pid}' termination error '{e}'")
        
        max_attempts = 10
        timeout_ms = 300
        for attempt in range(max_attempts):
            try:
                blue(f"deleting file '{self._path}' (attempt {attempt + 1}/{max_attempts})...")
                self._path.unlink()
                blue(f"file '{self._path}' deleted")
                break
            except FileNotFoundError:
                pink(f"file '{self._path}' not found")
                break
            except Exception as e:
                if attempt == max_attempts - 1: 
                    pink(f"file '{self._path}' deletion error '{e}'")
                else:
                    pink(f"delete '{self._path}' error: {e}")
                    pink(f"retrying in {timeout_ms}ms...")
                    time.sleep(timeout_ms / 1000)
    
    def __del__(self):
        if self._process and self._process.poll() is None:
            self._process.kill()

class Config:
    def __init__(self, binaries_list: list[Binary], targets_list: list[Target], duration: int):
        self._duration = duration
        self._binaries = binaries_list
        self._targets = targets_list
    
    @property
    def duration(self) -> int: return self._duration

    @property
    def binaries(self) -> list[Binary]: return self._binaries

    @property
    def targets(self) -> list[Target]: return self._targets

class Watcher:
    def __init__(self, config: Config):
        self.config = config

        hide_control_chars()
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
    def handle_signal(self, signum: int, frame: FrameType) -> None:
        del signum, frame
        self.cleanup()

    def cleanup(self) -> None:
        blue("cleanup...")
        self.stop_all()
        sys.exit(0)

    def start_all(self) -> None:
        for b in self.config.binaries:
            if not b.build_and_run():
                self.cleanup()

    def stop_all(self) -> None:
        for b in self.config.binaries:
            b.stop_and_delete()

    def restart_all(self) -> None:
        self.stop_all()
        self.start_all()
    
    def main(self) -> None:
        try:
            for target in self.config.targets:
                target.mtime = mtime(target.path)
            self.start_all()
            while True:
                for target in self.config.targets:
                    last_mtime = mtime(target.path)
                    if last_mtime > target.mtime:
                        blue(f"target '{target.path}' was changed")
                        blue("rebuilding...")
                        self.restart_all()
                        target.mtime = last_mtime
                time.sleep(self.config.duration)
        except Exception as e:
            pink(f"fatal error in main '{e}'")
            self.cleanup()

if __name__ == "__main__":
    try:
        binaries_list = [
            Binary(binary["BUILD_CMD"], Path(binary["BINARY_PATH"]))
            for binary in BINARIES_LIST
        ]
        targets_list = [Target(target) for target in TARGETS_LIST]
        if missing := [t.path for t in targets_list if not t.path.exists()]:
            pink(f"non-existent targets: {', '.join(map(str, missing))}")
            sys.exit(1)
        config = Config(binaries_list, targets_list, DURATION)
        Watcher(config).main()
    finally:
        blue("see you later!")