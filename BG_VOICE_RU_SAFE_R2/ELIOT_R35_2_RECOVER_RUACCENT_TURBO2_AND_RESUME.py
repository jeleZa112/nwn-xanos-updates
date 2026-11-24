# -*- coding: utf-8 -*-
# ELIOT R35.2: repair ONE missing RUAccent turbo2 model; resume existing R35.1.
# Not a new updater: BG_VOICE_UPDATE.cmd remains the ONLY permanent updater.
# Protected files (game, previous WAVs, user voice, updater) are never changed by this helper.
from __future__ import annotations
import base64, gzip, hashlib, os, pathlib, subprocess, sys, textwrap

R35_1_SHA256 = "154b4c3f08ee7d9fafa6f185ea69693ec13f137a649dcbac0045bdf8a5df5749"
R35_1_B64 = (
    'H4sIAAAAAAAC/6S8V7PjSLIm+F6/IrfnIasW1QWt2qweIAlCSxJAz7U0SEJrRaztf19kVbJv992embWd83BOEohwj/Bw8bkz0v/b'
    'l7/+n3/9kvRp2b3+9mVd8r9S35/89N++COrdcL/YKP4b/Lcvc9IPWfpFEr/0XVN22ZdXtGRf8n76YntMkmTdAv75p6y/7P1UZ9P8'
    'xdDV4LeLkBPlWfP+MkRLUnwRfIZzv5TdvERNc1G86H+ZL95N9mUd0ovo9OuXvVyKL1s2lXl5jYijpF6HX78sRdZ9mbJlen8nqvdf'
    'smOZos+s374/eUVt9qW99pKXSbSUfTf/8fjJPL6kWZN9f/LbF77P5i9dv3yJ30M0z1/mZcquPxbz20/51Ldfvn3L12Wdsm/fvpTt'
    '0E/Ll6i7hv9J76cfj+Jozgjs1y+vs7yWVkRz0ZTxr1/6+dcv8/v6dW32zydL1g552WTX8zUepj65eP3J5/uyl/Ja8A+Sn8/XnOv3'
    '2XfZTz9d0vlm2PfbXWfUb47EfPn9y19QGo2QJIezGEEIjKJJKMriPCNJMkshmIhJDCFiFEsSIo0iOqexHMVyCo5QNM5SOib+8q9U'
    'b+E3lsAuwj//9OX6+Sph853584cDySdFBGT8VO8rMAHZvaYX/Xbw8WCWihjmIMBqTnGIXnEiaMVgJ2jML3BbG7zO3gv82Dwq7xWK'
    'CYngGVBPRcw0//06wWOfpzKa8KTPbRQmI3kjp69/sm9V33WA1Azy4L044NH0tIuO1iaaYNMHPQRQvnPT5drEHjCtZv7QwQO2PZsS'
    'y6MYkNtsaMm3DJZYqm0geCv15QHEZs4H6FMrSMpI0sTwjj2VISknHuSbSjxzJ1/kD/ZwRaU8wPmwTZnTYhyaRXYPYHjlePsG7qg4'
    'wIDTR3C+dYeMt3WGlXTubyrRZJmKHkcMcs3Wgjc/htbQRMKH1O0ayEu3+g4OGkABy2pKiU2BUpeS2emKaZjXj/w4frDv7voaaTom'
    'qVRGcVPU6PmRgnGOojQF5ncqNR21f0yodTxvlkQCuvvqzFWSLI+pvUAWBMm+Jff3neMsed85FmI44mUK4msRKzkJnJLhzSQ4OHD1'
    'NKBh7i8SBJImWX6wp475BPWStQRHK/BUfXFmpwkyjw0qkxdHYXbxTShs9ixyqtK0F/MguQTfLSxvH4IQ0jeGtEhq73mzo0aM0+5b'
    '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'
    'lz8ol/9Y5Xcev/wfv//X5gh/LuD7zxSVc/bFXrvvnRSEaeqnn7/+y2jGdQXHZdy7oX8Tmbsq8F//ZNLNv/9fX79966I2+/bt69++'
    'Zk3ZL9/3923K8mzKuiT7+us14HtLhz8G/D1r4yxNs/Tbp2HFv47+j6//9x+EsyNLfv4ujmviHxv47SOIP3pufP3l16//Mu+34X0x'
    '+j7retXN/xDBz9382ytbfv7qGJ7NCd/3/fWSxdcYziM6yuKYztMcSxEExkjiQpJYniQxhuAxQkEZhaD49SQjcoSGrqQLRyIKhiIk'
    'QaGv12n+Q34fHrbhuf/JgrzoYAidkcnlN0jswjX498oJGmUpEREwcfk6DKaupAOFaIhK4CynE/j7QBT/3nwC//rL//qE1LsuMDfh'
    'm3Z3NMblpB/H8kMnu/mnn3RB4FXh95/jv/Tzb1m3lVPf/f2rJH6TPPabIYrfKXz9j0sFv8Jf//v037u//IPnv85wbUZ3RMPWBNv5'
    'r/P+8stPtmCqDCdogu7+/mdnjPgv3/5TG/7sgvLtz1Yn35tn/CfpP0X3R/eUb9+3BH8z9O/Ev2kGL1yKKrie+fWXL7//welL1KWf'
    'NcZ/+f77569//esffP568fnrtEZ/tFX565+cvn4pu+8NRn6Lptd2ndiXfxkc/ejA8u8G//LLf7L5XwnuUoZL0/6Hu82a6+i+S/ff'
    'Evwfy/X/I9m//PTLb1M2NFGS/RxfTL7+Gv9xkF9/eJ0/7Oz97Y92Mpe19dO3jx/6eYr277byt4+xXJ9/S/pLyX7+p+P85fff4e9i'
    '/6e3f+rU9QL6Tw39EP39+7DPev6JzK9/TvoV/uUfUy6O3fz3r+X8LTui5I89fv2Pnz+E/kn7/0mlf/4aNVMWpe+//tjQ11//wfrX'
    '70v8k/wltPzfLfi/7uRf9wn98fbfrOk73X8yxs9S8stXF19//S7Gf971j53+8+bhH07539mxpyu68dS/eSbPuIL9TTJU/ptufDO/'
    'G/SXr8APL/59DT+O9B8+9BJAUn/73v+nX5dv+1Qu2fyJLP/ti3tN+/LHNr7E7yX7khRRd5H6Y5N5E73++qNL0Q9dbC9j+PKD1pfo'
    'y7Ps0n6fv7RRUlxq99sfRP/oxPOjWc+nEY95ffzj5Ry1Q5NdruarJDC8YP+hhcCf0gD+VErWcF1D+6Ge3+dE85xdNP6c+v86rT+G'
    '/Lns9PcfY/6nUv5nmj/m/c+V8fcfZP/NxL//jfqPz+vv//5TAJcTufzD/GvUNP3+a3YMWbJcMrxcx99//vt//CpGl1n+epnlL7/+'
    '/Pd/8TZz1uTX8Sxf/+PX71H6zzH/ouL/7ue/EimWfmo/Dut/h9J/9ZT/svT/fWJ/Lgz6/0Hrv3rlf6L1H/9pg//ti3DF+vXS6ssr'
    'vr83u/p/Krm23rSRKPzeX+GyisZWHDdstC+wfuDiEFRqWGxasVFkEWMSK2BbtkmCqv73/c54BmwuofvQNhnP7dy+851RdZT8Lb7i'
    'vbbK/pzBof1nnTewokkIhvVsue2Ctd0vM0vusc81ti5UAKvOtu7LsSZ6BQk6k8AalLyASdxtBHZfC67DsbCIpXyTBNl2MEnj943J'
    'xwwnJD+0QbSyhK4ihDTxr9akjHViHv90z/I4XrKHS3Ld0s2JZGX6TxZnrMEP0xkSIGvQol+7eSIucNRhAjTNbQwQrvA5x3Pabqak'
    'jlVCXA5BwmAwaUDvWWZMUwviBS7MHjQNMb0bIzJWRG6ShtEe0XCswS0RW0Ct4zQEVFKHtVlOkcpbmOmyl5to5JYB/BNkmgB5NQsf'
    'w2WYg3kuluvsuWDf+wTM+ta2upwTMWFkqLiZmJJpGEmcqHWtmZs4JlITHXSWt5cza9z9rrLwqUYuOJurWpOqHlYhx7mRJbiE6j+n'
    'av1au6z90e59H/bBdUdT9w6EHcR97NYuxXdg3n39QU/0Gu1SA4+mHX/WJImvNfDjahZG+FGvSeZeayS/NCarHx9erPqruc7TiMg3'
    'FAYlVgelbYRNMWQUAaf+VpzorLh5d2i7P8Z912pPXauDScXXA0CRPtntO632wPJca4AwdsdTPv9XxSK7rnIGl+KezBBwKJk9LgEz'
    'V2ucf+UzndtNz/KUJNV0kvRBJyHxR1f8NySk4puRzFCC5DI5k+5kDoaPn8nVknoBAmWCuCJEq5DRA+pxLZdB4WQ2VBtRTiUJX8I9'
    'M468MFrEf6s3er1+ppL40YeufzjSYW68et0bW/9M+uNtofccrwJTJH6DMr5BI+L+i3g5D1KTRr6wbvwWLePZPGNfWLvnFa44nniu'
    '62DTVneK8ccn7zUO/QD12zJAQHuv4v9KQJ1msVtpcUGMDHxju7IOeE66B1EjD1U1El4MZJsVQvWlGCt2qwyf0YbTt3sDa0vHbLjr'
    '7XBid1EOU731VdZYszeTDqTA9IhfSWsScKwz0NIlAiQK3sDlz3NwKVix2DQFt2yUyTI2PEJbSUicUuVOe9z5mJSd4cjyEHhui4vI'
    'G02WslrRRtKbhzu7+mtKqXt2xW+3k8HAG42H3UmHXggwUg7ydqvzdTIST3VCkt3mFcM0jl20WO8502+kfM6Oj17TWL3gb7UIxoxj'
    'MehZmOVe/FJC5t0ic7f2i7rvbZDHEgKAgYtWk0YUv6my26Sxzn3NAAYsaERlF9OL1cXcvbi7+Hbh/Mu0S4aVBBExfx1IQsA3Bo3H'
    '2Uvp/rx3Z3ERg+M/e39EtTvLlEXVhguDQ4YKJ9CaC4MnHOQDbL7INpGvYghxEMWqVimw5ENVcULZV7XPpvhIW553GGmHu5b33Rr3'
    'b/udI+9BPNEGEU9fIo7VY4FsSNUeUZBYzypyiEGDWzQ74Sojy+4ieL1b3MjrDAeDvkP+uNsoTzdVQbn65d4f6r9sA4Tbb9ugagd5'
    '1HFD0L4UzuLXfXT5yGKnrNYZ2p3JeAyg8Dp3LbtnEYpJPbVb3eK1qrIVxJF8V1xXpwy4nbMg3FpuGlKWdcSjdxVm1Jj2MNog/b4k'
    'n02IetyEQ07HUPlyT9t71zrB4/o2OM4AXig5HOZQq10wOfnK2FSQdbNwHohgazBdNMrdp27EzRsfndYa8DR2eOq2BS/H+SaSdbZe'
    'kScfnEFVJBEKSvLq8SpRrwyD+y6W4dPz/njRjJdTi/JzIRFjc8vSOEmrmAOfq+5zREwOtHytzlLfZDqt0pk9VJyp7d5ZTt/RFflC'
    'TD2DHaVvu5REDsTdYy+00UlK7o4tx/F6HILBykm7yIlpDj0qQ9tSfJDwFZi5rys3CmmKjs4Oz6yqoKK0pyAKUkA622bdqkJOKMPr'
    'WbY15qCnpL7UB0Jx+wCVwZ45PIH9f6dyJp2ORUUICosQnOEGJBvhRZknK15dHASt5w4pjN3eyPVKOdhAjXSyBuHa/kQviYLhg1xI'
    'hi/4BcFiEYzOJsuDlfWOeqLgseL6736Q5MrXYPMYz9J5P0LtnK6TvPFxVII+jScjl2woVYRb+XFKuJEpVNAF6Su94R3zmIMb1W+u'
    'K9ex+D9gugTXH6uXkpTXGQzhT0ynQlkNNEMqhJP8QLtv3Px1/fB7V/lT+/QfYHyVmgpcAAA='
)
FILENAME = 'nn/nn_omograph/turbo2/model.onnx'
REPO = 'ruaccent/accentuator'
MODEL_MIN_SIZE = 280_000_000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prior_module():
    raw=gzip.decompress(base64.b64decode(''.join(R35_1_B64),validate=True))
    if sha256(raw)!=R35_1_SHA256:
        raise RuntimeError('R35_1_SOURCE_SHA_NOT_TRUSTED')
    ns={'__name__':'_eliot_r35_1_verified_','__file__':'[embedded_R35_1_verified]'}
    exec(compile(raw.decode('utf-8'), 'verified_r35_1.py','exec'),ns)
    return ns


def verify_immutable_updater(ns, cmd):
    if not cmd.is_file() or cmd.is_symlink():
        raise RuntimeError('ONE_UPDATER_MISSING_OR_LINK_HOLD')
    original_r35=ns['original_r35']()
    status, old, new=ns['verify_patched_or_original'](cmd.read_bytes(), original_r35)
    if status!='already-patched' or old==new:
        raise RuntimeError('R35_1_NOT_EXACTLY_INSTALLED_HOLD')
    if new!=cmd.read_bytes():
        raise RuntimeError('UPDATER_CHANGED_DURING_PREFLIGHT_HOLD')
    print('ELIOT_R35_2_EXACT_UPDATER_PASS: only R35.1 is installed',flush=True)
    return sha256(new)


def model_validation_script():
    return '''import pathlib,sys
import onnxruntime as ort
p=pathlib.Path(sys.argv[1]); min_size=int(sys.argv[2])
if not p.is_file() or p.stat().st_size < min_size:
    print('R35_2_MODEL_MISSING_OR_TOO_SMALL',p.stat().st_size if p.exists() else 0,flush=True)
    raise SystemExit(3)
opt=ort.SessionOptions()
opt.intra_op_num_threads=2
opt.inter_op_num_threads=1
opt.graph_optimization_level=ort.GraphOptimizationLevel.ORT_DISABLE_ALL
sess=ort.InferenceSession(str(p),sess_options=opt,providers=['CPUExecutionProvider'])
if not sess.get_inputs() or not sess.get_outputs():raise RuntimeError('MODEL_HAS_NO_INPUT_OR_OUTPUT')
print('ELIOT_R35_2_ONNX_READY',p.stat().st_size,'bytes',flush=True)
'''


def validate(py, target):
    return subprocess.call([str(py),'-u','-c',model_validation_script(),str(target),str(MODEL_MIN_SIZE)],
                           env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}) == 0


def download_script():
    return '''import pathlib,sys
from huggingface_hub import hf_hub_download
p=pathlib.Path(sys.argv[1]);filename=sys.argv[2];repo=sys.argv[3]
print('ELIOT_R35_2_DOWNLOAD_ONE_MISSING_ONNX',repo,filename,'HTTP_NO_XET',flush=True)
s=hf_hub_download(repo_id=repo,filename=filename,local_dir=str(p),force_download=True)
print('ELIOT_R35_2_DOWNLOAD_COMPLETE',s,flush=True)
'''


def repair(py, model_dir, target):
    if validate(py,target):
        print('ELIOT_R35_2_MODEL_ALREADY_VALID: no download needed',flush=True)
        return
    if not py.is_file() or py.is_symlink():raise RuntimeError('ISOLATED_RUACCENT_VENV_NOT_FOUND')
    if model_dir.is_symlink() or target.is_symlink():raise RuntimeError('RUACCENT_MODEL_PATH_SYMLINK_HOLD')
    env=os.environ.copy()
    env.update({'HF_HUB_OFFLINE':'0','TRANSFORMERS_OFFLINE':'0',
                'HF_HUB_DISABLE_XET':'1','HF_HUB_DISABLE_TELEMETRY':'1',
                'PYTHONDONTWRITEBYTECODE':'1',
                'HF_HOME':str(model_dir.parent/'HF')})
    print('ELIOT_R35_2_DOWNLOAD_ONLY_INCOMPLETE_TURBO2: other model caches unchanged',flush=True)
    rc=subprocess.call([str(py),'-u','-c',download_script(),str(model_dir),FILENAME,REPO],env=env)
    if rc!=0:raise RuntimeError('TURBO2_HTTP_DOWNLOAD_FAILED_HOLD_'+str(rc))
    if not validate(py,target):
        raise RuntimeError('TURBO2_ONNX_VERIFICATION_FAILED_HOLD')


def main():
    ns=prior_module()
    assert len(FILENAME)>0 and FILENAME.endswith('/model.onnx')
    print('ELIOT_R35_2_SELFTEST_PASS: exact previous R35.1 code embedded, one-file repair scope',flush=True)
    if '--selftest-only' in sys.argv:return 0
    if os.name!='nt' or sys.version_info<(3,11):raise RuntimeError('WINDOWS_PYTHON_3_11_REQUIRED')
    home=pathlib.Path.home()
    folder=home/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'
    cmd=folder/'BG_VOICE_UPDATE.cmd'
    original_sha=verify_immutable_updater(ns,cmd)
    full=home/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'
    model_dir=full/'ELIOT_R35_MOVIE_G08_DUAL_METHOD'/'RUACCENT_MODELS'
    target=model_dir/pathlib.Path(FILENAME)
    py=full/'ELIOT_R35_TEXT_ONLY_VENV'/'Scripts'/'python.exe'
    if not py.is_file():raise RuntimeError('RUACCENT_TEXT_VENV_MISSING_HOLD')
    if model_dir.is_symlink() or target.is_symlink():raise RuntimeError('MODEL_DIR_SYMLINK_HOLD')
    # We intentionally do not delete or rename anything previously downloaded.
    repair(py,model_dir,target)
    if sha256(cmd.read_bytes())!=original_sha:
        raise RuntimeError('UPDATER_CHANGED_DURING_CACHE_REPAIR_HOLD')
    # Disable Xet only in this process tree; the R35.1 worker retains its existing
    # isolated online/offline gates and its own original stress checks.
    saved=os.environ.get('HF_HUB_DISABLE_XET')
    os.environ['HF_HUB_DISABLE_XET']='1'
    try:
        print('ELIOT_R35_2_R35_1_RESUME: full RUAccent plus Accentik stress check, no bypass',flush=True)
        # This is the EXACT verified R35.1 main, no new generator or updater.
        result=ns['main']()
    finally:
        if saved is None:os.environ.pop('HF_HUB_DISABLE_XET',None)
        else:os.environ['HF_HUB_DISABLE_XET']=saved
    if sha256(cmd.read_bytes())!=original_sha:
        raise RuntimeError('UPDATER_UNEXPECTED_CHANGE_AFTER_RESUME_HOLD')
    return result

if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print('ELIOT_R35_2_INTERRUPTED_HOLD: keep all downloaded components, do not run in parallel',flush=True)
        raise SystemExit(130)
    except Exception as e:
        print('ELIOT_R35_2_HOLD',type(e).__name__,str(e)[:400],flush=True)
        raise SystemExit(2)
