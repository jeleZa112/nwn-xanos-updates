"""V138 standalone native ledger: exercises real compiled C, NEVER Baldur.exe.
Compiles shared library from source on Linux/macOS; Windows CI separately
compiles a Win64 COFF object to detect calling-convention/compile defects.
No hooks, no injection, no claim about game/EEex runtime.
"""
from __future__ import annotations
import ctypes as C
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import random

C_FILE=Path(__file__).with_name('v138_native_attempt_ledger.c')
class FixedRef(C.Structure):
    _fields_=[('bytes',C.c_ubyte*8),('length',C.c_ubyte)]

def ref(source):
    if source is None:return None
    if isinstance(source,FixedRef):return source
    if isinstance(source,(bytes,bytearray)):
        r=FixedRef()
        r.length=len(source)
        for i,b in enumerate(source[:8]):r.bytes[i]=b
        return r
    raise TypeError(source)

class Event(C.Structure):
    _fields_=[('session',C.c_uint64),('thread',C.c_uint64),
        ('frame',C.c_uint64),('seq',C.c_uint64),('attacker',C.c_uint64),
        ('target',C.c_uint64),('ability',C.c_uint16),('raw_return',C.c_uint8),
        ('raw_return_present',C.c_uint8),('render_count',C.c_uint8),
        ('valid',C.c_uint8),('row_token',C.c_uint64),
        ('weapon',C.c_char*9),('launcher',C.c_char*9),('ammo',C.c_char*9)]

class LedgerSupport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='V138_STANDALONE_NATIVE_')
        if os.name=='nt':
            cc=shutil.which('clang')
            linker=shutil.which('lld-link')
            if not cc or not linker:raise RuntimeError('WIN64_CLANG_AND_LLD_LINK_REQUIRED')
            obj=Path(cls.temp.name)/'v138_testing.obj'
            lib=Path(cls.temp.name)/'v138_testing.dll'
            subprocess.run([cc,'--target=x86_64-pc-windows-msvc','-std=c11','-O2',
                            '-ffreestanding','-funwind-tables','-fno-stack-protector',
                            '-c',str(C_FILE),'-o',str(obj)],check=True,timeout=30)
            subprocess.run([linker,'/dll','/noentry','/machine:x64',f'/out:{lib}',str(obj)],
                            check=True,timeout=30)
        else:
            cc=shutil.which('clang') or shutil.which('cc')
            if not cc:raise RuntimeError('NATIVE_C_COMPILER_REQUIRED')
            lib=Path(cls.temp.name)/'libv138_testing.so'
            subprocess.run([cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-fPIC',
                            '-shared',str(C_FILE),'-o',str(lib)],check=True,timeout=30)
        cls.lib=lib

    def setUp(self):
        self.S=13892026
        self.local_lib=Path(self.temp.name)/(self._testMethodName+(".dll" if os.name=="nt" else ".so"))
        shutil.copy2(self.lib,self.local_lib)
        self.dll=(C.WinDLL if os.name=="nt" else C.CDLL)(str(self.local_lib))
        self.d=self.dll
        d=self.dll
        d.bgv138_reset.argtypes=[C.c_uint64]
        d.bgv138_reset.restype=C.c_int
        d.bgv138_enter.argtypes=[C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,
                                 C.POINTER(FixedRef),C.POINTER(FixedRef),C.POINTER(FixedRef),C.c_uint16,C.POINTER(C.c_uint64)]
        d.bgv138_enter.restype=C.c_int
        d.bgv138_exit.argtypes=[C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint8]
        d.bgv138_exit.restype=C.c_int
        d.bgv138_direct_render.argtypes=[C.c_uint64,C.c_uint64,C.c_uint64]
        d.bgv138_direct_render.restype=C.c_int
        d.bgv138_read.argtypes=[C.c_uint64,C.c_uint64,C.POINTER(Event)]
        d.bgv138_read.restype=C.c_int
        d.bgv138_stats.argtypes=[C.c_uint64,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64),C.POINTER(C.c_uint8)]
        d.bgv138_stats.restype=C.c_int
        self.assertEqual(self.d.bgv138_reset(self.S),0)

    @classmethod
    def tearDownClass(cls):
        # Windows holds a loaded DLL until the test process exits.  Do not
        # unload a WinDLL behind ctypes function objects or try deleting it.
        # Runner-managed TEMP is reclaimed after the Python process exits.
        if os.name!='nt':cls.temp.cleanup()
    def enter(self,thread=7,frame=10,weapon=b'SW1H04',launcher=None,ammo=None,
              attacker=11,target=19,ability=0,session=None):
        s=C.c_uint64(0)
        w,l,a=ref(weapon),ref(launcher),ref(ammo)
        rc=self.d.bgv138_enter(self.S if session is None else session,thread,frame,
              attacker,target,C.byref(w) if w is not None else None,
              C.byref(l) if l is not None else None,C.byref(a) if a is not None else None,
              ability,C.byref(s))
        return rc,s.value
    def done(self,seq,thread=7,frame=10,raw=0,session=None):
        return self.d.bgv138_exit(self.S if session is None else session,thread,frame,seq,raw)
    def read(self,seq):
        e=Event()
        rc=self.d.bgv138_read(self.S,seq,C.byref(e))
        return rc,e
    def stats(self):
        a,b,c=C.c_uint64(),C.c_uint64(),C.c_uint8()
        rc=self.d.bgv138_stats(self.S,C.byref(a),C.byref(b),C.byref(c))
        return rc,a.value,b.value,c.value
