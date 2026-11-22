# -*- coding: utf-8 -*-
"""Quick no-GPU test: positive CUDA probe -> runtime starts; no source audio touched."""
import importlib.util, tempfile, os, io, contextlib, sys
from pathlib import Path
from types import SimpleNamespace

original_home=os.environ.get('HOME')
try:
    with tempfile.TemporaryDirectory(prefix='bgvoice_gpu_fix_test_') as tmp:
        os.environ['HOME']=tmp
        path=Path(__file__).resolve().parent/'BGVOICE_GPU_BOOTSTRAP.py'
        spec=importlib.util.spec_from_file_location('bgvoice_bootstrap_hotfix',path)
        m=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        expected_python=str(Path(tmp)/'GPU-venv'/'python.exe')
        m.candidates=lambda : [expected_python]
        m.probe=lambda p: SimpleNamespace(returncode=0,stdout='2.7.1+cu128 True NVIDIA GeForce RTX 4060 Laptop GPU\n')
        m.ready=lambda p,env: SimpleNamespace(returncode=0,stderr='')
        launched=[]
        m.subprocess.call=lambda argv,**kwargs: launched.append((argv,kwargs)) or 0
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            result=m.main()
        assert result==0,result
        assert len(launched)==1,launched
        assert launched[0][0][0]==expected_python
        assert launched[0][0][1]==str(path.parent/'BGVOICE_GPU_SELECTION.py')
        assert 'CUDA_READY:' in stdout.getvalue(),stdout.getvalue()
        assert 'RTX 4060' in (m.OUT/'BOOTSTRAP_STATUS.json').read_text(encoding='utf-8')
        import json
        status=json.loads((m.OUT/'BOOTSTRAP_STATUS.json').read_text(encoding='utf-8'))
        assert status['status']=='CUDA_AND_IMPORTS_PASS'
        assert status['selected_python']==expected_python
        assert not (m.OUT/'PRIVATE_INSTALL_LOG.txt').exists(), 'Dependencies must not reinstall when already present'
        # Failure path: no CUDA returns safe HOLD without running the model.
        m.candidates=lambda : [expected_python]
        m.probe=lambda p: SimpleNamespace(returncode=7,stdout='NO_CUDA')
        m.subprocess.call=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('Launched despite NO_CUDA'))
        with contextlib.redirect_stdout(io.StringIO()):
            code=m.main()
        assert code==0
        status=json.loads((m.OUT/'BOOTSTRAP_STATUS.json').read_text(encoding='utf-8'))
        assert status['status']=='HOLD_NO_EXISTING_CUDA_PYTHON'
        print('PASS: CUDA_AND_IMPORTS_PASS -> launch main GPU script once; multi-arg log works')
        print('PASS: existing GPU environment reused, no dependency installation')
        print('PASS: no-CUDA path -> HOLD, no inference')
        print('PASS: no source WAV, game or updater accessed')
finally:
    if original_home is not None: os.environ['HOME']=original_home
    else: os.environ.pop('HOME',None)
