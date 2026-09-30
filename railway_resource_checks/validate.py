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
assert set(style)=={'citizons_mainline_1435','citizons_outer_guard_1435','citizons_center_guard_1435'}
for settings in style.values(): assert settings['flipV'] is True and settings['repeatInterval']==.6
for path in PACK.rglob('*.json'): json.loads(path.read_text(encoding='utf-8-sig'))
for path in MODEL.glob('*.mtl'):
    for line in path.read_text().splitlines():
        if line.startswith('map_Kd '): assert (path.parent/line.split(' ',1)[1]).is_file()

report={'scope':'Exported resource geometry and deterministic rebuild; runtime validation is reported separately','models':{}}
for name in ('rail_high','rail_mid','rail_low','outer_guard_high','outer_guard_mid','outer_guard_low','center_guard_high','center_guard_mid','center_guard_low','outer_guard_endpoint','center_guard_endpoint','sleeper','fastener'):
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
    if name.endswith('_endpoint'):
        points=np.concatenate([p for _,p,_,_ in faces]); length=.4 if name.startswith('outer') else 1.8
        assert points[:,1].max()<=builder.TOP+1e-8,'Terminal or bolt exceeds running rail top'
        assert abs(points[:,2].min())<1e-8 and abs(points[:,2].max()-length)<1e-8
        for sign,side in ((-1,'left'),(1,'right')):
            ps=np.concatenate([p for p,_ in groups['terminal_'+side]])
            steel_start=0 if name.startswith('outer') else .55
            tip=ps[np.isclose(ps[:,2],steel_start)]; end=ps[np.isclose(ps[:,2],length)]
            tip_center=(tip[:,0].min()+tip[:,0].max())/2
            end_center=(end[:,0].min()+end[:,0].max())/2
            inset=(.10 if name.startswith('outer') else builder.CENTER_GUARD_CENTER-.070)*(1-steel_start/length)
            assert abs(sign*(end_center-tip_center)-inset)<1e-6,'Terminal bends away from centre'
            assert abs(tip[:,1].max()-builder.TOP)<1e-8
        if name.startswith('center'):
            nose=np.concatenate([p for p,_ in groups['terminal_nose']])
            assert abs(nose[np.isclose(nose[:,2],0),1].max()-(builder.SEAT+.015))<1e-8,'Concrete nose does not lower toward exposed tip'
            assert abs(nose[np.isclose(nose[:,2],.55),1].max()-builder.TOP)<1e-8
            for side in ('left','right'):
                for p,uv in groups['terminal_'+side]:
                    if np.ptp(p[:,2])>1e-8:
                        pixels=uv*np.array([800,536])
                        assert np.all(pixels[:,0]<264),'Central terminal retains polished rail-head material'
        report['models'][name]={'faces':len(faces),'length':length,'groups':list(groups)}
    elif name.startswith(('rail_','outer_guard_','center_guard_')):
        allp=np.concatenate([p for _,p,_,_ in faces]); assert abs(allp[:,2].min()+.3)<1e-8 and abs(allp[:,2].max()-.3)<1e-8
        for side in ('left','right'):
            prefix=('outer_guard' if name.startswith('outer_guard_') else 'center_guard' if name.startswith('center_guard_') else 'rail')
            longitudinal=np.concatenate([p for p,_ in groups[prefix+'_'+side]])
            head=longitudinal[longitudinal[:,1]>.23]; xs=head[:,0]
            expected_width=.068
            assert abs(xs.max()-xs.min()-expected_width)<1e-8 and abs(head[:,1].max()-.26428)<1e-8
            center=(-1 if side=='left' else 1)*(.7515 if prefix=='rail' else (builder.OUTER_GUARD_CENTER if prefix=='outer_guard' else builder.CENTER_GUARD_CENTER))
            assert abs((xs.min()+xs.max())/2-center)<1e-8
            if prefix!='rail':
                # No periodic terminal forks. Steel section, UVs, and seam vertices
                # must match the actual running rail translated laterally.
                assert not any('endpoint' in g for g in groups)
                running=groups['rail_'+side]
                assert len(running)==len(groups[prefix+'_'+side])
                offset=center-(-1 if side=='left' else 1)*builder.CENTER
                for (gp,guv),(rp,ruv) in zip(groups[prefix+'_'+side],running):
                    assert np.allclose(gp,rp+np.array([offset,0,0]),atol=1e-7)
                    if prefix=='outer_guard': assert np.array_equal(guv,ruv),'Outer guard material differs from running steel'
                    else:
                        pixels=guv*np.array([800,536])
                        assert np.all(pixels[:,0]<264),'Central guard retains polished rail-head material'
                sign=-1 if side=='left' else 1
                if prefix=='outer_guard':
                    assert abs(builder.CENTER-builder.OUTER_GUARD_CENTER-builder.HEAD_WIDTH-.055)<1e-8
                    clamp=np.concatenate([p for p,_ in groups['fastener_'+side]])
                    assert np.min(sign*(clamp[:,0]-sign*builder.CENTER))>=.14*.28-1e-6,'Duplicate inner running clamp'
                    support=np.concatenate([p for p,_ in groups['outer_fastener_'+side]])
                    assert abs(support[:,1].min()-builder.SEAT)<1e-8
                    assert abs(support[:,1].max()-(builder.BASE+.10))<1e-8,'Floating guard ribs'
            # Running rails retain their concave end caps. Fixed full-length guards
            # intentionally omit per-cell caps so repeated 0.6 m units stay seamless.
            edges=Counter(); volume=0
            shell_groups=groups[prefix+'_'+side]
            if prefix=='rail': shell_groups += groups[prefix+'_'+side+'_end']
            for p,_ in shell_groups:
                for a,b in zip(p,np.roll(p,-1,axis=0)):
                    edges[tuple(sorted((tuple(a),tuple(b))))]+=1
                for i in range(1,len(p)-1): volume+=np.dot(p[0],np.cross(p[i],p[i+1]))/6
            if prefix=='rail':
                assert set(edges.values())=={2},(name,side,'open rail shell')
                assert volume>0,(name,side,'inside-out shell')
                # Rail end caps have equal area to the measured section, not the bounding box.
                caps=groups[prefix+'_'+side+'_end']; cap_area=[]
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
        if name.startswith('center_guard_'): assert abs(center_top-builder.SEAT)<1e-8 and sleeper[:,1].max()-center_top<1e-8
        else: assert abs(center_top-(builder.SEAT-.035111))<1e-8 and sleeper[:,1].max()-center_top>.03
        ballast=np.concatenate([p for p,_ in groups['ballast']]); assert abs(ballast[:,1].min()-builder.BALLAST_BOTTOM)<1e-8
        assert abs(np.abs(ballast[:,0]).max()-builder.BALLAST_TOE)<1e-8
        assert abs(ballast[:,1].max()-ballast[:,1].min()-.35)<1e-8,'Requested 350 mm ballast depth'
        report['models'][name]={'faces':len(faces),'vertices':sum(len(p) for _,p,_,_ in faces),'groups':list(groups)}

# The guarded descriptor must load the same running-rail detail while retaining
# the two longitudinal guard groups as fixed geometry.
for descriptor_name in ('citizons_mainline_1435.json','citizons_outer_guard_1435.json','citizons_center_guard_1435.json'):
    descriptor=json.loads((PACK/'assets/citizons_railway/rail_profiles'/descriptor_name).read_text(encoding='utf8'))
    assert descriptor['style'] in style and descriptor['model']==style[descriptor['style']]['model']
    if descriptor['style']=='citizons_mainline_1435': assert descriptor['modelGroups']['rail']==['rail_right']
    else: assert descriptor['modelGroups']['rail']==['rail_right'] and descriptor['modelGroups']['fastener']==['fastener_right']
    if descriptor['style'] != 'citizons_mainline_1435':
        guard=descriptor['continuousGuard']
        prefix='outer' if 'outer' in descriptor['style'] else 'center'
        if prefix=='center': assert abs(guard['supportInset']-(builder.CENTER_GUARD_CENTER-.070))<1e-8
        assert guard['turnout']['model'].endswith('/rail_high.obj')
        assert guard['turnout']['modelGroups']['fastener']==['fastener_right']
        assert (MODEL/Path(guard['endpointModel'].split(':',1)[1]).name).is_file()
        assert not any(k in descriptor for k in ('turnoutFallbackStyle','guardEndpointFlare','flatSleeper'))
        assert set(descriptor['modelGroups'])=={'rail','sleeper','fastener','preserve','supports'}
        assert all(prefix+'_fastener_'+side in descriptor['modelGroups']['supports'] for side in ('left','right'))
    for level in ('near','mid','far'):
        assert Path(descriptor['lod'][level]['model'].split(':',1)[1]).name in {p.name for p in MODEL.glob('outer_guard_*.obj')} | {p.name for p in MODEL.glob('center_guard_*.obj')} | {p.name for p in MODEL.glob('rail_*.obj')}

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
