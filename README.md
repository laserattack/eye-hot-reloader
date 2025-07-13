# 👁️ Eye - Pure Python Hot-Reloader

Simple directories monitor with automatic rebuild and restart functionality for any project type

## What is it

- 🕵️‍♂️ **Universal Monitoring**: Tracks changes in directories or files
- 🔧 **Configurable Builds**: Works with any build system (Make, npm, go, etc.)
- 📦 **Zero Dependencies**: Pure Python
- 🎨 **Clean Output**: Color-coded messages with special prefix

## Quick Start

1. Place script in your project root
2. Configure the script:
```py
BINARIES_LIST = [
    {
        # Your custom build command
        "BUILD_CMD": ["go", "build", "-o", "./bin1.exe", "bin1.go"],
        # Output path
        "BINARY_PATH": "./bin1.exe"
    },
    {
        # Your custom build command
        "BUILD_CMD": ["go", "build", "-o", "./bin2.exe", "./1/bin2.go"],
        # Output path
        "BINARY_PATH": "./bin2.exe"
    },
]

# Directories/concrete files to watch
TARGETS_LIST = [
    "./target/target123", 
    "./target/222.txt",
]

# Delay between checks in seconds
DURATION = 1
```
3. Run it:
`py eye.py`