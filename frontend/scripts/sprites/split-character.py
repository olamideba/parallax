#!/usr/bin/env python3
"""
split-character.py — Split a 2x2 character sprite sheet into 4 directional PNGs.

Adapted from W17ant/agent-office (Claude Office). Differences:
  - Output names are clean: {role}-{direction}.png  (no "-1" suffix)
  - Default output dir is frontend/public/replay/sprites/
  - Auto-trims transparent edges per quadrant

Usage:
    python3 split-character.py <sheet.png> <role>
    python3 split-character.py advocate-sheet.png advocate

The input sheet is a 2x2 grid on a transparent background:
    ┌──────────┬───────────┐
    │front-left│front-right│
    ├──────────┼───────────┤
    │rear-left │rear-right │
    └──────────┴───────────┘

Outputs (into the output dir):
    {role}-front-left.png   {role}-front-right.png
    {role}-rear-left.png    {role}-rear-right.png

For the seated seminar layout the renderer only needs front-left / front-right,
but all four are produced (rear-* are free, useful for a walk-in entrance later).
"""

import argparse
import os
import sys

DEFAULT_OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "public", "replay", "sprites",
)


def split(input_path: str, role: str, output_dir: str) -> None:
    from PIL import Image

    img = Image.open(input_path).convert("RGBA")
    w, h = img.size
    hw, hh = w // 2, h // 2
    quadrants = {
        "front-left": (0, 0, hw, hh),
        "front-right": (hw, 0, w, hh),
        "rear-left": (0, hh, hw, h),
        "rear-right": (hw, hh, w, h),
    }
    for direction, box in quadrants.items():
        q = img.crop(box)
        bbox = q.getbbox()  # auto-trim transparent margins
        if bbox:
            q = q.crop(bbox)
        out = os.path.join(output_dir, f"{role}-{direction}.png")
        q.save(out, "PNG")
        print(f"  ✓ {out} ({q.size[0]}x{q.size[1]})")


def main() -> None:
    p = argparse.ArgumentParser(description="Split a 2x2 sprite sheet into 4 directions.")
    p.add_argument("input", help="Path to the 2x2 sprite sheet")
    p.add_argument("role", help="Role key, e.g. advocate|auditor|assessor|arbitrator|gatekeeper")
    p.add_argument("--output-dir", "-o", default=DEFAULT_OUT)
    args = p.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: input not found: {args.input}")
        sys.exit(1)
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\nSplitting {args.input} → '{args.role}' into {args.output_dir}\n")
    try:
        split(args.input, args.role, args.output_dir)
    except ImportError:
        print("Pillow required:  pip3 install Pillow")
        sys.exit(1)
    print("\nDone. Add the role to the asset manifest if it isn't there yet.\n")


if __name__ == "__main__":
    main()
