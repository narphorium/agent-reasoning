from pathlib import Path

def get_py_tree(root_path, prefix=""):
    root = Path(root_path)
    result = []
    if root:
        result.append(f"{prefix}{root.name}")
    
    # Get all items in directory, sorted alphabetically
    contents = sorted(root.iterdir())
    
    # Filter directories and .py files
    py_items = [
        item for item in contents 
        if item.is_file() and item.suffix == '.py'
        or (item.is_dir() and any(f.suffix == '.py' for f in item.rglob("*.py")))
    ]
    
    for i, path in enumerate(py_items):
        is_last = i == len(py_items) - 1
        connector = "└── " if is_last else "├── "
        
        result.append(f"{prefix}{connector}{path.name}")
        
        if path.is_dir():
            # Extend prefix for subdirectories
            extension = "    " if is_last else "│   "
            result.append(get_py_tree(path, prefix + extension))
    
    return "\n".join(filter(None, result))