# SPDX-License-Identifier: Apache-2.0
"""Prepare a tagged construction assembly for the Multifamily Anatomy web app.

Run with Blender --background --python export_assembly.py -- [arguments], or
with a Python environment containing the official bpy package.
"""
import argparse
import json
import sys
import struct
from pathlib import Path


def arguments():
    cli = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--save-blend', type=Path)
    parser.add_argument('--bevel', type=float, default=0.004)
    parser.add_argument('--exporter-path', type=Path,
                        help='Optional checkout/addons directory containing io_scene_gltf2')
    return parser.parse_args(cli)


def use_exporter(path):
    import bpy
    if path is None:
        return
    import ast
    source = path / 'io_scene_gltf2' / '__init__.py'
    tree = ast.parse(source.read_text())
    info = next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'bl_info'
                        for target in node.targets))
    required = tuple(info['blender'])
    if bpy.app.version < required:
        raise RuntimeError(f'Exporter requires Blender {required}, running {bpy.app.version}. '
                           'Use a matching Blender build or omit --exporter-path for its bundled exporter.')
    for key in list(sys.modules):
        if key == 'io_scene_gltf2' or key.startswith('io_scene_gltf2.'):
            del sys.modules[key]
    sys.path.insert(0, str(path.resolve()))
    import io_scene_gltf2
    io_scene_gltf2.register()


def validate_objects(objects):
    components = [obj for obj in objects if obj.get('componentId')]
    layers = [obj for obj in objects if obj.get('layerId')]
    if not components or not layers:
        raise ValueError('Input requires tagged componentId and layerId objects.')
    identities = [obj['componentId'] for obj in components]
    if len(identities) != len(set(identities)):
        raise ValueError('componentId values must be unique.')
    assembly_ids = {obj.get('id') for obj in components}
    if len(assembly_ids) != 1 or None in assembly_ids:
        raise ValueError('Every component must identify the same assembly.')
    for obj in components:
        if not obj.get('part'):
            raise ValueError(f'{obj.name} has no part identity.')
        current = obj
        while current and not current.get('layerId'):
            current = current.parent
        if current is None:
            raise ValueError(f'{obj.name} is detached from its semantic layer.')
    return next(iter(assembly_ids)), components, layers


def restore_source_pose(source, objects):
    # The seed's animation channels may evaluate to a hidden placement frame on
    # import. Restore its explicit glTF node transforms before geometry editing.
    from mathutils import Matrix, Quaternion, Vector
    raw = source.read_bytes()
    size, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4E4F534A:
        raise ValueError('Expected a GLB JSON chunk.')
    document = json.loads(raw[20:20 + size])
    conversion = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    by_name = {obj.name: obj for obj in objects}
    for obj in objects:
        obj.animation_data_clear()
    for node in document['nodes']:
        obj = by_name.get(node.get('name'))
        if obj is None:
            continue
        if 'matrix' in node:
            matrix = Matrix([node['matrix'][index:index + 4] for index in range(0, 16, 4)]).transposed()
        else:
            position = Vector(node.get('translation', [0, 0, 0]))
            x, y, z, w = node.get('rotation', [0, 0, 0, 1])
            scale = Vector(node.get('scale', [1, 1, 1]))
            matrix = Matrix.LocRotScale(position, Quaternion((w, x, y, z)), scale)
        obj.matrix_local = conversion @ matrix @ conversion.inverted()


def main():
    args = arguments()
    import bpy
    use_exporter(args.exporter_path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.source.resolve()))
    assembly_id, components, layers = validate_objects(bpy.context.scene.objects)
    restore_source_pose(args.source, bpy.context.scene.objects)
    bpy.context.view_layer.update()
    adjusted = 0
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or args.bevel <= 0:
            continue
        # Small service lines retain their exact teaching shape. Larger hard
        # edges receive a shallow bevel for readable highlights in the viewer.
        if min(obj.dimensions) < 0.06:
            continue
        modifier = obj.modifiers.new(name='Teaching edge highlight', type='BEVEL')
        modifier.width = args.bevel
        modifier.segments = 2
        modifier.limit_method = 'ANGLE'
        adjusted += 1
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 90
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.save_blend:
        args.save_blend.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.save_blend.resolve()), compress=True)
    bpy.ops.export_scene.gltf(
        filepath=str(args.output.resolve()), export_format='GLB',
        export_extras=True, export_animations=False, export_apply=True,
        export_yup=True, export_frame_range=False)
    import io_scene_gltf2
    result = {'assembly': assembly_id, 'components': len(components),
              'layers': len(layers), 'beveledMeshes': adjusted,
              'blender': bpy.app.version_string,
              'exporter': list(io_scene_gltf2.bl_info['version']),
              'exporterPath': str(Path(io_scene_gltf2.__file__).resolve()),
              'output': str(args.output.resolve())}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
