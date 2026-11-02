"""Zone-grid planning helper (`design.md` <-> build script <-> `quality.py`).

Divides a plot `(size_x, size_z)` into cells (default 5x5 or 8x8 depending on plot
size) so every chunk of the build has an explicit purpose, features, and density target.
"""


def default_cell_size(nx, nz):
    span = min(nx, nz)
    if span <= 36:
        return 8
    if span <= 64:
        return 10
    if span <= 128:
        return 16
    return 20


class ZoneGrid:
    """Grid of planned zones over `(nx, nz)`."""

    def __init__(self, nx, nz, cell_size=None, ascii_map=None, legend=None):
        self.nx = int(nx)
        self.nz = int(nz)
        self.legend = dict(legend or {})
        if ascii_map:
            rows = [
                [tok for tok in line.strip().split() if tok]
                if ' ' in line.strip() else list(line.strip())
                for line in ascii_map.strip().splitlines()
                if line.strip() and not line.strip().startswith('#')
            ]
            if not rows:
                raise ValueError('Empty ascii_map')
            self.gz = len(rows)
            self.gx = max(len(r) for r in rows)
            for r in rows:
                if len(r) != self.gx:
                    raise ValueError('Ragged ascii_map row: %r' % (r,))
            self.codes = rows
        else:
            cs = cell_size or default_cell_size(nx, nz)
            self.gx = max(2, int(round(nx / float(cs))))
            self.gz = max(2, int(round(nz / float(cs))))
            self.codes = [['G' for _ in range(self.gx)] for _ in range(self.gz)]

    def cell_bounds(self, cx, cz):
        """Inclusive `(x0, z0, x1, z1)` for cell `(cx, cz)`."""
        x0 = (cx * self.nx) // self.gx
        x1 = ((cx + 1) * self.nx) // self.gx - 1
        z0 = (cz * self.nz) // self.gz
        z1 = ((cz + 1) * self.nz) // self.gz - 1
        return x0, z0, x1, z1

    def cell_center(self, cx, cz):
        x0, z0, x1, z1 = self.cell_bounds(cx, cz)
        return (x0 + x1) // 2, (z0 + z1) // 2

    def code_at_cell(self, cx, cz):
        return self.codes[cz][cx]

    def iter_cells(self):
        """Yield `(cx, cz, code, role_name, (x0, z0, x1, z1))`."""
        for cz in range(self.gz):
            for cx in range(self.gx):
                code = self.codes[cz][cx]
                role = self.legend.get(code, code)
                yield cx, cz, code, role, self.cell_bounds(cx, cz)

    def to_manifest(self):
        cells = []
        for cx, cz, code, role, (x0, z0, x1, z1) in self.iter_cells():
            cells.append({
                'cx': cx, 'cz': cz,
                'code': code, 'role': role,
                'bounds': [x0, z0, x1, z1],
            })
        return {
            'gx': self.gx,
            'gz': self.gz,
            'legend': self.legend,
            'ascii': [' '.join(r) for r in self.codes],
            'cells': cells,
        }
