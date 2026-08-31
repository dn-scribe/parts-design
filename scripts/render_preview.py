#!/usr/bin/env python3
"""
Render a static isometric preview.png from a design's STL, for embedding in
READMEs (GitHub markdown can't embed an interactive glTF/GLB viewer inline,
so a raster preview is the only way to show the part's shape without
clicking through to the file). Pure matplotlib + trimesh, no FreeCAD needed.

Usage:
    python3 scripts/render_preview.py designs/<name>/outputs/<name>.stl \
        designs/<name>/outputs/preview.png
"""

import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def render(stl_path, png_path, size=800):
    mesh = trimesh.load(stl_path)

    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_proj_type("persp")

    tris = mesh.vertices[mesh.faces]
    normals = mesh.face_normals
    light = np.array([0.4, -0.5, 0.8])
    light = light / np.linalg.norm(light)
    shade = np.clip(normals @ light, 0.15, 1.0)
    base = np.array([0.35, 0.55, 0.85])
    colors = base[None, :] * shade[:, None]
    colors = np.clip(colors, 0, 1)

    coll = Poly3DCollection(tris, facecolor=colors, edgecolor=(0, 0, 0, 0.15), linewidths=0.2)
    ax.add_collection3d(coll)

    bounds = mesh.bounds
    center = bounds.mean(axis=0)
    extent = (bounds[1] - bounds[0]).max() / 2.0
    ax.set_xlim(center[0] - extent, center[0] + extent)
    ax.set_ylim(center[1] - extent, center[1] + extent)
    ax.set_zlim(center[2] - extent, center[2] + extent)
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=28, azim=-52)
    ax.set_axis_off()

    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    fig.savefig(png_path, transparent=True)
    plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    render(sys.argv[1], sys.argv[2])
    print("Wrote", sys.argv[2])
