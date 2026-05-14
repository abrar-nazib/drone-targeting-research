#!/usr/bin/env python3
"""Prefetch Fuel models referenced in a world SDF so the first sim launch
doesn't stall on downloads. Walks <include><uri>...</uri></include> blocks
and runs `gz fuel download -u <uri>` for each unique URI.

Run with the ROS environment sourced (so `gz` is on PATH).

Usage:
    python3 tools/prefetch_fuel.py path/to/world.sdf [path/to/another.sdf ...]
"""

import os
import subprocess
import sys
from pathlib import Path

from lxml import etree

CACHE_ROOT = Path(os.path.expanduser('~/.gz/fuel/fuel.gazebosim.org'))


def fuel_uris_in(sdf_path: Path):
    tree = etree.parse(str(sdf_path))
    seen = set()
    for include in tree.getroot().iter('include'):
        uri_el = include.find('uri')
        if uri_el is None or not uri_el.text:
            continue
        uri = uri_el.text.strip()
        if uri.startswith('https://fuel.gazebosim.org/') and uri not in seen:
            seen.add(uri)
            yield uri


def cache_dir_for(uri: str) -> Path:
    """Map https://fuel.gazebosim.org/1.0/<owner>/models/<name> to its cache dir.

    Cached as ~/.gz/fuel/fuel.gazebosim.org/<owner-lowercased>/models/<name>/<version>/.
    Returns the model parent dir; presence of any version subdir means the
    download landed."""
    suffix = uri.replace('https://fuel.gazebosim.org/', '').strip('/')
    parts = suffix.split('/')
    if len(parts) < 4 or parts[0] != '1.0' or parts[2] != 'models':
        return Path('/nonexistent')
    owner, name = parts[1].lower(), parts[3].lower()
    return CACHE_ROOT / owner / 'models' / name


def main():
    if len(sys.argv) < 2:
        print('Usage: prefetch_fuel.py <world.sdf> [...]', file=sys.stderr)
        sys.exit(2)

    all_uris = set()
    for arg in sys.argv[1:]:
        all_uris.update(fuel_uris_in(Path(arg)))

    if not all_uris:
        print('No Fuel <include> URIs found.')
        return

    print(f'Prefetching {len(all_uris)} Fuel models...')
    failed = []
    for uri in sorted(all_uris):
        print(f'  {uri}')
        result = subprocess.run(
            ['gz', 'fuel', 'download', '-u', uri, '-v', '1'],
            capture_output=True, text=True)

        cache_dir = cache_dir_for(uri)
        ok = cache_dir.exists() and any(cache_dir.iterdir())
        if not ok:
            failed.append(uri)
            tail = (result.stderr or result.stdout).strip().splitlines()[-3:]
            print(f'    FAILED (no cache dir at {cache_dir})')
            for ln in tail:
                print(f'      {ln}')

    if failed:
        print(f'\n{len(failed)} URI(s) failed:')
        for uri in failed:
            print(f'  {uri}')
        sys.exit(1)
    print('\nDone.')


if __name__ == '__main__':
    main()
