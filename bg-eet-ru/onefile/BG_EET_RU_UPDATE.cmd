@echo off & py -3 -x "%~f0" %* & pause & exit /b
# coding: utf-8
"""BG_EET_RU: one-file safe updater + one report folder, strict visible-only.

Hybrid Windows CMD/Python file. CMD first line calls Python -x and is skipped by Python.
Never writes into the installed game. No TLK editing, no installation, no WAV/AI.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import io
import json
import os
import re
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import types
import urllib.error
import urllib.request
import zipfile
import zlib

UPDATER_ID = 'BG_EET_RU_ONEFILE_VISIBLE_ONLY'
SELF_VERSION = 31
DEFAULT_GAME = r'C:\Games\BG_EET_FOXX_NEW'
WORKDIR = Path.home() / 'Documents' / 'BG_EET_RU'
REPORT_NAME = 'SEND_TO_CHATGPT_BG_EET_RU.zip'
REVIEW_SEEDS = json.loads('{"317979":{"excerpt_ru":"[Уверенно и спокойно]Моё имя - [Share-in-kull]Шеринкаль, и я возглавляю силы Легиона Химеры в этом регионе. [Threat","triage":"DIALOGUE_POSSIBLY_VISIBLE_NEEDS_DLG_LINK"},"319734":{"excerpt_ru":"Нет. Порталы в цитадель [zah-HIN-dah]З\'хинда открываются только изнутри. Невольники откроют порталы только если оди","triage":"DIALOGUE_POSSIBLY_VISIBLE_NEEDS_DLG_LINK"},"100436":{"excerpt_ru":"[Faulty]Жезл лабиринтов","triage":"ITEM_SPELL_POSSIBLY_VISIBLE_NEEDS_RESOURCE_LINK"},"100438":{"excerpt_ru":"[Faulty]Проклятие Бездны +4","triage":"ITEM_SPELL_POSSIBLY_VISIBLE_NEEDS_RESOURCE_LINK"},"100440":{"excerpt_ru":"[Faulty]Кольцо защиты от зла","triage":"ITEM_SPELL_POSSIBLY_VISIBLE_NEEDS_RESOURCE_LINK"},"100446":{"excerpt_ru":"[Faulty]Водоворот","triage":"ITEM_SPELL_POSSIBLY_VISIBLE_NEEDS_RESOURCE_LINK"},"101807":{"excerpt_ru":"[else] Молчи, женщина! Прекрати это бесстыдство…","triage":"DIALOGUE_POSSIBLY_VISIBLE_NEEDS_DLG_LINK"},"267454":{"excerpt_ru":"[Movie]Мост Боарескир","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"267455":{"excerpt_ru":"[Movie]Убийство","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"267456":{"excerpt_ru":"[movie]Засада","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"270251":{"excerpt_ru":"[Movie]Чёрные Копи. Вступление.","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"300993":{"excerpt_ru":"[Movie]Вступление","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"300994":{"excerpt_ru":"[Movie]Лавина на Кулдахарском перевале","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"300995":{"excerpt_ru":"[Movie]Прорицание Камня-Сердце","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"300996":{"excerpt_ru":"[Movie]Возвращение в Восточную Гавань","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"300997":{"excerpt_ru":"[Movie]Разрушение кристаллической башни","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"300998":{"excerpt_ru":"[Movie]Эпилог Сердца Зимы","triage":"MOVIE_LABEL_NEEDS_UI_LINK"},"300999":{"excerpt_ru":"[Movie]Пролог Сердца Зимы","triage":"MOVIE_LABEL_NEEDS_UI_LINK"}}')
LEGACY_REPORTS = Path.home() / 'Documents' / 'BG_EET_RU_REPORTS'
URL_BASE = ('https://raw.githubusercontent.com/jeleZa112/'
            'nwn-xanos-updates/bg-eet-ai/bg-eet-ru/onefile/')
RELEASE_URL = URL_BASE + 'release.json'
SRC_URL = URL_BASE + 'BG_EET_RU_UPDATE.cmd'
BUNDLE = {'V28': {'sha256': 'bf5c09b08af8f8d016aa1df2c000f2ddae8d7ef07b0baaa9741f55d50a57cd63', 'payload': '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'}, 'V29': {'sha256': 'f7078c5d132b7225e1b7996fbecc97306a33adedec3d234e9e3932ab7e6fd7f2', 'payload': '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'}, 'TARGETS': {'sha256': '8399d57b2c88e0fd18585dff6d1bdc2703026f867b2a94ffef2b7677deffd329', 'payload': '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'}}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def safe_external(game: Path, path: Path):
    if path.resolve().is_relative_to(game.resolve()):
        raise RuntimeError('STOP: отчёт/обновлятор не должен находиться внутри папки игры')


def module_source(key):
    meta = BUNDLE[key]
    raw = zlib.decompress(base64.b64decode(meta['payload']))
    if digest(raw) != meta['sha256']:
        raise RuntimeError('STOP: встроенный модуль '+key+' не прошёл SHA256')
    return raw.decode('utf-8')


def load_scanners():
    v28 = types.ModuleType('BG_EET_RU_V28_DLG_LINK_FIX_SOURCE_ONLY')
    v28.__file__ = str(Path(__file__).resolve())
    v28.__dict__['__name__'] = v28.__name__
    sys.modules[v28.__name__] = v28
    exec(compile(module_source('V28'),v28.__file__,'exec'),v28.__dict__)
    v29 = types.ModuleType('BG_EET_RU_V29_BLACKPITS_PLACEMENT_READONLY')
    v29.__file__ = str(Path(__file__).resolve())
    sys.modules[v29.__name__] = v29
    exec(compile(module_source('V29'),v29.__file__,'exec'),v29.__dict__)
    targets = json.loads(module_source('TARGETS'))
    if targets.get('automatic_patch_allowed') is not False:
        raise RuntimeError('STOP: visible-only gate is not locked')
    return v28, v29, targets


def read_archive(path: Path):
    """Only read a small fixed set of known archive entries; never extract any ZIP."""
    if not path.is_file(): return {}
    results={}
    try:
        with zipfile.ZipFile(path,'r') as z:
            for name in ('00_STATUS.json','01_V28_DLG_CONTEXT.json','02_V29_BP_PLACEMENT.json',
                         '04_FINGERPRINT.json'):
                try:
                    inf=z.getinfo(name)
                    if inf.file_size > 3_000_000: continue
                    results[name]=json.loads(z.read(name))
                except (KeyError, json.JSONDecodeError, ValueError): pass
    except (OSError,zipfile.BadZipFile):pass
    return results


def legacy_report(name, required_schema, game):
    path = LEGACY_REPORTS/name
    if not path.is_file() or path.stat().st_size>4_000_000:return None
    try:
        obj=json.loads(path.read_text(encoding='utf-8-sig'))
        if (obj.get('schema')!=required_schema or
            str(obj.get('game_root','')).lower()!=str(game).lower() or
            obj.get('game_files_written') is not False):return None
        return obj
    except (OSError,ValueError,UnicodeError):return None


def fingerprints(game: Path, v28):
    # Fingerprints are used solely for non-destructive cache selection.
    # Check complete TLKs, KEY, UI and target DLG/BIF. No file content stored in the ZIP.
    wanted=[('chitin.key',game/'chitin.key')]
    for name in ('dialog.tlk','dialogf.tlk'):
        wanted.append((name,v28.case_file(game,('lang','ru_RU',name))))
    for name in ('41SHERI.DLG','53MALAVO.DLG','BANOME25.DLG','UI.MENU'):
        path=v28.case_file(game,('override',name))
        wanted.append((name,path))
    target_bif = v28.case_file(game,('data','BlackPits.bif'))
    wanted.append(('BlackPits.bif',target_bif))
    result={}
    for name,p in wanted:
        if not p or not p.is_file(): result[name]=None;continue
        st=p.stat()
        result[name]={'size':st.st_size,'sha256':sha_path(p)}
    return result


def can_reuse(report, schema, game, fingerprint, old_fingerprint):
    return (isinstance(report,dict) and report.get('schema')==schema and
            report.get('game_files_written') is False and
            str(report.get('game_root','')).lower()==str(game).lower() and
            fingerprint == old_fingerprint)


def summary(v28report,v29report,used,fp,notes):
    v28_targets=v28report.get('targets', []) if isinstance(v28report,dict) else []
    r29=v29report if isinstance(v29report,dict) else {}
    tlk_match=v28report.get('baseline_matches_2026_11_11') if isinstance(v28report,dict) else None
    return {
        'project':'BG_EET_RU — текстовая русификация EET',
        'schema':'bg-eet-ru-onefile-unified-readonly-v1',
        'created_utc':now(), 'updater_version':SELF_VERSION,
        'game_root':DEFAULT_GAME, 'game_files_written':False,
        'patch_applied':False, 'translation_approved':False,
        'translation_rule':'ONLY TEXT ACTUALLY VISIBLE TO PLAYER. Resource ownership alone is NOT proof.',
        'previously_installed_strrefs_from_2026_11_11_report':491,
        'last_known_baseline_matches':tlk_match,
        'v28_targets_checked':len(v28_targets),
        'v28_visibility_proven':sum(t.get('visibility')=='PROVEN' for t in v28_targets),
        'v29_static_placement_count':r29.get('static_placement_count'),
        'v29_scope':r29.get('scope'),
        'v29_all_other_bifs_scanned':r29.get('all_other_bifs_scanned'),
        'v29_cre_inventories_scanned':r29.get('cre_inventories_scanned'),
        'v29_scripts_scanned':r29.get('scripts_scanned'),
        'sources_used':used,'notes':notes,
        'blocked_text_strrefs':[317979,319734,101807,100436,100438,100440,100446],
        'movie_labels_hold':11,
        'approved_new_text_changes':0,
        'next_safe_goal':'Prove actual on-screen visibility; do not patch on static references alone.',
        'review_queue_included':True
    }


def make_review_queue(v28report):
    """Editorial evidence inventory, not a proposed patch and never an approval gate."""
    verified = v28report.get('targets', []) if isinstance(v28report,dict) else []
    expected = {int(k) for k in REVIEW_SEEDS}
    actual = {int(row['strref']) for row in verified}
    if len(verified) != 18 or expected != actual:
        raise RuntimeError('STOP: expected 18 known targets; ambiguous or missing evidence')
    queue=[]
    for row in verified:
        ref=int(row['strref'])
        seed=REVIEW_SEEDS[str(ref)]
        is_movie = row.get('group')=='UI_MOVIE_VISIBILITY_HOLD'
        if ref==317979:
            reason='Русская реплика с актёрскими и фонетическими ремарками; не удалять русскую ремарку автоматически'
        elif ref==319734:
            reason='Русская реплика с фонетическими ремарками; показ конкретной ветви не подтверждён'
        elif ref==101807:
            reason='[else] в NPC_STATE; триггеры/видимость в игре не подтверждены'
        elif ref in (100436,100438,100440,100446):
            reason='[Faulty] имя ITM из BlackPits.bif; получение/показ игроку не доказаны'
        elif is_movie:
            reason='[Movie] метка ролика, UI.MENU не подтвердил вывод пользователю'
        else:
            raise RuntimeError('STOP: unknown candidate family')
        queue.append({
            'strref':ref,'excerpt':seed['excerpt_ru'],
            'triage_original':seed['triage'],
            'resource':row.get('expected_owner'),
            'resource_link_found':row.get('owner_link_in_current_resource') is True,
            'visibility':row.get('visibility','NOT_PROVEN'),
            'status':'HOLD_REQUIRES_DISPLAY_EVIDENCE',
            'reason':reason,
            'translation_approved':False,
            'user_requested_real_player_visible_only':True
        })
    return {
        'schema':'bg-eet-ru-v31-player-visible-only-review-v1',
        'status':'SOURCE_ONLY_EDITORIAL_HOLD',
        'candidates':queue,
        'new_translation_approvals':0,
        'scope':'From historical v26 queue and verified v28 report; static references cannot prove a real UI display.',
        'next_evidence':'Direct observed on-screen text with game context is required before a change can be proposed.',
        'game_files_written':False
    }


def write_bundle(path, status, v28report, v29report, fp, existing_log=''):
    safe_external(Path(status['game_root']), path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.zip.tmp')
    text=(existing_log.strip()+'\n' if existing_log.strip() else '') + (
        f"{now()} v{SELF_VERSION} READ_ONLY; v28={status['sources_used'].get('v28')}; "
        f"v29={status['sources_used'].get('v29')}; patched=0\n")
    if len(text)>120_000: text=text[-120_000:]
    def b(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('00_STATUS.json',b(status))
            z.writestr('01_V28_DLG_CONTEXT.json',b(v28report))
            z.writestr('02_V29_BP_PLACEMENT.json',b(v29report))
            z.writestr('03_ALL_RUNS.log',text)
            z.writestr('04_FINGERPRINT.json',b(fp))
            z.writestr('06_VISIBLE_ONLY_REVIEW.json',b(make_review_queue(v28report)))
            z.writestr('05_README_RU.txt',
                'BG_EET_RU: ЕДИНЫЙ ОТЧЁТ. Только чтение данных игры.\n'
                'ПЕРЕДАТЬ В ЧАТ ОДИН ФАЙЛ: SEND_TO_CHATGPT_BG_EET_RU.zip\n'
                'Видимость текста игроку не доказана; не устанавливать патчи.\n')
        with zipfile.ZipFile(tmp) as z:
            assert z.testzip() is None and set(z.namelist())=={
                '00_STATUS.json','01_V28_DLG_CONTEXT.json','02_V29_BP_PLACEMENT.json',
                '03_ALL_RUNS.log','04_FINGERPRINT.json','05_README_RU.txt',
                '06_VISIBLE_ONLY_REVIEW.json'}
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()


def get_log(path):
    if not path.is_file():return ''
    try:
        with zipfile.ZipFile(path) as z:
            inf=z.getinfo('03_ALL_RUNS.log')
            return z.read(inf).decode('utf-8') if inf.file_size<150_000 else ''
    except (OSError,KeyError,ValueError,zipfile.BadZipFile):return ''


def published_update(path, offline=False):
    """Optional future updates from an exact HTTPS repo path. No game changes."""
    if offline:return 'обновления через интернет отключены'
    req=urllib.request.Request(RELEASE_URL,headers={'User-Agent':'BG-EET-RU-onefile/30'})
    try:
        with urllib.request.urlopen(req,timeout=8) as resp:
            if resp.url!=RELEASE_URL or resp.status!=200:return 'канал обновлений недоступен'
            raw=resp.read(8193)
        if len(raw)>8192:return 'неверный размер канала обновлений'
        data=json.loads(raw)
        if (data.get('schema')!='bg-eet-ru-onefile-release-v1' or
            data.get('project')!=UPDATER_ID):return 'неверный формат канала'
        version=data.get('version')
        if not isinstance(version,int) or version<=SELF_VERSION:return 'актуальная версия'
        sha=data.get('sha256')
        if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
            return 'некорректный SHA256 релиза'
        req=urllib.request.Request(SRC_URL,headers={'User-Agent':'BG-EET-RU-onefile/30'})
        with urllib.request.urlopen(req,timeout=12) as resp:
            if resp.url!=SRC_URL or resp.status!=200:return 'неверный адрес исходника'
            buf=resp.read(750001)
        if not 1000<len(buf)<=750000 or digest(buf)!=sha:return 'STOP: SHA256 обновления не совпадает'
        first,sep,body=buf.partition(b'\n')
        if not (sep and first.startswith(b'@echo off & py -3 -x ') and
                UPDATER_ID.encode() in body and ('SELF_VERSION = '+str(version)).encode() in body):
            return 'STOP: неверный идентификатор обновления'
        compile(body.decode('utf-8'),str(path),'exec')
        target=WORKDIR/'BG_EET_RU_UPDATE.cmd'
        safe_external(Path(DEFAULT_GAME).resolve(),target)
        tmp=WORKDIR/'_pending_updater.tmp'
        tmp.write_bytes(buf)
        if sha_path(tmp)!=sha:raise ValueError('download SHA mismatch')
        os.replace(tmp,target)
        return 'обновлён до v'+str(version)+'; следующий запуск использует новую версию'
    except urllib.error.HTTPError as ex:
        if ex.code==404:return 'канал новых релизов пока не опубликован; офлайн-версия работает'
        return 'интернет недоступен ('+str(ex.code)+'); офлайн-версия работает'
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,UnicodeError) as exc:
        return 'новая версия не установлена ('+type(exc).__name__+'); офлайн-версия работает'


def main(argv=None):
    p=argparse.ArgumentParser(description='BG_EET_RU one-file visible-only read-only auto-updater')
    p.add_argument('--game',default=DEFAULT_GAME)
    p.add_argument('--offline',action='store_true',help='no GitHub update check')
    p.add_argument('--force',action='store_true',help='ignore result cache, repeat audit')
    p.add_argument('--selftest',action='store_true')
    p.add_argument('--no-open',action='store_true',help='do not open output folder')
    args=p.parse_args(argv)
    if args.selftest: return selftest()
    game=Path(args.game).expanduser().resolve()
    safe_external(game,WORKDIR)
    if not game.is_dir() or not (game/'chitin.key').is_file():
        print('STOP: папка игры неверна или chitin.key не найден:',game)
        return 2
    # User requested one persistent location; copy this file there, never inside EET.
    WORKDIR.mkdir(parents=True,exist_ok=True)
    canonical=WORKDIR/'BG_EET_RU_UPDATE.cmd'
    original=Path(__file__).resolve()
    if original!=canonical:
        try:
            existing_version=0
            if canonical.exists():
                head=canonical.read_bytes()[:2500].decode('utf-8','replace')
                match=re.search(r'^SELF_VERSION = ([0-9]+)$',head,re.M)
                existing_version=int(match.group(1)) if match else 0
            if existing_version>SELF_VERSION:
                import subprocess
                print('Запускаю установленную новую версию v'+str(existing_version))
                return subprocess.call([sys.executable,'-x',str(canonical),*sys.argv[1:]])
            if not canonical.exists() or existing_version<SELF_VERSION:
                temp=canonical.with_suffix('.tmp')
                shutil.copy2(original,temp)
                if sha_path(temp)!=sha_path(original):raise ValueError('staged updater checksum mismatch')
                os.replace(temp,canonical)
        except OSError as e:print('Не удалось сохранить обновлятор в одну папку:',e)
    print('BG_EET_RU v'+str(SELF_VERSION)+' — только чтение игры; один отчёт.')
    print('Папка:',WORKDIR)
    print('Проверяю существующие отчёты (без повторных запусков)...')
    v28,v29,targets=load_scanners()
    report_path=WORKDIR/REPORT_NAME
    old=read_archive(report_path)
    print('Сверка контрольных сумм файлов (только чтение)...')
    fp=fingerprints(game,v28)
    if fp.get('chitin.key') is None or fp.get('dialog.tlk') is None or fp.get('dialogf.tlk') is None:
        raise RuntimeError('STOP: не найдены ключевые файлы игры')
    oldfp=old.get('04_FINGERPRINT.json')
    v28report=old.get('01_V28_DLG_CONTEXT.json')
    v29report=old.get('02_V29_BP_PLACEMENT.json')
    used={};notes=[]
    # v27 was superseded by v28; do not need to rerun v27.
    # v29 was already run on 2026-11-16; import that evidence once where available.
    if not args.force and can_reuse(v28report,'bg-eet-ru-v28-dlg-incoming-corrected-readonly',game,fp,oldfp):
        used['v28']='CACHE'
    else:
        print('Проверка v28 (новый этап, только чтение)...')
        v28report=v28.analyze(game,targets)
        used['v28']='LIVE_READ_ONLY'
    legacy=legacy_report('BG_EET_RU_V29_BP_PLACEMENT.json',
                         'bg-eet-ru-v29-blackpits-static-placement-readonly',game)
    if not args.force and can_reuse(v29report,'bg-eet-ru-v29-blackpits-static-placement-readonly',game,fp,oldfp):
        previous=old.get('00_STATUS.json',{})
        used['v29']='CACHE_HISTORICAL' if previous.get('v29_historical') else 'CACHE'
    elif (not args.force and legacy and
          legacy.get('archives') and legacy['archives'][0].get('status')=='INDEXED_RESOURCES_SCANNED' and
          legacy.get('static_placement_count')==0 and
          fp.get('BlackPits.bif')):
        v29report=legacy
        used['v29']='IMPORTED_HISTORICAL'
        notes.append('v29 from prior report; its BlackPits.bif snapshot has no full BIF SHA; treated as historical only.')
    else:
        print('Проверка v29 (только если нет действующего отчёта)...')
        v29report=v29.analyze(game)
        used['v29']='LIVE_READ_ONLY'
    if v28report.get('approved_for_translation'):
        raise RuntimeError('STOP: parser unexpectedly approved translations')
    if v29report.get('translation_approved') is not False:
        raise RuntimeError('STOP: v29 violated visible-only gate')
    # Files can change while scanning; reject if game fingerprint changed.
    after=fingerprints(game,v28)
    if after!=fp:raise RuntimeError('STOP: игровые ресурсы изменились во время проверки; ZIP не обновлён')
    status=summary(v28report,v29report,used,fp,notes)
    status['v29_historical'] = used['v29'] in ('IMPORTED_HISTORICAL','CACHE_HISTORICAL')
    status['game_root']=str(game)
    write_bundle(report_path,status,v28report,v29report,fp,get_log(report_path))
    print('ГОТОВО. Один файл для ChatGPT:',report_path)
    print('Патчей/изменений в игре: 0')
    try:
        update_status=published_update(canonical,args.offline)
        print('Автообновление:',update_status)
    except Exception as e:print('Автообновление пропущено:',str(e)[:100])
    if os.name=='nt' and not args.no_open:
        try:
            import subprocess
            subprocess.Popen(['explorer.exe','/select,',str(report_path)])
        except Exception:pass
    return 0


def selftest():
    # Self-contained checks only; never read or change a real EET installation.
    v28,v29,targets=load_scanners()
    assert len(targets.get('priority',[]))==7 and len(targets.get('movies',[]))==11
    assert targets['automatic_patch_allowed'] is False
    assert v28.ITM == 0x03ED and v29.STO == 0x03F6
    with tempfile.TemporaryDirectory(prefix='BG_EET_RU_ONEFILE_TEST_') as d:
        base=Path(d); game=base/'game';game.mkdir()
        outside=base/'reports'/'SEND_TO_CHATGPT_BG_EET_RU.zip'
        safe_external(game,outside)
        try:safe_external(game,game/'fake.zip')
        except RuntimeError:pass
        else:raise AssertionError('game write must be rejected')
        stub28={'schema':'bg-eet-ru-v28-dlg-incoming-corrected-readonly',
                'game_root':str(game),'game_files_written':False,
                'targets':[{'strref':int(ref),
                     'group':'UI_MOVIE_VISIBILITY_HOLD' if int(ref) in (267454,267455,267456,270251,300993,300994,300995,300996,300997,300998,300999) else 'DLG_OR_ITEM_REACHABILITY_HOLD',
                     'expected_owner':None,'visibility':'NOT_PROVEN',
                     'owner_link_in_current_resource':False} for ref in REVIEW_SEEDS],
                'approved_for_translation':[],
                'baseline_matches_2026_11_11':True}
        stub29={'schema':'bg-eet-ru-v29-blackpits-static-placement-readonly',
                'game_root':str(game),'game_files_written':False,
                'static_placement_count':0,'scope':'synthetic',
                'translation_approved':False}
        info=summary(stub28,stub29,{'v28':'TEST','v29':'TEST'}, {},[])
        info['game_root']=str(game)
        write_bundle(outside,info,stub28,stub29,{'test':True})
        assert read_archive(outside)['00_STATUS.json']['game_files_written'] is False
        assert len(zipfile.ZipFile(outside).namelist())==7
        with zipfile.ZipFile(outside) as z:
            assert len(json.loads(z.read('06_VISIBLE_ONLY_REVIEW.json'))['candidates'])==18
        assert can_reuse(stub29,stub29['schema'],game,{'x':1},{'x':1})
        assert not can_reuse(stub29,stub29['schema'],game,{'x':2},{'x':1})
        write_bundle(outside,info,stub28,stub29,{'test':True},get_log(outside))
    print('SELFTEST: PASS. Один архив, очередь 18 HOLD, SHA, защита от записи, кэш.')
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,RuntimeError,KeyError,struct.error) as exc:
        print('SAFE_STOP:',type(exc).__name__,str(exc),file=sys.stderr)
        raise SystemExit(2)