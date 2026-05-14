"""Blender headless script: split a mesh by material into per-material files.

Run as:
    blender --background --python tools/subdivide_dae_by_material.py -- \
            <input> <output_dir>

Input format: .glb (preferred) or .obj. Ubuntu's apt-packaged Blender
4.0.2 was built WITHOUT Collada support, so .dae must be pre-converted
to .glb first using assimp:
    assimp export office_construction.dae /tmp/office.glb glb2

Output: one .glb per distinct material (e.g. GroundClay002_3K.glb,
Bricks01_3K.glb, ...). Output dir gets all the per-material files.
"""

import os
import sys

import bpy


def parse_args():
    argv = sys.argv
    if '--' not in argv:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    rest = argv[argv.index('--') + 1:]
    if len(rest) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    return os.path.abspath(rest[0]), os.path.abspath(rest[1])


def slug(name: str) -> str:
    safe = []
    for c in name:
        if c.isalnum() or c in '_-':
            safe.append(c)
        else:
            safe.append('_')
    return ''.join(safe).strip('_') or 'unnamed'


def import_by_extension(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == '.obj':
        bpy.ops.wm.obj_import(filepath=path)
    else:
        raise RuntimeError(f'Unsupported input format: {ext} (use .glb, .gltf, or .obj)')


def export_by_extension(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.glb':
        bpy.ops.export_scene.gltf(
            filepath=path,
            export_format='GLB',
            use_selection=True,
            export_materials='EXPORT',
            export_image_format='AUTO',
            export_apply=False,
        )
    elif ext == '.obj':
        bpy.ops.wm.obj_export(filepath=path, export_selected_objects=True)
    else:
        raise RuntimeError(f'Unsupported output format: {ext}')


def main():
    input_path, output_dir = parse_args()
    if not os.path.isfile(input_path):
        print(f'Input not found: {input_path}', file=sys.stderr)
        sys.exit(1)
    os.makedirs(output_dir, exist_ok=True)

    # Wipe Blender scene to a clean slate.
    bpy.ops.wm.read_factory_settings(use_empty=True)

    print(f'Importing {input_path} ...')
    import_by_extension(input_path)

    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not mesh_objs:
        print('No mesh objects imported', file=sys.stderr)
        sys.exit(1)
    print(f'Imported {len(mesh_objs)} mesh object(s)')

    # Join into one so "separate by material" sees all materials together.
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    if len(mesh_objs) > 1:
        bpy.ops.object.join()

    main_obj = bpy.context.view_layer.objects.active
    n_mats = sum(1 for m in main_obj.data.materials if m is not None)
    print(f'Joined object has {n_mats} materials')

    # Edit-mode → select all → separate by material → object-mode.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='MATERIAL')
    bpy.ops.object.mode_set(mode='OBJECT')

    parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    print(f'After separate: {len(parts)} parts')

    # Export each part as its own .dae.
    for i, obj in enumerate(parts):
        if obj.data.materials and obj.data.materials[0]:
            mat = obj.data.materials[0].name
        else:
            mat = f'unnamed_{i}'
        out_path = os.path.join(output_dir, f'{slug(mat)}.glb')

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        export_by_extension(out_path)
        print(f'  exported {mat:50s}  verts={len(obj.data.vertices):>6}  ->  {out_path}')

    print('done')


if __name__ == '__main__':
    main()
