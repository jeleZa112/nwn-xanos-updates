# BG Voice RU 4.9.0: locally cached runtime bridge.
# This first release reuses the tested embedded 4.8 audio engine; it does not
# modify models, user decisions, generated WAVs or Baldur's Gate files.
from pathlib import Path
import sys
import json
import sqlite3
import zipfile


def main():
    launcher = Path(__file__).resolve()
    body = launcher.read_text(encoding='utf-8-sig').split('\n#BGVOICE_PYTHON_START\n', 1)[1]
    scope = {'__name__': 'bgvoice_embedded_runtime', '__file__': str(launcher)}
    exec(compile(body, str(launcher), 'exec'), scope)
    scope['VERSION'] = '4.9.0-offline'
    result = scope['main']()
    if result == 0 and '--self-test' not in sys.argv:
        report = launcher.parent / 'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
        db_path = launcher.parent / 'BG_VOICE_RU_PROGRESS.sqlite3'
        try:
            with sqlite3.connect(str(db_path), timeout=5) as db:
                row = db.execute('select last_result,last_checked from bgvoice_update_status where slot=1').fetchone()
            meta = {'runtime':'4.9.0-offline',
                    'last_update_check':row[1] if row else None,
                    'update_result':row[0] if row else 'none',
                    'audio_network_calls':0,
                    'source_wavs_modified':False}
            if report.is_file():
                with zipfile.ZipFile(report, 'a', zipfile.ZIP_DEFLATED) as z:
                    if 'AUTO_UPDATE_STATUS.json' not in z.namelist():
                        z.writestr('AUTO_UPDATE_STATUS.json', json.dumps(meta, ensure_ascii=False, indent=2))
        except (OSError, sqlite3.Error, zipfile.BadZipFile) as err:
            print('AUTO UPDATE INFO: could not append diagnostic:',repr(err))
    return result


if __name__ == '__main__':
    sys.exit(main())
