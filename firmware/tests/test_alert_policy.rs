#[path = "../rmk_macropad/src/alert_policy.rs"]
mod alert_policy;
use alert_policy::{AlertKind, AlertSource, AlertState, Command, LineBuffer, pulse_color};

#[test]
fn protocol_validates_version_kind_ttl_and_fields() {
    let legacy = Command::parse(b"MP1 A 5").unwrap();
    assert_eq!((legacy.kind, legacy.ttl_s, legacy.source), (AlertKind::Approval, 5, AlertSource::Claude));
    assert!(Command::parse(b"MP1 Q 600\r").is_some());
    assert!(Command::parse(b"MP1 C 0").is_some());
    assert_eq!(Command::parse(b"MP1 A 5").unwrap().acknowledgement(), b"MP1 OK A\n");
    assert_eq!(Command::parse(b"MP1 Q 5").unwrap().acknowledgement(), b"MP1 OK Q\n");
    assert_eq!(Command::parse(b"MP1 C 0").unwrap().acknowledgement(), b"MP1 OK C\n");
    for invalid in [b"MP2 A 5".as_slice(), b"MP1 X 5", b"MP1 A 0", b"MP1 A 601", b"MP1 A -1", b"MP1 C 5", b"MP1 A 5 extra", b"\xff"] {
        assert_eq!(Command::parse(invalid), None);
    }
}

#[test]
fn protocol_distinguishes_sources_and_preserves_legacy() {
    for (wire, source, ack) in [
        (b"MP2 CLAUDE A 5".as_slice(), AlertSource::Claude, b"MP2 OK CLAUDE A\n".as_slice()),
        (b"MP2 CODEX Q 5", AlertSource::Codex, b"MP2 OK CODEX Q\n"),
        (b"MP2 BOTH A 5", AlertSource::Both, b"MP2 OK BOTH A\n"),
        (b"MP2 NONE C 0", AlertSource::None, b"MP2 OK NONE C\n"),
    ] {
        let command = Command::parse(wire).unwrap();
        assert_eq!(command.source, source);
        assert_eq!(command.acknowledgement(), ack);
        let mut state = AlertState::new();
        state.apply(command, 100);
        assert_eq!(state.source(101), source);
        assert_eq!(state.source(5100), AlertSource::None);
    }
    for wire in [b"MP2 OTHER Q 5".as_slice(), b"MP2 NONE A 5", b"MP2 CLAUDE C 0", b"MP2 CODEX Q 601"] {
        assert_eq!(Command::parse(wire), None);
    }
}

#[test]
fn clear_expiry_and_heartbeat_are_ram_only() {
    let mut state = AlertState::new();
    let alert = Command::parse(b"MP1 A 5").unwrap();
    assert_eq!(state.current(0), AlertKind::None);
    state.apply(alert, 100);
    assert_eq!(state.current(5099), AlertKind::Approval);
    assert_eq!(state.current(5100), AlertKind::None);
    state.apply(alert, 6000);
    state.apply(alert, 9000);
    assert_eq!(state.current(13000), AlertKind::Approval);
    state.apply(Command::parse(b"MP1 C 0").unwrap(), 13001);
    assert_eq!(state.current(13001), AlertKind::None);
}

#[test]
fn stream_handles_fragmentation_multiple_lines_and_overflow() {
    let mut lines = LineBuffer::default();
    for b in b"MP1 A " { assert_eq!(lines.push(*b), None); }
    assert_eq!(lines.push(b'5'), None);
    assert_eq!(lines.push(b'\n'), Command::parse(b"MP1 A 5"));
    for _ in 0..100 { assert_eq!(lines.push(b'x'), None); }
    assert_eq!(lines.push(b'\n'), None);
    for b in b"MP1 C 0" { assert_eq!(lines.push(*b), None); }
    assert_eq!(lines.push(b'\n'), Command::parse(b"MP1 C 0"));
}

#[test]
fn pulse_is_dim_smooth_periodic_and_distinct() {
    assert_eq!(pulse_color(AlertKind::None, 0), None);
    assert_ne!(pulse_color(AlertKind::Approval, 1000), pulse_color(AlertKind::Question, 1000));
    let mut previous = pulse_color(AlertKind::Question, 0).unwrap()[0];
    for now in (50..=4000).step_by(50) {
        let color = pulse_color(AlertKind::Question, now).unwrap();
        assert!(color.iter().all(|c| *c <= 20));
        assert!(color[0].abs_diff(previous) <= 1);
        previous = color[0];
    }
    assert_eq!(pulse_color(AlertKind::Approval, 0), pulse_color(AlertKind::Approval, 2000));
}
