"""Blender preview of the actual generated OBJ/atlas, including ground occlusion."""
from pathlib import Path
import math
import sys
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'resourcepacks/Citizons_Railway/assets/citizons_railway/models/rail'
OUT=Path(__file__).resolve().parent/'output'
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def load_obj(path,name):
    vertices=[]; tex=[]; faces=[]; uvfaces=[]; normals=[]; normalfaces=[]
    for line in path.read_text().splitlines():
        t=line.split()
        if not t: continue
        if t[0]=='v':
            x,y,z=map(float,t[1:]); vertices.append((x,-z,y))
        elif t[0]=='vt': tex.append(tuple(map(float,t[1:3])))
        elif t[0]=='vn':
            x,y,z=map(float,t[1:]);normals.append((x,-z,y))
        elif t[0]=='f':
            refs=[list(map(int,q.split('/'))) for q in t[1:]]
            faces.append(tuple(q[0]-1 for q in refs)); uvfaces.append([tex[q[1]-1] for q in refs])
            normalfaces.append([normals[q[2]-1] for q in refs])
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vertices,[],faces); mesh.update()
    layer=mesh.uv_layers.new(name='UVMap')
    for polygon,uvs in zip(mesh.polygons,uvfaces):
        for loop,uv in zip(polygon.loop_indices,uvs): layer.data[loop].uv=uv
    for polygon in mesh.polygons: polygon.use_smooth=True
    mesh.normals_split_custom_set([n for face in normalfaces for n in face])
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj)
    return obj

mat=bpy.data.materials.new('Actual pack atlas'); mat.use_nodes=True
mat.node_tree.nodes.clear()
bsdf=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.inputs['Roughness'].default_value=.70
output=mat.node_tree.nodes.new('ShaderNodeOutputMaterial'); mat.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
tex=mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(str(MODEL/'rail_atlas.png'))
tex.interpolation='Linear'; mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
guard_preview='--guards' in sys.argv
endpoint_preview='--endpoints' in sys.argv
source=load_obj(MODEL/('outer_guard_high.obj' if guard_preview else 'rail_high.obj'),'Rail cell'); source.data.materials.append(mat)
cells=[source]
for i in range(-5,6):
    if i==0: continue
    obj=bpy.data.objects.new(f'Cell {i}',source.data); bpy.context.collection.objects.link(obj); obj.location.y=i*.6; cells.append(obj)

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0)); ground=bpy.context.object
gmat=bpy.data.materials.new('Ground at rail datum'); gmat.use_nodes=True; gmat.node_tree.nodes.clear()
gshader=gmat.node_tree.nodes.new('ShaderNodeBsdfPrincipled'); gshader.inputs['Base Color'].default_value=(.19,.21,.23,1); gshader.inputs['Roughness'].default_value=.9
gout=gmat.node_tree.nodes.new('ShaderNodeOutputMaterial'); gmat.node_tree.links.new(gshader.outputs['BSDF'],gout.inputs['Surface']); ground.data.materials.append(gmat)
bpy.ops.object.light_add(type='AREA',location=(-3,-4,7)); bpy.context.object.data.energy=650; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=7
bpy.ops.object.light_add(type='AREA',location=(4,3,5)); bpy.context.object.data.energy=250; bpy.context.object.data.size=6
bpy.ops.object.camera_add(); camera=bpy.context.object
scene=bpy.context.scene; scene.camera=camera; scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.world.use_nodes=True; scene.world.node_tree.nodes.clear()
background=scene.world.node_tree.nodes.new('ShaderNodeBackground'); background.inputs['Color'].default_value=(.5,.5,.5,1); background.inputs['Strength'].default_value=.35
worldout=scene.world.node_tree.nodes.new('ShaderNodeOutputWorld'); scene.world.node_tree.links.new(background.outputs[0],worldout.inputs[0]); scene.view_settings.view_transform='Standard'
scene.render.resolution_x=1400; scene.render.resolution_y=1000; scene.render.resolution_percentage=100

def render(name,location,target,scale):
    camera.location=location; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO'; camera.data.ortho_scale=scale
    scene.render.filepath=str(OUT/name); bpy.ops.render.render(write_still=True)

if endpoint_preview:
    for obj in cells: obj.hide_render=True
    ground.hide_render=True
    for kind,length,scale in (('outer',.4,1.9),('center',1.8,2.5)):
        endpoint=load_obj(MODEL/f'{kind}_guard_endpoint.obj',kind+' terminal'); endpoint.data.materials.append(mat)
        render(kind+'-guard-terminal.png',(1.7,-2.9,2.0),(0,-length/2,.18),scale)
        render(kind+'-guard-terminal-top.png',(0,-length/2,4),(0,-length/2,.18),scale)
        if kind=='center': render('center-guard-terminal-side.png',(4,-length/2,.18),(0,-length/2,.18),2.15)
        endpoint.hide_render=True
elif guard_preview:
    render('outer-guard-overview.png',(3.6,-4.0,3.5),(0,0,.1),6.8)
    render('outer-guard-support-close.png',(-.3,-1.0,.85),(.61,0,.14),.9)
    center=load_obj(MODEL/'center_guard_high.obj','Central guard cell'); center.data.materials.append(mat)
    for obj in cells: obj.data=center.data
    bpy.data.objects.remove(center,do_unlink=True)
    render('center-guard-overview.png',(3.6,-4.0,3.5),(0,0,.1),6.8)
    render('center-guard-support-close.png',(-.15,-1.2,1.0),(.4,0,.12),1.1)
else:
    render('track-overview.png',(3.6,-4.0,3.5),(0,0,.1),6.8)
    render('sleeper-material-close.png',(1.6,-1.7,1.35),(0,0,.10),2.9)
    for obj in cells:
        if obj!=source: obj.hide_render=True
    ground.hide_render=True
    render('rail-section.png',(1.15,-1.3,.8),(.7515,0,.185),.52)
    render('fastener-top.png',(.7515,-.12,1.1),(.7515,0,.12),.48)
    render('ballast-cross-section.png',(0,-6,.18),(0,0,-.03),4.3)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'railway-preview.blend'))
