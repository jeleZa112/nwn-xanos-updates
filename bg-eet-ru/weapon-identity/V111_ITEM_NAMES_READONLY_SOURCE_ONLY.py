# V111: installed-game ITM/TLK exact names (READ ONLY, no EEex or game edits).
# IESDP: KEY V1 (14-byte resource index), BIFF V1 (16-byte file index),
# ITM V1 header (strrefs 0x08/0x0C, type 0x1C), TLK V1 (26-byte entries).
V111_ENTRY='55_V111_ACTUAL_ITM_TLK_NAMES_READONLY.json'
V111_TARGETS=('SW1H04','AROW01','BOW05')
V111_ITEM_TYPES={0x05:'ARROWS',0x0F:'BOWS',0x13:'SMALL_SWORDS',0x14:'LARGE_SWORDS',
                 0x1F:'BOLTS',0x0E:'BULLETS',0x12:'SLINGS',0x1B:'CROSSBOWS'}

def v111_inside_game(game, path):
  root=Path(game).resolve()
  path=Path(path)
  if not path.resolve().is_relative_to(root):
    raise ValueError('V111_OUTSIDE_GAME_PATH')
  parent=path
  while parent!=root:
    if parent.is_symlink():raise ValueError('V111_SYMLINK_RESOURCE_HOLD')
    parent=parent.parent
  return path

def v111_key_index(game):
  key=v111_inside_game(game,Path(game)/'chitin.key')
  if not key.is_file() or key.stat().st_size>64000000:
    raise ValueError('V111_KEY_ABSENT_OR_LARGE')
  raw=key.read_bytes()
  if len(raw)<24 or raw[:8]!=b'KEY V1  ':
    raise ValueError('V111_UNSUPPORTED_KEY_VERSION')
  nb,nr,bo,ro=struct.unpack_from('<IIII',raw,8)
  if nb>50000 or nr>3000000 or bo<24 or ro<24 or nb*12>len(raw)-bo or nr*14>len(raw)-ro:
    raise ValueError('V111_BAD_KEY_BOUNDS')
  rows={}
  wanted={v.encode('ascii') for v in V111_TARGETS}
  for i in range(nr):
    p=ro+14*i
    name=raw[p:p+8].split(b'\0',1)[0].upper()
    if name not in wanted:continue
    typ,loc=struct.unpack_from('<HI',raw,p+8)
    if typ==0x03ED:
      rows.setdefault(name.decode('ascii'),[]).append(loc)
  bif_names=[]
  for i in range(nb):
    _,off,nlen,_=struct.unpack_from('<IIHH',raw,bo+12*i)
    if not 1<=nlen<=260 or off>len(raw) or nlen>len(raw)-off:
      raise ValueError('V111_KEY_BIF_FILENAME_BOUNDS')
    name=raw[off:off+nlen].split(b'\0',1)[0].decode('cp1252')
    bif_names.append(name)
  return rows,bif_names,digest(raw)

def v111_load_itm(game,resref,index,bif_names):
  game=Path(game)
  o=v111_inside_game(game,game/'override'/(resref+'.ITM'))
  if o.exists() or o.is_symlink():
    if not o.is_file() or o.stat().st_size>8000000:
      raise ValueError('V111_INVALID_OVERRIDE_ITM')
    data=o.read_bytes()
    return data,{'source':'OVERRIDE','bytes':len(data),'sha256':digest(data)}
  locs=index.get(resref,[])
  if len(locs)!=1:
    raise ValueError('V111_KEY_ITEM_LOCATOR_COUNT_'+str(len(locs)))
  loc=locs[0]
  bi=loc>>20
  fi=loc&0x3fff
  if bi>=len(bif_names) or loc&0xfc000:
    # bits 14..19 are tileset index, invalid for ITM file resources
    raise ValueError('V111_KEY_ITM_LOCATOR_BOUNDS')
  raw_name=bif_names[bi].replace('\\','/')
  parts=raw_name.split('/')
  if any(not x or x in ('.','..') or ':' in x for x in parts):
    raise ValueError('V111_UNSAFE_BIF_FILENAME')
  bf=v111_inside_game(game,game.joinpath(*parts))
  if not bf.is_file():raise ValueError('V111_BIF_NOT_FOUND')
  with bf.open('rb') as f:
    head=f.read(20)
    if len(head)!=20 or head[:8]!=b'BIFFV1  ':
      raise ValueError('V111_UNSUPPORTED_BIF_COMPRESSION_HOLD')
    nf,nt,table=struct.unpack_from('<III',head,8)
    f.seek(0,2)
    size=f.tell()
    if nf>500000 or table<20 or table>size or nf*16>size-table:
      raise ValueError('V111_BIF_RESOURCE_INDEX_BOUNDS')
    f.seek(table)
    matches=[]
    for _ in range(nf):
      row=f.read(16)
      if len(row)!=16:raise ValueError('V111_SHORT_BIF_ENTRY')
      rid,start,length,typ,_=struct.unpack('<IIIHH',row)
      if (rid&0x3fff)==fi and typ==0x03ED:
        matches.append((start,length))
    if len(matches)!=1:raise ValueError('V111_BIF_ITM_COUNT_'+str(len(matches)))
    off,length=matches[0]
    if not 114<=length<=8000000 or off>size or length>size-off:
      raise ValueError('V111_BIF_ITM_DATA_BOUNDS')
    f.seek(off)
    data=f.read(length)
    if len(data)!=length:raise ValueError('V111_BIF_SHORT_READ')
  return data,{'source':'KEY_BIF','bif_relative':'/'.join(parts),
               'bytes':len(data),'sha256':digest(data)}

def v111_parse_itm(data):
  if len(data)<114 or data[:8]!=b'ITM V1  ':
    raise ValueError('V111_NOT_SUPPORTED_ITM_V1')
  no,yes=struct.unpack_from('<II',data,8)
  typ=struct.unpack_from('<H',data,0x1c)[0]
  return {'unidentified_name_strref':no,'identified_name_strref':yes,
          'item_type_id':typ,'item_type_category':V111_ITEM_TYPES.get(typ,'OTHER_OR_MODDED')}

def v111_tlk_names(game,refs,tlk_name):
  path=v111_inside_game(game,Path(game)/'lang'/'ru_RU'/tlk_name)
  if not path.is_file():return {'status':'V111_RU_TLK_MISSING_HOLD'}
  with path.open('rb') as f:
    size=path.stat().st_size
    head=f.read(18)
    if len(head)!=18 or head[:8]!=b'TLK V1  ':
      return {'status':'V111_RU_TLK_HEADER_HOLD'}
    lang,count,base=struct.unpack_from('<HII',head,8)
    if count>10000000 or base<18+count*26 or base>size:
      return {'status':'V111_RU_TLK_TABLE_BOUNDS_HOLD'}
    results={}
    for ref in sorted(set(refs)):
      if ref==0xffffffff:
        results[str(ref)]={'status':'NO_NAME_REFERENCE'}
        continue
      if ref&0xff000000:
        results[str(ref)]={'status':'NON_DEFAULT_TLK_FILE_ID_HOLD'}
        continue
      if ref>=count:
        results[str(ref)]={'status':'TLK_STRREF_OUT_OF_RANGE'}
        continue
      f.seek(18+26*ref)
      entry=f.read(26)
      if len(entry)!=26:raise ValueError('V111_TLK_TRUNCATED_ENTRY')
      flags=struct.unpack_from('<H',entry,0)[0]
      off,n=struct.unpack_from('<II',entry,18)
      if n>4096 or off>size-base or n>size-base-off:
        results[str(ref)]={'status':'TLK_TEXT_BOUNDS_HOLD'}
        continue
      if not (flags&1) or n==0:
        results[str(ref)]={'status':'TLK_NO_TEXT','flags':flags}
        continue
      f.seek(base+off)
      data=f.read(n)
      if len(data)!=n:raise ValueError('V111_SHORT_TLK_TEXT')
      try:text=data.decode('utf8','strict')
      except UnicodeDecodeError:
        results[str(ref)]={'status':'NON_UTF8_TLK_TEXT_HOLD',
                           'raw_sha256':digest(data)}
        continue
      results[str(ref)]={'status':'TEXT_READ','text':text,'flags':flags,
                         'text_sha256':digest(data)}
  return {'status':'V111_TLK_READ_ONLY','language_directory':'ru_RU',
          'tlk_language_id':lang,'tlk_sha256':sha_path(path),'entries':results}

def v111_build_report(game):
  game=Path(game)
  result={'schema':'BG_EET_RU_V111_ACTUAL_ITEM_NAMES_READONLY_V1',
          'updater_version':SELF_VERSION,'operation':'READ_ONLY_ITM_TLK_RESOURCE_LOOKUP',
          'status':'V111_LOCAL_NAMES_PENDING','game_files_written':0,
          'no_new_game_hook':True,'gameplay_modified':False,
          'exact_journal_row_proven':False,'miss_event_listener_proven':False,
          'source_live_v108_pairs':{'melee':'SW1H04','ranged_weapon':'AROW01',
                                    'ranged_launcher':'BOW05'},
          'items':{},'tlks':{},'errors':[],
          'name_visibility':'TLK_TEXT_NOT_SAME_AS_ONSCREEN_IDENTIFICATION_STATE'}
  try:index,bifs,keyhash=v111_key_index(game)
  except (OSError,RuntimeError,ValueError,struct.error) as ex:
    index,bifs={},[]
    result['errors'].append({'scope':'KEY','error':str(ex)[:150]})
    keyhash=None
  result['key_sha256']=keyhash
  refs=[]
  for resref in V111_TARGETS:
    try:
      raw,source=v111_load_itm(game,resref,index,bifs)
      itm=v111_parse_itm(raw)
      result['items'][resref]={'status':'V111_ITM_SOURCE_RESOLVED',
                              **source,**itm}
      refs.extend((itm['unidentified_name_strref'],itm['identified_name_strref']))
    except (OSError,RuntimeError,ValueError,struct.error) as ex:
      result['items'][resref]={'status':'V111_ITEM_HOLD','reason':str(ex)[:180]}
  for name in ('dialog.tlk','dialogf.tlk'):
    try:result['tlks'][name]=v111_tlk_names(game,refs,name)
    except (OSError,ValueError,RuntimeError,struct.error) as ex:
      result['tlks'][name]={'status':'V111_TLK_READ_ERROR_HOLD','reason':str(ex)[:180]}
  primary=result['tlks']['dialog.tlk']
  found=0
  for row in result['items'].values():
    for key in ('unidentified_name_strref','identified_name_strref'):
      ref=row.get(key)
      textrow=primary.get('entries',{}).get(str(ref),{})
      row[key.replace('_strref','_ru_tlk_text')]=textrow.get('text') if textrow.get('status')=='TEXT_READ' else None
    if row.get('identified_name_ru_tlk_text'):found+=1
  result['resolved_identified_names']=found
  result['status']=('V111_THREE_LOCAL_ITEM_NAMES_EXTRACTED_READONLY' if found==3 else
                   'V111_PARTIAL_NAMES_OR_RESOURCE_HOLD_READONLY')
  return result

def v111_save_zip(game,path,report):
  path=Path(path)
  safe_external(game,path)
  if path.is_symlink() or not path.is_file():
    raise ValueError('V111_CANONICAL_ZIP_MISSING')
  with zipfile.ZipFile(path) as z:
    names=z.namelist()
    if z.testzip() is not None or len(names)!=len(set(names)):
      raise ValueError('V111_ZIP_BAD_OR_DUPLICATE')
    if V111_ENTRY in names and json.loads(z.read(V111_ENTRY))==report:return False
  with tempfile.NamedTemporaryFile(dir=str(path.parent),prefix='.v111_',suffix='.zip',delete=False) as o:
    tmp=Path(o.name)
  try:
    with zipfile.ZipFile(path) as src,zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as dst:
      for info in src.infolist():
        if info.filename!=V111_ENTRY:dst.writestr(info,src.read(info))
      dst.writestr(V111_ENTRY,json.dumps(report,ensure_ascii=False,indent=2).encode('utf8'))
    with zipfile.ZipFile(tmp) as z:
      if z.testzip() is not None or z.namelist().count(V111_ENTRY)!=1:
        raise ValueError('V111_ZIP_RECHECK_FAILED')
    os.replace(tmp,path)
  finally:
    if tmp.exists():tmp.unlink()
  return True

def v111_run(game,path):
  report=v111_build_report(game)
  try:changed=v111_save_zip(game,path,report)
  except (OSError,RuntimeError,ValueError,zipfile.BadZipFile) as ex:
    print('V111_ZIP_SAFE_STOP:',type(ex).__name__,str(ex)[:180])
    return 2
  print('V111:',report['status'],'| names:',report['resolved_identified_names'],
        '| game writes: 0 | ZIP updated:',changed)
  return 0

def v111_selftest():
  def itm(unidentified,identified,itemtype):
    raw=bytearray(114)
    raw[:8]=b'ITM V1  '
    struct.pack_into('<II',raw,8,unidentified,identified)
    struct.pack_into('<H',raw,0x1c,itemtype)
    return bytes(raw)
  def tlk(names):
    n=20;offset=18+26*n
    entries=bytearray(26*n)
    body=b''
    for ref,val in names.items():
      data=val.encode('utf8')
      struct.pack_into('<H',entries,ref*26,1)
      struct.pack_into('<II',entries,ref*26+18,len(body),len(data))
      body+=data
    return b'TLK V1  '+struct.pack('<HII',7,n,offset)+entries+body
  with tempfile.TemporaryDirectory(prefix='BG_EET_RU_V111_TEST_') as root:
    base=Path(root);game=base/'game';game.mkdir()
    (game/'override').mkdir();(game/'data').mkdir()
    (game/'lang'/'ru_RU').mkdir(parents=True)
    namebytes=tlk({8:'Меч',9:'Длинный меч',10:'Стрела',11:'Обычная стрела',
                   12:'Лук',13:'Короткий лук'})
    (game/'lang'/'ru_RU'/'dialog.tlk').write_bytes(namebytes)
    (game/'override'/'SW1H04.ITM').write_bytes(itm(8,9,0x14))
    arrow=itm(10,11,5);bow=itm(12,13,0xf)
    biff=b'BIFFV1  '+struct.pack('<III',2,0,20)
    biff+=struct.pack('<IIIHH',1,52,len(arrow),0x3ed,0)
    biff+=struct.pack('<IIIHH',2,52+len(arrow),len(bow),0x3ed,0)
    biff+=arrow+bow
    (game/'data'/'TEST.BIF').write_bytes(biff)
    bname=b'data\\TEST.BIF\0'
    key=b'KEY V1  '+struct.pack('<IIII',1,2,24,36)
    key+=struct.pack('<IIHH',len(biff),64,len(bname),0)
    key+=b'AROW01\0\0'+struct.pack('<HI',0x3ed,1)
    key+=b'BOW05\0\0\0'+struct.pack('<HI',0x3ed,2)
    key+=bname
    (game/'chitin.key').write_bytes(key)
    report=v111_build_report(game)
    assert report['status']=='V111_THREE_LOCAL_ITEM_NAMES_EXTRACTED_READONLY',report
    assert report['items']['SW1H04']['source']=='OVERRIDE'
    assert report['items']['AROW01']['source']=='KEY_BIF'
    assert report['items']['BOW05']['identified_name_ru_tlk_text']=='Короткий лук'
    assert report['items']['AROW01']['item_type_category']=='ARROWS'
    (game/'override'/'AROW01.ITM').write_bytes(b'BAD')
    bad=v111_build_report(game)
    assert bad['items']['AROW01']['status']=='V111_ITEM_HOLD'
    assert bad['resolved_identified_names']==2
    (game/'override'/'AROW01.ITM').unlink()
    (game/'lang'/'ru_RU'/'dialog.tlk').write_bytes(b'BAD')
    no_tlk=v111_build_report(game)
    assert no_tlk['resolved_identified_names']==0
    assert no_tlk['status']=='V111_PARTIAL_NAMES_OR_RESOURCE_HOLD_READONLY'
    path=base/'reports.zip'
    with zipfile.ZipFile(path,'w') as z:z.writestr('54_V108_PRESERVED.json','{"ok":true}')
    assert v111_save_zip(game,path,report)
    before=digest(path.read_bytes())
    assert not v111_save_zip(game,path,report)
    assert digest(path.read_bytes())==before
    with zipfile.ZipFile(path) as z:
      assert z.testzip() is None
      assert z.read('54_V108_PRESERVED.json')==b'{"ok":true}'
      assert z.namelist().count(V111_ENTRY)==1
  return True
