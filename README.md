# 👁️ voyeur - Simple Hot-Reloader

Simple directories monitor with automatic rebuild and restart functionality for any project type

## What is it

- 🕵️‍♂️ **Universal Monitoring**: Tracks changes in directories or files
- 🔧 **Configurable Builds**: Works with any build system (Make, go, etc.)
- 📦 **Cross-platform**: Windows/Unix
- 🙂 **Simplicity**: Only 1 file
- 🎨 **Clean Output**: Color-coded messages with special prefix

## Dependencies

- Python

## Quick Start

1. Place script in your project root
2. Configure the script:
```py
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
        "CMD": ["py", "./target2/target.py"],
    },
]

TARGETS_LIST = [
    "./target/target123", 
    "./target/222.txt",
    "./target2/target.py",
]

DURATION = 1

# SETTINGS END
```
3. Run it using python interpreter

## How does it work?

For Binary Builds:

```python
{
    "BUILD_CMD": ["go", "build", "-o", "./bin.exe", "main.go"],
    "BINARY_PATH": "./bin.exe"
}
```

- Runs `BUILD_CMD` when changes detected
- Launches the built binary
- On restart:
- - Kills the process (with PID tracking)
- - Deletes the binary (with 10 retry attempts)
- - Repeats build + launch cycle

For Direct Commands:

```python
{
    "CMD": ["python", "script.py"]
}
```

- Starts the command as a subprocess
- Gracefully kills it on restart