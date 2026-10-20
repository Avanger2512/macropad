#[path = "../rmk_macropad/src/display_policy.rs"]
mod display_policy;

use display_policy::Activity;

#[test]
fn short_press_stays_visible_then_expires() {
    let mut activity = Activity::default();
    assert!(!activity.update(0, false, false, false));
    assert!(activity.update(100, true, false, false));
    assert!(activity.update(499, false, false, false));
    assert!(!activity.update(500, false, false, false));
}

#[test]
fn held_and_repeated_presses_extend_feedback() {
    let mut activity = Activity::default();
    assert!(activity.update(0, true, false, false));
    assert!(activity.update(300, true, false, false));
    assert!(activity.update(699, false, false, false));
    assert!(!activity.update(700, false, false, false));
    assert!(activity.update(2000, false, true, false));
    assert!(activity.update(5000, false, true, false));
    assert!(!activity.update(5400, false, false, false));
}

#[test]
fn sleep_clears_activity_and_idle_blinks_are_brief() {
    let mut activity = Activity::default();
    assert!(activity.update(100, true, false, false));
    assert!(!activity.update(101, false, false, true));
    assert!(!activity.update(102, false, false, false));
    assert!(!display_policy::blink(0, false));
    assert!(display_policy::blink(3800, false));
    assert!(display_policy::blink(3999, false));
    assert!(!display_policy::blink(4000, false));
    assert!(!display_policy::blink(3900, true));
}
