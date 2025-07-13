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
```
3. Run it using python interpreter