"""Offline regression for permanent BGXAI_UPDATE.cmd -> remote BGXAI_SYNC.ps1 -> BGXUNI.
Does not claim Windows/WeiDU runtime. Test against real saved EET BAF/IDS fixtures.
"""
import hashlib,json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SEL=(ROOT/'parallel/SYNC_SELECTOR_016_FRAGMENT.txt').read_text()
INST=(ROOT/'parallel/BGXUNI_AUTOINSTALL.ps1').read_text()
MAN=json.loads((ROOT/'parallel/latest.json').read_text())
BAF=(ROOT/'BGXUNI/BGXUN1.BAF').read_bytes()
TP2=(ROOT/'BGXUNI/setup-BGXUNI.tp2').read_bytes()

def sha(b):return hashlib.sha256(b).hexdigest()

def balance_ps(src):
    """Lexical bracket scan outside # comments and quoted literal text.
    Not a full PowerShell parser: runtime must be independently confirmed.
    """
    stack=[]; state='text'; i=0; n=len(src)
    match={'(':')','{':'}','[':']'}
    while i<n:
        c=src[i]
        if state=='comment':
            if c=='\n':state='text'
        elif state=='single':
            if c=="'":
                if i+1<n and src[i+1]=="'":i+=1
                else:state='text'
        elif state=='double':
            if c=='`':i+=1
            elif c=='"':state='text'
        else:
            if c=='#':state='comment'
            elif c=="'":state='single'
            elif c=='"':state='double'
            elif c in match:stack.append((c,i))
            elif c in match.values():
                assert stack, 'unexpected closing %s at %s'%(c,i)
                op,p=stack.pop();assert match[op]==c,'mismatched %s at %s with %s at %s'%(op,p,c,i)
        i+=1
    assert state in ('text','comment'),'unterminated quote'
    assert not stack,'remaining brackets: '+repr(stack[-5:])

class SingleFileUpdaterTests(unittest.TestCase):
    def test_manifest(self):
        self.assertEqual(MAN['channel'],'BGXUNI-parallel')
        self.assertEqual(MAN['version'],'0.1.6-no-idle-range-first')
        self.assertEqual(MAN['deployment'],'single-existing-BGXAI_UPDATE.cmd')
        self.assertEqual(len(MAN['files']),2)
        for row,content in zip(MAN['files'],[BAF,TP2]):
            self.assertEqual(row['size'],len(content))
            self.assertEqual(row['sha256'],sha(content))
        by=INST.encode('utf-8');self.assertEqual(MAN['installer']['size'],len(by));self.assertEqual(MAN['installer']['sha256'],sha(by))
    def test_ps_lexical_balance(self):
        balance_ps(INST);balance_ps(SEL)
    def test_known_remote_paths_only(self):
        self.assertIn('Disallowed remote source',INST)
        self.assertIn("$downloaded.ContainsKey($key)",INST)
        self.assertIn('Source hash/size mismatch',INST)
        self.assertIn('Invalid pinned GitHub commit',INST)
    def test_one_existing_cmd_not_new_launcher(self):
        self.assertIn('BGXAI_ONE_FILE_SELECTOR_016',SEL)
        self.assertIn('ONLY',SEL)
        self.assertIn("Read-Host 'Choose [1]'",SEL)
        self.assertIn("$bgxChoice='1'",SEL)
        self.assertIn("$bgxChoice -ne '2'",SEL)
        self.assertIn('BGXAI_UPDATE.cmd',SEL)
        self.assertIn("BGXUNI_AUTOINSTALL.current.ps1'",SEL)
    def test_existing_ai_choice_remains_available(self):
        self.assertIn("$bgxChoice -ne '1' -and $bgxChoice -ne '2'",SEL)
        self.assertIn('falls through unchanged',SEL)
    def test_explicit_weiDU_path_no_tp2_flag(self):
        self.assertNotRegex(INST, r'&\s*\$setup\s*[\'\"]--tp2')
        self.assertNotRegex(SEL,r'&\s*\$setup\s*[\'\"]--tp2')
        self.assertIn("'--force-install','0'",INST)
        self.assertIn("'--reinstall'",INST)
        self.assertIn("'--noautoupdate'",INST)
    def test_only_new_script_in_tp2(self):
        tp=TP2.decode()
        self.assertEqual(len(re.findall(r'(?m)^\s*BEGIN\s',tp)),1)
        self.assertIn('COMPILE ~BGXUNI/BGXUN1.BAF~',tp)
        self.assertIn('~scripts/BGXUN1.BS~',tp)
        self.assertNotRegex(tp,r'(?i)(BDDEFAI|BGXGRP|BGXTANK)')
    def test_old_ai_preserved_even_on_failure(self):
        paths=re.findall(r"\$filesToBackup=@\((.*?)\)",INST,flags=re.S)[0]
        for bad in ['BDDEFAI','BGXGRP','BGXTANK','BGXRANG','BGXSCOUT']:
            self.assertNotIn(bad,paths)
        self.assertIn('Existing BGXUN1.BS without project marker',INST)
        self.assertIn('Existing BGXUN1.BCS without project marker',INST)
        self.assertIn('Root setup-BGXUNI.tp2 differs',INST)
    def test_game_closed_even_loader(self):
        self.assertIn('Get-Process -Name Baldur,BaldursGate,InfinityLoader',INST)
        self.assertIn('Get-Process -Name Baldur,BaldursGate,InfinityLoader',SEL)
    def test_compile_proven_before_activation_marker(self):
        self.assertIn('ValidCompiledScript',INST)
        self.assertIn("Contains('BGXU016')",INST)
        self.assertIn('BGXUNI\\INSTALLED.TAG',INST)
        self.assertLess(INST.index('if(!(ValidCompiledScript))'),INST.index('WriteAllText($installedTag'))
    def test_rollback_backups_scoped(self):
        self.assertIn('BGXUNI_parallel_preinstall_',INST)
        self.assertIn('$backupTable',INST)
        self.assertIn('Copy-Item -LiteralPath $item.backup',INST)
        self.assertIn('WeiDU metadata/game TLK rollback was NOT proven',INST)
    def test_repeat_install_idempotence(self):
        self.assertIn('ALREADY CURRENT:',INST)
        self.assertIn('0.1.6-no-idle-range-first',INST)
    def test_manifest_not_published_with_wrong_runtime_claim(self):
        self.assertIn('UNVERIFIED',MAN['status'])
        self.assertIn('UNVERIFIED',MAN['status'])
    def test_baf_manual_safety(self):
        content=BAF.decode()
        self.assertIn('ActionListEmpty()',content)
        self.assertNotIn('RemoveTraps()',content)
        self.assertNotIn('ForceSpell(',content)
    def test_onefile_selector_alters_only_new_path(self):
        self.assertIn('GetFile',SEL)
        self.assertIn('if($bgxChoice -eq \'1\')',SEL)
        self.assertIn('exit 0',SEL)
if __name__=='__main__':unittest.main(verbosity=2)
