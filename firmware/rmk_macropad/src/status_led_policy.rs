use crate::alert_policy::AlertKind;

/// Timing only: `true` means illuminated, independently of hardware polarity.
#[derive(Clone, Copy, Debug, Default)]
pub struct StatusLedPolicy {
    layer: Option<u8>,
    sequence: Option<(u64, u8)>,
    alert_since: Option<u64>,
    pending_layer: bool,
    key_until: u64,
}

impl StatusLedPolicy {
    pub const fn new() -> Self {
        Self { layer: None, sequence: None, alert_since: None, pending_layer: false, key_until: 0 }
    }

    /// First observation establishes startup state without flashing.
    pub fn layer_changed(self, layer: u8, now_ms: u64) -> Self {
        if self.layer == Some(layer) { return self; }
        if self.layer.is_none() {
            return Self { layer: Some(layer), ..self };
        }
        let valid = layer < 4;
        Self {
            layer: Some(layer),
            sequence: if valid { Some((now_ms, layer + 1)) } else { None },
            pending_layer: valid && self.alert_since.is_some(),
            key_until: 0,
            ..self
        }
    }

    /// Ignore input feedback during higher-priority attention/layer sequences.
    pub fn key_pressed(self, now_ms: u64) -> Self {
        let sequence_active = self.sequence.is_some_and(|(start, count)| {
            now_ms.saturating_sub(start) < u64::from(count) * 400
        });
        if self.alert_since.is_some() || sequence_active { return self; }
        Self { key_until: now_ms.saturating_add(100), ..self }
    }

    pub fn input_active(self, now_ms: u64) -> bool {
        self.alert_since.is_none() && now_ms < self.key_until
    }

    pub fn update(self, alert: AlertKind, now_ms: u64) -> (Self, bool) {
        if alert != AlertKind::None {
            let since = self.alert_since.unwrap_or(now_ms);
            let sequence_active = self.sequence.map_or(false, |(start, count)| {
                now_ms.saturating_sub(start) < u64::from(count) * 400
            });
            let next = Self {
                alert_since: Some(since),
                key_until: 0,
                pending_layer: self.pending_layer || sequence_active,
                ..self
            };
            return (next, now_ms.saturating_sub(since) % 600 < 250);
        }
        let sequence = if self.alert_since.is_some() && self.pending_layer {
            self.layer.filter(|layer| *layer < 4).map(|layer| (now_ms, layer + 1))
        } else { self.sequence };
        let next = Self { sequence, alert_since: None, pending_layer: false, ..self };
        if let Some((start, count)) = sequence {
            let elapsed = now_ms.saturating_sub(start);
            if elapsed < u64::from(count) * 400 {
                return (next, elapsed % 400 < 150);
            }
        }
        (Self { sequence: None, ..next }, now_ms < next.key_until)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn baseline() -> StatusLedPolicy { StatusLedPolicy::new().layer_changed(0, 0) }

    #[test]
    fn key_press_pulses_expire_and_retrigger() {
        let state = baseline().key_pressed(10);
        assert!(state.update(AlertKind::None, 10).1);
        assert!(state.update(AlertKind::None, 109).1);
        assert!(!state.update(AlertKind::None, 110).1);
        assert!(state.key_pressed(90).update(AlertKind::None, 150).1);
    }

    #[test]
    fn keys_do_not_fill_alert_or_layer_dark_intervals() {
        let (state, _) = baseline().update(AlertKind::Question, 0);
        assert!(!state.key_pressed(300).update(AlertKind::Question, 300).1);
        let state = baseline().layer_changed(1, 0).key_pressed(200);
        assert!(!state.update(AlertKind::None, 200).1);
        assert!(!state.update(AlertKind::None, 800).1);
    }

    #[test]
    fn startup_and_idle_are_dark() {
        assert!(!StatusLedPolicy::new().update(AlertKind::None, 0).1);
        assert!(!StatusLedPolicy::new().layer_changed(2, 0).update(AlertKind::None, 50).1);
        assert!(!baseline().update(AlertKind::None, 1_000).1);
    }

    #[test]
    fn layer_pulses_have_exact_boundaries_and_finish() {
        for layer in 0..4 {
            let state = StatusLedPolicy::new().layer_changed(9, 0).layer_changed(layer, 100);
            for pulse in 0..=u64::from(layer) {
                let start = 100 + pulse * 400;
                assert!(state.update(AlertKind::None, start).1);
                assert!(state.update(AlertKind::None, start + 149).1);
                assert!(!state.update(AlertKind::None, start + 150).1);
                assert!(!state.update(AlertKind::None, start + 399).1);
            }
            assert!(!state.update(AlertKind::None, 100 + (u64::from(layer) + 1) * 400).1);
        }
    }

    #[test]
    fn repeated_layer_does_not_restart_and_unknown_cancels() {
        let state = baseline().layer_changed(1, 100).layer_changed(1, 250);
        assert!(!state.update(AlertKind::None, 250).1);
        assert!(!state.layer_changed(99, 251).update(AlertKind::None, 251).1);
    }

    #[test]
    fn alerts_override_layers_without_heartbeat_phase_reset() {
        let (state, on) = baseline().layer_changed(1, 0).update(AlertKind::Question, 100);
        assert!(on);
        let (state, on) = state.update(AlertKind::Question, 350);
        assert!(!on);
        let (state, on) = state.update(AlertKind::Approval, 700);
        assert!(on);
        assert!(!state.update(AlertKind::Approval, 950).1);
    }

    #[test]
    fn alert_clear_restarts_latest_pending_layer_once() {
        let (state, _) = baseline().layer_changed(1, 50).update(AlertKind::Question, 100);
        let state = state.layer_changed(3, 200).layer_changed(2, 300);
        let (state, on) = state.update(AlertKind::None, 2_000);
        assert!(on);
        assert!(state.update(AlertKind::None, 2_800).1);
        let (state, on) = state.update(AlertKind::None, 3_200);
        assert!(!on);
        assert!(!state.update(AlertKind::None, 4_000).1);
    }

    #[test]
    fn a_new_layer_replaces_the_previous_sequence() {
        let state = baseline().layer_changed(3, 0).layer_changed(0, 500);
        assert!(state.update(AlertKind::None, 500).1);
        assert!(!state.update(AlertKind::None, 900).1);
    }

    #[test]
    fn a_finished_sequence_is_not_replayed_after_an_alert() {
        let state = baseline().layer_changed(1, 0);
        let (state, _) = state.update(AlertKind::Question, 1_000);
        assert!(!state.update(AlertKind::None, 2_000).1);
    }

    #[test]
    fn alert_without_layer_event_returns_to_dark() {
        let (state, _) = baseline().update(AlertKind::Approval, 0);
        assert!(!state.update(AlertKind::None, 1_000).1);
    }
}
