"""Reproducibly derive a PASSIVE 065 observer candidate from exact installed 064 Lua.

This only writes files into the local development folder. NEVER touches EET, WeiDU,
or the existing GitHub pinned updater. The new policy does not issue combat orders.
"""
from pathlib import Path
from hashlib import sha256
HERE=Path(__file__).resolve().parent
BASE=HERE/'M_BX43_064_BASELINE_READONLY.lua'
POLICY=HERE/'BGXAI65_PRIORITY_POLICY.lua'
CANDIDATE=HERE/'M_BX43_065_OBSERVER_CANDIDATE.lua'
PIN064='bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b'
ANCHOR='''            if #P.guardSignals > P.maxGuardSignals then
                table.remove(P.guardSignals, 1)
            end'''
INSERT='''            -- 065 advisory: observe the confirmed hit for multi-threat priority.
            -- No engine orders or BGX52_* LOCALS are issued by this observer.
            if type(BGX65Policy)=="table" and type(BGX65Policy.observeHit)=="function" then
                local ok65 = pcall(BGX65Policy.observeHit, confirmedEvent,
                    safe(function()return EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime end))
                if not ok65 then BGX65Policy.errors=(BGX65Policy.errors or 0)+1 end
            end
            if #P.guardSignals > P.maxGuardSignals then
                table.remove(P.guardSignals, 1)
            end'''

def build()->bytes:
    base=BASE.read_bytes()
    assert sha256(base).hexdigest()==PIN064, 'B64_BASELINE_SHA_DRIFT'
    txt=base.decode('utf-8')
    assert txt.count(ANCHOR)==1, 'SINGLE_HOOK_ANCHOR_MISSING'
    # Keep entire original 064 Lua byte-identical except the one advisory hook.
    modified=txt.replace(ANCHOR,INSERT)
    assert modified.replace(INSERT,ANCHOR)==txt
    policy=POLICY.read_text(encoding='utf-8')
    assert 'return P\n' in policy[-16:], 'BAD_POLICY_FILE'
    assert 'Attack(' not in policy and 'MoveToObject(' not in policy and 'setLocalInt(' not in policy
    result=(modified+'\n-- 065 safe priority observation, source-only.\ndo\n'+policy+'\nend\n').encode('utf-8')
    return result

if __name__=='__main__':
    data=build()
    CANDIDATE.write_bytes(data)
    print('SOURCE_ONLY_065_BUILT',len(data),sha256(data).hexdigest(),'GAME_UNCHANGED')
