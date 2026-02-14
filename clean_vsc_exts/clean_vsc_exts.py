#!/usr/bin/env python3
"""
VSCode Extension Cleanup Tool

This tool removes VSCode extensions that are not in a specified keep list
and removes old versions of extensions, keeping only the latest version.
"""

import argparse
import sys
import shutil
from pathlib import Path
from typing import Set, List, Dict, Tuple
from collections import defaultdict


def read_extensions_to_keep(file_path: str) -> Set[str]:
    """
    Read the list of extensions to keep from a file.
    
    Args:
        file_path: Path to the file containing extension names (one per line)
        
    Returns:
        Set of extension names to keep
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        PermissionError: If the file can't be read
    """
    try:
        with open(file_path, 'r') as f:
            extensions = {line.strip() for line in f if line.strip() and not line.strip().startswith('#')}
        return extensions
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        raise
    except PermissionError:
        print(f"Error: Permission denied reading '{file_path}'.", file=sys.stderr)
        raise


def get_vscode_extensions_dir() -> Path:
    """
    Get the VSCode extensions directory path based on the OS.
    
    Returns:
        Path to the VSCode extensions directory
    """
    home = Path.home()
    
    if sys.platform == "darwin":  # macOS
        return home / ".vscode" / "extensions"
    elif sys.platform == "win32":  # Windows
        return home / ".vscode" / "extensions"
    else:  # Linux and others
        return home / ".vscode" / "extensions"


def get_installed_extensions(extensions_dir: Path) -> List[Path]:
    """
    Get a list of all installed extension directories.
    
    Args:
        extensions_dir: Path to the VSCode extensions directory
        
    Returns:
        List of Path objects for each installed extension
        
    Raises:
        FileNotFoundError: If the extensions directory doesn't exist
        PermissionError: If the directory can't be accessed
    """
    if not extensions_dir.exists():
        raise FileNotFoundError(f"Extensions directory not found: {extensions_dir}")
    
    if not extensions_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {extensions_dir}")
    
    try:
        return [d for d in extensions_dir.iterdir() if d.is_dir()]
    except PermissionError:
        print(f"Error: Permission denied accessing '{extensions_dir}'.", file=sys.stderr)
        raise


def extract_base_name(extension_dir_name: str) -> str:
    """
    Extract the base extension name from a directory name.
    
    Examples:
        ms-python.python-2021.5.842923320 -> ms-python.python
        esbenp.prettier-vscode-5.9.3 -> esbenp.prettier-vscode
        ms-python.python-2021.5.842923320-x64 -> ms-python.python
        
    Args:
        extension_dir_name: The full directory name
        
    Returns:
        The base extension name without version or architecture
    """
    # Split by '-' and find where the version starts
    # Version typically starts with a number after the first hyphen
    parts = extension_dir_name.split('-')
    
    if len(parts) <= 1:
        return extension_dir_name
    
    # The base name is usually the first part that doesn't start with a digit
    # We need to find the first part that looks like a version (starts with digit)
    base_parts = []
    for i, part in enumerate(parts):
        if i == 0:
            # Always include the first part (publisher.extension)
            base_parts.append(part)
        elif part and part[0].isdigit():
            # Found version number, stop here
            break
        else:
            # Still part of the name
            base_parts.append(part)
    
    return '-'.join(base_parts)


def extract_version_info(extension_dir_name: str) -> Tuple[str, str]:
    """
    Extract version information from an extension directory name.
    
    Args:
        extension_dir_name: The full directory name
        
    Returns:
        Tuple of (version_string, architecture) where architecture may be empty
    """
    base_name = extract_base_name(extension_dir_name)
    remainder = extension_dir_name[len(base_name):].lstrip('-')
    
    if not remainder:
        return ("", "")
    
    # Check if there's an architecture suffix (like x64, arm64)
    parts = remainder.split('-')
    if len(parts) > 1 and not parts[-1][0].isdigit():
        # Last part is likely architecture
        version = '-'.join(parts[:-1])
        arch = parts[-1]
        return (version, arch)
    else:
        return (remainder, "")


def compare_versions(ver1: str, ver2: str) -> int:
    """
    Compare two version strings.
    
    Args:
        ver1: First version string
        ver2: Second version string
        
    Returns:
        -1 if ver1 < ver2, 0 if equal, 1 if ver1 > ver2
    """
    if not ver1 and not ver2:
        return 0
    if not ver1:
        return -1
    if not ver2:
        return 1
    
    # Split by dots and compare each part
    parts1 = ver1.split('.')
    parts2 = ver2.split('.')
    
    for i in range(max(len(parts1), len(parts2))):
        p1 = parts1[i] if i < len(parts1) else '0'
        p2 = parts2[i] if i < len(parts2) else '0'
        
        # Try to compare as integers first
        try:
            n1 = int(p1)
            n2 = int(p2)
            if n1 < n2:
                return -1
            elif n1 > n2:
                return 1
        except ValueError:
            # Fallback to string comparison
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
    
    return 0


def find_latest_version(extension_dirs: List[Path]) -> Path:
    """
    Find the extension directory with the latest version.
    
    Args:
        extension_dirs: List of extension directories with the same base name
        
    Returns:
        The Path to the extension with the latest version
    """
    if len(extension_dirs) == 1:
        return extension_dirs[0]
    
    latest = extension_dirs[0]
    latest_version, latest_arch = extract_version_info(latest.name)
    
    for ext_dir in extension_dirs[1:]:
        version, arch = extract_version_info(ext_dir.name)
        
        cmp_result = compare_versions(version, latest_version)
        if cmp_result > 0:
            latest = ext_dir
            latest_version = version
            latest_arch = arch
        elif cmp_result == 0:
            # Same version, prefer native architecture or longer name (more specific)
            if len(ext_dir.name) > len(latest.name):
                latest = ext_dir
                latest_version = version
                latest_arch = arch
    
    return latest


def group_extensions_by_base_name(extension_dirs: List[Path]) -> Dict[str, List[Path]]:
    """
    Group extension directories by their base name.
    
    Args:
        extension_dirs: List of all extension directories
        
    Returns:
        Dictionary mapping base names to lists of extension directories
    """
    grouped = defaultdict(list)
    for ext_dir in extension_dirs:
        base_name = extract_base_name(ext_dir.name)
        grouped[base_name].append(ext_dir)
    return grouped


def should_keep_extension(extension_dir: Path, keep_list: Set[str]) -> bool:
    """
    Determine if an extension should be kept based on the keep list.
    
    Args:
        extension_dir: Path to the extension directory
        keep_list: Set of extension names to keep
        
    Returns:
        True if the extension should be kept, False otherwise
    """
    dir_name = extension_dir.name
    base_name = extract_base_name(dir_name)
    
    return base_name in keep_list


def remove_extension(extension_dir: Path, dry_run: bool = False, reason: str = "") -> bool:
    """
    Remove an extension directory.
    
    Args:
        extension_dir: Path to the extension directory to remove
        dry_run: If True, only simulate the removal
        reason: Optional reason for removal to display
        
    Returns:
        True if successful (or would be successful in dry run), False otherwise
    """
    try:
        if dry_run:
            msg = f"[DRY RUN] Would remove: {extension_dir.name}"
            if reason:
                msg += f" ({reason})"
            print(msg)
            return True
        else:
            msg = f"Removed: {extension_dir.name}"
            if reason:
                msg += f" ({reason})"
            shutil.rmtree(extension_dir)
            print(msg)
            return True
    except PermissionError:
        print(f"Error: Permission denied removing '{extension_dir.name}'.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error removing '{extension_dir.name}': {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the VSCode extension cleanup tool."""
    parser = argparse.ArgumentParser(
        description="Clean up VSCode extensions by removing those not in a keep list and old versions."
    )
    parser.add_argument(
        "keep_file",
        help="Path to file containing extensions to keep (one per line)"
    )
    parser.add_argument(
        "--extensions-dir",
        help="Path to VSCode extensions directory (auto-detected if not specified)",
        type=str,
        default=None
    )
    parser.add_argument(
        "--dry-run",
        help="Show what would be removed without actually removing anything",
        action="store_true"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="Show verbose output including kept extensions",
        action="store_true"
    )
    parser.add_argument(
        "--keep-all-versions",
        help="Keep all versions of extensions in the keep list (don't remove old versions)",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Read the keep list
    try:
        keep_list = read_extensions_to_keep(args.keep_file)
        print(f"Loaded {len(keep_list)} extension(s) to keep from '{args.keep_file}'")
        if args.verbose:
            print(f"Extensions to keep: {', '.join(sorted(keep_list))}")
    except (FileNotFoundError, PermissionError):
        return 1
    
    # Get extensions directory
    if args.extensions_dir:
        extensions_dir = Path(args.extensions_dir)
    else:
        extensions_dir = get_vscode_extensions_dir()
    
    print(f"Scanning extensions directory: {extensions_dir}")
    
    # Get installed extensions
    try:
        installed = get_installed_extensions(extensions_dir)
        print(f"Found {len(installed)} installed extension(s)")
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        return 1
    
    # Group extensions by base name
    grouped = group_extensions_by_base_name(installed)
    
    # Process extensions
    to_remove = []
    to_keep = []
    old_versions_to_remove = []
    
    for base_name, ext_dirs in grouped.items():
        if base_name in keep_list:
            # Extension is in keep list
            if args.keep_all_versions:
                # Keep all versions
                to_keep.extend(ext_dirs)
                if args.verbose:
                    for ext_dir in ext_dirs:
                        print(f"Keeping: {ext_dir.name}")
            else:
                # Keep only the latest version
                latest = find_latest_version(ext_dirs)
                to_keep.append(latest)
                
                if args.verbose:
                    print(f"Keeping: {latest.name} (latest version)")
                
                # Mark older versions for removal
                for ext_dir in ext_dirs:
                    if ext_dir != latest:
                        old_versions_to_remove.append(ext_dir)
                        if args.verbose:
                            print(f"Will remove old version: {ext_dir.name}")
        else:
            # Extension not in keep list, remove all versions
            to_remove.extend(ext_dirs)
            if args.verbose:
                for ext_dir in ext_dirs:
                    print(f"Will remove (not in keep list): {ext_dir.name}")
    
    # Summary
    print(f"\nSummary:")
    print(f"  Extensions to keep: {len(to_keep)}")
    print(f"  Unwanted extensions to remove: {len(to_remove)}")
    print(f"  Old versions to remove: {len(old_versions_to_remove)}")
    print(f"  Total to remove: {len(to_remove) + len(old_versions_to_remove)}")
    
    if not to_remove and not old_versions_to_remove:
        print("\nNo extensions to remove. All done!")
        return 0
    
    # Remove extensions
    if args.dry_run:
        print("\n[DRY RUN MODE] The following would be removed:")
    else:
        print("\nRemoving extensions...")
    
    success_count = 0
    fail_count = 0
    
    # Remove unwanted extensions
    for ext_dir in to_remove:
        if remove_extension(ext_dir, dry_run=args.dry_run, reason="not in keep list"):
            success_count += 1
        else:
            fail_count += 1
    
    # Remove old versions
    for ext_dir in old_versions_to_remove:
        if remove_extension(ext_dir, dry_run=args.dry_run, reason="old version"):
            success_count += 1
        else:
            fail_count += 1
    
    # Final summary
    print(f"\nComplete!")
    if args.dry_run:
        print(f"  Would remove: {success_count}")
    else:
        print(f"  Successfully removed: {success_count}")
        if fail_count > 0:
            print(f"  Failed to remove: {fail_count}")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
