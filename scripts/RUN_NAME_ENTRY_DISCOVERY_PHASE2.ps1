param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [Parameter(Mandatory=$true)][string]$CharALog,
  [Parameter(Mandatory=$true)][string]$CharBLog,
  [Parameter(Mandatory=$true)][string]$CharCLog,
  [string]$OutDir
)

$ErrorActionPreference='Stop'
if(-not $OutDir){ $OutDir=Join-Path $ProjectRoot 'work\name_entry_discovery' }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Tools=Join-Path $ProjectRoot 'tools'
$Parse=Join-Path $Tools 'mmr_name_entry_parse_write_pc_logs.py'
$GenCtx=Join-Path $Tools 'mmr_name_entry_generate_writer_context_probe.py'

foreach($p in @($CharALog,$CharBLog,$CharCLog,$Parse,$GenCtx)){
 if(-not (Test-Path -LiteralPath $p -PathType Leaf)){ throw "MISSING_FILE: $p" }
}

$Writer=Join-Path $OutDir 'writer_pc_report.json'
$Lua=Join-Path $OutDir 'name_entry_writer_context_probe.lua'

& python $Parse --log ("charA="+$CharALog) --log ("charB="+$CharBLog) --log ("charC="+$CharCLog) -o $Writer
if($LASTEXITCODE -ne 0){ throw "WRITE_PC_PARSE_FAIL" }

& python $GenCtx $Writer -o $Lua
if($LASTEXITCODE -ne 0){ throw "WRITER_CONTEXT_GEN_FAIL" }

[ordered]@{
 schema='MMR_NAME_ENTRY_DISCOVERY_PHASE2_V1'
 classification='PASS_NAME_ENTRY_DISCOVERY_PHASE2'
 writer_pc_report=$Writer
 next_lua=$Lua
 next='Run writer context probe in at least three controlled name-entry sessions, then parse context and perform mode-aware disassembly/dataflow.'
} | ConvertTo-Json -Depth 5 | Tee-Object -FilePath (Join-Path $OutDir 'PHASE2_SUMMARY.json')
