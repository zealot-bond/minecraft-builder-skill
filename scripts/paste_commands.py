#!/usr/bin/env python3
"""Emit the FAWE command lists for a safe paste, with the void arithmetic baked in.

    paste_commands.py --pos 195 42 259 --size 270 98 270 --schem macetopia-v6 \
                      --blocks 2126796 --outdir cmds/

Writes three JSON arrays meant to be run as SEPARATE console sessions (a single
session times out on multi-million-block pastes):

    cmds/01-paste.json    load + paste
    cmds/02-void.json     select the box + clear structure_void
    cmds/03-verify.json   save + count the blocks you care about

It prints the expected `N blocks have been replaced.` value; compare the server's
answer to it. Equality proves the paste was complete:
    void_replaced == sx*sy*sz - blocks
"""
import os, json, argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pos', nargs=3, type=int, required=True, metavar=('X', 'Y', 'Z'))
    ap.add_argument('--size', nargs=3, type=int, required=True, metavar=('SX', 'SY', 'SZ'))
    ap.add_argument('--schem', required=True, help='name inside plugins/FastAsyncWorldEdit/schematics')
    ap.add_argument('--blocks', type=int, help='block count written to the NBT')
    ap.add_argument('--count', nargs='*', default=[], metavar='minecraft:block',
                    help='blocks to //count for verification')
    ap.add_argument('--outdir', default='cmds')
    ap.add_argument('--world', default='world')
    a = ap.parse_args()

    px, py, pz = a.pos
    sx, sy, sz = a.size
    x2, y2, z2 = px + sx - 1, py + sy - 1, pz + sz - 1
    os.makedirs(a.outdir, exist_ok=True)

    files = {
        '01-paste.json': ['//world ' + a.world,
                          '//pos1 %d,%d,%d' % (px, py, pz),
                          '//schem load ' + a.schem,
                          '//paste'],
        '02-void.json': ['//world ' + a.world,
                         '//pos1 %d,%d,%d' % (px, py, pz),
                         '//pos2 %d,%d,%d' % (x2, y2, z2),
                         '//replace minecraft:structure_void minecraft:air'],
    }
    verify = ['//world ' + a.world, 'save-all flush',
              '//pos1 %d,%d,%d' % (px, py, pz),
              '//pos2 %d,%d,%d' % (x2, y2, z2),
              '//count minecraft:structure_void']
    verify += ['//count ' + c for c in a.count]
    files['03-verify.json'] = verify

    for name, cmds in files.items():
        path = os.path.join(a.outdir, name)
        with open(path, 'w') as f:
            json.dump(cmds, f, indent=1)
        print('%s  (%d commands)' % (path, len(cmds)))

    cell = sx * sy * sz
    print()
    print('box            : %d..%d  %d..%d  %d..%d' % (px, x2, py, y2, pz, z2))
    print('box volume     : %d' % cell)
    if a.blocks is not None:
        print('blocks written : %d' % a.blocks)
        print('EXPECT void replace = %d' % (cell - a.blocks))
        print()
        print('After 02-void.json the server must report exactly:')
        print('    %d blocks have been replaced.' % (cell - a.blocks))
        print('If it differs, STOP: wrong schematic loaded, interrupted paste,')
        print('or the box does not cover what you think it does.')
    print()
    print('Run each file in its own console session. Then 03-verify.json:')
    print('  structure_void must be 0, and each --count must equal the source count.')
    if a.blocks is not None and a.blocks <= 0:
        raise SystemExit('blocks must be > 0')


if __name__ == '__main__':
    main()
