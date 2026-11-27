"""BG_EET_RU V158 -- fresh read-only provenance capture.

This module cannot install, write or compile anything in the game. It reads
only WeiDU.log, five known DLGs in override and V157 TLKs, and returns JSON.
Its output is a provenance observation, not an installer or gameplay proof.
"""
from __future__ import annotations
import hashlib
import os
import re
import struct
from pathlib import Path

SCHEMA='BG_EET_RU_V158_FRESH_BANTER_BRANCH_PROVENANCE_RO'
EXPECTED=(
 (10000,'DDAMIEN',0,304617),(10003,'DDAMIEN',11,304651),
 (10133,'DHROTH',5,306470),(10158,'DHROTH',29,306523),
 (10163,'DHROTH',31,306526),(10166,'DHROTH',35,306534),
 (10179,'DHERMIT',0,306102),(10189,'DHERMIT',0,306102),
 (10275,'DMIREK',6,307815),(10287,'DWEENOG',1,310131)
)
DLG_BASELINE={
 'DDAMIEN':'fb0aa5959f0a6083d439d26f9f8058fa4b77010564d10f23997abc6d68d9ee99',
 'DHROTH':'b5383a8e08d2b7192168e6e02e8e2bfaf2ed8b6ec7ae9205738d3b0be45e5dac',
 'DHERMIT':'327cd9952938995f0ffd93c9e5c3f2be46571d6f9a2d0a0ce36550c666e1f5d9',
 'DMIREK':'f189ad29e2009e5997f072da135e20368ccd93b6a628433969963f390767ad07',
 'DWEENOG':'8bb8c408f29d6de7295b016f0d5680cf9eb7fa25765b162ffa368b7e891948f3'
}
DLG_ISOLATED={
 'DDAMIEN':'50e4c1dd1985c7bd74eec7769ba5c6868a807557f4e5ee552b7417b54f6b7a37',
 'DHROTH':'26c6dee28dad30507b98c8357338e229c4ad4279082a3a14c1e352c82147f78f',
 'DHERMIT':'72e6fd24244557275641ce586a06e1a8d713ba768cd50b5f7a6f95fe0d057675',
 'DMIREK':'3628a452d756d597fc191f956df7ffad9608459df993fdf5f4de6c9a1c77ba97',
 'DWEENOG':'5a15d8e286568202f5a1cb4e06f45886f64df6c610650d8ec16622bbb7d82296'
}
V157_TLK={
 'dialog.tlk':'8d61cd3805e450f4c09ec1c4c476e2ae5302a0cf2cb9d69f793d236389944b02',
 'dialogf.tlk':'795c07e88a6c4575201ec43cbd2ea730d045c501d48407d5c1df81f851a7e2e6'
}
WEIDU_COMPONENT=re.compile(r'^\s*~([^~\r\n]{1,260}\.TP2)~\s*#\s*(\d{1,5})\s*#\s*(\d{1,5})(?:\s|$)',re.I)
GROUPS=('IWD1_EET','IWD2_EET','IWD_PARTY_BANTER','HOW_EET','TOTLM')


def _hash(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _safe_regular(p:Path,max_size:int):
    if p.is_symlink() or not p.is_file():
        raise ValueError('MISSING_OR_UNSAFE:'+p.name)
    sz=p.stat().st_size
    if sz>max_size or sz<=0:
        raise ValueError('SIZE_UNSAFE:'+p.name)
    return sz


def _one_casefold(parent:Path,name:str):
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError('UNSAFE_DIRECTORY')
    matches=[p for p in parent.iterdir() if p.name.casefold()==name.casefold()]
    if len(matches)!=1:
        raise ValueError('EXACT_ONE_REQUIRED:'+name+':'+str(len(matches)))
    return matches[0]


def _sha_file(p:Path,max_size=120_000_000):
    size=_safe_regular(p,max_size)
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest(),size


def _group(tp2:str):
    basename=tp2.replace('\\','/').rsplit('/',1)[-1].upper()
    if not basename.endswith('.TP2'): return None
    stem=basename[:-4]
    if stem.startswith('SETUP-'):stem=stem[6:]
    if stem in GROUPS:return stem
    if stem in ('IWD_EET-PARTY-BANTER','IWD_EET_PARTY_BANTER','IWD_EET-PARTY_BANTER'):
        return 'IWD_PARTY_BANTER'
    return None


def parse_weidu(raw:bytes):
    if len(raw)>10_000_000:raise ValueError('WEIDU_LOG_TOO_LARGE')
    if raw.startswith((b'\xff\xfe',b'\xfe\xff')):
        t=raw.decode('utf-16')
    elif b'\x00' in raw[:1024]:
        raise ValueError('WEIDU_NUL_OR_UNMARKED_UTF16_HOLD')
    else:
        t=raw.decode('latin-1')  # ASCII TP2 paths survive legacy ANSI or UTF-8 titles
    entries=[];invalid_relevant=[]
    for i,line in enumerate(t.splitlines(),1):
        m=WEIDU_COMPONENT.match(line)
        if m:
            group=_group(m.group(1))
            if group:
                entries.append({'line_number':i,'group':group,'language_index':int(m.group(2)),
                                'component':int(m.group(3)),'tp2':m.group(1)})
        elif re.search(r'(?i)IWD[12][_\-]EET|IWD.EET.PARTY.BANTER',line):
            invalid_relevant.append(i)
    groups={g:sorted(set(e['component'] for e in entries if e['group']==g)) for g in GROUPS}
    iwd1=0 in groups['IWD1_EET'];iwd2=1 in groups['IWD2_EET']
    return {'sha256':_hash(raw),'bytes':len(raw),'lines':len(t.splitlines()),
            'groups':groups,'relevant_entries':entries[:100],
            'unparsed_relevant_line_numbers':invalid_relevant[:30],
            'iwd1_component_0_in_this_log':iwd1,
            'iwd2_component_1_in_this_log':iwd2,
            'main_branch_component_prerequisites_in_this_log':iwd1 and iwd2,
            'log_exhaustive_history_proven':False,
            'not_listed_means_not_proven_not_absent':True}


def _dlg(raw:bytes,dlgname:str):
    if len(raw)<52 or raw[:8]!=b'DLG V1.0':raise ValueError('INVALID_DLG_HEADER:'+dlgname)
    st_count,st_offset,tr_count,tr_offset=struct.unpack_from('<IIII',raw,8)
    if st_count>100000 or tr_count>250000 or st_offset<52 or tr_offset<52 or st_offset+st_count*16>len(raw) or tr_offset+tr_count*32>len(raw):
        raise ValueError('INVALID_DLG_TABLE:'+dlgname)
    rows=[]
    for id,n,idx,old_ref in EXPECTED:
        if n!=dlgname:continue
        if idx>=st_count:raise ValueError('EXPECTED_STATE_MISSING:'+dlgname)
        ref,first,num,trigger=struct.unpack_from('<IIII',raw,st_offset+idx*16)
        if first+num>tr_count:raise ValueError('DLG_TRANSITION_RANGE:'+dlgname)
        rows.append({'tra_id':id,'state_index':idx,'state_strref':ref,'old_state_strref_equal':ref==old_ref,
                     'state_transition_count':num})
    sha=_hash(raw)
    baseline=sha==DLG_BASELINE[dlgname]
    return {'dlg':dlgname,'sha256':sha,'bytes':len(raw),
            'state_count':st_count,'transition_count':tr_count,'snapshot_baseline_equal':baseline,
            'isolated_compiled_sha_equal':sha==DLG_ISOLATED[dlgname],
            'state_guards_original':all(x['old_state_strref_equal'] for x in rows),
            'tracked_states':rows}


def audit_game(game_root):
    """Returns a JSON-ready result; reads game assets, NEVER writes to game or external disk."""
    game=Path(game_root)
    report={'schema':SCHEMA,'status':'V158_READONLY_PROVENANCE_CAPTURE',
            'scope':'FRESH_GAME_DISK','game_files_written':0,'install_allowed':False,
            'dialogue_changes_installed_by_this_audit':0,'banter_runtime_visibility_proven':False,
            'weidu_main_branch_installed_proven':False,
            'limitations':['This reads current WeiDU.log, not deleted or archived WeiDU history.',
                           'Source DLG state references do not establish gameplay reachability.',
                           'No WeiDU install, decompile, dialogue/TLK patch or new updater performed.']}
    try:
        if game.is_symlink() or not game.is_dir() or not (game/'chitin.key').is_file():
            raise ValueError('GAME_ROOT_UNSAFE')
        log=_one_casefold(game,'WeiDU.log');_safe_regular(log,10_000_000)
        report['weidu']=parse_weidu(log.read_bytes())
    except (OSError,ValueError) as e:
        report['status']='V158_READONLY_SOURCE_HOLD';report['hold_weidu']=str(e)[:160]
        report['weidu']=None
    try:
        target=game/'override'
        rows=[]
        for name in sorted(DLG_BASELINE):
            path=_one_casefold(target,name+'.DLG');_safe_regular(path,30_000_000)
            rows.append(_dlg(path.read_bytes(),name))
        report['dlgs']=rows
        report['dlg_baseline_equal_count']=sum(x['snapshot_baseline_equal'] for x in rows)
        report['dlg_all_snapshot_baselines_equal']=all(x['snapshot_baseline_equal'] for x in rows)
        report['dlg_all_state_anchors_unchanged']=all(x['state_guards_original'] for x in rows)
    except (OSError,ValueError) as e:
        report['status']='V158_READONLY_SOURCE_HOLD';report['hold_dlgs']=str(e)[:160]
        report['dlgs']=[]
    try:
        report['tlk']={}
        for name,expected in V157_TLK.items():
            p=_one_casefold(game,name)
            actual,size=_sha_file(p)
            report['tlk'][name]={'sha256':actual,'bytes':size,'v157_sha_equal':actual==expected}
    except (OSError,ValueError) as e:
        report['hold_tlk']=str(e)[:160];report['status']='V158_READONLY_SOURCE_HOLD'
    return report
