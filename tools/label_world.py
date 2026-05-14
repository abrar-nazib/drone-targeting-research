#!/usr/bin/env python3
"""Walk a world SDF and inject gz-sim-label-system Label plugins so the
segmentation_camera sensor produces non-background pixels for everything
in the labels.yaml class map.

For <include> blocks the plugin is added as a child of <include> (the
canonical Harmonic pattern). For inline <model> blocks the plugin is
added inside each <visual> element. Both forms are idempotent: if a
Label plugin is already present, it is left alone.

Usage:
    python3 tools/label_world.py --in path/to/world.sdf --out path/to/world_labeled.sdf
    python3 tools/label_world.py --in path/to/world.sdf --in-place
    python3 tools/label_world.py --in path/to/world.sdf --dry-run
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from lxml import etree


LABEL_PLUGIN_FILENAME = 'gz-sim-label-system'
LABEL_PLUGIN_NAME = 'gz::sim::systems::Label'


class LabelMap:
    def __init__(self, schema_path: Path):
        with open(schema_path) as f:
            cfg = yaml.safe_load(f)
        self.default_label: int = int(cfg.get('default_label', 0))
        self.exact: Dict[str, int] = {k: int(v) for k, v in (cfg.get('models') or {}).items()}
        self.patterns: List[Tuple[re.Pattern, int]] = [
            (re.compile(p['regex']), int(p['label']))
            for p in (cfg.get('patterns') or [])
        ]

    def lookup(self, name: str) -> Tuple[Optional[int], str]:
        if name in self.exact:
            return self.exact[name], 'exact'
        for rgx, label in self.patterns:
            if rgx.search(name):
                return label, f'regex({rgx.pattern})'
        return None, 'no-match'


def _has_label_plugin(parent: etree._Element) -> bool:
    for plugin in parent.findall('plugin'):
        if plugin.get('filename') == LABEL_PLUGIN_FILENAME:
            return True
    return False


def _make_label_plugin(label: int) -> etree._Element:
    plugin = etree.Element('plugin', filename=LABEL_PLUGIN_FILENAME, name=LABEL_PLUGIN_NAME)
    label_el = etree.SubElement(plugin, 'label')
    label_el.text = str(label)
    return plugin


def _include_candidate_names(include_el: etree._Element) -> List[str]:
    """Names to try when looking up a label for an <include>.

    Returns both the URI's model name (e.g. "Apartment") and the optional
    <name> override (e.g. "apartment_n1"), in that order. The URI is more
    canonical for matching against labels.yaml (which is keyed by model
    name), but the <name> override sometimes carries the type (e.g. when
    a generic mesh is reused with semantic naming).
    """
    candidates = []
    uri_el = include_el.find('uri')
    if uri_el is not None and uri_el.text:
        candidates.append(uri_el.text.strip().rstrip('/').split('/')[-1])
    name_el = include_el.find('name')
    if name_el is not None and name_el.text:
        candidates.append(name_el.text.strip())
    return candidates


def _strip_label_plugins(parent: etree._Element) -> int:
    """Remove all gz-sim-label-system plugins directly under `parent`. Returns count removed."""
    removed = 0
    for plugin in list(parent.findall('plugin')):
        if plugin.get('filename') == LABEL_PLUGIN_FILENAME:
            parent.remove(plugin)
            removed += 1
    return removed


def annotate(tree: etree._ElementTree, labels: LabelMap, strip_existing: bool = False) -> Dict[str, int]:
    """Insert Label plugins where missing. Returns counters."""
    root = tree.getroot()
    stats = {'include_labeled': 0, 'include_skipped_existing': 0, 'include_no_match': 0,
             'include_stripped': 0,
             'inline_visuals_labeled': 0, 'inline_visuals_skipped_existing': 0,
             'inline_visuals_stripped': 0,
             'inline_models_no_match': 0}

    if strip_existing:
        for include in root.iter('include'):
            stats['include_stripped'] += _strip_label_plugins(include)
        for visual in root.iter('visual'):
            stats['inline_visuals_stripped'] += _strip_label_plugins(visual)

    for include in root.iter('include'):
        names = _include_candidate_names(include)
        if not names:
            continue
        if _has_label_plugin(include):
            stats['include_skipped_existing'] += 1
            continue
        label = None
        matched_on = ''
        for n in names:
            label, _why = labels.lookup(n)
            if label is not None:
                matched_on = n
                break
        if label is None:
            stats['include_no_match'] += 1
            print(f'  [no-match include] tried {names}', file=sys.stderr)
            continue
        include.append(_make_label_plugin(label))
        stats['include_labeled'] += 1
        print(f'  [labeled include]  "{matched_on}" -> {label}')

    for model in root.iter('model'):
        # Skip nested <model>s that come from includes (root.iter walks all);
        # we want only top-level models. A simple proxy: model whose direct
        # parent is <world>.
        parent = model.getparent()
        if parent is None or parent.tag != 'world':
            continue
        name = model.get('name', '')
        if not name:
            continue
        label, _why = labels.lookup(name)
        if label is None:
            stats['inline_models_no_match'] += 1
            print(f'  [no-match model]   "{name}"', file=sys.stderr)
            continue
        for visual in model.iter('visual'):
            if _has_label_plugin(visual):
                stats['inline_visuals_skipped_existing'] += 1
                continue
            visual.append(_make_label_plugin(label))
            stats['inline_visuals_labeled'] += 1
        print(f'  [labeled model]    "{name}" -> {label}')

    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='in_path', required=True, type=Path,
                    help='Input world SDF.')
    ap.add_argument('--out', dest='out_path', type=Path, default=None,
                    help='Output path. Required unless --in-place or --dry-run.')
    ap.add_argument('--in-place', action='store_true',
                    help='Overwrite the input file.')
    ap.add_argument('--dry-run', action='store_true',
                    help='Parse and report; do not write anywhere.')
    ap.add_argument('--strip-existing', action='store_true',
                    help='Remove pre-existing Label plugins before re-applying labels.yaml. '
                         'Use when forking a foreign world whose label IDs may not match our schema.')
    ap.add_argument('--labels', type=Path,
                    default=Path(__file__).parent / 'labels.yaml',
                    help='Path to labels.yaml (default: tools/labels.yaml).')
    args = ap.parse_args()

    if not args.dry_run:
        if args.in_place == bool(args.out_path):
            ap.error('Provide exactly one of --out or --in-place (or use --dry-run).')

    labels = LabelMap(args.labels)
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(args.in_path), parser)

    print(f'Augmenting {args.in_path} using {args.labels} ...')
    stats = annotate(tree, labels, strip_existing=args.strip_existing)

    print('\nSummary:')
    for k, v in stats.items():
        print(f'  {k}: {v}')

    if args.dry_run:
        print('\n(dry-run: no file written)')
        return

    out = args.in_path if args.in_place else args.out_path
    tree.write(str(out), pretty_print=True, xml_declaration=True, encoding='UTF-8')
    print(f'\nWrote {out}')


if __name__ == '__main__':
    main()
