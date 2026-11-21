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

Run `npm run build` and `npm run preview` to serve the production build. Open the printed Network address at `/syphon/` on a phone using the same Wi-Fi. Support and Privacy have their own pages at `/syphon/support/` and `/syphon/privacy/`.

## Publish

A push to `main` in `miseryco/syphon` triggers GitHub Actions. The Pages workflow decrypts `assets/fonts/fonts.tar.gpg` with the repository secret `FONT_ARCHIVE_PASSPHRASE`, builds with Vite, and uploads `dist/`. The archive contains the Henrietta webfont subset. Git ignores the local WOFF2 file. The organization’s Pages domain supplies the project URL.

Set `VITE_DOWNLOAD_URL` as a repository Actions variable when a direct Mac download is ready. Both download buttons lead to the availability page while it is empty. The default mount point is `/syphon/`. Use `VITE_BASE_PATH` for a different mount point. Local builds read both settings from `.env.local`.

## Refresh the artwork

The checked-in WebP images and silent MP4 loops let the site build independently of the app. To regenerate them, install FFmpeg with libx264 and put the app checkout in the sibling `sample-syphon/` directory, or point the scripts at it with `--artwork` and `--workspace`. The source icons use the approved 48-frame light renders. Each WebP poster also supplies the silhouette for its video. The variations and preset picker screenshots came from the running app. The loop screenshot shows its Output section with a processed Dexed C4 take. The capture originals live in the app checkout’s `build/site-features/` directory.

```sh
uv run --with pillow python scripts/prepare-art.py
uv run --with pillow python scripts/prepare-captures.py
```
