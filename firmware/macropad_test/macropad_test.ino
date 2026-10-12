#include <Arduino.h>
#include <initializer_list>
#include <Wire.h>
#include <U8g2lib.h>
#include <Adafruit_NeoPixel.h>
#include "InputLogic.h"

constexpr uint8_t BUTTON_PINS[] = {1, 2, 4, 5, 6, 7, 10};
constexpr uint8_t CLK_PIN = 8, DT_PIN = 9, SDA_PIN = 11, SCL_PIN = 12, RGB_PIN = 13;
constexpr uint16_t LED_COUNT = 4;  // Set to the actual number of external WS2812 LEDs.
constexpr uint8_t LED_BRIGHTNESS = 32;
constexpr uint32_t DEBOUNCE_MS = 20, DISPLAY_MS = 100;
constexpr int8_t ENCODER_TRANSITIONS = 4;  // Try 2 if there is one event per two detents.
constexpr int8_t ENCODER_DIRECTION = 1;  // Set -1 to reverse direction.
static_assert(LED_COUNT > 0 && ENCODER_TRANSITIONS > 0, "Invalid configuration");

U8G2_SH1106_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE, SCL_PIN, SDA_PIN);
Adafruit_NeoPixel pixels(LED_COUNT, RGB_PIN, NEO_GRB + NEO_KHZ800);
DebounceState buttons[7];
EncoderState encoder{3, 0};
portMUX_TYPE encoderMux = portMUX_INITIALIZER_UNLOCKED;
volatile int32_t pendingSteps = 0;
volatile uint8_t encoderAB = 3;
int32_t position = 0;
uint16_t hue = 0;
uint8_t oledAddress = 0;
char lastEvent[32] = "READY";
uint32_t lastDisplay = 0, lastRetry = 0;

// Capture transitions during OLED transfers too. Gray-code decoding cancels bounce
// and rejects illegal transitions; delay-based debounce would lose encoder edges.
void ARDUINO_ISR_ATTR encoderChanged() {
  const uint8_t ab = (digitalRead(CLK_PIN) << 1) | digitalRead(DT_PIN);
  portENTER_CRITICAL_ISR(&encoderMux);
  const EncoderResult next = decode(encoder, ab, ENCODER_TRANSITIONS);
  encoder = next.state;
  encoderAB = ab;
  if (next.step && pendingSteps < 100000 && pendingSteps > -100000)
    pendingSteps += next.step;
  portEXIT_CRITICAL_ISR(&encoderMux);
}

void showColor(uint32_t color) {
  for (uint16_t i = 0; i < LED_COUNT; ++i) pixels.setPixelColor(i, color);
  pixels.show();
}

void recordEvent(const char* event) {
  snprintf(lastEvent, sizeof(lastEvent), "%s", event);
  if (Serial) Serial.printf("[%lu ms] %s\n", (unsigned long)millis(), event);
}

uint8_t findDisplay() {
  for (uint8_t address : {uint8_t(0x3C), uint8_t(0x3D)}) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) return address;
  }
  return 0;
}

void connectDisplay() {
  oledAddress = findDisplay();
  if (!oledAddress) {
    recordEvent("OLED missing: 0x3C/0x3D");
    return;
  }
  oled.setI2CAddress(oledAddress << 1); // U8g2 uses an 8-bit I2C address.
  oled.setBusClock(400000);
  oled.begin();
  Wire.setTimeOut(20);
  char event[32];
  snprintf(event, sizeof(event), "OLED found: 0x%02X", oledAddress);
  recordEvent(event);
}

void pollButtons(uint32_t now) {
  constexpr uint32_t colors[7] = {0xFF0000,0x00FF00,0x0000FF,0xFFFF00,0x00FFFF,0xFF00FF,0xFFFFFF};
  for (uint8_t i = 0; i < 7; ++i) {
    const DebounceResult next = debounce(buttons[i], digitalRead(BUTTON_PINS[i]), now, DEBOUNCE_MS);
    buttons[i] = next.state;
    if (!next.changed) continue;
    char event[32];
    if (i < 6) snprintf(event, sizeof(event), "SW%u %s", i + 1, next.state.stable ? "UP" : "DOWN");
    else snprintf(event, sizeof(event), "ENC SW %s", next.state.stable ? "UP" : "DOWN");
    recordEvent(event);
    if (!next.state.stable) showColor(colors[i]);
  }
}

void pollEncoder() {
  portENTER_CRITICAL(&encoderMux);
  const int32_t steps = pendingSteps;
  pendingSteps = 0;
  portEXIT_CRITICAL(&encoderMux);
  if (!steps) return;
  const int32_t directed = steps * ENCODER_DIRECTION;
  // Bound position so a long-running hardware test cannot overflow a signed integer.
  const int64_t candidate = int64_t(position) + directed;
  position = int32_t(constrain(candidate, int64_t(-999999), int64_t(999999)));
  hue = uint16_t(int64_t(hue) + int64_t(directed) * 4096);
  showColor(pixels.ColorHSV(hue, 255, 255));
  char event[32];
  snprintf(event, sizeof(event), "ENC %+ld POS %ld", (long)directed, (long)position);
  recordEvent(event);
}

void drawDisplay() {
  portENTER_CRITICAL(&encoderMux);
  const uint8_t ab = encoderAB;
  portEXIT_CRITICAL(&encoderMux);
  char line[32];
  oled.clearBuffer();
  oled.setFont(u8g2_font_6x10_tf);
  oled.drawStr(0, 10, "MACROPAD HW TEST");
  snprintf(line, sizeof(line), "1:%u 2:%u 3:%u", !buttons[0].stable, !buttons[1].stable, !buttons[2].stable);
  oled.drawStr(0, 21, line);
  snprintf(line, sizeof(line), "4:%u 5:%u 6:%u", !buttons[3].stable, !buttons[4].stable, !buttons[5].stable);
  oled.drawStr(0, 32, line);
  snprintf(line, sizeof(line), "ENC:%ld SW:%u", (long)position, !buttons[6].stable);
  oled.drawStr(0, 43, line);
  snprintf(line, sizeof(line), "A:%u B:%u RGB:%u", (ab >> 1) & 1, ab & 1, LED_COUNT);
  oled.drawStr(0, 53, line);
  oled.setFont(u8g2_font_4x6_tr);
  oled.drawStr(0, 63, lastEvent);
  oled.sendBuffer();
}

void setup() {
  Serial.begin(115200); // Native USB CDC; no USB HID.
  const uint32_t started = millis();
  while (!Serial && uint32_t(millis() - started) < 1500) delay(1);
  for (uint8_t i = 0; i < 7; ++i) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    // A button held at boot produces DOWN after the debounce interval.
    buttons[i] = {true, true, millis()};
  }
  pinMode(CLK_PIN, INPUT_PULLUP);
  pinMode(DT_PIN, INPUT_PULLUP);
  encoderAB = (digitalRead(CLK_PIN) << 1) | digitalRead(DT_PIN);
  encoder = {encoderAB, 0};
  attachInterrupt(digitalPinToInterrupt(CLK_PIN), encoderChanged, CHANGE);
  attachInterrupt(digitalPinToInterrupt(DT_PIN), encoderChanged, CHANGE);
  pixels.begin();
  pixels.setBrightness(LED_BRIGHTNESS);
  recordEvent("RGB TEST: RED");
  showColor(pixels.Color(255, 0, 0));
  delay(600);
  recordEvent("RGB TEST: GREEN");
  showColor(pixels.Color(0, 255, 0));
  delay(600);
  recordEvent("RGB TEST: BLUE");
  showColor(pixels.Color(0, 0, 255));
  delay(600);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setTimeOut(20);
  connectDisplay();
  recordEvent("READY: press / turn");
}

void loop() {
  const uint32_t now = millis();
  pollButtons(now);
  pollEncoder();
  if (oledAddress && uint32_t(now - lastDisplay) >= DISPLAY_MS) {
    lastDisplay = now;
    drawDisplay();
  }
  if (!oledAddress && uint32_t(now - lastRetry) >= 5000) {
    lastRetry = now;
    connectDisplay();
  }
  // Periodic summary also appears when Serial Monitor was opened after boot.
  static uint32_t lastStatus = 0;
  if (Serial && uint32_t(now - lastStatus) >= 2000) {
    lastStatus = now;
    Serial.printf("STATUS keys=%u%u%u%u%u%u encSW=%u pos=%ld OLED=0x%02X\n",
      !buttons[0].stable, !buttons[1].stable, !buttons[2].stable,
      !buttons[3].stable, !buttons[4].stable, !buttons[5].stable,
      !buttons[6].stable, (long)position, oledAddress);
  }
  delay(1);
}
