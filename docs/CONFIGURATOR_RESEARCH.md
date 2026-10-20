# Free macropad configuration options

Research date: October 19, 2026. Scope: the assembled ESP32-S3 SuperMini (4 MB flash, 2 MB PSRAM), six direct-wired buttons, one rotary encoder, four WS2812 LEDs, SH1106 128x64 I2C OLED, and a macOS host.

The owner requires a free solution to configure shortcuts and the display from a computer. Editable button labels, profiles, icons, and a splash image are sufficient; a screen layout/widget editor would be a welcome addition. Live host data is not a baseline requirement.

## Findings

No verified, ready-to-flash package was found that provides a single graphical editor for all of these features on this exact wiring and display. Compatible building blocks exist. Hardware compatibility, a graphical keymap editor, and a graphical display editor are separate requirements.

| Option | Free software / host configuration | Display support | Fit for the existing hardware |
| --- | --- | --- | --- |
| RMK + Vial | Open-source firmware (MIT/Apache-2.0), free Vial GUI. Dynamic keymaps; rotary encoder support. ESP32-S3 USB and BLE are documented. | RMK v0.9 documents SH1106 128x64, a keyboard-status renderer, and custom Rust renderers. A general graphical OLED editor in Vial was not verified. | Best established firmware/configurator foundation found. Needs a board definition and a firmware migration; visual display editing requires additional work. |
| duckyPad Pro + configurator | MIT firmware, open-source configurator for Mac/Windows/Linux. Profiles and duckyScript macros. | Profile/key labels; duckyScript can draw on the OLED. Not a drag-and-drop screen designer. | Same ESP32-S3 memory class, but stock hardware uses 20 keys, two encoders, 128x128 SPI OLED and microSD. Porting to our I2C SH1106 and internal storage is substantial. |
| Keyboard Cowboy | Free open-source macOS graphical automation: shortcuts, app context, scripts and workflows. | No ready protocol for our OLED was found. | Good optional host automation after implementing USB HID. Does not replace a device/display configurator. |
| Hammerspoon | Free open-source macOS automation configured with Lua. | Its serial API can exchange data with a custom firmware protocol. No ready graphical OLED editor. | Useful for future live host data or app switching. Requires scripts and firmware integration. |
| FreeDeck | Open-source device and browser configurator, including text/images. | Built around separate per-key displays. | Stock design uses ATmega32U4 (with other official hardware variants), multiple SSD1306 screens and SD storage. Not a ready fit for one SH1106 on ESP32-S3. |
| Pog / KMK | Open-source graphical keyboard setup on CircuitPython-compatible hardware. | Custom behavior can be written in Python; full OLED GUI editing was not verified. | Does not establish an easier complete solution for this board/display. |

Important correction to the earlier chat: lack of a stock ESP32-S3 QMK port does **not** rule out Vial. RMK implements the Vial protocol independently and documents ESP32-S3 support. This is documented framework support, not a successful RMK flash/test on our particular assembly.

## Primary sources

- [RMK repository and license](https://github.com/rmk-rs/rmk)
- [RMK supported hardware](https://rmk.rs/docs/getting_started/supported_hardwares)
- [RMK Vial support](https://rmk.rs/docs/features/vial_support)
- [RMK v0.9 display support](https://rmk.rs/docs/features/display)
- [RMK display configuration](https://rmk.rs/docs/configuration/display)
- [Vial](https://get.vial.today/)
- [duckyPad Pro](https://github.com/dekuNukem/duckyPad-Pro)
- [duckyPad Pro tinkering guide](https://github.com/dekuNukem/duckyPad-Pro/blob/master/doc/tinkering_guide.md)
- [duckyPad configurator](https://github.com/duckyPad/duckyPad-Configurator)
- [duckyPad Pro display source](https://github.com/dekuNukem/duckyPad-Pro/blob/master/firmware/dpp_fw/main/ssd1306.c)
- [duckyPad Pro SD storage source](https://github.com/dekuNukem/duckyPad-Pro/blob/master/firmware/dpp_fw/main/sd_task.c)
- [Keyboard Cowboy](https://github.com/zenangst/KeyboardCowboy)
- [Hammerspoon serial API](https://www.hammerspoon.org/docs/hs.serial.html)
- [FreeDeck hardware](https://github.com/FreeYourStream/freedeck-hardware)
- [FreeDeck configurator](https://github.com/FreeYourStream/freedeck-configurator)
- [Pog introduction](https://pog.heaper.de/docs/intro/)

## Reddit feedback

These are individual reports, not a statistical comparison. Reviews of other hardware do not prove compatibility with our assembly. Author announcements were not counted as independent reviews.

- **duckyPad Pro:** In a [June 2025 discussion, including a July follow-up](https://www.reddit.com/r/macro_pads/comments/1layn7g/wireless_20_keys_tight_budget/), owners praised the configurator and profile workflow. One owner specifically appreciated readable macro scripting, while mentioning battery/enclosure inconvenience. Another explained that automatic application-based profile switching needs a host executable. These reports concern actual duckyPad hardware, not a generic ESP32 firmware port.
- **Vial:** A [DOIO KB16 port discussion](https://www.reddit.com/r/MechanicalKeyboards/comments/ya82hm/doio_kb16_megalodon_trip_knob_macroapd_has_been/) contains successful user reports alongside board-revision and compilation trouble. An OLED customization question was answered with a firmware-rebuild requirement. This concerns that older QMK-based port; it supports caution about assuming Vial includes a display designer, rather than establishing current RMK limits.
- **Vial versus custom configurators:** In a [July 2026 custom macropad thread](https://www.reddit.com/r/olkb/comments/1vb2br7/built_a_custom_macropad_rp2354a_custom/), commenters valued standard VIA/Vial/ZMK configuration and noted that VIA/Vial already have browser apps. This is useful feedback on the maintenance cost and user preference for established tooling.
- **Keyboard Cowboy:** A [July 18, 2025 firsthand app review](https://www.reddit.com/r/macapps/comments/1m33tsw/) found the workflow manager understandable and kept it. A [February 6, 2025 comment](https://www.reddit.com/r/macapps/comments/1igm82q/) reported shortcuts needing a relaunch or an open window. That is an older individual report, not proof of a current defect.
- **Hammerspoon:** [Users discussing free automation in August 2024](https://www.reddit.com/r/macapps/comments/1ezjpl7/) praised its flexibility. A [September 2025 discussion](https://www.reddit.com/r/macapps/comments/1n89q17/) described an initial learning curve. Lua is a meaningful tradeoff for someone wanting GUI setup.

No substantial independent Reddit review set was found for a ready-made, arbitrary SH1106 display editor on our exact ESP32-S3 layout.

## Recommendation for the stated requirements

If choosing an existing keyboard ecosystem is the priority, evaluate **RMK + Vial** first. It supplies keymap configuration without designing our own keyboard protocol, but display configuration still needs an extension or separate editor. There is no hardware-tested RMK build for this assembly yet.

If a **single free interface for keys, encoder, RGB and visual OLED editing** is the priority, the most direct engineering route appears to be extending the already verified Arduino firmware with a small browser configurator. This is a proposed development option, not an existing downloadable application or a completed feature.

A sensible initial scope:

1. Edit the six shortcuts and encoder actions; save named profiles to the device.
2. Edit short OLED labels, profile names, icons, splash image and display settings.
3. Add a 128x64 preview and simple text/icon blocks with position and size controls, rather than promising a full desktop-style dashboard.
4. Store configuration/assets in the board's flash and provide JSON export/import so everyday changes do not require rebuilding firmware.

The OLED is monochrome and only 128x64 pixels: compact labels and simple icons are realistic. A free-form editor needs bounds checks and content/asset limits. Live Mac volume, current track or active-app data would require an additional host-side integration and are outside the baseline scope.

This research does not change or flash the working test firmware. The earlier commit/push is separate; this report has not been committed or pushed.

## Jan Lunge videos checked

The owner supplied two videos. Their YouTube descriptions and linked project sources were inspected:

- [Adding Via & Vial support to the Macropad — part 2](https://www.youtube.com/watch?v=POi9ttF2dsk&t=170s), May 21, 2021. Tools explicitly listed: VIA, Vial, QMK MSYS, Keyboard Layout Editor, QMK Toolbox. Firmware preparation starts at 2:38; flashing/testing at 3:54. The description clones `vial-kb/vial-qmk` and compiles a `janlunge/w3by2` keymap.
- [Rotary encoder macro pad — part 3](https://www.youtube.com/watch?v=OCwuDV3WIkM), November 6, 2021. The description provides firmware with Vial support and links to the [w3by2-rotary project](https://github.com/JanLunge/keyboards/blob/main/w3by2-rotary/Readme.md). The keymap chapter begins at 3:23.

The roles are distinct: Keyboard Layout Editor designs the keyboard layout/JSON; Vial/VIA configure mappings; QMK MSYS is the Windows build environment; QMK Toolbox flashes compatible boards. None of the supplied descriptions establishes a visual OLED content editor.

The author's linked [firmware rules](https://raw.githubusercontent.com/wlard/vial-qmk/vial/keyboards/janlunge/w3by2/rules.mk) specify `MCU = atmega32u4` and the Caterina bootloader. Its precompiled `.hex` is not an ESP32-S3 image. For our board, Vial via RMK remains the relevant candidate rather than directly flashing that binary.


## Deferred: useful OLED context from Hammerspoon — October 20, 2026

Owner requested remembering this idea for later; do not implement it yet.
RMK + Vial is now running on the board and the interactive OLED update has been
flashed. Earlier statements in this research about the port being unimplemented
record the initial research stage; see firmware/rmk_macropad/README.md for current status.

Desired behavior: Hammerspoon detects the frontmost application and supplies a
compact profile and button labels to the OLED. The same physical key can then
run an app-specific action (for example, button 4 opens Chrome DevTools or selects
Bambu Studio's scale tool). App-specific shortcuts must be checked in each app.

Official hooks: hs.application.watcher activated/deactivated; window changes can
be watched separately. References:
- https://www.hammerspoon.org/docs/hs.application.watcher.html
- https://www.hammerspoon.org/docs/hs.serial.html

The present firmware has no host-to-display message receiver. Investigate either
a dedicated vendor HID channel with a small host helper, or USB CDC/serial if it
can coexist cleanly with RMK USB HID. Hammerspoon's hs.hid is not a general raw-HID
transport. Treat protocol choice as unresolved, not a ready-made integration.

Start with application/profile ID and short action labels sent on app changes.
Add bounded messages, reconnect/state resynchronization and timeout fallback to
the local display. Keep current Vial assignments usable without Hammerspoon.
Back up Vial settings and flash before updating; preserve RMK schema inputs.
Do not claim host-confirmed execution merely because a key was sent.

Other possible display content:
- Device-local: layer, button/encoder activity, session input count, local timer.
- From Mac: active application, profile-specific key/encoder hints, actual volume
  or mute state, keyboard input language, media title/progress, selected system
  metrics, task/build or print progress when the respective data source exists.
- Not automatic: current Vial action labels need reading the dynamic keymap and
  a human-friendly label mapping; existing static labels do not track Vial edits.

Prioritize readable app/profile context and button hints over dense dashboards
on the monochrome 128x64 screen. Show stale/disconnected state for host data.
