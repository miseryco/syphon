"""Prepare inline screenshot details and full-size views from the local Syphon captures."""
import argparse
from pathlib import Path

from PIL import Image

site = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace', type=Path, default=site.parent / 'sample-syphon/build/site-features')
workspace = parser.parse_args().workspace
output = site / 'public/capture'
output.mkdir(exist_ok=True)

# Keep type legible in the inline details and preserve the original view for the lightbox.
screens = [
    ('variations', 'variations-window.png', (40, 783, 1268, 1277)),
    ('patches', 'preset-window.png', (760, 1148, 1370, 1598)),
    ('loop', 'loop-controls.png', (40, 565, 1090, 1161)),
]
for name, filename, bounds in screens:
    with Image.open(workspace / filename) as image:
        image.save(output / f'{name}-window.webp', lossless=True, method=6)
        image.crop(bounds).save(output / f'{name}.webp', lossless=True, method=6)
