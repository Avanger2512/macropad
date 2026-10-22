//! Onboard WS2812 blue status indicator; legacy name preserves event wiring.
use embedded_hal::spi::SpiBus;
use rmk::event::LayerChangeEvent;
use rmk::macros::processor;

use crate::rgb_policy::{encode_frame, status_color};
use crate::status_led_policy::StatusLedPolicy;

/// SPI2 MOSI drives GPIO48 at2.4MHz, mode0, MSB-first. That net is shared with
/// a discrete red LED; framed data ends low, leaving that LED off between writes.
#[processor(subscribe = [LayerChangeEvent], poll_interval = 50)]
pub struct LayerRgb<S: SpiBus<u8>> {
    spi: S,
    layer: u8,
    policy: StatusLedPolicy,
    last_on: Option<bool>,
}

impl<S: SpiBus<u8>> LayerRgb<S> {
    pub fn new(spi: S) -> Self {
        Self { spi, layer: 0, policy: StatusLedPolicy::new(), last_on: None }
    }

    async fn on_layer_change_event(&mut self, event: LayerChangeEvent) {
        self.layer = event.0;
    }

    async fn poll(&mut self) {
        let now = embassy_time::Instant::now().as_millis();
        let policy = self.policy.layer_changed(self.layer, now);
        let (policy, on) = policy.update(crate::alerts::current(now), now);
        self.policy = policy;
        if self.last_on == Some(on) {
            return;
        }
        let frame = encode_frame(status_color(on));
        match self.spi.write(&frame).and_then(|()| self.spi.flush()) {
            Ok(()) => self.last_on = Some(on),
            Err(_) => esp_println::println!("Onboard status LED write failed; retrying"),
        }
    }
}
