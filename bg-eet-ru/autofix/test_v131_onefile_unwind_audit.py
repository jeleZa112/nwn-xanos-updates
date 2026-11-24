"""V131 onefile E2E: exact module download, dataclass exec, cache, one ZIP.

Never access/modify user's game. This uses a temporary fake Baldur.exe that
MUST be rejected by exact SHA, and checks that the result is still recorded.
"""
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main,mock
import zipfile

UPDATER=Path(__file__).resolve().parents[1]/"onefile"/"BG_EET_RU_UPDATE.cmd"
MODULE=Path(__file__).resolve().parents[1]/"native-correlation"/"pe_unwind_entry_gate_v130.py"

class Onefile(TestCase):
    def test_source_pin_complete_download_dataclass_and_one_zip(self):
        source=UPDATER.read_text("utf8")
        self.assertIn("SELF_VERSION = 131",source)
        self.assertIn("if a=='6':return v130_audit(",source)
        self.assertIn("sys.modules[mod.__name__]=mod",source)
        self.assertIn("r.read(12001)",source)
        ns={"__name__":"v131_ci_fixture","__file__":str(UPDATER)}
        exec(compile(source.split("\n",1)[1],str(UPDATER),"exec"),ns)
        original=MODULE.read_bytes().replace(b"\r\n",b"\n")
        self.assertGreater(len(original),9000)
        self.assertLess(len(original),12001)
        self.assertEqual(ns["digest"](original),ns["V130_PIN"])
        with TemporaryDirectory(prefix="V131_PE_RO_") as d:
            root=Path(d)
            game=root/"game";game.mkdir()
            exe=game/"Baldur.exe"
            exe.write_bytes(b"MZ"+b"X"*600)
            ns["WORKDIR"]=root/"reports"
            ns["WORKDIR"].mkdir()
            result_zip=ns["WORKDIR"]/"SEND_TO_CHATGPT_BG_EET_RU.zip"
            with zipfile.ZipFile(result_zip,"w") as z:z.writestr("00_PRIOR.txt",b"still here")
            def fetch(url,timeout=0):
                self.assertEqual(url,ns["V130_URL"])
                self.assertEqual(timeout,20)
                return io.BytesIO(original)
            with mock.patch.object(ns["urllib"].request,"urlopen",side_effect=fetch) as net:
                status=ns["v130_audit"](game,result_zip)
            self.assertEqual(status,0)
            self.assertEqual(net.call_count,1)
            cached=ns["WORKDIR"]/".BG_EET_RU_AUTOFIX_CACHE"/"V130_RO.py"
            self.assertEqual(cached.read_bytes(),original)
            with zipfile.ZipFile(result_zip) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.read("00_PRIOR.txt"),b"still here")
                self.assertEqual(z.namelist().count("64_V130_PE_UNWIND.json"),1)
                report=json.loads(z.read("64_V130_PE_UNWIND.json"))
                self.assertEqual(report["status"],"SOURCE_OR_GAME_HOLD")
                self.assertEqual(report["game_files_written"],0)
                self.assertFalse(report["native_hook_install_allowed"])
                self.assertIn("EXACT_GAME_EXE_SHA_MISMATCH",report["hold_reason"])
            with mock.patch.object(ns["urllib"].request,"urlopen",side_effect=AssertionError("offline cache hit only")):
                self.assertEqual(ns["v130_audit"](game,result_zip),0)
            self.assertEqual(exe.read_bytes(),b"MZ"+b"X"*600)

    def test_tampered_source_cannot_execute(self):
        source=UPDATER.read_text("utf8")
        ns={"__name__":"v131_ci_fixture","__file__":str(UPDATER)}
        exec(compile(source.split("\n",1)[1],str(UPDATER),"exec"),ns)
        with TemporaryDirectory(prefix="V131_PE_BADSHA_") as d:
            root=Path(d);game=root/"game";game.mkdir()
            (game/"Baldur.exe").write_bytes(b"MZFAKE")
            ns["WORKDIR"]=root/"out";ns["WORKDIR"].mkdir()
            path=ns["WORKDIR"]/"SEND_TO_CHATGPT_BG_EET_RU.zip"
            with zipfile.ZipFile(path,"w") as z:z.writestr("original",b"x")
            with mock.patch.object(ns["urllib"].request,"urlopen",return_value=io.BytesIO(b"tampered")):
                self.assertEqual(ns["v130_audit"](game,path),0)
            with zipfile.ZipFile(path) as z:
                r=json.loads(z.read("64_V130_PE_UNWIND.json"))
            self.assertIn("V130_SOURCE_SHA_HOLD",r["hold_reason"])
            self.assertFalse(r["native_hook_install_allowed"])
            self.assertEqual(list(game.iterdir()),[game/"Baldur.exe"])

if __name__=="__main__":
    main()
