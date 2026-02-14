# clean-vsc-exts

VSCode Extension Cleanup Tool

This tool removes VSCode extensions that are not in a specified keep list and removes old versions of extensions, keeping only the latest version.

## Installation

```bash
just install
```

Or manually:

```bash
uv tool install --editable .
```

## Usage

```bash
clean-vsc-exts extensions-to-keep.txt
```
