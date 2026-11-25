"""Source-only fail-closed tests for the genuine V136 external Windows adapter.

No game files, process injection or remote writes; these mocks do not certify
EEex JIT ownership or real ABI. Windows CI separately calls kernel32 APIs.
"""
from __future__ import annotations
import unittest,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import v136_jit_provenance_ro as M
BASE=0x140000000
TARGET=BASE+0x10000000
EXE_SIZE=0x900000
MODS=[('Baldur.exe','C:/Games/Baldur.exe',BASE,EXE_SIZE),
      ('EEex.dll','C:/Games/EEex.dll',BASE+0xB00000,0x100000)]

class Memory:
 def __init__(self):
  self.mem={};self.n=0;self.flip_at=None;self.fail_at=None
  for _,(rva,data) in M.SITES.items():self.put(BASE+rva,data)
  disp=TARGET-(BASE+M.FIRST+5)
  self.put(BASE+M.FIRST,b'\xe9'+disp.to_bytes(4,'little',signed=True))
  self.put(TARGET,bytes(range(1,M.SNAP_BYTES+1)))
  self.regions={
   'source':{'base':BASE+0x300000,'size':0x200000,'state':M.MEM_COMMIT,
             'protect':0x20,'type':M.MEM_IMAGE},
   'target':{'base':TARGET-0x100,'size':0x1000,'state':M.MEM_COMMIT,
             'protect':0x40,'type':M.MEM_PRIVATE},
  }
 def put(self,a,raw):
  for i,c in enumerate(raw):self.mem[a+i]=c
 def read(self,a,n):
  self.n+=1
  if self.fail_at==self.n:raise OSError('SYNTHETIC_READ_FAILURE')
  b=bytes(self.mem.get(a+i,0) for i in range(n))
  if self.flip_at and self.flip_at[0]==self.n:
   self.mem[self.flip_at[1]]^=1
  return b
 def query(self,a):
  if BASE+0x300000<=a<BASE+0x500000:return dict(self.regions['source'])
  if TARGET-0x100<=a<TARGET+0xf00:return dict(self.regions['target'])
  return {'base':a,'size':0x1000,'state':M.MEM_COMMIT,'protect':0x01,'type':M.MEM_PRIVATE}
 def audit(self,modules=None,base=BASE,size=EXE_SIZE):
  return M.audit(self.read,self.query,base,MODS if modules is None else modules,size)

class V136Tests(unittest.TestCase):
 def assertHeld(self,r):
  self.assertEqual(r['status'],'V136_RUNTIME_OWNER_AND_GAMEPLAY_HOLD',r)
  self.assertFalse(r['firstcall_owner_verified'])
  self.assertFalse(r['native_hooks_installed'])
  self.assertEqual(r['game_files_written'],0)
  self.assertFalse(r['gameplay_verified'])
 def test_positive_does_not_prove_owner_abi_or_gameplay(self):
  r=Memory().audit()
  self.assertEqual(r['status'],'V136_LIVE_PAIR_SITES_AND_EXECUTABLE_TARGET_OBSERVED_OWNER_HOLD')
  self.assertTrue(r['entry_exit_original_bytes_verified'])
  self.assertEqual(r['sites_checked'],4)
  self.assertTrue(r['memory_snapshot_twice_equal'])
  self.assertEqual(r['firstcall_target_region_type'],'PRIVATE')
  self.assertTrue(r['firstcall_target_in_unlisted_region'])
  self.assertFalse(r['firstcall_target_inside_eeex_module'])
  self.assertEqual(r['jit_target_code_sample_length'],48)
  self.assertFalse(r['firstcall_owner_verified'])
  self.assertFalse(r['runtime_unwind_registered_verified'])
  self.assertFalse(r['native_abi_verified'])
  self.assertFalse(r['hit_miss_meaning_verified'])
  self.assertFalse(r['row_join_verified'])
 def test_all_four_new_live_sites_cannot_drift(self):
  count=0
  for _,(rva,pin) in M.SITES.items():
   for i in range(len(pin)):
    x=Memory();x.mem[BASE+rva+i]^=0x40
    self.assertHeld(x.audit())
    count+=1
  self.assertEqual(count,25)
 def test_jmp_unpatched_fails(self):
  x=Memory();x.mem[BASE+M.FIRST]=0xE8
  self.assertHeld(x.audit())
 def test_not_an_executable_region_fails(self):
  for protect in (0x01,0x02,0x04,0x08,0x20|M.PAGE_GUARD):
   x=Memory();x.regions['target']['protect']=protect
   self.assertHeld(x.audit())
 def test_region_not_committed_or_wrong_type_fails(self):
  for field,value in [('state',0x10000),('type',0xDEADBEEF),('size',0)]:
   x=Memory();x.regions['target'][field]=value
   self.assertHeld(x.audit())
 def test_double_snapshot_detects_jump_mutation(self):
  x=Memory();x.flip_at=(6,BASE+M.FIRST+1)
  self.assertHeld(x.audit())
 def test_double_snapshot_detects_target_code_mutation(self):
  x=Memory();x.flip_at=(7,TARGET+4)
  self.assertHeld(x.audit())
 def test_any_remote_read_failure_fails_closed(self):
  for read_index in range(1,13):
   x=Memory();x.fail_at=read_index
   self.assertHeld(x.audit())
 def test_attack_result_is_never_mapped_to_miss_or_hit(self):
  s=Path(M.__file__).read_text('utf8')
  for name in ('return_0_is_miss_proven','return_1_is_hit_proven','HIT', 'MISS'):
   self.assertNotIn("'"+name+"':True",s)
  r=Memory().audit()
  self.assertFalse(r['hit_miss_meaning_verified'])
 def test_eeex_module_absent_fails(self):
  self.assertHeld(Memory().audit(modules=MODS[:1]))
 def test_game_module_invalid_fails(self):
  self.assertHeld(Memory().audit(modules=MODS[1:]))
 def test_exe_self_target_fails(self):
  x=Memory()
  jmp=BASE+0x400000-(BASE+M.FIRST+5)
  x.put(BASE+M.FIRST,b'\xe9'+jmp.to_bytes(4,'little',signed=True))
  self.assertHeld(x.audit())
 def test_overlap_module_or_other_module_fails(self):
  other=('other.dll','C:/Games/other.dll',TARGET-0x10,0x200)
  self.assertHeld(Memory().audit(modules=MODS+[other]))
  eeex=('EEex.dll','C:/Games/EEex.dll',TARGET-0x10,0x200)
  self.assertHeld(Memory().audit(modules=MODS+[other,eeex]))
 def test_target_inside_eeex_is_still_not_owner_proof(self):
  m=[MODS[0],('EEex.dll','C:/Games/EEex.dll',TARGET-0x2000,0x4000)]
  r=Memory().audit(modules=m)
  self.assertTrue(r['firstcall_target_inside_eeex_module']);self.assertFalse(r['firstcall_owner_verified'])
 def test_bogus_inputs_fails(self):
  for base in (None,0,-1,BASE+1,0x400000,2**48):
   self.assertHeld(M.audit(Memory().read,Memory().query,base,MODS,EXE_SIZE))
  self.assertHeld(M.audit(None,lambda a:{},BASE,MODS,EXE_SIZE))
  self.assertHeld(M.audit(Memory().read,None,BASE,MODS,EXE_SIZE))
 def test_adversarial_random_site_corruption(self):
  rng=random.Random(20261125)
  for _ in range(500):
   x=Memory();rva,raw=rng.choice(list(M.SITES.values()))
   addr=BASE+rva+rng.randrange(len(raw))
   x.mem[addr]^=1<<rng.randrange(8)
   self.assertHeld(x.audit())
 def test_no_write_or_injection_functions(self):
  source=Path(M.__file__).read_text('utf8')
  for forbidden in ('WriteProcessMemory(', 'VirtualProtectEx(', 'CreateRemoteThread(',
                    'SuspendThread(', 'SetThreadContext(', 'DebugActiveProcess(',
                    'EEex_HookBefore(', 'EEex_JITAt('):
   self.assertNotIn(forbidden,source)
  self.assertIn('ReadProcessMemory',source)
  self.assertIn('VirtualQueryEx',source)
 def test_windows_only_adapter_no_import_failure(self):
  if sys.platform!='win32':
   with self.assertRaisesRegex(RuntimeError,'WINDOWS_X64_PYTHON_REQUIRED'):
    M._make_windows_api()

if __name__=='__main__':unittest.main(verbosity=2)
