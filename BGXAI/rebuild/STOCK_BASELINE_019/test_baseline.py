"""Source/trace invariants from real, previously uploaded EET resources and logs."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'src'))
import stock_parity_audit as stock
import action_replay_gate as replay


def test_sources(stock_zip: Path):
    d=stock.inspect_zip(stock_zip)
    scripts=d['scripts']
    assert scripts['BDDEFAI.BCS']['rules']==322
    assert scripts['BDDEFAI.BCS']['actions']==700
    assert scripts['BDFTHI01.BCS']['rules']==30
    assert scripts['BDFTHI01.BCS']['meaningful_actions']['AttackReevaluate']==2
    assert 'RunAwayFromNoLeaveArea' not in scripts['BDDEFAI.BCS']['meaningful_actions']
    assert 'RunAwayFromNoLeaveArea' not in scripts['BDFTHI01.BCS']['meaningful_actions']
    assert scripts['BDAI0020.BCS']['retreat_state_tokens']
    assert d['safety']['stock_behavior_parity_proven'] is False
    with ZipFile(stock_zip) as z:
        bs=z.read('BDDEFAI.BCS')
    stock.verify_alias(bs,bs,bs)
    try:
        stock.verify_alias(bs,bs,bs[:-4]+b'FAIL')
    except AssertionError: pass
    else: raise AssertionError('Corrupted alias wrongly accepted')
    return d


def test_bad_logs(paths):
    audits=replay.create_report(paths)
    report={item['source']:item['sessions'] for item in audits}
    bad=[(r['source'],i,s['bad_oscillations'])
          for r in audits for i,s in enumerate(r['sessions']) if s['bad_oscillations']]
    assert any('093310' in name for name,_,_ in bad),'Known last failure must be detected'
    assert all(s['manual_vs_AI_origin']=='UNKNOWN' for r in audits for s in r['sessions'])
    return report,bad


def test_tp2_source():
    text=(ROOT/'src'/'setup-BGXUNI-STOCK-EXPERIMENT.tp2.txt').read_text()
    # No action to write source stock BDDEFAI or existing combat scripts.
    assert 'COPY_EXISTING ~BDDEFAI.BCS~ ~override/BGXUN1.BCS~' in text
    assert 'COPY_EXISTING ~BDDEFAI.BCS~ ~scripts/BGXUN1.BS~' in text
    assert 'COMPILE' not in text
    assert 'DO NOT RUN' in text


def main():
    if len(sys.argv)<3: raise SystemExit('Usage: test_baseline.py STOCK.zip COMBAT.log [...COMBAT.log]')
    d=test_sources(Path(sys.argv[1]));report,bad=test_bad_logs(sys.argv[2:]);test_tp2_source()
    result={'status':'OFFLINE PASS - NO IN-GAME VALIDATION',
        'game_modified':False,'live_updater_modified':False,
        'stock_resource_sha256':{k:v['sha256'] for k,v in d['scripts'].items()},
        'game_ai_structure':{k:{'rules':v['rules'],'actions':v['actions'],'known':v['meaningful_actions']}
                             for k,v in d['scripts'].items()},
        'old_bad_oscillations_detected':bad,
        'per_session_actions':report,
        'next_gate':'Isolated WeiDU installation of byte-identical stock-alias; class-slot verification',
        'behavioral_improvement_proven':False}
    dest=ROOT/'tests'/'results.json'
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS: exact stock resource recognition; alias integrity guard; class attack rules; old bad oscillation detection; no player/AI guessing')
    print('Detected known-bad oscillations:',len(bad),'from',len(sys.argv)-2,'real logs')
    print('Wrote',dest)

if __name__=='__main__':main()