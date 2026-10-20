#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum AlertKind {
    #[default]
    None,
    Approval,
    Question,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum AlertSource {
    #[default]
    None,
    Claude,
    Codex,
    Both,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Command {
    pub kind: AlertKind,
    pub ttl_s: u16,
    pub source: AlertSource,
    legacy: bool,
}

impl Command {
    pub fn parse(line: &[u8]) -> Option<Self> {
        let mut parts = core::str::from_utf8(line).ok()?.split_ascii_whitespace();
        let (source, legacy) = match parts.next()? {
            "MP1" => (AlertSource::Claude, true),
            "MP2" => (match parts.next()? {
                "CLAUDE" => AlertSource::Claude,
                "CODEX" => AlertSource::Codex,
                "BOTH" => AlertSource::Both,
                "NONE" => AlertSource::None,
                _ => return None,
            }, false),
            _ => return None,
        };
        let kind = match parts.next()? {
            "A" => AlertKind::Approval,
            "Q" => AlertKind::Question,
            "C" => AlertKind::None,
            _ => return None,
        };
        let ttl_s: u16 = parts.next()?.parse().ok()?;
        if parts.next().is_some()
            || (kind == AlertKind::None && ttl_s != 0)
            || (!legacy && ((kind == AlertKind::None) != (source == AlertSource::None)))
            || (kind != AlertKind::None && !(1..=600).contains(&ttl_s)) {
            return None;
        }
        Some(Self { kind, ttl_s, source, legacy })
    }

    pub fn acknowledgement(self) -> &'static [u8] {
        match (self.legacy, self.source, self.kind) {
            (true, _, AlertKind::None) => b"MP1 OK C\n",
            (true, _, AlertKind::Approval) => b"MP1 OK A\n",
            (true, _, AlertKind::Question) => b"MP1 OK Q\n",
            (false, AlertSource::Claude, AlertKind::Approval) => b"MP2 OK CLAUDE A\n",
            (false, AlertSource::Claude, AlertKind::Question) => b"MP2 OK CLAUDE Q\n",
            (false, AlertSource::Codex, AlertKind::Approval) => b"MP2 OK CODEX A\n",
            (false, AlertSource::Codex, AlertKind::Question) => b"MP2 OK CODEX Q\n",
            (false, AlertSource::Both, AlertKind::Approval) => b"MP2 OK BOTH A\n",
            (false, AlertSource::Both, AlertKind::Question) => b"MP2 OK BOTH Q\n",
            _ => b"MP2 OK NONE C\n",
        }
    }
}

#[derive(Default)]
pub struct AlertState {
    kind: AlertKind,
    source: AlertSource,
    expires_at_ms: u64,
}

impl AlertState {
    pub const fn new() -> Self {
        Self { kind: AlertKind::None, source: AlertSource::None, expires_at_ms: 0 }
    }

    pub fn apply(&mut self, command: Command, now_ms: u64) {
        self.kind = command.kind;
        self.source = command.source;
        self.expires_at_ms = now_ms.saturating_add(u64::from(command.ttl_s) * 1000);
    }

    pub fn current(&self, now_ms: u64) -> AlertKind {
        if now_ms < self.expires_at_ms { self.kind } else { AlertKind::None }
    }

    pub fn source(&self, now_ms: u64) -> AlertSource {
        if self.current(now_ms) == AlertKind::None { AlertSource::None } else { self.source }
    }
}

/// Fixed memory, newline framing; discard an oversized frame through its delimiter.
pub struct LineBuffer {
    bytes: [u8; 32],
    len: usize,
    overflow: bool,
}

impl Default for LineBuffer {
    fn default() -> Self { Self { bytes: [0; 32], len: 0, overflow: false } }
}

impl LineBuffer {
    pub fn push(&mut self, byte: u8) -> Option<Command> {
        if byte == b'\n' {
            let command = if self.overflow { None } else { Command::parse(&self.bytes[..self.len]) };
            self.len = 0;
            self.overflow = false;
            return command;
        }
        if self.len < self.bytes.len() && !self.overflow {
            self.bytes[self.len] = byte;
            self.len += 1;
        } else {
            self.overflow = true;
        }
        None
    }
}

pub fn pulse_color(kind: AlertKind, now_ms: u64) -> Option<[u8; 3]> {
    let phase = (now_ms % 2000) as u16;
    let ramp = if phase < 1000 { phase } else { 2000 - phase };
    let brightness = 1 + (ramp * 19 / 1000) as u8;
    match kind {
        AlertKind::None => None,
        AlertKind::Approval => Some([brightness, brightness / 4, 0]),
        AlertKind::Question => Some([brightness, brightness * 3 / 4, 0]),
    }
}
