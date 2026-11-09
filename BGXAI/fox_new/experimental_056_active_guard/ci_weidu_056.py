#!/usr/bin/env python3
"""BGXAI 056: independent real WeiDU v251 BCS integration test on CI.

No game files, installation, TP2, or account credentials are needed.
Downloads the public WeiDU 251 release for the runner OS, verifies the
release asset byte size, and executes --nogame --parse-check BAF in temp.
Full EET IDS compilation is NOT demonstrated by this grammar check.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

BAF_SHA256 = 'b8309fdfd903fb6a0c50cd14fb687b862ac06fb8bbd79a26c9324fd0908b5d88'
RELEASE_URL = 'https://github.com/WeiDUorg/weidu/releases/download/v251.00/'
ASSETS = {
    'Linux': ('WeiDU-Linux-251.zip', 2723764, 'weidu'),
    'Windows': ('WeiDU-Windows-251.zip', 2322613, 'weidu.exe'),
}
REPO_ROOT = Path(__file__).resolve().parents[3]  # root of GitHub checkout
SOURCE_REPO_PATH = 'BGXAI/fox_new/experimental_056_active_guard/BGX56/BGX56_RECEIVER.baf'
TP2_REPO_PATH = 'BGXAI/fox_new/experimental_056_active_guard/BGX56/setup-BGX56.tp2'
IDS_DIR = Path(__file__).resolve().parent/'ids'


def real_weidu_smoke() -> dict:
    osname = platform.system()
    if osname not in ASSETS:
        raise RuntimeError(f'Unsupported CI platform: {osname}')
    filename, expected_size, binary_name = ASSETS[osname]
    # git show returns the exact repository blob; checkout may CRLF-convert BAF on Windows.
    canonical = subprocess.run(['git','show','HEAD:'+SOURCE_REPO_PATH],
                               cwd=REPO_ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=12, check=True).stdout
    if hashlib.sha256(canonical).hexdigest() != BAF_SHA256:
        raise RuntimeError('Canonical Git BAF blob does not match pinned SHA256')
    with tempfile.TemporaryDirectory(prefix='BGXAI_056_REAL_WEIDU_') as tmp:
        root = Path(tmp)
        baf = root/'BX56CHCK.baf'
        baf.write_bytes(canonical)
        archive = root/filename
        with urllib.request.urlopen(RELEASE_URL + filename, timeout=45) as response:
            with archive.open('wb') as out:
                while chunk := response.read(256 * 1024):
                    out.write(chunk)
        if archive.stat().st_size != expected_size:
            raise RuntimeError('Official WeiDU release asset unexpected size')
        with zipfile.ZipFile(archive) as z:
            choices = [i for i in z.infolist() if not i.is_dir()
                       and Path(i.filename.replace('\\', '/')).name.casefold() == binary_name.casefold()]
            if len(choices) != 1:
                raise RuntimeError(f'WeiDU release did not contain one {binary_name}: {[i.filename for i in choices]}')
            tool = root/binary_name
            tool.write_bytes(z.read(choices[0]))
        if osname != 'Windows':
            tool.chmod(0o700)

        report = {
            'status': 'NOT_TESTED', 'platform': osname,
            'release': filename, 'asset_size_verified': True,
            'tool_sha256': hashlib.sha256(tool.read_bytes()).hexdigest(),
            'BAF_SHA256_verified': True, 'game_files_accessed': False,
            'installation_performed': False,
        }
        safe_flags = ['--nogame', '--no-auto-tp2', '--no-exit-pause', '--noautoupdate']
        version = subprocess.run([str(tool), *safe_flags, '--version'], cwd=root,
                                 input='', text=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=20, check=False)
        report['version_exit'] = version.returncode
        report['version_output'] = version.stdout[-1000:]
        if version.returncode != 0 or not re.search(r'251(?:00|\.00)', version.stdout, re.I):
            report['status'] = 'VERSION_FAILED'
            return report
        parsed = subprocess.run([str(tool), *safe_flags, '--search-ids', str(IDS_DIR),
                                 '--search', str(IDS_DIR), '--script-style', 'BG2',
                                 '--parse-check', 'BAF', str(baf)],
                                cwd=root, input='', text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=25, check=False)
        report['parse_exit'] = parsed.returncode
        report['ids_fixture'] = 'IESDP_BGEE_SIGNATURE_SUBSET_NOT_FULL_EET'
        report['parse_output'] = parsed.stdout[-3200:]
        success = 'successfully parsed as type [BAF]' in parsed.stdout
        failure = 'NOT successfully parsed as type [BAF]' in parsed.stdout
        if not (parsed.returncode == 0 and success and not failure):
            report['status'] = 'REAL_WEIDU_BAF_GRAMMAR_FAILED'
            return report
        # Parse the EXACT two-file WeiDU TP2 with the REAL WeiDU 251 binary.
        tp2_canonical = subprocess.run(['git','show','HEAD:'+TP2_REPO_PATH],
                       cwd=REPO_ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                       timeout=12,check=True).stdout
        tp2_file = root/'setup-BGX56.tp2'
        tp2_file.write_bytes(tp2_canonical)
        tp2 = subprocess.run([str(tool), *safe_flags, '--parse-check','TP2',str(tp2_file)],
                     cwd=root,input='',text=True,stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,timeout=25,check=False)
        report['tp2_parse_exit']=tp2.returncode
        report['tp2_parse_output']=tp2.stdout[-900:]
        if tp2.returncode!=0 or 'successfully parsed as type [TP2]' not in tp2.stdout \
            or 'NOT successfully parsed' in tp2.stdout:
            report['status']='REAL_WEIDU_TP2_GRAMMAR_FAILED'
            return report
        # Same real WeiDU binary, isolated BCS generation with only public IDS
        # fixture. This is a *synthetic* compile, NOT validation against EET.
        out = root/'bcs_output'
        out.mkdir()
        compiled = subprocess.run([str(tool), *safe_flags,
                                   '--search-ids', str(IDS_DIR),
                                   '--search', str(IDS_DIR),
                                   '--script-style', 'BG2',
                                   '--out', str(out), str(baf)],
                                  cwd=root, input='', text=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, timeout=25, check=False)
        report['compile_exit'] = compiled.returncode
        report['compile_output'] = compiled.stdout[-3000:]
        candidates = [f for f in out.rglob('*') if f.is_file()
                      and f.suffix.casefold() == '.bcs' and f.stem.casefold() == baf.stem.casefold()]
        if not candidates:
            candidates = [f for f in root.rglob('*') if f.is_file()
                          and f.suffix.casefold() == '.bcs' and f.stem.casefold() == baf.stem.casefold()]
        bad = bool(re.search(r'(?m)^\s*(?:FATAL ERROR:|ERROR:)', compiled.stdout))
        if compiled.returncode != 0 or bad or len(candidates) != 1 or candidates[0].stat().st_size == 0:
            report['status'] = 'REAL_WEIDU_BCS_COMPILE_FAILED'
            report['generated_bcs_files'] = [str(x.relative_to(root)) for x in candidates]
            return report
        output = candidates[0]
        data = output.read_bytes()
        report['compiler_output_sha256'] = hashlib.sha256(data).hexdigest()
        report['compiler_output_bytes'] = len(data)
        report['compiler_output_first8'] = data[:8].hex()
        # Validate ACTUAL compiled BCS: 8 blocks yield 16 CR delimiters
        # (opening and closing) in WeiDU's text-encoded BCS format.
        # Exact actions: 8 SetGlobal, 2 Continue, 6 ProtectObject,
        # 6 SetGlobalTimer. Do not confuse delimiters with block count.
        report['compiled_cr_delimiters'] = len(re.findall(rb'(?m)^(?:[0-9]+)?CR\r?$', data))
        action_ids = [int(x) for x in re.findall(rb'(?:^|\n)(?:[0-9]+)?AC\r?\n(-?[0-9]+)OB\r?\n', data)]
        counts = {str(k): action_ids.count(k) for k in (30, 36, 87, 115)}
        report['compiled_action_ids_counts'] = counts
        if report['compiled_cr_delimiters'] != 16 or len(action_ids) != 22 or counts != {'30':8,'36':2,'87':6,'115':6}:
            report['status'] = 'COMPILED_BCS_STRUCTURE_MISMATCH'
            report['action_ids_found'] = action_ids
            return report
        # Extra active-release proof: splice the 8 REAL compiled BCS blocks at
        # 1-based index 1032 in an offline synthetic 1057-block baseline.
        # Never touches any actual EET file, which is absent in CI.
        from BGXAI56_BUILDER import combine, segment
        def dummy_block(i):
            return (b'CR\nCO\n'+str(i).encode('ascii')+b'\nRS\n'
                    b'RP\n100\nAC\n0OB\nOB\nAC\nRS\nCR\n')
        baseline=b'SC\n'+b''.join(dummy_block(i) for i in range(1057))+b'SC\n'
        staged, proof=combine(baseline,data,strict=False)
        if proof['total_blocks']!=1065 or not proof['original_F_toggle_precedes_receiver']:
            report['status']='BCS_SPLICE_STRUCTURE_MISMATCH'
            return report
        report['splice']=proof
        report['status'] = 'REAL_WEIDU_BAF_BCS_AND_SPLICE_PASS'
        return report


if __name__ == '__main__':
    try:
        result = real_weidu_smoke()
    except Exception as e:
        result = {'status': 'CI_ERROR', 'error': type(e).__name__, 'detail': str(e)[:400],
                  'game_files_accessed': False, 'installation_performed': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['status'] == 'REAL_WEIDU_BAF_BCS_AND_SPLICE_PASS' else 1)
