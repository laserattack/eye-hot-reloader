# SETTINGS START

EXECUTABLES_LIST = [
    {
        "BUILD_CMD": ["go", "build", "-o", "./bin1.exe", "./bin1.go"],
        "BINARY_PATH": "./bin1.exe"
    },
    {
        "BUILD_CMD": ["go", "build", "-o", "./bin2.exe", "./target2/bin2.go"],
        "BINARY_PATH": "./bin2.exe"
    },
    {
        "RUN_CMD": ["py", "./target2/target.py"],
        "SCRIPT_PATH": "./target2/target.py"
    },
]

TARGETS_LIST = [
    "./target/target123", 
    "./target/222.txt",
    "./target2/target.py",
]

DURATION = 1

# SETTINGS END

from abc import ABC, abstractmethod
import signal
import subprocess
import time
from datetime import datetime
from types import FrameType
from pathlib import Path
import sys

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

class Executable(ABC):
    @abstractmethod
    def start(self) -> bool: pass
    
    @abstractmethod
    def stop(self) -> None: pass

def create_executable(exec_config: dict) -> Executable:
    if "BUILD_CMD" in exec_config and "BINARY_PATH" in exec_config:
        return Binary(exec_config["BUILD_CMD"], Path(exec_config["BINARY_PATH"]))
    elif "RUN_CMD" in exec_config and "SCRIPT_PATH" in exec_config:
        return Script(exec_config["RUN_CMD"], Path(exec_config["SCRIPT_PATH"]))
    raise ValueError("incorrect configuration of the 'EXECUTABLES_LIST', check fields names")

class Script(Executable):
    def __init__(self, run_cmd: list[str], script_path: str):
        self._path = Path(script_path)
        self._run_cmd = run_cmd
        self._process = None
    
    def start(self) -> bool:        
        if not self._path.exists():
            pink(f"file '{self._path}' not found")
            return False
        blue(f"running command '{' '.join(self._run_cmd)}'...")
        try:
            self._process = subprocess.Popen(self._run_cmd)
            blue(f"run command process started with pid '{self._process.pid}'")
            return True
        except Exception as e:
            pink(f"run command error '{e}'")
            return False
        
    def stop(self) -> None:
        if self._process:
            blue(f"killing process '{' '.join(self._run_cmd)}' with pid '{self._process.pid}'...")
            try:
                self._process.kill()
                tcode = self._process.wait(timeout=5)
                blue(f"process died with code {tcode:#X}")
            except Exception as e:
                pink(f"process termination error '{e}'")

    def __del__(self):
        if self._process and self._process.poll() is None:
            self._process.kill()

class Binary(Executable):
    def __init__(self, build_cmd: list[str], binary_path: str):
        self._path = Path(binary_path)
        self._build_cmd = build_cmd
        self._process = None

    def start(self) -> bool:
        if not self._build():
            pink(f"the executable file '{self._path}' specified in 'EXECUTABLES_LIST' was not built as result of its build command")
            return False
        return self._run_process()

    def stop(self) -> None:
        self._terminate_process()
        self._delete_file()

    def _build(self) -> bool:
        blue(f"running build command '{' '.join(self._build_cmd)}'...")    
        try:
            subprocess.run(self._build_cmd, check=True)
            blue(f"build command executed")
        except subprocess.CalledProcessError as e:
            pink(f"build command error '{e}'")
            return False

        if not self._path.exists():
            pink(f"file '{self._path}' not found")
            return False
        else:
            return True

    def _run_process(self) -> bool:
        blue(f"starting '{self._path}'...")
        try:
            self._process = subprocess.Popen([self._path.absolute()])
            blue(f"process started with pid '{self._process.pid}'")
            return True
        except FileNotFoundError:
            pink(f"file '{self._path}' not found")
            return False
        except Exception as e:
            pink(f"start error '{e}'")
            return False

    def _terminate_process(self) -> None:
        if self._process:
            blue(f"killing process '{self._path}' with pid '{self._process.pid}'...")
            try:
                self._process.kill()
                tcode = self._process.wait(timeout=5)
                blue(f"process died with code {tcode:#X}")
            except Exception as e:
                pink(f"process termination error '{e}'")

    def _delete_file(self) -> None:
        max_attempts = 10
        timeout_ms = 300
        for attempt in range(max_attempts):
            try:
                blue(f"deleting file '{self._path}' (attempt {attempt + 1}/{max_attempts})...")
                self._path.unlink()
                blue(f"file deleted")
                break
            except FileNotFoundError:
                pink(f"file not found")
                break
            except Exception as e:
                if attempt == max_attempts - 1: 
                    pink(f"file deletion error '{e}'")
                else:
                    pink(f"delete error '{e}'")
                    pink(f"retrying in {timeout_ms}ms...")
                    time.sleep(timeout_ms / 1000)
    
    def __del__(self):
        if self._process and self._process.poll() is None:
            self._process.kill()

class Config:
    def __init__(self, executables_list: list[Executable], targets_list: list[Target], duration: int):
        self._duration = duration
        self._executables = executables_list
        self._targets = targets_list
    
    @property
    def duration(self) -> int: return self._duration

    @property
    def executables(self) -> list[Executable]: return self._executables

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
        for e in self.config.executables:
            status = e.start()
            blue()
            if not status:
                self.cleanup()

    def stop_all(self) -> None:
        for e in self.config.executables:
            e.stop()
            blue()

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
                        blue("restarting...")
                        self.restart_all()
                        target.mtime = last_mtime
                time.sleep(self.config.duration)
        except Exception as e:
            pink(f"fatal error in main '{e}'")
            self.cleanup()

def main():
    try:
        try: 
            executables_list = [create_executable(exec) for exec in EXECUTABLES_LIST]
        except ValueError as e: 
            pink(f"configuration error '{e}'")
            sys.exit(1)
            
        targets_list = [Target(target) for target in TARGETS_LIST]
        if missing := [t.path for t in targets_list if not t.path.exists()]:
            pink(f"non-existent targets: {', '.join(map(str, missing))}")
            sys.exit(1)
        
        config = Config(executables_list, targets_list, DURATION)
        Watcher(config).main()
    finally:
        blue("see you later!")

def hide_control_chars() -> None:
    # Если терминала нет - выход (например если скрипт запустился на сервере)
    if not sys.stdin.isatty():
        return
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
            raise RuntimeError("failed to enable ANSI colors") from e

def blue(message: str = "") -> None:
    color_print(message, "\033[1;34m")

def pink(message: str = "") -> None:
    color_print(message, "\033[1;35m")

def color_print(message: str, ansi_color: str) -> None:
    current_time = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"{current_time} - voyeur | {message}"
    
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

if __name__ == "__main__":
    main()