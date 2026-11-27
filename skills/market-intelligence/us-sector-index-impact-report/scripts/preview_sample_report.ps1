param(
  [string]$Output = "",
  [switch]$Open
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$RepoRoot = Split-Path -Parent (Split-Path -Parent $SkillRoot)
$Input = Join-Path $SkillRoot "fixtures\sample-report.json"
$Renderer = Join-Path $SkillRoot "scripts\render_investment_bank_html.py"
$Launcher = Join-Path $RepoRoot "scripts\run-python.ps1"

if ([string]::IsNullOrWhiteSpace($Output)) {
  $Output = Join-Path (Get-Location) "output\us-sector-index-impact-report\sample-report.html"
}

if (Test-Path -LiteralPath $Launcher -PathType Leaf) {
  & $Launcher $Renderer --input $Input --output $Output
} else {
  $Python = Get-Command python, python3, py -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $Python) {
    throw "Python is required to render the sample report."
  }
  & $Python.Source $Renderer --input $Input --output $Output
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$ResolvedOutput = Resolve-Path $Output
Write-Host "Preview report: $ResolvedOutput"

if ($Open) {
  Start-Process $ResolvedOutput
}
