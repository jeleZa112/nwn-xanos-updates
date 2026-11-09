#!/usr/bin/env python3
"""BGXAI 055: independent real WeiDU v251 BAF grammar smoke on CI.

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

BAF_SHA256 = '10c625ecb516e676d5ea264665f186d5f2a16a6809f88e569a7023b65d2e414c'
RELEASE_URL = 'https://github.com/WeiDUorg/weidu/releases/download/v251.00/'
ASSETS = {
    'Linux': ('WeiDU-Linux-251.zip', 2723764, 'weidu'),
    'Windows': ('WeiDU-Windows-251.zip', 2322613, 'weidu.exe'),
}
REPO_ROOT = Path(__file__).resolve().parents[3]  # root of GitHub checkout
SOURCE_REPO_PATH = 'BGXAI/fox_new/release_054/BGX52_guard_receiver_PREVIEW.baf'
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
    with tempfile.TemporaryDirectory(prefix='BGXAI_055_REAL_WEIDU_') as tmp:
        root = Path(tmp)
        baf = root/'BX52CHK.baf'
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
        report['status'] = 'REAL_WEIDU_BAF_GRAMMAR_PASS' if parsed.returncode == 0 and success and not failure else 'REAL_WEIDU_BAF_GRAMMAR_FAILED'
        return report


if __name__ == '__main__':
    try:
        result = real_weidu_smoke()
    except Exception as e:
        result = {'status': 'CI_ERROR', 'error': type(e).__name__, 'detail': str(e)[:400],
                  'game_files_accessed': False, 'installation_performed': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['status'] == 'REAL_WEIDU_BAF_GRAMMAR_PASS' else 1)
