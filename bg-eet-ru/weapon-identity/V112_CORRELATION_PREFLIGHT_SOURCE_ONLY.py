# V112: Source/data-only preflight for combat journal identity correlation.
# Bundled into existing BG_EET_RU_UPDATE.cmd; NEVER installs a hook or changes game files.
V112_ENTRY='56_V112_COMBAT_JOURNAL_CORRELATION_PREFLIGHT.json'
V112_SCHEMA='BG_EET_RU_V112_CORRELATION_SOURCE_PREFLIGHT_V1'
V112_FILES={
 'UI':('override/UI.MENU',4000000),
 'EEex_Action':('EEex_scripts/EEex_Action.lua',1500000),
 'EEex_Action_Patch':('EEex_scripts/EEex_Action_Patch.lua',1500000),
}
V112_SIGNALS={
 'UI':('combatLog[rowNumber]','BG_EET_RU_LogView','BG_EET_RU_LOG_MODE','WORLD_MESSAGES'),
 'EEex_Action':('EEex_Action_AddSpriteStartedActionListener','EEex_Action_Private_SpriteStartedActionListeners'),
 'EEex_Action_Patch':('EEex_Action',),
}

def v112_probe_source(game,label):
  relative,cap=V112_FILES[label]
  game=Path(game)
  candidate=v111_inside_game(game,game.joinpath(*relative.split('/')))
  if not candidate.is_file():return {'status':'NOT_PRESENT','path':relative}
  size=candidate.stat().st_size
  if size>cap:return {'status':'SIZE_HOLD','path':relative,'bytes':size}
  raw=candidate.read_bytes()
  if len(raw)!=size:return {'status':'CHANGED_DURING_READ_HOLD','path':relative}
  try:src=raw.decode('utf-8-sig','strict')
  except UnicodeError:return {'status':'NON_UTF8_HOLD','path':relative,'sha256':digest(raw)}
  signals={s:src.count(s) for s in V112_SIGNALS[label]}
  return {'status':'STATIC_SOURCE_FINGERPRINTED','path':relative,'bytes':len(raw),
          'sha256':digest(raw),'signals':signals}

def v112_read_zip_history(game,path):
  safe_external(game,path)
  path=Path(path)
  if path.is_symlink() or not path.is_file():
    return {'status':'CANONICAL_ZIP_MISSING_HOLD'}
  if path.stat().st_size>20000000:
    return {'status':'ZIP_TOO_LARGE_HOLD'}
  with zipfile.ZipFile(path) as z:
    names=z.namelist()
    if len(names)!=len(set(names)) or z.testzip() is not None:
      raise ValueError('V112_ZIP_BAD_CRC_OR_DUPLICATES')
    prior={}
    for key,entry in (('v108',V108_ENTRY),('v111',V111_ENTRY)):
      if entry not in names:prior[key]={'status':'REPORT_MISSING'};continue
      if z.getinfo(entry).file_size>600000:raise ValueError('V112_PRIOR_REPORT_OVERSIZE')
      value=json.loads(z.read(entry))
      if not isinstance(value,dict):raise ValueError('V112_PRIOR_REPORT_NOT_OBJECT')
      if key=='v108':
        c=value.get('console_evidence') or {}
        samples=c.get('samples') or []
        if not isinstance(samples,list) or len(samples)>32:
          raise ValueError('V112_V108_SAMPLES_UNEXPECTED')
        events=[e for e in samples if isinstance(e,str) and e.startswith(V108_PREFIX+' EVENT')]
        # Structural facts only. No raw console lines or private user paths in report.
        fields={v:sum(1 for e in events if v in e)
                for v in ('weapon_resref=','launcher_resref=','attacker_id=',
                          'target_id=','attack_sequence=','journal_row_id=',
                          'hit_miss=UNVERIFIED','journal_row=UNVERIFIED')}
        prior[key]={'status':value.get('status'),
                    'callback_events':len(events),'field_counts':fields,
                    'provenance':'CONSOLE_EVENT_SNAPSHOT_NOT_JOURNAL_ROW'}
      else:
        items=value.get('items',{})
        if not isinstance(items,dict):raise ValueError('V112_ITEMS_MALFORMED')
        verified=[k for k in V111_TARGETS if isinstance(items.get(k),dict)
                  and items[k].get('status')=='V111_ITM_SOURCE_RESOLVED']
        prior[key]={'status':value.get('status'),
                    'targeted_item_resources_resolved':verified,
                    'resolved_identified_names':value.get('resolved_identified_names'),
                    'name_identification_state_proven_by_live_ui':False}
  return {'status':'V112_CANONICAL_HISTORY_READ_ONLY','prior':prior}

def v112_build_report(game,path):
  report={'schema':V112_SCHEMA,'updater_version':SELF_VERSION,
          'status':'V112_CORRELATION_EVIDENCE_HOLD',
          'operation':'READ_ONLY_STATIC_UI_ACTION_AND_PRIOR_V108_V111_AUDIT',
          'game_files_written':0,'gameplay_modified':False,
          'new_hook_installed':False,'v108_module_changed':False,
          'combat_log_row_to_weapon_join_verified':False,
          'miss_weapon_identity_verified':False,
          'source_and_runtime_evidence_are_distinct':True,
          'sources':{},'history':{},'errors':[],
          'policy':'NO_ACTOR_OR_ROW_ID_NO_WEAPON_LABEL_ON_MISS'}
  for label in V112_FILES:
    try:report['sources'][label]=v112_probe_source(game,label)
    except (OSError,ValueError,RuntimeError) as e:
      report['sources'][label]={'status':'SOURCE_HOLD','error':str(e)[:160]}
  try:report['history']=v112_read_zip_history(game,path)
  except (OSError,ValueError,RuntimeError,zipfile.BadZipFile,KeyError) as e:
    report['errors'].append({'area':'history','error':str(e)[:160]})
    report['history']={'status':'PRIOR_REPORT_UNREADABLE_HOLD'}
  p=report['history'].get('prior',{})
  ev=p.get('v108',{});item=p.get('v111',{})
  fs=ev.get('field_counts',{})
  source_ui=report['sources']['UI']
  source_action=report['sources']['EEex_Action']
  valid_ui=(source_ui.get('status')=='STATIC_SOURCE_FINGERPRINTED'
            and source_ui.get('signals',{}).get('combatLog[rowNumber]',0)==1
            and source_ui.get('signals',{}).get('BG_EET_RU_LogView',0)>=1)
  action_api=(source_action.get('status')=='STATIC_SOURCE_FINGERPRINTED'
              and source_action.get('signals',{}).get('EEex_Action_AddSpriteStartedActionListener',0)>=1)
  damage_item_chain=(ev.get('callback_events',0)>0
                     and fs.get('weapon_resref=',0)>0
                     and item.get('resolved_identified_names')==3)
  report['gates']={
      'ui_combatlog_text_binding_source_only':valid_ui,
      'action_started_api_source_only':action_api,
      'damage_callback_and_three_active_item_names':damage_item_chain,
      'v108_has_attacker_id':fs.get('attacker_id=',0)>0,
      'v108_has_target_id':fs.get('target_id=',0)>0,
      'v108_has_attack_sequence':fs.get('attack_sequence=',0)>0,
      'v108_has_combatlog_row_id':fs.get('journal_row_id=',0)>0,
      'action_started_equals_each_attack_roll':False,
      'display_row_hook_present_in_this_probe':False,
  }
  if damage_item_chain and valid_ui:
    report['status']='V112_ITEM_NAMES_AND_UI_SOURCE_CONFIRMED_JOIN_HOLD'
  report['recommendation']='KEEP_ORIGINAL_FULL_BRIEF_TEXT; DO_NOT_ATTRIBUTE_WEAPON_ON_MISS_OR_DAMAGE_ROW_UNTIL_STABLE_PER_ATTACK_AND_ROW_KEY'
  return report

def v112_zip_write(game,path,report):
  safe_external(game,path)
  path=Path(path)
  if path.is_symlink() or not path.is_file():raise ValueError('V112_CANONICAL_ZIP_UNSAFE')
  with zipfile.ZipFile(path) as z:
    names=z.namelist()
    if len(names)!=len(set(names)) or z.testzip() is not None:
      raise ValueError('V112_PRIOR_ZIP_INVALID')
    if V112_ENTRY in names and json.loads(z.read(V112_ENTRY))==report:
      return False
  with tempfile.NamedTemporaryFile(dir=str(path.parent),prefix='.v112_',suffix='.zip',delete=False) as out:
    tmp=Path(out.name)
  try:
    with zipfile.ZipFile(path) as src,zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as dst:
      for info in src.infolist():
        if info.filename!=V112_ENTRY:dst.writestr(info,src.read(info))
      dst.writestr(V112_ENTRY,json.dumps(report,ensure_ascii=False,indent=2).encode('utf8'))
    with zipfile.ZipFile(tmp) as z:
      if z.testzip() is not None or z.namelist().count(V112_ENTRY)!=1:
        raise ValueError('V112_ZIP_VERIFY_FAIL')
    os.replace(tmp,path)
  finally:
    if tmp.exists():tmp.unlink()
  return True

def v112_run(game,path):
  report=v112_build_report(game,path)
  try:changed=v112_zip_write(game,path,report)
  except (OSError,RuntimeError,ValueError,zipfile.BadZipFile) as exc:
    print('V112_ZIP_SAFE_STOP:',type(exc).__name__,str(exc)[:160])
    return 2
  print('V112:',report['status'],'| game writes: 0 | ZIP updated:',changed)
  return 0

def v112_selftest():
  with tempfile.TemporaryDirectory(prefix='BG_EET_RU_V112_TEST_') as root:
    base=Path(root);game=base/'game';game.mkdir()
    ui=game/'override';ui.mkdir()
    act=game/'EEex_scripts';act.mkdir()
    (ui/'UI.MENU').write_text('WORLD_MESSAGES combatLog[rowNumber] BG_EET_RU_LogView',encoding='utf8')
    (act/'EEex_Action.lua').write_text('function EEex_Action_AddSpriteStartedActionListener(listener) end',encoding='utf8')
    prior=base/'report.zip'
    v108={'status':'V108_INSTALLED_AWAITING_NATIVE_RESREF_CAPTURE',
          'console_evidence':{'samples':[
             V108_PREFIX+' EVENT\t1\tweapon_resref=AROW01\tlauncher_resref=BOW05\thit_miss=UNVERIFIED\tjournal_row=UNVERIFIED']}}
    v111={'resolved_identified_names':3,'items':{
          k:{'status':'V111_ITM_SOURCE_RESOLVED'} for k in V111_TARGETS}}
    with zipfile.ZipFile(prior,'w') as z:
      z.writestr('keep.txt',b'preserved')
      z.writestr(V108_ENTRY,json.dumps(v108))
      z.writestr(V111_ENTRY,json.dumps(v111))
    before_game={str(f.relative_to(game)):digest(f.read_bytes())
                 for f in game.rglob('*') if f.is_file()}
    r=v112_build_report(game,prior)
    assert r['status']=='V112_ITEM_NAMES_AND_UI_SOURCE_CONFIRMED_JOIN_HOLD',r
    assert r['gates']['action_started_api_source_only'] is True
    assert r['gates']['v108_has_attacker_id'] is False
    assert r['gates']['v108_has_combatlog_row_id'] is False
    assert r['combat_log_row_to_weapon_join_verified'] is False
    assert v112_zip_write(game,prior,r)
    previous=digest(prior.read_bytes())
    assert not v112_zip_write(game,prior,r)
    assert digest(prior.read_bytes())==previous
    with zipfile.ZipFile(prior) as z:
      assert z.testzip() is None and z.read('keep.txt')==b'preserved'
      assert z.namelist().count(V112_ENTRY)==1
    assert before_game=={str(f.relative_to(game)):digest(f.read_bytes())
                         for f in game.rglob('*') if f.is_file()}
    (ui/'UI.MENU').write_text('combatLog[rowNumber] broken UI',encoding='utf8')
    missing=v112_build_report(game,prior)
    assert missing['status']=='V112_CORRELATION_EVIDENCE_HOLD'
    assert missing['gates']['ui_combatlog_text_binding_source_only'] is False
    (ui/'UI.MENU').write_text('WORLD_MESSAGES combatLog[rowNumber] BG_EET_RU_LogView',encoding='utf8')
    (act/'EEex_Action.lua').write_text('missing listener',encoding='utf8')
    unavailable=v112_build_report(game,prior)
    assert unavailable['gates']['action_started_api_source_only'] is False
    assert unavailable['combat_log_row_to_weapon_join_verified'] is False
  return True