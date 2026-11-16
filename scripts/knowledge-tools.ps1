$commands = @{
    'mindmap-render' = 'mindmap-builder/scripts/render_offline_mindmap.ps1'
    'mindmap-publish' = 'mindmap-publisher/scripts/publish_mindmap.ps1'
    'vault-search' = 'obsidian-memory/scripts/search-memory.ps1'
    'vault-reindex' = 'obsidian-memory/scripts/rebuild-index.ps1'
    'vault-audit' = 'obsidian-memory-cleanup/scripts/audit-memory-vault.ps1'
}

if ($args.Count -eq 0 -or $args[0] -in @('-h', '--help')) {
    @'
Usage: pwsh -File scripts/knowledge-tools.ps1 <command> [arguments]

mindmap-render  -InputMarkdown <path> -OutputHtml <path>
mindmap-publish -SourceHtml <path> -StaticRoot <path> -PublicBaseUrl <url> -PathPrefix <prefix> -Slug <slug>
vault-search    -VaultPath <path> -Query <keywords> [-Scope <folder>] [-MatchMode All|Any] [-Limit <count>]
vault-reindex   -VaultPath <path>
vault-audit     -VaultPath <path> [-SimilarityThreshold <number>] [-Json]
'@
    exit 0
}

$command = $args[0]
if (-not $commands.ContainsKey($command)) {
    [Console]::Error.WriteLine("Unknown command: $command. Use --help.")
    exit 2
}

$root = Join-Path $PSScriptRoot '../skills/knowledge-visualization'
$script = Join-Path $root $commands[$command]
$forwarded = @($args | Select-Object -Skip 1)
# A child PowerShell binds forwarded named parameters and isolates explicit exit calls.
& (Join-Path $PSHOME 'pwsh') -NoProfile -NonInteractive -File $script @forwarded
exit $LASTEXITCODE
