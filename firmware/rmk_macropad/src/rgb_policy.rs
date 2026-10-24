//! Status colors and WS2812 SPI framing, independent of hardware.
use crate::alert_policy::AlertSource;

pub const PIXELS: usize = 4;
pub const LATCH_BYTES: usize = 90;
pub const FRAME_BYTES: usize = LATCH_BYTES * 2 + PIXELS * 9 + 1;

/// Layer feedback is blue; idle RGB output is black.
pub fn status_color(on: bool) -> [u8; 3] {
    if on { [0, 0, 64] } else { [0; 3] }
}

/// Attention uses source colors; BOTH alternates on a global 600ms cadence.
pub fn indicator_color(on: bool, key: bool, source: AlertSource, now_ms: u64) -> [u8; 3] {
    if !on { return [0; 3]; }
    let source = if source == AlertSource::Both {
        if (now_ms / 600) % 2 == 0 { AlertSource::Codex } else { AlertSource::Claude }
    } else { source };
    match source {
        AlertSource::Codex => [0, 64, 64],
        AlertSource::Claude => [64, 20, 0],
        _ if key => [0, 64, 0],
        _ => status_color(true),
    }
}

/// At 2.4 MHz each WS2812 bit is three SPI bits: zero=100, one=110.
/// Leading/trailing zeros provide 300 us resets, followed by one idle-high byte.
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
    // Experimental shared-line power indication: high AFTER the low reset.
    // The next frame begins with a complete low reset before any RGB data.
    frame[FRAME_BYTES - 1] = 0xff;
    frame
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn source_and_input_colors_are_distinct_and_idle_dark() {
        assert_eq!(indicator_color(true,false,AlertSource::Codex,0),[0,64,64]);
        assert_eq!(indicator_color(true,false,AlertSource::Claude,0),[64,20,0]);
        assert_ne!(indicator_color(true,false,AlertSource::Both,0),indicator_color(true,false,AlertSource::Both,600));
        assert_eq!(indicator_color(false,true,AlertSource::Both,600),[0;3]);
        assert_eq!(indicator_color(true,true,AlertSource::None,0),[0,64,0]);
        assert_eq!(indicator_color(true,false,AlertSource::None,0),[0,0,64]);
    }

    #[test]
    fn status_is_blue_only_and_idle_is_black() {
        assert_eq!(status_color(false), [0; 3]);
        assert_eq!(status_color(true), [0, 0, 64]);
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
        assert_eq!(frame[FRAME_BYTES - 1], 0xff);
        assert!(frame[..LATCH_BYTES].iter().all(|byte| *byte == 0));
        assert!(frame[FRAME_BYTES - LATCH_BYTES - 1..FRAME_BYTES - 1].iter().all(|byte| *byte == 0));
    }
}
