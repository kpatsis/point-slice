# Point Slice Parser

[![Tests](https://github.com/kpatsis/point_slice/actions/workflows/ci.yml/badge.svg)](https://github.com/kpatsis/point_slice/actions/workflows/ci.yml)

A Python library for parsing and analyzing 3D point cloud data from space-separated CSV files and DXF files.

## Features

- **DXF creation tool**: Ready-to-use script (`point_slice_studio_cli.py`) for converting CSV point clouds to DXF format
- **Data-based slice type detection**: Automatically determines if points form XY, XZ, YZ, or unknown slice patterns
- **Smart positioning**: Automatically positions different slice types at appropriate coordinates
- **Configurable thresholds**: Customizable precision for slice detection
- **Random sampling**: Efficient analysis of large datasets using representative samples
- **Color assignment**: Automatic color coding based on slice type and filename patterns
- **Batch processing**: Parse entire directories of CSV files
- **Command-line interface**: User-friendly CLI with comprehensive options and help

## Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd point-slice
   ```

2. **Create a virtual environment:**
   ```bash
   # Create virtual environment
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   **On Windows:**
   ```powershell
   # PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Command Prompt
   .\venv\Scripts\activate.bat
   ```

4. **Install main dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Install development dependencies (optional):**
   ```bash
   pip install -r requirements-dev.txt
   ```

6. **Verify installation:**
   ```bash
   python run_tests.py
   ```

### Deactivating the Environment

When you're done working:

```bash
deactivate
```


## Quick Start

### Prepare working directory

Provided that the installation described above has been performed, you can perform the following steps to get the environment ready to execute the script:

1. Open the Terminal

2. Execute

```bash
cd ~\point-slice
git pull
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Creating DXF Files (GUI - Recommended)

Use the graphical interface for an intuitive experience:

```bash
# Launch the GUI application
python point_slice_studio_gui.py
```

The **Point Slice Studio** GUI provides:
- Easy directory and file selection with browse buttons
- Visual input validation and error reporting
- Real-time progress logging
- Interactive configuration of colors and label positioning
- No command-line knowledge required

### Creating DXF Files (Command Line)

Use the provided script to convert CSV point cloud data to DXF format:

```bash
# Specify input directory and output file
python point_slice_studio_cli.py path/to/csv/files output.dxf

# Customize colors and label positioning
python point_slice_studio_cli.py path/to/csv/files output.dxf --colors 1 2 3 4 5 --label-x -50.0 --label-y 10.0 

# Get help
python point_slice_studio_cli.py --help
```


## Point Slice Studio (GUI Application)

**Point Slice Studio** is a user-friendly graphical interface for converting CSV point cloud data into DXF files. It provides the same powerful functionality as the command-line tool with an intuitive visual interface.

### Features

- **Easy file management**: Browse buttons for selecting input directories and output files
- **Visual validation**: Real-time input validation with clear error messages
- **Progress monitoring**: Live progress log showing processing status
- **Interactive configuration**: Visual controls for colors and label positioning
- **Modern interface**: Clean, responsive design with proper error handling
- **No command-line required**: Perfect for users who prefer graphical interfaces

### Usage

```bash
# Launch Point Slice Studio
python point_slice_studio_gui.py
```

### Building Executable

Create a standalone executable using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller pyinstaller.spec

# The executable will be in dist/Point_Slice_Studio/
```

## DXF Creation Tool (Command Line)

The `point_slice_studio_cli.py` script provides a complete workflow for converting CSV point cloud data into DXF files with proper layers, colors, and organization.

### Usage

```bash
python point_slice_studio_cli.py [input_directory] [output_file] [options]
```

### Arguments

- `input_directory` (optional): Directory containing CSV files
  - Default: `tests/testdata/02_csv`
- `output_file` (optional): Output DXF filename
  - Default: `output.dxf`

### Options

- `--colors COLOR [COLOR ...]`: Custom AutoCAD color indices (1-256)
  - Default: `1 2 3 4 5 6 7 8 9 10`
- `--label-x FLOAT`: X position for label start
  - Default: `-40.0`
- `--label-y FLOAT`: Y position for label start
  - Default: `0.0`
  
- `--threshold FLOAT`: Slice detection threshold (max allowed variation of the smallest axis)
  - Default: `0.050` (smaller is stricter; larger is more tolerant)

### Features

- **Automatic slice type detection**: Identifies XY, XZ, YZ, and unknown slice types
- **Smart positioning**: Places different slice types at different coordinates:
  - XY slices: Origin (0, 0, 0)
  - XZ slices: (100, 0, 0) - rotated to XY plane
  - YZ slices: (200, 0, 0) - rotated to XY plane
- **Color-coded layers**: Each point slice gets its own layer with unique colors
- **Progress reporting**: Real-time feedback during processing
- **Error handling**: Comprehensive validation and error messages

### Examples

```bash
# Process default test data
python point_slice_studio_cli.py

# Process custom directory
python point_slice_studio_cli.py data/measurements/ engineering_drawing.dxf

# Use custom colors (red, green, blue, cyan)
python point_slice_studio_cli.py --colors 1 3 5 4

# Position labels at custom location
python point_slice_studio_cli.py --label-x -100 --label-y 50

# Adjust slice detection threshold (e.g., stricter)
python point_slice_studio_cli.py path/to/csv/files output.dxf --threshold 0.005
```

### Output

The script generates:
- DXF file with organized blocks and layers
- Progress reporting during execution
- Summary with file statistics
- File size and location information

## Input File Format

The parser expects space-separated CSV files with X, Y, Z coordinates in the first three columns:

```
1.35350752 7.82825232 2.91184616 56.000000 0 201 54
1.35905170 7.82504892 2.91284609 49.000000 0 201 54
1.31357431 7.81813622 2.92184615 50.000000 0 201 54
```

## Slice Type Detection

The parser analyzes coordinate variations to determine slice types:

- **XY slice**: Z variation ≤ threshold (default 0.015)
- **XZ slice**: Y variation ≤ threshold  
- **YZ slice**: X variation ≤ threshold
- **Unknown**: No dimension constant enough

## Testing

Run the test suite:

```bash
# Run all tests
python run_tests.py

# Run specific test file
python tests/test_parse_file.py
```

## Code Quality

### Local Formatting and Linting

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

### Format Code with Black

```bash
# Auto-format code
black src/ tests/
```

### Run All Quality Checks

Use the provided script to run the same checks as CI:

```bash
python lint.py
```

This will:
- ✅ Check code formatting (Black)
- ✅ Check for critical linting issues (flake8)
- ✅ Show style warnings
- ✅ Report if code is ready to push

### Pre-commit Workflow

Before committing changes:

```bash
1. python lint.py        # Check code quality
2. black src/ tests/     # Fix formatting if needed  
3. python run_tests.py   # Run tests
4. git add & commit      # Push with confidence!
```


Automated testing runs on:
- Push to main branch
- Pull requests
- Ubuntu latest with Python 3.11
- Includes code quality checks (formatting, linting)

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
