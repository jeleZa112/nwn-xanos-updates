"""BGXAI071 read-only off-game CRE inventory scanner.

Input is a stored archive of CRE templates, NOT the currently running EET party.
0x10 original class flags and 0x244 CRE kit values are only hints; no cast,
attack, class change, game installation, script edit or data exfiltration.
All output is aggregated and excludes private CRE bytes or creature names.
Sources: IESDP CRE V1.0: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/cre_v1.htm
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zipfile

# Absolute 32-bit CRE *raw* fields, NOT KIT.IDS trigger tokens.
CORE_KIT_HINTS = {
    0x40010000:'BERSERKER', 0x40020000:'WIZARD_SLAYER', 0x40030000:'KENSAI',
    0x40040000:'CAVALIER', 0x40050000:'INQUISITOR', 0x40060000:'UNDEAD_HUNTER',
    0x40070000:'ARCHER', 0x40080000:'STALKER', 0x40090000:'BEASTMASTER',
    0x400A0000:'ASSASSIN',0x400B0000:'BOUNTY_HUNTER',0x400C0000:'SWASHBUCKLER',
    0x400D0000:'BLADE',0x400E0000:'JESTER',0x400F0000:'SKALD',
    0x40100000:'TOTEMIC_DRUID',0x40110000:'SHAPESHIFTER',0x40120000:'AVENGER',
    0x40130000:'TALOS',0x40140000:'HELM',0x40150000:'LATHANDER',
    0x40200000:'BLACKGUARD',0x40210000:'SHADOWDANCER',
    0x40220000:'DWARVEN_DEFENDER',0x40230000:'DRAGON_DISCIPLE',
    0x40240000:'DARK_MOON',0x40250000:'SUN_SOUL',
}
ORIGINAL_CLASS_BITS = {3:'FIGHTER',4:'MAGE',5:'CLERIC',
                       6:'THIEF',7:'DRUID',8:'RANGER'}


def cre_head(data: bytes):
    """Parse only fixed offsets of IESDP CRE V1.0; no untrusted nested pointers."""
    if len(data)<0x2d4 or data[:8]!=b'CRE V1.0':
        return None
    flags=struct.unpack_from('<I',data,0x10)[0]
    orig_bits=(flags >> 3)&0x3f
    kit=struct.unpack_from('<I',data,0x244)[0]
    cid=data[0x273]
    levels=tuple(data[0x234:0x237])
    one_hot=orig_bits>0 and orig_bits & (orig_bits-1)==0
    original_class = ORIGINAL_CLASS_BITS[3+(orig_bits.bit_length()-1)] if one_hot else None
    return {'class_id':cid,'kit_cre_raw':kit,'levels':levels,'original_bits':orig_bits,
            'old_class_hint':original_class,'kit_name_hint':CORE_KIT_HINTS.get(kit),
            'has_dual_original_flag_hint':one_hot}


def scan(archive: Path):
    if not archive.is_file() or archive.suffix.lower()!='.zip':
        raise ValueError('source must be an existing .zip (read-only)')
    counts=Counter(); cids=Counter();kits=Counter(); originals=Counter()
    level_zero=0
    with zipfile.ZipFile(archive,'r') as z:
        for obj in z.infolist():
            if not obj.filename.lower().endswith('.cre'):
                continue
            counts['cre_entries']+=1
            if obj.file_size>16_000_000:
                counts['oversized_rejected']+=1;continue
            try:
                data=z.read(obj)
            except (ValueError,EOFError,RuntimeError,zipfile.BadZipFile):
                counts['corrupt_rejected']+=1;continue
            x=cre_head(data)
            if x is None:counts['bad_header_or_unsupported_cre']+=1;continue
            counts['valid_v1_0_headers']+=1
            cids[str(x['class_id'])]+=1
            kits[f'0x{x["kit_cre_raw"]:08X}']+=1
            if 1<=x['class_id']<=21:counts['core_class_1_21']+=1
            else:counts['noncore_or_modded_class']+=1
            if x['kit_cre_raw']==0:counts['no_kit_raw']+=1
            elif x['kit_cre_raw']==0x40000000:counts['trueclass_raw']+=1
            elif x['kit_name_hint']:counts['standard_named_kit_hint']+=1
            else:counts['other_modded_or_special_kit_raw']+=1
            if x['kit_cre_raw']==0x40110000:counts['shapeshifter_raw']+=1
            if x['kit_cre_raw']==0x4011:counts['ids_token_misstored_in_cre']+=1
            if x['original_bits']==0:counts['no_original_class_bit']+=1
            elif x['old_class_hint']:
                counts['single_original_class_bit_hint']+=1
                originals[x['old_class_hint']]+=1
            else:counts['ambiguous_multiple_original_bits']+=1
            if x['levels']==(0,0,0):level_zero+=1
        if 'BDDEFAI.BCS' in z.namelist():
            # Archive's old script is not installed 066S. Only count for provenance.
            b=z.read('BDDEFAI.BCS')
            counts['archived_bcs_bytes']=len(b)
            counts['archived_bcs_cr_markers']=len([line for line in b.splitlines() if line==b'CR'])
    counts['cre_zero_level_templates']=level_zero
    with archive.open('rb') as stream:
        archive_digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return {'artifact':'BGXAI071_READONLY_ARCHIVE_STATISTICS',
            'meaning':'historical CRE template audit; never a live in-game class/kit/dual proof',
            'archive_sha256':archive_digest,
            'stats':dict(sorted(counts.items())),
            'original_class_flag_hints':dict(sorted(originals.items())),
            'class_id_counts':dict(sorted(cids.items(), key=lambda x:int(x[0]))),
            'kit_raw_counts':dict(sorted(kits.items())),
            'no_names_or_cre_bytes_exported':True,
            'installed_066s_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-archive',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(scan(a.source_archive),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
