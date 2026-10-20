/// Pure animation timing, independent of the keyboard event and USB paths.
#[derive(Default)]
pub struct Activity {
    last_input_ms: Option<u64>,
}

impl Activity {
    pub fn update(&mut self, now_ms: u64, pressed: bool, held: bool, sleeping: bool) -> bool {
        if sleeping {
            self.last_input_ms = None;
            return false;
        }
        if pressed || held {
            self.last_input_ms = Some(now_ms);
        }
        self.last_input_ms
            .is_some_and(|last| now_ms.saturating_sub(last) < 400)
    }
}

pub fn blink(now_ms: u64, active: bool) -> bool {
    !active && now_ms % 4000 >= 3800
}
