param([string]$GameRoot='.')
$gr=$GameRoot
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$gr=(Resolve-Path -LiteralPath $gr).Path
$expectedRoot='C:\Games\BG_EET_FOXX_NEW'
if($gr.TrimEnd('\') -ine $expectedRoot) {Write-Host 'STOP: wrong game folder';exit 2}
if(!(Test-Path -LiteralPath (Join-Path $gr 'chitin.key') -PathType Leaf)) {Write-Host 'STOP: chitin.key missing';exit 2}
$zcd=Join-Path $env:LOCALAPPDATA 'BGXAI_UPDATER'
$pinnedFile=Join-Path $zcd 'head.txt'
if(!(Test-Path -LiteralPath $pinnedFile -PathType Leaf)){Write-Host 'STOP: pinned GitHub commit missing';exit 2}
$commitId=[IO.File]::ReadAllText($pinnedFile).Trim()
if($commitId -notmatch '^[a-fA-F0-9]{40}$'){Write-Host 'STOP: invalid pinned GitHub commit';exit 2}
$xrr='BGXAI/fox_new/'
$b41=@{
id='041';version='0.3.11';manifest=$xrr+'release_041/manifest.json';prefix=$xrr+'release_041/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_041';installer='BGXAI41_INSTALL.py';
names=@('BGXAI41_INSTALL.py','README_RU.md','SOURCE_MANIFEST.json','build_assets.py',
'setup-BGX41.tp2','BGX41/icon.tra','BGX41/toggle_icon.baf',
'combat_ru/GLOSSARY_RU.md','combat_ru/explain_attack.py','combat_ru/parse_attack_feedback.py',
'tests/test_attack_parser_041.py','tests/test_attack_ru.py','tests/test_installer_041.py',
'tests/test_runtime_semantics_041.py','tests/test_source_041.py')
}
$b40=@{
id='040';version='0.3.10';manifest=$xrr+'release_040/manifest.json';prefix=$xrr+'release_040/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_040';installer='BGXAI40_INSTALL.py';
names=@('BGXAI40_INSTALL.py','setup-BGX40.tp2','BGX40/toggle_feedback.baf','BGX40/lang/ru_ru/feedback.tra','SOURCE_MANIFEST.json','README_RU.txt','tests/test_feedback_040.py')
}
$release039=@{
id='039';version='0.3.9';manifest=$xrr+'release_039/manifest.json';prefix=$xrr+'release_039/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_039';installer='BGXAI39_INSTALL.py';
names=@('BGXAI39_INSTALL.py','setup-BGX39.tp2','BGX39/team_guard_fallback.baf','SOURCE_MANIFEST.json','README_RU.txt','tests/test_team_guard_039.py')
}
$b42=@{
id='042B';version='0.3.12-042B';manifest=$xrr+'release_042b/manifest.json';prefix=$xrr+'release_042b/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_042b';installer='BGXAI42_INSTALL.py';
names=@('BGXAI42_INSTALL.py','build_042b_preview.py','guard_source_042a.py',
'setup-BGX42.tp2','SOURCE_MANIFEST.json','README_RU.md',
'BGX42/tests/test_installer_042b.py','BGX42/tests/test_recovery_gate.py')
}
$x43=@{
id='043P';version='0.3.14-043-PROBE';manifest=$xrr+'release_043p/manifest.json';prefix=$xrr+'release_043p/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_043p';installer='BGXAI43_PROBE_INSTALL.py';
names=@('BGXAI43_PROBE_INSTALL.py','BGX43/setup-BGX43.tp2','BGX43/M_BGX43Probe.lua',
'BGX43/tests/test_installer_043.py','README_RU.md','eeex_bridge_043.py',
'intercept_policy.py','test_eeex_bridge_043.py','SOURCE_MANIFEST.json')
}
$t44=@{
id='044';version='0.3.15-044-DIAG';manifest=$xrr+'release_044/manifest.json';prefix=$xrr+'release_044/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_044';installer='BGXAI44_INSTALL.py';
names=@('BGXAI44_INSTALL.py','BGX44/setup-BGX44.tp2','BGX44/M_BGX44Diag.lua',
'README_RU.md','BGX44/tests/test_installer_044.py',
'BGX44/tests/test_lua_044.py','SOURCE_MANIFEST.json')
}
$t45=@{
id='045';version='0.3.16b-045-RESREF-FIX';manifest=$xrr+'release_045b/manifest.json';prefix=$xrr+'release_045b/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_045';installer='BGXAI45_INSTALL.py';
names=@('BGXAI45_INSTALL.py','BGX45/setup-BGX45.tp2','BGX45/M_BX43.lua',
'BGX45/M_BX44.lua','README_RU.md','BGX45/tests/test_installer_045.py',
'BGX45/tests/test_lua_045.py','SOURCE_MANIFEST.json')
}
$t46=@{
id='046';version='0.3.17-046-ATTACK-FILTER';manifest=$xrr+'release_046/manifest.json';prefix=$xrr+'release_046/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_046';installer='BGXAI46_INSTALL.py';
names=@('BGXAI46_INSTALL.py','BGX46/setup-BGX46.tp2','BGX46/M_BX43.lua',
'BGX46/tests/test_installer_046.py','BGX46/tests/test_lua_046.py',
'README_RU.md','SOURCE_MANIFEST.json')
}
$t47=@{
id='047';version='0.3.18-047-RESOLVED-TARGET';manifest=$xrr+'release_047/manifest.json';prefix=$xrr+'release_047/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_047';installer='BGXAI47_INSTALL.py';
names=@('BGXAI47_INSTALL.py','BGX47/setup-BGX47.tp2','BGX47/M_BX43.lua',
'BGX47/tests/test_installer_047.py','BGX47/tests/test_lua_047.py',
'README_RU.md','SOURCE_MANIFEST.json')
}
$t48=@{
id='048';version='0.3.19-048-CONFIRMED-HIT';manifest=$xrr+'release_048/manifest.json';prefix=$xrr+'release_048/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_048';installer='BGXAI48_INSTALL.py';
names=@('BGXAI48_INSTALL.py','BGX48/setup-BGX48.tp2','BGX48/M_BX43.lua',
'BGX48/tests/test_installer_048.py','BGX48/tests/test_lua_048.py',
'README_RU.md','SOURCE_MANIFEST.json')
}
$t49=@{
id='049';version='0.3.20-049-GUARD-ADVISORY';manifest=$xrr+'release_049/manifest.json';prefix=$xrr+'release_049/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_049';installer='BGXAI49_INSTALL.py';
names=@('BGXAI49_INSTALL.py','BGX49/setup-BGX49.tp2','BGX49/M_BX43.lua',
'BGX49/tests/test_installer_049.py','BGX49/tests/test_lua_049.py',
'README_RU.md','SOURCE_MANIFEST.json')
}
$release054=@{
id='054';version='0.3.21-054-WEIDU-READONLY';manifest=$xrr+'release_054/manifest.json';prefix=$xrr+'release_054/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_054';installer='compile_guard_054.py';
names=@('compile_guard_054.py','verify_053_baseline.py','BGX52_guard_receiver_PREVIEW.baf',
'test_compile_054.py','README_RU.md','SOURCE_MANIFEST.json')
}
$x56=@{
id='056';version='0.3.22-056-ACTIVE-GUARD-OPTIN';
manifest=$xrr+'experimental_056_active_guard/manifest.json';prefix=$xrr+'experimental_056_active_guard/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_056';installer='BGXAI56_INSTALL.py';
names=@('BGX56/M_BX43.lua','BGX56/BGX56_RECEIVER.baf','BGX56/setup-BGX56.tp2','BGXAI56_BUILDER.py','BGXAI56_INSTALL.py','README_RU.md','tests/test_056.py','tests/test_lua_056.py','ci_weidu_056.py','ids/trigger.ids','ids/action.ids','ids/object.ids','ids/modal.ids','SOURCE_MANIFEST.json')
}
$b60=@{
id='060';version='0.3.26-060-READONLY-COMPILE';
manifest=$xrr+'experimental_060_direct_response_source_only/manifest.json';
prefix=$xrr+'experimental_060_direct_response_source_only/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_060';installer='BGXAI60_INSTALL.py';
names=@('BGX60_RECEIVER.baf','generate_baf.py','BGXAI60_BUILDER.py','BGXAI60_INSTALL.py','test_060.py','test_060_install.py','README_RU.md')
}
$x61=@{
id='061';version='0.3.27-061-RESCUE-APPROACH';
manifest=$xrr+'experimental_061_rescue_approach_source_only/manifest.json';
prefix=$xrr+'experimental_061_rescue_approach_source_only/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_061';installer='BGXAI61_INSTALL.py';
names=@('BGX61_RECEIVER.baf','generate_baf.py','BGXAI61_BUILDER.py','BGXAI61_INSTALL.py','test_061.py','test_061_install.py','README_RU.md')
}
$release064=@{
id='064';version='0.3.29-064-061-SAME-AREA-GUARD-SOURCE';
manifest=$xrr+'experimental_064_same_area_061_source_only/manifest.json';
prefix=$xrr+'experimental_064_same_area_061_source_only/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_064';installer='BGXAI64_PREFLIGHT_READONLY.py';
names=@('M_BX43_064_CANDIDATE.lua','BGX64_BRIDGE_PREPARE_NATIVE.lua','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','README_RU.md','lua64_harness.py','test_064_native.py','test_064_patch.py','test_064_preflight.py','SOURCE_MANIFEST.json')
}
$x64=@{
id='064G';version='0.3.30-064-GUARDED-WEIDU-CANDIDATE';
manifest=$xrr+'experimental_064_guarded_weidu_source_only/manifest.json';
prefix=$xrr+'experimental_064_guarded_weidu_source_only/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_064_guarded';installer='BGXAI64_INSTALL_SOURCE_ONLY.py';
names=@('M_BX43_064_CANDIDATE.lua','M_BX43_061_BASELINE_READONLY.lua','BGX64_BRIDGE_PREPARE_NATIVE.lua','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','BGXAI64_INSTALL_SOURCE_ONLY.py','test_064_install_mock.py','test_064_patch.py','test_064_preflight.py','README_RU.md')
}
$x66=@{
id='066';version='0.3.32-066-MULTI-FRONTLINE-GUARDED';
manifest=$xrr+'experimental_066_multi_guard_guarded/manifest.json';
prefix=$xrr+'experimental_066_multi_guard_guarded/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_066_guarded';installer='BGXAI66_INSTALL.py';
names=@('BGX66_TEAM_BRIDGE.lua','M_BX43_064_BASELINE_READONLY.lua','M_BX43_066_CANDIDATE.lua','build_066.py','BGXAI66_INSTALL.py','BGXAI64_INSTALL_SOURCE_ONLY.py','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','M_BX43_061_BASELINE_READONLY.lua','M_BX43_064_CANDIDATE.lua','test_066_native.py','test_066_install_mock.py','lua65_harness.py','README_RU.md')
}
$x6s=@{
id='066S';version='0.3.34-066S-CASTER-GUARDED';
manifest=$xrr+'experimental_066s_guarded_install_candidate/manifest_updater.json';
prefix=$xrr+'experimental_066s_guarded_install_candidate/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_066s_guarded';installer='BGXAI66S_INSTALL.py';
names=@('BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf','BGX66_CASTER_SUPPORT.lua','BGXAI64_INSTALL_SOURCE_ONLY.py','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','BGXAI66S_BCS_PATCH.py','BGXAI66S_INSTALL.py','M_BX43_061_BASELINE_READONLY.lua','M_BX43_064_CANDIDATE.lua','M_BX43_066S_CASTER_CANDIDATE.lua','M_BX43_066_BASELINE_READONLY.lua','M_BX43_066_CANDIDATE.lua','README_RELEASE_RU.md','README_RU.md','build_066.py','build_066s.py','ci_weidu_066s.py','generate_receiver.py','ids/action.ids','ids/modal.ids','ids/object.ids','ids/spell.ids','ids/trigger.ids','lua65_harness.py','native_066_fixture.py','test_066s_caster_native.py','test_066s_installer_mock.py','verify_066s.py','verify_release.py')
}
$x67=@{
id='067';version='0.3.35-067-EARLY-GUARD-GUARDED';
manifest=$xrr+'experimental_067_early_guard_guarded/manifest_updater.json';
prefix=$xrr+'experimental_067_early_guard_guarded/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_067_early_guard';installer='BGXAI67_INSTALL.py';
names=@('BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf','BGX66_CASTER_SUPPORT.lua','BGX67_EARLY_GUARD.baf','BGX67_PREHIT_GUARD.lua','BGXAI64_INSTALL_SOURCE_ONLY.py','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','BGXAI66S_BCS_PATCH.py','BGXAI66S_INSTALL.py','BGXAI67_BCS_PATCH.py','BGXAI67_INSTALL.py','M_BX43_064_CANDIDATE.lua','M_BX43_066S_CASTER_CANDIDATE.lua','M_BX43_066_BASELINE_READONLY.lua','M_BX43_066_CANDIDATE.lua','M_BX43_067_EARLY_CANDIDATE.lua','README_RU.md','build_066.py','build_066s.py','build_067.py','ci_weidu_067.py','generate_067_baf.py','generate_receiver.py','ids/action.ids','ids/modal.ids','ids/object.ids','ids/spell.ids','ids/trigger.ids','lua65_harness.py','native_066_fixture.py','test_066s_installer_mock.py','test_067_bcs.py','test_067_install_mock.py','test_067_native.py')
}

$xidle=@{
id='IDLE';version='0.3.36-066S-IDLE-GUARD-PILOT';
manifest='BGXAI/patchsets/eps_first_066s_idle_guard_pilot_guarded_installer_source_only/manifest_updater.json';
prefix='BGXAI/patchsets/eps_first_066s_idle_guard_pilot_guarded_installer_source_only/';
localPath=Join-Path $gr 'BGXAI_DEV\experimental_066s_idle_guard_pilot';
installer='BGXAI_IDLE_GUARD_INSTALL_SOURCE_ONLY.py';
names=@('066S_idle_guard_minimal.diff','BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf','BGX66_CASTER_SUPPORT.lua','BGXAI_IDLE_GUARD_INSTALL_SOURCE_ONLY.py','M_BX43_066S_IDLE_GUARD_CANDIDATE.lua','M_BX43_066S_VERIFIED_ORIGINAL.lua','M_BX43_066_BASELINE_READONLY.lua','README_INSTALLER_RU.md','README_RU.md','TEST_PROTOCOL_RU.md','lua65_harness.py','manifest_install_sha256.json','native_066_fixture.py','parse.lua','run_tests.py','test_066s_caster_native.py','test_guarded_installer.py','test_idle_guard.py','verify_install_release.py')
}

$xpr=@{
id='BGXPR';version='0.3.37-BGXPR-ONEFILE';
manifest='BGXAI/patchsets/priest_modes_eps_first_installable_20261116/manifest_updater.json';
prefix='BGXAI/patchsets/priest_modes_eps_first_installable_20261116/';
localPath=Join-Path $gr 'BGXAI_DEV\priest_modes_verified';installer='BGXPR_INSTALL.py';
names=@('M_BX43_066S_CASTER_CANDIDATE.lua','M_BX43_066S_GUARD_TEAM_CANDIDATE.lua','M_BX43_066S_PRIEST_MODES.lua','M_BX43_BGXTEAM_PRIEST_MODES.lua','BGXPR_LAST_PRIORITY.baf','BGXPR_BCS_PATCH.py','BGXPR_INSTALL.py','parse.lua','SHA256_FILES.json')
}
$xteam=@{
id='BGXTEAM';version='0.3.38-BGXTEAM-ONEFILE';
manifest='BGXAI/patchsets/team_f_guard_066s_installable_pilot_20261116/manifest_updater.json';
prefix='BGXAI/patchsets/team_f_guard_066s_installable_pilot_20261116/';
localPath=Join-Path $gr 'BGXAI_DEV\team_guard_verified';installer='BGXAI_TEAM_GUARD_INSTALL.py';
names=@('BGXAI_TEAM_GUARD_INSTALL.py','M_BX43_066S_VERIFIED_ORIGINAL.lua','M_BX43_066S_GUARD_TEAM_CANDIDATE.lua')
}
$xp2=@{
id='BGXP2';version='0.3.39-BGXP2-COMBAT-PRIEST';
manifest='BGXAI/patchsets/priest_combat_eps_first_20261116/manifest_updater.json';
prefix='BGXAI/patchsets/priest_combat_eps_first_20261116/';
localPath=Join-Path $gr 'BGXAI_DEV\priest_combat_verified';installer='BGXP2_INSTALL.py';
names=@('BGXP2_LAST_PRIORITY.baf','BGXP2_BCS_PATCH.py','BGXP2_INSTALL.py','README_RU.md','PLAYTEST_RU.md','test_bgxp2.py','SHA256_FILES.json')
}
$xp3=@{
id='BGXP3';version='0.3.40-BGXP3-AUTO-BUFFER';
manifest='BGXAI/patchsets/priest_auto_attack_buffer_source_only_20261117/manifest_updater.json';
prefix='BGXAI/patchsets/priest_auto_attack_buffer_source_only_20261117/';
localPath=Join-Path $gr 'BGXAI_DEV\priest_auto_buffer_verified';installer='BGXP3_INSTALL.py';
names=@('BGXP2_LAST_PRIORITY.baf','BGXP2_BCS_PATCH.py','BGXP3_AUTO_ATTACK_BUFFER_SOURCE_ONLY.py','BGXP3_BCS_PREFLIGHT_SOURCE_ONLY.py','BGXP3_INSTALL.py','README_RU.md','test_bgxp3_auto_attack_buffer.py','test_bgxp3_bcs_preflight.py','SHA256_FILES.json')
}
$xp5=@{
id='BGXP5';version='0.3.41-BGXP5-AUTO-PRIORITY-GUARD';
manifest='BGXAI/patchsets/priest_auto_priority_guard_source_20261117/manifest_updater.json';
prefix='BGXAI/patchsets/priest_auto_priority_guard_source_20261117/';
localPath=Join-Path $gr 'BGXAI_DEV\priest_auto_priority_verified';installer='BGXP5_INSTALL.py';
names=@('BGXPR_LAST_PRIORITY.baf','BGXP2_LAST_PRIORITY.baf','BGXP2_BCS_PATCH.py','BGXP5_PRIORITY_AND_ALLY_GUARD_SOURCE_ONLY.py','BGXP5_BCS_PREFLIGHT_READ_ONLY.py','BGXP5_INSTALL.py','test_bgxp5_source.py','test_bgxp5_bcs_preflight.py','test_bgxp5_installer_mock.py','README_RU.md','SHA256_FILES.json')
}
$ao=@{
id='AOE117';version='0.3.50-BGX122-IDS-HYPHEN';
manifest='BGXAI/patchsets/aoe_entangle_readonly_onefile_20261117/manifest_updater.json';
prefix='BGXAI/patchsets/aoe_entangle_readonly_onefile_20261117/';
localPath=Join-Path $gr 'BGXAI_DEV\aoe_readonly_verified';installer='BGXAI_AOE_AUDIT.py';
names=@('BGXAI_AOE_AUDIT.py','test_aoe_audit.py','BGXAI_TEST6_SAFE_COPY.py','test_safe_copy.py','BGX119_TRACE.py','BGX120_ENTANGLE_GUARD.py','test_guard120.py','BGX121_POLICY.py','BGX121_READONLY.py','test_121.py','BGX122_PROJECTILES_READONLY.py','test_122.py','README_RU.md')
}
$rg=@{
id='BGXRANGED';version='0.3.90-V7-R27-DPLAYER-FUNCTIONAL';
manifest='BGXAI/patchsets/ranged_fighter_guarded_20261119/manifest_updater.json';
prefix='BGXAI/patchsets/ranged_fighter_guarded_20261119/';
localPath=Join-Path $gr 'BGXAI_DEV\ranged_fighter_verified';installer='BGXRANGED_PREFLIGHT.py';
names=@('BGXRANGED_PREFLIGHT.py','BGX_RANGED_FIGHTER.baf','BGXRANGED_GUARDED_INSTALL.py','BGXRANGED_V2_MELEE_HANDOFF.baf','BGXRANGED_V2_PREFLIGHT.py','BGXRANGED_V2_GUARDED_INSTALL.py','BGXRANGED_V3_MELEE_HANDOFF.baf','BGXRANGED_V3_PREFLIGHT.py','BGXRANGED_V3_GUARDED_INSTALL.py','BGX_FRIENDLY_AGGRO_AUDIT_READONLY.py','BGXRANGED_V4_NO_FRIEND_ATTACK.baf','BGX_FRIENDLY_PROTECT_ISOLATION.py','BGXAI_SAVE_SCRIPT_AUDIT_READONLY.py','BGX_FRIENDLY_RETALIATION_GUARDED.py','BGX_COMBAT_LOG_READONLY_AUDIT.py','M_BXFR.lua','BGX_FRIEND_TRACE_GUARDED.py','BGX_FRIEND_TRACE_REPORT.py','M_BXFR_CONSOLE_V2.lua','BGXFTRACE_V2_GUARDED.py','BGXFTRACE_CONSOLE_CAPTURE.py','M_BXFR_MOTION_V3.lua','BGXFTRACE_V3_GUARDED.py','BGXF_WTASIGHT_ENEMY_GUARD_SOURCE_ONLY.py','BGXFENEMY_WTASIGHT_GUARDED.py','BGXAI_WEAPON_SAVED_SNAPSHOT_READONLY.py','BGXAI_WEAPON_CHOICE_ADVISORY_V1.js','BGXAI_WEAPON_TRAITS_ADVISORY_V1.js','BGXRANGED_V5_ANTICIPATORY_CLOSE_SOURCE_ONLY.baf','BGXRANGED_V5_NATIVE_CANDIDATE_READONLY.py','BGXRANGED_V5_GUARDED_INSTALL.py','BGXRANGED_V6_DPLAYER_CLOSE_GUARD_SOURCE_ONLY.baf','BGXRANGED_V6_DPLAYER_NATIVE_READONLY.py','BGXRANGED_V6_GUARDED_INSTALL.py','BGXRANGED_V7_GUARDED_INSTALL.py')
}
$wr=@{id='WRO';version='0.3.77-WEAPON-NATIVE-READONLY';manifest=($rg.prefix+'BGXAI_WEAPON_NATIVE_PREFLIGHT_MANIFEST_V1.json');prefix=$rg.prefix;localPath=Join-Path $gr 'BGXAI_DEV\weapon_native_ro';names=@('BGXAI_WEAPON_GAME_PREFLIGHT_RO.py','BGXAI_WEAPON_GAME_PREFLIGHT_V1.baf')}
$wp=@{id='WP';version='0.3.82-R4-ALLPROF-BUFF-RO';manifest=($rg.prefix+'BGXWP_OBSERVER_MANIFEST_R1.json');prefix=$rg.prefix;localPath=Join-Path $gr 'BGXAI_DEV\weapon_runtime_ro';names=@('BGXWP_OBSERVER_GUARDED.py','M_BGXWP.lua','BGXW2_OBSERVER_GUARDED.py','M_BGXW2.lua','BGXAI_WEAPON_NATIVE_ITM_R3_RO.py','M_BGXW4.lua')}
$td13=@{id='TD13';version='0.3.85-R13-TARGET-MISSILE-RO';manifest=($rg.prefix+'BGXAI_R13_MANIFEST_V1.json');prefix=$rg.prefix;localPath=Join-Path $gr 'BGXAI_DEV\weapon_target_r13';names=@('BGXAI_R13_GUARDED.py','M_BGXTDEF13.lua')}
$td14=@{id='TD14';version='0.3.87-R13-CONSOLE-CAPTURE-RO';manifest=($rg.prefix+'BGXAI_R13_SHORTNAME_MANIFEST_V1.json');prefix=$rg.prefix;localPath=Join-Path $gr 'BGXAI_DEV\weapon_target_r13_shortfix';names=@('BGXAI_R13_SHORTNAME_GUARDED.py','M_BGXD13.lua')}
$td15=@{id='TD15';version='0.3.88-R13-HOLD-DIAG-RO';manifest=($rg.prefix+'BGXAI_R13_HOLD_DIAG_MANIFEST_V1.json');prefix=$rg.prefix;localPath=Join-Path $gr 'BGXAI_DEV\weapon_target_r13_diag';names=@('BGXAI_R13_HOLD_DIAG_GUARDED.py','R15_M_BGXD13.lua')}
$r27=@{id='R27';version='0.3.89-R27-PASSIVE-GUARDED';manifest='BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/manifest_updater.json';prefix='BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/';localPath=Join-Path $gr 'BGXAI_DEV\weapon_r27_observer';names=@('BGXAI_R27_GUARDED.py','M_BGXR27.lua','BGXAI_R28_NATIVE_FROM_R27_RO.py','BGXAI_WEAPON_NATIVE_ITM_R3_RO.py')}
$w3=@{id='W3';version='0.3.92-BGXAI-AUTO-BATCH-RO';manifest='BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_COMPILE_MANIFEST_V1.json';prefix='BGXAI/patchsets/ranged_fighter_guarded_20261119/';localPath=Join-Path $gr 'BGXAI_DEV\weapon_priority_v3';names=@('BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py','BGXAI_WEAPON_SLOT_CONSUMER_V3.baf','BGXAI_AUTO_BATCH_RO_V1.py','test_auto_batch_ro_v1.py','test_weapon_native_compile_ro_v1.py','BGXAI_R29_GUARDED.py','BGXAI_R29_KHALID_BOW_TO_SWORD.baf')}
$v2install=Join-Path $rg.localPath 'BGXRANGED_V2_GUARDED_INSTALL.py'
$ff=Join-Path $rg.localPath 'BGX_FRIENDLY_RETALIATION_GUARDED.py'
$rr=$rg.localPath
$trace=Join-Path $rr 'BGX_FRIEND_TRACE_GUARDED.py'
$fix=Join-Path $rr 'BGXFTRACE_V2_GUARDED.py'
$cap=Join-Path $rr 'BGXFTRACE_CONSOLE_CAPTURE.py'
$motion=Join-Path $rr 'BGXFTRACE_V3_GUARDED.py'
$enemy=Join-Path $rr 'BGXFENEMY_WTASIGHT_GUARDED.py'
function Get-PinnedBytes([string]$zrp) {
if($zrp -notmatch '^BGXAI/(?:fox_new/(?:release_0(39|40|41|42b|43p|44|45|45b|46|47|48|49|54)|experimental_056_active_guard|experimental_060_direct_response_source_only|experimental_061_rescue_approach_source_only|experimental_064_same_area_061_source_only|experimental_064_guarded_weidu_source_only|experimental_066_multi_guard_guarded|experimental_066s_guarded_install_candidate|experimental_067_early_guard_guarded)|patchsets/eps_first_066s_idle_guard_pilot_guarded_installer_source_only|patchsets/priest_modes_eps_first_installable_20261116|patchsets/team_f_guard_066s_installable_pilot_20261116|patchsets/priest_combat_eps_first_20261116|patchsets/priest_auto_attack_buffer_source_only_20261117|patchsets/priest_auto_priority_guard_source_20261117|patchsets/aoe_entangle_readonly_onefile_20261117|patchsets/ranged_fighter_guarded_20261119|BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123)/[A-Za-z0-9_./-]+$' -or $zrp.Contains('..')) {
throw ('Remote source path blocked: '+$zrp)
}
$urls=@(
('https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'+$commitId+'/'+$zrp),
('https://cdn.jsdelivr.net/gh/jeleZa112/nwn-xanos-updates@'+$commitId+'/'+$zrp)
)
[IO.Directory]::CreateDirectory($zcd) | Out-Null
$ztf=Join-Path $zcd ('pinned_'+[guid]::NewGuid().ToString('N')+'.tmp')
$failures=@()
try {
foreach($uri in $urls) {
try {
Invoke-WebRequest -Uri $uri -Headers @{'User-Agent'='BGXAI-Foxx-Onefile'} -TimeoutSec 60 -UseBasicParsing -OutFile $ztf -ErrorAction Stop | Out-Null
$rawBytes=[IO.File]::ReadAllBytes($ztf)
if($rawBytes.Length -lt 1 -or $rawBytes.Length -gt 500000) {throw ('Unexpected pinned source byte count: '+$zrp)}
return ,$rawBytes
} catch {
$failures+=($_.Exception.Message)
if(Test-Path -LiteralPath $ztf){Remove-Item -LiteralPath $ztf -Force -ErrorAction SilentlyContinue}
}
}
throw ('Both raw source hosts failed for '+$zrp+': '+($failures -join '; '))
} finally {
if(Test-Path -LiteralPath $ztf){Remove-Item -LiteralPath $ztf -Force -ErrorAction SilentlyContinue}
}
}
function HashBytes([byte[]]$payload) {
$hasher=[Security.Cryptography.SHA256]::Create()
try {return ([BitConverter]::ToString($hasher.ComputeHash($payload))).Replace('-','').ToLowerInvariant()}
finally {$hasher.Dispose()}
}
function HashFile([string]$filePath) {
if(!(Test-Path -LiteralPath $filePath -PathType Leaf)){return ''}
$hasher=[Security.Cryptography.SHA256]::Create()
try {
$stream=[IO.File]::OpenRead($filePath)
try{return ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
finally {$stream.Dispose()}
} finally {$hasher.Dispose()}
}
function ANR([string]$item) {
if(Test-Path -LiteralPath $item){
$node=Get-Item -LiteralPath $item -Force
if(($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('Reparse path blocked: '+$item)}
}
}
function VM($spec) {
$bytes=Get-PinnedBytes $spec.manifest
if($bytes.Length -gt 30000){throw 'Oversized manifest'}
$m=[Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
if($m.schema -ne 1 -or $m.channel -ne 'bgxai-fox-new-safe-source' -or $m.version -ne $spec.version){throw 'Unexpected release manifest'}
$items=@($m.files)
if($items.Count -ne $spec.names.Count){throw 'Unexpected release source count'}
$seen=@{}
foreach($entry in $items){
$file=[string]$entry.dest;$remote=[string]$entry.source
if(($spec.names -cnotcontains $file) -or $seen.ContainsKey($file) -or $remote -cne ($spec.prefix+$file)){throw 'Release path not in allowlist'}
if($entry.size -le 0 -or $entry.size -gt 500000 -or [string]$entry.sha256 -cnotmatch '^[a-f0-9]{64}$'){throw 'Bad release size/hash'}
$seen[$file]=@{sha=[string]$entry.sha256;size=[int]$entry.size;remote=$remote}
}
if($seen.Count -ne $spec.names.Count){throw 'Missing release files'}
return $seen
}
function Generate041Assets($spec) {
if($spec.id -ne '041'){return}
$checked=VM $spec
foreach($name in $spec.names) {
$f=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
ANR $f
if((HashFile $f) -cne $checked[$name].sha){throw ('Unverified BGX41 generator/source: '+$name)}
}
$manifest=[Text.Encoding]::UTF8.GetString((Get-PinnedBytes $spec.manifest)) | ConvertFrom-Json
$expected=@('BGX41/BGX41IC.BAM','BGX41/BGX41ON.SPL','BGX41/BGX41OF.SPL')
$generated=@($manifest.generated_files)
if($generated.Count -ne 3){throw 'BGX41: incorrect generated asset count'}
$seen=@{}
foreach($x in $generated) {
$name=[string]$x.dest
if(($expected -cnotcontains $name) -or $seen.ContainsKey($name) -or $x.size -le 0 -or $x.size -gt 5000 -or [string]$x.sha256 -cnotmatch '^[a-f0-9]{64}$'){
throw 'BGX41: invalid binary metadata'
}
$seen[$name]=$x
}
$zcur=$true
foreach($name in $expected) {
$dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
ANR (Split-Path -Parent $dest)
ANR $dest
if((HashFile $dest) -cne [string]$seen[$name].sha256) {$zcur=$false}
}
if(!$zcur) {
Write-Host 'BGX41: build icons from verified source.'
$builder=Join-Path $spec.localPath 'build_assets.py'
& py -3 $builder
if($LASTEXITCODE -ne 0){throw ('BGX41: asset generator exited '+$LASTEXITCODE)}
}
foreach($name in $expected) {
$dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
if(!(Test-Path -LiteralPath $dest -PathType Leaf)){throw ('BGX41: generated binary missing '+$name)}
if((Get-Item -LiteralPath $dest).Length -ne [int]$seen[$name].size -or (HashFile $dest) -cne [string]$seen[$name].sha256){
throw ('BGX41: generated checksum mismatch '+$name)
}
Write-Host (' VERIFIED generated '+$name)
}
}
function SyncRelease($spec){
ANR $gr
ANR (Join-Path $gr 'BGXAI_DEV')
ANR $spec.localPath
Write-Host ('Verifying BGXAI '+$spec.id+' from pinned commit ...')
$list=VM $spec
$payload=@{}
foreach($name in $spec.names){
$bytes=Get-PinnedBytes $list[$name].remote
if($bytes.Length -ne $list[$name].size -or (HashBytes $bytes) -cne $list[$name].sha){throw ('SHA256 mismatch: '+$name)}
$payload[$name]=$bytes
Write-Host (' VERIFIED '+$name)
}
$zcur=$true
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
if((HashFile $dest) -cne $list[$name].sha){$zcur=$false}
}
if($zcur){Generate041Assets $spec;Write-Host ('BGXAI '+$spec.id+' verified; no changes.');return}
$stamp=(Get-Date -Format 'yyyyMMdd_HHmmss_fff')
$oldCopy=Join-Path $zcd ($spec.id+'_backup_'+$stamp)
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
ANR (Split-Path -Parent $dest)
ANR $dest
if(Test-Path -LiteralPath $dest){
$oldFile=Join-Path $oldCopy ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
[IO.Directory]::CreateDirectory((Split-Path -Parent $oldFile))|Out-Null
[IO.File]::Copy($dest,$oldFile,$false)
}
}
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
[IO.Directory]::CreateDirectory((Split-Path -Parent $dest))|Out-Null
$temp=$dest+'.bgxsync.tmp'
if(Test-Path -LiteralPath $temp){throw ('Unresolved temp file, stop: '+$temp)}
[IO.File]::WriteAllBytes($temp,[byte[]]$payload[$name])
if((HashFile $temp) -cne $list[$name].sha){throw ('Staged file hash failure: '+$name)}
if(Test-Path -LiteralPath $dest){[IO.File]::Delete($dest)}
[IO.File]::Move($temp,$dest)
if((HashFile $dest) -cne $list[$name].sha){throw ('Source file hash failure: '+$name)}
}
Generate041Assets $spec
Write-Host ('BGXAI '+$spec.id+' SOURCE SYNC DONE. Live scripts and WeiDU unchanged.')
}
function RR($spec,[string]$mode){
$list=VM $spec
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
ANR $dest
if((HashFile $dest) -cne $list[$name].sha){throw ('Unverified local source; select source sync first: '+$name)}
}
Generate041Assets $spec
$installerPath=Join-Path $spec.localPath $spec.installer
if($mode -eq '--install' -or $mode -eq '--uninstall'){
Write-Host 'WARNING: experimental WeiDU change; requires explicit YES.'
Write-Host 'Close game/loader/WeiDU; backup required.'
}
if($spec.id -eq '042B' -and $mode -eq '--status'){
& py -3 $installerPath
} else {
& py -3 $installerPath $mode
}
if($LASTEXITCODE -ne 0){throw ('BGXAI '+$spec.id+' installer returned code '+$LASTEXITCODE)}
}
function Run060Guarded([string]$mode) {
if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI060 unsafe operation blocked'}
SyncRelease $b60
$files=VM $b60
foreach($name in $b60.names){
$dest=Join-Path $b60.localPath $name
ANR $dest
if((HashFile $dest) -cne $files[$name].sha){throw ('BGXAI060 source SHA mismatch: '+$name)}
}
$ztok=if($mode -ceq 'install'){'INSTALL_BGXAI_060'}else{'ROLLBACK_BGXAI_060'}
Write-Host '060 EXPERIMENTAL: WeiDU game edit.'
Write-Host 'Close game/loader; SHA backup required.'
$zcf=Read-Host ('Type '+$ztok+' exactly to authorize or press ENTER to cancel')
if($zcf -cne $ztok){Write-Host '060 cancelled; no game change.';return}
& py -3 (Join-Path $b60.localPath 'BGXAI60_INSTALL.py') $mode '--yes' '--confirm' 'BGXAI_060_EXPERIMENTAL'
if($LASTEXITCODE -ne 0){throw ('BGXAI060 '+$mode+' STOP code '+$LASTEXITCODE+'. No automatic retry. Save output for review.')}
Write-Host ('BGXAI060 '+$mode+' completed; inspect WeiDU status and game behavior.')
}
function Status060ReadOnly {
$log=Join-Path $gr 'WeiDU.log'
$bcs=Join-Path $gr 'override\BDDEFAI.BCS'
$lua=Join-Path $gr 'override\M_BX43.lua'
ANR $log
ANR $bcs
ANR $lua
if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
$rows=@(Get-Content -LiteralPath $log -ErrorAction Stop | Where-Object {$_.TrimStart().StartsWith('~')})
if($rows.Count -lt 1){throw 'WeiDU.log has no active components'}
$last=[string]$rows[-1]
$is060=($last -match '(?i)BGX60[/\\]SETUP-BGX60[.]TP2~')
$is056=($last -match '(?i)BGX56[/\\]SETUP-BGX56[.]TP2~')
$actualBCS=HashFile $bcs
$actualLua=HashFile $lua
Write-Host ('Last WeiDU component: '+$last)
Write-Host ('BGXAI060 is LAST: '+$is060)
Write-Host ('BGXAI056 is LAST: '+$is056)
Write-Host ('056 Lua SHA unchanged: '+($actualLua -ceq '35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab'))
if($is056){
Write-Host ('056 BCS SHA correct: '+($actualBCS -ceq '054c1c8e99b4d8ef8fb541287844d46cb81faa4c320f59c3f39f82f8bf0ab87c'))
} elseif($is060) {
$stage=Join-Path $gr 'BGX60\staged\BDDEFAI.BCS'
ANR $stage
Write-Host ('060 staged BCS SHA matches installed: '+((HashFile $stage) -ceq $actualBCS -and $actualBCS.Length -eq 64))
} else {Write-Host 'BGXAI060/056 is not last; do not install/rollback blindly.'}
Write-Host ('Installed BCS SHA256: '+$actualBCS)
}
function Test061ReadOnly {
$spec=$x61
$list=VM $spec
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath $name
ANR $dest
if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI061 unverified file: '+$name)}
}
Write-Host '061 WeiDU BAF/Lua preflight (RO).'
& py -3 (Join-Path $spec.localPath 'BGXAI61_INSTALL.py') preflight
if($LASTEXITCODE -ne 0){throw ('BGXAI 061 preflight FAILED: exit '+$LASTEXITCODE+'. No changes to game.')}
Write-Host 'BGXAI 061 - preflight PASS; installed 060 unchanged.'
}
function Run061Guarded([string]$mode) {
if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI061 unknown mode blocked'}
SyncRelease $x61
$list=VM $x61
foreach($name in $x61.names){
$dest=Join-Path $x61.localPath $name
ANR $dest
if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI061 source SHA mismatch: '+$name)}
}
$ztok=if($mode -ceq 'install'){'INSTALL_BGXAI_061'}else{'ROLLBACK_BGXAI_061'}
Write-Host 'BGXAI061: guarded BCS+Lua via WeiDU.'
Write-Host 'Close game/loader; SHA backup required.'
$zcf=Read-Host ('Type '+$ztok+' exactly to authorize or ENTER to cancel')
if($zcf -cne $ztok){Write-Host '061 cancelled.';return}
& py -3 (Join-Path $x61.localPath 'BGXAI61_INSTALL.py') $mode '--yes' '--confirm' 'BGXAI_061_EXPERIMENTAL'
if($LASTEXITCODE -ne 0){throw ('BGXAI 061 '+$mode+' STOP code '+$LASTEXITCODE+'. Do not retry blindly.')}
Write-Host ('BGXAI 061 '+$mode+' completed, inspect status 68.')
}
function Verify064GuardedSource {
$spec=$x64
$list=VM $spec
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath $name
ANR $dest
if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI064G source SHA mismatch: '+$name)}
}
}
function Test064GuardedReadOnly {
SyncRelease $x64
Verify064GuardedSource
Write-Host '064 guarded preflight (RO).'
& py -3 (Join-Path $x64.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') preflight
if($LASTEXITCODE -ne 0){throw ('BGXAI064 guarded PRECHECK STOP '+$LASTEXITCODE)}
Write-Host 'BGXAI064 guarded preflight PASS. Installed 061 remains unchanged.'
}
function Status064GuardedReadOnly {
SyncRelease $x64
Verify064GuardedSource
& py -3 (Join-Path $x64.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') status
if($LASTEXITCODE -ne 0){throw ('BGXAI064 guarded STATUS STOP '+$LASTEXITCODE)}
}
function Run064Guarded([string]$mode) {
if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI064 illegal mode'}
SyncRelease $x64
Verify064GuardedSource
if($mode -ceq 'install'){
& py -3 (Join-Path $x64.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') preflight
}else{
& py -3 (Join-Path $x64.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') status
}
if($LASTEXITCODE -ne 0){throw ('BGXAI064 pre-authorization CHECK FAILED '+$LASTEXITCODE)}
$ztok=if($mode -ceq 'install'){'INSTALL_BGXAI_064'}else{'ROLLBACK_BGXAI_064'}
Write-Host '064: verified backup; Lua changes via WeiDU.'
Write-Host 'Close game/loader; BCS and EPS unchanged.'
$zcf=Read-Host ('Type '+$ztok+' exactly to authorize or ENTER to cancel')
if($zcf -cne $ztok){Write-Host '064 cancelled; game unchanged.';return}
& py -3 (Join-Path $x64.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') $mode '--yes' '--confirm' $ztok
if($LASTEXITCODE -ne 0){throw ('BGXAI064 '+$mode+' STOP code '+$LASTEXITCODE+'; do NOT retry blindly')}
Write-Host ('BGXAI064 '+$mode+' completed; check guarded read-only STATUS menu 75.')
}
function Verify066Source {
$spec=$x66
$checked=VM $spec
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath $name
ANR $dest
if((HashFile $dest) -cne $checked[$name].sha){throw ('BGXAI066 source SHA mismatch: '+$name)}
}
}
function Verify066SGuardedSource {
$spec=$x6s
$items=VM $spec
foreach($name in $spec.names){
$file=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
ANR $file
if((HashFile $file) -cne $items[$name].sha){throw ('BGXAI066S source SHA mismatch: '+$name)}
}
}
function Test066SReadOnly {
SyncRelease $x6s
Verify066SGuardedSource
Write-Host '066S native preflight READ ONLY.'
& py -3 (Join-Path $x6s.localPath 'BGXAI66S_INSTALL.py') preflight
if($LASTEXITCODE -ne 0){throw ('BGXAI066S REAL EET IDS preflight STOP '+$LASTEXITCODE)}
Write-Host 'BGXAI066S PRECHECK PASS. Existing 064 remains installed.'
}
function Status066SReadOnly {
SyncRelease $x6s
Verify066SGuardedSource
& py -3 (Join-Path $x6s.localPath 'BGXAI66S_INSTALL.py') status
if($LASTEXITCODE -ne 0){throw ('BGXAI066S status STOP '+$LASTEXITCODE)}
}
function Run066SGuarded([string]$mode) {
if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI066S unsupported mode'}
SyncRelease $x6s
Verify066SGuardedSource
$ztok=if($mode -ceq 'install'){'INSTALL_BGXAI_066S'}else{'ROLLBACK_BGXAI_066S'}
Write-Host '066S: pinned scripts, verified backup.'
Write-Host 'Close game/loader. No auto-retry.'
$zcf=Read-Host ('Type '+$ztok+' exactly to authorize, or ENTER to cancel')
if($zcf -cne $ztok){Write-Host '066S cancelled.';return}
& py -3 (Join-Path $x6s.localPath 'BGXAI66S_INSTALL.py') $mode '--yes' '--confirm' $ztok
if($LASTEXITCODE -ne 0){throw ('BGXAI066S '+$mode+' STOP '+$LASTEXITCODE+'. DO NOT AUTO-RETRY')}
Write-Host 'BGXAI066S action completed. Verify via menu 85.'
}

function Verify067GuardedSource {
$spec=$x67
$items=VM $spec
foreach($name in $spec.names){
$file=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
ANR $file
if((HashFile $file) -cne $items[$name].sha){throw ('BGXAI067 source SHA mismatch: '+$name)}
}
}
function Test067ReadOnly {
SyncRelease $x67
Verify067GuardedSource
Write-Host '067 prehit guard preflight READ ONLY.'
& py -3 (Join-Path $x67.localPath 'BGXAI67_INSTALL.py') preflight
if($LASTEXITCODE -ne 0){throw ('BGXAI067 REAL EET preflight STOP '+$LASTEXITCODE)}
Write-Host 'BGXAI067 PRECHECK PASS. Existing 066S remains installed.'
}
function Status067ReadOnly {
SyncRelease $x67
Verify067GuardedSource
& py -3 (Join-Path $x67.localPath 'BGXAI67_INSTALL.py') status
if($LASTEXITCODE -ne 0){throw ('BGXAI067 status STOP '+$LASTEXITCODE)}
}
function Run067Guarded([string]$mode) {
if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI067 unsupported mode'}
SyncRelease $x67
Verify067GuardedSource
$ztok=if($mode -ceq 'install'){'INSTALL_BGXAI_067'}else{'ROLLBACK_BGXAI_067'}
Write-Host 'BGXAI067 guarded Lua/BCS; 066S baseline required.'
Write-Host 'CLOSE BALDUR + INFINITYLOADER. No retry after a failure.'
$zcf=Read-Host ('Type '+$ztok+' exactly to authorize, or ENTER to cancel')
if($zcf -cne $ztok){Write-Host 'BGXAI067 CANCELLED. Game unchanged.';return}
& py -3 (Join-Path $x67.localPath 'BGXAI67_INSTALL.py') $mode '--yes' '--confirm' $ztok
if($LASTEXITCODE -ne 0){throw ('BGXAI067 '+$mode+' STOP '+$LASTEXITCODE+'. DO NOT AUTO-RETRY')}
Write-Host 'BGXAI067 action completed. Read-only status via menu 90.'
}


function VerifyIdleGuardSource {
$spec=$xidle
$items=VM $spec
foreach($name in $spec.names){
$file=Join-Path $spec.localPath $name
ANR $file
if((HashFile $file) -cne $items[$name].sha){throw ('BGXAI IDLE source SHA mismatch: '+$name)}
}
}
function CheckIdleGuardReadOnly([string]$mode) {
if($mode -cne 'preflight' -and $mode -cne 'status'){throw 'BGXAI IDLE read-only mode invalid'}
SyncRelease $xidle
VerifyIdleGuardSource
Write-Host ('BGXAI 066S idle guard '+$mode+': READ ONLY, no override/WeiDU changes.')
& py -3 (Join-Path $xidle.localPath 'BGXAI_IDLE_GUARD_INSTALL_SOURCE_ONLY.py') $mode '--game-root' $gr
if($LASTEXITCODE -ne 0){throw ('BGXAI IDLE '+$mode+' STOP '+$LASTEXITCODE)}
}
function RunIdleGuardGuarded([string]$mode) {
if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI IDLE guarded mode invalid'}
SyncRelease $xidle
VerifyIdleGuardSource
$zin=Join-Path $xidle.localPath 'BGXAI_IDLE_GUARD_INSTALL_SOURCE_ONLY.py'
$check=if($mode -ceq 'install'){'preflight'}else{'status'}
& py -3 $zin $check '--game-root' $gr
if($LASTEXITCODE -ne 0){throw ('BGXAI IDLE pre-authorization STOP '+$LASTEXITCODE)}
$ztok=if($mode -ceq 'install'){'INSTALL_BGXAI_IDLE_GUARD'}else{'ROLLBACK_BGXAI_IDLE_GUARD'}
Write-Host 'IDLE guard changes Lua only via WeiDU.'
Write-Host 'Close game/loader; backup+SHA required.'
$approval=Read-Host ('Type '+$ztok+' exactly to authorize, or press ENTER to cancel')
if($approval -cne $ztok){Write-Host 'BGXAI IDLE cancelled.';return}
& py -3 $zin $mode '--yes' '--confirm' $ztok '--game-root' $gr
if($LASTEXITCODE -ne 0){throw ('BGXAI IDLE '+$mode+' STOP '+$LASTEXITCODE+'. NO AUTOMATIC RETRY')}
Write-Host ('BGXAI IDLE '+$mode+' completed. Use menu 95 for status.')
}

function BGXAOEReadOnly {
SyncRelease $ao
$checked=VM $ao
foreach($name in $ao.names) {
$file=Join-Path $ao.localPath $name
ANR $file
if((HashFile $file) -cne $checked[$name].sha){throw ('AOE117 source SHA mismatch: '+$name)}
}
Write-Host 'AOE117 READ ONLY.'
& py -3 (Join-Path $ao.localPath $ao.installer) '--game' $gr
if($LASTEXITCODE -ne 0){throw ('AOE117 READ-ONLY STOP '+$LASTEXITCODE)}
Write-Host 'AOE117 report ready.'
}
function BGXTest6Safe {
SyncRelease $ao
$ztok='CREATE_BGXAI_TEST6_NO_PRIEST1'
Write-Host '118 NEW TEST SAVE ONLY; game unchanged.'
if((Read-Host ('Type '+$ztok+' to authorize, ENTER cancels')) -cne $ztok){Write-Host 'Cancelled';return}
& py -3 (Join-Path $ao.localPath 'BGXAI_TEST6_SAFE_COPY.py') --game-root $gr --yes --confirm $ztok
if($LASTEXITCODE -ne 0){throw ('BGXAI 118 SAFE COPY STOP '+$LASTEXITCODE)}
}
function BGXOneFileLastWeiDU {
$rows=@(Get-Content -LiteralPath (Join-Path $gr 'WeiDU.log') -ErrorAction Stop | Where-Object {$_.TrimStart().StartsWith('~')})
if($rows.Count -lt 1){throw 'No WeiDU components'}
return [string]$rows[-1]
}
function BOM($spec,[string]$mode,[string]$yesInstall,[string]$yesRollback){
if(@('status','preflight','install','rollback') -cnotcontains $mode){throw 'Invalid managed mode'}
SyncRelease $spec
$expected=VM $spec
foreach($name in $spec.names){
$file=Join-Path $spec.localPath $name
ANR $file
if((HashFile $file) -cne $expected[$name].sha){throw ('BGX source SHA invalid: '+$name)}
}
$zin=Join-Path $spec.localPath $spec.installer
$last=BGXOneFileLastWeiDU
$rx=if($spec.id -ceq 'BGXPR'){'BGXPRIEST[/\\]SETUP-BGXPRIEST[.]TP2~'}elseif($spec.id -ceq 'BGXP2'){'BGXP2[/\\]SETUP-BGXP2[.]TP2~'}elseif($spec.id -ceq 'BGXP3'){'BGXP3[/\\]SETUP-BGXP3[.]TP2~'}elseif($spec.id -ceq 'BGXP5'){'BGXP5[/\\]SETUP-BGXP5[.]TP2~'}else{'BGXTEAM[/\\]SETUP-BGXTEAM[.]TP2~'}
$installed=($last -match $rx)
if($spec.id -ceq 'BGXP3' -and $last -match 'BGXP5[/\\]SETUP-BGXP5[.]TP2~'){
if($mode -ceq 'status'){Write-Host 'BGXP3 below BGXP5; use 113.';return}
throw 'BGXP5 installed; rollback via 116 before BGXP3 change.'
}
if($spec.id -ceq 'BGXP2' -and $last -match 'BGXP3[/\\]SETUP-BGXP3[.]TP2~|BGXP5[/\\]SETUP-BGXP5[.]TP2~'){
if($mode -ceq 'status'){Write-Host 'BGXP2 below BGXP3; select 109.';return}
throw 'BGXP3 installed; rollback via 112 before changing BGXP2.'
}
if($spec.id -ceq 'BGXPR' -and $last -match 'BGXP2[/\\]SETUP-BGXP2[.]TP2~|BGXP3[/\\]SETUP-BGXP3[.]TP2~|BGXP5[/\\]SETUP-BGXP5[.]TP2~'){
if($mode -ceq 'status'){Write-Host 'BGXPR below BGXP2; select 105.';return}
throw 'BGXP2 installed; rollback via 108 before BGXPR change.'
}
if($spec.id -ceq 'BGXTEAM' -and ($last -match 'BGXPRIEST[/\\]SETUP-BGXPRIEST[.]TP2~' -or $last -match 'BGXP2[/\\]SETUP-BGXP2[.]TP2~' -or $last -match 'BGXP3[/\\]SETUP-BGXP3[.]TP2~' -or $last -match 'BGXP5[/\\]SETUP-BGXP5[.]TP2~')){
if($mode -ceq 'status'){Write-Host 'BGXTEAM under BGXPR; menu 97.';return}
throw 'BGXPR is last in WeiDU. Use menu 100 rollback first to change BGXTEAM.'
}
if($mode -ceq 'status' -or ($installed -and ($mode -ceq 'install' -or $mode -ceq 'preflight'))){
& py -3 $zin status '--game-root' $gr
if($LASTEXITCODE -ne 0){throw ('BGX status STOP '+$LASTEXITCODE)}
if($installed -and $mode -cne 'status'){Write-Host 'Already installed; no reinstall.'}
return
}
if($mode -ceq 'rollback' -and !$installed){throw ('BGX '+$spec.id+' not last in WeiDU; rollback blocked')}
$pre=if($mode -ceq 'rollback'){'status'}else{'preflight'}
& py -3 $zin $pre '--game-root' $gr
if($LASTEXITCODE -ne 0){throw ('BGX '+$spec.id+' '+$pre+' STOP '+$LASTEXITCODE)}
if($mode -ceq 'preflight'){Write-Host 'Preflight PASS; no game change.';return}
$ztok=if($mode -ceq 'install'){$yesInstall}else{$yesRollback}
Write-Host 'Close game/loader/WeiDU. Backup required.'
$reply=Read-Host ('Type '+$ztok+' exactly to authorize, or ENTER to cancel')
if($reply -cne $ztok){Write-Host 'Cancelled; game unchanged.';return}
& py -3 $zin $mode '--yes' '--confirm' $ztok '--game-root' $gr
if($LASTEXITCODE -ne 0){throw ('BGX '+$spec.id+' '+$mode+' STOP '+$LASTEXITCODE+'. NO AUTOMATIC RETRY')}
Write-Host ('BGX '+$spec.id+' '+$mode+' finished, verified.')
}
function Test066GuardedReadOnly {
$parsedTokens=$null
$zpe=$null
[System.Management.Automation.Language.Parser]::ParseFile($PSCommandPath,[ref]$parsedTokens,[ref]$zpe) | Out-Null
if($zpe.Count -gt 0){throw ('BGXAI066 parser STOP: '+(($zpe | ForEach-Object {$_.Message}) -join '; '))}
SyncRelease $x66
Verify066Source
Write-Host '066 preflight READ ONLY.'
& py -3 (Join-Path $x66.localPath 'BGXAI66_INSTALL.py') preflight
if($LASTEXITCODE -ne 0){throw ('BGXAI066 preflight STOP '+$LASTEXITCODE)}
Write-Host '066 preflight PASS. 064 unchanged.'
}
function Status066GuardedReadOnly {
SyncRelease $x66
Verify066Source
& py -3 (Join-Path $x66.localPath 'BGXAI66_INSTALL.py') status
if($LASTEXITCODE -ne 0){throw ('BGXAI066 status STOP '+$LASTEXITCODE)}
}
function Run066Guarded([string]$mode) {
if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI066 illegal mode'}
SyncRelease $x66
Verify066Source
if($mode -ceq 'install'){
& py -3 (Join-Path $x66.localPath 'BGXAI66_INSTALL.py') preflight
}else{
& py -3 (Join-Path $x66.localPath 'BGXAI66_INSTALL.py') status
}
if($LASTEXITCODE -ne 0){throw ('BGXAI066 pre-authorization STOP '+$LASTEXITCODE)}
$ztok=if($mode -ceq 'install'){'INSTALL_BGXAI_066'}else{'ROLLBACK_BGXAI_066'}
Write-Host '066 updates M_BX43 with verified backup.'
Write-Host 'Close game/loader/WeiDU; exact baseline needed.'
$zcf=Read-Host ('Type '+$ztok+' exactly to authorize or ENTER to cancel')
if($zcf -cne $ztok){Write-Host '066 cancelled.';return}
& py -3 (Join-Path $x66.localPath 'BGXAI66_INSTALL.py') $mode '--yes' '--confirm' $ztok
if($LASTEXITCODE -ne 0){throw ('BGXAI066 '+$mode+' STOP '+$LASTEXITCODE+'; do NOT retry automatically')}
Write-Host 'BGXAI066 action complete. Check status with option 80.'
}
function Test064ReadOnly {
$parsedTokens=$null
$zpe=$null
[System.Management.Automation.Language.Parser]::ParseFile($PSCommandPath,[ref]$parsedTokens,[ref]$zpe) | Out-Null
if($zpe.Count -gt 0){throw ('BGXAI064 PowerShell parser STOP: '+(($zpe | ForEach-Object {$_.Message}) -join '; '))}
$spec=$release064
$list=VM $spec
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath $name
ANR $dest
if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI064 source SHA mismatch: '+$name)}
}
Write-Host '064 SHA-checked 061 status; read only.'
& py -3 (Join-Path $spec.localPath 'BGXAI64_PREFLIGHT_READONLY.py') '--game-root' $gr
if($LASTEXITCODE -ne 0){throw ('BGXAI064 read-only preflight STOP: '+$LASTEXITCODE)}
Write-Host '064 preflight PASS; not installed; runtime unverified.'
}
function Status061ReadOnly {
$log=Join-Path $gr 'WeiDU.log'
$bcs=Join-Path $gr 'override\BDDEFAI.BCS'
$lua=Join-Path $gr 'override\M_BX43.lua'
ANR $log
ANR $bcs
ANR $lua
if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
$rows=@(Get-Content -LiteralPath $log -ErrorAction Stop | Where-Object {$_.TrimStart().StartsWith('~')})
if($rows.Count -lt 1){throw 'WeiDU.log has no installed components'}
$last=[string]$rows[-1]
$is061=($last -match '(?i)BGX61[/\\]SETUP-BGX61[.]TP2~')
$is060=($last -match '(?i)BGX60[/\\]SETUP-BGX60[.]TP2~')
$bhash=HashFile $bcs
$lhash=HashFile $lua
Write-Host ('Last WeiDU: '+$last)
Write-Host ('061 is LAST: '+$is061)
Write-Host ('060 is LAST: '+$is060)
if($is061){
$sourceBCS=Join-Path $gr 'BGX61\staged\BDDEFAI.BCS'
$sourceLua=Join-Path $gr 'BGX61\staged\M_BX43.lua'
ANR $sourceBCS
ANR $sourceLua
Write-Host ('061 BCS staged SHA matches live: '+((HashFile $sourceBCS) -ceq $bhash -and $bhash.Length -eq 64))
Write-Host ('061 Lua staged SHA matches live: '+((HashFile $sourceLua) -ceq $lhash -and $lhash.Length -eq 64))
} elseif($is060) {
Write-Host ('060 BCS SHA correct: '+($bhash -ceq '038b41c529fb45bb75528722577beef7b474e1ce55e280dc5fca4d6ed9e72841'))
Write-Host ('060 Lua SHA correct: '+($lhash -ceq '35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab'))
} else {Write-Host 'STOP: last WeiDU is not BGX60/BGX61.'}
Write-Host ('Live BCS SHA: '+$bhash)
Write-Host ('Live Lua SHA: '+$lhash)
}
function Test060ReadOnly {
$spec=$b60
$list=VM $spec
foreach($name in $spec.names){
$dest=Join-Path $spec.localPath $name
ANR $dest
if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI060 unverified file: '+$name)}
}
Write-Host 'BGXAI 060 - READ-ONLY Windows WeiDU compile (NO INSTALL).'
& py -3 (Join-Path $spec.localPath 'BGXAI60_INSTALL.py') preflight
if($LASTEXITCODE -ne 0){throw ('BGXAI 060 preflight failed: exit '+$LASTEXITCODE)}
Write-Host 'BGXAI 060 - preflight PASSED; installed 056 unchanged.'
}
function Test041ReadOnly {
Write-Host ''
Write-Host '041 precheck (RO)'
$logPath=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $logPath -PathType Leaf)){throw 'WeiDU.log missing'}
$zln=@(Get-Content -LiteralPath $logPath -ErrorAction Stop)
$zact=@($zln | Where-Object { $_.TrimStart().StartsWith('~') })
$has039=@($zact | Where-Object { $_ -match 'BGX39[^~]*[.]TP2~' }).Count -gt 0
$has040=@($zact | Where-Object { $_ -match 'BGX40[^~]*[.]TP2~' }).Count -gt 0
$has041=@($zact | Where-Object { $_ -match 'BGX41[^~]*[.]TP2~' }).Count -gt 0
$is040Last=$zact.Count -gt 0 -and $zact[-1] -match 'BGX40[^~]*[.]TP2~'
$eps=@($zact | Where-Object { $_.ToUpperInvariant().Contains('ENHANCED-POWERGAMING-SCRIPTS') }).Count -gt 0
Write-Host ('EPS in WeiDU.log: '+$eps)
Write-Host ('BGX39 in WeiDU.log: '+$has039)
Write-Host ('BGX40 in WeiDU.log: '+$has040)
Write-Host ('BGX41 in WeiDU.log: '+$has041)
Write-Host ('BGX40 is LAST installed WeiDU mod: '+$is040Last)
$stat=Join-Path $gr 'override\STATDESC.2DA'
Write-Host ('STATDESC.2DA in override: '+(Test-Path -LiteralPath $stat -PathType Leaf))
Write-Host 'NOTE: STATDESC may exist in game archives even when not in override.'
$bcs=Join-Path $gr 'override\BDDEFAI.BCS'
Write-Host ('EPS script in override: '+(Test-Path -LiteralPath $bcs -PathType Leaf))
$toolsOk=(Test-Path -LiteralPath (Join-Path $gr 'setup-enhanced-powergaming-scripts.exe') -PathType Leaf)
Write-Host ('WeiDU executable available: '+$toolsOk)
if($eps -and $has039 -and $has040 -and !$has041 -and $is040Last -and $toolsOk -and (Test-Path -LiteralPath $bcs -PathType Leaf)) {
Write-Host '041 read-only PASS; icon compilation unproven.'
} else {
Write-Host '041 precheck: REVIEW before install.'
}
Write-Host 'NO GAME WRITE.'
}
function Test042EPSReadOnly {
Write-Host ''
Write-Host 'BGXAI 042 - EPS GUARD / AUTOATTACK AUDIT (READ ONLY)'
$fileName=Join-Path $gr 'override\BDDEFAI.BCS'
if(!(Test-Path -LiteralPath $fileName -PathType Leaf)){throw 'Current BDDEFAI.BCS missing'}
$bytes=[IO.File]::ReadAllBytes($fileName)
if($bytes.Length -gt 8000000 -or $bytes.Length -lt 50){throw 'Unexpected compiled BCS size'}
$bcs=[Text.Encoding]::GetEncoding(28591).GetString($bytes)
if(!$bcs.StartsWith(('SC'+[char]10))){throw 'Unexpected compiled BCS signature'}
$blockPattern=[regex]'(?s)CR\nCO\n(.*?)\nRS\n(.*?)\nRS\nCR(?=\n(?:CR|SC))'
$blocks=$blockPattern.Matches($bcs)
if($blocks.Count -lt 1){throw 'Unable to recognize complete BCS blocks'}
$modeCount=0;$guardCount=0;$modeActionList=0;$protectCount=0
$attackReeval=0;$attackOneRound=0
$interesting=@()
for($i=0;$i -lt $blocks.Count;$i++){
$condition=$blocks[$i].Groups[1].Value
$actions=$blocks[$i].Groups[2].Value
$isMode=$condition.Contains('BDAI_ATTACK_MODE')
$isGuard=$condition.Contains('BGX38_GUARD')
if($isMode){$modeCount++}
if($isGuard){$guardCount++}
if($isMode -and $condition.Contains('16427 ')){$modeActionList++}
$actionIds=@([regex]::Matches($actions,'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n') | ForEach-Object {$_.Groups[1].Value})
$protectCount+=@($actionIds | Where-Object {$_ -eq '87'}).Count
$attackReeval+=@($actionIds | Where-Object {$_ -eq '134'}).Count
$attackOneRound+=@($actionIds | Where-Object {$_ -eq '105'}).Count
if(($isMode -or $isGuard) -and $interesting.Count -lt 12){
$interesting+=('  Block '+($i+1)+': mode='+$isMode+' guard='+$isGuard+
' idle='+$condition.Contains('16427 ')+' actions='+($actionIds -join ','))
}
}
Write-Host ('Live BDDEFAI.BCS SHA256: '+(HashBytes $bytes))
Write-Host ('Bytes: '+$bytes.Length+'; complete blocks: '+$blocks.Count)
Write-Host ('EPS attack-mode blocks: '+$modeCount+' (ActionListEmpty: '+$modeActionList+')')
Write-Host ('BGXAI guard-mode blocks: '+$guardCount)
Write-Host ('Actions: ProtectObject='+$protectCount+' AttackReevaluate='+$attackReeval+' AttackOneRound='+$attackOneRound)
foreach($item in $interesting){Write-Host $item}
Write-Host 'Only live game sources; READ ONLY.'
Write-Host '042 audit only; no game files changed by this option.'
}
function Test042BReadOnly {
Write-Host ''
Write-Host 'BGXAI 042B - LIVE EET READ-ONLY PREFLIGHT'
$log=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
$zact=@(Get-Content -LiteralPath $log | Where-Object { $_.TrimStart().StartsWith('~') })
$has41=@($zact | Where-Object { $_ -match 'BGX41[^~]*[.]TP2~' }).Count -gt 0
$has42=@($zact | Where-Object { $_ -match 'BGX42[^~]*[.]TP2~' }).Count -gt 0
$last41=$zact.Count -gt 0 -and $zact[-1] -match 'BGX41[^~]*[.]TP2~'
$last42=$zact.Count -gt 0 -and $zact[-1] -match 'BGX42[^~]*[.]TP2~'
$eps=@($zact | Where-Object { $_.ToUpperInvariant().Contains('ENHANCED-POWERGAMING-SCRIPTS') }).Count -gt 0
$bcs=Join-Path $gr 'override\BDDEFAI.BCS'
if(!(Test-Path -LiteralPath $bcs -PathType Leaf)){throw 'BDDEFAI.BCS missing'}
$hash=HashFile $bcs
$orig='86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5'
$patched='8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
$weidu=Test-Path -LiteralPath (Join-Path $gr 'setup-enhanced-powergaming-scripts.exe') -PathType Leaf
Write-Host ('EPS installed: '+$eps+'; WeiDU available: '+$weidu)
Write-Host ('BGX41 present: '+$has41+'; 041 last: '+$last41)
Write-Host ('BGX42 present: '+$has42+'; 042 last: '+$last42)
Write-Host ('Live BCS SHA256: '+$hash)
if($eps -and $weidu -and $has41 -and !$has42 -and $last41 -and $hash -ceq $orig) {
Write-Host 'BGXAI 042B PRECHECK: BASELINE OK. NOT INSTALLED.'
} elseif($eps -and $has42 -and $last42 -and $hash -ceq $patched) {
Write-Host '042B patch present; status 16.'
} else {
Write-Host '042B REVIEW before install.'
}
Write-Host 'NO GAME WRITE.'
}
function Test043PReadOnly {
Write-Host ''
Write-Host '043P EEex observer precheck (RO)'
$logPath=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $logPath -PathType Leaf)){throw 'WeiDU.log missing'}
$zact=@(Get-Content -LiteralPath $logPath | Where-Object { $_.TrimStart().StartsWith('~') })
$has42=@($zact | Where-Object { $_ -match 'BGX42[^~]*[.]TP2~' }).Count -gt 0
$has43=@($zact | Where-Object { $_ -match 'BGX43[^~]*[.]TP2~' }).Count -gt 0
$last42=$zact.Count -gt 0 -and $zact[-1] -match 'BGX42[^~]*[.]TP2~'
$last43=$zact.Count -gt 0 -and $zact[-1] -match 'BGX43[^~]*[.]TP2~'
$bcs=Join-Path $gr 'override\BDDEFAI.BCS'
if(!(Test-Path -LiteralPath $bcs -PathType Leaf)){throw 'BDDEFAI.BCS missing'}
$bcsSha=HashFile $bcs
$expect='8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
$eeex=Test-Path -LiteralPath (Join-Path $gr 'override\M___EEex.lua') -PathType Leaf
$loader=Test-Path -LiteralPath (Join-Path $gr 'InfinityLoader.exe') -PathType Leaf
$lua=Test-Path -LiteralPath (Join-Path $gr 'override\M_BGX43Probe.lua') -PathType Leaf
Write-Host ('BGX42 installed: '+$has42+'; 042 last: '+$last42)
Write-Host ('BGX43 installed: '+$has43+'; 043 last: '+$last43)
Write-Host ('EEex M___EEex.lua present: '+$eeex+'; InfinityLoader present: '+$loader)
Write-Host ('Probe Lua in override: '+$lua)
Write-Host ('BGX42 BCS SHA256: '+$bcsSha)
if($has42 -and !$has43 -and $last42 -and !$lua -and $eeex -and $loader -and $bcsSha -ceq $expect){
Write-Host 'BGXAI 043P PRECHECK: BASELINE OK. NOT INSTALLED.'
} elseif($has43 -and $last43 -and $lua -and $bcsSha -ceq $expect){
Write-Host '043P probe present; status 21.'
} else {
Write-Host '043P REVIEW before install.'
}
Write-Host 'NO GAME WRITE.'
}
function Test044ReadOnly {
Write-Host ''
Write-Host '044 hotkey precheck (RO)'
$log=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
$zln=@(Get-Content -LiteralPath $log | Where-Object { $_.TrimStart().StartsWith('~') })
$has42=@($zln | Where-Object { $_ -match 'BGX42[^~]*[.]TP2~' }).Count -gt 0
$has43=@($zln | Where-Object { $_ -match 'BGX43[^~]*[.]TP2~' }).Count -gt 0
$has44=@($zln | Where-Object { $_ -match 'BGX44[^~]*[.]TP2~' }).Count -gt 0
$last43=$zln.Count -gt 0 -and $zln[-1] -match 'BGX43[^~]*[.]TP2~'
$last44=$zln.Count -gt 0 -and $zln[-1] -match 'BGX44[^~]*[.]TP2~'
$bcs=HashFile (Join-Path $gr 'override\BDDEFAI.BCS')
$obs=HashFile (Join-Path $gr 'override\M_BGX43Probe.lua')
$goodBCS=$bcs -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
$goodObs=$obs -ceq 'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'
$loader=Test-Path -LiteralPath (Join-Path $gr 'InfinityLoader.exe') -PathType Leaf
$eeex=Test-Path -LiteralPath (Join-Path $gr 'override\M___EEex.lua') -PathType Leaf
$diag=Test-Path -LiteralPath (Join-Path $gr 'override\M_BGX44Diag.lua') -PathType Leaf
Write-Host ('042B installed='+$has42+'; 043P installed='+$has43+'; 043P last='+$last43)
Write-Host ('044 installed='+$has44+'; 044 last='+$last44+'; 044 lua exists='+$diag)
Write-Host ('042B exact BCS hash='+$goodBCS+'; 043P exact Lua hash='+$goodObs)
Write-Host ('EEex boot='+$eeex+'; InfinityLoader='+$loader)
if($has42 -and $has43 -and $last43 -and !$has44 -and !$diag -and
$goodBCS -and $goodObs -and $eeex -and $loader) {
Write-Host 'BGXAI 044 PREFLIGHT: BASELINE OK. NOT INSTALLED.'
} elseif($has44 -and $last44 -and $diag -and $goodBCS -and $goodObs) {
Write-Host '044 installed; status 26.'
} else {
Write-Host '044 REVIEW before install.'
}
Write-Host 'NO GAME WRITE.'
}
function Test045ReadOnly {
Write-Host ''
Write-Host '045 Lua RESREF preflight (RO)'
$log=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
$zln=@(Get-Content -LiteralPath $log | Where-Object { $_.TrimStart().StartsWith('~') })
$has42=@($zln | Where-Object { $_ -match 'BGX42[^~]*[.]TP2~' }).Count -gt 0
$has43=@($zln | Where-Object { $_ -match 'BGX43[^~]*[.]TP2~' }).Count -gt 0
$has44=@($zln | Where-Object { $_ -match 'BGX44[^~]*[.]TP2~' }).Count -gt 0
$has45=@($zln | Where-Object { $_ -match 'BGX45[^~]*[.]TP2~' }).Count -gt 0
$last44=$zln.Count -gt 0 -and $zln[-1] -match 'BGX44[^~]*[.]TP2~'
$last45=$zln.Count -gt 0 -and $zln[-1] -match 'BGX45[^~]*[.]TP2~'
$base42=(HashFile (Join-Path $gr 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
$base43=(HashFile (Join-Path $gr 'override\M_BGX43Probe.lua')) -ceq 'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'
$base44=(HashFile (Join-Path $gr 'override\M_BGX44Diag.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
$short43=Test-Path -LiteralPath (Join-Path $gr 'override\M_BX43.lua') -PathType Leaf
$short44=Test-Path -LiteralPath (Join-Path $gr 'override\M_BX44.lua') -PathType Leaf
$boot=Test-Path -LiteralPath (Join-Path $gr 'override\M___EEex.lua') -PathType Leaf
$loader=Test-Path -LiteralPath (Join-Path $gr 'InfinityLoader.exe') -PathType Leaf
Write-Host ('042B/043P/044 installed: '+$has42+'/'+$has43+'/'+$has44)
Write-Host ('044 last: '+$last44+'; 045 installed: '+$has45+'; 045 last: '+$last45)
Write-Host ('Original 042B/043P/044 SHA256 match: '+$base42+'/'+$base43+'/'+$base44)
Write-Host ('Short Lua files exist: '+$short43+'/'+$short44)
Write-Host ('EEex boot='+$boot+'; InfinityLoader='+$loader)
if($has42 -and $has43 -and $has44 -and $last44 -and !$has45 -and
!$short43 -and !$short44 -and $base42 -and $base43 -and $base44 -and $boot -and $loader){
Write-Host 'BGXAI 045 PRECHECK: BASELINE OK. NOT INSTALLED.'
} elseif($has45 -and $last45 -and $short43 -and $short44 -and $base42 -and $base43 -and $base44) {
Write-Host '045 probe present; status 31.'
} else {
Write-Host '045 REVIEW before install.'
}
Write-Host 'NO GAME WRITE.'
}
function Test046ReadOnly {
Write-Host ''
Write-Host 'BGXAI 046 ATTACK FILTER - PRECHECK (READ ONLY)'
$p=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'WeiDU.log missing'}
$e=@(Get-Content -LiteralPath $p | Where-Object { $_.TrimStart().StartsWith('~') })
$last45=$e.Count -gt 0 -and $e[-1] -match 'BGX45[^~]*[.]TP2~'
$last46=$e.Count -gt 0 -and $e[-1] -match 'BGX46[^~]*[.]TP2~'
$present46=@($e | Where-Object { $_ -match 'BGX46[^~]*[.]TP2~' }).Count -gt 0
$old='f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'
$old45=(HashFile (Join-Path $gr 'override\M_BX43.lua')) -ceq $old
$bcs=(HashFile (Join-Path $gr 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
$other=(HashFile (Join-Path $gr 'override\M_BX44.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
Write-Host ('045 last='+$last45+'; 046 present='+$present46+'; 046 last='+$last46)
Write-Host ('045 observer original='+$old45+'; 042B BCS='+$bcs+'; 044 short Lua='+$other)
if($last45 -and !$present46 -and $old45 -and $bcs -and $other){
Write-Host 'BGXAI 046 PRECHECK: BASELINE OK. NOT INSTALLED.'
} elseif($last46 -and $bcs -and $other) {
Write-Host '046 present; status 36.'
} else {
Write-Host 'BGXAI 046 PRECHECK: REVIEW. DO NOT INSTALL.'
}
Write-Host 'NO GAME WRITE.'
}
function Test047ReadOnly {
Write-Host ''
Write-Host '047 target precheck (RO)'
$p=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'WeiDU.log missing'}
$e=@(Get-Content -LiteralPath $p | Where-Object { $_.TrimStart().StartsWith('~') })
$last46=$e.Count -gt 0 -and $e[-1] -match 'BGX46[^~]*[.]TP2~'
$last47=$e.Count -gt 0 -and $e[-1] -match 'BGX47[^~]*[.]TP2~'
$present47=@($e | Where-Object { $_ -match 'BGX47[^~]*[.]TP2~' }).Count -gt 0
$old46=(HashFile (Join-Path $gr 'override\M_BX43.lua')) -ceq '1c1e314e1f14a693fa0b10d7450e737447a992e9d7900fb7112437f75c26a6a3'
$bcs=(HashFile (Join-Path $gr 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
$diag=(HashFile (Join-Path $gr 'override\M_BX44.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
Write-Host ('046 last='+$last46+'; 047 installed='+$present47+'; 047 last='+$last47)
Write-Host ('046 Lua='+$old46+'; 042B BCS='+$bcs+'; 044 Lua='+$diag)
if($last46 -and !$present47 -and $old46 -and $bcs -and $diag){
Write-Host 'BGXAI 047 PRECHECK: BASELINE OK. NOT INSTALLED.'
} elseif($last47 -and $bcs -and $diag) {
Write-Host 'BGXAI 047 PRECHECK: PRESENT. Use 41 for checksum status.'
} else {Write-Host '047 REVIEW before install.'}
Write-Host 'NO GAME WRITE.'
}
function Test048ReadOnly {
Write-Host ''
Write-Host '048 hit observer precheck (RO)'
$p=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'WeiDU.log missing'}
$e=@(Get-Content -LiteralPath $p | Where-Object { $_.TrimStart().StartsWith('~') })
$last47=$e.Count -gt 0 -and $e[-1] -match 'BGX47[^~]*[.]TP2~'
$last48=$e.Count -gt 0 -and $e[-1] -match 'BGX48[^~]*[.]TP2~'
$present48=@($e | Where-Object { $_ -match 'BGX48[^~]*[.]TP2~' }).Count -gt 0
$old47=(HashFile (Join-Path $gr 'override\M_BX43.lua')) -ceq 'c5b72a9bd22e120b38aa0d4f82fc9ce3532c31c8676e52cfdc855ee39521ddfd'
$bcs=(HashFile (Join-Path $gr 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
$diag=(HashFile (Join-Path $gr 'override\M_BX44.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
Write-Host ('047 last='+$last47+'; 048 installed='+$present48+'; 048 last='+$last48)
Write-Host ('047 Lua='+$old47+'; 042B BCS unchanged='+$bcs+'; 044 Lua unchanged='+$diag)
if($last47 -and !$present48 -and $old47 -and $bcs -and $diag) {
Write-Host 'BGXAI 048 PRECHECK: BASELINE OK. NOT INSTALLED.'
} elseif($last48 -and $bcs -and $diag) {
Write-Host '048 present; status 46.'
} else { Write-Host '048 REVIEW before install.' }
Write-Host 'NO GAME WRITE.'
}
function Test049ReadOnly {
Write-Host ''
Write-Host 'BGXAI 049 GUARD ADVISORY PRECHECK (READ ONLY)'
$p=Join-Path $gr 'WeiDU.log'
if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'WeiDU.log missing'}
$e=@(Get-Content -LiteralPath $p | Where-Object { $_.TrimStart().StartsWith('~') })
$last48=$e.Count -gt 0 -and $e[-1] -match 'BGX48[^~]*[.]TP2~'
$last49=$e.Count -gt 0 -and $e[-1] -match 'BGX49[^~]*[.]TP2~'
$present49=@($e | Where-Object { $_ -match 'BGX49[^~]*[.]TP2~' }).Count -gt 0
$old48=(HashFile (Join-Path $gr 'override\M_BX43.lua')) -ceq '7b7b613c736df4d7d8a360e9879486bfe26ca52b7f29242c64ab6b2a27c694ea'
$bcs=(HashFile (Join-Path $gr 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
$diag=(HashFile (Join-Path $gr 'override\M_BX44.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
Write-Host ('048 last='+$last48+'; 049 present='+$present49+'; 049 last='+$last49)
Write-Host ('048 Lua='+$old48+'; 042B BCS unchanged='+$bcs+'; 044 Lua unchanged='+$diag)
if($last48 -and !$present49 -and $old48 -and $bcs -and $diag) {
Write-Host 'BGXAI 049 PRECHECK: BASELINE OK. NOT INSTALLED.'
} elseif($last49 -and $bcs -and $diag) {
Write-Host '049 present; status 51.'
} else {Write-Host '049 REVIEW before install.'}
Write-Host 'NO GAME WRITE.'
}
Write-Host ''
Write-Host @'
 BGXAI ONE-FILE UPDATER / EET Foxx / EPS 18.4
 EPS 18.4 / EET. BGXPR status: 97.
 1-4  040 download/status/install/rollback
 5-6  039 status/rollback
 7-11 041 precheck/download/status/install/rollback
 12-17 042 precheck/preflight/download/install/status/rollback
 18-22 043P precheck/source/install/status/rollback
 23-27 044 precheck/source/install/status/rollback
 28-32 045 precheck/source/install/status/rollback
 33-37 046 precheck/source/install/status/rollback
 38-42 047 precheck/source/install/status/rollback
 43-47 048 precheck/source/install/status/rollback
 48-52 049 precheck/source/install/status/rollback
 53-54 054 download/compile
 55-59 056 precheck/source/install/status/rollback
 60-64 060 source/precheck/install/status/rollback
 65-69 061 source/precheck/install/status/rollback
'@
70..92 | ForEach-Object { Write-Host ('{0,3} - BGX' -f $_) }
echo ' 93 - 066S precheck'
echo ' 94 - 066S install'
echo ' 95 - 066S status'
echo ' 96 - 066S rollback'
97..116 | ForEach-Object { Write-Host ('{0,3} - BGX' -f $_) }
117..122 | ForEach-Object { Write-Host ('{0} - AOE' -f $_) }
123..130 | ForEach-Object { Write-Host ('{0} - RANGE' -f $_) }
$bgx131='V3 RO|V3 I|V3 S|V3 RB|Aggro RO|SAFE I|SAFE S|SAFE RB|FR I|FR S|FR RB|Trace I|Trace S|Trace RB|V2 I|Game+log|V2 S|V2 RB|Motion I|Motion S|Motion RB' -split '\|';131..151 | ForEach-Object { Write-Host ('{0} - {1}' -f $_,$bgx131[$_-131]) }
Write-Host @'
152 - Enemy guard native preflight (RO)
153 - Enemy guard install+verify
154 - Enemy guard status (RO)
155 - Enemy guard rollback
156 - V5 old ranged pilot
157 - V6 old DPLAYER pilot
158 - Weapon V3 native preflight READ ONLY
159 - EEex R1 observer
160 - EEex R11 static RO
161 - R13 target pilot RO
162 - R13 Lua name fix RO
163 - R13.2 diagnostics RO
164 - Installed EEex R19 static audit (READ ONLY)
165 - R27 observer (guarded)
166 - V7 DPLAYER close-fire fix (guarded)
167 - Weapon V3 native BAF compile (READ ONLY)
168 - AUTO batch weapon READ ONLY
169 - R29 bow-to-sword native pilot (guarded)
 0 - Exit [default]
'@
$choice=Read-Host 'Choice [0]'
if([string]::IsNullOrWhiteSpace($choice)){$choice='0'}
if($choice -eq '0'){Write-Host 'No changes.';exit 0}
try {
switch($choice){
'1' {SyncRelease $b40;break}
'2' {RR $b40 '--status';break}
'3' {SyncRelease $b40;RR $b40 '--install';break}
'4' {RR $b40 '--uninstall';break}
'5' {RR $release039 '--status';break}
'6' {RR $release039 '--uninstall';break}
'7' {Test041ReadOnly;break}
'8' {SyncRelease $b41;break}
'9' {RR $b41 '--status';break}
'10' {SyncRelease $b41;RR $b41 '--install';break}
'11' {RR $b41 '--uninstall';break}
'12' {Test042EPSReadOnly;break}
'13' {Test042BReadOnly;break}
'14' {SyncRelease $b42;break}
'15' {SyncRelease $b42;RR $b42 '--install';break}
'16' {RR $b42 '--status';break}
'17' {SyncRelease $b42;RR $b42 '--uninstall';break}
'18' {Test043PReadOnly;break}
'19' {SyncRelease $x43;break}
'20' {SyncRelease $x43;RR $x43 '--install';break}
'21' {RR $x43 '--status';break}
'22' {SyncRelease $x43;RR $x43 '--uninstall';break}
'23' {Test044ReadOnly;break}
'24' {SyncRelease $t44;break}
'25' {SyncRelease $t44;RR $t44 '--install';break}
'26' {RR $t44 '--status';break}
'27' {SyncRelease $t44;RR $t44 '--uninstall';break}
'28' {Test045ReadOnly;break}
'29' {SyncRelease $t45;break}
'30' {SyncRelease $t45;RR $t45 '--install';break}
'31' {RR $t45 '--status';break}
'32' {SyncRelease $t45;RR $t45 '--uninstall';break}
'33' {Test046ReadOnly;break}
'34' {SyncRelease $t46;break}
'35' {SyncRelease $t46;RR $t46 '--install';break}
'36' {RR $t46 '--status';break}
'37' {SyncRelease $t46;RR $t46 '--uninstall';break}
'38' {Test047ReadOnly;break}
'39' {SyncRelease $t47;break}
'40' {SyncRelease $t47;RR $t47 '--install';break}
'41' {RR $t47 '--status';break}
'42' {SyncRelease $t47;RR $t47 '--uninstall';break}
'43' {Test048ReadOnly;break}
'44' {SyncRelease $t48;break}
'45' {SyncRelease $t48;RR $t48 '--install';break}
'46' {RR $t48 '--status';break}
'47' {SyncRelease $t48;RR $t48 '--uninstall';break}
'48' {Test049ReadOnly;break}
'49' {SyncRelease $t49;break}
'50' {SyncRelease $t49;RR $t49 '--install';break}
'51' {RR $t49 '--status';break}
'52' {SyncRelease $t49;RR $t49 '--uninstall';break}
'53' {SyncRelease $release054;break}
'54' {SyncRelease $release054;RR $release054 '--compile-readonly';break}
'55' {SyncRelease $x56;RR $x56 '--precheck';break}
'56' {SyncRelease $x56;break}
'57' {SyncRelease $x56;RR $x56 '--install';break}
'58' {RR $x56 '--status';break}
'59' {SyncRelease $x56;RR $x56 '--uninstall';break}
'60' {SyncRelease $b60;break}
'61' {SyncRelease $b60;Test060ReadOnly;break}
'62' {Run060Guarded 'install';break}
'63' {Status060ReadOnly;break}
'64' {Run060Guarded 'rollback';break}
'65' {SyncRelease $x61;break}
'66' {SyncRelease $x61;Test061ReadOnly;break}
'67' {Run061Guarded 'install';break}
'68' {Status061ReadOnly;break}
'69' {Run061Guarded 'rollback';break}
'70' {SyncRelease $release064;break}
'71' {SyncRelease $release064;Test064ReadOnly;break}
'72' {SyncRelease $x64;break}
'73' {Test064GuardedReadOnly;break}
'74' {Run064Guarded 'install';break}
'75' {Status064GuardedReadOnly;break}
'76' {Run064Guarded 'rollback';break}
'77' {SyncRelease $x66;break}
'78' {Test066GuardedReadOnly;break}
'79' {throw 'BGXAI 066 deprecated: frontline-only regression; use tested BGXAI066S 83/84 instead.'}
'80' {Status066GuardedReadOnly;break}
'81' {Run066Guarded 'rollback';break}
'82' {SyncRelease $x6s;break}
'83' {Test066SReadOnly;break}
'84' {Run066SGuarded 'install';break}
'85' {Status066SReadOnly;break}
'86' {Run066SGuarded 'rollback';break}
'87' {SyncRelease $x67;break}
'88' {Test067ReadOnly;break}
'89' {Run067Guarded 'install';break}
'90' {Status067ReadOnly;break}
'91' {Run067Guarded 'rollback';break}
'92' {SyncRelease $xidle;break}
'93' {CheckIdleGuardReadOnly 'preflight';break}
'94' {RunIdleGuardGuarded 'install';break}
'95' {CheckIdleGuardReadOnly 'status';break}
'96' {RunIdleGuardGuarded 'rollback';break}
'97' {BOM $xpr 'status' 'INSTALL_BGXPRIEST_MODES' 'ROLLBACK_BGXPRIEST_MODES';break}
'98' {BOM $xpr 'preflight' 'INSTALL_BGXPRIEST_MODES' 'ROLLBACK_BGXPRIEST_MODES';break}
'99' {BOM $xpr 'install' 'INSTALL_BGXPRIEST_MODES' 'ROLLBACK_BGXPRIEST_MODES';break}
'100' {BOM $xpr 'rollback' 'INSTALL_BGXPRIEST_MODES' 'ROLLBACK_BGXPRIEST_MODES';break}
'101' {BOM $xteam 'status' 'INSTALL_BGXAI_TEAM_GUARD' 'ROLLBACK_BGXAI_TEAM_GUARD';break}
'102' {BOM $xteam 'preflight' 'INSTALL_BGXAI_TEAM_GUARD' 'ROLLBACK_BGXAI_TEAM_GUARD';break}
'103' {BOM $xteam 'install' 'INSTALL_BGXAI_TEAM_GUARD' 'ROLLBACK_BGXAI_TEAM_GUARD';break}
'104' {BOM $xteam 'rollback' 'INSTALL_BGXAI_TEAM_GUARD' 'ROLLBACK_BGXAI_TEAM_GUARD';break}
'105' {BOM $xp2 'status' 'INSTALL_BGXP2_COMBAT_PRIEST' 'ROLLBACK_BGXP2_COMBAT_PRIEST';break}
'106' {BOM $xp2 'preflight' 'INSTALL_BGXP2_COMBAT_PRIEST' 'ROLLBACK_BGXP2_COMBAT_PRIEST';break}
'107' {BOM $xp2 'install' 'INSTALL_BGXP2_COMBAT_PRIEST' 'ROLLBACK_BGXP2_COMBAT_PRIEST';break}
'108' {BOM $xp2 'rollback' 'INSTALL_BGXP2_COMBAT_PRIEST' 'ROLLBACK_BGXP2_COMBAT_PRIEST';break}
'109' {BOM $xp3 'status' 'INSTALL_BGXP3_AUTO_BUFFER' 'ROLLBACK_BGXP3_AUTO_BUFFER';break}
'110' {BOM $xp3 'preflight' 'INSTALL_BGXP3_AUTO_BUFFER' 'ROLLBACK_BGXP3_AUTO_BUFFER';break}
'111' {BOM $xp3 'install' 'INSTALL_BGXP3_AUTO_BUFFER' 'ROLLBACK_BGXP3_AUTO_BUFFER';break}
'112' {BOM $xp3 'rollback' 'INSTALL_BGXP3_AUTO_BUFFER' 'ROLLBACK_BGXP3_AUTO_BUFFER';break}
'113' {BOM $xp5 'status' 'INSTALL_BGXP5_EARLY_HEAL_SAFE' 'ROLLBACK_BGXP5_EARLY_HEAL_SAFE';break}
'114' {BOM $xp5 'preflight' 'INSTALL_BGXP5_EARLY_HEAL_SAFE' 'ROLLBACK_BGXP5_EARLY_HEAL_SAFE';break}
'115' {BOM $xp5 'install' 'INSTALL_BGXP5_EARLY_HEAL_SAFE' 'ROLLBACK_BGXP5_EARLY_HEAL_SAFE';break}
'116' {BOM $xp5 'rollback' 'INSTALL_BGXP5_EARLY_HEAL_SAFE' 'ROLLBACK_BGXP5_EARLY_HEAL_SAFE';break}
'117' {BGXAOEReadOnly;break}
'118' {BGXTest6Safe;break}
'119' {SyncRelease $ao;& py -3 (Join-Path $ao.localPath 'BGX119_TRACE.py');if($LASTEXITCODE){throw '119 STOP'};break}
'120' {SyncRelease $ao;& py -3 (Join-Path $ao.localPath 'BGX120_ENTANGLE_GUARD.py');if($LASTEXITCODE){throw '120 STOP'};break}
'121' {SyncRelease $ao;& py -3 (Join-Path $ao.localPath 'BGX121_READONLY.py');if($LASTEXITCODE){throw '121 STOP'};break}
'122' {SyncRelease $ao;& py -3 (Join-Path $ao.localPath 'BGX122_PROJECTILES_READONLY.py');if($LASTEXITCODE){throw '122 STOP'};break}
'123' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_PREFLIGHT.py') --mode preflight --game $gr;if($LASTEXITCODE){throw '123 STOP'};break}
'124' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_GUARDED_INSTALL.py') install --game $gr;if($LASTEXITCODE){throw '124 STOP'};break}
'125' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_GUARDED_INSTALL.py') status --game $gr;if($LASTEXITCODE){throw '125 STOP'};break}
'126' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_GUARDED_INSTALL.py') rollback --game $gr;if($LASTEXITCODE){throw '126 STOP'};break}
'127' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_V2_PREFLIGHT.py') --game $gr;if($LASTEXITCODE){throw '127 STOP'};break}
'128' {SyncRelease $rg;& py -3 $v2install install --game $gr;if($LASTEXITCODE){throw '128 STOP'};& py -3 $v2install status --game $gr;if($LASTEXITCODE){throw '128 VERIFY STOP'};break}
'129' {SyncRelease $rg;& py -3 $v2install status --game $gr;if($LASTEXITCODE){throw '129 STOP'};break}
'130' {SyncRelease $rg;& py -3 $v2install rollback --game $gr;if($LASTEXITCODE){throw '130 STOP'};break}
'131' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_V3_PREFLIGHT.py') --game $gr;if($LASTEXITCODE){throw '131 STOP'};break}
'132' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_V3_GUARDED_INSTALL.py') install --game $gr;if($LASTEXITCODE){throw '132 STOP'};break}
'133' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_V3_GUARDED_INSTALL.py') status --game $gr;if($LASTEXITCODE){throw '133 STOP'};break}
'134' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_V3_GUARDED_INSTALL.py') rollback --game $gr;if($LASTEXITCODE){throw '134 STOP'};break}
'135' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGX_FRIENDLY_AGGRO_AUDIT_READONLY.py') --game $gr;if($LASTEXITCODE){throw '135 STOP'};break}
'136' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGX_FRIENDLY_PROTECT_ISOLATION.py') install --game $gr;if($LASTEXITCODE){throw '136 STOP'};break}
'137' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGX_FRIENDLY_PROTECT_ISOLATION.py') status --game $gr;if($LASTEXITCODE){throw '137 STOP'};break}
'138' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGX_FRIENDLY_PROTECT_ISOLATION.py') rollback --game $gr;if($LASTEXITCODE){throw '138 STOP'};break}
'139' {SyncRelease $rg;& py -3 $ff install --game $gr;if($LASTEXITCODE){throw '139 STOP'};break}
'140' {SyncRelease $rg;& py -3 $ff status --game $gr;if($LASTEXITCODE){throw '140 STOP'};break}
'141' {SyncRelease $rg;& py -3 $ff rollback --game $gr;if($LASTEXITCODE){throw '141 STOP'};break}
'142' {SyncRelease $rg;& py -3 $trace install --game $gr;if($LASTEXITCODE){throw '142 STOP'};break}
'143' {SyncRelease $rg;& py -3 $trace status --game $gr;if($LASTEXITCODE){throw '143 STOP'};break}
'144' {SyncRelease $rg;& py -3 $trace rollback --game $gr;if($LASTEXITCODE){throw '144 STOP'};break}
'145' {SyncRelease $rg;& py -3 $fix install;if($LASTEXITCODE){throw '145 STOP'};break}
'146' {SyncRelease $rg;& py -3 $cap;if($LASTEXITCODE){throw '146 STOP'};break}
'147' {SyncRelease $rg;& py -3 $fix status;if($LASTEXITCODE){throw '147 STOP'};break}
'148' {SyncRelease $rg;& py -3 $fix rollback;if($LASTEXITCODE){throw '148 STOP'};break}
'149' {SyncRelease $rg;& py -3 $motion install;if($LASTEXITCODE){throw '149 STOP'};break}
'150' {SyncRelease $rg;& py -3 $motion status;if($LASTEXITCODE){throw '150 STOP'};break}
'151' {SyncRelease $rg;& py -3 $motion rollback;if($LASTEXITCODE){throw '151 STOP'};break}
'152' {SyncRelease $rg;& py -3 $enemy preflight --game $gr;if($LASTEXITCODE){throw '152 STOP'};break}
'153' {SyncRelease $rg;& py -3 $enemy install --game $gr;if($LASTEXITCODE){throw '153 STOP'};break}
'154' {SyncRelease $rg;& py -3 $enemy status --game $gr;if($LASTEXITCODE){throw '154 STOP'};break}
'155' {SyncRelease $rg;& py -3 $enemy rollback --game $gr;if($LASTEXITCODE){throw '155 STOP'};break}
'156' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_V5_GUARDED_INSTALL.py') --game $gr;if($LASTEXITCODE){throw '156 STOP'};break}
'157' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_V6_GUARDED_INSTALL.py') --game $gr;if($LASTEXITCODE){throw '157 STOP'};break}
'158' {SyncRelease $wr;& py -3 (Join-Path $wr.localPath 'BGXAI_WEAPON_GAME_PREFLIGHT_RO.py') --game $gr;if($LASTEXITCODE){throw '158 STOP'};break}
'159' {SyncRelease $wp;& py -3 (Join-Path $wp.localPath 'BGXWP_OBSERVER_GUARDED.py') --game $gr;if($LASTEXITCODE){throw '159 STOP'};break}
'160' {$r='BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_EEEX_R11_STATIC_COMPAT_RO_V3.py';$b=Get-PinnedBytes $r;if($b.Length -ne 8301 -or (HashBytes $b) -cne '4bf4e2a981a6602da02ba53dc3e5601fd69bb2f408c64d880c208f1a19bf83f4'){throw '160 SHA STOP'};$f=Join-Path $zcd ('eeex_ro_'+[guid]::NewGuid().ToString('N')+'.py');ANR $zcd;try{$h=[IO.File]::Open($f,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None);try{$h.Write($b,0,$b.Length)}finally{$h.Dispose()};if((HashFile $f) -cne '4bf4e2a981a6602da02ba53dc3e5601fd69bb2f408c64d880c208f1a19bf83f4'){throw '160 CACHE STOP'};& py -3 $f --game $gr;if($LASTEXITCODE){throw '160 STOP'}}finally{if(Test-Path -LiteralPath $f){Remove-Item -LiteralPath $f -Force}};break}
'161' {SyncRelease $td13;& py -3 (Join-Path $td13.localPath 'BGXAI_R13_GUARDED.py') --game $gr;if($LASTEXITCODE){throw '161 STOP'};break}
'162' {SyncRelease $td14;& py -3 (Join-Path $td14.localPath 'BGXAI_R13_SHORTNAME_GUARDED.py') --game $gr;if($LASTEXITCODE){throw '162 STOP'};break}
'163' {SyncRelease $td15;& py -3 (Join-Path $td15.localPath 'BGXAI_R13_HOLD_DIAG_GUARDED.py') --game $gr;if($LASTEXITCODE){throw '163 STOP'};break}
'164' {$p='BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_R19_INSTALLED_EEEX_AUDIT_RO.py';$b=Get-PinnedBytes $p;if($b.Length -ne 11013 -or (HashBytes $b) -cne '7426faaa18c1a7bb9a8437ee0733854bed0f868a419e96593c58c7ec71451300'){throw '164 SHA STOP'};$f=Join-Path $zcd ('r19_'+[guid]::NewGuid().ToString('N')+'.py');ANR $zcd;try{$h=[IO.File]::Open($f,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None);try{$h.Write($b,0,$b.Length)}finally{$h.Dispose()};if((HashFile $f) -cne '7426faaa18c1a7bb9a8437ee0733854bed0f868a419e96593c58c7ec71451300'){throw '164 CACHE STOP'};$d=Join-Path $env:USERPROFILE 'Documents\BGXAI_LIVE_REPORTS';if(!(Test-Path -LiteralPath $d)){New-Item -ItemType Directory -Path $d|Out-Null};ANR $d;$o=Join-Path $d ('BGXAI_R20_EEEX_STATIC_'+(Get-Date -Format 'yyyyMMddTHHmmssfff')+'.json');& py -3 $f --game $gr | Out-File -LiteralPath $o -Encoding utf8;$rc=$LASTEXITCODE;Get-Content -LiteralPath $o -Raw;Write-Host ('REPORT_FILE='+$o);if($rc -ne 0 -and $rc -ne 2){throw '164 SCAN ERROR'}}finally{if(Test-Path -LiteralPath $f){Remove-Item -LiteralPath $f -Force}};break}
'165' {SyncRelease $r27;& py -3 (Join-Path $r27.localPath 'BGXAI_R27_GUARDED.py') --game $gr;if($LASTEXITCODE){throw '165 STOP'};break}
'166' {SyncRelease $rg;& py -3 (Join-Path $rr 'BGXRANGED_V7_GUARDED_INSTALL.py') --game $gr;if($LASTEXITCODE){throw '166 STOP'};break}
'167' {SyncRelease $w3;$d=Join-Path $env:USERPROFILE 'Documents\BGXAI_LIVE_REPORTS';if(!(Test-Path -LiteralPath $d)){[IO.Directory]::CreateDirectory($d)|Out-Null};ANR $d;$o=Join-Path $d ('BGXAI_WEAPON_NATIVE_COMPILE_RO_'+(Get-Date -Format 'yyyyMMddTHHmmssfff')+'.json');& py -3 (Join-Path $w3.localPath 'BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py') --game $gr --source (Join-Path $w3.localPath 'BGXAI_WEAPON_SLOT_CONSUMER_V3.baf') | Out-File -LiteralPath $o -Encoding utf8;$rc=$LASTEXITCODE;Get-Content -LiteralPath $o -Raw;Write-Host ('REPORT_FILE='+$o);if($rc){throw '167 STOP'};break}
'168' {SyncRelease $w3;& py -3 (Join-Path $w3.localPath 'BGXAI_AUTO_BATCH_RO_V1.py') --game $gr;if($LASTEXITCODE){throw '168 STOP'};break}
'169' {SyncRelease $w3;& py -3 (Join-Path $w3.localPath 'BGXAI_R29_GUARDED.py') --game $gr;if($LASTEXITCODE){throw '169 STOP'};break}
default {throw 'Unknown menu option, no game change.'}
}
exit 0
} catch {
Write-Host ('BGXAI STOP: '+$_.Exception.Message) -ForegroundColor Red
Write-Host 'STOP. No auto retry.'
exit 1
}
