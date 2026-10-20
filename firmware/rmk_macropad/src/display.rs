use embedded_graphics::{
    mono_font::{ascii::FONT_6X10, MonoTextStyle},
    pixelcolor::BinaryColor,
    prelude::*,
    primitives::{PrimitiveStyle, Rectangle},
    text::Text,
};
use rmk::display::{DisplayRenderer, RenderContext};

use crate::display_policy::{Activity, blink};

#[derive(Default)]
pub struct MacropadRenderer {
    activity: Activity,
}

impl DisplayRenderer<BinaryColor> for MacropadRenderer {
    fn render<D: DrawTarget<Color = BinaryColor>>(&mut self, ctx: &RenderContext, display: &mut D) {
        let now = embassy_time::Instant::now().as_millis();
        let active = self.activity.update(now, ctx.key_press_latch, ctx.key_pressed, ctx.sleeping);
        if draw_screen(display, ctx.layer, active, blink(now, active), ctx.sleeping).is_err() {
            esp_println::println!("OLED drawing failed");
        }
    }
}

fn draw_screen<D: DrawTarget<Color = BinaryColor>>(
    display: &mut D,
    layer: u8,
    active: bool,
    blinking: bool,
    sleeping: bool,
) -> Result<(), D::Error> {
    display.clear(BinaryColor::Off)?;
    if sleeping {
        return Ok(());
    }
    let text = MonoTextStyle::new(&FONT_6X10, BinaryColor::On);
    let title = match layer {
        0 => "L0 BASE",
        1 => "L1 WORK",
        2 => "L2 CAD",
        3 => "L3 MEDIA",
        _ => "L? OTHER",
    };
    Text::new("MACROPAD", Point::new(0, 9), text).draw(display)?;
    Text::new(title, Point::new(74, 9), text).draw(display)?;
    let outline = PrimitiveStyle::with_stroke(BinaryColor::On, 1);
    let fill = PrimitiveStyle::with_fill(BinaryColor::On);
    Rectangle::new(Point::new(8, 18), Size::new(54, 33))
        .into_styled(outline).draw(display)?;
    let eye_height = if blinking { 2 } else if active { 12 } else { 8 };
    let eye_y = 27 - (eye_height as i32 - 8) / 2;
    for x in [19, 42] {
        Rectangle::new(Point::new(x, eye_y), Size::new(9, eye_height))
            .into_styled(fill).draw(display)?;
    }
    Rectangle::new(Point::new(29, 42), Size::new(12, 2))
        .into_styled(fill).draw(display)?;
    Text::new(if active { "INPUT" } else { "READY" }, Point::new(80, 36), text)
        .draw(display)?;
    Rectangle::new(Point::new(0, 59), Size::new(128, 5))
        .into_styled(outline).draw(display)?;
    if active {
        Rectangle::new(Point::new(2, 61), Size::new(124, 1))
            .into_styled(fill).draw(display)?;
    }
    Ok(())
}
