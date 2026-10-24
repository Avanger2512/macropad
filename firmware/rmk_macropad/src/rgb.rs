//! Onboard WS2812 color status indicator; legacy name preserves event wiring.
use embedded_hal::spi::SpiBus;
use esp_hal::gpio::{Flex, OutputSignal};
use rmk::event::{KeyboardEvent, KeyboardEventSource, LayerChangeEvent};
use rmk::macros::processor;

use crate::rgb_policy::{encode_frame, indicator_color};
use crate::status_led_policy::StatusLedPolicy;

/// SPI2 MOSI drives GPIO48 at2.4MHz, mode0, MSB-first. That net is shared with
/// a discrete red LED; experimental frames end high to illuminate it at idle.
#[processor(subscribe = [LayerChangeEvent, KeyboardEvent], poll_interval = 50)]
pub struct LayerRgb<S: SpiBus<u8>> {
    spi: S,
    pin: Flex<'static>,
    layer: u8,
    policy: StatusLedPolicy,
    last_color: Option<[u8; 3]>,
}

impl<S: SpiBus<u8>> LayerRgb<S> {
    pub fn new(spi: S, mut pin: Flex<'static>) -> Self {
        pin.set_high();
        pin.set_output_enable(true);
        Self { spi, pin, layer: 0, policy: StatusLedPolicy::new(), last_color: None }
    }

    async fn on_layer_change_event(&mut self, event: LayerChangeEvent) {
        self.layer = event.0;
    }

    async fn on_keyboard_event(&mut self, event: KeyboardEvent) {
        if event.pressed && matches!(event.source, KeyboardEventSource::Key(_)) {
            let now = embassy_time::Instant::now().as_millis();
            self.policy = self.policy.key_pressed(now);
        }
    }

    async fn poll(&mut self) {
        let now = embassy_time::Instant::now().as_millis();
        let policy = self.policy.layer_changed(self.layer, now);
        let (source, alert) = crate::alerts::snapshot(now);
        let (policy, on) = policy.update(alert, now);
        self.policy = policy;
        let color = indicator_color(on, policy.input_active(now), source, now);
        if self.last_color == Some(color) {
            return;
        }
        let frame = encode_frame(color);
        OutputSignal::FSPID.connect_to(&self.pin);
        let result = self.spi.write(&frame).and_then(|()| self.spi.flush());
        // Restore an explicit GPIO HIGH, independent of SPI idle-level behavior.
        OutputSignal::FSPID.disconnect_from(&self.pin);
        self.pin.set_high();
        match result {
            Ok(()) => self.last_color = Some(color),
            Err(_) => esp_println::println!("Onboard status LED write failed; retrying"),
        }
    }
}
