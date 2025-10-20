# Configuration Guide

This directory contains configuration files for the JSBSim XML Generator.

## Quick Start

### Automatic Setup (Recommended)

Run the setup script from the project root to automatically detect your environment:

```bash
python setup.py
```

This will:
1. Detect your operating system
2. Search for FlightGear installation
3. Verify Python and JSBSim
4. Create `config.yaml` in the project root with detected settings

### Manual Setup

If you prefer manual configuration:

1. Copy the default configuration to the project root:
   ```bash
   cp config/config.default.yaml config.yaml
   ```

2. Edit `config.yaml` to match your environment

3. See platform-specific examples in `config/examples/`:
   - `config.windows.yaml` - Windows configuration example
   - `config.linux.yaml` - Linux configuration example

## Configuration Structure

### Required Settings

These settings are typically auto-detected but can be overridden:

```yaml
paths:
  flightgear_exe: null          # FlightGear executable path (null = auto-detect)
  output_dir: "output"          # Output directory for generated files
```

### Optional Settings

```yaml
flightgear:
  host: "localhost"             # FlightGear UDP host
  port: 5550                    # FlightGear UDP port

simulation:
  dt: 0.02                      # Simulation timestep (50 Hz)

generator:
  default_evidence_level: "L2"  # Default Evidence Level (L1-L4)
```

## Finding FlightGear Installation

### Windows

Open PowerShell and run:
```powershell
where fgfs
```

Common locations:
- `C:/Program Files/FlightGear/bin/fgfs.exe`
- `C:/FlightGear/bin/fgfs.exe`

### Linux

Open terminal and run:
```bash
which fgfs
```

Common locations:
- `/usr/bin/fgfs`
- `/usr/local/bin/fgfs`
- `/opt/FlightGear/bin/fgfs`

### macOS

Open terminal and run:
```bash
which fgfs
```

Common locations:
- `/Applications/FlightGear.app/Contents/MacOS/fgfs`
- `/usr/local/bin/fgfs`

## Environment Variables

You can set environment variables to override config file settings:

- `FLIGHTGEAR_EXE` - FlightGear executable path
- `JSBSIM_DATA_DIR` - JSBSim data directory (rarely needed)

Example (Windows PowerShell):
```powershell
$env:FLIGHTGEAR_EXE = "C:/FlightGear/bin/fgfs.exe"
python tests/test_e2e.py
```

Example (Linux/macOS):
```bash
export FLIGHTGEAR_EXE=/usr/local/bin/fgfs
python tests/test_e2e.py
```

## Path Resolution Order

The configuration system searches for paths in this order:

1. **Explicit config.yaml setting** (if not null)
2. **Environment variable** (e.g., FLIGHTGEAR_EXE)
3. **System PATH** (checks if command is available)
4. **Common installation locations** (platform-specific)
5. **User prompt** (asks user to specify path)

## Configuration File Format

Configuration files use YAML format:

- **Comments**: Lines starting with `#`
- **Sections**: Top-level keys (e.g., `paths:`, `simulation:`)
- **Settings**: Indented key-value pairs
- **Null values**: Use `null` for auto-detection
- **Paths**: Use forward slashes `/` or escaped backslashes `\\`

### Example

```yaml
# This is a comment
paths:
  # Auto-detect FlightGear
  flightgear_exe: null

  # Explicit path (Windows)
  # flightgear_exe: "C:/Program Files/FlightGear/bin/fgfs.exe"

  # Explicit path (Linux)
  # flightgear_exe: "/usr/bin/fgfs"

  output_dir: "output"

simulation:
  dt: 0.02
```

## Troubleshooting

### FlightGear Not Found

If setup.py cannot find FlightGear:

1. Check if FlightGear is installed:
   - Windows: Check Programs and Features
   - Linux: `dpkg -l | grep flightgear` or `rpm -qa | grep flightgear`

2. Manually specify the path in `config.yaml`:
   ```yaml
   paths:
     flightgear_exe: "/path/to/fgfs"
   ```

3. Check executable permissions (Linux/macOS):
   ```bash
   ls -l /path/to/fgfs
   chmod +x /path/to/fgfs  # If needed
   ```

### Permission Errors

If you get permission errors:

- Windows: Run as Administrator (right-click → Run as Administrator)
- Linux/macOS: Check file permissions, may need `sudo` for system directories

### YAML Syntax Errors

If you get YAML parsing errors:

1. Check indentation (must use spaces, not tabs)
2. Check quotes around paths with special characters
3. Validate YAML syntax: https://www.yamllint.com/

### Python Module Not Found

If you get "PyYAML not found":

```bash
pip install -r requirements.txt
```

## Advanced Configuration

### Custom Evidence Levels

You can customize quality criteria for different Evidence Levels by modifying the `generator` section:

```yaml
generator:
  default_evidence_level: "L2"
  evidence_levels:
    L1:
      description: "Measured values (strict)"
      trim_tolerance: 0.01
    L2:
      description: "Estimated values (relaxed)"
      trim_tolerance: 0.05
```

### Batch Processing

For batch operations on multiple aircraft:

```yaml
advanced:
  parallel_processing: true
  max_workers: 4  # Number of parallel processes
```

### Debug Mode

Enable verbose output for troubleshooting:

```yaml
logging:
  level: "DEBUG"

advanced:
  verbose: true
```

## Related Documentation

- [Main README](../README.md) - Project overview
- [JSBSim Integration Guide](../docs/user_guide/jsbsim_integration.md) - JSBSim setup
- [Test Documentation](../tests/README.md) - Running tests

## Support

If you encounter issues with configuration:

1. Check the examples in `config/examples/`
2. Run `python setup.py` to re-detect your environment
3. Check the [GitHub Issues](https://github.com/[your-repo]/issues)
4. Consult platform-specific documentation in examples/

---

**© 2025 Yaaasoh. All Rights Reserved.**

本ドキュメントの著作権はYaaasohに帰属します。引用部分については各引用元のライセンスが適用されます。
