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
        assert kwargs['cwd']==str(game)
        assert Path(cmd[-1]).parent!=game
        assert '--out' in cmd and '--tlkin' in cmd and '--use-lang' not in cmd
        assert '--force-install' not in cmd
        dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath(mod.COMPILE_NAME.replace('.baf','.bcs')).write_bytes(b'SC\n0CR\n')
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
        dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath(mod.COMPILE_NAME.replace('.baf','.bcs')).write_bytes(b'SC\n')
        return subprocess.CompletedProcess(cmd,0,'','')
    result=mod.compile_readonly(game,SOURCE,exe,runner=unwanted_write)
    assert result['status']=='REVIEW_LIVE_HASH_CHANGED' and not result['live_unchanged']

@pytest.mark.parametrize('exit_code,emit',[(1,True),(0,False),(1,False)])
def test_compiler_failures_never_mean_success(tmp_path,monkeypatch,exit_code,emit):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    def failing(cmd,**kwargs):
        if emit:
            dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath(mod.COMPILE_NAME.replace('.baf','.bcs')).write_bytes(b'SC\n')
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
    with pytest.raises(ValueError,match='SOURCE_IN_LIVE_GAME_UNAPPROVED'):
        mod.compile_readonly(game,bad,exe)

def test_missing_tlk_blocks(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'lang/ru_ru/dialog.tlk').unlink()
    with pytest.raises(ValueError,match='DIALOG_TLK_LANGUAGE_UNRESOLVED'):
        mod.compile_readonly(game,SOURCE,exe)

def test_missing_weidu_log_blocks(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'WeiDU.log').unlink()
    with pytest.raises(ValueError,match='WEIDU_LOG_MISSING_OR_UNREADABLE'):
        mod.compile_readonly(game,SOURCE,exe)


def test_updater_approved_source_inside_game(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    root=game/'BGXAI_DEV'/'experimental_054';root.mkdir(parents=True)
    approved=root/mod.NAME;approved.write_bytes(SOURCE.read_bytes())
    def fake_compiler(cmd,**kwargs):
        assert str(approved)==cmd[-1] or str(approved) not in cmd
        dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath(mod.COMPILE_NAME.replace('.baf','.bcs')).write_bytes(b'SC\n')
        return subprocess.CompletedProcess(cmd,0,'','')
    result=mod.compile_readonly(game,approved,exe,runner=fake_compiler)
    assert result['status']=='COMPILED_TEMP_ONLY' and result['live_unchanged']

def test_approved_dir_other_filename_denied(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    root=game/'BGXAI_DEV'/'experimental_054';root.mkdir(parents=True)
    bad=root/'other.baf';bad.write_bytes(SOURCE.read_bytes())
    with pytest.raises(ValueError,match='SOURCE_IN_LIVE_GAME_UNAPPROVED'):
        mod.compile_readonly(game,bad,exe)


def test_weidu_config_english_selects_english_tlk_without_game_changes(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'weidu.conf').write_text('lang_dir = en_US\n',encoding='ascii')
    english=game/'lang'/'en_US'/'dialog.tlk';english.parent.mkdir(parents=True)
    english.write_bytes(b'english dialog')
    before=mod.snapshot(game)
    def fake_compiler(cmd,**kwargs):
        assert cmd[cmd.index('--tlkin')+1]==str(english)
        dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath('BX52CHK.bcs').write_bytes(b'SC\n')
        return subprocess.CompletedProcess(cmd,0,'','')
    result=mod.compile_readonly(game,SOURCE,exe,runner=fake_compiler)
    assert result['status']=='COMPILED_TEMP_ONLY'
    assert result['selected_tlk']=='lang/en_US/dialog.tlk'
    assert result['live_unchanged'] and mod.snapshot(game)==before


def test_weidu_config_lowercase_maps_mixed_case_directory(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'weidu.conf').write_text('lang_dir = en_us\n',encoding='ascii')
    lang=game/'lang'/'en_US';lang.mkdir(parents=True)
    (lang/'dialog.tlk').write_bytes(b'english dialog')
    assert mod.resolve_dialog_tlk(game)==lang/'dialog.tlk'


def test_without_conf_russian_preferred(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'weidu.conf').unlink()
    other=game/'lang'/'en_US';other.mkdir(parents=True)
    (other/'dialog.tlk').write_bytes(b'english')
    assert mod.resolve_dialog_tlk(game)==game/'lang/ru_ru/dialog.tlk'


def test_mismatched_config_stops_with_available_language(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'weidu.conf').write_text('lang_dir = en_US\n',encoding='ascii')
    with pytest.raises(ValueError,match='DIALOG_TLK_CONFIGURED_LANGUAGE_MISSING: en_us; available=ru_ru'):
        mod.compile_readonly(game,SOURCE,exe)


def test_ambiguous_language_without_config_stops(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    (game/'weidu.conf').unlink()
    (game/'lang/ru_ru/dialog.tlk').unlink()
    for name in ('en_US','de_DE'):
        folder=game/'lang'/name;folder.mkdir(parents=True)
        (folder/'dialog.tlk').write_bytes(b'lang')
    with pytest.raises(ValueError,match='DIALOG_TLK_LANGUAGE_UNRESOLVED'):
        mod.compile_readonly(game,SOURCE,exe)


def test_tlk_mutated_during_compile_is_review(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    def runner(cmd,**kwargs):
        (game/'lang/ru_ru/dialog.tlk').write_bytes(b'changed')
        dest=Path(cmd[cmd.index('--out')+1]);dest.joinpath('BX52CHK.bcs').write_bytes(b'SC\n')
        return subprocess.CompletedProcess(cmd,0,'','')
    result=mod.compile_readonly(game,SOURCE,exe,runner=runner)
    assert result['status']=='REVIEW_LIVE_HASH_CHANGED' and not result['live_unchanged']


def test_weidu_fatal_even_zero_exit_is_failure(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    before=mod.snapshot(game)
    def faulty_weidu(cmd,**kwargs):
        assert kwargs['cwd']==str(game)
        return subprocess.CompletedProcess(cmd,0,'FATAL ERROR: Failure("Not a game directory")','')
    result=mod.compile_readonly(game,SOURCE,exe,runner=faulty_weidu)
    assert result['status']=='WEIDU_FATAL_ERROR'
    assert result['weidu_fatal_in_output'] and result['live_unchanged']
    assert result['install_performed'] is False and mod.snapshot(game)==before

def test_zero_exit_with_error_message_and_fake_output_still_fails(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    def faulty_weidu(cmd,**kwargs):
        dest=Path(cmd[cmd.index('--out')+1])
        dest.joinpath('BX52CHK.bcs').write_bytes(b'SC\n')
        return subprocess.CompletedProcess(cmd,0,'ERROR: Unable to find ACTION.IDS','')
    result=mod.compile_readonly(game,SOURCE,exe,runner=faulty_weidu)
    assert result['status']=='WEIDU_FATAL_ERROR'
    assert result['live_unchanged']

def test_weidu_arguments_source_and_output_stay_in_temp(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    def fake_weidu(cmd,**kwargs):
        assert kwargs['cwd']==str(game)
        assert '--noautoupdate' in cmd and '--tlkin' in cmd
        assert '--force-install' not in cmd and '--use-lang' not in cmd
        source=Path(cmd[-1]);out=Path(cmd[cmd.index('--out')+1])
        assert source.parent!=game and out!=game and game not in out.parents
        assert source.name=='BX52CHK.baf' and source.parent==out.parent
        out.joinpath('BX52CHK.bcs').write_bytes(b'SC\n0CR\n')
        return subprocess.CompletedProcess(cmd,0,'Compiled','')
    report=mod.compile_readonly(game,SOURCE,exe,runner=fake_weidu)
    assert report['status']=='COMPILED_TEMP_ONLY' and report['live_unchanged']

# R3 regression: the prior 90-second timeout was caused by invoking
# setup-enhanced-powergaming-scripts.exe, which defaults to auto-run a TP2.
def test_setup_exe_is_copied_and_invoked_as_temp_weidu_no_auto_tp2(tmp_path,monkeypatch):
    game,old_exe=make_game(tmp_path);gate_ok(monkeypatch)
    setup=game/'setup-enhanced-powergaming-scripts.exe'
    setup.write_bytes(old_exe.read_bytes())
    import compile_guard_054 as m
    def fake(cmd,**kwargs):
        assert Path(cmd[0]).name.lower()=='weidu.exe'
        assert Path(cmd[0]).parent!=game
        assert '--no-auto-tp2' in cmd
        assert '--no-exit-pause' in cmd
        assert '--noautoupdate' in cmd
        assert '--log' in cmd and Path(cmd[cmd.index('--log')+1]).parent!=game
        assert kwargs['stdin']==subprocess.DEVNULL
        assert kwargs['timeout']==25
        assert kwargs['cwd']==str(game)
        assert Path(cmd[0]).read_bytes()==setup.read_bytes()
        dest=Path(cmd[cmd.index('--out')+1])
        dest.joinpath('BX52CHK.bcs').write_bytes(b'SC\n0CR\n')
        return subprocess.CompletedProcess(cmd,0,'compiled','')
    before=m.snapshot(game)
    result=m.compile_readonly(game,SOURCE,setup,runner=fake)
    assert result['status']=='COMPILED_TEMP_ONLY'
    assert result['compiler_staged_as']=='TEMP_WEIDU_EXE'
    assert result['live_unchanged']
    assert before==m.snapshot(game)


def test_timeout_is_explicit_and_preserves_partial_output(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    before=mod.snapshot(game)
    def timeout(cmd,**kwargs):
        raise subprocess.TimeoutExpired(cmd,25,output=b'prompts waiting for input',stderr=b'tp2 blocked')
    report=mod.compile_readonly(game,SOURCE,exe,runner=timeout)
    assert report['status']=='COMPILER_TIMEOUT'
    assert report['timeout_seconds']==25
    assert 'prompts waiting' in report['stdout_tail']
    assert 'tp2 blocked' in report['stderr_tail']
    assert report['live_unchanged'] and not report['install_performed']
    assert mod.snapshot(game)==before


def test_actual_subprocess_with_staged_fake_exe_exits_without_prompt(tmp_path,monkeypatch):
    """Real OS subprocess execution, but intentionally a fake executable,
    NOT a claim that the true Windows WeiDU was tested."""
    import os
    if os.name=='nt':pytest.skip('POSIX shebang fake executable test')
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    # Stand-in process that refuses to compile if invoked as setup-* or
    # without the explicit WeiDU safety flags.
    exe.write_text('''#!/usr/bin/env python3
import sys,pathlib
args=sys.argv[1:]
if pathlib.Path(sys.argv[0]).name.lower()!='weidu.exe':
    print('AUTO_TP2_UNSAFE');sys.exit(5)
if not {'--no-auto-tp2','--no-exit-pause','--noautoupdate'}.issubset(args):
    print('INTERACTIVE_UNSAFE');sys.exit(6)
if sys.stdin.read()!='':
    print('STDIN_NOT_CLOSED');sys.exit(7)
out=pathlib.Path(args[args.index('--out')+1]);out.mkdir(exist_ok=True)
(out/'BX52CHK.bcs').write_bytes(b'SC\\n0CR\\n')
print('compile complete')
''',encoding='utf-8')
    exe.chmod(0o755)
    before=mod.snapshot(game)
    report=mod.compile_readonly(game,SOURCE,exe)
    assert report['status']=='COMPILED_TEMP_ONLY',report
    assert report['live_unchanged']
    assert report['compiler_output_size']==7
    assert mod.snapshot(game)==before


def test_process_stdin_closed_and_setup_mode_protected_even_with_output(tmp_path,monkeypatch):
    game,exe=make_game(tmp_path);gate_ok(monkeypatch)
    def fake(cmd,**kwargs):
        assert cmd[1:4]==['--noautoupdate','--no-auto-tp2','--no-exit-pause']
        assert kwargs['stdin']==subprocess.DEVNULL
        out=Path(cmd[cmd.index('--out')+1]);out.joinpath('BX52CHK.bcs').write_bytes(b'SC\n')
        return subprocess.CompletedProcess(cmd,0,'ERROR: unexpected', '')
    report=mod.compile_readonly(game,SOURCE,exe,runner=fake)
    assert report['status']=='WEIDU_FATAL_ERROR'
    assert report['live_unchanged']
