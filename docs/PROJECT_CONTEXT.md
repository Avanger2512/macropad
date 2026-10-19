> Archive of the first session handoff. Source files and a report dated October 7, 2026 were recovered after this archive was created: see [firmware/VERIFICATION.md](../firmware/VERIFICATION.md). The references below to 5–6 LEDs and missing source files reflect the incomplete handoff context; the recovered version uses 4 LEDs.

# First Session Context: Components and Wiring

Source: [Creating a macropad for macOS](https://chatgpt.com/share/6acca682-6e54-83ed-97ae-ab7ec588329c).
Handoff date: 2026-10-12.

## Completeness and Status of the Information

The accessible final portion of the shared conversation was read: an explanation of MX switch terminals, the final proposed pin assignment, the user's confirmation that the breadboard was assembled, and the response about test firmware. The page provides navigation through 14 user messages, but the earlier messages were not read because navigation failed due to an automatic action review error (429).

The sections below distinguish the assembly confirmed by the user, the assistant's proposals, and information from the conversation's final summary. This is a handoff of project context, rather than an independent electrical verification of the board or components.

## Project Goal and Stage

- A macropad for macOS with 6 mechanical keys, an encoder, an OLED display, and RGB lighting.
- The user reported that the ESP32-S3 had arrived; the assistant assumed the previously selected ESP32-S3 SuperMini. The exact board revision needs to be checked against its markings.
- The user confirmed assembling the breadboard according to the wiring below and requested test firmware and verification.
- First debug the electronics and firmware on the breadboard, then work on the enclosure.

## Assembled Board Update — October 19, 2026

Physical SW1–SW6 use GPIO1, 2, 3, 6, 5, 4 respectively. Press tests identified SW1/2/4/5/6; the user confirmed SW3 is wired to the pin marked 3. The earlier firmware did not poll GPIO3. GPIO7 is unused. This supersedes the breadboard assignment below.

## Recorded Breadboard Pin Assignment

The numbers in the table are GPIO numbers, not physical pin positions.

| Component | Terminal | Connection |
|---|---|---|
| Key SW1 | First electrical terminal | GPIO1 |
| Key SW2 | First electrical terminal | GPIO2 |
| Key SW3 | First electrical terminal | GPIO4 |
| Key SW4 | First electrical terminal | GPIO5 |
| Key SW5 | First electrical terminal | GPIO6 |
| Key SW6 | First electrical terminal | GPIO7 |
| All keys | Second electrical terminal | Common GND |
| Encoder | CLK | GPIO8 |
| Encoder | DT | GPIO9 |
| Encoder | SW | GPIO10 |
| Encoder | + | 3V3 |
| Encoder | GND | Common GND |
| OLED | SDA | GPIO11 |
| OLED | SCL | GPIO12 |
| OLED | VCC | 3V3 |
| OLED | GND | Common GND |
| RGB strip | DIN | GPIO13 through 330 Ω |
| RGB strip | +5V | 5V from the board's USB/VBUS |
| RGB strip | GND | Common GND |

The user specifically confirmed GPIO13 → 330 Ω → DIN, with the OLED and encoder powered from 3V3 and RGB powered from 5V. The presence of additional parts, such as a capacitor or level shifter, was not confirmed.

## Keys and Encoder

- A mechanical MX switch has two non-polarized terminals for the switching mechanism: either terminal can connect to GPIO, with the other connected to GND. Built-in LED/RGB terminals, if present, are separate from this pair.
- A direct connection from each key to a separate GPIO was proposed; this circuit does not use a matrix.
- Use `INPUT_PULLUP` for the keys: released → HIGH, pressed → LOW. Separate pull-up resistors are not required in the proposed circuit.
- The response identifies the encoder as KY-040 / Encoder; the user's exact model could not be established from the portion that was read.
- Powering the encoder module from 3.3 V was proposed to prevent its outputs from applying 5 V to the ESP32 GPIOs.
- All components share a common ground.

## OLED

- The final response specifies SH1106; the summary refers to a 1.3-inch OLED already owned by the user. The original message identifying the display model was not read, so the controller and size need to be confirmed from the module itself.
- I²C interface, SDA = GPIO11, SCL = GPIO12; proposed initialization: `Wire.begin(11, 12)`.
- The I²C address, resolution, exact model, and terminal layout are not specified in the accessible portion.

## RGB Lighting and Power

- A 5 V addressable WS2812 strip was discussed. The summary lists 5–6 LEDs; the later response mentions an initial test with six LEDs. The actual count needs to be confirmed.
- The LEDs are powered from USB/VBUS; GPIO13 carries data only.
- A 330 Ω resistor was proposed in series with the data line; it is included in the wiring confirmed by the user.
- A software brightness limit of approximately 30–40% was proposed.
- The assistant recommended a 470–1000 µF electrolytic capacitor between 5V and GND (positive to 5V, negative to GND); its presence in the assembly was not confirmed.
- The final summary mentions a recommendation for a logic level shifter for the RGB signal. The final breadboard diagram shows a direct signal from GPIO through a resistor. The reliability of a 3.3 V signal for the specific 5 V strip has not been verified; the resistor must not be treated as a level shifter.
- The conversation's claim that USB power is sufficient at limited brightness is not supported by project measurements. The exact current budget has not yet been determined.

## Board Pins Left Unused

The original response intentionally excluded GPIO3 as a strapping pin; TX/RX were kept in reserve. GPIO19/20 were identified as USB D−/D+ and are not used for peripherals. A possible onboard WS2812 on GPIO48 on a common SuperMini variant was also mentioned. These details have not yet been verified for the specific board revision; the onboard LED on GPIO48 is not part of the confirmed external wiring.

## Initial Test Firmware Plan from the Conversation

1. Check the electronics without USB HID.
2. Read SW1–SW6 on GPIO1, 2, 4, 5, 6, 7.
3. Read encoder rotation and its button on GPIO8, 9, 10.
4. Check the OLED on I²C GPIO11/12 with the assumed SH1106 controller.
5. Check the WS2812 LEDs on GPIO13.
6. Report events through Serial and show states on the OLED.
7. Make the lighting respond to keys and encoder rotation.
8. Debounce keys and handle encoder contact bounce.
9. Add USB HID for macOS after successful breadboard verification.

The assistant's response states that the task was handed off to Work mode for implementation and compilation checks. The source code, compilation log, flashing result, and hardware test result are absent from the portion that was read. Firmware implementation and testing were therefore not recorded as completed in this archive.

## Information Still to Recover or Confirm

- The original shopping list, component links, and decisions from earlier messages.
- The exact ESP32-S3 SuperMini revision and whether its GPIO markings match the table.
- The OLED model and specifications, encoder model, and LED type and count.
- Macro assignments, modes, macOS keyboard shortcuts, and encoder behavior.
- Physical layout, enclosure dimensions, selected switch type, and mounting method.
- Whether the capacitor and level shifter are actually installed, and the power budget.
- The build environment and existing firmware work results, if they were created in another session.

When continuing the project, use the pin assignment above as the confirmed wiring of the assembled breadboard. Do not replace it without an explicit decision, and do not treat the assistant's proposals as evidence of hardware verification.
