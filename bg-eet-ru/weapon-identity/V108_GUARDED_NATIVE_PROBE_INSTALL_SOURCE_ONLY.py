# V108 — guarded native CItem RESREF observer. Contains NO automatic installation.
# Must be integrated in the ONE original BG_EET_RU_UPDATE.cmd only.
V108_SCHEMA = 'BG_EET_RU_V108_NATIVE_ITEM_RESREF_PILOT'
V108_ENTRY = '54_V108_NATIVE_ITEM_RESREF_PILOT.json'
V108_STATE = WORKDIR / 'BG_EET_RU_V108_NATIVE_ITEM_STATE.json'
V108_APPROVE_INSTALL = 'INSTALL_BG_EET_RU_V108_NATIVE_ITEM_READ'
V108_APPROVE_ROLLBACK = 'ROLLBACK_BG_EET_RU_V108_NATIVE_ITEM_READ'
V108_PREFIX = '[BG_EET_RU_V108]'
V108_BASIS_SHA = {
    'EEex.dll': 'b6c7c98804360cb46531db75ab9608e378fd403d60c29c0e29946a60a334276a',
    'InfinityLoader.exe': 'df0d3604cb91c127643126b7960429194f3333bce8bac0e59aecb6a178ac84b9',
    'Baldur.exe': 'fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580',
    'EEex_scripts/EEex_Main.lua': '5a0cf85af1da9a2c13813f9be03001d8d821addffe137780b74a73b6c4d75618',
    'EEex_scripts/BG_EET_RU_WeaponObserver.lua': '4130359dc7778e816ad2bbf1cca20152e48fa9df4907d6411a793c0754e09bc6',
    'EEex_scripts/EEex_Sprite.lua': '4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28',
    'EEex_scripts/EEex_Sprite_Patch.lua': 'e301b46770477cf29e3d39d6591a5a9fba4f3aeafa03c3dbfa75f7ef6bc13b7f',
}
V108_LUA_SOURCE_SHA256 = '653e6001b0578bb027ea971e7d6e51d7ef5d838373f9c0854f2b6ec81748728c'
V108_LUA_SOURCE_B64 = (
    'LS0gQkdfRUVUX1JVIFYxMDggUkVTVFJJQ1RFRCBDSXRlbSBSRVNSRUYgcGlsb3QsIFNPVVJDRSBPTkxZLCBOT1QgSU5TVEFMTEVELgotLSBBcHBlbmQgb25s'
    'eSB0byBleGFjdCBwaW5uZWQgVjEwNiBCR19FRVRfUlVfV2VhcG9uT2JzZXJ2ZXIubHVhLgotLSBObyBuZXcgbGlzdGVuZXIgcmVnaXN0cmF0aW9uLCBubyBn'
    'YW1lIGVmZmVjdCAvIGFjdGlvbiAvIFVJIC8gVExLIG11dGF0aW9uLgotLSBBIGZ1dHVyZSBndWFyZGVkIGluc3RhbGxlciBNVVNUIGhhc2ggRUVleC5kbGws'
    'IEVFZXhfU3ByaXRlLmx1YSwKLS0gRUVleF9TcHJpdGVfUGF0Y2gubHVhLCBFRWV4X01haW4ubHVhIGFuZCBleGFjdCBWMTA2IG1vZHVsZSwgdGFrZSBleHRl'
    'cm5hbAotLSBiYWNrdXAsIHJlcXVpcmUgdHlwZWQgdXNlciBhcHByb3ZhbCwgYW5kIHByb3ZpZGUgYXRvbWljIGxhc3Qtb25seSByb2xsYmFjay4KLS0gTk9U'
    'RTogcGNhbGwgZG9lcyBOT1QgcHJldmVudCBuYXRpdmUgbWVtb3J5IGNvcnJ1cHRpb24gLyBwcm9jZXNzIGNyYXNoLgoKQkdfRUVUX1JVX1YxMDggPSB7CiAg'
    'ICBlbmFibGVkID0gZmFsc2UsIC0tIE1VU1QgcmVtYWluIG9mZiB1bnRpbCBhIHNlcGFyYXRlbHkgYXV0aG9yaXplZCBpbnN0YWxsCiAgICBuYXRpdmVfcmVh'
    'ZF9hdXRob3JpemVkID0gZmFsc2UsCiAgICBtYXhfc2FtcGxlcyA9IDgsCiAgICBzZWVuID0gMCwKICAgIGVtaXR0ZWQgPSAwLAogICAgd2VhcG9uX3JlZnNf'
    'dmVyaWZpZWQgPSAwLAogICAgbGF1bmNoZXJfcmVmc192ZXJpZmllZCA9IDAsCiAgICBhbW1vX3ZlcmlmaWVkID0gZmFsc2UsCiAgICBtaXNzZXNfdmVyaWZp'
    'ZWQgPSBmYWxzZSwKICAgIGpvdXJuYWxfbWFwcGluZ192ZXJpZmllZCA9IGZhbHNlLAp9Cgpsb2NhbCBmdW5jdGlvbiB2MTA4X3JlZihvYmopCiAgICBpZiB0'
    'eXBlKG9iaikgfj0gJ3VzZXJkYXRhJyB0aGVuIHJldHVybiAnTk9UX0NJVEVNX1VTRVJEQVRBJyBlbmQKICAgIC0tIFRoaXMgZGVyZWZlcmVuY2VzIG5hdGl2'
    'ZSBDSXRlbS4gSXQgaXMgT05MWSBwZXJtaXR0ZWQgd2hpbGUgdGhlIGNhbGxiYWNrCiAgICAtLSBpcyBleGVjdXRpbmcgd2l0aCB0aGUgZXhhY3QgYXBwcm92'
    'ZWQgQUJJICsgc291cmNlIGhhc2hlcy4KICAgIGxvY2FsIG9rLCByZWYgPSBwY2FsbChmdW5jdGlvbigpIHJldHVybiBvYmouY1Jlc1JlZjpnZXQoKSBlbmQp'
    'CiAgICBpZiBub3Qgb2sgdGhlbiByZXR1cm4gJ0xVQV9SRUFEX0VSUk9SJyBlbmQKICAgIGlmIHR5cGUocmVmKSB+PSAnc3RyaW5nJyBvciAjcmVmID09IDAg'
    'b3IgI3JlZiA+IDggdGhlbiByZXR1cm4gJ0lOVkFMSURfUkVTUkVGJyBlbmQKICAgIGlmIHJlZjpmaW5kKCdbXkEtWmEtejAtOV9dJykgdGhlbiByZXR1cm4g'
    'J0lOVkFMSURfUkVTUkVGJyBlbmQKICAgIHJldHVybiBzdHJpbmcudXBwZXIocmVmKQplbmQKCmxvY2FsIHYxMDhfcHJldmlvdXNfY2FsbGJhY2sgPSBCR19F'
    'RVRfUlVfV0VBUE9OX0VWRU5UX09CU0VSVkVSX1YxX09uQmFzZURhbWFnZQpmdW5jdGlvbiBCR19FRVRfUlVfV0VBUE9OX0VWRU5UX09CU0VSVkVSX1YxX09u'
    'QmFzZURhbWFnZShjb250ZXh0KQogICAgLS0gUHJlc2VydmUgdGhlIHByb3ZlbiwgaW5zdGFsbGVkIFYxMDYgb2JzZXJ2ZXIgYW5kIGl0cyBib3VuZGVkIGV2'
    'ZW50IGxvZ3MuCiAgICB2MTA4X3ByZXZpb3VzX2NhbGxiYWNrKGNvbnRleHQpCiAgICBsb2NhbCBzdCA9IEJHX0VFVF9SVV9WMTA4CiAgICBpZiBub3Qgc3Qu'
    'ZW5hYmxlZCBvciBub3Qgc3QubmF0aXZlX3JlYWRfYXV0aG9yaXplZCB0aGVuIHJldHVybiBuaWwgZW5kCiAgICBpZiB0eXBlKGNvbnRleHQpIH49ICd0YWJs'
    'ZScgdGhlbiByZXR1cm4gbmlsIGVuZAogICAgc3Quc2VlbiA9IHN0LnNlZW4gKyAxCiAgICBpZiBzdC5lbWl0dGVkID49IHN0Lm1heF9zYW1wbGVzIHRoZW4g'
    'cmV0dXJuIG5pbCBlbmQKICAgIGxvY2FsIHdlYXBvbiA9IHYxMDhfcmVmKGNvbnRleHQud2VhcG9uKQogICAgbG9jYWwgbGF1bmNoZXIgPSB2MTA4X3JlZihj'
    'b250ZXh0LmxhdW5jaGVyKQogICAgaWYgd2VhcG9uIH49ICdJTlZBTElEX1JFU1JFRicgYW5kIHdlYXBvbiB+PSAnTk9UX0NJVEVNX1VTRVJEQVRBJyBhbmQg'
    'd2VhcG9uIH49ICdMVUFfUkVBRF9FUlJPUicgdGhlbgogICAgICAgIHN0LndlYXBvbl9yZWZzX3ZlcmlmaWVkID0gc3Qud2VhcG9uX3JlZnNfdmVyaWZpZWQg'
    'KyAxCiAgICBlbmQKICAgIGlmIGxhdW5jaGVyIH49ICdJTlZBTElEX1JFU1JFRicgYW5kIGxhdW5jaGVyIH49ICdOT1RfQ0lURU1fVVNFUkRBVEEnIGFuZCBs'
    'YXVuY2hlciB+PSAnTFVBX1JFQURfRVJST1InIHRoZW4KICAgICAgICBzdC5sYXVuY2hlcl9yZWZzX3ZlcmlmaWVkID0gc3QubGF1bmNoZXJfcmVmc192ZXJp'
    'ZmllZCArIDEKICAgIGVuZAogICAgc3QuZW1pdHRlZCA9IHN0LmVtaXR0ZWQgKyAxCiAgICBpZiB0eXBlKEluZmluaXR5X0xvZykgPT0gJ2Z1bmN0aW9uJyB0'
    'aGVuCiAgICAgICAgbG9jYWwgbGluZSA9ICdbQkdfRUVUX1JVX1YxMDhdIEVWRU5UXHQnIC4uIHRvc3RyaW5nKHN0LmVtaXR0ZWQpIC4uCiAgICAgICAgICAg'
    'ICAgICAgICAgICdcdHdlYXBvbl9yZXNyZWY9JyAuLiB3ZWFwb24gLi4gJ1x0bGF1bmNoZXJfcmVzcmVmPScgLi4gbGF1bmNoZXIgLi4KICAgICAgICAgICAg'
    'ICAgICAgICAgJ1x0YW1tbz1VTlZFUklGSUVEXHRoaXRfbWlzcz1VTlZFUklGSUVEXHRqb3VybmFsX3Jvdz1VTlZFUklGSUVEJwogICAgICAgIHBjYWxsKElu'
    'ZmluaXR5X0xvZyxsaW5lKQogICAgZW5kCiAgICByZXR1cm4gbmlsCmVuZAoKZnVuY3Rpb24gQkdfRUVUX1JVX1YxMDhfU3RhdHVzKCkKICAgIGxvY2FsIHM9'
    'QkdfRUVUX1JVX1YxMDgKICAgIHJldHVybiB7ZW5hYmxlZD1zLmVuYWJsZWQsIG5hdGl2ZV9yZWFkX2F1dGhvcml6ZWQ9cy5uYXRpdmVfcmVhZF9hdXRob3Jp'
    'emVkLAogICAgICAgIG1heF9zYW1wbGVzPXMubWF4X3NhbXBsZXMsIHNlZW49cy5zZWVuLCBlbWl0dGVkPXMuZW1pdHRlZCwKICAgICAgICB3ZWFwb25fcmVm'
    'c192ZXJpZmllZD1zLndlYXBvbl9yZWZzX3ZlcmlmaWVkLAogICAgICAgIGxhdW5jaGVyX3JlZnNfdmVyaWZpZWQ9cy5sYXVuY2hlcl9yZWZzX3ZlcmlmaWVk'
    'LAogICAgICAgIGFtbW9fdmVyaWZpZWQ9ZmFsc2UsIG1pc3Nlc192ZXJpZmllZD1mYWxzZSwgam91cm5hbF9tYXBwaW5nX3ZlcmlmaWVkPWZhbHNlfQplbmQK'
)

def v108_pilot_source():
    b = base64.b64decode(V108_LUA_SOURCE_B64)
    if digest(b) != V108_LUA_SOURCE_SHA256: raise RuntimeError('V108_LUA_PIN_SHA_MISMATCH')
    if b.count(b'    enabled = false, -- MUST remain off until a separately authorized install') != 1:
        raise RuntimeError('V108_SOURCE_NOT_DISABLED_BY_DEFAULT')
    if b.count(b'    native_read_authorized = false,') != 1:
        raise RuntimeError('V108_SOURCE_WITHOUT_NATIVE_GUARD')
    return b

def v108_candidate(v106_exact):
    if digest(v106_exact)!=V108_BASIS_SHA['EEex_scripts/BG_EET_RU_WeaponObserver.lua']:
        raise RuntimeError('V108_EXACT_V106_SOURCE_SHA_REQUIRED')
    source=v108_pilot_source()
    source=source.replace(b'    enabled = false, -- MUST remain off until a separately authorized install',
                          b'    enabled = true, -- enabled only after exact typed approval and pinned SHA preflight')
    source=source.replace(b'    native_read_authorized = false,',
                          b'    native_read_authorized = true,')
    if source.count(b'    native_read_authorized = true,')!=1:
        raise RuntimeError('V108_AUTHORIZATION_FLAG_PATCH_FAILED')
    candidate=v106_exact+b'\n'+source
    if candidate.count(b'BG_EET_RU_V108 = {')!=1 or candidate.count(b'function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)')!=v106_exact.count(b'function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)')+1:
        raise RuntimeError('V108_CANDIDATE_NOT_SINGLE_APPEND')
    return candidate

def v108_get_state():
    if not V108_STATE.exists(): return None
    if V108_STATE.is_symlink() or not V108_STATE.is_file() or V108_STATE.stat().st_size>16000:
        raise RuntimeError('V108_STATE_FILE_UNSAFE')
    obj=json.loads(V108_STATE.read_text('utf8'))
    if obj.get('schema')!=V108_SCHEMA or obj.get('phase') not in ('PREPARED','INSTALLED','ROLLED_BACK'):
        raise RuntimeError('V108_STATE_NOT_RECOGNIZED')
    return obj

def v108_put_state(game,data):
    safe_external(Path(game),V108_STATE)
    if V108_STATE.is_symlink() or data.get('schema')!=V108_SCHEMA:
        raise RuntimeError('V108_STATE_PATH_OR_SCHEMA_UNSAFE')
    V108_STATE.parent.mkdir(parents=True,exist_ok=True)
    stage=V108_STATE.with_name(V108_STATE.name+'.stage')
    if stage.exists():raise RuntimeError('V108_STATE_STAGE_COLLISION')
    try:
        with stage.open('x',encoding='utf8') as o: json.dump(data,o,ensure_ascii=False,indent=2)
        if json.loads(stage.read_text('utf8'))!=data:
            raise RuntimeError('V108_STATE_STAGING_VERIFICATION_FAILED')
        os.replace(stage,V108_STATE)
    finally:
        if stage.exists():stage.unlink()

def v108_preflight(game,installed=False):
    game=Path(game)
    status=v106_get_state()
    if not status or status.get('phase')!='INSTALLED':
        raise RuntimeError('V108_V106_BASELINE_NOT_INSTALLED')
    p=v106_preflight(game,installed=True)
    if p['expected_main_sha256']!=V108_BASIS_SHA['EEex_scripts/EEex_Main.lua']:
        raise RuntimeError('V108_MAIN_SOURCE_SHA_MISMATCH')
    if p['original_sha256']!=v105_get_state()['module_sha256']:
        raise RuntimeError('V108_V105_BASELINE_DRIFT')
    target=p['target']
    if target.is_symlink() or not target.is_file():raise RuntimeError('V108_TARGET_UNSAFE')
    current=target.read_bytes()
    if not installed and digest(current)!=V108_BASIS_SHA['EEex_scripts/BG_EET_RU_WeaponObserver.lua']:
        raise RuntimeError('V108_EXPECTED_V106_MODULE_DRIFT')
    fingerprints=v107_probe_files(game)
    for rel,expected in V108_BASIS_SHA.items():
        if rel=='EEex_scripts/BG_EET_RU_WeaponObserver.lua' and installed:
            continue
        info=fingerprints.get(rel,{})
        if info.get('sha256')!=expected or info.get('status')!='FINGERPRINTED':
            raise RuntimeError('V108_NATIVE_ABI_FINGERPRINT_HOLD:'+rel)
    if status['candidate_sha256']!=V108_BASIS_SHA['EEex_scripts/BG_EET_RU_WeaponObserver.lua']:
        raise RuntimeError('V108_V106_STATE_CANDIDATE_SHA_MISMATCH')
    if digest(p['target'].parent.joinpath('EEex_Main.lua').read_bytes())!=V108_BASIS_SHA['EEex_scripts/EEex_Main.lua']:
        raise RuntimeError('V108_MAIN_CHANGED_AFTER_FINGERPRINT')
    if installed:
        return {'target':target,'actual_sha256':digest(current),
                'expected_original_sha256':V108_BASIS_SHA['EEex_scripts/BG_EET_RU_WeaponObserver.lua']}
    candidate=v108_candidate(current)
    return {'target':target,'original':current,'candidate':candidate,
            'original_sha256':digest(current),'candidate_sha256':digest(candidate)}

def v108_capture_parse(game,log_path):
    path=Path(log_path)
    safe_external(Path(game),path)
    if path.is_symlink() or not path.is_file():return {'status':'V108_CAPTURE_MISSING'}
    if path.stat().st_size>8_000_000:return {'status':'V108_CAPTURE_OVERSIZE_HOLD'}
    lines=path.read_bytes().decode('utf8','replace').splitlines()
    matching=[]
    for line in lines:
        idx=line.find(V108_PREFIX)
        if idx>=0 and len(matching)<24:
            matching.append(line[idx:idx+1600])
    events=[x for x in matching if x.startswith(V108_PREFIX+' EVENT')]
    return {'status':'V108_NATIVE_RESREF_CALLBACK_EVENTS_CAPTURED' if events else 'V108_NO_RUNTIME_EVENTS_YET',
            'source_log_sha256':digest(path.read_bytes()),'event_lines':len(events),'samples':matching,
            'actual_weapon_resref_to_be_validated':bool(events),
            'ammunition_verified':False,'misses_verified':False,'journal_row_verified':False}

def v108_zip_report(game,path,report):
    game=Path(game);path=Path(path)
    safe_external(game,path)
    if path.is_symlink() or not path.is_file():raise RuntimeError('V108_CANONICAL_ZIP_UNSAFE')
    with zipfile.ZipFile(path) as src:
        names=src.namelist()
        if src.testzip() is not None or len(names)!=len(set(names)):
            raise RuntimeError('V108_PRIOR_ZIP_INVALID')
        old=json.loads(src.read(V108_ENTRY)) if V108_ENTRY in names else None
        if old==report:return False
    with tempfile.NamedTemporaryFile(dir=str(path.parent),prefix='.v108_',suffix='.zip',delete=False) as o:
        tmp=Path(o.name)
    try:
        with zipfile.ZipFile(path) as src,zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as dst:
            for info in src.infolist():
                if info.filename!=V108_ENTRY:dst.writestr(info,src.read(info))
            dst.writestr(V108_ENTRY,json.dumps(report,ensure_ascii=False,indent=2).encode('utf8'))
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() is not None or z.namelist().count(V108_ENTRY)!=1:
                raise RuntimeError('V108_ZIP_VERIFICATION_FAILED')
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()
    return True

def v108_run(game,report_path,mode='status'):
    report={'schema':V108_SCHEMA,'updater_version':SELF_VERSION,'mode':mode,
            'game_files_written':0,'gameplay_verified':False,
            'resref_verified':False,'ammo_verified':False,'misses_verified':False,
            'journal_row_verified':False,'errors':[],
            'prior_v106_events_not_repeated':True}
    try:
        if mode not in ('status','install','rollback','capture'):
            raise RuntimeError('V108_BAD_MODE')
        state=v108_get_state()
        if state and state['phase']=='PREPARED':
            # Partial transaction cannot be accepted as successful; do not guess.
            report['status']='V108_PREPARED_RECOVERY_HOLD'
            if mode=='rollback':
                closed,why=v71_processes_closed()
                if not closed:raise RuntimeError('V108_CLOSE_GAME_BEFORE_RECOVERY:'+why)
                proof=v108_preflight(game,installed=True)
                original_sha=state['original_sha256']; candidate_sha=state['candidate_sha256']
                if proof['actual_sha256'] not in (original_sha,candidate_sha):
                    raise RuntimeError('V108_PREPARED_SHA_UNKNOWN')
                backup=Path(state['backup_module'])
                safe_external(Path(game),backup)
                if backup.is_symlink() or not backup.is_file() or digest(backup.read_bytes())!=original_sha:
                    raise RuntimeError('V108_PREPARED_BACKUP_MISSING')
                if not v85_read_input_approval(V108_APPROVE_ROLLBACK):
                    report['status']='V108_ROLLBACK_NOT_AUTHORIZED'
                else:
                    if proof['actual_sha256']==candidate_sha:
                        v108_swap_exact(proof['target'],candidate_sha,backup.read_bytes(),original_sha)
                        report['game_files_written']=1
                    v108_put_state(game,{**state,'phase':'ROLLED_BACK','recovered_utc':now()})
                    report['status']='V108_PREPARED_ROLLED_BACK_EXACT_V106'
        elif state and state['phase']=='INSTALLED':
            proof=v108_preflight(game,installed=True)
            if proof['actual_sha256']!=state['candidate_sha256'] or proof['expected_original_sha256']!=state['original_sha256']:
                raise RuntimeError('V108_INSTALLED_MODULE_SHA_DRIFT')
            report['status']='V108_INSTALLED_AWAITING_NATIVE_RESREF_CAPTURE'
            if mode=='rollback':
                closed,why=v71_processes_closed()
                if not closed:raise RuntimeError('V108_CLOSE_GAME_BEFORE_ROLLBACK:'+why)
                backup=Path(state['backup_module'])
                safe_external(Path(game),backup)
                if backup.is_symlink() or not backup.is_file() or digest(backup.read_bytes())!=state['original_sha256']:
                    raise RuntimeError('V108_BACKUP_INVALID')
                if v85_read_input_approval(V108_APPROVE_ROLLBACK):
                    v108_swap_exact(proof['target'],state['candidate_sha256'],backup.read_bytes(),state['original_sha256'])
                    v108_put_state(game,{**state,'phase':'ROLLED_BACK','rolled_back_utc':now()})
                    report['game_files_written']=1
                    report['status']='V108_ROLLED_BACK_EXACT_V106'
                else:report['status']='V108_ROLLBACK_NOT_AUTHORIZED'
            elif mode=='capture':
                capture=v106_capture_console(game,v106_get_state())
                report['v106_capture_process_status']=capture['status']
                if capture.get('log_path'):
                    report['console_evidence']=v108_capture_parse(game,capture['log_path'])
                    report['status']=report['console_evidence']['status']
                else:report['status']='V108_CAPTURE_NO_LOG'
            elif mode=='install':report['status']='V108_ALREADY_INSTALLED_NO_WRITES'
            if mode=='status':
                prior=v106_get_state()
                if prior and prior.get('last_console_log'):
                    closed,_=v71_processes_closed()
                    if closed:
                        report['console_evidence']=v108_capture_parse(game,prior['last_console_log'])
        elif mode in ('rollback','capture'):
            report['status']='V108_NOT_INSTALLED_NO_ACTION'
        else:
            pre=v108_preflight(game)
            report.update({'status':'V108_GUARDED_PREFLIGHT_PASS_NATIVE_UNINSTALLED',
                'module_baseline_sha256':pre['original_sha256'],
                'candidate_sha256':pre['candidate_sha256'],
                'game_write_scope':'EEex_scripts/BG_EET_RU_WeaponObserver.lua ONLY',
                'requires_user_typed_approval':True,
                'native_crash_risk':'PCALL_DOES_NOT_PREVENT_NATIVE_CRASH'})
            if mode=='install':
                closed,why=v71_processes_closed()
                if not closed:raise RuntimeError('V108_CLOSE_GAME_BEFORE_INSTALL:'+why)
                if not v85_read_input_approval(V108_APPROVE_INSTALL):
                    report['status']='V108_INSTALL_NOT_AUTHORIZED'
                else:
                    again=v108_preflight(game)
                    if again['original_sha256']!=pre['original_sha256'] or again['candidate_sha256']!=pre['candidate_sha256']:
                        raise RuntimeError('V108_PREFLIGHT_CHANGED_AFTER_APPROVAL')
                    closed,why=v71_processes_closed()
                    if not closed:raise RuntimeError('V108_GAME_STARTED_AFTER_APPROVAL:'+why)
                    safe_external(Path(game),WORKDIR/'SAFE_BACKUPS')
                    backups=WORKDIR/'SAFE_BACKUPS';backups.mkdir(parents=True,exist_ok=True)
                    backup=backups/('BG_EET_RU_V108_BEFORE_'+pre['original_sha256'][:16]+'.lua.bak')
                    if backup.is_symlink():raise RuntimeError('V108_BACKUP_SYMLINK')
                    if not backup.exists():
                        with backup.open('xb') as o:o.write(pre['original'])
                    if not backup.is_file() or digest(backup.read_bytes())!=pre['original_sha256']:
                        raise RuntimeError('V108_BACKUP_VERIFY_FAILED')
                    record={'schema':V108_SCHEMA,'phase':'PREPARED',
                        'original_sha256':pre['original_sha256'],
                        'candidate_sha256':pre['candidate_sha256'],
                        'backup_module':str(backup),'created_utc':now()}
                    v108_put_state(game,record)
                    try:
                        v108_swap_exact(pre['target'],pre['original_sha256'],pre['candidate'],pre['candidate_sha256'])
                        v108_put_state(game,{**record,'phase':'INSTALLED','installed_utc':now()})
                        report['game_files_written']=1
                        report['status']='V108_INSTALLED_NATIVE_CAPTURE_REQUIRED'
                    except Exception:
                        # Never blindly overwrite an unknown SHA. Preserve PREPARED for deliberate recovery.
                        current=digest(pre['target'].read_bytes()) if pre['target'].is_file() else ''
                        if current==pre['candidate_sha256']:
                            v108_swap_exact(pre['target'],pre['candidate_sha256'],pre['original'],pre['original_sha256'])
                        if pre['target'].is_file() and digest(pre['target'].read_bytes())==pre['original_sha256']:
                            v108_put_state(game,{**record,'phase':'ROLLED_BACK','failed_utc':now()})
                        raise
    except (OSError,RuntimeError,ValueError,TypeError,KeyError,zipfile.BadZipFile) as exc:
        report['status']='V108_SAFE_STOP'
        report['errors'].append({'type':type(exc).__name__,'message':str(exc)[:200]})
    try:v108_zip_report(game,report_path,report)
    except (OSError,RuntimeError,ValueError,zipfile.BadZipFile) as exc:
        print('V108_ZIP_SAFE_STOP',type(exc).__name__,str(exc)[:180]);return 2
    print('V108:',report['status'],'| game files written:',report['game_files_written'])
    return 2 if report['status']=='V108_SAFE_STOP' else 0

def v108_swap_exact(target,expected_old_sha,desired,desired_sha):
    if target.is_symlink() or not target.is_file() or digest(target.read_bytes())!=expected_old_sha:
        raise RuntimeError('V108_SWAP_LIVE_FILE_CHANGED')
    if digest(desired)!=desired_sha:raise RuntimeError('V108_SWAP_SOURCE_SHA_INVALID')
    stage=target.with_name(target.name+'.v108stage')
    if stage.exists():raise RuntimeError('V108_STAGE_COLLISION')
    try:
        with stage.open('xb') as o:o.write(desired)
        if digest(stage.read_bytes())!=desired_sha:raise RuntimeError('V108_STAGE_SHA_INVALID')
        if digest(target.read_bytes())!=expected_old_sha:raise RuntimeError('V108_SWAP_RACE_HOLD')
        os.replace(stage,target)
        if digest(target.read_bytes())!=desired_sha:raise RuntimeError('V108_SWAP_VERIFY_FAILED')
    finally:
        if stage.exists():stage.unlink()

def v108_selftest():
    source=v108_pilot_source()
    assert b'    enabled = false,' in source and b'    native_read_authorized = false,' in source
    assert b'EEex_Sprite_AddAlterBaseWeaponDamageListener(' not in source
    assert b'context.weapon' in source and b'context.launcher' in source
    assert all(len(v)==64 for v in V108_BASIS_SHA.values())
    assert len(V108_LUA_SOURCE_SHA256)==64
    # Exact V106 source is data-derived; never let a different module pass.
    with tempfile.TemporaryDirectory(prefix='BG_EET_RU_V108_TEST_') as td:
        root=Path(td);game=root/'game';game.mkdir()
        p=root/'one.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('keep.txt',b'preserved')
        report={'status':'V108_TEST','schema':V108_SCHEMA}
        assert v108_zip_report(game,p,report)
        before=digest(p.read_bytes())
        assert not v108_zip_report(game,p,report)
        assert digest(p.read_bytes())==before
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None and z.read('keep.txt')==b'preserved'
        f=root/'module.lua';f.write_bytes(b'original')
        original_sha=digest(f.read_bytes())
        candidate=b'candidate';candidate_sha=digest(candidate)
        v108_swap_exact(f,original_sha,candidate,candidate_sha)
        assert f.read_bytes()==candidate
        v108_swap_exact(f,candidate_sha,b'original',original_sha)
        assert f.read_bytes()==b'original'
        try:v108_swap_exact(f,candidate_sha,b'bad',digest(b'bad'))
        except RuntimeError:pass
        else:raise AssertionError('V108_SHA_GATE_FAILED_TO_STOP')
    return True
