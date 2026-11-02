#!/usr/bin/env python3
"""Render a structure as a grid of chunk tiles -- the only reliable way to spot
"slop" inside a large build.

A single wide shot hides everything that matters: floating canopies, banners
hanging on air, bare patches. A 4x4 contact sheet of 25-block tiles makes them
obvious.

    chunk_sheet.py out.nbt --box 85 85 100 100 --tiles 4 --out sheet.png
    chunk_sheet.py out.nbt --box 85 85 100 100 --tiles 4 --y 18 88 --step 2

Tiles are cropped from the same voxel renderer used by render3d.py, so no extra
dependencies.
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d
from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('nbt')
    ap.add_argument('--box', nargs=4, type=int, required=True,
                    metavar=('X0', 'Z0', 'SIZE', 'SIZE'))
    ap.add_argument('--tiles', type=int, default=4)
    ap.add_argument('--y', nargs=2, type=int, default=None, metavar=('Y0', 'Y1'),
                    help='vertical window (default: whole build)')
    ap.add_argument('--out', default='sheet.png')
    ap.add_argument('--tile-px', type=int, default=380)
    ap.add_argument('--step', type=int, default=1,
                    help='sample every Nth block (2 keeps big builds fast)')
    ap.add_argument('--cam', default='1.0,0.85,1.0')
    a = ap.parse_args()

    sx, sy, sz, g = render3d.load(a.nbt)
    x0, z0, w, h = a.box
    if a.y:
        y0, y1 = a.y
    else:
        y0, y1 = 0, sy
    tm = max(1, a.step)

    def crop(cx, cz, tw, th):
        sub = {}
        for (x, y, z), nm in g.items():
            if x0 + cx <= x < x0 + cx + tw and z0 + cz <= z < z0 + cz + th \
               and y0 <= y < y1:
                sub[((x - x0 - cx) // tm, (y - y0) // tm,
                     (z - z0 - cz) // tm)] = nm
        return sub

    tiles = a.tiles
    tw = max(1, w // tiles)
    th = max(1, h // tiles)
    TS = a.tile_px
    sheet = Image.new('RGB', (TS * tiles, TS * tiles), (12, 13, 17))
    dr = ImageDraw.Draw(sheet)
    cx_, cy_, cz_ = [float(v) for v in a.cam.split(',')]
    tmp = os.path.join(os.path.dirname(a.out) or '.', '_tile.png')
    for ti in range(tiles):
        for tj in range(tiles):
            sub = crop(ti * tw, tj * th, tw, th)
            if not sub:
                continue
            render3d.render(sub, (max(1, tw // tm), max(1, (y1 - y0) // tm),
                                  max(1, th // tm)), tmp,
                            cam=(cx_, cy_, cz_), W=TS)
            sheet.paste(Image.open(tmp).convert('RGB'), (ti * TS, tj * TS))
            dr.text((ti * TS + 6, tj * TS + 4),
                    'x%d-%d z%d-%d' % (x0 + ti * tw, x0 + ti * tw + tw - 1,
                                       z0 + tj * th, z0 + tj * th + th - 1),
                    fill=(255, 255, 0))
    sheet.save(a.out)
    if os.path.exists(tmp):
        os.remove(tmp)
    print('wrote %s (%dx%d)' % (a.out, sheet.size[0], sheet.size[1]))


if __name__ == '__main__':
    main()
