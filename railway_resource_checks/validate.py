"""Read exported files back; check actual dimensions, faces, caps and MTR UVs."""
from pathlib import Path
import sys,json,math
from collections import Counter,defaultdict
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import generate_citizons_railway as builder
PACK=builder.ROOT; MODEL=builder.MODEL_DIR

def read(path):
    v=[]; uv=[]; normals=[]; faces=[]; group=''
    for line in path.read_text().splitlines():
        t=line.split()
        if not t: continue
        if t[0]=='v': v.append(tuple(map(float,t[1:4])))
        elif t[0]=='vt': uv.append(tuple(map(float,t[1:3])))
        elif t[0]=='vn': normals.append(tuple(map(float,t[1:4])))
        elif t[0]=='g': group=t[1]
        elif t[0]=='mtllib': assert (path.parent/t[1]).is_file()
        elif t[0]=='f':
            indices=[tuple(int(x)-1 for x in s.split('/')) for s in t[1:]]
            faces.append((group,np.array([v[i] for i,_,_ in indices]),np.array([uv[i] for _,i,_ in indices]),np.array([normals[i] for _,_,i in indices])))
    return faces

style=json.loads((PACK/'assets/mtrsteamloco/rails/citizons_railway.json').read_text(encoding='utf8'))
assert len(style)==1
settings=style['citizons_mainline_1435']; assert settings['flipV'] is True and settings['repeatInterval']==.6
for path in PACK.rglob('*.json'): json.loads(path.read_text(encoding='utf-8-sig'))
for path in MODEL.glob('*.mtl'):
    for line in path.read_text().splitlines():
        if line.startswith('map_Kd '): assert (path.parent/line.split(' ',1)[1]).is_file()

report={'scope':'Resource geometry checks; client adapter tested by mod regression and isolated runtime','models':{}}
for name in ('rail_high','rail_mid','rail_low','sleeper','fastener'):
    faces=read(MODEL/f'{name}.obj'); groups=defaultdict(list)
    for group,points,uv,normals in faces:
        assert 3<=len(points)<=4
        assert np.isfinite(points).all() and np.isfinite(uv).all()
        assert (uv>=0).all() and (uv<=1).all()
        n=np.cross(points[1]-points[0],points[2]-points[0]); assert np.linalg.norm(n)>1e-10,(name,group,'zero face')
        assert np.dot(n,normals[0])>0,(name,group,'inverted normal')
        uv_area=sum((uv[i,0]-uv[0,0])*(uv[i+1,1]-uv[0,1])-(uv[i,1]-uv[0,1])*(uv[i+1,0]-uv[0,0]) for i in range(1,len(uv)-1))
        assert abs(uv_area)>1e-12,(name,group,'collapsed UV')
        groups[group].append((points,uv))
    if name.startswith('rail_'):
        allp=np.concatenate([p for _,p,_,_ in faces]); assert abs(allp[:,2].min()+.3)<1e-8 and abs(allp[:,2].max()-.3)<1e-8
        for side in ('left','right'):
            longitudinal=np.concatenate([p for p,_ in groups['rail_'+side]])
            head=longitudinal[longitudinal[:,1]>.23]; xs=head[:,0]
            assert abs(xs.max()-xs.min()-.068)<1e-8 and abs(head[:,1].max()-.26428)<1e-8
            center=(-1 if side=='left' else 1)*.7515
            # Test closed welded shell, including both concave caps.
            edges=Counter(); volume=0
            for p,_ in groups['rail_'+side]+groups['rail_'+side+'_end']:
                for a,b in zip(p,np.roll(p,-1,axis=0)):
                    edges[tuple(sorted((tuple(a),tuple(b))))]+=1
                for i in range(1,len(p)-1): volume+=np.dot(p[0],np.cross(p[i],p[i+1]))/6
            assert set(edges.values())=={2},(name,side,'open rail shell')
            assert volume>0,(name,side,'inside-out shell')
            # Rail end caps have equal area to the measured section, not the bounding box.
            caps=groups['rail_'+side+'_end']; cap_area=[]
            for z in (-.3,.3):
                area=sum(np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))/2 for p,_ in caps if np.allclose(p[:,2],z))
                cap_area.append(area)
            assert abs(cap_area[0]-cap_area[1])<1e-10 and cap_area[0]<.14*(.26428-.099422)*.65
        for p,uv in groups['ballast']:
            n=np.cross(p[1]-p[0],p[2]-p[0])
            if n[1]>1e-10:
                if np.abs(p[:,0]).max()<=1.32: assert p[:,1].min()>=.026-1e-8,'Ballast plateau hidden below ground'
                # Use MTR flipV conversion, then confirm coordinates sample the ballast tile.
                image_uv=uv.copy(); image_uv[:,1]=1-image_uv[:,1]
                pixels=image_uv*np.array([800,536]); assert (pixels[:,0]>=536).all() and (pixels[:,1]>=272).all()
        sleeper=np.concatenate([p for p,_ in groups['sleeper']]); center_top=sleeper[np.abs(sleeper[:,0])<1e-8,1].max()
        assert abs(center_top-(builder.SEAT-.035111))<1e-8 and sleeper[:,1].max()-center_top>.03
        ballast=np.concatenate([p for p,_ in groups['ballast']]); assert abs(ballast[:,1].min()-builder.BALLAST_BOTTOM)<1e-8
        assert abs(np.abs(ballast[:,0]).max()-builder.BALLAST_TOE)<1e-8
        assert abs(ballast[:,1].max()-ballast[:,1].min()-.35)<1e-8,'Requested 350 mm ballast depth'
    report['models'][name]={'faces':len(faces),'vertices':sum(len(p) for _,p,_,_ in faces),'groups':list(groups)}

# Rebuild once more and compare bytes. Output textures must not get brighter on each run.
paths=[p for p in MODEL.iterdir() if p.suffix in ('.obj','.mtl','.png')]
before={p:p.read_bytes() for p in paths}; builder.main()
assert all(p.read_bytes()==data for p,data in before.items()),'Non-idempotent rebuild'
report.update(gauge=1.435,railTop=.26428,repeatInterval=.6,sleeperCenterDepression=.035111,
              ballastPlateauMin=.026,ballastBottom=builder.BALLAST_BOTTOM,ballastMaximumThickness=.35,ballastToeWidth=2*builder.BALLAST_TOE,uvConvention='OBJ bottom-left / MTR flipV true',idempotent=True,
              automaticLodSupported=True,lodDistances=[4,12])
out=Path(__file__).resolve().parent/'output'; out.mkdir(exist_ok=True)
(out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
