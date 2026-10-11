param(
    [Parameter(Mandatory = $true)]
    [string]$InputMarkdown,

    [Parameter(Mandatory = $true)]
    [string]$OutputHtml
)

$ErrorActionPreference = "Stop"

$markmap = Get-Command markmap -ErrorAction SilentlyContinue
if (-not $markmap) {
    throw "markmap command not found. Install with: npm install -g markmap-cli"
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
$sourceAssetsDir = Join-Path (Join-Path $skillDir "assets") "markmap"

if (-not (Test-Path -LiteralPath $sourceAssetsDir)) {
    throw "Missing bundled markmap assets: $sourceAssetsDir"
}

$inputPath = (Resolve-Path -LiteralPath $InputMarkdown).Path
$outputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputHtml)
$outputDir = Split-Path -Parent $outputPath
if (-not $outputDir) {
    $outputDir = (Get-Location).Path
    $outputPath = Join-Path $outputDir $OutputHtml
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$temporaryPath = Join-Path $outputDir ([guid]::NewGuid().ToString() + ".html")
try {
    & $markmap.Source $inputPath --output $temporaryPath --no-open
    if ($LASTEXITCODE -ne 0) {
        throw "markmap failed with exit code $LASTEXITCODE"
    }

    # Inline only supported runtime assets. MatchEvaluator preserves literal JS $ signs.
    $assetPatterns = [ordered]@{
        'd3.min.js' = '<script\b[^>]*\bsrc=["'']https?://cdn\.jsdelivr\.net/npm/d3@[^/]+/dist/d3(?:\.min)?\.js["''][^>]*>\s*</script>'
        'markmap-view.js' = '<script\b[^>]*\bsrc=["'']https?://cdn\.jsdelivr\.net/npm/markmap-view@[^/]+/dist/browser/index\.js["''][^>]*>\s*</script>'
        'markmap-toolbar.js' = '<script\b[^>]*\bsrc=["'']https?://cdn\.jsdelivr\.net/npm/markmap-toolbar@[^/]+/dist/index\.js["''][^>]*>\s*</script>'
        'markmap-toolbar.css' = '<link\b[^>]*\bhref=["'']https?://cdn\.jsdelivr\.net/npm/markmap-toolbar@[^/]+/dist/style\.css["''][^>]*>'
    }
    $html = Get-Content -LiteralPath $temporaryPath -Raw -Encoding UTF8
    foreach ($asset in $assetPatterns.Keys) {
        $pattern = $assetPatterns[$asset]
        if ([regex]::Matches($html, $pattern, 'IgnoreCase').Count -ne 1) {
            throw "Expected exactly one runtime reference for $asset. Unsupported markmap-cli output."
        }
        $content = Get-Content -LiteralPath (Join-Path $sourceAssetsDir $asset) -Raw -Encoding UTF8
        if ($asset.EndsWith('.css')) {
            $content = [regex]::Replace($content, '</style', '<\/style', 'IgnoreCase')
            $inlineTag = "<style>$content</style>"
        } else {
            $content = [regex]::Replace($content, '</script', '<\/script', 'IgnoreCase')
            $inlineTag = "<script>$content</script>"
        }
        $html = [regex]::Replace($html, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($match) $inlineTag }, 'IgnoreCase')
    }
    # Inspect loading attributes rather than all URLs: links in mindmap nodes are allowed.
    if ($html -match '(?i)<(?:script|link|img|iframe|source|video|audio|object|embed)\b[^>]*\b(?:src|href|data|poster)\s*=\s*["''](?!data:)[^"'']+') {
        throw "Generated HTML still loads a separate resource. Use text-only Markdown or embed media as data URLs."
    }
    foreach ($styleBlock in [regex]::Matches($html, '(?is)<style\b[^>]*>(.*?)</style>')) {
    $css = $styleBlock.Groups[1].Value
    if ($css -match '(?i)url\(\s*["'']?(?!data:|#)[^\s)"'']+' -or $css -match '(?i)@import\s') {
        throw "Generated HTML still has a CSS resource dependency."
    }
    }
    Set-Content -LiteralPath $outputPath -Value $html -Encoding UTF8
} finally {
    if (Test-Path -LiteralPath $temporaryPath) {
        Remove-Item -LiteralPath $temporaryPath -Force
    }
}
Write-Output $outputPath
