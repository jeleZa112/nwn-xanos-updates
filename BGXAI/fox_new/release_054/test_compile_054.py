from pathlib import Path
import subprocess
import pytest
import compile_guard_054 as mod

SOURCE=Path(__file__).with_name(mod.NAME)

def make_game(tmp_path):
    game=tmp_path/'BG_EET_FOXX_NEW'
    for rel,content in {
        'chitin.key':b'test key',
        'WeiDU.log':b'~BGX49/SETUP-BGX49.TP2~ #0 #0 // sample test',
        'lang/ru_ru/dialog.tlk':b'test tlk',
        'lang/ru_ru/dialogf.tlk':b'test tlkf',
        'override/BDDEFAI.BCS':b'test bcs',
        'override/M_BX43.lua':b'test lua',
        'override/M_BX44.lua':b'test lua44',
        'weidu.conf':b'game_lang=ru',
    }.items():
        p=game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
    exe=game/'weidu.exe';exe.write_bytes(b'fake compiler')
    return game,exe

def gate_ok(monkeypatch):
    monkeypatch.setattr(mod.preflight,'inspect', lambda _:{'verdict':'BASELINE_OK_SOURCE_ONLY','issues':[]})

def test_source_structure_and_actions():
    result=mod.validate_baf(SOURCE)
    assert result['blocks']==8 and result['protect_slots']==[1,2,3,4,5,6]
    assert result['source_sha256']==mod.BAF_SHA

def test_valid_compile_is_temporary_and_readonly(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    before=mod.snapshot(game)
    def fake_runner(cmd,**kwargs):
        assert kwargs['cwd']!=str(game)
        assert '--out' in cmd and '--tlkin' in cmd and '--use-lang' not in cmd
        assert '--force-install' not in cmd
        dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath(mod.NAME.replace('.baf','.bcs')).write_bytes(b'SC\n0CR\n')
        return subprocess.CompletedProcess(cmd,0,'compiled','')
    report=mod.compile_readonly(game,SOURCE,exe,runner=fake_runner)
    assert report['status']=='COMPILED_TEMP_ONLY'
    assert report['live_unchanged'] and report['install_performed'] is False
    assert report['output_deleted_after_verification'] and mod.snapshot(game)==before
    assert report['compiler_output_size']==7

def test_preflight_mismatch_blocks_before_compiler(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path)
    monkeypatch.setattr(mod.preflight,'inspect',lambda _:{'verdict':'REVIEW_DO_NOT_INSTALL','issues':['wrong_BCS_hash']})
    with pytest.raises(ValueError,match='BASELINE_GATE_BLOCKED'):
        mod.compile_readonly(game,SOURCE,exe,runner=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('compiler started')))

def test_modified_baf_hash_blocks(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    bad=tmp_path/'bad.baf';bad.write_bytes(SOURCE.read_bytes()+b'\nAttack(Myself)\n')
    with pytest.raises(ValueError,match='BAF_SHA_MISMATCH'):
        mod.compile_readonly(game,bad,exe)

def test_live_game_modified_during_compile_is_review(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    def unwanted_write(cmd,**kwargs):
        (game/'override/BDDEFAI.BCS').write_bytes(b'CHANGED')
        dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath(mod.NAME.replace('.baf','.bcs')).write_bytes(b'SC\n')
        return subprocess.CompletedProcess(cmd,0,'','')
    result=mod.compile_readonly(game,SOURCE,exe,runner=unwanted_write)
    assert result['status']=='REVIEW_LIVE_HASH_CHANGED' and not result['live_unchanged']

@pytest.mark.parametrize('exit_code,emit',[(1,True),(0,False),(1,False)])
def test_compiler_failures_never_mean_success(tmp_path,monkeypatch,exit_code,emit):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    def failing(cmd,**kwargs):
        if emit:
            dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath(mod.NAME.replace('.baf','.bcs')).write_bytes(b'SC\n')
        return subprocess.CompletedProcess(cmd,exit_code,'bad','')
    result=mod.compile_readonly(game,SOURCE,exe,runner=failing)
    assert result['status']=='COMPILER_FAILED'
    assert result['live_unchanged']

def test_wrong_executable_location_blocks(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    outside=tmp_path/'other.exe';outside.write_bytes(b'fake compiler')
    with pytest.raises(ValueError,match='WEIDU_MUST_BE_IN_GAME_ROOT'):
        mod.compile_readonly(game,SOURCE,outside)

def test_source_inside_game_blocks(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    bad=game/'override'/mod.NAME
    bad.write_bytes(SOURCE.read_bytes())
    with pytest.raises(ValueError,match='SOURCE_IN_LIVE_GAME'):
        mod.compile_readonly(game,bad,exe)

def test_missing_tlk_blocks(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'lang/ru_ru/dialog.tlk').unlink()
    with pytest.raises(ValueError,match='REQUIRED_LOG_OR_TLK_MISSING'):
        mod.compile_readonly(game,SOURCE,exe)

def test_missing_weidu_log_blocks(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'WeiDU.log').unlink()
    with pytest.raises(ValueError,match='REQUIRED_LOG_OR_TLK_MISSING'):
        mod.compile_readonly(game,SOURCE,exe)
