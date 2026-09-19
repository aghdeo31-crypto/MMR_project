param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [Parameter(Mandatory=$true)][string]$CandidateRom,
  [Parameter(Mandatory=$true)][string]$ExpectedCandidateSha256,
  [Parameter(Mandatory=$true)][string]$NameOriginalCaptures,
  [Parameter(Mandatory=$true)][string]$NameCandidateCaptures,
  [Parameter(Mandatory=$true)][string]$NameCrop,
  [Parameter(Mandatory=$true)][string]$UiCapturePlan,
  [string]$OutDir
)

$ErrorActionPreference = 'Stop'
if(-not $OutDir) {
  $OutDir = Join-Path $ProjectRoot 'work\stage1468_system_ui_preflight'
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Need-File([string]$p) {
  if(-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "MISSING_FILE: $p" }
}
function Need-Dir([string]$p) {
  if(-not (Test-Path -LiteralPath $p -PathType Container)) { throw "MISSING_DIR: $p" }
}
function Run-Python {
  param([string]$Script,[string[]]$Args)
  Need-File $Script
  & python $Script @Args
  if($LASTEXITCODE -ne 0) { throw "PYTHON_FAIL $Script exit=$LASTEXITCODE" }
}

$Tools = Join-Path $ProjectRoot 'tools'
$NameBinding = Join-Path $Tools 'mmr_name_entry_rom_binding_gate.py'
$NameGeometry = Join-Path $Tools 'mmr_name_entry_geometry_compare.py'
$UiCompare = Join-Path $Tools 'mmr_ui_surface_compare.py'
$Identity = Join-Path $Tools 'mmr_ks2350_identity_gate.py'

Need-File $CandidateRom
Need-Dir $NameOriginalCaptures
Need-Dir $NameCandidateCaptures
Need-File $UiCapturePlan
foreach($p in @($NameBinding,$NameGeometry,$UiCompare,$Identity)) { Need-File $p }

$ExpectedCandidateSha256 = $ExpectedCandidateSha256.ToUpperInvariant()
$actualSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $CandidateRom).Hash.ToUpperInvariant()
if($actualSha -ne $ExpectedCandidateSha256) {
  throw "CANDIDATE_SHA_MISMATCH: $actualSha != $ExpectedCandidateSha256"
}

# Gate A: all 2350 private-token identities, including 한/힌/이/히.
$IdentityReport = Join-Path $OutDir 'MMR_KS2350_IDENTITY_GATE.json'
$IdentityLedger = Join-Path $OutDir 'MMR_KS2350_IDENTITY_LEDGER.tsv'
Run-Python $Identity @(
  '-o',$IdentityReport,
  '--ledger',$IdentityLedger
)

# Gate B: exact four 50-entry name page payloads in this exact ROM.
$BindingReport = Join-Path $OutDir 'MMR_NAME_ENTRY_ROM_BINDING_GATE.json'
Run-Python $NameBinding @(
  '--rom',$CandidateRom,
  '--expected-sha256',$ExpectedCandidateSha256,
  '-o',$BindingReport
)

# Gate C: JP original vs KR candidate five-row cursor/font geometry.
$GeometryOut = Join-Path $OutDir 'name_geometry'
Run-Python $NameGeometry @(
  '--original',$NameOriginalCaptures,
  '--candidate',$NameCandidateCaptures,
  '--candidate-sha256',$ExpectedCandidateSha256,
  '--crop',$NameCrop,
  '--out',$GeometryOut
)
$GeometryReport = Join-Path $GeometryOut 'MMR_NAME_ENTRY_GEOMETRY_COMPARE.json'

# Gate D: P0 fixed system/UI surfaces.
$plan = Get-Content -Raw -LiteralPath $UiCapturePlan | ConvertFrom-Json
if(-not $plan.surfaces -or $plan.surfaces.Count -eq 0) { throw 'UI_CAPTURE_PLAN_EMPTY' }

$required = @(
  'MEMORY_CENTER_NOTICE',
  'RECORD_SELECTION',
  'MAIN_MENU',
  'ITEM_EQUIPMENT_STATUS',
  'SHOP_SERVICE_UI',
  'BATTLE_UI',
  'SAVE_LOAD_UI'
)
$gotIds = @($plan.surfaces | ForEach-Object { [string]$_.id })
foreach($id in $required) {
  if($gotIds -notcontains $id) { throw "UI_CAPTURE_PLAN_MISSING_P0: $id" }
}

$surfaceResults = @()
$UiRoot = Join-Path $OutDir 'ui_surfaces'
New-Item -ItemType Directory -Force -Path $UiRoot | Out-Null

foreach($s in $plan.surfaces) {
  $id = [string]$s.id
  $orig = [string]$s.original_png
  $cand = [string]$s.candidate_png
  $manifest = [string]$s.manifest_json
  foreach($p in @($orig,$cand,$manifest)) { Need-File $p }
  $report = Join-Path $UiRoot ($id + '.json')
  Run-Python $UiCompare @(
    '--original',$orig,
    '--candidate',$cand,
    '--manifest',$manifest,
    '--candidate-sha256',$ExpectedCandidateSha256,
    '--out',$report
  )
  $r = Get-Content -Raw -LiteralPath $report | ConvertFrom-Json
  $surfaceResults += [ordered]@{
    id = $id
    classification = $r.classification
    pass_count = $r.pass_count
    total = $r.total
    report = $report
  }
}

# Final fail-closed summary.
$idr = Get-Content -Raw -LiteralPath $IdentityReport | ConvertFrom-Json
$br = Get-Content -Raw -LiteralPath $BindingReport | ConvertFrom-Json
$gr = Get-Content -Raw -LiteralPath $GeometryReport | ConvertFrom-Json

$uiAllPass = ($surfaceResults | Where-Object { $_.classification -ne 'PASS_UI_FONT_SURFACES' }).Count -eq 0
$allPass =
  ($idr.classification -eq 'PASS_KS2350_IDENTITY') -and
  ($br.classification -eq 'PASS_NAME_ENTRY_ROM_BINDING_EXACT') -and
  ($gr.classification -eq 'PASS_NAME_ENTRY_GEOMETRY') -and
  $uiAllPass

$summary = [ordered]@{
  schema = 'MMR_STAGE1468_SYSTEM_UI_PREFLIGHT_V1'
  candidate = [ordered]@{
    path = $CandidateRom
    sha256 = $actualSha
  }
  gates = [ordered]@{
    glyph_identity = $idr.classification
    name_entry_rom_binding = $br.classification
    name_entry_geometry = $gr.classification
    p0_ui_surfaces_all_pass = $uiAllPass
    p0_ui_surfaces = $surfaceResults
  }
  classification = $(if($allPass) { 'PASS_STAGE1468_SYSTEM_UI_PREFLIGHT' } else { 'HOLD_STAGE1468_SYSTEM_UI_PREFLIGHT' })
  allow_runtime_candidate = $allPass
  allow_release = $false
  note = 'This preflight allows a runtime test candidate only. It never promotes RC/final.'
}
$SummaryPath = Join-Path $OutDir 'MMR_STAGE1468_SYSTEM_UI_PREFLIGHT_SUMMARY.json'
$summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $SummaryPath -Encoding UTF8
$summary | ConvertTo-Json -Depth 10

if(-not $allPass) { exit 2 }
exit 0
