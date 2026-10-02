"""Validate and render the Pinterest research corpus. No production policy writes.

Input: own annotations + public source URLs/hashes, reviewed thumbnail directory.
Thumbnails are supplied separately; this script does not crawl Pinterest.
"""
import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'fashion_v2/evidence_data/pinterest_v02'


def load_and_validate(data=DATA):
    archive = {p.stem: json.loads(p.read_text()) for p in data.glob('*.json')}
    m = archive['manifest']
    assert m['production_enabled'] is False
    images = {x['id']: x for x in archive['images']}
    outfits = {x['id']: x for x in archive['outfits']}
    assert len(images) == len(archive['images'])
    assert len(outfits) == len(archive['outfits'])
    assert len({p['id'] for p in archive['pins']}) == len(archive['pins'])
    assert len({i['sha256'] for i in images.values()}) == len(images)
    for o in outfits.values():
        assert o['image_id'] in images
        assert o['realism_score'] is None and o['aesthetic_score'] is None
        assert o['wearer_age'] is None and o['wearer_country'] is None
        assert o['owner_verdict'] is None
        assert o['palette_mapping']['status'] == 'not_mapped'
    for p in archive['patterns']:
        full, partial = p['full_support'], p['partial_support']
        ids = full + partial
        assert ids and len(ids) == len(set(ids))
        assert all(i in outfits for i in ids)
        assert all(outfits[i]['full_outfit_visible'] for i in full), p['id']
        assert all(not outfits[i]['full_outfit_visible'] for i in partial), p['id']
        assert p['observed_unique_looks'] == len({outfits[i]['outfit_cluster_id'] for i in ids})
        assert p['full_outfit_count'] == len(full)
        groups = {outfits[i]['source_group_id'] for i in ids if outfits[i]['source_group_id']}
        assert p['traceable_source_group_count'] == len(groups)
        assert set(p['traceable_source_groups']) == groups
        assert p['unresolved_source_looks'] == sum(outfits[i]['source_group_id'] is None for i in ids)
        assert p['production_enabled'] is False and p['validation']['approved'] is False
    expected = {'pinterest_urls': len(archive['pins']),
                'individual_pins': sum(p['kind'] == 'pin' for p in archive['pins']),
                'idea_pages': sum(p['kind'] == 'idea_page' for p in archive['pins']),
                'reference_images': len(images), 'annotated_outfits': len(outfits),
                'full_outfits': sum(o['full_outfit_visible'] for o in outfits.values()),
                'partial_outfits': sum(not o['full_outfit_visible'] for o in outfits.values()),
                'patterns': len(archive['patterns']),
                'publisher_pages_checked': len({o['original_url'] for o in outfits.values() if o['source_status'] == 'publisher_page_checked'}),
                'rules_approved': sum(p['validation']['approved'] for p in archive['patterns'])}
    assert m['counts'] == expected, (m['counts'], expected)
    # Reviewed image rows and pin discovery IDs must resolve, without URL-host counting.
    pin_urls = {p['url'] for p in archive['pins']}
    assert all(i['source_url'] in pin_urls for i in images.values())
    archive['coverage'] = dict(style_catalog=dict(Counter(o['style_catalog'] for o in outfits.values())),
                               season=dict(Counter(o['season_candidate'] for o in outfits.values())),
                               tpo=dict(Counter(o['tpo_candidate'] for o in outfits.values())))
    return archive


def build(output, thumbnails):
    archive = load_and_validate()
    for i in archive['images']:
        raw = (thumbnails / (i['id'] + '.jpg')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != i['thumbnail_sha256']:
            raise ValueError('Reference thumbnail mismatch: ' + i['id'])
        i['thumbnail'] = 'data:image/jpeg;base64,' + base64.b64encode(raw).decode()
    # Canonical data fingerprint excludes binary previews and derived coverage.
    fingerprint = hashlib.sha256(b''.join(p.read_bytes() for p in sorted(DATA.glob('*.json')))).hexdigest()
    archive['fingerprint'] = fingerprint
    payload = json.dumps(archive, ensure_ascii=False).replace('<', '\\u003c')
    template = (ROOT / 'scripts/pinterest_archive_review.html').read_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.replace('__ARCHIVE_DATA__', payload))
    print(json.dumps({'file':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
                      'corpus_fingerprint':fingerprint, 'counts':archive['manifest']['counts']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--thumbnails', type=Path)
    args = parser.parse_args()
    if args.validate_only:
        print(json.dumps(load_and_validate()['manifest']['counts']))
    else:
        if not args.output or not args.thumbnails:
            parser.error('--output and --thumbnails are required to build the review')
        build(args.output, args.thumbnails)
