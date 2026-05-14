#!/usr/bin/env python3
"""Symlink texture files into the locations Gazebo's OBJ/Collada loaders
search, working around the path mismatch in old OpenRobotics car models
where .mtl references like "hatchback.png" or "model://name/materials/
textures/file.png" point at files that actually live in
materials/textures/ rather than next to the mesh.

For each Fuel-cached model under ~/.gz/fuel/.../models/<name>/<ver>/,
walks materials/textures/ (if any) and creates a symlink for each
texture inside meshes/ pointing at the real file. Idempotent.
"""

import os
import sys
from pathlib import Path

CACHE_ROOT = Path(os.path.expanduser('~/.gz/fuel/fuel.gazebosim.org'))
TEXTURE_EXTS = {'.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tif', '.tiff', '.exr'}


def model_versions(cache_root: Path):
    """Yield each /owner/models/<name>/<version>/ directory."""
    for owner_dir in cache_root.iterdir():
        if not owner_dir.is_dir():
            continue
        models_dir = owner_dir / 'models'
        if not models_dir.is_dir():
            continue
        for model_dir in models_dir.iterdir():
            if not model_dir.is_dir():
                continue
            for version_dir in model_dir.iterdir():
                if version_dir.is_dir() and version_dir.name.isdigit():
                    yield version_dir


def link_textures_into(version_dir: Path) -> int:
    """For each texture under materials/textures/, link it into meshes/
    and into the version_dir root. Returns count of symlinks created."""
    src_dir = version_dir / 'materials' / 'textures'
    if not src_dir.is_dir():
        return 0
    targets = [version_dir / 'meshes', version_dir]
    created = 0
    for src in src_dir.iterdir():
        if src.suffix.lower() not in TEXTURE_EXTS:
            continue
        for target_dir in targets:
            if not target_dir.is_dir():
                continue
            link = target_dir / src.name
            if link.exists() or link.is_symlink():
                continue
            try:
                link.symlink_to(os.path.relpath(src, target_dir))
                created += 1
            except OSError as e:
                print(f'  WARN: cannot link {link} -> {src}: {e}', file=sys.stderr)
    return created


def _resolve_model_uri(uri: str) -> Path:
    """model://<owner_or_name>/<path...> -> cache file path.

    OpenRobotics cars use `model://<model_name>/...` (no owner), so we
    search every owner's models/ for that name and pick the highest
    version directory."""
    rel = uri[len('model://'):].lstrip('/')
    parts = rel.split('/', 1)
    if len(parts) != 2:
        return Path('/nonexistent')
    name, sub = parts[0], parts[1]
    for owner_dir in CACHE_ROOT.iterdir():
        if not owner_dir.is_dir():
            continue
        models_dir = owner_dir / 'models' / name
        if not models_dir.is_dir():
            continue
        versions = sorted(
            (v for v in models_dir.iterdir() if v.is_dir() and v.name.isdigit()),
            key=lambda v: int(v.name), reverse=True)
        for v in versions:
            candidate = v / sub
            if candidate.exists():
                return candidate
    return Path('/nonexistent')


def patch_mtls_in(version_dir: Path) -> int:
    """Strip `model://name/path/` prefixes from texture refs in .mtl files
    so the OBJ loader's same-directory search finds them. Also symlinks
    the cross-model target texture into this model's meshes/ when
    needed (for models like Bus that reference SUV's wheel texture).

    Returns the number of .mtl files modified."""
    import re
    mesh_dir = version_dir / 'meshes'
    if not mesh_dir.is_dir():
        return 0
    line_pat = re.compile(r'^(\s*map_\w+\s+)(model://[^\s]+)\s*$', re.MULTILINE)
    modified = 0
    for mtl in mesh_dir.glob('*.mtl'):
        original = mtl.read_text()
        new_text = original
        for m in line_pat.finditer(original):
            prefix, uri = m.group(1), m.group(2)
            basename = uri.rsplit('/', 1)[-1]
            target_link = mesh_dir / basename
            if not (target_link.exists() or target_link.is_symlink()):
                source = _resolve_model_uri(uri)
                if source.exists():
                    try:
                        target_link.symlink_to(os.path.relpath(source, mesh_dir))
                    except OSError as e:
                        print(f'  WARN: cross-model link {target_link}: {e}', file=sys.stderr)
            new_text = new_text.replace(uri, basename)
        if new_text != original:
            mtl.write_text(new_text)
            modified += 1
    return modified


def main():
    if not CACHE_ROOT.is_dir():
        print(f'No Fuel cache at {CACHE_ROOT}', file=sys.stderr)
        sys.exit(1)
    total_links = 0
    total_link_models = 0
    total_mtl_patched = 0
    for vdir in model_versions(CACHE_ROOT):
        n = link_textures_into(vdir)
        m = patch_mtls_in(vdir)
        if n or m:
            extra = []
            if n: extra.append(f'+{n} symlinks')
            if m: extra.append(f'patched {m} mtls')
            print(f'  {vdir.relative_to(CACHE_ROOT)}: {", ".join(extra)}')
        total_links += n
        if n: total_link_models += 1
        total_mtl_patched += m
    print(f'\nDone. {total_links} symlinks across {total_link_models} models; '
          f'{total_mtl_patched} .mtl files patched.')


if __name__ == '__main__':
    main()
