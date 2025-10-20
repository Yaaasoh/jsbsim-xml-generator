#!/usr/bin/env python3
"""
Configuration Manager for JSBSim XML Generator

Provides centralized configuration management with:
- YAML config file loading
- Automatic path detection (FlightGear, JSBSim)
- Environment variable support
- Platform-specific defaults
- User-friendly error messages

Usage:
    from config_manager import ConfigManager

    # Load configuration
    config = ConfigManager()

    # Access settings
    fg_path = config.get_flightgear_path()
    output_dir = config.get('paths.output_dir')

    # Check if FlightGear is available
    if config.has_flightgear():
        print("FlightGear found!")
"""

import os
import sys
import platform
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml


class ConfigManager:
    """Centralized configuration manager with auto-detection"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to config.yaml (default: auto-detect)
        """
        self.project_root = self._find_project_root()
        self.config_path = self._resolve_config_path(config_path)
        self.config = self._load_config()
        self.platform = platform.system().lower()

    def _find_project_root(self) -> Path:
        """Find project root directory

        Searches for:
        - config/ directory
        - requirements.txt
        - README.md

        Returns:
            Path to project root
        """
        current = Path(__file__).resolve().parent

        # Search up to 3 levels
        for _ in range(3):
            if (current / 'config').exists() and (current / 'requirements.txt').exists():
                return current
            current = current.parent

        # Fallback: parent of src/
        return Path(__file__).resolve().parent.parent

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Resolve config file path

        Search order:
        1. Explicit config_path parameter
        2. config.yaml in project root
        3. config/config.default.yaml

        Args:
            config_path: Optional explicit path

        Returns:
            Path to config file
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Try config.yaml in project root
        root_config = self.project_root / 'config.yaml'
        if root_config.exists():
            return root_config

        # Fallback to default config
        default_config = self.project_root / 'config' / 'config.default.yaml'
        if default_config.exists():
            return default_config

        raise FileNotFoundError(
            f"No config file found. Please run 'python setup.py' to create config.yaml"
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config:
                raise ValueError("Config file is empty")

            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in {self.config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config file {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key

        Args:
            key: Dot-notation key (e.g., 'paths.output_dir')
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config.get('paths.output_dir')
            'output'
            >>> config.get('simulation.dt')
            0.02
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def has_flightgear(self) -> bool:
        """Check if FlightGear is available

        Returns:
            True if FlightGear can be found
        """
        try:
            fg_path = self.get_flightgear_path()
            return fg_path is not None
        except Exception:
            return False

    def get_flightgear_path(self) -> Optional[Path]:
        """Get FlightGear executable path with auto-detection

        Search order:
        1. Config file setting (if not null)
        2. Environment variable FLIGHTGEAR_EXE
        3. System PATH
        4. Common installation locations

        Returns:
            Path to FlightGear executable, or None if not found
        """
        # 1. Check config file
        config_path = self.get('paths.flightgear_exe')
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            print(f"Warning: FlightGear path in config not found: {config_path}")

        # 2. Check environment variable
        env_path = os.environ.get('FLIGHTGEAR_EXE')
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path

        # 3. Check system PATH
        fg_cmd = 'fgfs.exe' if self.platform == 'windows' else 'fgfs'
        path_result = shutil.which(fg_cmd)
        if path_result:
            return Path(path_result)

        # 4. Check common installation locations
        common_paths = self._get_common_flightgear_paths()
        for path in common_paths:
            if path.exists():
                return path

        return None

    def _get_common_flightgear_paths(self) -> List[Path]:
        """Get platform-specific common FlightGear installation paths

        Returns:
            List of possible FlightGear paths
        """
        if self.platform == 'windows':
            return [
                Path("C:/Program Files/FlightGear/bin/fgfs.exe"),
                Path("C:/FlightGear/bin/fgfs.exe"),
                Path("D:/Program Files/FlightGear/bin/fgfs.exe"),
                Path("D:/FlightGear/bin/fgfs.exe"),
            ]
        elif self.platform == 'linux':
            return [
                Path("/usr/bin/fgfs"),
                Path("/usr/local/bin/fgfs"),
                Path("/opt/FlightGear/bin/fgfs"),
            ]
        elif self.platform == 'darwin':  # macOS
            return [
                Path("/Applications/FlightGear.app/Contents/MacOS/fgfs"),
                Path("/usr/local/bin/fgfs"),
            ]
        else:
            return []

    def get_output_dir(self) -> Path:
        """Get output directory path

        Returns:
            Absolute path to output directory
        """
        output_dir = self.get('paths.output_dir', 'output')
        path = Path(output_dir)

        # Convert relative paths to absolute
        if not path.is_absolute():
            path = self.project_root / path

        return path

    def get_temp_dir(self) -> Path:
        """Get temporary directory path

        Returns:
            Absolute path to temp directory
        """
        temp_dir = self.get('paths.temp_dir', 'temp')
        path = Path(temp_dir)

        # Convert relative paths to absolute
        if not path.is_absolute():
            path = self.project_root / path

        return path

    def get_simulation_dt(self) -> float:
        """Get simulation timestep

        Returns:
            Timestep in seconds (default: 0.02)
        """
        return float(self.get('simulation.dt', 0.02))

    def get_flightgear_host(self) -> str:
        """Get FlightGear UDP host

        Returns:
            Host address (default: 'localhost')
        """
        return str(self.get('flightgear.host', 'localhost'))

    def get_flightgear_port(self) -> int:
        """Get FlightGear UDP port

        Returns:
            Port number (default: 5550)
        """
        return int(self.get('flightgear.port', 5550))

    def get_default_evidence_level(self) -> str:
        """Get default Evidence Level

        Returns:
            Evidence Level string (default: 'L2')
        """
        return str(self.get('generator.default_evidence_level', 'L2'))

    def ensure_directories(self):
        """Ensure required directories exist

        Creates:
        - output_dir
        - temp_dir
        - log_dir (if logging enabled)
        - data output dir (if data logging enabled)
        """
        dirs_to_create = [
            self.get_output_dir(),
            self.get_temp_dir(),
        ]

        if self.get('logging.enabled', True):
            log_dir = self.get('logging.log_dir', 'logs')
            path = Path(log_dir)
            if not path.is_absolute():
                path = self.project_root / path
            dirs_to_create.append(path)

        if self.get('logging.data_logging.enabled', True):
            data_dir = self.get('logging.data_logging.output_dir', 'dataout')
            path = Path(data_dir)
            if not path.is_absolute():
                path = self.project_root / path
            dirs_to_create.append(path)

        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)

    def print_summary(self):
        """Print configuration summary"""
        print("=" * 70)
        print("CONFIGURATION SUMMARY")
        print("=" * 70)
        print(f"Config file: {self.config_path}")
        print(f"Project root: {self.project_root}")
        print(f"Platform: {self.platform}")
        print()
        print("Paths:")
        print(f"  Output dir: {self.get_output_dir()}")
        print(f"  Temp dir: {self.get_temp_dir()}")

        fg_path = self.get_flightgear_path()
        if fg_path:
            print(f"  FlightGear: {fg_path}")
        else:
            print(f"  FlightGear: Not found")

        print()
        print("Simulation:")
        print(f"  Timestep (dt): {self.get_simulation_dt()} s")
        print(f"  FlightGear UDP: {self.get_flightgear_host()}:{self.get_flightgear_port()}")
        print()
        print("Generator:")
        print(f"  Default Evidence Level: {self.get_default_evidence_level()}")
        print("=" * 70)


# Singleton instance for convenience
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """Get singleton ConfigManager instance

    Args:
        config_path: Optional path to config file

    Returns:
        ConfigManager instance
    """
    global _config_instance
    if _config_instance is None or config_path is not None:
        _config_instance = ConfigManager(config_path)
    return _config_instance


def main():
    """CLI for testing configuration"""
    print("Testing Configuration Manager")
    print()

    try:
        config = ConfigManager()
        config.print_summary()

        print()
        print("FlightGear availability test:")
        if config.has_flightgear():
            print("  [OK] FlightGear found and ready")
        else:
            print("  [WARN] FlightGear not found")
            print("  Run 'python setup.py' to configure, or install FlightGear")

        print()
        print("Directory creation test:")
        config.ensure_directories()
        print("  [OK] Required directories created/verified")

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print()
        print("Please run 'python setup.py' to create config.yaml")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
