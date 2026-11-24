"""V126 real source loader integration, not just string presence."""
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main, mock
from zipfile import ZipFile

UPDATER=Path(__file__).resolve().parents[1]/'onefile'/'BG_EET_RU_UPDATE.cmd'
MODULE=Path(__file__).resolve().parents[1]/'live-observer'/'visible_row_guarded_v1.py'

class SourceDispatch(TestCase):
    def test_pinned_module_loaded_full_with_valid_python_name_and_offline_cache(self):
        original=UPDATER.read_text('utf8')
        code=original.split('\n',1)[1]
        ns={'__name__':'ci_v126_onefile','__file__':str(UPDATER)}
        exec(compile(code,str(UPDATER),'exec'),ns)
        raw=MODULE.read_bytes().replace(b'\r\n',b'\n')  # checkout on Windows uses CRLF; pinned GitHub raw uses LF
        self.assertGreater(len(raw),15001)
        self.assertEqual(ns['digest'](raw),ns['V126_SHA'])
        self.assertIn('r.read(20001)',code)
        self.assertIn("ns={'__name__':'v126'}",code)
        with TemporaryDirectory(prefix='BG_EET_RU_V126_DISPATCH_') as td:
            root=Path(td)
            game=root/'game'
            override=game/'override'
            override.mkdir(parents=True)
            (game/'chitin.key').write_bytes(b'test')
            (override/'UI.MENU').write_bytes(b'UI.MENU TEST SHA IS NOT LIVE PIN')
            ns['WORKDIR']=root/'reports'
            ns['WORKDIR'].mkdir()
            report=ns['WORKDIR']/'SEND_TO_CHATGPT_BG_EET_RU.zip'
            with ZipFile(report,'w') as z:
                z.writestr('00_LEGACY.txt','preserve')
            def fetch(url,timeout):
                self.assertEqual(url,ns['V126_URL'])
                self.assertEqual(timeout,20)
                return io.BytesIO(raw)
            with mock.patch.object(ns['urllib'].request,'urlopen',side_effect=fetch) as urlopen:
                self.assertEqual(ns['v126_dispatch'](game,report,'status'),2)
                self.assertEqual(urlopen.call_count,1)
            staged=ns['WORKDIR']/'.BG_EET_RU_AUTOFIX_CACHE'/'V126.py'
            self.assertEqual(staged.read_bytes(),raw)
            with ZipFile(report) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.read('00_LEGACY.txt'),b'preserve')
                self.assertIn('63_V126_VISIBLE_ROW_OBSERVER.json',z.namelist())
                result=json.loads(z.read('63_V126_VISIBLE_ROW_OBSERVER.json'))
                self.assertEqual(result['status'],'V126_SAFE_STOP')
                self.assertEqual(result['game_files_written'],0)
            with mock.patch.object(ns['urllib'].request,'urlopen',side_effect=AssertionError('download not needed')):
                self.assertEqual(ns['v126_dispatch'](game,report,'status'),2)
            self.assertEqual((override/'UI.MENU').read_bytes(),b'UI.MENU TEST SHA IS NOT LIVE PIN')

if __name__=='__main__':
    main()
