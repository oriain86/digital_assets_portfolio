# create_init_files.py

from pathlib import Path


def create_init_files():
    """Create all necessary __init__.py files."""

    # Define all directories that need __init__.py
    directories = [
        "src",
        "src/core",
        "src/core/entities",
        "src/core/interfaces",
        "src/core/value_objects",
        "src/application",
        "src/application/services",
        "src/application/use_cases",
        "src/infrastructure",
        "src/infrastructure/cache",
        "src/infrastructure/data_sources",
        "src/infrastructure/repositories",
        "src/presentation",
        "src/presentation/cli",
        "src/presentation/dashboard",
        "src/presentation/dashboard/callbacks",
        "src/presentation/dashboard/components",
        "src/presentation/dashboard/layouts",
        "src/shared",
        "src/shared/utils",
        "src/config",
    ]

    created = 0
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)

        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"✓ Created {init_file}")
            created += 1
        else:
            print(f"  Already exists: {init_file}")

    print(f"\nCreated {created} __init__.py files")


if __name__ == "__main__":
    create_init_files()
