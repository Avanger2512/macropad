#include <initializer_list>

#include <cassert>
#include <cstdint>
#include "../macropad_test/InputLogic.h"
#include "../macropad_test/BoardPins.h"
int main() {
  constexpr uint8_t physicalPins[] = {1, 2, 3, 6, 5, 4, 10};
  static_assert(sizeof(BUTTON_PINS) == sizeof(physicalPins));
  for (unsigned i = 0; i < sizeof(physicalPins); ++i) {
    assert(BUTTON_PINS[i] == physicalPins[i]);
    for (unsigned j = i + 1; j < sizeof(physicalPins); ++j)
      assert(BUTTON_PINS[i] != BUTTON_PINS[j]);
  }
  DebounceState b{true,true,0};
  auto r=debounce(b,false,100,20); assert(!r.changed);
  r=debounce(r.state,true,105,20); assert(!r.changed);
  r=debounce(r.state,false,108,20); assert(!r.changed);
  auto stable=debounce(r.state,false,128,20); assert(stable.changed && !stable.state.stable);
  assert(!debounce(stable.state,false,500,20).changed);
  auto release=debounce(stable.state,true,600,20);
  assert(debounce(release.state,true,620,20).changed);
  DebounceState wrap{false,true,UINT32_MAX-10};
  assert(debounce(wrap,false,10,20).changed);
  EncoderState e{3,0}; int sum=0;
  for (uint8_t s: {uint8_t(2),uint8_t(0),uint8_t(1),uint8_t(3)}) {auto q=decode(e,s,4);e=q.state;sum+=q.step;} assert(sum==1);
  for (uint8_t s: {uint8_t(1),uint8_t(0),uint8_t(2),uint8_t(3)}) {auto q=decode(e,s,4);e=q.state;sum+=q.step;} assert(sum==0);
  for (uint8_t s: {uint8_t(2),uint8_t(3),uint8_t(2),uint8_t(0),uint8_t(1),uint8_t(3)}) {auto q=decode(e,s,4);e=q.state;sum+=q.step;} assert(sum==1);
  auto invalid=decode({3,2},0,4); assert(invalid.step==0 && invalid.state.partial==0);
  assert(decode({3,0},3,4).step==0);
  assert(decode({3,0},2,1).step==1);
}
