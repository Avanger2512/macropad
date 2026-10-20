"""Place V8 shell and diffuser face-down and validate mesh topology/volume."""
import json
from pathlib import Path

from prepare_enclosure_v6_meshes import prepare

HERE = Path(__file__).parent


def main():
    report = json.loads((HERE / 'exports/service-v8-validation.json').read_text())
    result = []
    for source, output, body in (
            ('upper_shell_service_v8', 'UpperShell_Service_V8', 'UpperShell_Draft'),
            ('diffuser_service_v8', 'Diffuser_Service_V8', 'Diffuser_Draft')):
        result.append(prepare(HERE / 'exports' / (source + '_native.stl'),
                              HERE.parent / 'print' / (output + '.stl'),
                              175, report['volumes_mm3'][body]))
    (HERE / 'exports/service-v8-print-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
