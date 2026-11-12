"""Synthetic BCS + mocked WeiDU integration. Never touches an actual EET game."""
from __future__ import annotations
import tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch as monkey
from hashlib import sha256
import BGXAI66S_INSTALL as m
import BGXAI66S_BCS_PATCH as b
import BGXAI64_INSTALL_SOURCE_ONLY as old

def block(i,acts,marker=b''):
    raw=b'CR\nCO\n'+b'FAKE_BLOCK_'+str(i).encode()+marker+b'\nRS\nRP\n100\n'
    for act in acts:
        raw+=b'AC\n'+str(act).encode()+b'OB\nOB\nAC\n'
    return raw+b'RS\nCR\n'

def base_bcs():
    chunks=[block(i,[0]) for i in range(1065)]
    acts=[[30,36],[30,36]]+[[30,115,87] for _ in range(6)]
    for i,aa in enumerate(acts):
        chunks[1031+i]=block(1031+i,aa,b'LOCALSBGX52_REQ_SLOT')
    chunks[-1]+=b'SC\n'
    return b'SC\n'+b''.join(chunks)

def fragment():
    acts=[[30,36] for _ in range(4)]+[[30,115,31] for _ in range(7)]
    chunks=[block(i,aa,b'LOCALSBGX66_S_X') for i,aa in enumerate(acts)]
    chunks[-1]+=b'SC\n'
    return b'SC\n'+b''.join(chunks)

def put(root,rel,data):
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

class FakeWeidu:
    def __init__(self,fail=False):self.calls=[];self.fail=fail
    def __call__(self,cmd,*,cwd,**kwargs):
        game=Path(cwd)
        install='--force-install' in cmd
        self.calls.append('install' if install else 'rollback')
        if self.fail:return subprocess.CompletedProcess(cmd,1,'FAIL','ERROR: MOCK STOP')
        log=game/'WeiDU.log'
        if install:
            put(game,m.LUA,(game/m.STAGE_LUA).read_bytes())
            put(game,m.BCS,(game/m.STAGE_BCS).read_bytes())
            with log.open('ab') as f:f.write(b'~BGX66S\\SETUP-BGX66S.TP2~ #0 #0\n')
        else:
            put(game,m.LUA,old.source_check())
            put(game,m.BCS,self.baseline)
            log.write_bytes(b'~BGX64\\SETUP-BGX64.TP2~ #0 #0\n')
        return subprocess.CompletedProcess(cmd,0,'MOCK_WEIDU_OK','')

class Guarded066S(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='bg66s_model_');self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)/'game';self.root.mkdir()
        self.backups=Path(temp.name)/'external'
        self.oldbcs=base_bcs();self.frag=fragment();self.mock=FakeWeidu()
        self.mock.baseline=self.oldbcs
        put(self.root,'WeiDU.log',b'~BGX64\\SETUP-BGX64.TP2~ #0 #0\n')
        for x in ('chitin.key','weidu.conf','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk'):
            put(self.root,x,b'DUMMY:'+x.encode())
        put(self.root,m.BCS,self.oldbcs)
        put(self.root,m.LUA,(m.SOURCE/'M_BX43_064_CANDIDATE.lua').read_bytes())
        put(self.root,old.STAGED_LUA,(m.SOURCE/'M_BX43_064_CANDIDATE.lua').read_bytes())
        put(self.root,old.TP2,old.TP2_TEXT.encode())
        put(self.root,old.EXE,b'MZ'+b'X'*100_001)
        put(self.root,m.WEIDU,b'MZ'+b'Y'*100_001)
        bcs_sha=sha256(self.oldbcs).hexdigest()
        for obj,key,value in ((b,'PIN_064_BCS',bcs_sha),(old,'BCS_SHA',bcs_sha)):
            x=monkey.object(obj,key,value);x.start();self.addCleanup(x.stop)
        self.no=lambda:None
        self.compiler=lambda *a:self.frag
        self.backup=lambda game,proof,label:old.make_backup(game,proof,label,parent=self.backups)

    def instal(self,**kw):return m.install(self.root,process_guard=kw.get('guard',self.no),compiler=kw.get('compiler',self.compiler),make_backup=kw.get('backup',self.backup),runner=kw.get('runner',self.mock))
    def rollback(self,**kw):return m.rollback(self.root,process_guard=kw.get('guard',self.no),make_backup=kw.get('backup',self.backup),runner=kw.get('runner',self.mock))
    def test_01_source_pins_and_deterministic_caster(self):
        self.assertEqual(m.source_check()['lua_sha256'],m.PIN066S)
    def test_02_1065_to_1076_lossless_bcs_splice(self):
        new,proof=b.splice(self.oldbcs,self.frag)
        self.assertEqual(proof['total_blocks'],1076)
        oldchunk=b.segment(self.oldbcs,1065)
        newchunk=b.segment(new,1076)
        self.assertEqual(newchunk[:1039],oldchunk[:1039]);self.assertEqual(newchunk[1050:],oldchunk[1039:])
        self.assertEqual(len(newchunk[1039:1050]),11)
    def test_03_patch_rejects_bcs_drift(self):
        with self.assertRaisesRegex(ValueError,'064_BCS_SHA'):b.splice(self.oldbcs+b'EVIL',self.frag)
    def test_04_patch_rejects_unexpected_receiver_actions(self):
        with self.assertRaisesRegex(ValueError,'ACTION_LAYOUT'):
            b.splice(self.oldbcs,fragment().replace(b'31OB',b'87OB',1))
    def test_05_preflight_readonly(self):
        before={x.relative_to(self.root):x.read_bytes() for x in self.root.rglob('*') if x.is_file()}
        proof,data=m.prepare(self.root,process_guard=self.no,compiler=self.compiler)
        self.assertEqual(proof['authorized_to_install'],False)
        self.assertEqual(len(b.segment(data,1076)),1076)
        self.assertEqual(before,{x.relative_to(self.root):x.read_bytes() for x in self.root.rglob('*') if x.is_file()})
    def test_06_fake_install_rollback(self):
        self.instal()
        after=m.status066s(self.root)
        self.assertEqual(after['status'],'INSTALLED_066S_VERIFIED')
        self.assertNotEqual((self.root/m.BCS).read_bytes(),self.oldbcs)
        self.assertEqual((self.root/m.LUA).read_bytes(),m.CANDIDATE.read_bytes())
        res=self.rollback()
        self.assertEqual(res['status'],'ROLLED_BACK_TO_064_VERIFIED')
        self.assertEqual((self.root/m.BCS).read_bytes(),self.oldbcs)
        self.assertEqual((self.root/m.LUA).read_bytes(),old.source_check())
        self.assertEqual(self.mock.calls,['install','rollback'])
    def test_07_backup_exact_original_both_files(self):
        out=self.instal();p=Path(out['backup'])
        self.assertEqual((p/m.BCS).read_bytes(),self.oldbcs)
        self.assertEqual((p/m.LUA).read_bytes(),old.source_check())
    def test_08_other_last_weidu_rejected_without_game_write(self):
        with (self.root/'WeiDU.log').open('ab') as f:f.write(b'~OTHER\\SETUP.TP2~ #0 #0\n')
        with self.assertRaisesRegex(m.Stop,'064_BASELINE_NOT_VERIFIED'):self.instal()
        self.assertFalse((self.root/'BGX66S').exists())
    def test_09_changed_bcs_denied(self):
        (self.root/m.BCS).write_bytes(b'DRIFT')
        with self.assertRaisesRegex(m.Stop,'064_BASELINE_NOT_VERIFIED'):self.instal()
    def test_10_changed_lua_denied(self):
        (self.root/m.LUA).write_bytes(b'DRIFT')
        with self.assertRaisesRegex(m.Stop,'064_BASELINE_NOT_VERIFIED'):self.instal()
    def test_11_process_guard_blocks_install(self):
        with self.assertRaisesRegex(m.Stop,'ACTIVE_GAME'):self.instal(guard=lambda: (_ for _ in ()).throw(m.Stop('ACTIVE_GAME')))
        self.assertFalse((self.root/'BGX66S').exists())
    def test_12_backup_failure_blocks_stage(self):
        with self.assertRaisesRegex(m.Stop,'BACKUP_FAILED'):self.instal(backup=lambda *a: (_ for _ in ()).throw(m.Stop('BACKUP_FAILED')))
        self.assertFalse((self.root/'BGX66S').exists())
    def test_13_weidu_install_failure_no_false_success(self):
        fail=FakeWeidu(fail=True)
        with self.assertRaisesRegex(m.Stop,'WEIDU_FAILED_DO_NOT_RETRY'):self.instal(runner=fail)
        self.assertEqual((self.root/m.BCS).read_bytes(),self.oldbcs)
    def test_14_rollback_blocks_drift_bcs(self):
        self.instal();(self.root/m.BCS).write_bytes(b'DRIFT')
        with self.assertRaisesRegex(m.Stop,'066S_STAGED_BCS_DRIFT'):self.rollback()
    def test_15_rollback_blocks_foreign_last(self):
        self.instal();withopen=self.root/'WeiDU.log'
        with withopen.open('ab') as f:f.write(b'~OTHER\\SETUP.TP2~ #0 #0\n')
        with self.assertRaisesRegex(m.Stop,'066S_NOT_LAST_WEIDU'):self.rollback()
    def test_16_wrong_token_denied(self):
        self.assertEqual(m.main(['install','--yes','--confirm','WRONG','--game-root',str(self.root)]),2)
    def test_17_noncanonical_root_denied(self):
        self.assertEqual(m.main(['install','--yes','--confirm','INSTALL_BGXAI_066S','--game-root',str(self.root)]),2)
    def test_18_stage_collision_denied(self):
        (self.root/'BGX66S').mkdir()
        with self.assertRaisesRegex(m.Stop,'066S_STAGE_COLLISION'):self.instal()
    def test_19_missing_spell_compile_output_denied(self):
        with self.assertRaisesRegex(ValueError,'066S_RECEIVER_ACTION_LAYOUT'):
            m.prepare(self.root,compiler=lambda *a:self.frag.replace(b'31OB',b'87OB'),process_guard=self.no)
    def test_20_installed_bcs_double_tamper_caught(self):
        self.instal()
        live=self.root/m.BCS
        data=live.read_bytes().replace(b'LOCALSBGX66_S_X',b'LOCALSBGX66_S_Y',1)
        live.write_bytes(data)
        (self.root/m.STAGE_BCS).write_bytes(data)
        with self.assertRaisesRegex(m.Stop,'066S_BCS_EXPECTED_SHA_DRIFT'):
            m.status066s(self.root)
    def test_21_rollback_process_guard_blocks_mutation(self):
        self.instal();before=(self.root/m.BCS).read_bytes()
        with self.assertRaisesRegex(m.Stop,'ACTIVE_GAME'):self.rollback(guard=lambda: (_ for _ in ()).throw(m.Stop('ACTIVE_GAME')))
        self.assertEqual((self.root/m.BCS).read_bytes(),before)

if __name__=='__main__':unittest.main()
