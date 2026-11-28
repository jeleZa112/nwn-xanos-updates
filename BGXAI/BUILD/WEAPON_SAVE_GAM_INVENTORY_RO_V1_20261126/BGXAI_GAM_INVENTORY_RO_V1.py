#!/usr/bin/env python3
"""Read-only BG(2)EE GAME V2.0 BALDUR.GAM embedded party CRE V1.0 items.

Uses published IESDP structures; rejects other versions rather than guessing.
No game process, no write, no editing save, no installation, no automation.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct,sys
from pathlib import Path

SCHEMA="BGXAI_GAM_V20_PARTY_INVENTORY_SOURCE_RO_V1"
# CRE V1.0 item slots are NOT ordered like SLOTS.IDS.
CRE_TO_RUNTIME=(6,1,9,5,7,8,0,2,3,35,36,37,38,
                11,12,13,14,4,15,16,17,*range(18,34),34)
assert len(CRE_TO_RUNTIME)==38 and len(set(CRE_TO_RUNTIME))==38
class Hold(ValueError):pass
def u16(raw,off):
 if off<0 or off+2>len(raw):raise Hold("HOLD_U16_BOUNDS")
 return struct.unpack_from("<H",raw,off)[0]
def u32(raw,off):
 if off<0 or off+4>len(raw):raise Hold("HOLD_U32_BOUNDS")
 return struct.unpack_from("<I",raw,off)[0]
def piece(raw,off,size):
 if off<0 or size<0 or off+size>len(raw):raise Hold("HOLD_SECTION_BOUNDS")
 return raw[off:off+size]
def checkedres(raw):
 if not raw or len(raw)>8:return None
 raw=raw.split(b"\0",1)[0].rstrip(b" ")
 if not raw or not re.fullmatch(rb"[A-Za-z0-9_#-]{1,8}",raw):
  raise Hold("HOLD_INVALID_RESREF_BYTES")
 return raw.decode("ascii").upper()
def character(raw):
 if raw[:8]!=b"CRE V1.0":raise Hold("HOLD_UNSUPPORTED_CRE_VERSION")
 if len(raw)<0x2d4:raise Hold("HOLD_SHORT_CRE")
 slot_off,item_off,item_count=u32(raw,0x2b8),u32(raw,0x2bc),u32(raw,0x2c0)
 if not 0<=item_count<=1000:raise Hold("HOLD_ITEM_COUNT")
 slots=piece(raw,slot_off,40*2)
 table=piece(raw,item_off,item_count*20)
 allitems=[]
 for i in range(item_count):
  o=i*20
  rr=checkedres(table[o:o+8])
  if not rr:raise Hold("HOLD_EMPTY_ITEM_REFERENCE")
  allitems.append({"resref":rr,
    "expiryRaw":struct.unpack_from("<H",table,o+8)[0],
    "useCount1Raw":struct.unpack_from("<H",table,o+10)[0],
    "useCount2Raw":struct.unpack_from("<H",table,o+12)[0],
    "useCount3Raw":struct.unpack_from("<H",table,o+14)[0],
    "flagsRaw":struct.unpack_from("<I",table,o+16)[0]})
 result={}
 used=set()
 for pos,runtime in enumerate(CRE_TO_RUNTIME):
  ix=u16(slots,pos*2)
  if ix==0xffff:
   result[runtime]={"slot":runtime,"status":"EMPTY"}
  else:
   if ix>=item_count or ix in used:
    raise Hold("HOLD_INVALID_OR_DUPLICATE_CRE_ITEM_INDEX")
   used.add(ix)
   result[runtime]={"slot":runtime,"status":"PRESENT_RAW",
      **allitems[ix],"creItemIndex":ix}
 # Slot 10 (SLOT_FIST) is an implicit engine slot, not one of the 40
 # stored CRE item references; never report it as an observed empty cell.
 result[10]={"slot":10,"status":"UNOBSERVED_IMPLICIT_FIST_SLOT"}
 # Note original raw CRE item slots have two additional entries:
 # selected weapon index and ability (not item table indices).
 selectedWeaponRaw=u16(slots,38*2)
 selectedAbilityRaw=u16(slots,39*2)
 if len(used)!=item_count:
  raise Hold("HOLD_UNREFERENCED_ITEMS_IN_CRE")
 return {"slots":result,"selectedWeaponSlotIndexRaw":selectedWeaponRaw,
   "selectedAbilityRaw":selectedAbilityRaw,"rawInventoryComplete":True,
   "duplicateItemTableReferencesObserved":False}
def parse(raw):
 if type(raw) is not bytes or len(raw)<0xa4 or len(raw)>50_000_000:
  raise Hold("HOLD_GAM_SIZE")
 if raw[:8]!=b"GAMEV2.0":
  raise Hold("HOLD_UNSUPPORTED_GAM_VERSION_NOT_GUESSING")
 table_off,count=u32(raw,0x20),u32(raw,0x24)
 if not 1<=count<=6:raise Hold("HOLD_PARTY_COUNT_NOT_1_TO_6")
 piece(raw,table_off,count*0x160)
 members=[]
 seen=set()
 for i in range(count):
  base=table_off+i*0x160
  party=u16(raw,base+2)
  offset,size=u32(raw,base+4),u32(raw,base+8)
  if party>5 or party in seen:
   raise Hold("HOLD_PARTY_ORDER_UNTRUSTED")
  seen.add(party)
  creature=piece(raw,offset,size)
  data=character(creature)
  nameBytes=piece(raw,base+0xc0,32).split(b"\0",1)[0]
  name=nameBytes.decode("cp1252",errors="replace").strip()
  slots=data["slots"]
  members.append({"partyIndex":party,"nameLabel":name,
     "actorIdNotAvailableInSave":True,
     "sourceSlots18to33":[slots[x] for x in range(18,34)],
     "quickWeaponSlots35to38":[slots[x] for x in range(35,39)],
     "topLevelSlots":[slots[x] for x in range(39)],
     "freeQuickSlotCandidates":[x for x in range(35,39) if slots[x]["status"]=="EMPTY"],
     "creVersion":"V1.0",
     "selectedWeaponSlotIndexRaw":data["selectedWeaponSlotIndexRaw"],
     "selectedAbilityRaw":data["selectedAbilityRaw"]})
 members.sort(key=lambda r:r["partyIndex"])
 return {"schema":SCHEMA,"status":"SAVED_PARTY_GAM_READONLY_PARSED_NOT_LIVE_GAME",
   "gameVersion":"GAMEV2.0","partyMembers":members,
   "gamSha256":hashlib.sha256(raw).hexdigest(),
   "userGameRuntimeItemPresentVerified":False,
   "saveMatchesCurrentlyLoadedSessionVerified":False,
   "classKitWeaponSlotCapacityVerified":False,
   "currentItemUniqueAcrossContainersVerified":False,
   "partyActorEngineIdVerified":False,
   "implicitFistSlotObserved":False,
   "gameModified":False,"filesWritten":0,
   "ordersSent":0,"dispatchAuthorized":False}
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--gam",type=Path,required=True)
 p.add_argument("--max-bytes",type=int,default=50_000_000)
 args=p.parse_args(argv)
 try:
  if args.gam.is_symlink() or not args.gam.is_file():raise Hold("HOLD_FILE_NOT_REGULAR")
  if args.gam.stat().st_size>min(args.max_bytes,50_000_000):
   raise Hold("HOLD_GAM_TOO_LARGE")
  d=parse(args.gam.read_bytes())
  print(json.dumps(d,ensure_ascii=False,indent=2))
  return 0
 except (Hold,OSError,ValueError,TypeError,struct.error) as e:
  print(json.dumps({"schema":SCHEMA,"status":"HOLD_GAM_INVENTORY_READONLY",
    "reason":str(e),"gameModified":False,"ordersSent":0,"dispatchAuthorized":False}))
  return 3
if __name__=="__main__":raise SystemExit(main())
