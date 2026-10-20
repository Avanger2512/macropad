use embassy_usb::{Builder, class::hid::{Config, HidBootProtocol, HidReaderWriter, HidSubclass, State}, driver::Driver};
use static_cell::StaticCell;
use crate::alert_policy::LineBuffer;

// Separate vendor page: Vial uses FF60; alerts use FF61, usage 61.
const DESCRIPTOR: &[u8] = &[
    0x06, 0x61, 0xff, 0x09, 0x61, 0xa1, 0x01,
    0x15, 0x00, 0x26, 0xff, 0x00, 0x75, 0x08, 0x95, 0x20,
    0x09, 0x62, 0x81, 0x02, 0x95, 0x20, 0x09, 0x63, 0x91, 0x02, 0xc0,
];

pub fn new<D: Driver<'static>>(builder: &mut Builder<'static, D>) -> HidReaderWriter<'static, D, 32, 32> {
    static STATE: StaticCell<State<'static>> = StaticCell::new();
    HidReaderWriter::new(builder, STATE.init(State::new()), Config {
        report_descriptor: DESCRIPTOR,
        request_handler: None,
        poll_ms: 10,
        max_packet_size: 32,
        hid_subclass: HidSubclass::No,
        hid_boot_protocol: HidBootProtocol::None,
    })
}

pub async fn run<D: Driver<'static>>(mut hid: HidReaderWriter<'static, D, 32, 32>) {
    loop {
        hid.ready().await;
        let mut packet = [0; 32];
        loop {
            let Ok(count) = hid.read(&mut packet).await else { break; };
            let mut lines = LineBuffer::default();
            for byte in &packet[..count] {
                if *byte == 0 { break; }
                if let Some(command) = lines.push(*byte) {
                    crate::alerts::apply(command);
                    let mut reply = [0; 32];
                    let ack = command.acknowledgement();
                    reply[..ack.len()].copy_from_slice(ack);
                    // An absent/blocked reader cannot stall keyboard tasks or this loop forever.
                    let _ = embassy_time::with_timeout(
                        embassy_time::Duration::from_millis(100),
                        hid.write(&reply),
                    ).await;
                }
            }
        }
    }
}
