# Notification brand icons

These 32×32 monochrome assets identify the notification source on the OLED.
They are derived from official artwork already installed on the user's Mac,
not generated or redrawn logos:

- **Claude:** `/Applications/Claude.app/Contents/Resources/TrayIconTemplate@3x.png`,
  Claude Desktop 2.42304.2. Uses the template's alpha mask (Claude asterisk).
- **Codex:** `/Applications/ChatGPT.app/Contents/Resources/icon-codex-light.png`,
  Codex desktop bundle version 26.1013.40934. Removes the white app tile and
  converts the blue/purple flower to a monochrome silhouette. The terminal
  glyph remains negative space.

The Claude and Codex marks remain the property of their respective owners.
Their use here identifies the originating application and does not imply
endorsement. The project license does not relicense these marks.

## Regenerate

Install Pillow 13 in a temporary Python environment, then run from the project
root (source paths can be overridden with `--claude` and `--codex`):

```sh
python firmware/rmk_macropad/assets/generate_icons.py \
  --preview build/brand-icons-preview.png
```

The script crops foreground bounds, preserves aspect ratio, fits within 30×30,
centers on a 32×32 canvas, and thresholds without dithering. Each `.raw` file is
128 bytes: four bytes per row, most-significant pixel first, white = 1. It can
be rendered with `ImageRaw::<BinaryColor>::new(bytes, 32)`.

The preview is rendered from the same final binary pixels and enlarged with
nearest-neighbor sampling. Changes to installed upstream artwork can affect
regeneration; inspect the preview before using new outputs.

Original source SHA-256 values:

```text
Claude eb3faa1ffaf88cf6692a98e7b608cd481a2d202eab096d9dc9efd89dbac60597
Codex  de7d43f3386105ab20952958c2c25beb0d903e2aeb6e1aef57c49a648c0d1c07
```
