param(
  [Parameter(Mandatory=$true)]
  [string]$FontPath,
  [string]$ProjectRoot = 'H:\한글화\MMR_Project'
)

$ErrorActionPreference = 'Stop'
$ExpectedSha = '29EBF0A5DAB0A646FF9AF6E68127AAE6C8182AB2129C2819FB37177A94453BEB'
$BaseRom = Join-Path $ProjectRoot 'referenced-chatgpt-conversation-this-is-an-2\work\release\stage1467\Metal_Max_Returns_Korean_RC2_TEST_20260918.sfc'
$ToolRoot = Join-Path $ProjectRoot 'tools'
$OutDir = Join-Path $ProjectRoot 'work\release\stage1468_mona12_font_assets_only'
$OrientationTool = Join-Path $ToolRoot 'mmr_native12_orientation_resolver.py'
$Builder = Join-Path $ToolRoot 'mmr_stage1468_font_assets_only.py'
$DiffGate = Join-Path $ToolRoot 'mmr_font_only_diff_gate.py'

foreach($p in @($BaseRom,$FontPath,$OrientationTool,$Builder,$DiffGate)) {
  if(-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "MISSING_FILE: $p" }
}
$got = (Get-FileHash -Algorithm SHA256 -LiteralPath $BaseRom).Hash.ToUpperInvariant()
if($got -ne $ExpectedSha) { throw "STAGE1467_SHA_MISMATCH: $got != $ExpectedSha" }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$orientReport = Join-Path $OutDir 'MMR_STAGE1468_NATIVE12_ORIENTATION.json'
$candidate = Join-Path $OutDir 'Metal_Max_Returns_Korean_STAGE1468_MONA12_FONT_ASSETS_ONLY.sfc'
$buildReport = Join-Path $OutDir 'MMR_STAGE1468_MONA12_FONT_ASSETS_ONLY_REPORT.json'
$diffSpec = Join-Path $OutDir 'MMR_STAGE1468_FONT_ALLOWED_RANGES.json'
$diffReport = Join-Path $OutDir 'MMR_STAGE1468_FONT_ONLY_DIFF_REPORT.json'

& python $OrientationTool --rom $BaseRom -o $orientReport
if($LASTEXITCODE -ne 0) { throw "ORIENTATION_RESOLVER_FAIL: $LASTEXITCODE" }
$oj = Get-Content -Raw -LiteralPath $orientReport | ConvertFrom-Json
if(-not $oj.safe_to_choose_orientation) { throw "ORIENTATION_NOT_SAFE" }

& python $Builder --rom $BaseRom --expected-sha256 $ExpectedSha --font $FontPath --out-rom $candidate --report $buildReport
if($LASTEXITCODE -ne 0) { throw "FONT_ASSETS_BUILDER_FAIL: $LASTEXITCODE" }

@'
{
  "schema": "MMR_STAGE1468_FONT_ALLOWED_RANGES_V1",
  "ranges": [
    {"start":"0x358000","end_exclusive":"0x35FFEE","label":"EB_FONT_1310"},
    {"start":"0x360000","end_exclusive":"0x366590","label":"EC_FONT_1040"}
  ]
}
'@ | Set-Content -LiteralPath $diffSpec -Encoding UTF8

& python $DiffGate $BaseRom $candidate --allowed-ranges $diffSpec --out $diffReport
if($LASTEXITCODE -ne 0) { throw "FONT_ONLY_DIFF_GATE_FAIL: $LASTEXITCODE" }

$bj = Get-Content -Raw -LiteralPath $buildReport | ConvertFrom-Json
$dj = Get-Content -Raw -LiteralPath $diffReport | ConvertFrom-Json
[ordered]@{
  classification = 'STAGE1468_MONA12_FONT_ASSETS_ONLY_STATIC_PASS_RUNTIME_PENDING'
  baseline_sha256 = $ExpectedSha
  orientation = $oj.orientation
  candidate = $candidate
  candidate_sha256 = $bj.candidate.sha256
  changed_bytes = $bj.changed_bytes
  pointer_table_changed = $bj.pointer_table_changed
  d12_kmode_ecc6_changed = $bj.d12_kmode_ecc6_changed
  translation_bytes_changed = $bj.translation_bytes_changed
  diff_gate = $dj.classification
  runtime = 'NOT_RUN'
  new_real = $false
} | ConvertTo-Json -Depth 8 | Tee-Object -FilePath (Join-Path $OutDir 'MMR_STAGE1468_SUMMARY.json')
