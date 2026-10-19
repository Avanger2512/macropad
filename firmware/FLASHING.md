# Flashing the assembled ESP32-S3 macropad (macOS)

Run these commands from the repository root. This is the procedure that successfully flashed the assembled board on October 19, 2026, including recovery from a stalled USB connection.

## Verified board and firmware

- ESP32-S3 revision v0.2, 4 MB flash, 2 MB PSRAM; this firmware keeps PSRAM disabled.
- USB Serial/JTAG: VID `303A`, PID `1001`; the observed serial number is `28:84:85:6F:32:18`.
- Physical SW1–SW6: GPIO `1, 2, 3, 6, 5, 4`, defined in `macropad_test/BoardPins.h`.
- Encoder CLK/DT/SW: GPIO `8/9/10`. `ENCODER_DIRECTION = -1`: clockwise increases, counterclockwise decreases. The owner confirmed both buttons and direction work.
- OLED: SH1106, SDA/SCL `11/12`, detected address `0x3C`.
- Four external WS2812 LEDs: GPIO13.

The successful October 19 build used **Arduino-ESP32 3.2.0**, **U8g2 2.36.19**, and **Adafruit NeoPixel 1.15.5**. Earlier October 7 builds used core 3.3.12; use 3.2.0 to reproduce the latest hardware-verified build. Do not silently substitute a different core.

## 1. Prepare the tools

Use an installed `arduino-cli`, or the copy bundled with Arduino IDE on this Mac:

```sh
ARDUINO_CLI='/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli'
"$ARDUINO_CLI" version
"$ARDUINO_CLI" core list
```

If dependencies are missing, install the versions above into the configured Arduino environment:

```sh
"$ARDUINO_CLI" core update-index --additional-urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
"$ARDUINO_CLI" core install esp32:esp32@3.2.0 --additional-urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
"$ARDUINO_CLI" lib update-index
"$ARDUINO_CLI" lib install 'U8g2@2.36.19' 'Adafruit NeoPixel@1.15.5'
```

Prepare an isolated Python environment for uploading, monitoring, and USB recovery:

```sh
FLASH_VENV=/tmp/macropad-flash-venv
python3 -m venv "$FLASH_VENV"
"$FLASH_VENV/bin/python" -m pip install 'cryptography>=43,<46' 'esptool==5.6.0' 'pyserial==3.5' 'pyusb==1.3.1' 'libusb-package==1.0.30.0'
FLASH_PYTHON="$FLASH_VENV/bin/python"
```

The cryptography constraint selects a compatible binary dependency used during this session. Temporary tools/build directories can disappear after a reboot; recreate them rather than relying on old `/tmp` files.

## 2. Test and compile the current source

```sh
clang++ -std=c++17 -Wall -Wextra -Werror -pedantic firmware/tests/test_inputs.cpp -o /tmp/macropad-input-tests
/tmp/macropad-input-tests

FQBN='esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,UploadMode=default,FlashMode=dio,FlashSize=4M,PSRAM=disabled,PartitionScheme=default,CPUFreq=240,UploadSpeed=460800'
BUILD_DIR=/tmp/macropad-map-build
"$ARDUINO_CLI" compile --warnings all --build-path "$BUILD_DIR" --fqbn "$FQBN" firmware/macropad_test
```

Confirm the build reports core 3.2.0 and succeeds before uploading. The final direction-reversed build reported 359694 bytes of program storage and 24052 bytes RAM.

If using libraries installed outside the configured Arduino sketchbook, add `--libraries /absolute/path/to/libraries` to the compile command. During this session they were installed in `/tmp/macropad-arduino/user/libraries`; that temporary path is not required for future builds.

## 3. Identify the board and release its serial port

Connect a USB data cable and close Serial Monitor or any other program using the port.

```sh
"$ARDUINO_CLI" board list
"$FLASH_PYTHON" -m serial.tools.list_ports -v
```

Select the Espressif `303A:1001` device. On the verified Mac it was:

```sh
PORT=/dev/cu.usbmodem2101
ESP32_CORE="$HOME/Library/Arduino15/packages/esp32/hardware/esp32/3.2.0"
```

Port names can change after reconnection. Recheck the port; do not assume the previous name is still correct.

## 4. Upload (the successful command)

```sh
"$FLASH_PYTHON" -m esptool \
  --chip esp32s3 --port "$PORT" --baud 115200 \
  --before usb-reset --after hard-reset --connect-attempts 3 \
  write-flash -z --flash-mode keep --flash-freq keep --flash-size keep \
  0x0 "$BUILD_DIR/macropad_test.ino.bootloader.bin" \
  0x8000 "$BUILD_DIR/macropad_test.ino.partitions.bin" \
  0xe000 "$ESP32_CORE/tools/partitions/boot_app0.bin" \
  0x10000 "$BUILD_DIR/macropad_test.ino.bin"
```

Success means the chip is identified, every written region reports `Hash of data verified`, and the command exits successfully after `Hard resetting via RTS pin`. Do not report success if output stops at `Connecting`.

These addresses apply to this ESP32-S3 Arduino build and its partition scheme. Use the binaries from the same fresh build, and the matching core's `boot_app0.bin`.

## 5. Recover a visible USB port that receives no data

Observed failure: the device enumerated as `303A:1001`, but Serial received nothing and every esptool attempt ended with `No serial data received`. BOOT/RESET, BOOT-held reconnection, lower baud, the `/dev/tty.*` port, 1200-baud touch, and `--no-stub` did not recover it. OpenOCD USB-JTAG also failed while reading a USB string descriptor.

**The step that recovered communication was a targeted USB-device reset through libusb.** Its exact underlying cause was not established; these symptoms alone did not demonstrate faulty BOOT hardware or a need for a UART adapter.

Close all serial tools, connect exactly one matching Espressif device, then run:

```sh
"$FLASH_PYTHON" - <<'PY'
import libusb_package
import usb.util

boards = list(libusb_package.find(find_all=True, idVendor=0x303A, idProduct=0x1001))
if len(boards) != 1:
    raise SystemExit("Connect exactly one ESP32 USB Serial/JTAG device; no reset performed")
board = boards[0]
try:
    board.reset()
    print("ESP32 USB-device reset completed")
finally:
    usb.util.dispose_resources(board)
PY
```

This resets the USB connection without erasing flash. Recheck `board list` and `PORT`, then repeat step 4. On October 19, this immediately restored communication and the full upload passed hash verification. The subsequent encoder update uploaded normally without another libusb reset.

In a sandboxed agent session, direct USB/serial access and package downloads may need the tool's approved elevated execution mode. This is distinct from the board's BOOT mode; an OS permission error is not a firmware failure.

If the targeted reset does not help, try BOOT/RESET: BOOT is the left button below USB in the saved board photo; RST is the right button. Hold BOOT, press/release RST, then release BOOT. A dark OLED can be consistent with the ROM loader, but is not proof of a working connection. Do not erase all flash or modify eFuses to troubleshoot a missing serial response.

## 6. Verify startup and physical controls

```sh
"$FLASH_PYTHON" - "$PORT" <<'PY'
import sys
import time
import serial

with serial.Serial(sys.argv[1], 115200, timeout=0.5) as port:
    end = time.monotonic() + 10
    while time.monotonic() < end:
        print(port.read(8192).decode(errors="replace"), end="", flush=True)
PY
```

Expected idle output, approximately every two seconds:

```text
STATUS keys=000000 encSW=0 pos=0 OLED=0x3C
```

Press SW1–SW6: numbers must match the physical buttons and colors must be red, green, blue, yellow, cyan, magenta. Events include the GPIO, for example `SW3 GPIO3 DOWN`. Turn clockwise to increase the position and counterclockwise to decrease it. The owner confirmed these behaviors after the October 19 uploads. Record new results in `VERIFICATION.md` and close the serial port afterward.

## References

- [Espressif: esptool troubleshooting](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/troubleshooting.html)
- [Espressif: USB CDC flashing](https://docs.espressif.com/projects/arduino-esp32/en/latest/tutorials/cdc_dfu_flash.html)
- [Espressif: USB-JTAG / OpenOCD](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/jtag-debugging/)
