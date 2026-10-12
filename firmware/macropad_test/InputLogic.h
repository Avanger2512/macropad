#pragma once
#include <stdint.h>
#ifdef ARDUINO_ARCH_ESP32
#include <esp_attr.h>
#define INPUT_ISR_CODE IRAM_ATTR
#define INPUT_ISR_DATA DRAM_ATTR
#else
#define INPUT_ISR_CODE
#define INPUT_ISR_DATA
#endif

static INPUT_ISR_DATA const int8_t QUADRATURE_TABLE[16] = {0,1,-1,0,-1,0,0,1,1,0,0,-1,0,-1,1,0};

struct DebounceState { bool raw; bool stable; uint32_t since; };
struct DebounceResult { DebounceState state; bool changed; };
inline DebounceResult debounce(DebounceState old, bool raw, uint32_t now, uint32_t interval) {
  const uint32_t since = raw != old.raw ? now : old.since;
  const bool changed = raw != old.stable && uint32_t(now - since) >= interval;
  return {{raw, changed ? raw : old.stable, since}, changed};
}

struct EncoderState { uint8_t previous; int8_t partial; };
struct EncoderResult { EncoderState state; int8_t step; };
inline INPUT_ISR_CODE EncoderResult decode(EncoderState old, uint8_t current, int8_t transitions) {
  if (current == old.previous) return {old,0};
  if ((current ^ old.previous) == 3) return {{current,0},0};
  const int8_t partial = old.partial + QUADRATURE_TABLE[(old.previous << 2) | current];
  const int8_t step = partial >= transitions ? 1 : partial <= -transitions ? -1 : 0;
  return {{current, int8_t(step ? 0 : partial)},step};
}

#undef INPUT_ISR_CODE
#undef INPUT_ISR_DATA
