# Bill of materials

Components of the current prototype and the saved test firmware configuration. Purchase links and exact part numbers are not available in the recovered materials.

| Component | Quantity | Notes |
|---|---:|---|
| ESP32-S3 SuperMini | 1 | Upload report: ESP32-S3 rev. v0.2, 4 MB flash, 2 MB PSRAM; PSRAM disabled |
| MX mechanical switch | 6 | Direct GPIO connections; exact manufacturer and model not recorded |
| Keycap compatible with the selected switch | 6 | Needed for the completed assembly; availability not recorded |
| Rotary encoder with push button | 1 | CLK/DT/SW; referred to as KY-040, exact model not established |
| SH1106 128×64 I²C OLED | 1 | Firmware uses this controller; responds at 0x3C; context mentions a 1.3-inch display |
| WS2812 addressable RGB LEDs, 5 V | 4 LEDs | Count confirmed by the user and saved in firmware |
| 330 Ω resistor | 1 | In series between GPIO13 and DIN |
| USB data cable | 1 | Connector depends on the board; used for power and uploads |
| Breadboard and jumper wires | As required | Prototype assembled; wire count not recorded |

## Parts needed to finish the mechanical assembly

- Mounts or sockets for six switches: the type and quantity of individual printed parts have not been decided. Available models are listed in [cad/README.md](../cad/README.md).
- Enclosure, encoder knob, and fasteners: finished files, dimensions, and specifications have not been recorded.
- Hot-swap contacts or sockets: exact type not established; compatibility with the available models has not been checked.

## Additional parts recommended in the original instructions

A 470–1000 µF capacitor between RGB 5 V and GND, and a 74AHCT125 or 74HCT245 level shifter for DIN. Their presence in the current prototype is not confirmed. See the [original instructions](../firmware/README.md).

## Confirmed enclosure fasteners and print setup (2026-10-20)

- Heat-set inserts: M2 thread, 4 mm length, 3.5 mm outside diameter; eight total
  (four carrier mounts and four independent bottom-cover mounts).
- CAD insert pilots: 3.2 mm diameter, 4.5 mm depth. Physical heat-set fit remains
  to be checked in the selected PLA Matte.
- Bottom-cover screws: measured cylindrical socket heads, 4 mm diameter and
  2 mm height. M2 x 6 mm (length below head) is the nominal cover candidate:
  the 2 mm cover leaves approximately 4 mm inside the insert. Confirm actual
  seating and engagement after installing the inserts.
- The current cover has no head recess. Feet must stand higher than the 2 mm
  screw-head projection; approximately 3 mm rubber feet are a candidate, with
  at least 2.5 mm effective installed height.
- Printer stated by user: Bambu Lab X2D; 0.4 mm nozzle; gray PLA Matte. No sliced
  job or printer profile was generated or verified during the geometry audit.
- Encoder threaded bushing measured by user: 7 mm diameter, 7 mm threaded length.
  V8 upper-shell opening is 7.4 mm, with a 2.4 mm shell wall and 4.6 mm remaining
  thread before allowance for the washer and nut. Actual encoder body/shaft and
  push clearance still require assembly checks.
