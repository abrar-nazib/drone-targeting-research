#!/usr/bin/env python3
"""Apply a single semantic label to every <visual> in a Fuel-cached
model.sdf. Use this to make a Fuel model spawn-able with segmentation
labels baked in (since Gazebo Harmonic has no runtime API to label an
already-spawned entity).

Usage:
    python3 tools/label_fuel_model.py <model_subpath> <label_id>

Where <model_subpath> is the cache-relative path under ~/.gz/fuel/...,
e.g. 'openrobotics/models/Pickup' (case-insensitive). The script picks
the highest version dir present and patches its model.sdf in place.
"""

import os
import sys
from pathlib import Path

from lxml import etree

CACHE_ROOT = Path(os.path.expanduser('~/.gz/fuel/fuel.gazebosim.org'))
PLUGIN_FNAME = 'gz-sim-label-system'
PLUGIN_NAME = 'gz::sim::systems::Label'


def find_latest_version(model_subpath: str) -> Path:
    """Return the highest-version model dir under CACHE_ROOT/<model_subpath>.
    Case-insensitive owner/model lookup since Fuel lower-cases on cache."""
    parts = [p.lower() for p in model_subpath.strip('/').split('/')]
    cur = CACHE_ROOT
    for part in parts:
        if not cur.is_dir():
            return Path('/nonexistent')
        match = next((c for c in cur.iterdir() if c.name.lower() == part), None)
        if match is None:
            return Path('/nonexistent')
        cur = match
    if not cur.is_dir():
        return Path('/nonexistent')
    versions = sorted((v for v in cur.iterdir() if v.is_dir() and v.name.isdigit()),
                      key=lambda v: int(v.name), reverse=True)
    return versions[0] if versions else Path('/nonexistent')


def patch_model_sdf(model_dir: Path, label: int) -> tuple[int, int]:
    """Insert a Label plugin in every <visual> in the model.sdf that
    doesn't already have one. Returns (added, skipped)."""
    sdf = model_dir / 'model.sdf'
    if not sdf.is_file():
        raise RuntimeError(f'No model.sdf at {sdf}')
    tree = etree.parse(str(sdf))
    added = skipped = 0
    for visual in tree.getroot().iter('visual'):
        if any(p.get('filename') == PLUGIN_FNAME for p in visual.findall('plugin')):
            skipped += 1
            continue
        plugin = etree.Element('plugin', filename=PLUGIN_FNAME, name=PLUGIN_NAME)
        etree.SubElement(plugin, 'label').text = str(label)
        visual.append(plugin)
        added += 1
    tree.write(str(sdf), pretty_print=True, xml_declaration=True, encoding='UTF-8')
    return added, skipped


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    model_subpath = sys.argv[1]
    label = int(sys.argv[2])

    model_dir = find_latest_version(model_subpath)
    if not model_dir.is_dir():
        print(f'No cache dir for {model_subpath} under {CACHE_ROOT}', file=sys.stderr)
        sys.exit(1)
    added, skipped = patch_model_sdf(model_dir, label)
    print(f'{model_subpath} -> label {label}: +{added} visuals, {skipped} already labeled')
    print(f'  patched: {model_dir}/model.sdf')


if __name__ == '__main__':
    main()
