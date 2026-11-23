V116_ENTRY='57_V116_DISPATCH_CALLEE_STATIC_READONLY.json'
V116_SCHEMA='BG_EET_RU_V116_DISPATCH_CALLEE_STATIC_READONLY_V1'
V116_EXE_SHA='fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580'
V116_TARGET_RVA=0x204C60
V116_PATTERN=bytes.fromhex('4889742410574883EC20488B02')

def v116_pe_to_raw(b,rva):
  if len(b)<0x200 or b[:2]!=b'MZ':raise ValueError('V116_NOT_PE_MZ')
  nt=struct.unpack_from('<I',b,0x3c)[0]
  if nt<0x40 or nt+24>len(b) or b[nt:nt+4]!=b'PE\x00\x00':
    raise ValueError('V116_INVALID_PE_HEADER')
  n=struct.unpack_from('<H',b,nt+6)[0]
  opt=struct.unpack_from('<H',b,nt+20)[0]
  if not 1<=n<=64 or nt+24+opt+n*40>len(b) or opt<0x70:
    raise ValueError('V116_PE_SECTION_BOUNDS')
  if struct.unpack_from('<H',b,nt+24)[0]!=0x20b:
    raise ValueError('V116_NOT_PE64')
  hits=[]
  for i in range(n):
    s=nt+24+opt+i*40
    vs,va,rawsize,rawbase=struct.unpack_from('<IIII',b,s+8)
    if va<=rva<va+rawsize and rva-va<vs and rawbase+rawsize<=len(b):
      hits.append(rawbase+rva-va)
  if len(hits)!=1:raise ValueError('V116_PE_RVA_NOT_UNIQUE_RAW_SECTION')
  return hits[0]

def v116_report(game):
  report={'schema':V116_SCHEMA,'updater_version':SELF_VERSION,'operation':'READ_ONLY_PE64_SYMBOL_CROSSCHECK',
          'game_files_written':0,'new_hook_installed':False,'runtime_event_join_verified':False,
          'journal_row_id_verified':False,'miss_weapon_identity_verified':False,
          'reference':'Bubb13/EEex InfinityLoader.db [CMessageHandler::AddMessage]',
          'rva':hex(V116_TARGET_RVA),'matched_pattern':False,'status':'V116_DISPATCH_SYMBOL_HOLD'}
  try:
    game=Path(game)
    exe=v111_inside_game(game,game/'Baldur.exe')
    db=v111_inside_game(game,game/'InfinityLoader.db')
    if not exe.is_file() or not db.is_file() or exe.stat().st_size>16000000 or db.stat().st_size>8000000:
      raise ValueError('V116_EXPECTED_SOURCE_MISSING_OR_OVERSIZED')
    raw=exe.read_bytes()
    current_sha=digest(raw)
    report['exe_sha256']=current_sha
    if current_sha!=V116_EXE_SHA:raise ValueError('V116_PINNED_EXE_SHA_MISMATCH')
    db_data=db.read_bytes()
    report['loader_db_sha256']=digest(db_data)
    source=db_data.decode('utf-8-sig','strict')
    section=re.search(r'(?m)^\[CMessageHandler::AddMessage\]\s*\r?\n([^\[]*)',source)
    if not section:raise ValueError('V116_DB_SYMBOL_ABSENT')
    pattern=re.search(r'(?m)^Pattern=([A-Fa-f0-9]+)\s*$',section.group(1))
    adjustment=re.search(r'(?m)^Operations=ADD\s+(-?\d+)\s*$',section.group(1))
    if (not pattern or not adjustment or bytes.fromhex(pattern.group(1))!=V116_PATTERN
        or int(adjustment.group(1))!=-5):
      raise ValueError('V116_DB_SYMBOL_SIGNATURE_CHANGED')
    offset=v116_pe_to_raw(raw,V116_TARGET_RVA)
    report['file_offset']=offset
    if offset+5+len(V116_PATTERN)>len(raw):raise ValueError('V116_DISPATCH_BYTES_OOB')
    report['callee_prefix_sha256']=digest(raw[offset:offset+64])
    if raw[offset+5:offset+5+len(V116_PATTERN)]!=V116_PATTERN:
      raise ValueError('V116_DISPATCH_NOT_MATCHING_DB_SIGNATURE')
    report['matched_pattern']=True
    report['status']='V116_SYMBOL_CMESSAGEHANDLER_ADDMESSAGE_MATCHED_STATIC_ONLY'
  except (OSError,RuntimeError,ValueError,struct.error,UnicodeError) as ex:
    report['hold_reason']=str(ex)[:170]
  return report

def v116_zip(game,path,report):
  game=Path(game);path=Path(path)
  safe_external(game,path)
  if not path.is_file() or path.is_symlink():raise ValueError('V116_CANONICAL_ZIP_MISSING')
  with zipfile.ZipFile(path) as z:
    names=z.namelist()
    if z.testzip() is not None or len(names)!=len(set(names)):
      raise ValueError('V116_ZIP_CRC_OR_DUPLICATE')
    if V116_ENTRY in names and json.loads(z.read(V116_ENTRY))==report:return False
  with tempfile.NamedTemporaryFile(dir=str(path.parent),prefix='.v116_',suffix='.zip',delete=False) as out:
    tmp=Path(out.name)
  try:
    with zipfile.ZipFile(path) as src,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as dst:
      for info in src.infolist():
        if info.filename!=V116_ENTRY:dst.writestr(info,src.read(info))
      dst.writestr(V116_ENTRY,json.dumps(report,ensure_ascii=False,indent=2).encode('utf8'))
    with zipfile.ZipFile(tmp) as z:
      if z.testzip() is not None or z.namelist().count(V116_ENTRY)!=1:
        raise ValueError('V116_WRITTEN_ZIP_INVALID')
    os.replace(tmp,path)
  finally:
    if tmp.exists():tmp.unlink()
  return True

def v116_run(game,path):
  report=v116_report(game)
  try:changed=v116_zip(game,path,report)
  except (OSError,RuntimeError,ValueError,zipfile.BadZipFile) as ex:
    print('V116_SAFE_STOP',type(ex).__name__,str(ex)[:130]);return 2
  print('V116:',report['status'],'| game writes: 0 | ZIP updated:',changed)
  if report.get('hold_reason'):print('V116 HOLD reason:',report['hold_reason'])
  return 0

def v116_selftest():
  with tempfile.TemporaryDirectory(prefix='V116_TEST_') as td:
    root=Path(td);game=root/'game';game.mkdir()
    b=bytearray(0x7000);b[:2]=b'MZ';struct.pack_into('<I',b,0x3c,0x80)
    b[0x80:0x84]=b'PE\x00\x00'
    struct.pack_into('<HH',b,0x80+6,1,0)
    struct.pack_into('<H',b,0x80+20,0xf0)
    struct.pack_into('<H',b,0x80+24,0x20b)
    struct.pack_into('<IIII',b,0x188+8,0x6000,0x200000,0x6000,0x400)
    off=v116_pe_to_raw(b,0x204c60)
    assert off==0x5060
    b[off+5:off+5+len(V116_PATTERN)]=V116_PATTERN
    for pos in (0,0x80+24):
      bad=bytearray(b);bad[pos]=0
      try:v116_pe_to_raw(bad,0x204c60)
      except ValueError:pass
      else:raise AssertionError('V116_BAD_HEADER_ACCEPTED')
    (game/'Baldur.exe').write_bytes(b)
    (game/'InfinityLoader.db').write_text('[CMessageHandler::AddMessage]\nPattern=4889742410574883EC20488B02\nOperations=ADD -5\n')
    report=v116_report(game)
    assert report['status']=='V116_DISPATCH_SYMBOL_HOLD'
    assert report['hold_reason']=='V116_PINNED_EXE_SHA_MISMATCH'
    dest=root/'report.zip'
    with zipfile.ZipFile(dest,'w') as z:z.writestr('old',b'preserved')
    assert v116_zip(game,dest,report) and not v116_zip(game,dest,report)
    with zipfile.ZipFile(dest) as z:
      assert z.testzip() is None and z.read('old')==b'preserved'
      assert z.namelist().count(V116_ENTRY)==1
  return True