"""V132 onefile end-to-end installed EEex source + raw unwind SHA gate.

Tests the actual single-CMD Python source via a temporary fake game.
Does not launch the game, install hooks or modify any game file.
"""
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main,mock
import zipfile

UPDATER=Path(__file__).resolve().parents[1]/"onefile"/"BG_EET_RU_UPDATE.cmd"
MODULE=Path(__file__).resolve().parents[1]/"native-correlation"/"v132_eeex_unwind_contract_ro.py"

class V132OneFile(TestCase):
    def test_exact_download_one_zip_and_offline_reuse(self):
        source=UPDATER.read_text("utf8")
        self.assertIn("SELF_VERSION = 132",source)
        self.assertIn("if a=='7':return v130_audit(game,WORKDIR/REPORT_NAME,132)",source)
        ns={"__name__":"v132_ci_fixture","__file__":str(UPDATER)}
        exec(compile(source.split("\n",1)[1],str(UPDATER),"exec"),ns)
        raw=MODULE.read_bytes().replace(b"\r\n",b"\n")
        self.assertGreater(len(raw),10000)
        self.assertLess(len(raw),14001)
        self.assertEqual(ns["digest"](raw),ns["V132_PIN"])
        with TemporaryDirectory(prefix="BG_EET_RU_V132_ONEFILE_") as d:
            root=Path(d);game=root/"game";game.mkdir()
            exe=game/"Baldur.exe"
            exe.write_bytes(b"MZ"+b"n"*1600)
            (game/"EEex_scripts").mkdir()
            asm=game/"EEex_scripts"/"EEex_Assembly_x86-64.lua"
            patterns=[
                "function EEex_HookBeforeRestoreWithLabels(",
                "function EEex_HookCallInternal(",
                "EEex_JITNear(","EEex_JITAt(",
                "function EEex_Assembly_Private_WriteAndRegisterFunctionTable(",
                "function EEex_Assembly_Private_PostJIT(",
                "EEex_RtlLookupFunctionEntry(",
                "EEex_RtlAddFunctionTable(","#MAKE_PROLOG",
                "EEex_HookIntegrityWatchdog_"]
            asm.write_text("\n".join(patterns)+"\n"+"-- synthetic fixture\n"*300,encoding="utf8")
            (game/"EEex_scripts"/"EEex_Sprite_Patch.lua").write_text("mock")
            (game/"InfinityLoader.db").write_bytes(b"Hook-CGameSprite::Hit()-FirstCall")
            game_files={str(p.relative_to(game)):p.read_bytes() for p in game.rglob("*") if p.is_file()}
            ns["WORKDIR"]=root/"reports";ns["WORKDIR"].mkdir()
            archive=ns["WORKDIR"]/"SEND_TO_CHATGPT_BG_EET_RU.zip"
            with zipfile.ZipFile(archive,"w") as z:z.writestr("00_PRIOR.txt",b"original preserved")
            def fetch(url,timeout=0):
                self.assertEqual(url,ns["V132_URL"])
                self.assertEqual(timeout,20)
                return io.BytesIO(raw)
            with mock.patch.object(ns["urllib"].request,"urlopen",side_effect=fetch) as internet:
                rc=ns["v130_audit"](game,archive,132)
            self.assertEqual(rc,0)
            self.assertEqual(internet.call_count,1)
            cache=ns["WORKDIR"]/".BG_EET_RU_AUTOFIX_CACHE"/"V132_RO.py"
            self.assertEqual(cache.read_bytes(),raw)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.read("00_PRIOR.txt"),b"original preserved")
                self.assertEqual(z.namelist().count("65_V132_EEEX_ABI.json"),1)
                report=json.loads(z.read("65_V132_EEEX_ABI.json"))
                self.assertEqual(report["status"],"STATIC_SOURCE_OR_RAW_XDATA_HOLD")
                self.assertTrue(report["eeex_x64"]["all_required_symbols_present"])
                self.assertIn("BALDUR_EXE_SHA_DRIFT_HOLD",report["unwind"]["reason"])
                self.assertTrue(report["firstcall_label_present_in_db"])
                self.assertFalse(report["eeex_existing_firstcall_owner_verified"])
                self.assertFalse(report["native_hook_install_allowed"])
                self.assertEqual(report["game_files_written"],0)
            with mock.patch.object(ns["urllib"].request,"urlopen",side_effect=AssertionError("must use pinned cache")):
                self.assertEqual(ns["v130_audit"](game,archive,132),0)
            self.assertEqual(game_files,{str(p.relative_to(game)):p.read_bytes() for p in game.rglob("*") if p.is_file()})

    def test_malicious_module_sha_never_executes(self):
        text=UPDATER.read_text("utf8")
        ns={"__name__":"v132_ci_fixture","__file__":str(UPDATER)}
        exec(compile(text.split("\n",1)[1],str(UPDATER),"exec"),ns)
        with TemporaryDirectory(prefix="V132_BAD_SOURCE_") as tmp:
            root=Path(tmp);game=root/"game";game.mkdir()
            (game/"Baldur.exe").write_bytes(b"MZ"+b"n"*1600)
            ns["WORKDIR"]=root/"reports";ns["WORKDIR"].mkdir()
            archive=ns["WORKDIR"]/"SEND_TO_CHATGPT_BG_EET_RU.zip"
            with zipfile.ZipFile(archive,"w") as z:z.writestr("ORIGINAL",b"one")
            with mock.patch.object(ns["urllib"].request,"urlopen",return_value=io.BytesIO(b"tampered")):
                self.assertEqual(ns["v130_audit"](game,archive,132),0)
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(z.read("ORIGINAL"),b"one")
                out=json.loads(z.read("65_V132_EEEX_ABI.json"))
                self.assertIn("V130_SOURCE_SHA_HOLD",out["hold_reason"])
                self.assertFalse(out["native_hook_install_allowed"])
                self.assertEqual(out["game_files_written"],0)
            self.assertEqual(list(game.iterdir()),[game/"Baldur.exe"])

if __name__=="__main__":main()
