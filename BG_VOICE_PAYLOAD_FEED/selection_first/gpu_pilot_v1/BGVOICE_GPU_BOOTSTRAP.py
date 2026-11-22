# -*- coding: utf-8 -*-
"""Choose existing CUDA PyTorch interpreter, optionally install only missing small Python libs in private folder."""
import os,subprocess,sys,json,time
from pathlib import Path
OUT=Path.home()/'Documents'/'BG_VOICE_RU'/'VOICE_SELECTION_GPU'
OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parent

def log(*parts): print(*parts, flush=True)  # Supports both one and multiple log arguments

def candidates():
    home=Path.home()
    paths=[
      home/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'/'venv_asr'/'Scripts'/'python.exe',
      home/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'/'venv_tts'/'Scripts'/'python.exe',
      home/'Downloads'/'BG_VOICE_RU_KELDORN_EMOTION_CLONING_PILOT_V1'/'BG_VOICE_RU_KELDORN_CLONE_PILOT'/'.venv'/'Scripts'/'python.exe',
      home/'Downloads'/'BG_VOICE_RU_10_ACTING_SER_STRESS_V3'/'BG_VOICE_RU_10_ACTING_SER_STRESS_V3'/'.venv'/'Scripts'/'python.exe',
      Path(sys.executable)]
    return list(dict.fromkeys(map(str,(p for p in paths if p.is_file()))))

def probe(p):
    code='import torch,sys; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO_CUDA"); sys.exit(0 if torch.cuda.is_available() else 7)'
    try:return subprocess.run([p,'-c',code],capture_output=True,text=True,timeout=45)
    except (OSError,subprocess.TimeoutExpired):return None

def ready(p,env):
    cmd=[p,'-c','from transformers import WavLMForXVector, Wav2Vec2FeatureExtractor; from scipy.signal import resample_poly;import numpy,torch; print("MODEL_LIBRARY_READY")']
    try:return subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=45)
    except (OSError,subprocess.TimeoutExpired):return None

def main():
    cuda=[];debug=[]
    for p in candidates():
        x=probe(p)
        debug.append({'python':p,'cuda_ready':bool(x and x.returncode==0),'info':x.stdout[-170:] if x else 'PROBE_FAILED'})
        if x is not None and x.returncode==0:cuda.append(p)
    if not cuda:
        (OUT/'BOOTSTRAP_STATUS.json').write_text(json.dumps({'status':'HOLD_NO_EXISTING_CUDA_PYTHON','probes':debug},ensure_ascii=False,indent=2),encoding='utf-8')
        log('HOLD_NO_EXISTING_CUDA_PYTHON: No model inference was started; game and master WAV unchanged.')
        return 0
    py=cuda[0];env=os.environ.copy()
    private=OUT/'_PRIVATE_PYTHON_DEPS';private.mkdir(parents=True,exist_ok=True)
    env['PYTHONPATH']=str(private)+os.pathsep+env.get('PYTHONPATH','')
    check=ready(py,env)
    if check is None or check.returncode!=0:
        log('GPU Torch found. Installing missing Python inference helpers to private project folder (NOT main venv)...')
        command=[py,'-m','pip','install','--disable-pip-version-check','--no-input','--target',str(private),
                 'transformers==4.57.3','huggingface-hub>=0.34,<1','tokenizers>=0.22,<0.23',
                 'safetensors>=0.4','scipy>=1.9','numpy>=1.23,<3','packaging','pyyaml','regex','requests','tqdm','filelock']
        try:
            result=subprocess.run(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
            (OUT/'PRIVATE_INSTALL_LOG.txt').write_text((result.stdout or '')[-14000:],encoding='utf-8')
            if result.returncode!=0:raise RuntimeError('PRIVATE_PACKAGE_INSTALL_FAILED')
        except Exception as e:
            (OUT/'BOOTSTRAP_STATUS.json').write_text(json.dumps({'status':'HOLD_PRIVATE_DEPENDENCIES','error':str(e),'python':py},ensure_ascii=False,indent=2),encoding='utf-8')
            log('HOLD_PRIVATE_DEPENDENCIES:',str(e),'See PRIVATE_INSTALL_LOG.txt')
            return 0
        check=ready(py,env)
        if check is None or check.returncode!=0:
            detail=(check.stderr if check else 'NO_RESPONSE')[-1500:]
            (OUT/'BOOTSTRAP_STATUS.json').write_text(json.dumps({'status':'HOLD_DEPENDENCIES_STILL_MISSING','detail':detail,'python':py},ensure_ascii=False,indent=2),encoding='utf-8')
            log('HOLD_DEPENDENCIES_STILL_MISSING:',detail)
            return 0
    (OUT/'BOOTSTRAP_STATUS.json').write_text(json.dumps({'status':'CUDA_AND_IMPORTS_PASS','selected_python':py,'device':'cuda',
          'probes':debug,'private_dependencies':str(private),'model':'microsoft/wavlm-base-plus-sv'},ensure_ascii=False,indent=2),encoding='utf-8')
    log('CUDA_READY:',py)
    log('Independent WavLM first-run model download may occur; cached thereafter. No changes to game/master.')
    return subprocess.call([py,str(ROOT/'BGVOICE_GPU_SELECTION.py')]+sys.argv[1:],env=env,cwd=str(ROOT))

if __name__=='__main__':raise SystemExit(main())
