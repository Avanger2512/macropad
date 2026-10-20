"""Migration checks for the physically verified board and Vial definition."""
import json
import csv
from pathlib import Path
import tomllib
import unittest

PROJECT = Path(__file__).resolve().parents[1] / 'rmk_macropad'


class BoardMigrationTests(unittest.TestCase):
    def setUp(self):
        self.config = tomllib.loads((PROJECT / 'keyboard.toml').read_text())
        self.vial = json.loads((PROJECT / 'vial.json').read_text())

    def test_confirmed_buttons_and_encoder_push(self):
        matrix = self.config['matrix']
        self.assertEqual(matrix['matrix_type'], 'direct_pin')
        self.assertTrue(matrix['direct_pin_low_active'])
        self.assertEqual(matrix['direct_pins'], [[
            'GPIO1', 'GPIO2', 'GPIO3', 'GPIO6', 'GPIO5', 'GPIO4', 'GPIO10']])

    def test_vial_covers_every_switch_and_both_encoder_directions(self):
        self.assertEqual(self.vial['matrix'], {'rows': 1, 'cols': 7})
        cells = [cell for row in self.vial['layouts']['keymap'] for cell in row
                 if isinstance(cell, str)]
        buttons = [cell for cell in cells if '\n' not in cell]
        rotations = [cell for cell in cells if cell.endswith('\ne')]
        self.assertCountEqual(buttons, [f'0,{i}' for i in range(7)])
        self.assertCountEqual(rotations, ['0,0' + '\n' * 9 + 'e',
                                          '0,1' + '\n' * 9 + 'e'])

    def test_encoder_pins_and_resolution(self):
        encoder, = self.config['input_device']['encoder']
        self.assertEqual((encoder['pin_a'], encoder['pin_b']), ('GPIO8', 'GPIO9'))
        self.assertTrue(encoder['internal_pullup'])
        self.assertEqual(encoder['resolution'], 4)
        self.assertTrue(encoder['reverse'])
        pins = self.config['matrix']['direct_pins'][0] + ['GPIO8', 'GPIO9']
        self.assertEqual(len(set(pins)), len(pins))
        self.assertTrue(set(pins).isdisjoint({'GPIO0', 'GPIO11', 'GPIO12',
                                             'GPIO13', 'GPIO19', 'GPIO20'}))

    def test_oled_uses_verified_bus_and_driver(self):
        display = self.config['display']
        self.assertEqual((display['driver'], display['size']), ('sh1106', '128x64'))
        self.assertEqual(display['protocol']['i2c'], {
            'instance': 'I2C0', 'sda': 'GPIO11', 'scl': 'GPIO12', 'address': 0x3C})

    def test_usb_identity_matches_vial(self):
        keyboard = self.config['keyboard']
        self.assertEqual(keyboard['chip'], 'esp32s3')
        self.assertTrue(keyboard['usb_enable'])
        self.assertFalse(self.config['ble']['enabled'])
        for name in ('vendor', 'product'):
            self.assertEqual(keyboard[f'{name}_id'], int(self.vial[f'{name}Id'], 16))

    def test_layers_have_encoder_actions(self):
        keymap = self.config['keymap']
        self.assertEqual(len(keymap['layer']), keymap['layers'])
        for layer in keymap['layer']:
            self.assertEqual(len(layer['keys'].split()), 7)
            self.assertEqual(len(layer['encoders']), 1)
            self.assertEqual(len(layer['encoders'][0]), 2)
        self.assertEqual(keymap['layer'][0]['encoders'][0],
                         ['AudioVolUp', 'AudioVolDown'])

    def test_persistence_and_physical_unlock(self):
        storage = self.config['storage']
        self.assertTrue(storage['enabled'])
        self.assertEqual(storage['start_addr'] % 4096, 0)
        self.assertEqual(storage['start_addr'] + storage['num_sectors'] * 4096,
                         4 * 1024 * 1024)
        self.assertGreaterEqual(storage['num_sectors'], 2)
        self.assertEqual(self.config['host']['unlock_keys'], [[0, 0], [0, 5]])
        self.assertFalse(self.config['host'].get('insecure', False))
        cargo = tomllib.loads((PROJECT / 'Cargo.toml').read_text())
        self.assertIn('host_lock', cargo['dependencies']['rmk']['features'])

    def test_flash_partitions_reserve_settings_and_runner_uses_them(self):
        rows = csv.reader(line for line in (PROJECT / 'partitions.csv').read_text().splitlines()
                          if line and not line.startswith('#'))
        partitions = {row[0]: (int(row[3], 0), int(row[4], 0)) for row in rows}
        app_start, app_size = partitions['factory']
        storage_start, storage_size = partitions['rmk']
        self.assertLessEqual(app_start + app_size, storage_start)
        self.assertEqual(storage_start, self.config['storage']['start_addr'])
        self.assertEqual(storage_size, self.config['storage']['num_sectors'] * 4096)
        cargo_config = tomllib.loads((PROJECT / '.cargo/config.toml').read_text())
        for target in cargo_config['target'].values():
            self.assertIn('--partition-table partitions.csv', target['runner'])


if __name__ == '__main__':
    unittest.main()
