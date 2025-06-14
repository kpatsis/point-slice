
# point_slice_studio_v7.py
# Τελική έκδοση με layer coloring, legend text και σωστή διαχείριση offsets & blocks

import ezdxf
import os
import random
import re
from ezdxf.entities import Point
from collections import defaultdict

def ask_user_input():
    folder = input("📂 Drag and drop τον φάκελο με τα DXF slices και πάτα Enter: ").strip('"')
    floor_info = input("🏢 Δώσε ορόφους και slices (π.χ. Υπόγειο 01-03, Α Όροφος 04-06): ").strip()
    offset = int(input("📏 Δώσε vertical offset (π.χ. 100): ").strip())
    return folder, floor_info, offset

def parse_floor_info(info):
    mapping = {}
    floor_names = []
    for part in info.split(','):
        if not part.strip(): continue
        floor, rng = part.strip().split(maxsplit=1)
        floor_upper = floor.upper()
        floor_names.append(floor_upper)
        nums = []
        for r in rng.split(','):
            if '-' in r:
                a, b = r.split('-')
                nums.extend(range(int(a), int(b)+1))
            else:
                nums.append(int(r))
        for n in nums:
            mapping[f"{n:02}"] = floor_upper
    return mapping, floor_names

def detect_slice_type(points):
    zs = [p.dxf.location.z for p in points]
    ys = [p.dxf.location.y for p in points]
    xs = [p.dxf.location.x for p in points]
    dz = max(zs) - min(zs)
    dy = max(ys) - min(ys)
    dx = max(xs) - min(xs)
    if dz <= 0.015: return 'XY'
    if dy <= 0.015: return 'XZ'
    if dx <= 0.015: return 'YZ'
    return 'UNKNOWN'

def get_random_sample(msp, size=250):
    points = [e for e in msp if isinstance(e, Point)]
    return random.sample(points, min(len(points), size))

def assign_color(index, total):
    palette = [5, 4, 2, 3, 30, 1, 6, 241]  # blue, cyan, yellow, green, orange, red, magenta, pink
    return palette[index % len(palette)]

def create_block(doc, name, points, layer, color, z_avg=None, floor=None, text_pos=None):
    blk = doc.blocks.new(name=name)
    for p in points:
        new_p = blk.add_point(p.dxf.location)
        new_p.dxf.layer = layer
        new_p.dxf.color = color
    if z_avg is not None and floor and text_pos:
        text = blk.add_text(f"Z: {z_avg:.2f} | {floor}", dxfattribs={
            "height": 0.7,
            "layer": layer,
            "color": color
        })
        text.set_placement(text_pos)
    return blk

def main():
    folder, floor_info, offset = ask_user_input()
    mapping, floor_names = parse_floor_info(floor_info)
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith('.dxf'))

    slice_data = []
    all_xy_samples = []

    merged = ezdxf.new(setup=True)
    msp = merged.modelspace()

    for filename in files:
        path = os.path.join(folder, filename)
        doc = ezdxf.readfile(path)
        msp_in = doc.modelspace()
        sample = get_random_sample(msp_in)
        slice_type = detect_slice_type(sample)
        prefix = filename[:2]
        floor = mapping.get(prefix, "UNKNOWN")
        z_avg = sum(p.dxf.location.z for p in sample) / len(sample)
        slice_data.append((filename, slice_type, z_avg, sample, floor))
        if slice_type == 'XY':
            all_xy_samples.extend(sample)

    if all_xy_samples:
        max_y = max(p.dxf.location.y for p in all_xy_samples)
        min_x = min(p.dxf.location.x for p in all_xy_samples)
        text_origin = (min_x - 20, max_y - 20)

    # Ταξινόμηση XY slices κατά z_avg
    xy_slices = sorted([s for s in slice_data if s[1] == 'XY'], key=lambda x: x[2])

    for i, (filename, slice_type, z_avg, sample, floor) in enumerate(slice_data):
        path = os.path.join(folder, filename)
        doc = ezdxf.readfile(path)
        msp_in = doc.modelspace()
        points = msp_in.query('POINT')
        layer = filename
        if slice_type == 'XY':
            color = assign_color(xy_slices.index((filename, slice_type, z_avg, sample, floor)), len(xy_slices))
        elif slice_type == 'XZ':
            color = 6  # magenta
        elif slice_type == 'YZ':
            color = 1  # red
        else:
            color = 7  # default white

        text_pos = None
        if slice_type == 'XY' and all_xy_samples:
            text_pos = (text_origin[0], text_origin[1] - i * 1.4)

        blk = create_block(merged, filename, points, layer, color, z_avg if slice_type == 'XY' else None, floor, text_pos)
        msp.add_blockref(blk.name, insert=(0, 0, 0))

        if floor in floor_names:
            idx = floor_names.index(floor)
            y_offset = - (idx + 1) * offset
            msp.add_blockref(blk.name, insert=(0, y_offset, 0))

    merged.saveas(os.path.join(folder, "00_point_cloud_merged.dxf"))
    input("✅ Τέλος εκτέλεσης. Πάτα Enter για έξοδο.")

if __name__ == "__main__":
    main()
