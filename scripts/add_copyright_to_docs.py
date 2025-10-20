#!/usr/bin/env python3
"""
Add copyright notice to all documentation files.

Original work by Yaaasoh (https://github.com/Yaaasoh/jsbsim-xml-generator)
Licensed under CC BY-NC-SA 4.0
"""

import os
from pathlib import Path

COPYRIGHT_NOTICE = """
---

**© 2025 Yaaasoh. All Rights Reserved.**

本ドキュメントの著作権はYaaasohに帰属します。引用部分については各引用元のライセンスが適用されます。
"""

# Files to process
FILES_TO_PROCESS = [
    "./aircraft/README.md",
    "./config/README.md",
    "./docs/development/ENVIRONMENT_CONFIG_IMPLEMENTATION.md",
    "./docs/development/GITIGNORE_VERIFICATION_REPORT.md",
    "./docs/development/README.md",
    "./docs/technical/jsbsim_structure.md",
    "./docs/technical/README.md",
    "./docs/user_guide/jsbsim_integration.md",
    "./docs/user_guide/README.md",
    "./engines/README.md",
    "./examples/README.md",
    "./templates/README.md",
    "./tests/README.md",
]

def add_copyright(file_path):
    """Add copyright notice to a file if it doesn't already have one."""

    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if copyright notice already exists
    if "© 2025 Yaaasoh. All Rights Reserved." in content:
        print(f"✓ {file_path} - Copyright already exists")
        return False

    # Add copyright notice to the end
    if content.endswith('\n'):
        new_content = content + COPYRIGHT_NOTICE
    else:
        new_content = content + '\n' + COPYRIGHT_NOTICE

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ {file_path} - Copyright added")
    return True

def main():
    print("Adding copyright notices to documentation files...\n")

    added_count = 0
    skipped_count = 0
    error_count = 0

    for file_path in FILES_TO_PROCESS:
        try:
            if os.path.exists(file_path):
                if add_copyright(file_path):
                    added_count += 1
                else:
                    skipped_count += 1
            else:
                print(f"✗ {file_path} - File not found")
                error_count += 1
        except Exception as e:
            print(f"✗ {file_path} - Error: {e}")
            error_count += 1

    print(f"\n--- Summary ---")
    print(f"Added: {added_count}")
    print(f"Skipped (already has copyright): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Total: {len(FILES_TO_PROCESS)}")

if __name__ == "__main__":
    main()
