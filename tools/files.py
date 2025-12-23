"""
C.O.R.A File Operations Module

File management utilities for CORA.
Per ARCHITECTURE.md: Open, create, search, move, copy, delete files.
"""

import os
import shutil
import json
import datetime


def create_file(file_path, content='', overwrite=False):
    """Create a new file with optional content.

    Args:
        file_path: Path to create file at
        content: Initial file content (default empty)
        overwrite: Overwrite if exists (default False)

    Returns:
        bool: True if created successfully
    """
    try:
        if os.path.exists(file_path) and not overwrite:
            print(f"[!] File already exists: {file_path}")
            return False

        # Create directory if needed
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"[!] Failed to create file: {e}")
        return False


def read_file(file_path, encoding='utf-8'):
    """Read file contents.

    Args:
        file_path: Path to file
        encoding: File encoding (default utf-8)

    Returns:
        str: File contents or None if error
    """
    try:
        if not os.path.exists(file_path):
            print(f"[!] File not found: {file_path}")
            return None

        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"[!] Failed to read file: {e}")
        return None


def append_file(file_path, content, create_if_missing=True):
    """Append content to file.

    Args:
        file_path: Path to file
        content: Content to append
        create_if_missing: Create file if it doesn't exist

    Returns:
        bool: True if appended successfully
    """
    try:
        if not os.path.exists(file_path) and not create_if_missing:
            print(f"[!] File not found: {file_path}")
            return False

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"[!] Failed to append to file: {e}")
        return False


def delete_file(file_path, confirm=True):
    """Delete a file.

    Args:
        file_path: Path to file
        confirm: Require confirmation (for future GUI integration)

    Returns:
        bool: True if deleted successfully
    """
    try:
        if not os.path.exists(file_path):
            print(f"[!] File not found: {file_path}")
            return False

        os.remove(file_path)
        return True
    except Exception as e:
        print(f"[!] Failed to delete file: {e}")
        return False


def move_file(source, destination, overwrite=False):
    """Move a file to a new location.

    Args:
        source: Source file path
        destination: Destination path
        overwrite: Overwrite if destination exists

    Returns:
        bool: True if moved successfully
    """
    try:
        if not os.path.exists(source):
            print(f"[!] Source not found: {source}")
            return False

        if os.path.exists(destination) and not overwrite:
            print(f"[!] Destination already exists: {destination}")
            return False

        # Create destination directory if needed
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        shutil.move(source, destination)
        return True
    except Exception as e:
        print(f"[!] Failed to move file: {e}")
        return False


def copy_file(source, destination, overwrite=False):
    """Copy a file to a new location.

    Args:
        source: Source file path
        destination: Destination path
        overwrite: Overwrite if destination exists

    Returns:
        bool: True if copied successfully
    """
    try:
        if not os.path.exists(source):
            print(f"[!] Source not found: {source}")
            return False

        if os.path.exists(destination) and not overwrite:
            print(f"[!] Destination already exists: {destination}")
            return False

        # Create destination directory if needed
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"[!] Failed to copy file: {e}")
        return False


def rename_file(file_path, new_name):
    """Rename a file (keeps it in same directory).

    Args:
        file_path: Current file path
        new_name: New filename (not full path)

    Returns:
        bool: True if renamed successfully
    """
    try:
        if not os.path.exists(file_path):
            print(f"[!] File not found: {file_path}")
            return False

        directory = os.path.dirname(file_path)
        new_path = os.path.join(directory, new_name)

        os.rename(file_path, new_path)
        return True
    except Exception as e:
        print(f"[!] Failed to rename file: {e}")
        return False


def get_file_info(file_path):
    """Get file metadata.

    Args:
        file_path: Path to file

    Returns:
        dict: File info or None if error
    """
    try:
        if not os.path.exists(file_path):
            return None

        stat = os.stat(file_path)
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'extension': os.path.splitext(file_path)[1],
            'size_bytes': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'created': datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'is_file': os.path.isfile(file_path),
            'is_dir': os.path.isdir(file_path),
        }
    except Exception as e:
        print(f"[!] Failed to get file info: {e}")
        return None


def list_directory(dir_path, extensions=None, recursive=False):
    """List files in a directory.

    Args:
        dir_path: Directory path
        extensions: List of extensions to filter (e.g., ['.txt', '.py'])
        recursive: Include subdirectories

    Returns:
        list: File paths
    """
    try:
        if not os.path.isdir(dir_path):
            print(f"[!] Not a directory: {dir_path}")
            return []

        files = []

        if recursive:
            for root, dirs, filenames in os.walk(dir_path):
                for filename in filenames:
                    if extensions is None or any(filename.endswith(ext) for ext in extensions):
                        files.append(os.path.join(root, filename))
        else:
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    if extensions is None or any(item.endswith(ext) for ext in extensions):
                        files.append(item_path)

        return sorted(files)
    except Exception as e:
        print(f"[!] Failed to list directory: {e}")
        return []


def create_directory(dir_path):
    """Create a directory (and parents if needed).

    Args:
        dir_path: Directory path to create

    Returns:
        bool: True if created successfully
    """
    try:
        if os.path.exists(dir_path):
            return True  # Already exists

        os.makedirs(dir_path)
        return True
    except Exception as e:
        print(f"[!] Failed to create directory: {e}")
        return False


def delete_directory(dir_path, recursive=False):
    """Delete a directory.

    Args:
        dir_path: Directory to delete
        recursive: Delete contents recursively (default False)

    Returns:
        bool: True if deleted successfully
    """
    try:
        if not os.path.exists(dir_path):
            print(f"[!] Directory not found: {dir_path}")
            return False

        if recursive:
            shutil.rmtree(dir_path)
        else:
            os.rmdir(dir_path)  # Only works if empty

        return True
    except Exception as e:
        print(f"[!] Failed to delete directory: {e}")
        return False


def read_json(file_path):
    """Read JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        dict/list: Parsed JSON or None if error
    """
    try:
        content = read_file(file_path)
        if content is None:
            return None
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[!] Invalid JSON: {e}")
        return None


def write_json(file_path, data, indent=2):
    """Write data to JSON file.

    Args:
        file_path: Path to JSON file
        data: Data to write (dict or list)
        indent: JSON indentation

    Returns:
        bool: True if written successfully
    """
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return create_file(file_path, content, overwrite=True)
    except Exception as e:
        print(f"[!] Failed to write JSON: {e}")
        return False


def search_in_file(file_path, query, case_sensitive=False):
    """Search for text within a file.

    Args:
        file_path: Path to file
        query: Search query
        case_sensitive: Case-sensitive search

    Returns:
        list: List of (line_number, line_content) tuples
    """
    try:
        content = read_file(file_path)
        if content is None:
            return []

        results = []
        lines = content.split('\n')

        search_query = query if case_sensitive else query.lower()

        for i, line in enumerate(lines, 1):
            search_line = line if case_sensitive else line.lower()
            if search_query in search_line:
                results.append((i, line.strip()))

        return results
    except Exception as e:
        print(f"[!] Search error: {e}")
        return []


def get_recent_files(dir_path, limit=10, extensions=None):
    """Get most recently modified files.

    Args:
        dir_path: Directory to search
        limit: Maximum files to return
        extensions: File extensions to filter

    Returns:
        list: File paths sorted by modification time (newest first)
    """
    try:
        files = list_directory(dir_path, extensions=extensions, recursive=True)

        # Sort by modification time
        files_with_time = [(f, os.path.getmtime(f)) for f in files]
        files_with_time.sort(key=lambda x: x[1], reverse=True)

        return [f[0] for f in files_with_time[:limit]]
    except Exception as e:
        print(f"[!] Failed to get recent files: {e}")
        return []
