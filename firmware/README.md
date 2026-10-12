# Тест ESP32-S3 SuperMini — Arduino Framework

Откройте `macropad_test/macropad_test.ino` в Arduino IDE. Файл `InputLogic.h` должен оставаться рядом со скетчем. USB HID не используется; Serial работает через native USB CDC.

## Зависимости, зафиксированные для сборки

- Boards Manager: **esp32 by Espressif Systems 3.3.12**.
- Library Manager: **U8g2 by oliver 2.36.19**.
- Library Manager: **Adafruit NeoPixel by Adafruit 1.15.5**.
- `Wire`, `Arduino`, GPIO и прерывания входят в esp32 core.

Дополнительный URL Boards Manager:
`https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`

Версии проверены по официальным каталогам Arduino. U8g2 2.36.19 — опубликованная версия Library Manager; версия master репозитория может быть новее.

## Arduino IDE → Tools

| Параметр | Значение |
|---|---|
| Board | ESP32S3 Dev Module |
| USB Mode | Hardware CDC and JTAG |
| USB CDC On Boot | Enabled |
| USB DFU On Boot | Disabled |
| USB Firmware MSC On Boot | Disabled |
| Upload Mode | UART0 / Hardware CDC |
| CPU Frequency | 240MHz (WiFi) |
| Flash Mode | DIO 80MHz |
| Flash Size | 4MB (32Mb), предварительный профиль |
| Partition Scheme | Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS) |
| PSRAM | Disabled |
| Upload Speed | 460800 |
| Core Debug Level | None |
| Erase All Flash Before Sketch Upload | Disabled |
| Port | USB-порт подключённой платы |

Название SuperMini не определяет однозначно объём/тип памяти. Профиль 4MB без PSRAM подходит для тестовой сборки и платы с минимум 4MB flash; если у вашей ревизии другой объём, выберите его по маркировке/данным продавца. Прошивка не требует PSRAM. Компиляция не подтверждает параметры конкретного экземпляра.

## Подключения

| Устройство | GPIO / питание |
|---|---|
| SW1 / SW2 / SW3 / SW4 / SW5 / SW6 | 1 / 2 / 4 / 5 / 6 / 7 |
| Encoder CLK / DT / SW | 8 / 9 / 10 |
| SH1106 SDA / SCL | 11 / 12 |
| WS2812 DIN | 13 через 330 Ом |
| OLED и encoder VCC | 3.3V |
| WS2812 VCC | 5V |
| Все земли | Общий GND |

Каждый switch замыкает GPIO на GND; INPUT_PULLUP включён, нажатие = LOW. У голого энкодера общий контакт A/B подключается к GND; VCC относится к модулю энкодера. Дисплей настроен именно на SH1106 128×64, поиск адреса 0x3C и 0x3D.

## Настраиваемые константы

В начале скетча:

- `LED_COUNT = 4`: измените на фактическое число внешних WS2812. Все указанные светодиоды показывают одинаковый цвет. Автоматически определить их число нельзя.
- `LED_BRIGHTNESS = 32`: невысокая яркость для теста.
- `ENCODER_TRANSITIONS = 4`: если счётчик меняется раз в два щелчка, попробуйте 2.
- `ENCODER_DIRECTION = 1`: установите -1, если направление нужно поменять.
- `DEBOUNCE_MS = 20`: фильтр кнопок. Энкодер использует декодирование квадратуры, отменяющее обратные переходы при дребезге, вместо задержки на каждом фронте.

## Проверка после загрузки

1. Подключите USB-кабель с передачей данных. Если загрузка не начинается: удерживайте BOOT, нажмите и отпустите RESET, отпустите BOOT; выберите появившийся USB-порт и загрузите. После первой загрузки нажмите RESET при необходимости.
2. Откройте Serial Monitor на **115200**. События DOWN/UP и ENC печатаются при действиях, STATUS — каждые 2 секунды, даже если монитор открыли после запуска.
3. На OLED должны появиться шесть состояний кнопок (1 = нажата), положение/кнопка энкодера, A/B и последнее событие. Обновление 10 раз в секунду; краткие нажатия лучше отслеживать также через Serial.
4. Нажмите каждую кнопку: один DOWN, один UP; цвет соответственно красный, зелёный, синий, жёлтый, голубой, пурпурный. Нажатие encoder SW — белый. Последний цвет сохраняется после отпускания.
5. Поверните encoder в обе стороны: позиция увеличивается/уменьшается, цвет меняется по кругу оттенков. На старте все 4 WS2812 проходят красный, зелёный и синий цвет по 600 мс; затем остаётся синий. Опрос кнопок начинается после этого теста.
6. Отсутствующий OLED не блокирует кнопки и RGB: Serial сообщает `OLED missing`; поиск повторяется каждые 5 секунд. Наличие ACK подтверждает I2C-устройство по адресу, но не его модель и не работоспособность матрицы.

GPIO энкодера обслуживаются прерываниями, поэтому OLED-передачи не останавливают захват фронтов. События нескольких быстрых шагов могут объединяться в одну запись ENC с величиной изменения.

## Если RGB не реагирует

Проверьте DIN (не DOUT), общую землю, питание и число LED. У WS2812 при питании 5V сигнал 3.3V может не соответствовать гарантированному порогу HIGH. Для устойчивой работы используйте преобразователь уровня 74AHCT125/74HCT245 на 5V между GPIO13 и резистором 330 Ом. Сам резистор уровень не повышает. Рекомендуется конденсатор 500–1000 мкФ на питании ленты; для большого числа LED нужен подходящий источник 5V. Не подавайте 5V на GPIO ESP32.

## Источники

- https://github.com/espressif/arduino-esp32/releases/tag/3.3.12
- https://raw.githubusercontent.com/espressif/arduino-esp32/3.3.12/boards.txt
- https://docs.espressif.com/projects/arduino-esp32/en/latest/tutorials/cdc_dfu_flash.html
- https://github.com/olikraus/U8g2_Arduino/releases/tag/2.36.19
- https://github.com/olikraus/u8g2/wiki/u8g2setupcpp#sh1106-128x64_noname
- https://github.com/adafruit/Adafruit_NeoPixel/releases/tag/1.15.5
- https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices

## Повторяемые проверки

Нативные тесты логики доступны в `tests/test_inputs.cpp`. Из папки этого README:

```sh
clang++ -std=c++17 -Wall -Wextra -pedantic tests/test_inputs.cpp -o /tmp/macropad-input-tests
/tmp/macropad-input-tests
```

Сборка через Arduino CLI после установки указанных зависимостей:

```sh
arduino-cli compile --fqbn 'esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,UploadMode=default,FlashMode=dio,FlashSize=4M,PSRAM=disabled,PartitionScheme=default,CPUFreq=240,UploadSpeed=460800' macropad_test
```
