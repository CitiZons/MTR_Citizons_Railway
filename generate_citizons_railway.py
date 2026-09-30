"""Deterministic, resource-only Citizons Railway model builder.

Metres, Y-up, outward CCW faces, standard OBJ UVs (MTR flipV=true).
Run: python generate_citizons_railway.py. Requires numpy and Pillow.
"""
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent/'resourcepacks/Citizons_Railway'
MODEL_DIR=ROOT/'assets/citizons_railway/models/rail'
TEXTURE_DIR=ROOT/'assets/citizons_railway/textures/rail'
CELL,GUTTER=256,8
ATLAS_W,ATLAS_H=800,536
GAUGE,HEAD_WIDTH,CENTER=1.435,.068,.7515
# Both guard families stay between the running rails. The outer family sits
# beside the running rail like the turnout check rail; the central family is
# pulled toward the track centre.
OUTER_GUARD_CENTER=CENTER-HEAD_WIDTH-.055  # FrogGeometry.guard / PointSettings.DEFAULT
CENTER_GUARD_CENTER=.3900-HEAD_WIDTH/2
TOP,BASE,SEAT=.264280,.099422,.085422
BALLAST_SHOULDER=1.32
BALLAST_TOE=1.85
# Maximum local thickness is 350 mm; keep the existing rail and shoulder datum.
BALLAST_BOTTOM=.046-.35
REGIONS={'rail':(0,0),'head':(1,0),'end':(2,0),'concrete':(0,1),'fastener':(1,1),'ballast':(2,1)}
REGIONS.update(pad=(1,1),rubber=(1,1))
REGION_BOUNDS={'fastener':(0,0,.75,1),'pad':(.84,.62,.98,.98),'rubber':(.84,.02,.98,.38)}

def surface(seed,base,grain,cloud):
    rng=np.random.default_rng(seed)
    coarse=Image.fromarray(rng.integers(70,185,(16,16),dtype=np.uint8))
    coarse=np.asarray(coarse.resize((CELL,CELL),Image.Resampling.BICUBIC),dtype=float)
    values=np.asarray(base)[None,None,:]+(coarse[:,:,None]-128)*cloud+rng.normal(0,grain,(CELL,CELL,1))
    return Image.fromarray(np.clip(values,0,255).astype(np.uint8))

def make_ballast():
    rng=np.random.default_rng(1435); img=surface(14,(65,72,77),5,.10); draw=ImageDraw.Draw(img)
    for _ in range(480):
        cx,cy=rng.uniform(0,CELL,2); radius=rng.uniform(5,12); n=int(rng.integers(5,8))
        angles=np.arange(n)*math.tau/n+rng.uniform(-.12,.12,n); radii=radius*rng.uniform(.65,1.15,n)
        points=list(zip(cx+np.cos(angles)*radii,cy+np.sin(angles)*radii))
        color=np.array((116,128,135))+int(rng.integers(-21,41))
        for ox in (-CELL,0,CELL):
            for oy in (-CELL,0,CELL):
                pts=[(x+ox,y+oy) for x,y in points]
                draw.polygon([(x+1,y+2) for x,y in pts],fill=(49,56,62)); draw.polygon(pts,fill=tuple(color))
                draw.polygon([pts[0],pts[1],pts[2],(cx+ox,cy+oy)],fill=tuple(np.minimum(255,color+17)))
                draw.polygon([pts[-2],pts[-1],pts[0],(cx+ox,cy+oy)],fill=tuple(np.maximum(0,color-14)))
    return img

def build_atlas():
    # Generated textures are outputs, never inputs; rebuilding cannot bleach them.
    textures={'rail':surface(1,(102,89,76),3.2,.10),'head':surface(2,(178,186,190),1.6,.08),
              'end':surface(3,(124,121,113),4,.20),'concrete':surface(4,(172,182,183),4,.09),
              'fastener':surface(5,(54,58,55),2,.12),'ballast':make_ballast()}
    textures['fastener'].paste(surface(6,(155,145,86),1.5,.08).crop((0,0,52,110)),(204,0))
    textures['fastener'].paste(surface(7,(31,35,33),1,.06).crop((0,0,52,110)),(204,146))
    rng=np.random.default_rng(68); d=ImageDraw.Draw(textures['head'])
    for y in range(CELL):
        if rng.random()<.24:
            tone=int(rng.integers(159,204)); d.line((0,y,CELL,y),fill=(tone,tone+7,tone+10))
    d=ImageDraw.Draw(textures['concrete'])
    for _ in range(600):
        x,y=rng.integers(0,CELL,2); tone=int(rng.integers(127,165)); d.point((int(x),int(y)),fill=(tone,tone+5,tone+5))
    filenames={'rail':'steel_side.png','head':'steel.png','end':'steel_end.png','concrete':'concrete.png','fastener':'fastener.png','ballast':'ballast.png'}
    atlas=Image.new('RGB',(ATLAS_W,ATLAS_H),(58,60,61))
    for region,tile in textures.items():
        col,row=REGIONS[region]; x,y=GUTTER+col*(CELL+GUTTER),GUTTER+row*(CELL+GUTTER)
        padded=Image.fromarray(np.pad(np.asarray(tile),((GUTTER,GUTTER),(GUTTER,GUTTER),(0,0)),mode='edge'))
        atlas.paste(padded,(x-GUTTER,y-GUTTER))
        for folder in (MODEL_DIR,TEXTURE_DIR): tile.save(folder/filenames[region])
    atlas.save(MODEL_DIR/'rail_atlas.png')

def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def unit(v):
    length=math.sqrt(sum(x*x for x in v))
    if length<1e-12: raise ValueError('Degenerate normal')
    return tuple(x/length for x in v)

def triangles(points):
    """Ear clip concave caps; do not fill the I-section's notches with a fan."""
    normal=cross(sub(points[1],points[0]),sub(points[2],points[0])); axis=max(range(3),key=lambda i:abs(normal[i]))
    p=[tuple(v[i] for i in range(3) if i!=axis) for v in points]
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])); sign=1 if area>0 else -1
    def turn(a,b,c): return sign*((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
    indices=list(range(len(points))); result=[]
    while len(indices)>3:
        for k,b in enumerate(indices):
            a,c=indices[k-1],indices[(k+1)%len(indices)]
            if turn(p[a],p[b],p[c])<=1e-12: continue
            if any(all(turn(p[i],p[j],p[q])>=-1e-12 for i,j in ((a,b),(b,c),(c,a))) for q in indices if q not in (a,b,c)): continue
            result.append((a,b,c)); indices.pop(k); break
        else: raise ValueError('Non-simple polygon')
    return result+[tuple(indices)]

class Obj:
    def __init__(self,name): self.name,self.group,self.faces,self.smooth=name,name,[],set()
    @staticmethod
    def uv(region,s,t):
        col,row=REGIONS[region]
        if region in REGION_BOUNDS:
            x0,y0,x1,y1=REGION_BOUNDS[region];s=x0+s*(x1-x0);t=y0+t*(y1-y0)
        x=GUTTER+col*(CELL+GUTTER)+.5+s*(CELL-1); y=GUTTER+row*(CELL+GUTTER)+.5+(1-t)*(CELL-1)
        return x/ATLAS_W,1-y/ATLAS_H
    def face(self,points,region,uv,outward):
        points,uv=list(points),list(uv)
        if len(points)!=len(uv): raise ValueError('UV count')
        normal=cross(sub(points[1],points[0]),sub(points[2],points[0]))
        if sum(a*b for a,b in zip(normal,outward))<0: points.reverse(); uv.reverse()
        normal=unit(cross(sub(points[1],points[0]),sub(points[2],points[0])))
        planar=all(abs(sum(a*b for a,b in zip(sub(p,points[0]),normal)))<1e-8 for p in points)
        pieces=[tuple(range(len(points)))] if len(points)<=4 and planar else triangles(points)
        for piece in pieces:
            ps=[points[i] for i in piece]; ts=[self.uv(region,*uv[i]) for i in piece]
            n=unit(cross(sub(ps[1],ps[0]),sub(ps[2],ps[0])))
            self.faces.append((self.group,region,ps,ts,n))
    def save(self,path):
        lines=['# metres; Y up; CCW outward; repeat 0.6 m',f'mtllib {path.stem}.mtl']
        for _,_,ps,_,_ in self.faces: lines += ['v %.6f %.6f %.6f'%p for p in ps]
        for _,_,_,ts,_ in self.faces: lines += ['vt %.8f %.8f'%uv for uv in ts]
        accumulated={}
        for i,(_,_,ps,_,n) in enumerate(self.faces):
            if i in self.smooth:
                for p in ps:
                    key=tuple(round(v,6) for v in p);accumulated[key]=tuple(a+b for a,b in zip(accumulated.get(key,(0,0,0)),n))
        for i,(_,_,ps,_,n) in enumerate(self.faces):
            for p in ps:
                normal=unit(accumulated[tuple(round(v,6) for v in p)]) if i in self.smooth else n
                lines.append('vn %.8f %.8f %.8f'%normal)
        offset=1; group=None
        for index,(g,_,ps,_,_) in enumerate(self.faces,1):
            if g!=group: lines += ['g '+g,'usemtl mat']; group=g
            lines.append('f '+' '.join(f'{k}/{k}/{k}' for k in range(offset,offset+len(ps)))); offset+=len(ps)
        path.write_text('\n'.join(lines)+'\n',encoding='ascii')
        path.with_suffix('.mtl').write_text('newmtl mat\nKa 1 1 1\nKd 1 1 1\nKs 0.12 0.12 0.12\nNs 32\nd 1\nillum 2\nmap_Kd rail_atlas.png\n',encoding='ascii')

def add_rail(obj,cx,profile,group_prefix='rail',caps=True,polished_head=True):
    side='right' if cx>0 else 'left'
    obj.group=f'{group_prefix}_{side}'
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(profile,profile[1:]+profile[:1]))<0: profile=list(reversed(profile))
    for a,b in zip(profile,profile[1:]+profile[:1]):
        ps=[(cx+a[0],a[1],-.3),(cx+b[0],b[1],-.3),(cx+b[0],b[1],.3),(cx+a[0],a[1],.3)]
        polished=polished_head and min(a[1],b[1])>=TOP-.008
        if polished: v0,v1=(a[0]+.034)/.068,(b[0]+.034)/.068
        else:
            v0,v1=(a[1]-BASE)/(TOP-BASE),(b[1]-BASE)/(TOP-BASE)
            if abs(v1-v0)<1e-8: v0,v1=0,.14
        obj.face(ps,'head' if polished else 'rail',[(0,v0),(0,v1),(1,v1),(1,v0)],(b[1]-a[1],a[0]-b[0],0))
    if caps:
        obj.group+= '_end'
        for z in (-.3,.3): obj.face([(cx+x,y,z) for x,y in profile],'end',[((x+.07)/.14,(y-BASE)/(TOP-BASE)) for x,y in profile],(0,0,z))

HIGH_PROFILE=[(-.070,BASE),(-.070,.108),(-.064,.113),(-.026,.124),(-.012,.134),(-.009,.145),(-.009,.207),
              (-.013,.219),(-.027,.225),(-.033,.231),(-.034,.239),(-.034,.254),(-.032,.260),(-.026,TOP),
              (.026,TOP),(.032,.260),(.034,.254),(.034,.239),(.033,.231),(.027,.225),(.013,.219),
              (.009,.207),(.009,.145),(.012,.134),(.026,.124),(.064,.113),(.070,.108),(.070,BASE)]
MID_PROFILE=[HIGH_PROFILE[i] for i in (0,1,3,5,6,8,10,11,13,14,16,17,19,21,22,24,26,27)]
LOW_PROFILE=[(-.070,BASE),(-.070,.111),(-.009,.135),(-.009,.219),(-.034,.232),(-.034,.254),(-.026,TOP),
             (.026,TOP),(.034,.254),(.034,.232),(.009,.219),(.009,.135),(.070,.111),(.070,BASE)]
# Point Advanced uses the same steel section for a turnout check rail. Keep the
# full I-section here too; only the lateral offset and the support hardware differ.
GUARD_PROFILE=HIGH_PROFILE

def sleeper_top(x):
    a=abs(x)
    if a<.53: return SEAT-.035111+.035111*(.5-.5*math.cos(math.pi*a/.53))
    if a<=.93: return SEAT
    return SEAT-(a-.93)/.32*.012

def add_sleeper(obj,z=0,detail=2,flat=False):
    obj.group='sleeper'; bottom=SEAT-.12
    xs=[-1.25,-1.22,-1.2,-.93,-.7515,-.6,-.53,-.40,-.27,-.13,0,.13,.27,.40,.53,.6,.7515,.93,1.2,1.22,1.25]
    if detail==0: xs=[-1.25,-1.2,-.93,-.6,-.53,0,.53,.6,.93,1.2,1.25]
    rings=[]
    for x in xs:
        h=SEAT if flat else sleeper_top(x); w=.12 if abs(x)<1.22 else .105
        rings.append([(x,bottom,z-w),(x,bottom,z+w),(x,h-.008,z+w-.009),(x,h,z+w-.019),(x,h,z-w+.019),(x,h-.008,z-w+.009)])
    for k in range(len(rings)-1):
        tile=math.floor((xs[k]+xs[k+1])/.6/2)
        for j in range(6):
            n=(j+1)%6; ps=[rings[k][j],rings[k+1][j],rings[k+1][n],rings[k][n]]
            if j in (0,2,3,4): outward=(0,-1 if j==0 else 1,0); uv=[(p[0]/.6-tile,(p[2]-z+.3)/.6) for p in ps]
            else: outward=(0,0,1 if j==1 else -1); uv=[(p[0]/.6-tile,(p[1]-bottom)/.6) for p in ps]
            obj.face(ps,'concrete',uv,outward)
    for k in (0,len(rings)-1): obj.face(rings[k],'concrete',[((p[2]-z+.12)/.24,(p[1]-bottom)/.12) for p in rings[k]],(-1 if k==0 else 1,0,0))

def prism(obj,cx,cz,hx,hz,y0,y1,region='fastener',sides=8):
    rings=[[(cx+hx*math.cos(math.tau*k/sides),y,cz+hz*math.sin(math.tau*k/sides)) for k in range(sides)] for y in (y0,y1)]
    for k in (0,1): obj.face(rings[k],region,[((p[0]-cx+hx)/(2*hx),(p[2]-cz+hz)/(2*hz)) for p in rings[k]],(0,k*2-1,0))
    for i in range(sides):
        j=(i+1)%sides; ps=[rings[0][i],rings[0][j],rings[1][j],rings[1][i]]
        obj.face(ps,region,[(i/sides,0),((i+1)/sides,0),((i+1)/sides,1),(i/sides,1)],(sum(p[0]-cx for p in ps),0,sum(p[2]-cz for p in ps)))

def add_clip(obj,cx,cz,side):
    # One continuous W clip: two lobes, a central waist under the washer,
    # and two lowered toes pressing the rail-foot insulator. No closed single ring.
    anchors=[(.068,.132,-.040),(.077,.137,-.066),(.100,.151,-.085),(.134,.157,-.090),
             (.163,.148,-.079),(.178,.126,-.057),(.168,.118,-.035),(.141,.129,-.026),
             (.116,.150,-.017),(.109,.155,0),(.116,.150,.017),(.141,.129,.026),
             (.168,.118,.035),(.178,.126,.057),(.163,.148,.079),(.134,.157,.090),
             (.100,.151,.085),(.077,.137,.066),(.068,.132,.040)]
    path=[]
    for k in range(len(anchors)-1):
        p0,p1,p2,p3=[np.array(anchors[max(0,min(len(anchors)-1,j))]) for j in (k-1,k,k+1,k+2)]
        for t in (0,.5):
            v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            path.append((cx+side*v[0],v[1],cz+v[2]))
    x,y,z=anchors[-1];path.append((cx+side*x,y,cz+z))
    rings=[]; count=10; radius=.0085
    for k,p in enumerate(path):
        tangent=unit(sub(path[min(len(path)-1,k+1)],path[max(0,k-1)])); u=unit(cross(tangent,(0,1,0))); v=cross(tangent,u)
        rings.append([tuple(p[i]+radius*(u[i]*math.cos(j*math.tau/count)+v[i]*math.sin(j*math.tau/count)) for i in range(3)) for j in range(count)])
    smooth_start=len(obj.faces)
    for k in range(len(rings)-1):
        midpoint=tuple((a+b)/2 for a,b in zip(path[k],path[k+1]))
        for j in range(count):
            n=(j+1)%count; ps=[rings[k][j],rings[k][n],rings[k+1][n],rings[k+1][j]]
            outward=tuple(sum(p[i] for p in ps)/4-midpoint[i] for i in range(3))
            obj.face(ps,'fastener',[(j/count,k/(len(path)-1)),((j+1)/count,k/(len(path)-1)),((j+1)/count,(k+1)/(len(path)-1)),(j/count,(k+1)/(len(path)-1))],outward)
    obj.smooth.update(range(smooth_start,len(obj.faces)))
    for k,other in ((0,1),(-1,-2)): obj.face(rings[k],'fastener',[(.5+.5*math.cos(j*math.tau/count),.5+.5*math.sin(j*math.tau/count)) for j in range(count)],sub(path[k],path[other]))

def plate(obj,cx,cz,hx,hz,y0,y1,chamfer=.006,region='fastener'):
    outline=[(-hx+chamfer,-hz),(hx-chamfer,-hz),(hx,-hz+chamfer),(hx,hz-chamfer),(hx-chamfer,hz),(-hx+chamfer,hz),(-hx,hz-chamfer),(-hx,-hz+chamfer)]
    if chamfer==0: outline=[(-hx,-hz),(hx,-hz),(hx,hz),(-hx,hz)]
    rings=[[(cx+x,y,cz+z) for x,z in outline] for y in (y0,y1)]
    for k in (0,1): obj.face(rings[k],region,[((x+hx)/(2*hx),(z+hz)/(2*hz)) for x,z in outline],(0,2*k-1,0))
    for i in range(len(outline)):
        j=(i+1)%len(outline);ps=[rings[0][i],rings[0][j],rings[1][j],rings[1][i]]
        obj.face(ps,region,[(0,0),(1,0),(1,1),(0,1)],(sum(p[0]-cx for p in ps),0,sum(p[2]-cz for p in ps)))

def pressure_plate(obj,cx,cz,side):
    # A full rectangular plate beneath BOTH W-clip loops. Its inner lip overlaps
    # the sloping rail foot; the outer part seats on the side base plate.
    section=[(.042,.1194),(.070,.108),(.082,SEAT+.010),(.188,SEAT+.010),
             (.188,.1095),(.150,.1095),(.076,.1235),(.068,.1235),(.042,.129)]
    rings=[[(cx+side*x,y,cz+z) for x,y in section] for z in (-.105,.105)]
    for k in (0,1):
        obj.face(rings[k],'fastener',[((x-.042)/.146,(y-(SEAT+.010))/(.129-SEAT-.010)) for x,y in section],(0,0,2*k-1))
    for i,(x,y) in enumerate(section):
        j=(i+1)%len(section);nx,ny=section[j]
        ps=[rings[0][i],rings[0][j],rings[1][j],rings[1][i]]
        obj.face(ps,'fastener',[(0,0),(1,0),(1,1),(0,1)],(side*(ny-y),x-nx,0))

def add_fastener(obj,cx,cz=0,detail=2,group_prefix='fastener'):
    obj.group=group_prefix+'_right' if cx>0 else group_prefix+'_left' if cx<0 else group_prefix
    plate(obj,cx,cz,.076,.107,SEAT,BASE-.004,region='rubber')
    plate(obj,cx,cz,.075,.106,BASE-.004,BASE,region='pad')
    for sign in (-1,1):
        # Separate side plate and outer gauge stop, as in the user's reference.
        plate(obj,cx+sign*.132,cz,.063,.103,SEAT,SEAT+.010,.003)
        plate(obj,cx+sign*.191,cz,.008,.107,SEAT+.010,BASE+.027,.002,region='rubber')
        pressure_plate(obj,cx,cz,sign)
        if detail>0:
            bolt=cx+sign*.133
            prism(obj,bolt,cz,.010,.010,SEAT+.010,.192,sides=10)
            prism(obj,bolt,cz,.030,.030,.162,.168,sides=12)
            prism(obj,bolt,cz,.020,.020,.168,.186,sides=6)
            prism(obj,bolt,cz,.018,.018,.186,.189,sides=6)
            if detail>1:
                for y in (.190,.194,.198):prism(obj,bolt,cz,.0108,.0108,y,y+.0015,sides=10)
            if detail>1: add_clip(obj,cx,cz,sign)

def add_guard_fastener(obj,cx,running,cz=0,detail=2,group_prefix='guard_fastener'):
    """Point Advanced style guardPair: shared base, running-rail cheek, ribs and bolt."""
    obj.group=group_prefix+'_right' if cx>0 else group_prefix+'_left'
    direction=1 if cx>running else -1
    a,b=running-direction*.21,cx+direction*.20
    plate(obj,(a+b)/2,cz,abs(b-a)/2,.108,SEAT,BASE,chamfer=0)
    plate(obj,cx+direction*.0185,cz,.0055,.08,BASE+.036,BASE+.10,chamfer=0)
    section=[(.024,0),(.145,0),(.145,.012),(.024,.095)]
    for along in ((-.055,0,.055) if detail==2 else (0,)):
        rings=[[(cx+direction*x,BASE+y,cz+along+z) for x,y in section] for z in (-.009,.009)]
        for k in (0,1):
            obj.face(rings[k],'fastener',[(x/.145,y/.095) for x,y in section],(0,0,2*k-1))
        for i,(x,y) in enumerate(section):
            j=(i+1)%4; nx,ny=section[j]
            obj.face([rings[0][i],rings[0][j],rings[1][j],rings[1][i]],'fastener',[(0,0),(1,0),(1,1),(0,1)],(direction*(ny-y),x-nx,0))
    bolt=cx+direction*.155
    if detail==2: prism(obj,bolt,cz,.025,.025,BASE,BASE+.006,sides=10)
    if detail>0: prism(obj,bolt,cz,.017,.017,BASE+.006,BASE+.027,sides=6)
    if detail==2: prism(obj,bolt,cz,.008,.008,BASE+.027,BASE+.034,sides=8)


def add_outer_clamp(obj,cx,detail):
    """Same plane clipping as TurnoutFittings.outerClamp (footWidth * .28)."""
    source=Obj('clamp'); add_fastener(source,cx,detail=detail)
    sign=1 if cx>0 else -1
    for index,(group,region,points,uv,normal) in enumerate(source.faces):
        polygon=list(zip(points,uv)); clipped=[]
        for (a,ta),(b,tb) in zip(polygon,polygon[1:]+polygon[:1]):
            da,db=sign*(a[0]-cx)-.14*.28,sign*(b[0]-cx)-.14*.28
            if da>=0: clipped.append((a,ta))
            if (da<0<db) or (db<0<da):
                t=da/(da-db)
                clipped.append((tuple(x+(y-x)*t for x,y in zip(a,b)),tuple(x+(y-x)*t for x,y in zip(ta,tb))))
        if len(clipped)<3: continue
        ps,ts=map(list,zip(*clipped))
        pieces=[tuple(range(len(ps)))] if len(ps)<=4 else triangles(ps)
        for piece in pieces:
            if index in source.smooth: obj.smooth.add(len(obj.faces))
            obj.faces.append((group,region,[ps[i] for i in piece],[ts[i] for i in piece],normal))


def add_center_fastener(obj,cx,detail):
    """Independent compact bolted seats; do not bridge the wide central gap."""
    obj.group='center_fastener_right' if cx>0 else 'center_fastener_left'
    plate(obj,cx,0,.132,.105,SEAT,BASE-.004)
    plate(obj,cx,0,.075,.102,BASE-.004,BASE,region='pad')
    for sign in (-1,1):
        plate(obj,cx+sign*.089,0,.039,.075,BASE+.014,BASE+.025,chamfer=.003)
        if detail>0:
            prism(obj,cx+sign*.106,0,.017,.017,BASE+.025,BASE+.045,sides=6)
        if detail>1:
            prism(obj,cx+sign*.106,0,.024,.024,BASE+.019,BASE+.025,sides=10)
            prism(obj,cx+sign*.106,0,.008,.008,BASE+.045,BASE+.052,sides=8)

def ballast_height(x,z):
    a=abs(x); center=.026+.008*(.5+.5*math.cos(math.tau*z/.6))
    if a<=1.20: return center
    if a<=1.32: return center+(a-1.20)/.12*.012
    t=min(1,(a-BALLAST_SHOULDER)/(BALLAST_TOE-BALLAST_SHOULDER))
    return (center+.012)*(1-t)+BALLAST_BOTTOM*t+.044*math.sin(math.pi*t)

def clip_height(points,height,above):
    out=[]
    for a,b in zip(points,points[1:]+points[:1]):
        da,db=(a[1]-height)*(1 if above else -1),(b[1]-height)*(1 if above else -1)
        if da>=-1e-10: out.append(a)
        if (da<0<db) or (db<0<da):
            t=(height-a[1])/(b[1]-a[1]);out.append(tuple(v+(w-v)*t for v,w in zip(a,b)))
    return [p for i,p in enumerate(out) if sum((a-b)**2 for a,b in zip(p,out[i-1]))>1e-16]

def add_ballast(obj,detail=2):
    obj.group='ballast'
    positive={0,.6,1.2,1.8,*[round(BALLAST_SHOULDER+(BALLAST_TOE-BALLAST_SHOULDER)*i/8,6) for i in range(9)]}
    xs=sorted(positive|{-x for x in positive})
    zs=[-.30,-.20,-.10,0,.10,.20,.30] if detail>1 else [-.30,0,.30]; bottom=BALLAST_BOTTOM
    for a,b in zip(xs,xs[1:]):
        tile=math.floor(((a+b)/2)/.6)
        for c,d in zip(zs,zs[1:]):
            ps=[(a,ballast_height(a,c),c),(b,ballast_height(b,c),c),(b,ballast_height(b,d),d),(a,ballast_height(a,d),d)]
            obj.face(ps,'ballast',[(p[0]/.6-tile,(p[2]+.3)/.6) for p in ps],(0,1,0))
        for z in (-.3,.3):
            ps=[(a,bottom,z),(b,bottom,z),(b,ballast_height(b,z),z),(a,ballast_height(a,z),z)]
            ps=[p for i,p in enumerate(ps) if sum((v-w)**2 for v,w in zip(p,ps[i-1]))>1e-15]
            for row in range(math.floor(bottom/.6),1):
                cap=clip_height(clip_height(ps,row*.6,True),(row+1)*.6,False)
                if len(cap)>=3: obj.face(cap,'ballast',[(p[0]/.6-tile,p[1]/.6-row) for p in cap],(0,0,z))
        obj.face([(a,bottom,-.3),(b,bottom,-.3),(b,bottom,.3),(a,bottom,.3)],'ballast',[(0,0),(1,0),(1,1),(0,1)],(0,-1,0))
    # The sloped sides meet the wider bottom directly: no vertical rectangular walls.

def make_guard_endpoint(kind):
    """Separate terminal asset: z=0 exposed tip, z=length straight handoff.

    Never include this in the repeated 0.6 m model. Point places it once at a
    genuinely exposed end, following the same grade/cant frames as the rails.
    """
    obj=Obj(kind+'_guard_endpoint')
    length=.4 if kind=='outer' else 1.8
    center=OUTER_GUARD_CENTER if kind=='outer' else CENTER_GUARD_CENTER
    inset=.10 if kind=='outer' else center-.070
    profile=list(reversed(GUARD_PROFILE))
    for sign in (-1,1):
        obj.group='terminal_left' if sign<0 else 'terminal_right'
        def ring(z):
            c=sign*(center-inset*(1-z/length))
            return [(c+x,y,z) for x,y in profile]
        # Subdivide the long central convergence so curved/pitched terminals can
        # use the client's path frames without a single rigid diagonal beam.
        # Central steel terminates underneath the protective nose; the nose
        # projects ahead instead of leaving two silver rail ends protruding.
        steel_start=0 if kind=='outer' else .55
        steps=math.ceil((length-steel_start)/.1)
        for k in range(steps):
            a,b=ring(steel_start+(length-steel_start)*k/steps),ring(steel_start+(length-steel_start)*(k+1)/steps)
            for i,(x,y) in enumerate(profile):
                j=(i+1)%len(profile); nx,ny=profile[j]
                polished=kind=='outer' and min(y,ny)>=TOP-.008
                v0,v1=((x+.034)/.068,(nx+.034)/.068) if polished else ((y-BASE)/(TOP-BASE),(ny-BASE)/(TOP-BASE))
                if abs(v1-v0)<1e-8: v0,v1=0,.14
                obj.face([a[i],a[j],b[j],b[i]],'head' if polished else 'rail',[(0,v0),(0,v1),(1,v1),(1,v0)],(ny-y,x-nx,-sign*inset/length*(ny-y)))
        obj.face(ring(steel_start),'end',[((x+.07)/.14,(y-BASE)/(TOP-BASE)) for x,y in profile],(0,0,-1))
    if kind=='center':
        # Blunt protective closure bridging the two converging rails, with a
        # sloping top and broad rear shoulder like the supplied photograph.
        obj.group='terminal_nose'
        nose_tip=SEAT+.015
        a=[(-.055,SEAT,0),(.055,SEAT,0),(.045,nose_tip,0),(-.045,nose_tip,0)]
        b=[(-.238,SEAT,.55),(.238,SEAT,.55),(.230,TOP,.55),(-.230,TOP,.55)]
        for i,outward in enumerate(((0,-1,0),(1,0,0),(0,1,0),(-1,0,0))):
            j=(i+1)%4
            obj.face([a[i],a[j],b[j],b[i]],'concrete',[(0,0),(1,0),(1,1),(0,1)],outward)
        for ring_,outward in ((a,(0,0,-1)),(b,(0,0,1))):
            obj.face(ring_,'concrete',[(0,0),(1,0),(1,1),(0,1)],outward)
        for sign in (-1,1):
            bolt_seat=nose_tip+(TOP-nose_tip)*(.44/.55)
            prism(obj,sign*.13,.44,.018,.018,bolt_seat-.006,bolt_seat+.009,sides=6)
    obj.save(MODEL_DIR/f'{obj.name}.obj')
    return obj

def make_rail(name,profile,detail,kind='mainline'):
    obj=Obj(name); add_ballast(obj,detail); add_sleeper(obj,detail=detail,flat=kind=='center')
    for center in (-CENTER,CENTER):
        if kind=='outer': add_outer_clamp(obj,center,detail)
        else: add_fastener(obj,center,detail=detail)
        add_rail(obj,center,profile)
    if kind in ('outer','center'):
        centers=(-OUTER_GUARD_CENTER,OUTER_GUARD_CENTER) if kind=='outer' else (-CENTER_GUARD_CENTER,CENTER_GUARD_CENTER)
        prefix='outer_guard' if kind=='outer' else 'center_guard'
        fitting='outer_fastener' if kind=='outer' else 'center_fastener'
        for center in centers:
            if kind=='outer': add_guard_fastener(obj,center,(-CENTER if center<0 else CENTER),detail=detail,group_prefix=fitting)
            else: add_center_fastener(obj,center,detail)
            add_rail(obj,center,GUARD_PROFILE,prefix,caps=False,polished_head=kind!='center')
    obj.save(MODEL_DIR/f'{name}.obj'); return obj

def main():
    MODEL_DIR.mkdir(parents=True,exist_ok=True); TEXTURE_DIR.mkdir(parents=True,exist_ok=True); build_atlas()
    # Preserve identical steel sections across LOD boundaries so joined rails cannot crack.
    for name,profile,detail,kind in (
            ('rail_high',HIGH_PROFILE,2,'mainline'),('rail_mid',HIGH_PROFILE,1,'mainline'),('rail_low',HIGH_PROFILE,0,'mainline'),
            ('outer_guard_high',HIGH_PROFILE,2,'outer'),('outer_guard_mid',HIGH_PROFILE,1,'outer'),('outer_guard_low',HIGH_PROFILE,0,'outer'),
            ('center_guard_high',HIGH_PROFILE,2,'center'),('center_guard_mid',HIGH_PROFILE,1,'center'),('center_guard_low',HIGH_PROFILE,0,'center')):
        model=make_rail(name,profile,detail,kind); print(name,len(model.faces),'faces')
    sleeper=Obj('sleeper'); add_sleeper(sleeper); sleeper.save(MODEL_DIR/'sleeper.obj')
    fitting=Obj('fastener'); add_fastener(fitting,0); fitting.save(MODEL_DIR/'fastener.obj')
    for kind in ('outer','center'): make_guard_endpoint(kind)
    style=ROOT/'assets/mtrsteamloco/rails/citizons_railway.json'; data=json.loads(style.read_text(encoding='utf-8-sig'))
    data.pop('citizons_guarded_1435',None)
    data['citizons_mainline_1435'].update(name='Citizons 高仿真钢轨1435mm',repeatInterval=.6,flipV=True,yOffset=0.0)
    data['citizons_outer_guard_1435']={'name':'Citizons 高仿真钢轨(外护轨) 1435mm','model':'citizons_railway:models/rail/outer_guard_high.obj','repeatInterval':.6,'yOffset':0.0,'flipV':True}
    data['citizons_center_guard_1435']={'name':'Citizons 高仿真钢轨(中央护轨) 1435mm','model':'citizons_railway:models/rail/center_guard_high.obj','repeatInterval':.6,'yOffset':0.0,'flipV':True}
    style.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    descriptor=ROOT/'assets/citizons_railway/rail_profiles/citizons_mainline_1435.json'
    data=json.loads(descriptor.read_text(encoding='utf-8-sig'))
    data['style']='citizons_mainline_1435'
    for key in ('sleeperModel','fastenerModel','detailLevel','nativeProfile','fallback'): data.pop(key,None)
    data['modelGroups']={'rail':['rail_right'],'sleeper':['sleeper'],'fastener':['fastener_right'],'preserve':['ballast'],'supports':['sleeper','fastener_left','fastener_right']}
    data['alignEndpointSleepers']=True
    descriptor.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for style_id,prefix,fitting in (('citizons_outer_guard_1435','outer_guard','outer_fastener'),('citizons_center_guard_1435','center_guard','center_fastener')):
        variant=json.loads(json.dumps(data)); variant['style']=style_id
        variant['model']=f'citizons_railway:models/rail/{prefix}_high.obj'
        variant['lod']['near']['model']=f'citizons_railway:models/rail/{prefix}_high.obj'
        variant['lod']['mid']['model']=f'citizons_railway:models/rail/{prefix}_mid.obj'
        variant['lod']['far']['model']=f'citizons_railway:models/rail/{prefix}_low.obj'
        variant['lod']['note']='Continuous guard steel and separate terminals share the same section at every LOD.'
        variant['continuousGuard']={
            'groups':[prefix+'_left',prefix+'_right'],
            'supportGroups':[fitting+'_left',fitting+'_right'],
            'supportInset':.10 if prefix=='outer_guard' else CENTER_GUARD_CENTER-.070,
            'supportMode':'shared' if prefix=='outer_guard' else 'independent',
            'noseLength':0 if prefix=='outer_guard' else .55,
            'endpointModel':f'citizons_railway:models/rail/{prefix}_endpoint.obj',
            'endpointLength':.4 if prefix=='outer_guard' else 1.8,
            'turnout':{'model':data['model'],'modelGroups':data['modelGroups'],'lod':data['lod']}}
        variant['modelGroups']['rail']=['rail_right']
        variant['modelGroups']['fastener']=['fastener_right']
        variant['modelGroups']['supports']=['sleeper','fastener_left','fastener_right',fitting+'_left',fitting+'_right']
        (ROOT/f'assets/citizons_railway/rail_profiles/{style_id}.json').write_text(json.dumps(variant,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for path in (ROOT/'assets/citizons_railway/rail_lod.json',ROOT/'assets/citizons_railway/rail_profiles/citizons_mainline_1435.json'):
        data=json.loads(path.read_text(encoding='utf-8-sig')); lod=data.get('lod',data)
        data['style']='citizons_mainline_1435'
        lod['selection']='distance'; lod['note']='Point Advanced client: full details within 4 m, simplified fittings within 12 m, low detail beyond; continuous rail sections.'
        if 'levels' in lod:
            for item,distance in zip(lod['levels'],(4,12,128)):item['maxDistance']=distance
        else:
            for key,distance in (('near',4),('mid',12),('far',128)):lod[key]['maxDistance']=distance
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Resource-only build complete:',MODEL_DIR)

if __name__=='__main__': main()
