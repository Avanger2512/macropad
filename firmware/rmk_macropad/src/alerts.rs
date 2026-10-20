use core::cell::RefCell;
use critical_section::Mutex;
use crate::alert_policy::{AlertKind, AlertSource, AlertState, Command};

static STATE: Mutex<RefCell<AlertState>> = Mutex::new(RefCell::new(AlertState::new()));

pub fn apply(command: Command) {
    let now = embassy_time::Instant::now().as_millis();
    critical_section::with(|cs| STATE.borrow(cs).borrow_mut().apply(command, now));
}

pub fn current(now_ms: u64) -> AlertKind {
    critical_section::with(|cs| STATE.borrow(cs).borrow().current(now_ms))
}

pub fn snapshot(now_ms: u64) -> (AlertSource, AlertKind) {
    critical_section::with(|cs| {
        let state = STATE.borrow(cs).borrow();
        (state.source(now_ms), state.current(now_ms))
    })
}
