# Verification Results — October 7, 2026

Arduino CLI 1.2.0, Arduino-ESP32 3.3.12, U8g2 2.36.19, Adafruit NeoPixel 1.15.5.

FQBN:
`esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,UploadMode=default,FlashMode=dio,FlashSize=4M,PSRAM=disabled,PartitionScheme=default,CPUFreq=240,UploadSpeed=460800`

The build with `--warnings all` completed with exit code 0; the log contains no errors or warnings.

```
Sketch uses 336622 bytes (25%) of program storage space. Maximum is 1310720 bytes.
Global variables use 25752 bytes (7%) of dynamic memory, leaving 301928 bytes for local variables. Maximum is 327680 bytes.
```

Native debounce/quadrature decoder tests pass. Checks cover DOWN/UP, contact bounce, holding a button, millis rollover, both encoder directions, reverse transitions, an invalid transition, and transition-count configuration.

InputLogic.h function coverage: 100% of lines and branches (Clang llvm-cov). This covers the extracted input logic, not the entire firmware and its libraries.

Compilation checks Arduino API and library compatibility with ESP32-S3. Initial verification was limited to compilation; the subsequent upload result is recorded below. A full hardware test of all inputs and RGB has not yet been completed. Manual verification steps are in README.md. The build does not confirm the flash capacity of a specific SuperMini revision.

## Board Upload — October 7, 2026

At the user's request, the firmware was successfully uploaded to the connected ESP32-S3 revision v0.2. Built-in 4MB flash and 2MB PSRAM were detected; PSRAM remains disabled in the test profile. Hash verification passed for all written regions, and the bootloader restarted the board.

Serial Monitor at 115200 confirmed startup and an OLED response at I2C address 0x3C:

```
[346 ms] OLED found: 0x3C
[346 ms] READY: press / turn
STATUS keys=000000 encSW=0 pos=0 OLED=0x3C
```

Repeated STATUS messages were observed without errors. No buttons were pressed, encoder SW was not pressed, and the position was 0. The visible OLED image, WS2812 colors, and events from actual presses/rotation require manual verification. Serial Monitor was closed after reading, releasing the port.

## RGB Update — October 7, 2026

The user specified the WS2812 count: 4. LED_COUNT=4, brightness 32/255. A startup sequence was added: red/green/blue for 600 ms each. The build with --warnings all completed without warnings or errors; size was 336726 bytes of flash and 25752 bytes of RAM. Upload completed with hash verification. Serial confirmed RGB TEST RED/GREEN/BLUE, READY, and OLED 0x3C. This confirms command execution, not visible LED illumination.

Previous diagnostics recorded DOWN/UP for SW1–SW5; SW6 was not confirmed. The user confirmed that all but one switch worked, and that the encoder/display worked. Visible RGB operation has not yet been confirmed.

## Assembled Board Mapping — October 19, 2026

The user reported physical SW1→old SW1, SW2→old SW2, SW4→old SW5, SW5→old SW4, SW6→old SW3; physical SW3 produced no events. They confirmed SW3 is connected to the board pin marked 3. The previous firmware never scanned GPIO3.

The corrected SW1–SW6 map is GPIO1, 2, 3, 6, 5, 4; encoder SW remains GPIO10. The mapping is shared with native tests in BoardPins.h, and button events now include their GPIO.

Native debounce, encoder, mapping and pin uniqueness tests pass with Clang C++17 and -Wall -Wextra -Werror -pedantic. Arduino CLI build with --warnings all passed without warnings using the locally installed ESP32 core 3.2.0, U8g2 2.36.19 and Adafruit NeoPixel 1.15.5. This differs from the earlier pinned core 3.3.12; its separate download was stopped. The corrected build uses 359690 bytes flash and 24052 bytes RAM.

USB upload to /dev/cu.usbmodem2101 failed before writing: esptool reported “No serial data received.” The port was free and VID/PID 303A:1001 identified the ESP32 USB Serial/JTAG interface. Retries after user-performed BOOT/RESET and BOOT-held USB reconnection, no-reset connection at 115200, and USB-specific reset also received no data. The same connection failure was reproduced with fresh esptool 5.6.0. No flash regions were written. Upload and physical button validation remain pending diagnosis of USB/bootloader connectivity.

Further retries: the user confirmed the previous RGB/OLED test still runs and USB is connected directly to the computer. A fresh esptool USB-reset upload and a no-reset upload while BOOT was held both failed with no serial data, before any flash writes. GPIO0/BOOT and reset-level checks are the next hardware diagnostic.

Alternative software paths were also tried: /dev/tty.usbmodem2101 with traced sync at 9600 baud, CDC 1200-baud touch, and ROM-only write-flash (--no-stub) through the tty port. All stopped at sync with no received bytes; no flash writes occurred. A separate USB-UART interface on UART0 is a possible next transport if available.

## Successful Upload and USB Recovery — October 19, 2026

The connectivity failure was resolved by a targeted libusb USB-device reset of the single attached Espressif device (VID 303A, PID 1001). Before recovery, OpenOCD also failed while reading USB string descriptors. After the USB reset, esptool 5.6.0 immediately connected to ESP32-S3 revision v0.2, MAC 28:84:85:6F:32:18, reporting 4MB flash and 2MB PSRAM. The exact cause of the stalled USB communication was not established; BOOT-button or board failure was not demonstrated.

The corrected firmware was successfully written at bootloader 0x0, partitions 0x8000, boot_app0 0xE000 and application 0x10000. All four regions passed hash verification; esptool exited with status 0 and issued a hard reset. This supersedes the pending-upload status above. Physical button/color confirmation is still required.

Post-upload USB Serial check passed: four consecutive `STATUS keys=000000 encSW=0 pos=0 OLED=0x3C` messages were received. The firmware is running and the OLED acknowledges at 0x3C. No buttons were pressed during this observation.

## Encoder Direction Reversal — October 19, 2026

The user confirmed all six physical buttons work after remapping. At their request ENCODER_DIRECTION was changed from 1 to -1, reversing position and hue direction. Native tests and Arduino --warnings all build passed (359694 bytes flash, 24052 bytes RAM). Upload using esptool 5.6.0 with USB reset succeeded, all regions passed hash verification, and post-reset Serial confirmed STATUS and OLED=0x3C. The user subsequently confirmed the encoder direction is corrected. All six buttons and the requested encoder direction are now physically verified.
