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


def main():
    import json
    import sys
    try:
        report = analyze(fetch_pinned(0), fetch_pinned(1))
    except (OSError, ValueError, UnicodeError) as exc:
        report = {'status': 'UPSTREAM_SOURCE_FETCH_OR_PIN_HOLD',
                  'reason': f'{type(exc).__name__}: {str(exc)[:160]}',
                  'allowGameInstallation': False,
                  'userGameFilesWritten': 0}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get('sourceOnlyPass') is True else 2


if __name__ == '__main__':
    raise SystemExit(main())