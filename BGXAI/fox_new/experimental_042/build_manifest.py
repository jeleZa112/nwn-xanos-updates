from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
paths=sorted(str(x.relative_to(ROOT)) for x in ROOT.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x.name!='SOURCE_MANIFEST.json')
data={'schema':1,'project':'BGXAI 042 EPS-AI guard priority read-only research','status':'READ_ONLY_NO_INSTALL','files':[{'path':p,'size':(ROOT/p).stat().st_size,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths]}
(ROOT/'SOURCE_MANIFEST.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('manifest',len(paths),'files')
