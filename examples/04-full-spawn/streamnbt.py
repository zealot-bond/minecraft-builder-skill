"""Streaming structure-NBT writer.

The arena alone is 148k blocks and the plateau fill pushes the total past a
million, so the old `build_structure` (which materialises a list of compounds)
is not affordable.  This writer walks the grid twice - once to count, once to
emit - and gzips straight to disk, so peak RAM is one block's worth of bytes.
"""
import os, struct, gzip

TAG_INT = 3
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10


def _pstr(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


_POS = _pstr('pos')
_STATE = _pstr('state')
_ENTRY_PRE = b'\x09' + _POS + struct.pack('>Bi', TAG_INT, 3)
_ENTRY_MID = struct.pack('>B', TAG_INT) + _STATE


def write_structure(path, size, palette, count, iterator, data_version=5023):
    """palette: [(name, props_dict|None)]; iterator yields (x, y, z, idx)."""
    tmp = path + '.tmp'
    with gzip.open(tmp, 'wb', compresslevel=6) as f:
        f.write(b'\x0a' + _pstr(''))
        f.write(struct.pack('>B', TAG_INT) + _pstr('DataVersion')
                + struct.pack('>i', data_version))
        f.write(struct.pack('>B', TAG_LIST) + _pstr('size')
                + struct.pack('>Bi', TAG_INT, 3) + struct.pack('>iii', *size))
        f.write(struct.pack('>B', TAG_LIST) + _pstr('palette')
                + struct.pack('>Bi', TAG_COMPOUND, len(palette)))
        for name, props in palette:
            body = struct.pack('>B', TAG_STRING) + _pstr('Name') + _pstr(name)
            if props:
                body += struct.pack('>B', TAG_COMPOUND) + _pstr('Properties')
                for k in sorted(props):
                    body += (struct.pack('>B', TAG_STRING) + _pstr(k)
                             + _pstr(str(props[k])))
                body += b'\x00'
            f.write(body + b'\x00')
        f.write(struct.pack('>B', TAG_LIST) + _pstr('blocks')
                + struct.pack('>Bi', TAG_COMPOUND, count))
        # A compound *inside* a TAG_List is a bare payload: the element type is
        # already in the list header and a list element has NO name.  Writing
        # b'\x0a\x00\x00' here inserted three stray bytes per block and every
        # parser then read the element as empty.
        head = _ENTRY_PRE
        for x, y, z, idx in iterator:
            f.write(head)
            f.write(struct.pack('>iii', x, y, z))
            f.write(_ENTRY_MID)
            f.write(struct.pack('>i', idx))
            f.write(b'\x00')
        f.write(struct.pack('>B', TAG_LIST) + _pstr('entities')
                + struct.pack('>Bi', TAG_COMPOUND, 0))
        f.write(b'\x00')
    os.replace(tmp, path)
    return os.path.getsize(path)
