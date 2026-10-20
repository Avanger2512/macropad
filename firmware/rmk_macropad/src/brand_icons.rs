//! Official application marks, converted to 32×32 monochrome OLED bitmaps.
//! Packed row-major, MSB first; compatible with ImageRaw<BinaryColor>.

pub const CLAUDE: &[u8; 128] = include_bytes!("../assets/claude_32.raw");
pub const CODEX: &[u8; 128] = include_bytes!("../assets/codex_32.raw");
