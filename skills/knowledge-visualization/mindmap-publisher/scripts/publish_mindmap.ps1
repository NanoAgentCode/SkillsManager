param(
    [Parameter(Mandatory = $true)]
    [string]$SourceHtml,

    [Parameter(Mandatory = $true)]
    [string]$StaticRoot,

    [Parameter(Mandatory = $true)]
    [string]$PublicBaseUrl,

    [Parameter(Mandatory = $true)]
    [string]$PathPrefix,

    [Parameter(Mandatory = $true)]
    [string]$Slug
)

$ErrorActionPreference = "Stop"

function Normalize-PublicBaseUrl([string]$value) {
    $trimmed = $value.Trim()
    if (-not $trimmed) {
        throw "PublicBaseUrl is required."
    }
    return $trimmed.TrimEnd("/")
}

function Normalize-PathPrefix([string]$value) {
    $trimmed = $value.Trim()
    if (-not $trimmed) {
        throw "PathPrefix is required and must not be empty."
    }
    if ($trimmed -eq "/") {
        throw "PathPrefix must not be '/'. Provide a non-root prefix such as /mindmaps."
    }
    if (-not $trimmed.StartsWith("/")) {
        $trimmed = "/" + $trimmed
    }
    return $trimmed.TrimEnd("/")
}

function Assert-Slug([string]$value) {
    if (-not $value -or $value -notmatch "^[A-Za-z0-9._-]+$") {
        throw "Slug must contain only letters, digits, dots, underscores, or hyphens."
    }
    if ($value -eq "." -or $value -eq "..") {
        throw "Slug must be a real folder name."
    }
}

$sourcePath = (Resolve-Path -LiteralPath $SourceHtml).Path
$sourceDir = Split-Path -Parent $sourcePath
$sourceAssets = Join-Path $sourceDir "markmap-assets"

$html = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
if ($html.Contains("cdn.jsdelivr.net")) {
    throw "SourceHtml still references CDN assets. Render it with mindmap-builder offline script first."
}

$needsAssets = $html -match 'markmap-assets/'
if ($needsAssets -and -not (Test-Path -LiteralPath $sourceAssets -PathType Container)) {
    throw "Missing source markmap-assets directory next to SourceHtml: $sourceAssets"
}

Assert-Slug $Slug
$normalizedBase = Normalize-PublicBaseUrl $PublicBaseUrl
$normalizedPrefix = Normalize-PathPrefix $PathPrefix

$staticRootPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($StaticRoot)
New-Item -ItemType Directory -Force -Path $staticRootPath | Out-Null

$destinationDir = Join-Path $staticRootPath $Slug
$destinationAssets = Join-Path $destinationDir "markmap-assets"
New-Item -ItemType Directory -Force -Path $destinationDir | Out-Null
if ($needsAssets) {
    New-Item -ItemType Directory -Force -Path $destinationAssets | Out-Null

    $requiredAssets = @("d3.min.js", "markmap-view.js", "markmap-toolbar.js", "markmap-toolbar.css")
    foreach ($asset in $requiredAssets) {
        $sourceAsset = Join-Path $sourceAssets $asset
        if (-not (Test-Path -LiteralPath $sourceAsset -PathType Leaf)) {
            throw "Missing required source asset: $sourceAsset"
        }
        Copy-Item -LiteralPath $sourceAsset -Destination (Join-Path $destinationAssets $asset) -Force
    }

    foreach ($asset in $requiredAssets) {
        $publishedAsset = Join-Path $destinationAssets $asset
        if (-not (Test-Path -LiteralPath $publishedAsset -PathType Leaf)) {
            throw "Failed to publish required asset: $publishedAsset"
        }
    }

}

# Publish the entrypoint only after any required assets are in place. LiteralPath does not
# expand wildcards, so enumerate the fixed offline asset contract explicitly.
Copy-Item -LiteralPath $sourcePath -Destination (Join-Path $destinationDir "index.html") -Force

$url = "$normalizedBase$normalizedPrefix/$Slug/index.html"

[ordered]@{
    published_dir = $destinationDir
    index_file = Join-Path $destinationDir "index.html"
    url = $url
} | ConvertTo-Json
