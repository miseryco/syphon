# Syphon

The website for Syphon, a Mac app that turns a synth patch into a playable sampled instrument. [misery.co/syphon](https://misery.co/syphon/)

## Run locally

Use Node.js 24 and npm. A fresh checkout needs the licensed VC Henrietta Regular webfont at `assets/fonts/henrietta.woff2`. To make the website subset from the installed font on a Mac, use FontTools with WOFF2 support.

```sh
pyftsubset "$HOME/Library/Fonts/VCHenrietta-Regular.otf" --flavor=woff2 \
  --unicodes=U+0000-00FF,U+2000-206F,U+2190-21FF,U+2212 \
  '--layout-features=*' --output-file=assets/fonts/henrietta.woff2
npm ci
npm run dev
```

Run `npm run build` and `npm run preview` to serve the production build on localhost. Support and Privacy have their own pages at `/syphon/support/` and `/syphon/privacy/`.

## Publish

A push to `main` in `miseryco/syphon` triggers GitHub Actions. The Pages workflow decrypts `assets/fonts/fonts.tar.gpg` with the repository secret `FONT_ARCHIVE_PASSPHRASE`, builds with Vite, and uploads `dist/`. The archive contains the Henrietta webfont subset. Git ignores the local WOFF2 file. The organization’s Pages domain supplies the project URL.

Set `VITE_DOWNLOAD_URL` as a repository Actions variable when a direct Mac download is ready. Both download buttons lead to the availability page while it is empty. The default mount point is `/syphon/`. Use `VITE_BASE_PATH` for a different mount point. Local builds read both settings from `.env.local`.

## Refresh the artwork

The site builds from the checked-in WebP images and silent MP4s. To refresh the icons, put Blender and FFmpeg with libx264 on your path. The script renders the light-edition scenes from the sibling `sample-syphon/` app checkout with the same Blender recipe as the native app. Each glass vessel holds its own amber current. The MIDI cable’s current follows its curved bore. Each WebP poster supplies the silhouette for its video. To reuse native light frames, pass `--frames /path/to/light/Frames`. To refresh individual sources, pass `--icon Plugin`, `--icon MIDI-Device` or `--icon Audio-File`. The option is repeatable.

The variations and preset picker screenshots came from the running app. The loop screenshot shows its Output section with a processed Dexed C4 take. The originals live in the app checkout’s `build/site-features/` directory. Use `--artwork` and `--workspace` to point the respective scripts at other copies of their sources.

```sh
uv run --with pillow python scripts/prepare-art.py
uv run --with pillow python scripts/prepare-captures.py
```
