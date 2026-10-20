# Installing Vial and preparing RMK on macOS

Updated: October 19, 2026.

Target: the assembled ESP32-S3 macropad with six buttons, one rotary encoder, an SH1106 128x64 OLED, and four WS2812 LEDs.

## Current status — October 20, 2026

RMK firmware in `rmk_macropad/` has now been built and flashed successfully.
macOS detects **Macropad Vial**, VID `FEED`, PID `6061`, including its Vial HID
interface. Open Vial and select that device. Physical display/LED/encoder behavior
and editing through the GUI still need owner confirmation after flashing.

See [the implemented firmware instructions](rmk_macropad/README.md) for the
validated build command, partition table, pin map, defaults and rollback.
The development walkthrough below records the original preparation plan;
use the checked-in implementation instead of generating a new board project.

## 1. Install Vial on the Mac (can be done now)

1. Open the [official Vial download page](https://get.vial.today/download/).
2. Select **macOS (dmg)**. At the time of writing the official page lists beta v0.7.5.
3. Open the downloaded disk image and copy the Vial application to **Applications**.
4. Launch Vial from Applications. Installation alone does not require changing the board firmware.

Alternatively, the [Vial web application](https://vial.rocks/) can configure compatible firmware from a browser with WebHID support, such as desktop Chrome or Edge. The desktop application is the initial choice for this setup.

Expected result after the RMK flash: Vial lists **Macropad Vial** and displays six keys, encoder rotation controls and its push button. If it does not, reconnect USB and reopen Vial. Hold SW1 and SW6 when Vial asks for a physical unlock.

You do not need QMK MSYS or QMK Toolbox for this ESP32-S3 workflow. Jan Lunge's videos use those tools with a different ATmega32U4-based board; its `.hex` firmware is not an ESP32-S3 image.

## 2. Prepare the firmware development tools (developer step)

These tools are needed by the person building the RMK firmware. The owner only needs Vial after a compatible firmware build is installed.

Install Rust by following the [official Rust installation instructions](https://www.rust-lang.org/tools/install). On macOS, Cargo also needs the Apple command-line developer tools; if absent, install them with:

```sh
xcode-select --install
```

Open a new Terminal window after installing Rust, then check:

```sh
rustup --version
cargo --version
```

ESP32-S3 uses Xtensa. Install Espressif's Rust toolchain rather than an ARM target from a generic keyboard tutorial:

```sh
cargo install espup --locked
espup install --targets esp32s3
. "$HOME/export-esp.sh"
```

The export command applies to each new build terminal. Follow the toolchain version selected by the eventual RMK firmware project if it pins one.

Install the project generator and ESP flasher:

```sh
cargo install rmkit --locked
cargo install espflash --locked
```

These are setup commands from the official tool documentation, not commands executed or validated locally during preparation of this guide. Pin the compatible RMK/toolchain versions and commit the firmware lockfile when the board port is created.

## 3. Create and adapt the RMK firmware (required before connecting Vial)

Use the [RMK project-creation guide](https://rmk.rs/docs/user_guide/create_firmware/local_compilation). The interactive entry point is:

```sh
rmkit init
```

Generate into a new firmware project directory, separate from the working `macropad_test/` sketch. Select ESP32-S3 and a single-board keyboard; begin with wired USB and Vial. Configure direct GPIO inputs, not a diode matrix: our six keys connect individually to GND.

Use the following verified wiring as the source of truth:

| Function | GPIO / setting |
| --- | --- |
| Physical SW1–SW6 | 1, 2, 3, 6, 5, 4 |
| Encoder A / B / push | 8 / 9 / 10 |
| OLED SDA / SCL | 11 / 12 |
| OLED | SH1106, 128x64, I2C address 0x3C |
| External WS2812 data | 13 |
| External WS2812 count | 4 |
| Flash | 4 MB |
| On-chip PSRAM detected previously | 2 MB; do not select an unrelated PSRAM interface/profile |
| Native USB data pins | GPIO19/20, reserved for USB |

Match the actual physical arrangement of the buttons in the Vial layout. Configure all six buttons plus the encoder push, and include both rotation directions as encoder actions. The verified desired direction is clockwise = increase, counterclockwise = decrease; the sign convention must be tested again after changing firmware frameworks.

The port must include:

- A matching `keyboard.toml` and `vial.json` keyboard definition.
- Vial enabled, with RMK's storage feature so remapping survives a restart.
- An explicitly selected Vial unlock combination, for example physical SW1 + SW2, mapped to their actual logical coordinates.
- A USB configuration compatible with ESP32-S3's USB OTG peripheral. Do not assume the Arduino Hardware CDC/JTAG configuration carries over unchanged.
- A tested build that fits this board's flash and RAM.

This guide intentionally does not provide an invented complete `keyboard.toml` or claim that an unmodified template is ready for our hardware. The board definition, exact build target and artifact name must be recorded with the implemented port.

## 4. Add OLED and RGB inside RMK

RMK documents support for SH1106 128x64. Start with its keyboard-status renderer to display the active layer. A custom renderer can replace numeric layer labels with names such as `Work`, `CAD`, and `Media`.

Vial itself supports RGB color, brightness, speed and effects when the firmware implements the lighting protocol. The linked Vial lighting guide describes QMK/VialRGB; RMK Vial keymap support does not by itself establish that the same RGB controls work. RMK documents indicator lights, while a broader RGB architecture is still discussed in its issue tracker. Vial RGB configuration must therefore be verified or implemented for our selected RMK revision.

For the four WS2812 LEDs, add a supported driver/task and connect it to layer/key events. Initial proposed behavior:

| Logical layer | OLED label | LED color |
| --- | --- | --- |
| 0 | Work | Blue |
| 1 | CAD | Green |
| 2 | Media | Purple |

The table is a proposed default, not an installed feature. Test brightness at the existing low level and check the physical LED chain.

Vial changes assignments and layers. Automatic display/RGB responses must be implemented in the firmware. Vial is not a graphical OLED designer: editable labels, icons, splash images, and a future screen-layout editor require an additional configuration mechanism. The OLED and LEDs do not need a second controller or separate firmware image.

## 5. Build and flash the completed port

Once the board project exists, use its checked-in Rust/toolchain configuration and run the build command documented by that project, usually `cargo build --release` from the generated project directory.

RMK's ESP32 flashing documentation uses `espflash` with an ELF artifact. The following is a **template**, not a command ready to paste today:

```text
espflash flash --port <current-ESP32-port> <path-to-built-ESP32-S3-firmware.elf>
```

Use the actual port and artifact produced by the completed port. This differs from the Arduino multi-binary upload in [FLASHING.md](FLASHING.md): do not apply the old Arduino binary offsets to an arbitrary RMK artifact.

If connection stalls at `No serial data received` while the ESP32 USB port is visible, the targeted USB-device reset in [FLASHING.md](FLASHING.md#5-recover-a-visible-usb-port-that-receives-no-data) previously restored communication. That recovery code selects the ROM USB Serial/JTAG identity `303A:1001`; the running RMK USB identity may differ. If necessary enter the ROM loader with BOOT/RESET and recheck the port/identity first. BOOT is the left onboard button below USB; RST is the right.

Keep the Arduino test source available as a recovery baseline. A future RMK upload must record its firmware revision, tool versions, upload result and hardware checks in [VERIFICATION.md](VERIFICATION.md).

## 6. Configure the macropad in Vial (after RMK is installed)

1. Connect the board with a USB data cable and open Vial.
2. Select our macropad. Its definition should show all physical keys and encoder actions.
3. Assign shortcuts in the keymap view; configure clockwise, counterclockwise and encoder push actions.
4. Add layer-switch actions to access the configured layers. Vial layers are not automatic per-application profiles.
5. Use the configured physical unlock combination when Vial requests it for protected operations. Export the layout using Vial's save function for backup.
6. Close Vial, disconnect/reconnect the board, and verify assignments persisted.
7. Check all six buttons, encoder push and both rotation directions. Check that switching layers updates the OLED and RGB as implemented.

Once configuration is stored on the device, normal HID shortcuts and local OLED/RGB behavior should work without Vial running. Launching applications, automatically following the active application, or displaying live Mac data may require optional host-side automation.

## Official references

- [Vial download](https://get.vial.today/download/) and [Vial web](https://vial.rocks/)
- [RMK supported hardware](https://rmk.rs/docs/getting_started/supported_hardwares)
- [RMK local project creation](https://rmk.rs/docs/user_guide/create_firmware/local_compilation)
- [RMK Vial support](https://rmk.rs/docs/features/vial_support)
- [RMK display support](https://rmk.rs/docs/features/display)
- [RMK ESP32 flashing](https://rmk.rs/docs/user_guide/flash_firmware/)
- [Espressif Rust toolchain setup: espup](https://github.com/esp-rs/espup)

- [Vial lighting protocol and GUI](https://get.vial.today/docs/lighting.html)
- [RMK RGB architecture proposal (not a released implementation)](https://github.com/rmk-rs/rmk/issues/979)
