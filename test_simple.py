# test_simple.py (in project root)

import sys
from pathlib import Path

print("=== Environment Check ===")
print(f"Current directory: {Path.cwd()}")
print(f"Script location: {Path(__file__).parent}")
print(f"Python executable: {sys.executable}")

# Check if src directory exists
src_path = Path("src")
if src_path.exists():
    print(f"✓ src directory found at: {src_path.absolute()}")
else:
    print(f"✗ src directory NOT found")
    print(f"  Looking in: {src_path.absolute()}")

# List directories
print("\nDirectories in current path:")
for item in Path.cwd().iterdir():
    if item.is_dir():
        print(f"  - {item.name}/")

# Try to import
try:
    import src
    print("\n✓ Can import src module")
except ImportError as e:
    print(f"\n✗ Cannot import src: {e}")

# Check if __init__.py exists
init_file = Path("src/__init__.py")
if not init_file.exists():
    print("\n⚠️  src/__init__.py not found - creating it...")
    init_file.touch()
    print("✓ Created src/__init__.py")
