"""Prepare the website stills and loops from Syphon’s approved renders."""
import argparse
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageOps

site = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--artwork', type=Path, default=site.parent / 'sample-syphon/artwork')
artwork = parser.parse_args().artwork
public = site / 'public'
(public / 'art').mkdir(exist_ok=True)

image = Image.open(artwork / 'syphon-final/Syphon-Light-1024.png').convert('RGBA')
image = image.crop(image.getchannel('A').getbbox())
image.thumbnail((640, 640), Image.Resampling.LANCZOS)
image.save(public / 'art/syphon-light.webp', quality=94, method=6)
image.resize((64, 64), Image.Resampling.LANCZOS).save(public / 'art/favicon.png')

frames_root = artwork / 'workflow-light-concepts-2026-11-18/Frames'
for name, slug, max_width in [('Plugin', 'plugin', 415), ('MIDI-Device', 'midi', 332), ('Audio-File', 'audio', 382)]:
    paths = sorted((frames_root / name).glob('frame-*.png'))
    if len(paths) != 48:
        raise ValueError(f'Expected all 48 frames in {frames_root / name}, found {len(paths)}')
    frames = [Image.open(p).convert('RGBA') for p in paths]
    # Use the same canvas for the poster and every animation frame.
    boxes = [im.getchannel('A').getbbox() for im in frames]
    bounds = (min(b[0] for b in boxes)-2, min(b[1] for b in boxes)-2,
              max(b[2] for b in boxes)+2, max(b[3] for b in boxes)+2)
    frames = [im.crop(bounds) for im in frames]
    for frame in frames:
        frame.thumbnail((max_width, frame.height), Image.Resampling.LANCZOS)
    width, height = frames[0].size
    frames = [ImageOps.expand(frame, (0, 0, width % 2, height % 2)) for frame in frames]
    width, height = frames[0].size
    # The glass and cabling keep the same outline. The poster supplies the alpha
    # mask for every video frame, so a standard H.264 file can carry the moving colour.
    alpha = frames[0].getchannel('A')
    if any(ImageChops.difference(alpha, frame.getchannel('A')).getbbox() for frame in frames[1:]):
        raise ValueError(f'{name} needs a changing alpha mask')
    target = public / 'art' / f'{slug}-light'
    frames[0].save(target.with_suffix('.webp'), quality=94, method=6)
    inside = alpha.point(lambda value: 255 if value else 0)
    video = bytearray()
    for frame in frames:
        colour = Image.new('RGB', frame.size, '#f6f1e6')
        colour.paste(frame.convert('RGB'), mask=inside)
        video.extend(colour.tobytes())
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24',
        '-video_size', f'{width}x{height}', '-framerate', '24', '-i', 'pipe:0',
        '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-threads', '2',
        '-vf', 'scale=out_color_matrix=bt709', '-pix_fmt', 'yuv420p',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'iec61966-2-1',
        '-movflags', '+faststart', str(target) + '.mp4',
    ], input=video, check=True)
