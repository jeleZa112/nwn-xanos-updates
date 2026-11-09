from __future__ import annotations
from pathlib import Path
import hashlib, os, re, subprocess, sys, json, pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import BGXAI56_BUILDER as b
import BGXAI56_INSTALL as i


def block(n, acts, *,guard=False, f=False):
    triggers=(b'LOCALSBGX38_GUARD\n' if guard or f else b'STATE\n')
    aa=b''.join(b'AC\n'+str(x).encode()+b'OB\nOB\nAC\n' for x in acts)
    return b'CR\nCO\n'+triggers+b'CO\nRS\nRP\n100\n'+aa+b'RS\nCR\n'


def synthetic_original():
    parts=[]
    for idx in range(1,1058):
        acts=[115,87] if 1032<=idx<=1042 else [105] if idx in (1043,1056) else [0]
        parts.append(block(idx,acts,guard=1032<=idx<=1042,f=idx==1))
    return b'SC\n'+b''.join(parts)


def compiled_receiver():
    return b'SC\n'+b''.join([block(n,[30,36]) if n<=2 else block(n,[30,115,87]) for n in range(1,9)])


def test_insert_exactly_after_F_before_guards(monkeypatch):
    original=synthetic_original()
    monkeypatch.setattr(b,'PIN_BCS',b.sha(original))
    monkeypatch.setattr(b,'PIN_BCS_BYTES',len(original))
    new,proof=b.combine(original,compiled_receiver())
    assert proof['total_blocks']==1065
    old_blocks=b.segment(original,1057);new_blocks=b.segment(new,1065)
    assert old_blocks[:1031]==new_blocks[:1031]
    assert new_blocks[1031:1039]==b.segment(compiled_receiver(),8)
    assert new_blocks[1039:]==old_blocks[1031:]
    assert b.actions(new_blocks[1042])==[115,87]
    assert b.actions(new_blocks[1050])==[105]


def test_hash_pin_blocks_unknown_042b():
    with pytest.raises(ValueError,match='LIVE_042B_HASH_MISMATCH'):
        b.verify_old(synthetic_original())


def test_corrupt_splice_is_rejected():
    with pytest.raises(ValueError,match='NEW_RECEIVER_ACTION_IDS_UNEXPECTED'):
        b.verify_insert(b'SC\n'+block(1,[3])+b''.join(block(x,[0]) for x in range(2,9)))


def test_056_source_never_clears_actions():
    lua=(ROOT/i.LUA).read_text(encoding='utf8')
    assert lua.count('B.enabled = true')==1
    assert 'local guard=safe(function()return obj:getLocalInt("BGX38_GUARD")end)' in lua
    assert 'set("BGX52_REQ_SLOT",slot)' in lua
    assert 'return false -- CRITICAL' in lua
    baf=(ROOT/i.BAF).read_text(encoding='ascii')
    assert baf.count('ActionListEmpty()')==6
    assert baf.count('ModalState(NONE)')==6
    assert baf.count('ProtectObject(')==6
    for bad in ('ClearActions()', 'ActionOverride(', 'Attack(', 'AttackReevaluate('):
        assert bad not in baf
    assert (ROOT/i.TP2).read_text().count('COPY ~')==2


def prepare_fixture(tmp_path,monkeypatch):
    g=tmp_path/'game';g.mkdir()
    original=synthetic_original();old_lua=b'original 049 local read-only\n'
    def write(name,data):
        p=g/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    write('chitin.key',b'X'*3000)
    write('InfinityLoader.exe',b'MZ'+b'Y'*12000)
    write(i.WEIDU,b'MZ'+b'W'*100020)
    write(i.BCS,original)
    write(i.DEST_LUA,old_lua)
    write('WeiDU.log',b'~BGX49/SETUP-BGX49.TP2~ #0 #0 // 049')
    write('weidu.conf',b'lang_dir = ru_ru\n')
    write('lang/ru_RU/dialog.tlk',b'DIALOG'*100)
    write('lang/ru_RU/dialogf.tlk',b'DIALOGF'*100)
    for p in i.OTHER_BASE:write(p,(p*5).encode())
    monkeypatch.setattr(b,'PIN_BCS',b.sha(original))
    monkeypatch.setattr(b,'PIN_BCS_BYTES',len(original))
    monkeypatch.setattr(i,'PIN_BCS',b.sha(original))
    monkeypatch.setattr(i,'PIN_BCS_BYTES',len(original))
    monkeypatch.setattr(i,'OLD_LUA',i.digest(g/i.DEST_LUA))
    monkeypatch.setattr(i,'OTHER_BASE',{p:i.digest(g/p) for p in i.OTHER_BASE})
    monkeypatch.setattr(i,'verify_package',lambda _: {'files':{i.LUA:{'sha256':i.digest(ROOT/i.LUA)}}})
    return g,original,old_lua


def test_preflight_exact_and_no_staging(tmp_path,monkeypatch):
    g,old,lua=prepare_fixture(tmp_path,monkeypatch)
    pre=i.preflight(g,enforce=False)
    assert pre['hashes'][i.BCS]==b.sha(old)
    assert not (g/i.MOD).exists()
    (g/i.BCS).write_bytes(old+b'X')
    with pytest.raises(RuntimeError,match='BASELINE_SHA_MISMATCH'):
        i.preflight(g,enforce=False)


def test_install_and_uninstall_with_fake_weidu(tmp_path,monkeypatch):
    g,old,lua=prepare_fixture(tmp_path,monkeypatch)
    backup_dir=tmp_path/'backup'
    def fake_weidu(cmd,**kwargs):
        assert kwargs['stdin']==subprocess.DEVNULL
        assert '--no-exit-pause' in cmd
        assert kwargs['cwd']==str(g)
        log=(g/'WeiDU.log').read_text()
        if '--force-uninstall' in cmd:
            (g/i.BCS).write_bytes(old)
            (g/i.DEST_LUA).write_bytes(lua)
            log="\n".join(log.splitlines()[:-1])
        else:
            (g/i.BCS).write_bytes((g/i.MOD/'staged/BDDEFAI.BCS').read_bytes())
            (g/i.DEST_LUA).write_bytes((g/i.LUA).read_bytes())
            log+="\n~BGX56/SETUP-BGX56.TP2~ #0 #0 // 056"
        (g/'WeiDU.log').write_text('\n'.join(log.splitlines())+'\n')
        return subprocess.CompletedProcess(cmd,0,'ok','')
    res=i.install(g,ROOT,guard=lambda:None,runner=fake_weidu,
                  base=backup_dir,enforce=False,
                  compiler=lambda *_:compiled_receiver())
    assert res['status']=='INSTALLED_EXPERIMENTAL_056',res
    assert all(res['checks'].values())
    assert i.digest(g/i.BCS)==res['proposal']['patched_sha']
    assert i.digest(g/i.DEST_LUA)==i.digest(ROOT/i.LUA)
    assert (backup_dir).exists()
    undone=i.uninstall(g,ROOT,guard=lambda:None,runner=fake_weidu,
                       base=backup_dir,enforce=False)
    assert undone['status']=='UNINSTALLED_RESTORED_049',undone
    assert (g/i.BCS).read_bytes()==old
    assert (g/i.DEST_LUA).read_bytes()==lua


def test_blocked_if_049_not_last(tmp_path,monkeypatch):
    g,_,_=prepare_fixture(tmp_path,monkeypatch)
    with (g/'WeiDU.log').open('ab') as f:f.write(b'\n~UNKNOWN/SETUP-UNKNOWN.TP2~ #0 #0\n')
    with pytest.raises(RuntimeError,match='WEIDU_LAST_MOD_UNEXPECTED'):
        i.preflight(g,enforce=False)


def test_staged_path_collision_blocked(tmp_path,monkeypatch):
    g,_,_=prepare_fixture(tmp_path,monkeypatch)
    (g/i.MOD).mkdir()
    with pytest.raises(RuntimeError,match='STAGING_COLLISION'):
        i.preflight(g,enforce=False)


def test_no_game_change_if_compile_failed(tmp_path,monkeypatch):
    g,_,_=prepare_fixture(tmp_path,monkeypatch)
    before={f:i.digest(g/f) for f in i.BACKUP_FILES}
    def fail(*_):raise RuntimeError('real compile failed')
    with pytest.raises(RuntimeError,match='real compile failed'):
        i.install(g,ROOT,guard=lambda:None,runner=lambda *a,**kw: (_ for _ in ()).throw(AssertionError('WEIDU STARTED')),
                  base=tmp_path/'backup',enforce=False,compiler=fail)
    assert before=={f:i.digest(g/f) for f in i.BACKUP_FILES}
    assert not (g/i.MOD).exists()


def test_staged_hash_verification_fails_if_modified(tmp_path,monkeypatch):
    g,_,_=prepare_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(i,'verify_package',lambda _: {'files':{i.LUA:{'sha256':'0'*64}}})
    res=i.install(g,ROOT,guard=lambda:None,base=tmp_path/'backup',enforce=False,
                  compiler=lambda *_:compiled_receiver())
    assert res['status']=='BLOCKED_BEFORE_WEIDU'
    assert not (g/i.MOD).exists()
    assert not (g/i.EXECUTABLE).exists()
