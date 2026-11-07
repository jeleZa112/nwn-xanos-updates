#!/usr/bin/env python3
"""Create small original game resources for BGXAI 041, WITHOUT touching EET.

Resources: 12x12 BAM V1 icon and two SPL V1 scripted effects.
Generated files require WeiDU dynamic STATDESC index patch; source only.
"""
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
OUT=HERE/'BGX41'
ICON='BGX41IC'
SPELL_ON='BGX41ON'
SPELL_OFF='BGX41OF'
ICON_INDEX_SENTINEL=30000  # Must be overwritten by WeiDU, never install this number.

# Original 12 x 12 green shield with a pale gold check.
ART=(
    '............',
    '....####....',
    '...#++++#...',
    '..#++++++#..',
    '..#++++++#..',
    '..#+g+++g#..',
    '..#++g+g+#..',
    '...#++g+#...',
    '...#++++#...',
    '....#++#....',
    '.....##.....',
    '............',
)
PAL={
    '.':(0,255,0), # transparent green key; index 0
    '#':(15,42,38),
    '+':(38,162,99),
    'g':(255,223,114)
}

def icon_bam():
    assert len(ART)==12 and all(len(x)==12 for x in ART)
    keys=list(PAL)
    pal=bytearray(256*4)
    for idx,key in enumerate(keys):
        r,g,b=PAL[key]
        struct.pack_into('<4B',pal,idx*4,b,g,r,0)
    pixels=bytes(keys.index(c) for row in ART for c in row)
    header_size=24
    frame_entries=12
    cycle_entries=4
    palette_off=header_size+frame_entries+cycle_entries
    lookup_off=palette_off+1024
    pixel_off=lookup_off+2
    out=bytearray(pixel_off+len(pixels))
    out[:8]=b'BAM V1  '
    struct.pack_into('<HBBIII',out,8,1,1,0,header_size,palette_off,lookup_off)
    struct.pack_into('<HHhhI',out,header_size,12,12,6,6,pixel_off|0x80000000)
    struct.pack_into('<HH',out,header_size+12,1,0)
    out[palette_off:lookup_off]=pal
    struct.pack_into('<H',out,lookup_off,0)
    out[pixel_off:]=pixels
    return bytes(out)

def effect(opcode,*,param2=0,resref='',timing=0):
    e=bytearray(48)
    struct.pack_into('<H',e,0,opcode)
    e[2]=1 # target: self
    e[3]=0 # power
    struct.pack_into('<I',e,8,param2)
    e[12]=timing
    e[13]=2 # cannot dispel / ignores resistance
    e[18:20]=bytes([100,0]) # IESDP BG2EE: probability low/high 100/0; 0/100 NEVER applies
    if resref:
        assert len(resref)<=8 and resref.isascii()
        e[20:20+len(resref)]=resref.encode('ascii')
    return bytes(e)

def spell(effects):
    header=bytearray(0x72)
    header[:8]=b'SPL V1  '
    struct.pack_into('<IIII',header,8,0xFFFFFFFF,0xFFFFFFFF,0,0)
    struct.pack_into('<H',header,0x1c,4) # Innate
    struct.pack_into('<I',header,0x34,1) # lvl 1
    struct.pack_into('<II',header,0x50,0xFFFFFFFF,0xFFFFFFFF)
    struct.pack_into('<I',header,0x64,0x72) # ext hdr offset
    struct.pack_into('<H',header,0x68,1) # ext hdr count
    struct.pack_into('<I',header,0x6a,0x72+0x28) # feature table
    ext=bytearray(0x28)
    ext[0]=1 # standard
    ext[12]=5 # self
    struct.pack_into('<H',ext,0x10,1) # min level
    struct.pack_into('<H',ext,0x1e,len(effects)) # effects count
    struct.pack_into('<H',ext,0x20,0) # first effect index
    return bytes(header+ext)+b''.join(effects)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(ICON+'.BAM')).write_bytes(icon_bam())
    # Turn-on spell: remove stale own effects, then add own icon until switched off.
    on=spell((effect(321,resref=SPELL_ON),effect(142,param2=ICON_INDEX_SENTINEL,timing=1)))
    off=spell((effect(321,resref=SPELL_ON),))
    (OUT/(SPELL_ON+'.SPL')).write_bytes(on)
    (OUT/(SPELL_OFF+'.SPL')).write_bytes(off)
    print('Generated', [(f.name,f.stat().st_size) for f in OUT.glob('*')])

if __name__=='__main__':main()
