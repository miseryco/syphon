"""Prepare the website stills and loops from Syphon’s approved renders."""
import argparse
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops, ImageOps

site = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--artwork', type=Path, default=site.parent / 'sample-syphon/artwork')
parser.add_argument('--audio-frames', type=Path, help='reuse the light Audio File frames rendered for the app')
args = parser.parse_args()
artwork = args.artwork
public = site / 'public'
(public / 'art').mkdir(exist_ok=True)

image = Image.open(artwork / 'syphon-final/Syphon-Light-1024.png').convert('RGBA')
image = image.crop(image.getchannel('A').getbbox())
image.thumbnail((640, 640), Image.Resampling.LANCZOS)
image.save(public / 'art/syphon-light.webp', quality=94, method=6)
image.resize((64, 64), Image.Resampling.LANCZOS).save(public / 'art/favicon.png')


def export_loop(folder, stem, max_width):
    paths = sorted(folder.glob('frame-*.png'))
    if len(paths) != 48:
        raise ValueError(f'Expected all 48 frames in {folder}, found {len(paths)}')
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
        raise ValueError(f'{stem} needs a changing alpha mask')
    target = public / 'art' / stem
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
        '-movflags', '+faststart', str(target.with_suffix('.mp4')),
    ], input=video, check=True)


light_edition = artwork / 'workflow-light-concepts-2026-11-18'
export_loop(light_edition / 'Frames/Plugin', 'plugin-light', 415)
export_loop(light_edition / 'Frames/MIDI-Device', 'midi-light', 332)
with TemporaryDirectory(prefix='syphon-audio-frames-') as work:
    audio_frames = args.audio_frames
    if audio_frames is None:
        subprocess.run([
            'blender', '--background', '--factory-startup', '--python-exit-code', '1',
            '--python', str(site / 'scripts/audio-file-motion.py'),
            '--python', str(light_edition / 'light_variants.py'),
        ], env={**os.environ, 'ICONS': 'Audio-File', 'ANIM': '1', 'OUT': work,
                'SIZE': '512', 'SAMPLES': '64'}, check=True)
        audio_frames = Path(work) / 'Frames/Audio-File'
    export_loop(audio_frames, 'audio-swirl', 382)
