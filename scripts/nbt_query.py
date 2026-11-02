#!/usr/bin/env python3
"""Read a vanilla structure NBT and report / query it.

Used both to sanity-check what you just wrote and to learn the exact block states
a working world uses (so you never guess a property).

    nbt_query.py out.nbt --summary
    nbt_query.py out.nbt --counts --top 25
    nbt_query.py out.nbt --bbox
    nbt_query.py out.nbt --at 100 73 200          world-space is caller's job
    nbt_query.py out.nbt --props minecraft:oak_stairs
    nbt_query.py out.nbt --hist y                blocks per Y
    nbt_query.py out.nbt --family leaves
"""
import sys, os, gzip, struct, argparse
from collections import Counter

# ------------------------------------------------------------------ minimal NBT
def read_nbt(raw, i=0):
    t = raw[i]; i += 1
    if t == 0:
        return None, i
    nl = struct.unpack_from('>H', raw, i)[0]; i += 2
    name = raw[i:i + nl].decode('utf-8', 'replace'); i += nl
    v, i = payload(raw, i, t)
    return (name, v), i


def payload(raw, i, t):
    if t == 1: return struct.unpack_from('>b', raw, i)[0], i + 1
    if t == 2: return struct.unpack_from('>h', raw, i)[0], i + 2
    if t == 3: return struct.unpack_from('>i', raw, i)[0], i + 4
    if t == 4: return struct.unpack_from('>q', raw, i)[0], i + 8
    if t == 5: return struct.unpack_from('>f', raw, i)[0], i + 4
    if t == 6: return struct.unpack_from('>d', raw, i)[0], i + 8
    if t == 7:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return raw[i:i + n], i + n
    if t == 8:
        n = struct.unpack_from('>H', raw, i)[0]; i += 2
        return raw[i:i + n].decode('utf-8', 'replace'), i + n
    if t == 9:
        et = raw[i]; n = struct.unpack_from('>i', raw, i + 1)[0]; i += 5
        out = []
        for _ in range(n):
            v, i = payload(raw, i, et); out.append(v)
        return out, i
    if t == 10:
        out = {}
        while True:
            tt = raw[i]; i += 1
            if tt == 0: break
            nl = struct.unpack_from('>H', raw, i)[0]; i += 2
            nm = raw[i:i + nl].decode('utf-8', 'replace'); i += nl
            v, i = payload(raw, i, tt); out[nm] = v
        return out, i
    if t == 11:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return [struct.unpack_from('>i', raw, i + 4 * k)[0] for k in range(n)], i + 4 * n
    if t == 12:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return [struct.unpack_from('>q', raw, i + 8 * k)[0] for k in range(n)], i + 8 * n
    raise ValueError('bad tag %d at %d' % (t, i))


def load(path):
    with gzip.open(path, 'rb') as f:
        raw = f.read()
    (name, root), i = read_nbt(raw, 0)
    return root, len(raw) - i


def state_name(entry):
    return (entry.get('Name') if isinstance(entry, dict) else entry).split(':')[-1]


def state_full(entry):
    nm = entry.get('Name') if isinstance(entry, dict) else entry
    pr = entry.get('Properties') if isinstance(entry, dict) else None
    if not pr:
        return nm
    inner = ','.join('%s=%s' % (k, v) for k, v in sorted(pr.items()))
    return '%s[%s]' % (nm, inner)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('nbt')
    ap.add_argument('--summary', action='store_true')
    ap.add_argument('--counts', action='store_true')
    ap.add_argument('--top', type=int, default=15)
    ap.add_argument('--bbox', action='store_true')
    ap.add_argument('--at', nargs=3, type=int, metavar=('X', 'Y', 'Z'))
    ap.add_argument('--props')
    ap.add_argument('--hist')
    ap.add_argument('--family')
    a = ap.parse_args()

    root, leftover = load(a.nbt)
    size = tuple(root['size'])
    bpal = root['palette']
    blocks = root['blocks']

    if leftover:
        print('!! WARNING: %d trailing bytes after root — file is malformed'
              % leftover, file=sys.stderr)

    if a.summary or not any([a.counts, a.bbox, a.at, a.props, a.hist, a.family]):
        nprop = sum(1 for e in bpal if isinstance(e, dict) and e.get('Properties'))
        print('file            : %s' % a.nbt)
        print('DataVersion     : %s' % root.get('DataVersion'))
        print('size            : %d x %d x %d  (%d cells)'
              % (size[0], size[1], size[2], size[0] * size[1] * size[2]))
        print('palette         : %d states (%d with properties)' % (len(bpal), nprop))
        print('blocks          : %d' % len(blocks))
        print('fill of box     : %.1f%%' % (100.0 * len(blocks) /
                                            max(1, size[0] * size[1] * size[2])))
        print('void if pasted  : %d' % (size[0] * size[1] * size[2] - len(blocks)))
        if state_name(bpal[0]) != 'air':
            print('!! palette[0] is %r, expected air' % state_name(bpal[0]))
        if leftover:
            print('!! file has trailing garbage')

    if a.counts or a.family:
        c = Counter(state_name(bpal[b['state']]) for b in blocks)
        if a.family:
            fam = a.family
            sel = {k: v for k, v in c.items() if fam in k}
        else:
            sel = dict(c.most_common(a.top))
        for k, v in sorted(sel.items(), key=lambda kv: -kv[1]):
            print('%-38s %8d' % (k, v))

    if a.bbox:
        xs = [b['pos'][0] for b in blocks]
        ys = [b['pos'][1] for b in blocks]
        zs = [b['pos'][2] for b in blocks]
        print('bbox local: x %d..%d  y %d..%d  z %d..%d'
              % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
        oob = sum(1 for b in blocks
                  if not (0 <= b['pos'][0] < size[0] and 0 <= b['pos'][1] < size[1]
                          and 0 <= b['pos'][2] < size[2]))
        print('out of bounds: %d' % oob)

    if a.at:
        want = tuple(a.at)
        for b in blocks:
            if tuple(b['pos']) == want:
                print('%s -> %s' % (want, state_full(bpal[b['state']])))
                break
        else:
            print('%s -> (empty)' % (want,))

    if a.props:
        seen = Counter()
        for b in blocks:
            e = bpal[b['state']]
            nm = e.get('Name') if isinstance(e, dict) else e
            if nm == a.props:
                seen[state_full(e)] += 1
        if not seen:
            print('no blocks named %r' % a.props)
        for k, v in seen.most_common():
            print('%-70s %7d' % (k, v))

    if a.hist:
        axis = {'x': 0, 'y': 1, 'z': 2}[a.hist]
        c = Counter(b['pos'][axis] for b in blocks)
        for k in sorted(c):
            print('%4d %8d %s' % (k, c[k], '#' * min(60, c[k] // max(1, len(blocks) // 600))))


if __name__ == '__main__':
    main()
