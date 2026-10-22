//! Low-brightness layer colors and WS2812 SPI framing, independent of hardware.
pub const PIXELS: usize = 4;
pub const LATCH_BYTES: usize = 90;
pub const FRAME_BYTES: usize = LATCH_BYTES * 2 + PIXELS * 9;

/// The onboard WS2812 is blue only, and explicitly black when idle.
pub fn status_color(on: bool) -> [u8; 3] {
    if on { [0, 0, 20] } else { [0; 3] }
}

/// At 2.4 MHz each WS2812 bit is three SPI bits: zero=100, one=110.
/// Leading/trailing zeros provide 300 us reset periods and force MOSI low.
pub fn encode_frame(rgb: [u8; 3]) -> [u8; FRAME_BYTES] {
    let mut frame = [0; FRAME_BYTES];
    let grb = [rgb[1], rgb[0], rgb[2]];
    for pixel in 0..PIXELS {
        for (channel, value) in grb.iter().enumerate() {
            let mut encoded = 0u32;
            for bit in (0..8).rev() {
                let symbol = if value & (1 << bit) == 0 { 0b100 } else { 0b110 };
                encoded = (encoded << 3) | symbol;
            }
            let offset = LATCH_BYTES + pixel * 9 + channel * 3;
            frame[offset..offset + 3].copy_from_slice(&encoded.to_be_bytes()[1..]);
        }
    }
    frame
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn status_is_blue_only_and_idle_is_black() {
        assert_eq!(status_color(false), [0; 3]);
        assert_eq!(status_color(true), [0, 0, 20]);
        let frame = encode_frame(status_color(true));
        // GRB stream: the G and R channels must both encode zero, B nonzero.
        assert_eq!(&frame[LATCH_BYTES..LATCH_BYTES + 6],
                   &[0x92, 0x49, 0x24, 0x92, 0x49, 0x24]);
        assert_ne!(&frame[LATCH_BYTES + 6..LATCH_BYTES + 9], &[0x92, 0x49, 0x24]);
    }

    #[test]
    fn frame_is_grb_msb_first_and_all_four_pixels_match() {
        let frame = encode_frame([0x80, 0, 0xff]);
        let pixel = [0x92, 0x49, 0x24, 0xd2, 0x49, 0x24, 0xdb, 0x6d, 0xb6];
        for index in 0..PIXELS {
            assert_eq!(&frame[LATCH_BYTES + index * 9..LATCH_BYTES + (index + 1) * 9], &pixel);
        }
        assert!(frame[..LATCH_BYTES].iter().all(|byte| *byte == 0));
        assert!(frame[FRAME_BYTES - LATCH_BYTES..].iter().all(|byte| *byte == 0));
    }
}
