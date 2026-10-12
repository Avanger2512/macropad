# Test prototype wiring

Numbers refer to GPIO identifiers, not physical pin positions. This wiring matches the saved firmware.

| Component | Contact | Connection |
|---|---|---|
| SW1–SW6 | First contact | GPIO1, 2, 4, 5, 6, 7 respectively |
| SW1–SW6 | Second contact | GND |
| Encoder | CLK / DT / SW | GPIO8 / GPIO9 / GPIO10 |
| Encoder module | VCC / GND | 3V3 / GND |
| OLED | SDA / SCL | GPIO11 / GPIO12 |
| OLED | VCC / GND | 3V3 / GND |
| WS2812 | DIN | GPIO13 through 330 Ω |
| WS2812 | VCC / GND | USB/VBUS 5 V / GND |

All grounds are common. Keys and the encoder button use INPUT_PULLUP; pressing a button connects its GPIO to GND. Switch LED contacts are separate from the mechanical switch contacts. For a bare encoder, the common A/B contact connects to GND; VCC applies to an encoder module.

GPIO19/20 are reserved for native USB. The external RGB chain contains four LEDs. The firmware searches for an OLED at 0x3C/0x3D; the upload report records 0x3C.

Full instructions and troubleshooting: [firmware/README.md](../firmware/README.md).
