param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [Parameter(Mandatory=$true)][string]$Slot1Manifest,
  [Parameter(Mandatory=$true)][string]$Slot2Manifest,
  [string]$OutDir
)

$ErrorActionPreference='Stop'
if(-not $OutDir){ $OutDir=Join-Path $ProjectRoot 'work\name_entry_discovery' }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Tools=Join-Path $ProjectRoot 'tools'
$Diff=Join-Path $Tools 'mmr_name_entry_wram_diff.py'
$Stride=Join-Path $Tools 'mmr_name_entry_wram_stride.py'
$GenWrite=Join-Path $Tools 'mmr_name_entry_generate_write_pc_probe.py'

foreach($p in @($Slot1Manifest,$Slot2Manifest,$Diff,$Stride,$GenWrite)){
 if(-not (Test-Path -LiteralPath $p -PathType Leaf)){ throw "MISSING_FILE: $p" }
}

$R1=Join-Path $OutDir 'slot1_wram_diff.json'
$R2=Join-Path $OutDir 'slot2_wram_diff.json'
$RS=Join-Path $OutDir 'slot_stride.json'
$Lua=Join-Path $OutDir 'name_entry_write_pc_probe.lua'

& python $Diff $Slot1Manifest -o $R1
if($LASTEXITCODE -ne 0){ throw "SLOT1_DIFF_FAIL" }

& python $Diff $Slot2Manifest -o $R2
if($LASTEXITCODE -ne 0){ throw "SLOT2_DIFF_FAIL" }

& python $Stride $R1 $R2 -o $RS
if($LASTEXITCODE -ne 0){ throw "STRIDE_FAIL" }

& python $GenWrite $R1 -o $Lua
if($LASTEXITCODE -ne 0){ throw "WRITE_PROBE_GEN_FAIL" }

[ordered]@{
 schema='MMR_NAME_ENTRY_DISCOVERY_PHASE1_V1'
 classification='PASS_NAME_ENTRY_DISCOVERY_PHASE1'
 slot1_report=$R1
 slot2_report=$R2
 stride_report=$RS
 next_lua=$Lua
 next='Run the generated Lua in three controlled original-JP one-character input sessions and save three logs.'
} | ConvertTo-Json -Depth 5 | Tee-Object -FilePath (Join-Path $OutDir 'PHASE1_SUMMARY.json')
