# SETTINGS START

BINARIES_LIST = [
    {
        "BUILD_CMD": ["go", "build", "-o", "./bin1.exe", "bin1.go"],
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

def enable_windows_ansi() -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hStdOut = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode))
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
    
    @property
    def path(self) -> Path: return self._path

    @property
    def build_cmd(self) -> list[str]: return self._build_cmd

    def build_and_run(self) -> None:
        blue("building...")    
        try:
            subprocess.run(self.build_cmd, check=True)
        except subprocess.CalledProcessError as e:
            pink(f"build error '{e}'")

        if not self._path.exists():
            pink(f"file '{self._path}' not found")
            return
        
        blue("starting...")
        try:
            self._process = subprocess.Popen([str(self._path)])
            blue(f"process started with pid '{self._process.pid}'")
        except Exception as e:
            pink(f"start error '{e}'")

    def stop_and_delete(self) -> None:
        if self._process:
            blue(f"killing process with pid '{self._process.pid}'...")
            try:
                self._process.kill()
                tcode = self._process.wait(timeout=5)
                blue(f"process exited with code '{tcode:#X}'")
            except Exception as e:
                pink(f"process with pid '{self._process.pid}' termination error '{e}'")
            blue(f"process with pid '{self._process.pid}' is dead")
        
        max_attempts = 10
        timeout_ms = 300
        for attempt in range(max_attempts):
            try:
                blue(f"deleting file '{self._path}' (attempt {attempt + 1}/{max_attempts})...")
                self._path.unlink()
                blue(f"file '{self._path}' deleted")
                break
            except Exception as e:
                if attempt == 9: sys.exit(1)
                pink(f"delete '{self._path}' error: {e}")
                pink(f"retrying in {timeout_ms}ms...")
                time.sleep(timeout_ms / 1000)

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

        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
    def handle_signal(self, signum: int, frame: FrameType) -> None:
        del signum, frame
        self.cleanup()

    def cleanup(self) -> None:
        blue("cleanup...")
        self.stop_all()
        blue("see you later!")
        sys.exit(0)

    def start_all(self) -> None:
        for b in self.config.binaries:
            b.build_and_run()

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
            pink(f"fatal error in main loop '{e}'")
            self.cleanup()
            sys.exit(1)

if __name__ == "__main__":
    binaries_list = [
        Binary(binary["BUILD_CMD"], Path(binary["BINARY_PATH"]))
        for binary in BINARIES_LIST
    ]
    targets_list = [Target(target) for target in TARGETS_LIST]
    config = Config(binaries_list, targets_list, DURATION)
    Watcher(config).main()