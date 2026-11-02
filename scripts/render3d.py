"""Real full-cube voxel renderer: orthographic 3D, face culling, painter's algorithm."""
import sys, gzip, struct, math
from PIL import Image, ImageDraw
sys.path.insert(0,'/home/rhythm/Documents/kayleesmp/mace-work')

def read_struct(path):
    raw=gzip.open(path,'rb').read(); i=0
    def rd(f):
        nonlocal i; v=struct.unpack_from(f,raw,i); i+=struct.calcsize(f); return v[0]
    def rstr():
        nonlocal i; n=struct.unpack_from('>H',raw,i)[0]; i+=2; s=raw[i:i+n].decode('utf-8','replace'); i+=n; return s
    def parse(t):
        nonlocal i
        if t==1: return rd('>b')
        if t==2: return rd('>h')
        if t==3: return rd('>i')
        if t==4: return rd('>q')
        if t==5: return rd('>f')
        if t==6: return rd('>d')
        if t==7: n=rd('>i'); v=raw[i:i+n]; i+=n; return v
        if t==8: return rstr()
        if t==9:
            et=rd('>B'); n=rd('>i'); return [parse(et) for _ in range(n)]
        if t==10:
            d={}
            while True:
                tt=rd('>B')
                if tt==0: return d
                k=rstr(); d[k]=parse(tt)
        if t==11: n=rd('>i'); return [rd('>i') for _ in range(n)]
        if t==12: n=rd('>i'); return [rd('>q') for _ in range(n)]
        raise ValueError(t)
    t=rd('>B'); rstr(); return parse(t)

PAL={'red_concrete':(180,36,36),'blue_stained_glass':(48,96,214),'water':(50,110,214),
 'grass_block':(106,158,74),'short_grass':(126,176,84),'grass':(126,176,84),'fern':(96,146,72),
 'tall_grass':(126,176,84),'dirt':(134,96,67),'rooted_dirt':(124,88,62),'coarse_dirt':(120,86,60),
 'sand':(226,214,166),'suspicious_sand':(220,206,158),'terracotta':(152,94,72),
 'polished_granite':(160,110,95),'stone':(136,136,138),'andesite':(132,132,134),
 'tuff':(108,110,102),'deepslate':(86,86,92),'polished_andesite':(138,138,140),
 'quartz_block':(238,232,222),'dark_prismarine':(58,120,114),'sea_lantern':(206,228,208),
 'dirt_path':(150,120,80),'warped_planks':(44,140,132),'jungle_leaves':(56,126,42),
 'oak_leaves':(62,124,46),'jungle_wood':(96,78,48),'jungle_log':(96,78,48),'oak_wood':(150,112,66),
 'oak_log':(150,112,66),'light_blue_concrete':(110,190,240),'pink_concrete':(238,150,175),
 'black_concrete':(30,30,34),'campfire':(234,144,64),'player_head':(255,120,210),
 'player_wall_head':(255,120,210),'lantern':(250,232,160),'chain':(96,96,102),
 'iron_chain':(96,96,102),'moss_carpet':(96,140,70),'spruce_trapdoor':(126,96,58),
 'spruce_slab':(126,96,58),'spruce_planks':(126,96,58),'stone_slab':(140,140,142),
 'pink_petals':(238,170,200),'cherry_planks':(226,168,168),'cherry_slab':(226,168,168),
 'light_blue_candle':(240,230,180),'lodestone':(96,100,116),'diamond_block':(96,220,214),
 'verdant_froglight':(190,238,196),'pearlescent_froglight':(238,208,232),'farmland':(92,66,44),
 'carrots':(240,150,60),'wheat':(196,176,96),'barrel':(146,110,66),'beehive':(200,170,100),
 'chest':(170,130,70),'shulker_box':(160,110,160),'ender_chest':(60,52,70),'hopper':(80,80,86),
 'glass':(170,200,220),'pink_stained_glass':(238,170,200),'white_concrete':(210,210,214),
 'red_terracotta':(140,60,46),'spruce_fence':(126,96,58),'oak_fence':(150,112,66),
 'stone_bricks':(122,122,124),'cobblestone':(120,120,122),'gravel':(132,126,120),
 'moss_block':(96,140,70),'azalea_leaves':(96,140,70),'flowering_azalea_leaves':(150,120,140),
 'bamboo':(140,170,80),'sugar_cane':(150,180,90),'pumpkin':(220,150,50),'melon':(150,180,70),
 'banner':(150,60,60),'sign':(150,112,66),'brushable_block':(210,190,150),'bee_nest':(200,170,100),
 'ladder':(150,112,66),'cobweb':(200,200,200),'tripwire':(90,90,90)}
def col(nm):
    n=nm.replace('minecraft:','')
    if n in PAL: return PAL[n]
    if 'leaves' in n: return (58,124,44)
    if 'glass' in n: return (150,190,220)
    if 'concrete' in n:
        base={'light_blue':(110,190,240),'pink':(238,150,175),'red':(180,36,36),
              'white':(210,210,214),'black':(30,30,34),'blue':(48,70,190)}
        for k,v in base.items():
            if k in n: return v
        return (160,160,164)
    if 'terracotta' in n: return (152,94,72)
    if 'sand' in n: return (226,214,166)
    if 'slab' in n or 'stairs' in n or 'wall' in n: return (140,140,142)
    if 'fence' in n or 'trapdoor' in n or 'planks' in n or 'wood' in n or 'log' in n: return (140,104,64)
    if 'flower' in n or 'tulip' in n or 'poppy' in n or 'petal' in n: return (226,150,180)
    if 'candle' in n or 'lantern' in n: return (240,226,170)
    if 'stone' in n: return (130,130,132)
    if 'dirt' in n: return (126,90,62)
    if 'coral' in n: return (200,110,150)
    h=(abs(hash(n))*2654435761)&0xffffff
    return (96+(h&63), 96+((h>>8)&63), 96+((h>>16)&63))

def load(path):
    r=read_struct(path); sx,sy,sz=r['size']; pal=r['palette']
    g={}
    for b in r['blocks']:
        p=pal[b['state']]['Name']
        g[(b['pos'][0],b['pos'][1],b['pos'][2])]=p
    return sx,sy,sz,g

FACE={'px':(1,0,0),'nx':(-1,0,0),'py':(0,1,0),'ny':(0,-1,0),'pz':(0,0,1),'nz':(0,0,-1)}
SHADE={'py':1.00,'ny':0.42,'px':0.78,'nx':0.62,'pz':0.88,'nz':0.55}

def corners(x,y,z,d):
    if d=='py': return [(x,y+1,z),(x+1,y+1,z),(x+1,y+1,z+1),(x,y+1,z+1)]
    if d=='ny': return [(x,y,z),(x,y,z+1),(x+1,y,z+1),(x+1,y,z)]
    if d=='px': return [(x+1,y,z),(x+1,y,z+1),(x+1,y+1,z+1),(x+1,y+1,z)]
    if d=='nx': return [(x,y,z+1),(x,y,z),(x,y+1,z),(x,y+1,z+1)]
    if d=='pz': return [(x,y,z+1),(x+1,y,z+1),(x+1,y+1,z+1),(x,y+1,z+1)]
    return [(x+1,y,z),(x,y,z),(x,y+1,z),(x+1,y+1,z)]

def render(g, size, out, cam=(1.0,0.80,1.0), W=900, scale=None, bg=(12,13,17)):
    sx,sy,sz=size
    cx,cy,cz=sx/2.0, sy/2.0, sz/2.0
    vx,vy,vz=cam
    L=math.sqrt(vx*vx+vy*vy+vz*vz); vx,vy,vz=vx/L,vy/L,vz/L
    # right = normalize(cross(view, worldUp))
    rx,ry,rz = (vz*1.0 - 0.0, 0.0, -vx*1.0)  # cross((vx,vy,vz),(0,1,0)) = (vz*1-0, 0-vz*0? ) compute properly
    # cross(v, up) where up=(0,1,0): (vy*0 - vz*1, vz*0 - vx*0, vx*1 - vy*0) = (-vz, 0, vx)
    rx,ry,rz = -vz, 0.0, vx
    rl=math.sqrt(rx*rx+rz*rz); rx,rz=rx/rl, rz/rl
    # up2 = cross(right, view)
    ux = ry*vz - rz*vy
    uy = rz*vx - rx*vz
    uz = rx*vy - ry*vx
    ul=math.sqrt(ux*ux+uy*uy+uz*uz); ux,uy,uz=ux/ul,uy/ul,uz/ul
    pts=[]
    for (x,y,z),nm in g.items():
        for d,(dx,dy,dz) in FACE.items():
            if (x+dx,y+dy,z+dz) in g: continue
            pts.append((x,y,z,d,nm))
    # depth along view dir (bigger = closer to camera) -> draw ascending
    def depth(p):
        x,y,z,_,_=p
        return (x+0.5-cx)*vx+(y+0.5-cy)*vy+(z+0.5-cz)*vz
    pts.sort(key=depth)
    # project
    proj=[]
    for x,y,z,d,nm in pts:
        q=[]
        for (a,b,c) in corners(x,y,z,d):
            a-=cx; b-=cy; c-=cz
            u=a*rx+b*ry+c*rz
            vv=a*ux+b*uy+c*uz
            q.append((u,vv))
        proj.append((q,d,nm))
    us=[p[0] for f in proj for p in f[0]]; vs=[p[1] for f in proj for p in f[0]]
    minu,maxu=min(us),max(us); minv,maxv=min(vs),max(vs)
    span=max(maxu-minu,(maxv-minv)*1.0)
    if scale is None: scale=(W-40)/max(maxu-minu, 1e-9)
    H=int((maxv-minv)*scale)+40
    img=Image.new('RGB',(W,H),bg); dr=ImageDraw.Draw(img)
    ox = 20 - minu*scale; oy = H-20 + minv*scale
    for q,d,nm in proj:
        s=SHADE[d]
        c=col(nm)
        poly=[(p[0]*scale+ox, -p[1]*scale+oy) for p in q]
        dr.polygon(poly, fill=(int(c[0]*s),int(c[1]*s),int(c[2]*s)))
    img.save(out); return img.size, len(proj)

VIEWS = {
    'iso':    (1.00, 0.80, 1.00),
    'top':    (0.00, 1.00, 0.001),
    'low':    (1.00, 0.20, 0.35),
    'west':   (-1.00, 0.50, 0.55),
    'east':   (1.00, 0.30, 0.25),
    'corner': (-1.00, 0.45, -1.00),
}

if __name__ == '__main__':
    # two forms:
    #   render3d.py in.nbt out.png [W cx cy cz]        (positional, legacy)
    #   render3d.py in.nbt --views iso,top --outdir r  (documented)
    if len(sys.argv) > 2 and sys.argv[2].startswith('--'):
        import argparse, os
        ap = argparse.ArgumentParser()
        ap.add_argument('nbt')
        ap.add_argument('--views', default='iso,top')
        ap.add_argument('--outdir', default='renders')
        ap.add_argument('--width', type=int, default=1100)
        ap.add_argument('--prefix', default=None)
        a = ap.parse_args()
        os.makedirs(a.outdir, exist_ok=True)
        sx, sy, szk, g = load(a.nbt)
        base = a.prefix or os.path.splitext(os.path.basename(a.nbt))[0]
        want = [v.strip() for v in a.views.split(',') if v.strip()]
        for v in want:
            cam = VIEWS.get(v)
            if cam is None:
                print('unknown view %r (have %s)' % (v, ','.join(VIEWS)))
                continue
            out = os.path.join(a.outdir, '%s-%s.png' % (base, v))
            render(g, (sx, sy, szk), out, cam=cam, W=a.width)
            print('%-8s -> %s' % (v, out))
    else:
        src = sys.argv[1]; out = sys.argv[2]
        W = int(sys.argv[3]) if len(sys.argv) > 3 else 900
        cx = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        cy = float(sys.argv[5]) if len(sys.argv) > 5 else 0.80
        cz = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
        sx, sy, sz, g = load(src)
        n = len(g)
        sz2, faces = render(g, (sx, sy, sz), out, cam=(cx, cy, cz), W=W)
        print(f'{src}: {sx}x{sy}x{sz}, {n} blocks, {faces} visible faces -> {out} {sz2}')
