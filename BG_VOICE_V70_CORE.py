# BG Voice RU V70 workflow code only; data and private files remain on the user's PC.
# SHA-pinned, versioned component invoked by the one permanent BG_VOICE_UPDATE.cmd.
from __future__ import annotations

V70_CORE_VERSION = '1.0.0'


def selftest():
    assert V70_CORE_VERSION == '1.0.0'
    assert callable(run)
    print('BG_VOICE_V70_CORE_SELFTEST_PASS')
    return 0


def run(host, *, mode='stage', limit=None):
    # The host enforces all SHA, protected ID, calibration, staging and report checks.
    # No model inference, direct file writes, network requests or game modifications.
    if set(host) != {'run_local'} or not callable(host['run_local']):
        raise RuntimeError('V70_UNEXPECTED_HOST_CAPABILITIES')
    if mode not in ('stage', 'calibration'):
        raise RuntimeError('V70_UNRECOGNIZED_MODE')
    if limit is not None and (type(limit) is not int or limit < 1 or limit > 420):
        raise RuntimeError('V70_INVALID_LIMIT')
    return host['run_local'](mode=mode,limit=limit)


if __name__ == '__main__':
    raise SystemExit(selftest())
