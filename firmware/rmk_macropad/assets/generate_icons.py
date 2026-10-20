#!/usr/bin/env python3
"""Derive 32px monochrome display icons from installed official app artwork.

Requires Pillow; no network downloads. See README.md for source provenance.
"""
import argparse
from pathlib import Path
from PIL import Image

SIZE = 32
HERE = Path(__file__).resolve().parent


def convert(source: Path, brand: str) -> Image.Image:
    image = Image.open(source).convert('RGBA')
    if brand == 'claude':
        mask = image.getchannel('A')
    else:
        # Keep the blue/purple Codex mark; white tile and terminal glyph become
        # background, retaining the terminal symbol as negative space.
        mask = Image.new('L', image.size)
        mask.putdata([255 if a > 128 and b - r > 12 and b - g > 8 and min(r, g) < 205 else 0
                      for r, g, b, a in image.get_flattened_data()])
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError(f'No foreground in {source}')
    mask = mask.crop(bounds)
    mask.thumbnail((30, 30), Image.Resampling.LANCZOS)
    canvas = Image.new('L', (SIZE, SIZE))
    canvas.paste(mask, ((SIZE - mask.width) // 2, (SIZE - mask.height) // 2))
    return canvas.point(lambda value: 255 if value >= 128 else 0).convert('1')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--claude', type=Path, default=Path('/Applications/Claude.app/Contents/Resources/TrayIconTemplate@3x.png'))
    parser.add_argument('--codex', type=Path, default=Path('/Applications/ChatGPT.app/Contents/Resources/icon-codex-light.png'))
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    icons = [(brand, convert(getattr(args, brand), brand)) for brand in ('claude', 'codex')]
    for brand, icon in icons:
        raw = icon.tobytes()
        assert len(raw) == 128
        (HERE / f'{brand}_32.raw').write_bytes(raw)
    if args.preview:
        preview = Image.new('RGB', (SIZE * 2 + 6, SIZE + 4), 'black')
        for i, (_, icon) in enumerate(icons):
            preview.paste(icon.convert('RGB'), (2 + i * (SIZE + 2), 2))
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview.resize((preview.width * 8, preview.height * 8), Image.Resampling.NEAREST).save(args.preview)


if __name__ == '__main__':
    main()
