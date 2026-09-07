param([switch]$Live, [string]$Reviews, [string]$ReplayRun, [string]$RecheckRun, [switch]$ImageSearch, [string]$SkuEvidence, [string]$ReviewEvidence, [switch]$Test, [switch]$VerifyMigration)
$ErrorActionPreference = 'Stop'
$projectRoot = (Get-Item -LiteralPath $PSScriptRoot).Parent.Parent.Parent.FullName
$pythonExe = Join-Path $projectRoot 'runtime_support/python_environment/venv/Scripts/python.exe'
$launchScript = Join-Path $projectRoot 'workflow_execution/launcher/scripts/launch.py'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Project Python environment is missing; see START_HERE.md.' }
if (@($Live.IsPresent, [bool]$Reviews, [bool]$ReplayRun, [bool]$RecheckRun).Where({ $_ }).Count -gt 1) { throw 'Choose a single input mode.' }
$agentArgs = @('-B', $launchScript)
if ($Live) { $agentArgs += @('--live-read', '--live-search') }
if ($Reviews) { $agentArgs += @('--reviews', $Reviews) }
if ($ReplayRun) { $agentArgs += @('--replay-run', $ReplayRun) }
if ($RecheckRun) { $agentArgs += @('--recheck-run', $RecheckRun) }
if ($ImageSearch) { $agentArgs += '--image-search' }
if ($SkuEvidence) { $agentArgs += @('--sku-evidence', $SkuEvidence) }
if ($ReviewEvidence) { $agentArgs += @('--review-evidence', $ReviewEvidence) }
if ($Test) { $agentArgs += '--test' }
if ($VerifyMigration) { $agentArgs += '--verify-migration' }
$env:PYTHONIOENCODING = 'utf-8'
Push-Location -LiteralPath $projectRoot
try { & $pythonExe @agentArgs; $agentExit = $LASTEXITCODE } finally { Pop-Location }
exit $agentExit
