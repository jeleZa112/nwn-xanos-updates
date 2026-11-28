"""Read-only, pinned upstream x64 CItem binding evidence for BG_EET_RU.

Does not load DLLs, touch a game, use native addresses, or enable any hooks.
Only corroborates SOURCE; installed EEex/LuaBindings ABI and callback lifetime remain HOLD.
"""
import hashlib
import re
import urllib.request

UPSTREAM = (
    ('Bubb13/InfinityLoader', '817925caab3eb9cf600cfaf38853da8d30c28247',
     'LuaBindings-v2.6.6.0/source/LuaBindings-v2.6.6.0/Generated/EEexLua_generated.cpp',
     'bd72b333c437d3bfb52703018085af6b95baf198', 14_303_385),
    ('Bubb13/EEex-Docs', '2b175c02656e12ba22fa56c311d564e41bd0cae4',
     'source/EE Game Structures (x64)/CI/index.rst',
     '3ae793d014a801f30df7a48dacab4ba0ff8d2149', 161_863),
)


def _git_blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\x00' + data).hexdigest()


def fetch_pinned(index):
    repo, commit, path, sha, size = UPSTREAM[index]
    url = f'https://raw.githubusercontent.com/{repo}/{commit}/{urllib.parse.quote(path, safe="/")}'
    with urllib.request.urlopen(url, timeout=35) as response:
        data = response.read(size + 1)
    if len(data) != size or _git_blob_sha(data) != sha:
        raise ValueError(f'UPSTREAM_PIN_MISMATCH:{index}')
    return data.decode('utf-8')


def analyze(generated_cpp, x64_struct):
    """Produce evidence, never runtime/installation approval."""
    if not isinstance(generated_cpp, str) or not isinstance(x64_struct, str):
        raise TypeError('SOURCE_TEXT_REQUIRED')
    # The EEex x64 structure table explicitly states the size, field and bit.
    start = x64_struct.find('.. _CItem:')
    if start < 0:
        raise ValueError('X64_CITEM_STRUCT_MISSING')
    item_doc = x64_struct[start:start + 8000]
    layout = bool(re.search(r'Size \(Total: 168\)', item_doc)
                  and re.search(r'\|\s*0x24\s*\|\s*4\s*\|\s*unsigned int\s*\|\s*m_flags\s*\|', item_doc)
                  and re.search(r'1 IDENTIFIED', item_doc))
    # Registering a tolua variable for CItem is the important extra proof:
    # it differs from merely having a field in a C++ header.
    module = re.search(r'tolua_beginmodule\([^\n]*["\']CItem["\']\)\s*;', generated_cpp)
    registration = ''
    if module:
        registration = generated_cpp[module.end():module.end() + 20000]
        # The generated registration closes with tolua_endmodule(L).
        end = re.search(r'tolua_endmodule\([^\n]*\)\s*;', registration)
        if end:
            registration = registration[:end.start()]
    registered = bool(re.search(r'tolua_variable\([^\n]*["\']m_flags["\']', registration))
    accessor = bool(re.search(r'tolua_get_[A-Za-z0-9_]*CItem[A-Za-z0-9_]*m_flags', generated_cpp))
    return {
        'schema': 'BG_EET_RU_V107_UPSTREAM_X64_CITEM_BINDING_SOURCE_V1',
        'sourceStructX64FlagsOffset24Bit0': layout,
        'sourceLuaCItemFlagsRegistered': registered,
        'sourceLuaCItemFlagsGetterPresent': accessor,
        'sourceOnlyPass': layout and registered and accessor,
        'userInstalledLuaBindingsShaKnown': False,
        'userCallbackWeaponFlagsLiveVerified': False,
        'userGameFilesWritten': 0,
        'newEngineHooks': 0,
        'allowGameInstallation': False,
        'status': 'UPSTREAM_SOURCE_PASS_USER_ABI_HOLD' if layout and registered and accessor
                  else 'SOURCE_BINDING_HOLD',
    }



# Official EEex v1.2.0, immutable release commit (2026-08-12).
# Both installed DLL *sizes* match this release; only exact SHA-256 can prove
# equality of bytes. Do not equate this evidence with callback pointer safety.
RELEASE_V120_COMMIT = '204040502ac920161d60046d90b766b8d2d08152'
RELEASE_V120_BINARIES = (
    ('EEex.dll', 'EEex/loader/v2.6.6.0/EEex.dll',
     1_282_048, '934553ccfb25a2fe89b4734667b18998adc9f4f5'),
    ('LuaBindings.dll', 'EEex/loader/v2.6.6.0/LuaBindings.dll',
     6_432_256, '4ff9d0d8c230b626eb6cb35489faec1140af2b2c'),
)


def compare_pinned_binary(data, expected_size, expected_gitsha, installed_sha256):
    """Pure byte comparison: wrong upstream bytes must NEVER yield a pass."""
    source_pin_ok = (len(data) == expected_size
                     and _git_blob_sha(data) == expected_gitsha)
    published_sha256 = hashlib.sha256(data).hexdigest()
    return {
        'pinnedSourceBytesVerified': source_pin_ok,
        'officialSha256': published_sha256 if source_pin_ok else None,
        'installedSha256MatchesOfficial': (
            source_pin_ok and published_sha256 == installed_sha256),
    }


def compare_release_v120(installed_eeex_sha256, installed_luabindings_sha256):
    """Compare official Git-pinned bytes with hashes from the V164 READ-ONLY ZIP.

    Downloads published upstream files into memory on the CI runner only:
    no local user DLLs are loaded, no game files are touched or changed.
    """
    expected = (installed_eeex_sha256, installed_luabindings_sha256)
    if any(not isinstance(sha, str) or
           not re.fullmatch(r'[0-9a-f]{64}', sha) for sha in expected):
        raise ValueError('INSTALLED_SHA256_ARGUMENT_INVALID')
    files = {}
    all_match = True
    for (name, path, size, gitsha), installed_sha in zip(RELEASE_V120_BINARIES, expected):
        url = ('https://raw.githubusercontent.com/Bubb13/EEex/'
               + RELEASE_V120_COMMIT + '/' + path)
        with urllib.request.urlopen(url, timeout=45) as response:
            data = response.read(size + 1)
        result = compare_pinned_binary(data, size, gitsha, installed_sha)
        files[name] = {'officialSize': size, 'officialGitBlobSha': gitsha,
                       'installedSha256': installed_sha, **result}
        all_match = all_match and result['installedSha256MatchesOfficial']
    return {
        'schema': 'BG_EET_RU_V107_USER_DLL_OFFICIAL_RELEASE_PROVENANCE_RO_V1',
        'upstreamRelease': 'Bubb13/EEex v1.2.0',
        'upstreamReleaseCommit': RELEASE_V120_COMMIT,
        'files': files,
        'userFilesExactlyMatchOfficialRelease': all_match,
        'callbackWeaponFlagsLifetimeVerified': False,
        'loadedRuntimeDLLVerified': False,
        'allowNativeRead': False,
        'allowGameInstallation': False,
        'gameFilesWritten': 0,
        'status': ('V107_OFFICIAL_V120_DLL_BYTES_MATCH_CALLBACK_HOLD' if all_match
                   else 'V107_DLL_PROVENANCE_MISMATCH_HOLD'),
    }


def main():
    import json
    import sys
    try:
        if len(sys.argv) == 4 and sys.argv[1] == '--compare-release-v120':
            report = compare_release_v120(sys.argv[2], sys.argv[3])
        elif len(sys.argv) == 1:
            report = analyze(fetch_pinned(0), fetch_pinned(1))
        else:
            raise ValueError('INVALID_SOURCE_AUDIT_ARGUMENTS')
    except (OSError, ValueError, UnicodeError) as exc:
        report = {'status': 'UPSTREAM_SOURCE_FETCH_OR_PIN_HOLD',
                  'reason': f'{type(exc).__name__}: {str(exc)[:160]}',
                  'allowGameInstallation': False,
                  'userGameFilesWritten': 0}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if (report.get('sourceOnlyPass') is True or
                 report.get('userFilesExactlyMatchOfficialRelease') is True) else 2


if __name__ == '__main__':
    raise SystemExit(main())