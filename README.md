# Point Slice Studio v7

A Python tool for processing and merging 3D point cloud data from DXF files.

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the script:**
   ```bash
   python src/point_slice_studio_v7.py
   ```

## Usage

- Drag and drop the folder containing DXF slice files
- Specify floor information (e.g., "Basement 01-03, Floor A 04-06")  
- Set vertical offset value (e.g., 100)
- Output: `00_point_cloud_merged.dxf` in your input folder 
