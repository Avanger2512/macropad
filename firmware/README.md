# ESP32-S3 SuperMini Macropad Firmware

The board now runs [RMK + Vial](rmk_macropad/README.md), with configurable keys,
encoder actions, four layers, layer RGB and an interactive SH1106 OLED. Start
with [the installation guide](INSTALL_RMK_VIAL.md). The Arduino hardware test
below is retained for diagnostics and recovery.

## Arduino hardware test

Open `macropad_test/macropad_test.ino` in Arduino IDE. Keep `InputLogic.h` and `BoardPins.h` next to the sketch. USB HID is not used; Serial runs over native USB CDC.

For the complete macOS build, upload, and USB recovery procedure, see [FLASHING.md](FLASHING.md). For RMK/Vial and Mac application setup, see [INSTALL_RMK_VIAL.md](INSTALL_RMK_VIAL.md).

## Pinned Build Dependencies

- Boards Manager: **esp32 by Espressif Systems 3.2.0** (October 19 hardware-verified build; earlier builds used 3.3.12).
- Library Manager: **U8g2 by oliver 2.36.19**.
- Library Manager: **Adafruit NeoPixel by Adafruit 1.15.5**.
- `Wire`, `Arduino`, GPIO, and interrupts are included in the esp32 core.

Additional Boards Manager URL:
`https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`

Versions were checked against the official Arduino catalogs. U8g2 2.36.19 is a published Library Manager release; the repository's master version may be newer.

## Arduino IDE → Tools

| Setting | Value |
|---|---|
| Board | ESP32S3 Dev Module |
| USB Mode | Hardware CDC and JTAG |
| USB CDC On Boot | Enabled |
| USB DFU On Boot | Disabled |
| USB Firmware MSC On Boot | Disabled |
| Upload Mode | UART0 / Hardware CDC |
| CPU Frequency | 240MHz (WiFi) |
| Flash Mode | DIO 80MHz |
| Flash Size | 4MB (32Mb), provisional profile |
| Partition Scheme | Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS) |
| PSRAM | Disabled |
| Upload Speed | 460800 |
| Core Debug Level | None |
| Erase All Flash Before Sketch Upload | Disabled |
| Port | USB port of the connected board |

The SuperMini name does not uniquely identify the memory size or type. The 4MB profile with PSRAM disabled is suitable for the test build and a board with at least 4MB of flash; if your revision has a different capacity, select it according to its markings or the seller's specifications. The firmware does not require PSRAM. Compilation does not confirm the specifications of an individual board.

## Wiring

| Device | GPIO / Power |
|---|---|
| SW1 / SW2 / SW3 / SW4 / SW5 / SW6 | 1 / 2 / 3 / 6 / 5 / 4 |
| Encoder CLK / DT / SW | 8 / 9 / 10 |
| SH1106 SDA / SCL | 11 / 12 |
| WS2812 DIN | 13 through 330 ohms |
| OLED and encoder VCC | 3.3V |
| WS2812 VCC | 5V |
| All grounds | Common GND |

Each switch connects its GPIO to GND; INPUT_PULLUP is enabled, and pressed = LOW. For a bare encoder, connect the common A/B terminal to GND; VCC applies to an encoder module. The display is configured specifically for SH1106 128×64, scanning addresses 0x3C and 0x3D.

GPIO3 is used for SW3 on the assembled board (confirmed October 19, 2026). It is a strapping pin; test normal power-on with this button released. Button events include the GPIO number.

## Configurable Constants

At the beginning of the sketch:

- `LED_COUNT = 4`: change this to the actual number of external WS2812 LEDs. All configured LEDs show the same color. Their number cannot be detected automatically.
- `LED_BRIGHTNESS = 32`: low brightness for testing.
- `ENCODER_TRANSITIONS = 4`: if the counter changes once every two detents, try 2.
- `ENCODER_DIRECTION = -1`: clockwise increases the position and counterclockwise decreases it on the assembled board. Set to 1 to reverse.
- `DEBOUNCE_MS = 20`: button debounce filter. The encoder uses quadrature decoding that cancels reverse transitions caused by contact bounce, instead of a delay on each edge.

## Checks After Uploading

1. Connect a USB data cable. If uploading does not start: hold BOOT, press and release RESET, then release BOOT; select the USB port that appears and upload. After the first upload, press RESET if needed.
2. Open Serial Monitor at **115200**. DOWN/UP and ENC events are printed when inputs change; STATUS is printed every 2 seconds, even if the monitor was opened after startup.
3. The OLED should show six button states (1 = pressed), the encoder position/button, A/B, and the latest event. It refreshes 10 times per second; also use Serial to track brief presses.
4. Press each button: one DOWN and one UP; the corresponding colors are red, green, blue, yellow, cyan, and magenta. Pressing encoder SW selects white. The last color remains after release.
5. Turn the encoder in both directions: the position increases/decreases, and the color cycles through the hue wheel. At startup, all 4 WS2812 LEDs cycle through red, green, and blue for 600 ms each, then remain blue. Button polling starts after this test.
6. A missing OLED does not block buttons or RGB: Serial reports `OLED missing`; scanning repeats every 5 seconds. An ACK confirms an I2C device at the address, but does not confirm its model or the display panel's operation.

Encoder GPIOs are handled by interrupts, so OLED transfers do not stop edge capture. Several fast steps may be combined into one ENC entry with the total change.

## If RGB Does Not Respond

Check DIN (not DOUT), the common ground, power, and LED count. With WS2812 powered at 5V, a 3.3V signal may not meet the guaranteed HIGH threshold. For reliable operation, use a 74AHCT125/74HCT245 level shifter powered at 5V between GPIO13 and the 330-ohm resistor. The resistor itself does not raise the signal level. A 500–1000 µF capacitor across the LED strip's power supply is recommended; a large number of LEDs requires a suitable 5V supply. Do not apply 5V to ESP32 GPIOs.

## Sources

- https://github.com/espressif/arduino-esp32/releases/tag/3.3.12
- https://raw.githubusercontent.com/espressif/arduino-esp32/3.3.12/boards.txt
- https://docs.espressif.com/projects/arduino-esp32/en/latest/tutorials/cdc_dfu_flash.html
- https://github.com/olikraus/U8g2_Arduino/releases/tag/2.36.19
- https://github.com/olikraus/u8g2/wiki/u8g2setupcpp#sh1106-128x64_noname
- https://github.com/adafruit/Adafruit_NeoPixel/releases/tag/1.15.5
- https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices

## Repeatable Checks

Native input logic tests are available in `tests/test_inputs.cpp`. Run from this README's directory:

```sh
clang++ -std=c++17 -Wall -Wextra -pedantic tests/test_inputs.cpp -o /tmp/macropad-input-tests
/tmp/macropad-input-tests
```

Build with Arduino CLI after installing the dependencies listed above:

```sh
arduino-cli compile --fqbn 'esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,UploadMode=default,FlashMode=dio,FlashSize=4M,PSRAM=disabled,PartitionScheme=default,CPUFreq=240,UploadSpeed=460800' macropad_test
```

## USB Connection Recovery

If the USB port is visible but Serial and esptool receive no data, follow the targeted libusb reset procedure in [FLASHING.md](FLASHING.md#5-recover-a-visible-usb-port-that-receives-no-data). This recovered the connection on October 19; the full upload and subsequent encoder update passed verification.
