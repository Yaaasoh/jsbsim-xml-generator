#!/usr/bin/env python3
"""
JSBSim XML Generator - Initial Setup

This script helps you set up your environment for the first time.
It will:
1. Detect your operating system
2. Search for FlightGear installation
3. Verify Python dependencies
4. Create config.yaml with detected settings
5. Create required directories

Usage:
    python setup.py

Options:
    --reconfigure    Force reconfiguration even if config.yaml exists
    --minimal        Create minimal config without FlightGear detection
    --batch          Non-interactive mode (use defaults for all prompts)
"""

import os
import sys
import platform
import shutil
import argparse
from pathlib import Path
from typing import Optional, Dict, Any


def print_header(text: str):
    """Print formatted header"""
    print()
    print("=" * 70)
    print(text)
    print("=" * 70)


def print_step(step_num: int, text: str):
    """Print step header"""
    print()
    print(f"[Step {step_num}] {text}")
    print("-" * 70)


def detect_os() -> str:
    """Detect operating system

    Returns:
        OS name: 'windows', 'linux', 'darwin'
    """
    return platform.system().lower()


def find_flightgear(os_name: str) -> Optional[Path]:
    """Find FlightGear executable

    Args:
        os_name: Operating system name

    Returns:
        Path to FlightGear executable, or None
    """
    print("[INFO] Searching for FlightGear...")

    # Try system PATH first
    fg_cmd = 'fgfs.exe' if os_name == 'windows' else 'fgfs'
    path_result = shutil.which(fg_cmd)
    if path_result:
        print(f"[OK] Found in PATH: {path_result}")
        return Path(path_result)

    # Check common installation locations
    common_paths = []

    if os_name == 'windows':
        common_paths = [
            Path("C:/Program Files/FlightGear/bin/fgfs.exe"),
            Path("C:/FlightGear/bin/fgfs.exe"),
            Path("D:/Program Files/FlightGear/bin/fgfs.exe"),
            Path("D:/FlightGear/bin/fgfs.exe"),
        ]
    elif os_name == 'linux':
        common_paths = [
            Path("/usr/bin/fgfs"),
            Path("/usr/local/bin/fgfs"),
            Path("/opt/FlightGear/bin/fgfs"),
        ]
    elif os_name == 'darwin':
        common_paths = [
            Path("/Applications/FlightGear.app/Contents/MacOS/fgfs"),
            Path("/usr/local/bin/fgfs"),
        ]

    for path in common_paths:
        if path.exists():
            print(f"[OK] Found at: {path}")
            return path

    print("[WARN] FlightGear not found")
    return None


def check_python_version() -> bool:
    """Check Python version

    Returns:
        True if Python >= 3.8
    """
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[WARN] Python {version.major}.{version.minor}.{version.micro} detected")
        print("       Python 3.8 or higher is recommended")
        return False


def check_dependencies() -> Dict[str, bool]:
    """Check required Python packages

    Returns:
        Dictionary of package availability
    """
    packages = {
        'yaml': 'PyYAML',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'jsbsim': 'jsbsim',
        'scipy': 'scipy',
        'numpy': 'numpy',
    }

    results = {}

    for module_name, package_name in packages.items():
        try:
            __import__(module_name)
            results[package_name] = True
        except ImportError:
            results[package_name] = False

    return results


def prompt_user(question: str, default: str = 'y', batch_mode: bool = False) -> str:
    """Prompt user for input

    Args:
        question: Question to ask
        default: Default answer
        batch_mode: If True, use default without prompting

    Returns:
        User response or default
    """
    if batch_mode:
        return default

    response = input(f"{question} [{default}]: ").strip()
    return response if response else default


def create_config_yaml(output_path: Path, os_name: str,
                       flightgear_path: Optional[Path],
                       batch_mode: bool = False):
    """Create config.yaml file

    Args:
        output_path: Path to output config.yaml
        os_name: Operating system name
        flightgear_path: Path to FlightGear (or None)
        batch_mode: Non-interactive mode
    """
    print()
    print(f"Creating config.yaml at: {output_path}")

    # Read default config template
    template_path = output_path.parent / 'config' / 'config.default.yaml'

    if not template_path.exists():
        print(f"[ERROR] Default config template not found: {template_path}")
        return False

    with open(template_path, 'r', encoding='utf-8') as f:
        config_content = f.read()

    # Replace values
    if flightgear_path:
        # Use forward slashes for cross-platform compatibility
        fg_path_str = str(flightgear_path).replace('\\', '/')
        config_content = config_content.replace(
            'flightgear_exe: null',
            f'flightgear_exe: "{fg_path_str}"'
        )

    config_content = config_content.replace(
        'os: null',
        f'os: "{os_name}"'
    )

    # Write config.yaml
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print("[OK] config.yaml created successfully")
    return True


def create_directories(project_root: Path):
    """Create required directories

    Args:
        project_root: Project root directory
    """
    directories = [
        'output',
        'temp',
        'logs',
        'dataout',
    ]

    print()
    print("Creating required directories...")

    for dir_name in directories:
        dir_path = project_root / dir_name

        # If a file exists with the same name, remove it
        if dir_path.exists() and dir_path.is_file():
            print(f"  [WARN] {dir_name} exists as a file, removing...")
            dir_path.unlink()

        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {dir_name}/")


def print_next_steps(flightgear_found: bool, missing_packages: list):
    """Print next steps after setup

    Args:
        flightgear_found: Whether FlightGear was found
        missing_packages: List of missing Python packages
    """
    print_header("SETUP COMPLETE")

    print()
    print("Configuration file created: config.yaml")
    print()

    if missing_packages:
        print("NEXT STEPS:")
        print()
        print("1. Install missing Python packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        print()
        print("   Or install all dependencies:")
        print("   pip install -r requirements.txt")
        print()

    if not flightgear_found:
        print("2. Install FlightGear (optional, for visualization):")
        print()
        os_name = detect_os()
        if os_name == 'windows':
            print("   Download from: https://www.flightgear.org/download/")
        elif os_name == 'linux':
            print("   Ubuntu/Debian: sudo apt-get install flightgear")
            print("   Fedora/RHEL: sudo yum install flightgear")
        elif os_name == 'darwin':
            print("   Download from: https://www.flightgear.org/download/")
        print()
        print("   After installation, run 'python setup.py --reconfigure'")
        print()

    print("3. Test your installation:")
    print("   python tests/test_jsbsim_load.py ExampleAircraft")
    print()

    print("4. Generate your first aircraft:")
    print("   python src/generate_jsbsim_from_gsheet.py \\")
    print("       -i templates/Aircraft_Input_Template.xlsx \\")
    print("       -o output/MyAircraft")
    print()

    print("For more information:")
    print("  - README.md - Project overview")
    print("  - config/README.md - Configuration guide")
    print("  - docs/user_guide/ - User documentation")
    print()


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(
        description='JSBSim XML Generator - Initial Setup',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--reconfigure', action='store_true',
                       help='Force reconfiguration even if config.yaml exists')
    parser.add_argument('--minimal', action='store_true',
                       help='Create minimal config without FlightGear detection')
    parser.add_argument('--batch', action='store_true',
                       help='Non-interactive mode (use defaults)')

    args = parser.parse_args()

    print_header("JSBSim XML Generator - Initial Setup")

    # Determine project root
    project_root = Path(__file__).resolve().parent
    config_path = project_root / 'config.yaml'

    # Check if config already exists
    if config_path.exists() and not args.reconfigure:
        print()
        print(f"[INFO] Configuration file already exists: {config_path}")
        print()
        response = prompt_user(
            "Do you want to reconfigure?",
            default='n',
            batch_mode=args.batch
        )
        if response.lower() not in ['y', 'yes']:
            print()
            print("Setup cancelled. Use --reconfigure to force reconfiguration.")
            return 0

    # Step 1: Detect OS
    print_step(1, "Detecting Operating System")
    os_name = detect_os()
    print(f"[OK] Detected OS: {os_name}")

    # Step 2: Check Python version
    print_step(2, "Checking Python Version")
    check_python_version()

    # Step 3: Check dependencies
    print_step(3, "Checking Python Dependencies")
    deps = check_dependencies()

    missing_packages = [pkg for pkg, available in deps.items() if not available]

    if missing_packages:
        print()
        print("[WARN] Missing packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print()
        print("You can install them after setup with:")
        print("  pip install -r requirements.txt")
    else:
        print("[OK] All required packages are installed")

    # Step 4: Find FlightGear
    flightgear_path = None
    if not args.minimal:
        print_step(4, "Finding FlightGear Installation")
        flightgear_path = find_flightgear(os_name)

        if not flightgear_path:
            print()
            print("[INFO] FlightGear is optional but recommended for visualization")
            response = prompt_user(
                "Do you want to specify FlightGear path manually?",
                default='n',
                batch_mode=args.batch
            )

            if response.lower() in ['y', 'yes']:
                manual_path = input("Enter FlightGear executable path: ").strip()
                if manual_path and Path(manual_path).exists():
                    flightgear_path = Path(manual_path)
                    print(f"[OK] Using: {flightgear_path}")
                else:
                    print("[WARN] Invalid path, continuing without FlightGear")

    # Step 5: Create config.yaml
    print_step(5, "Creating Configuration File")
    if not create_config_yaml(config_path, os_name, flightgear_path, args.batch):
        return 1

    # Step 6: Create directories
    print_step(6, "Creating Required Directories")
    create_directories(project_root)

    # Print next steps
    print_next_steps(flightgear_path is not None, missing_packages)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print()
        print("Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"[ERROR] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
