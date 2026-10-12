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
