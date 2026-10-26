# CLAUDE.md

Point Slice Studio converts directories of space-separated CSV point clouds (one slice per file) into a single DXF drawing, using `ezdxf`. There are two front ends: a CLI and a Tkinter GUI. Both are thin wrappers over the `ps_core` package. Licence: GPL-3.0-or-later. Every source file starts with a GPL header.

## Environment and commands

Run everything from the repo root with the project venv active. System Python lacks the dependencies, and on Windows the emoji in the output crash a cp1252 console unless `PYTHONIOENCODING=utf-8` is set.

```bash
source venv/Scripts/activate            # Git Bash  (PowerShell: .\venv\Scripts\Activate.ps1)
pip install -e ".[dev]"                 # required: tests import ps_core as an installed package

PYTHONIOENCODING=utf-8 python run_tests.py                     # all tests (unittest discovery in tests/)
PYTHONIOENCODING=utf-8 python -m unittest tests.test_points_slice -v   # one module
PYTHONIOENCODING=utf-8 python -m unittest tests.test_points_slice.TestFilterSliceThickness.test_xz_filters_on_y

python lint.py                          # same checks as CI: black --check + flake8 critical set
black src/ tests/ point_slice_studio_cli.py point_slice_studio_gui.py   # auto-format

python point_slice_studio_cli.py [in_dir] [out.dxf] [--colors ..] [--threshold ..] [--thickness ..] ...
python point_slice_studio_gui.py
pyinstaller pyinstaller.spec            # builds dist/Point_Slice_Studio/ (GUI, windowed)
```

CI (`.github/workflows/ci.yml`, Ubuntu, Python 3.12) runs `lint.py` and `run_tests.py` on pushes and PRs to `main`. Lint fails on black diffs and on flake8 `E9,F63,F7,F82,F401,F841`, which means **unused imports and unused variables fail CI**. Other style warnings only print. `release.yml` builds a Windows PyInstaller zip when a GitHub release is published.

## Architecture

```
point_slice_studio_cli.py   argparse → validates colors/thickness → workflow
point_slice_studio_gui.py   Tk form → validates → runs workflow in a daemon thread
src/ps_core/
  points_slice.py   Point3D, SliceType (XY/XZ/YZ/UNKNOWN), PointsSlice dataclasses;
                    rotate_slice_to_xy(), filter_slice_thickness()  (pure, return new objects)
  parse_file.py     parse_csv_file(), parse_directory(), detect_slice_type_from_data()
  dxf_document.py   Block dataclass + DXFDocument (wraps an ezdxf Drawing)
  workflow.py       create_dxf_from_csv_directory(): the single end-to-end pipeline
```

Pipeline in `workflow.create_dxf_from_csv_directory`:
1. `parse_directory` reads every `*.csv` in **sorted filename order**. Columns 1–3 are X Y Z and extra columns are ignored. A file that fails to parse is printed as a warning and skipped.
2. Slice type detection takes a random sample of 250 points, finds the axis with the smallest range, and gives it the matching type if that range is ≤ `threshold`. Otherwise the slice is UNKNOWN. The smallest axis maps to a type as follows: Z → XY, Y → XZ, X → YZ.
3. If `thickness` is set, `filter_slice_thickness` keeps only the points inside a band of that width. The band is centred on the **midpoint of the range** (not the mean) along the constant axis. UNKNOWN slices and slices already thinner than the band are left unchanged.
4. Each slice becomes a `Block` named `Block_<name>` on layer `L_<name>`, inserted at the origin. `<name>` is the filename stem, except that `parse_csv_file` appends the level to XY slice names using `format_level` (the Z-range midpoint, rounded half-up to 2 decimals, e.g. `01_Of_Low+0.96`). The level therefore shows in the layer, block and label, and it is measured before any thickness filtering. XZ and YZ slices also get a second block, `Block_<name>_rotated`. It is rotated into the XY plane and inserted at `anchor + xz/yz_rotated_x_offset` on the **same layer**.
5. `DXFDocument.plot()` assigns colours round-robin, one per *new layer*. It rounds point coordinates to 4 decimal places. Each block gets a text label holding the slice name, starting at `label_start_position` with each next label 0.7 units lower. `save()` writes the DXF.

## Gotchas

- **The workflow reports errors with `print` and returns `False` instead of raising.** It returns `True` only once the DXF has been written, and the GUI picks its Success or Error dialog from that value. Any new failure path must print a `❌` line and `return False`. The GUI captures stdout into its log through a queue (`RedirectText`), so all progress must go through `print`.
- **Threshold defaults differ.** `detect_slice_type_from_data` defaults to 0.015, but `parse_csv_file`, `parse_directory`, the workflow and the CLI all pass 0.050. The README's "default 0.015" refers to the inner function. The GUI has no threshold field, so it always uses 0.050.
- **The real colour default is 6 colours, not 10.** When `--colors` is omitted, the CLI passes `colors=None`. That overrides the workflow's `[1..10]` default, so `DXFDocument` falls back to `[1..6]`. The GUI pre-fills "1 2 3 4 5 6 7 8 9 10".
- The `rotate_slice_to_xy` docstring says that YZ maps to `(y, x, z)`, but the code does `(y, z, x)`. Trust the code and the inline comment.
- `ps_core/__init__.py` does not re-export `filter_slice_thickness`. Import it from `ps_core.points_slice`.
- The CLI default input is `tests/testdata/02_csv`, which is real sample data of 10 files. It is also bundled into the PyInstaller build.
- `tests/test_dxf_document.py` writes `test_output.dxf` into the current directory. Generated `*.dxf` files are gitignored, and several large ones already sit in the repo root. `build/`, `dist/` and `temp/` are local artefacts.
- New CLI options are normally mirrored in the GUI, with a grey help label that names the CLI flag. Also update the options section of `README.md`.

## Conventions

- Black, line length 88, target py310 (`requires-python >= 3.10`). Use `typing.List`/`Optional` and dataclasses, matching the existing code.
- Tests use `unittest` (not pytest), with one `tests/test_<module>.py` per core module.
- Work happens on branches and merges through PRs. Commit and PR titles usually reference the GitHub issue, such as `Issue 27: ... (#28)`.
