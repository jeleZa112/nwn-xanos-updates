"""R27 source-only deterministic composition of existing R2/R4 Lua observation cores.

No EEex, games, installs, commands, listeners or network. No copies of the
ranker/EPS system. Keep the input source byte-for-byte within Lua functions.
"""
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parent
SOURCES=(
 ('BGXAI_WEAPON_SLOTS_R2_READONLY.lua','R2_CORE'),
 ('BGXAI_WEAPON_ACTIVE_R4_READONLY.lua','R4_CORE'),
)
PINS={
 'BGXAI_WEAPON_SLOTS_R2_READONLY.lua':'7bd88866eab1d73f59b6619b2f38e26b846c0daa85a54f6c1de9e77e0730b5a0',
 'BGXAI_WEAPON_ACTIVE_R4_READONLY.lua':'2b618df53566b75f651ae75ce737496e4b24cb18fd754be7eb7c245ccfbbcc40',
}
def sha(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def input_dir(root:Path=ROOT)->Path:
    # In the repository use the existing source-of-truth; never duplicate it.
    original=root.parent.parent/'patchsets'/'ranged_fighter_guarded_20261119'
    return original if original.is_dir() else root

def compose(root:Path=ROOT)->bytes:
 parts=[b'-- BGXAI R27 composed from SHA-pinned R2/R4. SOURCE ONLY, not installed.\n']
 for name,binding in SOURCES:
  data=(input_dir(root)/name).read_bytes()
  if sha(data)!=PINS[name]:raise ValueError('BASELINE_SOURCE_DRIFT: '+name)
  if not data.endswith(b'\n') or not data.rstrip().endswith(b'return M'):
   raise ValueError('BASELINE_MODULE_NOT_EXPECTED: '+name)
  parts.extend((b'local '+binding.encode()+b' = (function()\n',data,b'end)()\n'))
 tail=(root/'R27_EVENT_JOIN_TAIL.lua').read_bytes()
 if not tail.rstrip().endswith(b'return R27'):raise ValueError('R27_TAIL_MISSING_EXPORT')
 parts.append(tail)
 return b''.join(parts)
if __name__=='__main__':
 out=ROOT/'BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO.lua'
 out.write_bytes(compose())
 print(out.name, out.stat().st_size, sha(out.read_bytes()))
