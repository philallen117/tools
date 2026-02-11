#!/usr/bin/env python3
"""
Clean build files using .cleanignore patterns.

This tool removes files and directories based on gitignore-style patterns
defined in a .cleanignore file.
"""

import pathlib
import shutil
import argparse
import pathspec

IGNORE_FILE = ".cleanignore"

def get_paths_to_clean(root, patterns):
    """Matches files based on gitignore-style logic."""
    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    
    # We walk the tree and collect everything that matches the spec
    matches = []
    # We use rglob("*") to get every file/folder and check against spec
    for path in root.rglob("*"):
        # pathspec expects relative strings
        rel_path = str(path.relative_to(root))
        if spec.match_file(rel_path):
            matches.append(path)
    return matches

def clean(perform_delete=False):
    root = pathlib.Path.cwd()
    ignore_path = root / IGNORE_FILE
    
    if not ignore_path.exists():
        print(f"No {IGNORE_FILE} found in this directory.")
        return

    with open(ignore_path, "r") as f:
        patterns = f.read().splitlines()

    to_delete = get_paths_to_clean(root, patterns)
    
    if not to_delete:
        print("Everything is already clean.")
        return

    mode_label = "DELETING" if perform_delete else "DRY RUN (Safe Mode)"
    print(f"--- {mode_label} ---")

    # Sort by depth so we delete files inside folders before the folders themselves
    to_delete.sort(key=lambda p: len(p.parts), reverse=True)

    for path in to_delete:
        rel_path = path.relative_to(root)
        if perform_delete:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"✔ Removed: {rel_path}")
            except Exception as e:
                print(f"✘ Error removing {rel_path}: {e}")
        else:
            print(f"○ Would remove: {rel_path}")

def main():
    """Main entry point for the clean build files tool."""
    parser = argparse.ArgumentParser(description="Clean directories using .cleanignore logic.")
    parser.add_argument("--force", action="store_true", help="Perform the actual deletion.")
    args = parser.parse_args()
    clean(perform_delete=args.force)

if __name__ == "__main__":
    main()

