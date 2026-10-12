# Macropad for macOS

An ESP32-S3 SuperMini macropad with six mechanical keys, a rotary encoder with a push button, a SH1106 128×64 OLED, and four external WS2812 RGB LEDs.

## Project structure

```text
macropad/
├── firmware/                 # Test firmware, tests, and instructions
│   ├── macropad_test/
│   │   ├── macropad_test.ino
│   │   └── InputLogic.h
│   ├── tests/test_inputs.cpp
│   ├── README.md
│   └── VERIFICATION.md
├── cad/                      # STL and 3MF mechanical assets
│   ├── MX.stl
│   ├── choc.stl
│   ├── hotswap_mx__with_wing.stl
│   ├── whotswap-MX-v2.3mf
│   └── README.md
├── hardware/                 # Electronics and wiring
│   ├── BOM.md
│   └── WIRING.md
├── docs/PROJECT_CONTEXT.md   # Archived project context
├── LICENSE
└── README.md
```

## Firmware

The [firmware directory](firmware/README.md) contains the unchanged test version from October 7, 2026. It reads the keys and encoder, displays their states on the OLED and in Serial, and controls the RGB LEDs. USB HID and macOS macros are not implemented yet.

Current settings: `LED_COUNT=4`, brightness `32/255`, key debounce `20 ms`, Serial `115200`.

### Build and upload

1. Install **esp32 by Espressif Systems 3.3.12** in Arduino IDE.
2. Install **U8g2 2.36.19** and **Adafruit NeoPixel 1.15.5**.
3. Open [macropad_test.ino](firmware/macropad_test/macropad_test.ino); keep `InputLogic.h` beside the sketch.
4. Select **ESP32S3 Dev Module**, **USB Mode: Hardware CDC and JTAG**, **USB CDC On Boot: Enabled**, **Flash Size: 4MB**, and **PSRAM: Disabled**.
5. Select the board's USB port, upload the firmware, and open Serial Monitor at **115200**.

Full settings and hardware checks: [firmware instructions](firmware/README.md).

### Tests

Run from the repository root:

```sh
clang++ -std=c++17 -Wall -Wextra -pedantic firmware/tests/test_inputs.cpp -o /tmp/macropad-input-tests
/tmp/macropad-input-tests
```

The [October 7 report](firmware/VERIFICATION.md) records compilation and upload results. Startup, an OLED at `0x3C`, the encoder, and five switches were confirmed; one switch and visible RGB output remained unverified. The original report records 100% line and branch coverage for the extracted input logic, not the entire firmware.

## CAD and printing

STL and 3MF files are in [cad](cad/README.md). These are switch mounting models; a complete enclosure, lid, and parametric CAD sources are not available yet. The directory README describes each file's intended purpose, fit verification status, and authorship information.

## Components and wiring

The [bill of materials](hardware/BOM.md) lists the prototype components and additional parts needed to finish the assembly. The [wiring guide](hardware/WIRING.md) matches the saved firmware.

| Component | GPIO |
|---|---|
| SW1–SW6 | 1, 2, 4, 5, 6, 7 |
| Encoder CLK / DT / SW | 8 / 9 / 10 |
| OLED SDA / SCL | 11 / 12 |
| WS2812 DIN | 13 through 330 Ω |

Keys connect their GPIO to common GND when pressed. The OLED and encoder module use 3.3 V; WS2812 LEDs use 5 V.

## License

The project's own firmware and documentation are licensed under [MIT](LICENSE), Copyright (c) 2026 Den. Dependencies retain their respective licenses.

The authors, source links, and licenses of the existing STL/3MF files have not been established. These files are excluded from the project's MIT license; their distribution terms still need clarification.
