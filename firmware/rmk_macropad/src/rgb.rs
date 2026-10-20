//! Optional four-pixel layer indicator; not the Vial RGB protocol.
use embedded_hal::spi::SpiBus;
use rmk::event::LayerChangeEvent;
use rmk::macros::processor;

use crate::rgb_policy::{encode_frame, layer_color};

/// The bus must use mode 0, MSB first, 2.4 MHz and exclusively drive GPIO13.
/// Writes take about 720 us and occur only when the active layer changes.
#[processor(subscribe = [LayerChangeEvent], poll_interval = 50)]
pub struct LayerRgb<S: SpiBus<u8>> {
    spi: S,
    layer: u8,
    dirty: bool,
}

impl<S: SpiBus<u8>> LayerRgb<S> {
    pub fn new(spi: S) -> Self {
        Self { spi, layer: 0, dirty: true }
    }

    async fn on_layer_change_event(&mut self, event: LayerChangeEvent) {
        if self.layer != event.0 {
            self.layer = event.0;
            self.dirty = true;
        }
    }

    async fn poll(&mut self) {
        if !self.dirty {
            return;
        }
        let frame = encode_frame(layer_color(self.layer));
        match self.spi.write(&frame).and_then(|()| self.spi.flush()) {
            Ok(()) => self.dirty = false,
            Err(_) => {
                // Retry on the next poll; a failed write must not stop key scanning.
                esp_println::println!("RGB SPI write failed; retrying");
            }
        }
    }
}
