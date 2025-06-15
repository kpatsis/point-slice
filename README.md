# Point Slice Parser

[![Tests](https://github.com/YOUR_USERNAME/point_slice/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/point_slice/actions/workflows/ci.yml)

A Python library for parsing and analyzing 3D point cloud data from space-separated CSV files and DXF files.

## Features

- **Data-based slice type detection**: Automatically determines if points form XY, XZ, YZ, or unknown slice patterns
- **Configurable thresholds**: Customizable precision for slice detection
- **Random sampling**: Efficient analysis of large datasets using representative samples
- **Color assignment**: Automatic color coding based on slice type and filename patterns
- **Batch processing**: Parse entire directories of CSV files
- **DXF integration**: Compatible with existing DXF workflow in `point_slice_studio.py`

## Quick Start

```python
from src.parse_file import parse_csv_file, parse_directory

# Parse a single file
slice_obj = parse_csv_file("data/points.csv", max_points=1000)
print(f"Detected {slice_obj.slice_type.value} slice with {len(slice_obj.points)} points")

# Parse entire directory
slices = parse_directory("data/csv_files/", max_points_per_file=500)
print(f"Loaded {len(slices)} slice files")
```

## File Format

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

## Dependencies

- Python 3.8+
- ezdxf >= 1.0.0

## Development

The project includes comprehensive unit tests (24 tests) covering:

- Slice type detection with various point configurations
- Color assignment logic
- File parsing with error handling
- Directory batch processing
- Edge cases and error conditions

## GitHub Actions

Automated testing runs on:
- Push to main/master branch
- Pull requests
- Ubuntu latest with Python 3.11
- Includes code quality checks (formatting, linting)
