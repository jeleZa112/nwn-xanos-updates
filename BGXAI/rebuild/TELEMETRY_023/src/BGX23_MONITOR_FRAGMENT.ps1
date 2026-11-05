# Candidate function for BGXAI_LIVE_MONITOR.ps1 v0.4.5 after Windows PS5.1 validation.
# Source-only: deliberately NOT auto-injected into the active local/private-sync monitor.
# Separately consumes BGX23 OBS records already emitted into BGXAI_COMBAT.log.
$script:BGX23ActionCounts=@{attack=0;retreat=0;song=0;other=0}
$script:BGX23Snapshots=@{}
function Observe-BGX23([string]$line) {
  if($line.Length -gt 600){return}
  if($line -notmatch '\[BGX23\] OBS seq=(\d+) actor=A([1-6]) slot=([1-6]) action=(\d+|\?) hp=(-?\d+|\?) class=(\d+|\?) pos=(-?\d+|\?),(-?\d+|\?) dest=(-?\d+|\?),(-?\d+|\?) target=(SELF|PARTY[1-6]|NONPARTY_UNVERIFIED|UNKNOWN) enemyLOS=(\d+|\?) selected=(SELECTED|UNKNOWN) skill=(-?\d+|\?) atkMode=(-?\d+|\?) manual=UNKNOWN enemyTarget=UNKNOWN weapon=UNKNOWN maxHP=UNKNOWN path=UNKNOWN sessionEpoch=UNKNOWN$') {return}
  $actor='A'+$Matches[2];$slot=[int]$Matches[3]
  if([int]$Matches[2] -ne $slot){return}
  $action=[int]$Matches[4]
  if($action -eq 355){$script:BGX23ActionCounts.retreat++}
  elseif($action -eq 296){$script:BGX23ActionCounts.song++}
  elseif(@(3,105,134) -contains $action){$script:BGX23ActionCounts.attack++}
  else{$script:BGX23ActionCounts.other++}
  # Do not publish exact coordinates, raw actor IDs, character names or source-game paths.
  $script:BGX23Snapshots[$actor]=@{
    actor=$actor;slot=$slot;hp=($Matches[5]);action=$action;
    target_category=([string]$Matches[11]);visible_hostiles=([string]$Matches[12]);
    skill_mode=([string]$Matches[14]);attack_mode=([string]$Matches[15]);
    manual_origin='UNKNOWN';enemy_target='UNKNOWN';path_safety='UNKNOWN'
  }
}
