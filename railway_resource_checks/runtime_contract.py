"""Audit the resource pack against the contracts Point Advanced and MTR enforce.

This is deliberately independent of the generator's own data: it re-reads the
exported OBJ/MTL/profile/style files and emulates the checks that run on the
client.  It exists because a pack can look complete on disk yet still make the
client discard a LOD level or fall back to a missing texture.

Failures here are build failures: run after generate_citizons_railway.py.
"""
from pathlib import Path
import json

PACK = Path(__file__).resolve().parents[1] / 'resourcepacks' / 'Citizons_Railway'
ASSETS = PACK / 'assets'
PROFILE_DIR = ASSETS / 'citizons_railway' / 'rail_profiles'
STYLE_FILE = ASSETS / 'mtrsteamloco' / 'rails' / 'citizons_railway.json'


def resolve(identifier):
    if ':' not in identifier:
        raise AssertionError(f'Resource path has no namespace: {identifier}')
    namespace, path = identifier.split(':', 1)
    return ASSETS / namespace / path


def render_resolve(identifier):
    """Minecraft's texture manager always prepends textures/."""
    namespace, path = identifier.split(':', 1)
    if path.startswith('textures/'):
        path = path[len('textures/'):]
    return ASSETS / namespace / 'textures' / path


def parse_obj(path):
    vertices = []
    groups = {}
    mtllibs = []
    materials = set()
    group = 'default'
    for line in path.read_text(encoding='utf-8').splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        key = parts[0]
        if key == 'v':
            vertices.append(tuple(float(v) for v in parts[1:4]))
        elif key in ('g', 'o'):
            group = parts[1]
        elif key == 'mtllib':
            mtllibs.append(parts[1])
        elif key == 'usemtl':
            materials.add(parts[1])
        elif key == 'f':
            ids = []
            for token in parts[1:]:
                index = int(token.split('/')[0])
                ids.append(len(vertices) + index if index < 0 else index - 1)
            groups.setdefault(group, []).append(ids)
    return {
        'path': path,
        'vertices': vertices,
        'groups': groups,
        'mtllibs': mtllibs,
        'materials': materials,
    }


def parse_mtl(path):
    materials = {}
    current = None
    for line in path.read_text(encoding='utf-8').splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) < 2:
            continue
        if parts[0] == 'newmtl':
            current = parts[1].strip()
            materials[current] = {}
        elif parts[0] == 'map_Kd':
            if current is None:
                raise AssertionError(f'map_Kd before newmtl in {path}')
            materials[current]['map_Kd'] = parts[1].strip()
    return materials


def face_points(obj, face):
    return [obj['vertices'][i] for i in face]


def select(obj, names, context):
    out = []
    for name in names:
        if name not in obj['groups']:
            raise AssertionError(f'{context}: missing OBJ group {name!r} in {obj["path"].name}')
        if not obj['groups'][name]:
            raise AssertionError(f'{context}: empty OBJ group {name!r} in {obj["path"].name}')
        out.extend(obj['groups'][name])
    return out


def detail(obj, roles, context):
    rails = select(obj, roles['rail'], context)
    bearers = select(obj, roles['sleeper'], context)
    fittings = select(obj, roles['fastener'], context)
    if not rails or not bearers or not fittings:
        raise AssertionError(f'{context}: rail/sleeper/fastener roles must all be non-empty')

    points = [p for face in rails for p in face_points(obj, face)]
    zmin = min(p[2] for p in points)
    zmax = max(p[2] for p in points)
    if zmax - zmin < 0.01:
        raise AssertionError(f'{context}: rail template has no length ({zmax - zmin:.4f} m)')
    for face in rails:
        zs = [p[2] for p in face_points(obj, face)]
        if max(zs) - min(zs) < 0.001:
            raise AssertionError(f'{context}: rail end cap leaked into sweep group {obj["path"].name}')

    top = max(p[1] for p in points)
    head = [p[0] for p in points if p[1] > top - 0.035]
    center = (min(head) + max(head)) / 2
    return {
        'railCenter': center,
        'railTop': top,
        'headWidth': max(head) - min(head),
        'zMin': zmin,
        'zMax': zmax,
    }


def load_model(identifier, cache):
    if identifier in cache:
        return cache[identifier]
    path = resolve(identifier)
    if not path.is_file():
        raise AssertionError(f'Missing OBJ: {identifier} -> {path}')
    obj = parse_obj(path)
    cache[identifier] = obj
    return obj


def mtl_for(obj, context, require_render=True):
    if len(obj['mtllibs']) != 1:
        raise AssertionError(
            f'{context}: {obj["path"].name} must contain exactly one mtllib line, '
            f'found {obj["mtllibs"] or "none"}; MTR would invent texture <material>.png "'
        )
    mtl_path = obj['path'].parent / obj['mtllibs'][0]
    if not mtl_path.is_file():
        raise AssertionError(f'{context}: mtllib {obj["mtllibs"][0]!r} does not exist next to {obj["path"].name}')
    materials = parse_mtl(mtl_path)
    if not materials:
        raise AssertionError(f'{context}: {mtl_path.name} has no materials')
    for name, values in materials.items():
        if 'map_Kd' not in values:
            raise AssertionError(f'{context}: material {name!r} in {mtl_path.name} has no map_Kd')
        texture = values['map_Kd']
        if ':' in texture:
            mod_path = resolve(texture)
            render_path = render_resolve(texture)
        else:
            name = texture if texture.endswith('.png') else texture + '.png'
            namespace_path = obj['path'].relative_to(ASSETS)
            namespace = namespace_path.parts[0]
            relative = Path(*namespace_path.parts[1:])
            mod_path = obj['path'].parent / name
            render_path = ASSETS / namespace / 'textures' / relative.parent / name
        if not mod_path.is_file():
            raise AssertionError(f'{context}: texture {texture!r} missing at {mod_path}')
        if require_render and not render_path.is_file():
            raise AssertionError(f'{context}: texture {texture!r} missing at the render path {render_path}')
    return materials


def selected_groups(roles):
    return {name for names in roles.values() for name in names}


def audit(verbose=True):
    styles = json.loads(STYLE_FILE.read_text(encoding='utf-8-sig'))
    profiles = {}
    for path in PROFILE_DIR.glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        style = data.get('style')
        if not style:
            raise AssertionError(f'{path.name}: missing style field')
        if style in profiles:
            raise AssertionError(f'Duplicate profile style {style}')
        profiles[style] = (path, data)

    style_ids = set(styles)
    profile_ids = set(profiles)
    if style_ids != profile_ids:
        raise AssertionError(
            'Styles and profiles differ; missing profiles: '
            f'{sorted(style_ids - profile_ids)}, orphan profiles: {sorted(profile_ids - style_ids)}'
        )

    cache = {}
    mtl_cache = {}
    summary = {
        'scope': 'Point Advanced profile/LOD/support roles, MTL texture resolution and MTR startup textures',
        'styles': 0,
        'profiles': 0,
        'models': 0,
        'lodParity': True,
        'guardSupportsOffsetOnly': True,
        'mtllibPresent': True,
    }

    for style_id, style in styles.items():
        summary['styles'] += 1
        for key in ('name', 'model', 'textureId', 'repeatInterval', 'flipV'):
            if key not in style:
                raise AssertionError(f'Style {style_id}: missing {key}')
        if style['flipV'] is not True:
            raise AssertionError(f'Style {style_id}: flipV must be true')
        if abs(float(style['repeatInterval']) - 0.6) > 1e-9:
            raise AssertionError(f'Style {style_id}: repeatInterval must be 0.6')
        if not style['model'].startswith('citizons_railway:models/rail/'):
            raise AssertionError(f'Style {style_id}: unexpected model namespace/path {style["model"]!r}')
        texture = style['textureId']
        if not resolve(texture).is_file():
            raise AssertionError(f'Style {style_id}: texture {texture!r} missing for profile existence check')
        if not render_resolve(texture).is_file():
            raise AssertionError(f'Style {style_id}: texture {texture!r} missing for rendering')
        if style_id.endswith('_old') and '/old/' not in style['model']:
            raise AssertionError(f'Style {style_id}: old style must use /old/ models')
        if style_id.endswith('_new') and '/new/' not in style['model']:
            raise AssertionError(f'Style {style_id}: new style must use /new/ models')
        if not style_id.endswith(('_old', '_new')) and style_id in (
            'citizons_mainline_1435', 'citizons_outer_guard_1435', 'citizons_center_guard_1435'
        ) and '/new/' not in style['model']:
            raise AssertionError(f'Style {style_id}: base ballasted tracks must use /new/ models')

        path, profile = profiles[style_id]
        summary['profiles'] += 1
        # ProfileModel.read rejects a descriptor whose model differs from the
        # style actually selected, which silently drops the profile at runtime.
        if profile.get('model') != style['model']:
            raise AssertionError(
                f'{path.name}: model {profile.get("model")!r} differs from style model {style["model"]!r}'
            )
        roles = profile.get('modelGroups')
        if not roles:
            raise AssertionError(f'{path.name}: missing modelGroups')
        for role in ('rail', 'sleeper', 'fastener', 'preserve', 'supports'):
            if role not in roles:
                raise AssertionError(f'{path.name}: missing modelGroups.{role}')

        guard = profile.get('continuousGuard')
        guard_groups = list(guard.get('groups', [])) if guard else []
        guard_supports = list(guard.get('supportGroups', [])) if guard else []
        if guard:
            for key in ('groups', 'supportGroups'):
                if not guard.get(key):
                    raise AssertionError(f'{path.name}: continuousGuard.{key} must be non-empty')
            missing = [name for name in guard_supports if name not in roles['supports']]
            if missing:
                raise AssertionError(
                    f'{path.name}: guard support groups not listed in modelGroups.supports: {missing}; '
                    'they will render once unshifted (fixed) and once offset (ContinuousGuards.supports)'
                )
            overlap = [name for name in guard_supports if name in guard_groups]
            if overlap:
                raise AssertionError(f'{path.name}: supportGroups also guard rails: {overlap}')
            inset = float(guard.get('supportInset', 0))
            if inset <= 0:
                raise AssertionError(f'{path.name}: supportInset must be positive for termination narrowing')
            mode = guard.get('supportMode', 'independent')
            if mode not in ('shared', 'independent'):
                raise AssertionError(f'{path.name}: invalid supportMode {mode!r}')
            endpoint_identifier = guard.get('endpointModel')
            length = float(guard.get('endpointLength', 0))
            if length <= 0:
                raise AssertionError(f'{path.name}: endpointLength must be positive')
            endpoint_obj = load_model(endpoint_identifier, cache)
            endpoint_points = [
                p
                for faces in endpoint_obj['groups'].values()
                for face in faces
                for p in face_points(endpoint_obj, face)
            ]
            if not endpoint_points:
                raise AssertionError(f'{path.name}: endpoint model has no geometry')
            zs = [p[2] for p in endpoint_points]
            if abs(min(zs)) > 0.001 or abs(max(zs) - length) > 0.001:
                raise AssertionError(
                    f'{path.name}: endpoint z range {min(zs):.4f}..{max(zs):.4f} must be 0..{length}'
                )
            summary['models'] += 1

        # RailLod.register: read the high/mid/low models with their own group maps.
        models = [style['model']]
        lod = profile.get('lod', {})
        near = lod.get('near', {}).get('model')
        if near and near != style['model']:
            raise AssertionError(f'{path.name}: lod.near.model {near!r} differs from style model {style["model"]!r}')
        for key in ('mid', 'far'):
            if key not in lod or 'model' not in lod[key]:
                raise AssertionError(f'{path.name}: lod.{key}.model missing')
            if lod[key]['model'] == style['model']:
                raise AssertionError(f'{path.name}: lod.{key}.model must not reuse the high model')
            models.append(lod[key]['model'])

        turn = guard.get('turnout') if guard else None
        details = []
        for index, identifier in enumerate(models):
            context = f'{style_id} lod{index} {identifier}'
            obj = load_model(identifier, cache)
            summary['models'] += 1
            materials = mtl_for(obj, context)
            if index == 0:
                maps = {values['map_Kd'] for values in materials.values()}
                if texture not in maps:
                    raise AssertionError(
                        f'{style_id}: high model MTL points at {sorted(maps)}, '
                        f'but the legacy MTR textureId is {texture!r}; startup and Point Advanced would disagree'
                    )
            if turn:
                turnout_model = turn['model'] if index == 0 else turn['lod'][('mid', 'far')[index - 1]]['model']
                turnout_groups = turn['modelGroups']
                if index > 0 and 'modelGroups' in turn['lod'][('mid', 'far')[index - 1]]:
                    turnout_groups = turn['lod'][('mid', 'far')[index - 1]]['modelGroups']
                turn_obj = load_model(turnout_model, cache)
                mtl_for(turn_obj, f'{context} turnout {turnout_model}')
                details.append(detail(turn_obj, turnout_groups, f'{context} turnout'))
            else:
                details.append(detail(obj, roles, context))

        # Every LOD model must carry the role and support groups that were selected.
        for index, identifier in enumerate(models):
            obj = load_model(identifier, cache)
            context = f'{style_id} lod{index}'
            for role in ('rail', 'sleeper', 'fastener', 'preserve', 'supports'):
                select(obj, roles[role], f'{context} {role}')
            if guard:
                select(obj, guard_groups, f'{context} guard')
                select(obj, guard_supports, f'{context} guard supports')
            # Fixed must not retain offset-only groups (the reported double render).
            fixed_names = set(obj['groups']) - set(roles['supports']) - set(guard_groups)
            leaked = fixed_names & set(guard_supports)
            if leaked:
                raise AssertionError(f'{context}: guard support groups remain in fixed: {sorted(leaked)}')

        base = details[0]
        for index in (1, 2):
            for key in ('railCenter', 'railTop', 'zMin', 'zMax'):
                if abs(details[index][key] - base[key]) > 1e-5:
                    raise AssertionError(
                        f'{style_id}: LOD {index} {key} {details[index][key]:.6f} differs from high {base[key]:.6f}; '
                        'RailLod.register would discard mid/low'
                    )

        # Variant styles must actually reference their own atlas.
        if style_id.endswith('_old') or style_id.endswith('_new'):
            want = '/old/' if style_id.endswith('_old') else '/new/'
            for identifier in models:
                materials = mtl_for(load_model(identifier, cache), f'{style_id} {identifier}')
                for name, values in materials.items():
                    if want not in values['map_Kd']:
                        raise AssertionError(
                            f'{style_id}: {identifier} material {name} points at {values["map_Kd"]}, expected {want}'
                        )

    # Every OBJ in the pack must declare a resolvable mtllib.  The MTR startup
    # renderer treats a bare/garbage line as no mtllib, invents <material>.png
    # (mat.png), and shows purple until Point Advanced's geometry takes over.
    for path in sorted((ASSETS / 'citizons_railway' / 'models').rglob('*.obj')):
        obj = parse_obj(path)
        # Historical, unreferenced models may use relative map_Kd; only require
        # the mod-side file for them, while every referenced model is stricter.
        mtl_for(obj, str(path.relative_to(PACK)), require_render=False)
    for path in sorted((ASSETS / 'citizons_railway' / 'models').rglob('*.mtl')):
        parse_mtl(path)
    for path in sorted((ASSETS / 'citizons_railway' / 'models').rglob('*.png')):
        if not path.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n':
            raise AssertionError(f'Not a PNG: {path}')

    if verbose:
        print(
            'runtime contract: {styles} styles, {profiles} profiles, {models} model references; '
            'mtllib, textures, LOD parity and guard support roles OK'.format(**summary)
        )
    return summary


if __name__ == '__main__':
    audit()
