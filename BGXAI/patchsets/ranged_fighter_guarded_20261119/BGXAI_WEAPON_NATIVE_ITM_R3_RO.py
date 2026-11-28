#!/usr/bin/env python3
"""BGXAI weapon R3 native RESOURCE AUDIT, read-only for exact EET installation.

Reads only resources named by verified R2 records, WSPATCK/CLSWPBON, and
bounded linked spells. ZIP snapshot is supported only for OFFLINE evaluation.
Never changes the game, selects weapons, or validates EPS/manual action state.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import sys
import zipfile
import zlib

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
R2_NAME = 'BGXAI_WEAPON_SLOTS_RAW_R2.jsonl'
REPORT_NAME = 'BGXAI_WEAPON_NATIVE_ITM_R3.json'
RESREF = re.compile(r'^[A-Z0-9_#\-]{1,8}$')
LIMIT_RESOURCE = 2_000_000
LIMIT_KEY = 12_000_000
LIMIT_BIF = 64_000_000
LIMIT_REPORT = 12_000_000
RES_TYPES = {'.ITM': 0x03ed, '.SPL':0x03ee, '.2DA':0x03f4}

class Hold(ValueError):
    pass

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def u8(b,off):return b[off]
def u16(b,off):return struct.unpack_from('<H',b,off)[0]
def s16(b,off):return struct.unpack_from('<h',b,off)[0]
def u32(b,off):return struct.unpack_from('<I',b,off)[0]
def resref(b):
    s=b.split(b'\x00',1)[0]
    try:r=s.decode('ascii').upper()
    except UnicodeError:return None
    return r if RESREF.fullmatch(r) else None

def bounds(b,start,size,label):
    if start<0 or size<0 or start+size>len(b):raise Hold('RESOURCE_OFFSET_OUTSIDE:'+label)

def _effects(b, off, start, count, label):
    if count>2048:raise Hold('EFFECT_COUNT_OVER_LIMIT:'+label)
    bounds(b,off+start*48,count*48,label)
    result=[]
    for i in range(start,start+count):
        p=off+i*48
        result.append({'index':i,'opcodeRaw':u16(b,p),'targetRaw':u8(b,p+2),
          'parameter1Raw':u32(b,p+4),'parameter2Raw':u32(b,p+8),
          'timingRaw':u8(b,p+12),'probability1Raw':u8(b,p+18),
          'probability2Raw':u8(b,p+19),'resourceRaw':resref(b[p+20:p+28])})
    return result

def parse_itm(b:bytes):
    if len(b)<114 or len(b)>LIMIT_RESOURCE or b[:8]!=b'ITM V1  ':
        raise Hold('ITM_FORMAT_OR_SIZE_UNSUPPORTED')
    off=u32(b,0x64);n=u16(b,0x68);fx=u32(b,0x6a)
    if n>64:raise Hold('ITM_ABILITY_COUNT_EXCESS')
    bounds(b,off,56*n,'ITM_ABILITIES')
    if fx<114 or fx>len(b):raise Hold('ITM_EFFECT_TABLE_INVALID')
    equip=_effects(b,fx,u16(b,0x6e),u16(b,0x70),'ITM_EQUIPPED')
    abilities=[]
    for i in range(n):
        p=off+i*56
        ef=_effects(b,fx,u16(b,p+0x20),u16(b,p+0x1e),'ITM_ABILITY_EFFECTS')
        dice=u8(b,p+0x18);sides=u8(b,p+0x16);dmg=s16(b,p+0x1a)
        abilities.append({'abilityIndex':i,'attackTypeRaw':u8(b,p),'locationRaw':u8(b,p+2),
         'rangeRaw':u16(b,p+0xe),'launcherRequiredRaw':u8(b,p+0x10),
         'speedRaw':u8(b,p+0x12),'thac0BonusRaw':s16(b,p+0x14),
         'diceCountRaw':dice,'diceSidesRaw':sides,'damageBonusRaw':dmg,
         'baseDamageMeanBeforeEffects':round(dice*(sides+1)/2+dmg,4) if dice<=50 and sides<=100 else None,
         'damageTypeRaw':u16(b,p+0x1c),'abilityFlagsRaw':u32(b,p+0x26),
         'effects':ef,'effectiveDamageAndAPRVerified':False})
    return {'schema':'BGXAI_ITM_RAW_V1','itemTypeRaw':u16(b,0x1c),
        'itemFlagsRaw':u32(b,0x18),'twoHandedFlagRaw':bool(u32(b,0x18)&2),
        'proficiencyIdRaw':u8(b,0x31),'enchantmentRaw':u32(b,0x60),
        'minStrengthRaw':u16(b,0x26),'maxStackRaw':u16(b,0x38),
        'abilities':abilities,'equippedEffects':equip,'rawOnly':True,
        'activeBuffsVerified':False,'engineEffectsAppliedVerified':False,
        'characterCanEquipVerified':False,'targetImmunityVerified':False}

def parse_spl(b:bytes):
    if len(b)<114 or len(b)>LIMIT_RESOURCE or b[:8]!=b'SPL V1  ':
        raise Hold('SPL_FORMAT_OR_SIZE_UNSUPPORTED')
    off=u32(b,0x64);n=u16(b,0x68);fx=u32(b,0x6a)
    if n>64:raise Hold('SPL_ABILITY_COUNT_EXCESS')
    bounds(b,off,40*n,'SPL_ABILITIES')
    if fx<114 or fx>len(b):raise Hold('SPL_EFFECT_TABLE_INVALID')
    return {'schema':'BGXAI_SPL_RAW_V1','castingEffects':_effects(b,fx,u16(b,0x6e),u16(b,0x70),'SPL_CASTING'),
      'abilities':[{'abilityIndex':i,'effects':_effects(b,fx,u16(b,off+40*i+0x20),u16(b,off+40*i+0x1e),'SPL_ABILITY')}
      for i in range(n)],'effectSemanticsVerified':False}

def _zlimited(c:bytes, size:int)->bytes:
    if not 0<=size<=LIMIT_BIF:raise Hold('COMPRESSED_BIF_TOO_LARGE')
    obj=zlib.decompressobj()
    try:
        out=obj.decompress(c,size+1)
        if len(out)>size or obj.unconsumed_tail:raise Hold('COMPRESSED_BIF_LIMIT_EXCEEDED')
        out+=obj.flush()
    except zlib.error as e:raise Hold('BIF_ZLIB_INVALID') from e
    if len(out)!=size or not obj.eof or obj.unused_data:
        raise Hold('BIF_DECOMPRESSION_LENGTH_MISMATCH')
    return out

def expand_bif(path:Path):
    size=path.stat().st_size
    with path.open('rb') as f:header=f.read(12)
    # Uncompressed BIFF V1 is streamed directly in read_bif_resource.
    if header[:8]==b'BIF V1.0':
        fnlen=u32(header,8)
        if not 1<=fnlen<=260:raise Hold('COMPRESSED_BIF_FILENAME_INVALID')
        with path.open('rb') as f:
            f.seek(12+fnlen); meta=f.read(8)
            if len(meta)!=8:raise Hold('COMPRESSED_BIF_HEADER_TRUNCATED')
            unpacked,packed=struct.unpack('<II',meta)
            if packed>LIMIT_BIF or 20+fnlen+packed!=size:raise Hold('COMPRESSED_BIF_LENGTH_UNSAFE')
            blob=f.read(packed)
        return io.BytesIO(_zlimited(blob,unpacked))
    if header[:8]==b'BIFCV1.0':
        out=bytearray();limit=u32(header,8)
        if limit>LIMIT_BIF:raise Hold('CHUNKED_BIF_TOO_LARGE')
        with path.open('rb') as f:
            f.seek(12)
            while len(out)<limit:
                chunk=f.read(8)
                if len(chunk)!=8:raise Hold('BIFC_BLOCK_TRUNCATED')
                un,packed=struct.unpack('<II',chunk)
                if not 1<=un<=8192*64 or packed>LIMIT_BIF or len(out)+un>limit:
                    raise Hold('BIFC_BLOCK_SIZE_INVALID')
                data=f.read(packed)
                if len(data)!=packed:raise Hold('BIFC_BLOCK_DATA_SHORT')
                out.extend(_zlimited(data,un))
            if f.read(1):raise Hold('BIFC_TRAILING_BYTES')
        return io.BytesIO(out)
    raise Hold('BIF_FORMAT_UNSUPPORTED:'+header[:8].hex())

def _read_biff(stream,length,loc,rtype):
    stream.seek(0);h=stream.read(20)
    if len(h)!=20 or h[:8]!=b'BIFFV1  ':
        # IESDP signature is four bytes BIFF followed by four bytes V1 [space][space].
        raise Hold('BIFF_V1_HEADER_INVALID')
    count=u32(h,8);table=u32(h,16)
    if count>100000 or table<20 or table+count*16>length:
        raise Hold('BIFF_TABLE_OUTSIDE')
    target=loc&0x3fff
    found=None
    stream.seek(table)
    for _ in range(count):
        entry=stream.read(16)
        if len(entry)!=16:raise Hold('BIFF_ENTRY_TRUNCATED')
        locator,off,size,typ=struct.unpack_from('<IIIH',entry)
        if (locator&0x3fff)==target and typ==rtype:
            if found is not None:raise Hold('BIFF_DUPLICATE_RESOURCE_INDEX')
            found=(off,size)
    if found is None:raise Hold('BIFF_RESOURCE_INDEX_NOT_FOUND')
    off,size=found
    if not 1<=size<=LIMIT_RESOURCE or off<20 or off+size>length:
        raise Hold('BIFF_RESOURCE_OFFSET_INVALID')
    stream.seek(off);data=stream.read(size)
    if len(data)!=size:raise Hold('BIFF_RESOURCE_TRUNCATED')
    return data

def _safe_game_file(root:Path,rel:str)->Path:
    norm=rel.replace('\\','/').strip('/')
    parts=norm.split('/')
    if not parts or any(not p or p in ('.','..') or ':' in p for p in parts):
        raise Hold('KEY_BIF_PATH_UNSAFE')
    path=root
    for p in parts:
        path=path/p
        if path.is_symlink():raise Hold('BIF_SYMLINK_UNSAFE')
    if not path.is_file():raise Hold('BIF_NOT_FOUND:'+norm)
    return path

class NativeSource:
    def __init__(self,root:Path):
        if root.is_symlink() or not root.is_dir():raise Hold('GAME_ROOT_UNSAFE')
        self.root=root;self.key_path=root/'chitin.key'
        if self.key_path.is_symlink() or not self.key_path.is_file() or self.key_path.stat().st_size>LIMIT_KEY:
            raise Hold('CHITIN_KEY_UNSAFE')
        self.key=self.key_path.read_bytes()
        if len(self.key)>LIMIT_KEY or self.key[:8]!=b'KEY V1  ' or len(self.key)<24:
            raise Hold('CHITIN_KEY_FORMAT_UNSUPPORTED')
        self.count_bif=u32(self.key,8); self.count_res=u32(self.key,12)
        self.bif_off=u32(self.key,16);self.res_off=u32(self.key,20)
        if self.count_bif>8192 or self.count_res>500000:
            raise Hold('CHITIN_KEY_TOO_MANY_RESOURCES')
        bounds(self.key,self.bif_off,self.count_bif*12,'KEY_BIF_TABLE')
        bounds(self.key,self.res_off,self.count_res*14,'KEY_RESOURCE_TABLE')
        self.index={}
        for i in range(self.count_res):
            p=self.res_off+i*14
            name=resref(self.key[p:p+8]);typ=u16(self.key,p+8);loc=u32(self.key,p+10)
            if name and typ in RES_TYPES.values():
                key=(name,typ)
                if key in self.index:raise Hold('CHITIN_KEY_DUPLICATE_RESOURCE:'+name)
                self.index[key]=loc
    def get(self,ref:str,extension:str):
        key=ref.upper()+extension.upper()
        if not RESREF.fullmatch(ref.upper()) or extension.upper() not in RES_TYPES:
            raise Hold('RESOURCE_NAME_OR_TYPE_UNSAFE')
        # Override precedence is used only for resource bytes; no user files modified.
        for name in [key.upper(),key.lower()]:
            over=self.root/'override'/name
            if over.is_symlink():raise Hold('OVERRIDE_SYMLINK')
            if over.is_file():
                if over.stat().st_size>LIMIT_RESOURCE:raise Hold('OVERRIDE_RESOURCE_TOO_LARGE')
                data=over.read_bytes()
                return data,{'origin':'CURRENT_GAME_OVERRIDE','source':str(over),'sha256':sha(data)}
        loc=self.index.get((ref.upper(),RES_TYPES[extension.upper()]))
        if loc is None:raise Hold('RESOURCE_NOT_IN_CHITIN_KEY:'+key)
        bix=loc>>20
        if bix>=self.count_bif:raise Hold('KEY_BIF_INDEX_OUTSIDE')
        e=self.bif_off+bix*12
        namelen=u16(self.key,e+8);nameoff=u32(self.key,e+4)
        if not 1<=namelen<=260:raise Hold('KEY_BIF_NAME_LENGTH')
        bounds(self.key,nameoff,namelen,'KEY_BIF_NAME')
        path=_safe_game_file(self.root,self.key[nameoff:nameoff+namelen].split(b'\0',1)[0].decode('latin-1'))
        with path.open('rb') as f:h=f.read(8)
        if h==b'BIFFV1  ':
            with path.open('rb') as f: data=_read_biff(f,path.stat().st_size,loc,RES_TYPES[extension.upper()])
        else:
            expanded=expand_bif(path)
            data=_read_biff(expanded,len(expanded.getbuffer()),loc,RES_TYPES[extension.upper()])
        return data,{'origin':'CURRENT_GAME_BIFF','source':str(path),'sha256':sha(data),
                     'bifIndexRaw':bix,'resourceIndexRaw':loc&0x3fff}

class ArchiveSource:
    """Offline only: inspect old provided ZIP. Never imply current game exactness."""
    def __init__(self,path:Path):
        if path.is_symlink() or not path.is_file() or path.stat().st_size>50_000_000:
            raise Hold('ARCHIVE_SOURCE_UNSAFE')
        self.archive=zipfile.ZipFile(path)
        names=self.archive.namelist()
        if len(names)>30000:raise Hold('ARCHIVE_ENTRY_COUNT')
        self.names={}
        for n in names:
            k=n.upper()
            if k in self.names:raise Hold('ARCHIVE_CASE_COLLISION:'+k)
            self.names[k]=n
        self.origin=sha(path.read_bytes())
    def get(self,ref:str,extension:str):
        name=ref.upper()+extension.upper()
        actual=self.names.get(name)
        if not actual:raise Hold('ARCHIVE_RESOURCE_MISSING:'+name)
        meta=self.archive.getinfo(actual)
        if not 0<meta.file_size<=LIMIT_RESOURCE:raise Hold('ARCHIVE_RESOURCE_SIZE_UNSAFE')
        data=self.archive.read(actual)
        return data,{'origin':'OLDER_USER_ZIP_NOT_CURRENT','source':actual,'sha256':sha(data)}

def parse_2da(data:bytes):
    # Only decode plain, bounded 2DA V1.0 tables. Encrypted/unknown -> HOLD.
    if len(data)>100000:raise Hold('2DA_TOO_LARGE')
    try:src=data.decode('utf-8-sig')
    except UnicodeError:raise Hold('2DA_ENCODING_UNSUPPORTED')
    lines=[x.split('//',1)[0].strip() for x in src.splitlines()]
    lines=[x for x in lines if x]
    if len(lines)<3 or not re.fullmatch(r'2DA\s+V1\.0',lines[0],flags=re.I):
        raise Hold('2DA_VERSION_UNKNOWN')
    default=lines[1].split()
    if len(default)!=1:raise Hold('2DA_DEFAULT_VALUE_INVALID')
    columns=lines[2].split()
    if not 1<=len(columns)<=80 or len(set(columns))!=len(columns):
        raise Hold('2DA_COLUMNS_INVALID')
    rows={}
    if len(lines)>4000:raise Hold('2DA_TOO_MANY_ROWS')
    for line in lines[3:]:
        parts=line.split()
        if len(parts)!=len(columns)+1:raise Hold('2DA_ROW_SHAPE_INVALID')
        if parts[0] in rows:raise Hold('2DA_DUPLICATE_ROW')
        rows[parts[0]]=dict(zip(columns,parts[1:]))
    return {'defaultRaw':default[0],'columns':columns,'rows':rows,'rowCount':len(rows),
            'semanticsAndCharacterRowVerified':False}

def _read_r2(path:Path):
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=LIMIT_REPORT:
        raise Hold('R2_REPORT_MISSING_UNSAFE')
    session=ready=False;actors={};last=None
    for line in path.read_text(encoding='utf-8').splitlines():
        try:e=json.loads(line)
        except ValueError:continue
        if not isinstance(e,dict):continue
        if e.get('type')=='SESSION' and e.get('schema')=='BGXAI_WEAPON_SLOTS_RAW_R2':session=True;ready=False;actors={}
        elif session and e.get('type')=='READY' and e.get('hookRegistered') is True:ready=True
        elif session and ready and e.get('type')=='SLOTS' and e.get('schema')=='BGXAI_WEAPON_SLOTS_RAW_R2':
            if type(e.get('actor')) is not int or not 0<=e['actor']<=2147483647:continue
            if type(e.get('seq')) is not int or not 1<=e['seq']<=64:continue
            actor=e['actor'];actors[actor]=e
            last=e
    if not actors:raise Hold('R2_REPORT_NO_VALID_SLOTS')
    names=set()
    for e in actors.values():
        for slot in (e.get('quickWeapons') or [])+(e.get('quivers') or [])+[e.get('offhand')]:
            if not isinstance(slot,dict):continue
            name=slot.get('resrefRaw')
            if isinstance(name,str) and RESREF.fullmatch(name.upper()):names.add(name.upper())
    if len(names)>48:raise Hold('R2_TOO_MANY_ITEM_REFERENCES')
    return sorted(names),{'actorCount':len(actors),'lastSeq':last.get('seq'),'lastActor':last.get('actor')}

def audit(source, names, snapshot=None):
    info={};missing=[];linked={}
    for ref in names:
        try:
            data,prov=source.get(ref,'.ITM')
            itm=parse_itm(data)
            info[ref]={'resource':ref,'provenance':prov,'item':itm}
            for ability in itm['abilities']:
                for eff in ability['effects']:
                    if eff['opcodeRaw']==146 and eff['resourceRaw']:
                        linked[eff['resourceRaw']]=None
        except (Hold,OSError,struct.error,zipfile.BadZipFile) as ex:
            missing.append({'resource':ref+'.ITM','reason':str(ex)[:180]})
    links={}
    for ref in sorted(linked):
        try:
            data,prov=source.get(ref,'.SPL')
            links[ref]={'provenance':prov,'spell':parse_spl(data),'effectCompletionVerified':False}
        except (Hold,OSError,struct.error,zipfile.BadZipFile) as ex:
            links[ref]={'status':'LINKED_SPELL_UNAVAILABLE','reason':str(ex)[:180]}
            missing.append({'resource':ref+'.SPL','reason':str(ex)[:180]})
    tables={}
    for ref in ('WSPATCK','CLSWPBON'):
        try:
            data,prov=source.get(ref,'.2DA')
            if len(data)>100000:raise Hold('2DA_TOO_LARGE')
            parsed=parse_2da(data)
            tables[ref]={'provenance':prov,'bytes':len(data),
               'contentsParsed':True,'table':parsed,'aprProvenanceBoundToActor':False}
        except (Hold,OSError) as ex:tables[ref]={'status':'MISSING_OR_UNSUPPORTED','reason':str(ex)[:180]}
    return {'schema':'BGXAI_WEAPON_NATIVE_ITM_R3_READONLY','status':'ITM_NATIVE_ALL_ITEMS_RAW_READ' if not missing else 'ITM_NATIVE_PARTIAL_HOLD',
      'sourceKind':'CURRENT_GAME' if isinstance(source,NativeSource) else 'OLDER_USER_ZIP_SNAPSHOT',
      'r2SnapshotSummary':snapshot or {},'requestedItems':names,'items':info,'linkedSpells':links,
      'aprtables':tables,'missingItemsOrLinkedSpells':missing,
      'targetImmuneOrResistantVerified':False,'launcherAmmoPairVerified':False,
      'currentCharacterBuffsVerified':False,'proficiencyAlreadyAppliedVerified':False,
      'aprPerSlotVerified':False,'fullWeaponEffectsVerified':False,
      'manualAndEPSQueueVerified':False,'gameModified':False,
      'executable':False,'weaponSwitchAuthorized':False,'dispatchAuthorized':False}

def audit_r37_top_level(source, capture:dict):
    """Reuse R3's EXISTING ITM/2DA/BIF parser for R37's 39-slot raw map.

    It is not an EEex callback, native observer, or live actor APR adapter.
    Lua JSON numeric slot keys become strings; reject ambiguous aliases.
    """
    if not isinstance(capture,dict) or (
        capture.get('schema')!='BGXAI_BACKPACK16_R37_DOUBLE_READ_RO_V3' or
        capture.get('status')!='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY' or
        capture.get('sourceOnly') is not True or
        capture.get('readOnly') is not True or
        capture.get('rawInventoryDoubleRead') is not True or
        capture.get('r37QuickQuiverOffhandMatched') is not True or
        capture.get('rawSnapshotDriftObserved') is not False or
        capture.get('nativeInstanceIdentityVerified') is not False or
        capture.get('alternativeAPRVerified') is not False or
        capture.get('dispatchAuthorized') is not False or
        capture.get('inventoryMoveAuthorized') is not False or
        capture.get('topLevelSlotsCount')!=39):
        raise Hold('R37_TOPLEVEL_CAPTURE_UNTRUSTED_OR_INCOMPLETE')
    actor=capture.get('actorId')
    if type(actor) is not int or not 1<=actor<=2147483647:
        raise Hold('R37_ACTOR_ID_INVALID')
    bag=capture.get('backpack')
    if not isinstance(bag,dict) or (
        bag.get('status')!='BACKPACK16_RAW_NOT_INSTANCE_PROOF' or
        bag.get('actorId')!=actor or
        not isinstance(bag.get('slots'),dict)):
        raise Hold('R37_BACKPACK_CONTEXT_INVALID')
    groups=((bag['slots'],list(range(18,34)),'BACKPACK'),
            (capture.get('quick'),list(range(35,39)),'QUICK'),
            (capture.get('other'),list(range(0,18))+[34],'OTHER'))
    all_slots={}; seen={}
    for slots,indices,group in groups:
        if not isinstance(slots,dict) or len(slots)!=len(indices):
            raise Hold('R37_SLOT_MAP_SHAPE_INVALID:'+group)
        for slot in indices:
            a=slots.get(slot); b=slots.get(str(slot))
            # If both Lua numeric and serialized string aliases occur, HOLD.
            if a is not None and b is not None:
                raise Hold('R37_SLOT_ALIAS_COLLISION:'+group)
            item=a if a is not None else b
            if not isinstance(item,dict) or type(item.get('slot')) is not int or item['slot']!=slot:
                raise Hold('R37_SLOT_MISSING_OR_INDEX_CHANGED:'+group)
            status=item.get('status')
            if status=='EMPTY':
                if item.get('resref') is not None:
                    raise Hold('R37_EMPTY_SLOT_HAS_RESREF:'+group)
                name=None
            elif status=='PRESENT_RAW':
                name=item.get('resref')
                if not isinstance(name,str) or not RESREF.fullmatch(name) or name!=name.upper():
                    raise Hold('R37_SLOT_RESREF_UNSAFE:'+group)
                for field in ('flagsRaw','useCount1Raw','useCount2Raw','useCount3Raw'):
                    value=item.get(field)
                    upper=4294967295 if field=='flagsRaw' else 65535
                    if type(value) is not int or not 0<=value<=upper:
                        raise Hold('R37_SLOT_RAW_ITEM_INCOMPLETE:'+group)
                seen[name]=seen.get(name,0)+1
            else:
                raise Hold('R37_SLOT_UNSUPPORTED_STATUS:'+group)
            all_slots[slot]={'slot':slot,'status':status,'resref':name}
        if {str(x) for x in slots} != {str(x) for x in indices}:
            raise Hold('R37_SLOT_MAP_EXTRAS:'+group)
    if len(all_slots)!=39:
        raise Hold('R37_TOPLEVEL_COUNT_INCORRECT')
    names=sorted(seen)
    if len(names)>39:
        raise Hold('R37_RESOURCE_COUNT_EXCESS')
    report=audit(source,names,{'origin':'R37_39_SLOT_RAW_MAP_SOURCE_ONLY',
                               'topLevelRawSlots':39,'distinctResrefs':len(names)})
    report.update({
        'inventoryLinkSchema':'BGXAI_R3_R37_TOPLEVEL_ITM_JOIN_SOURCE_ONLY_V1',
        'inventoryRawMap':all_slots,
        'duplicateTopLevelResrefs':sorted(k for k,v in seen.items() if v>1),
        'itemAbilityStrideFromITMBytes':56,
        'allAlternateItemEffectsVerified':False,
        'nativeRuntimeInventorySnapshotAuthenticated':False,
        'nativeCurrentAlternativeAPRVerified':False,
        'actorTargetBound':False,
        'safeManualEpsRoundBoundaryVerified':False,
        'inventoryTransferAuthorized':False,
        'dispatchAuthorized':False,
        'gameModified':False,
    })
    return report


def native_run(root:Path=GAME):
    if os.name!='nt' or os.path.normcase(os.path.abspath(root))!=os.path.normcase(os.path.abspath(GAME)):
        raise Hold('EXACT_WINDOWS_GAME_ROOT_ONLY')
    if not (root/'chitin.key').is_file():raise Hold('GAME_NOT_PRESENT')
    home=os.environ.get('USERPROFILE')
    if not home:raise Hold('USERPROFILE_MISSING')
    report=Path(home)/'Documents'/'BGXAI_LIVE_REPORTS'
    if report.is_symlink() or not report.is_dir():raise Hold('LIVE_REPORT_DIR_MISSING_OR_SYMLINK')
    names,context=_read_r2(report/R2_NAME)
    src=NativeSource(root)
    result=audit(src,names,context)
    out=report/REPORT_NAME
    if out.is_symlink():raise Hold('REPORT_SYMLINK')
    # Avoid replacing earlier evidence; fail closed if the report already exists.
    with out.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
        f.write('\n')
    return {'status':result['status'],'report_file':str(out),'source':'CURRENT_GAME','total_items':len(names),
      'resource_bytes_read':len(result['items']),'unresolved':len(result['missingItemsOrLinkedSpells']),
      'game_modified':False,'weapon_switch_authorized':False}

if __name__=='__main__':
    if '--archive-snapshot' in sys.argv:
        idx=sys.argv.index('--archive-snapshot')
        z=ArchiveSource(Path(sys.argv[idx+1]));names=['SW1H04','BOW05','AROW01','STAF01','SHLD03A']
        print(json.dumps(audit(z,names),ensure_ascii=False,indent=2))
    else:
        try:r=native_run();print(json.dumps(r,ensure_ascii=False,indent=2))
        except (Hold,OSError) as exc:
            print(json.dumps({'status':'R3_READONLY_HOLD','reason':str(exc),'game_modified':False},ensure_ascii=False))
            sys.exit(2)
