"""Check 64-bit ctypes layout used by the Win32 InjectTouchInput bridge.

These pure-Python checks run on a 64-bit CI host without touching Roblox.
They do not prove that Windows or Roblox accepts injected touch events.
"""
import ctypes as C

class Point(C.Structure):
    _fields_ = [("x", C.c_int32), ("y", C.c_int32)]

class Rect(C.Structure):
    _fields_ = [("left", C.c_int32), ("top", C.c_int32),
                ("right", C.c_int32), ("bottom", C.c_int32)]

class PointerInfo(C.Structure):
    _fields_ = [("pointerType", C.c_uint32), ("pointerId", C.c_uint32),
                ("frameId", C.c_uint32), ("pointerFlags", C.c_uint32),
                ("sourceDevice", C.c_void_p), ("hwndTarget", C.c_void_p),
                ("ptPixelLocation", Point), ("ptHimetricLocation", Point),
                ("ptPixelLocationRaw", Point), ("ptHimetricLocationRaw", Point),
                ("dwTime", C.c_uint32), ("historyCount", C.c_uint32),
                ("InputData", C.c_int32), ("dwKeyStates", C.c_uint32),
                ("PerformanceCount", C.c_uint64),
                ("ButtonChangeType", C.c_uint32)]

class PointerTouchInfo(C.Structure):
    _fields_ = [("pointerInfo", PointerInfo),
                ("touchFlags", C.c_uint32), ("touchMask", C.c_uint32),
                ("rcContact", Rect), ("rcContactRaw", Rect),
                ("orientation", C.c_uint32), ("pressure", C.c_uint32)]

def test_struct_layout():
    assert C.sizeof(C.c_void_p) == 8, "Run layout test on 64-bit Python"
    assert C.sizeof(Point) == 8
    assert C.sizeof(Rect) == 16
    assert C.sizeof(PointerInfo) == 96
    assert C.sizeof(PointerTouchInfo) == 144
    assert PointerInfo.ptPixelLocation.offset == 32
    assert PointerInfo.PerformanceCount.offset == 80
    assert PointerTouchInfo.touchMask.offset == 100

if __name__ == "__main__":
    test_struct_layout()
    print("Win32 touch ctypes ABI layout OK (64-bit)")
