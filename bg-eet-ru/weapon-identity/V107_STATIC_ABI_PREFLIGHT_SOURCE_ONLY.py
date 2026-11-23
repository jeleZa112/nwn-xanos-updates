# V107 source-only body for the existing single BG_EET_RU_UPDATE.cmd.
# READ ONLY for all files inside the installed EET; only external canonical ZIP may change.
V107_SCHEMA = 'BG_EET_RU_V107_CITEM_STATIC_ABI_PREFLIGHT'
V107_ENTRY = '53_V107_CITEM_STATIC_ABI_PREFLIGHT.json'
V107_EXPECTED_FILES = {
    'EEex_scripts/EEex_Sprite.lua': '4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28',
    'EEex_scripts/EEex_Sprite_Patch.lua': 'e301b46770477cf29e3d39d6591a5a9fba4f3aeafa03c3dbfa75f7ef6bc13b7',
}
V107_PROBE_FILES = (
    'EEex.dll', 'InfinityLoader.exe', 'InfinityLoader.dll', 'EEex/EEex.dll',
    'Baldur.exe', 'EEex_scripts/EEex_Main.lua',
    'EEex_scripts/BG_EET_RU_WeaponObserver.lua',
    'EEex_scripts/EEex_Sprite.lua', 'EEex_scripts/EEex_Sprite_Patch.lua',
)

def v107_probe_files(game):
    game = Path(game)
    results = {}
    for relative in V107_PROBE_FILES:
        item = game.joinpath(*relative.split('/'))
        if item.is_symlink() or not item.is_file():
            results[relative] = {'status': 'SYMLINK_HOLD' if item.is_symlink() else 'ABSENT'}
            continue
        try:
            st = item.stat()
            if st.st_size > 200_000_000:
                results[relative] = {'status': 'SIZE_LIMIT_HOLD', 'size_bytes': st.st_size}
                continue
            # Read-only fingerprint; avoid retaining native pointers or loading DLL.
            with item.open('rb') as stream:
                h = hashlib.sha256()
                total = 0
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > 200_000_000:
                        raise RuntimeError('V107_SIZE_CHANGED_DURING_READ')
                    h.update(chunk)
            if item.is_symlink() or item.stat().st_size != total:
                results[relative] = {'status': 'RACE_OR_LINK_HOLD'}
                continue
            sha = h.hexdigest()
            rec = {'status': 'FINGERPRINTED', 'size_bytes': total, 'sha256': sha}
            expected = V107_EXPECTED_FILES.get(relative)
            if expected:
                rec['matches_v104_captured_source_sha256'] = sha == expected
            results[relative] = rec
        except (OSError, RuntimeError, ValueError) as exc:
            results[relative] = {'status': 'ERROR_HOLD', 'error_type': type(exc).__name__}
    return results

def v107_static_report(game):
    result = {
        'schema': V107_SCHEMA,
        'updater_version': SELF_VERSION,
        'scope': 'STATIC_READ_ONLY_NO_NATIVE_API_CALLS',
        'game_files_written': 0,
        'runtime_native_resref_proven': False,
        'callback_item_lifetime_proven': False,
        'misses_verified': False,
        'ammunition_resref_verified': False,
        'combat_journal_correlation_verified': False,
        'files': v107_probe_files(game),
        'release_gate': 'HOLD_V107_NATIVE_ABI_AND_CALLBACK_LIFETIME',
    }
    state = v106_get_state()
    if state and state.get('phase') == 'INSTALLED':
        # Read state only; do not launch or modify game.
        result['v106_installed_state_present'] = True
        result['v106_module_state_sha256'] = state.get('candidate_sha256')
    else:
        result['v106_installed_state_present'] = False
    results = result['files']
    result['v104_sprite_source_sha_match'] = all(
        results.get(key, {}).get('matches_v104_captured_source_sha256') is True
        for key in V107_EXPECTED_FILES
    )
    result['status'] = 'V107_STATIC_FINGERPRINT_READY_NATIVE_READ_HOLD'
    return result

def v107_save_report(game, report_path, report):
    game = Path(game)
    report_path = Path(report_path)
    safe_external(game, report_path)
    if report_path.is_symlink() or not report_path.is_file():
        raise RuntimeError('V107_CANONICAL_ZIP_MISSING_OR_UNSAFE')
    with zipfile.ZipFile(report_path) as z:
        names = z.namelist()
        if z.testzip() is not None or len(names) != len(set(names)):
            raise RuntimeError('V107_CANONICAL_ZIP_BAD_CRC_OR_DUPLICATE')
        previous = json.loads(z.read(V107_ENTRY)) if V107_ENTRY in names else None
        if previous == report:
            return False
    with tempfile.NamedTemporaryFile(dir=str(report_path.parent), prefix='.v107_', suffix='.zip', delete=False) as out:
        tmp = Path(out.name)
    try:
        with zipfile.ZipFile(report_path) as src, zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=7) as dst:
            for info in src.infolist():
                if info.filename != V107_ENTRY:
                    dst.writestr(info, src.read(info))
            dst.writestr(V107_ENTRY, json.dumps(report, ensure_ascii=False, indent=2).encode('utf8'))
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() is not None or z.namelist().count(V107_ENTRY) != 1:
                raise RuntimeError('V107_ZIP_RECHECK_FAILED')
        os.replace(tmp, report_path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return True

def v107_run(game, report_path):
    try:
        report = v107_static_report(game)
        changed = v107_save_report(game, report_path, report)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print('V107_SAFE_STOP:', type(exc).__name__, str(exc)[:200])
        return 2
    print('V107:', report['status'], '| game writes: 0 | ZIP updated:', changed)
    return 0

def v107_selftest():
    with tempfile.TemporaryDirectory(prefix='BG_EET_RU_V107_TEST_') as tmp:
        root = Path(tmp)
        game = root / 'game'
        game.mkdir()
        scripts = game / 'EEex_scripts'
        scripts.mkdir()
        (scripts / 'EEex_Sprite.lua').write_bytes(b'function EEex_Sprite_AddAlterBaseWeaponDamageListener() end')
        (scripts / 'EEex_Sprite_Patch.lua').write_bytes(b'-- source')
        (game / 'Baldur.exe').write_bytes(b'MZ' + b'\0' * 128)
        report = root / 'SEND_TO_CHATGPT_BG_EET_RU.zip'
        with zipfile.ZipFile(report, 'w') as z:
            z.writestr('keep.txt', b'preserved')
        evidence = v107_static_report(game)
        assert evidence['status'] == 'V107_STATIC_FINGERPRINT_READY_NATIVE_READ_HOLD'
        assert not evidence['runtime_native_resref_proven']
        assert evidence['game_files_written'] == 0
        assert not evidence['v104_sprite_source_sha_match']
        assert evidence['files']['Baldur.exe']['status'] == 'FINGERPRINTED'
        assert v107_save_report(game, report, evidence)
        prior_hash = digest(report.read_bytes())
        assert not v107_save_report(game, report, evidence)
        assert digest(report.read_bytes()) == prior_hash
        with zipfile.ZipFile(report) as z:
            assert z.testzip() is None and z.read('keep.txt') == b'preserved'
            assert z.namelist().count(V107_ENTRY) == 1
        # A symlink never becomes a game file read.
        try:
            (game / 'EEex.dll').symlink_to(game / 'Baldur.exe')
        except (OSError, NotImplementedError):
            pass
        else:
            assert v107_probe_files(game)['EEex.dll']['status'] == 'SYMLINK_HOLD'
    return True