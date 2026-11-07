"""Windows SendInput structure sizes used by V2.2 battle WASD pilot.

This test covers 64-bit layout only, not game acceptance of key events.
"""
import ctypes as C

class MouseInput(C.Structure):
    _fields_ = [("dx", C.c_int32), ("dy", C.c_int32),
                ("mouseData", C.c_uint32), ("dwFlags", C.c_uint32),
                ("time", C.c_uint32), ("dwExtraInfo", C.c_void_p)]
class KeyboardInput(C.Structure):
    _fields_ = [("wVk", C.c_uint16), ("wScan", C.c_uint16),
                ("dwFlags", C.c_uint32), ("time", C.c_uint32),
                ("dwExtraInfo", C.c_void_p)]
class HardwareInput(C.Structure):
    _fields_ = [("uMsg", C.c_uint32), ("wParamL", C.c_uint16),
                ("wParamH", C.c_uint16)]
class InputUnion(C.Union):
    _fields_ = [("mi", MouseInput), ("ki", KeyboardInput),
                ("hi", HardwareInput)]
class Input(C.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", C.c_uint32), ("data", InputUnion)]

def main():
    assert C.sizeof(C.c_void_p) == 8
    assert C.sizeof(MouseInput) == 32
    assert C.sizeof(KeyboardInput) == 24
    assert C.sizeof(InputUnion) == 32
    assert C.sizeof(Input) == 40
    assert Input.data.offset == 8
    down = Input()
    down.type = 1
    down.ki.wScan = 0x11
    down.ki.dwFlags = 0x0008
    assert down.ki.wScan == 0x11
    assert down.ki.dwFlags == 0x0008
    print("Battle keyboard INPUT/KEYBDINPUT ABI OK (x64).")

if __name__ == "__main__":
    main()
