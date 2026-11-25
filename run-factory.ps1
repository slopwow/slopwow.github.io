<#
.SYNOPSIS
    Operations helper for the WOW Forever Sloptoon static archive pipeline.

.DESCRIPTION
    Provides one-command inspection and maintenance helpers for WOW Forever Sloptoon
    (<REPO_ROOT>, static archive only at https://slopwow.github.io/):
      - Default / -Status : Read-only dashboard showing Antigravity sidecar status,
                            optional Windows Task Scheduler status, and static archive
                            summary (never mutates JSON/config files).
      - -Scout            : Scans unproduced DCInside wowforever recommend candidates.
      - -DryRun           : Runs `python -m wow_sloptoon.cli autopilot --dry-run`.
      - -BuildSite        : Rebuilds `site/` static archive locally (`build-site`).
      - -Watermark        : Applies the bottom `slopwow.github.io` banner (`watermark`).
      - -Deploy           : Rebuilds & deploys `site/` + `main` to https://slopwow.github.io/.

.EXAMPLE
    .\run-factory.ps1
    Displays full read-only automation and static archive status.

.EXAMPLE
    .\run-factory.ps1 -Scout -Pages 3
    Lists top unproduced wowforever concept post candidates across 3 pages.

.EXAMPLE
    .\run-factory.ps1 -Deploy
    Rebuilds site/ and deploys to https://slopwow.github.io/.
#>
[CmdletBinding()]
param(
    [switch]$Status,
    [switch]$Scout,
    [switch]$DryRun,
    [switch]$BuildSite,
    [switch]$Watermark,
    [switch]$Deploy,
    [ValidateRange(1, 10)]
    [int]$Pages = 2,
    [ValidateRange(1, 30)]
    [int]$Limit = 10
)

$ErrorActionPreference = "Stop"
$RootDir = $PSScriptRoot
$SidecarId = "wow-sloptoon-factory"
$SidecarPath = Join-Path $HOME ".gemini\config\sidecars\$SidecarId\sidecar.json"
$UserConfigPath = Join-Path $HOME ".gemini\config\user_config.json"
$EpisodesJsonPath = Join-Path $RootDir "data\episodes.json"
$SiteIndexPath = Join-Path $RootDir "site\index.html"
$SetupAutoScript = Join-Path $RootDir "setup-automation.ps1"
$DeployScript = Join-Path $RootDir "deploy-pages.ps1"

function Show-FactoryStatus {
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host "  WOW Forever Sloptoon (sloptoon) - Static Archive Status" -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host "  Project Root : $RootDir"
    Write-Host "  Live Archive : https://slopwow.github.io/"
    Write-Host "  Publish Mode : Static Web Archive Only (Route A: 2~2.5-head SD)"
    Write-Host ""

    # 1. Antigravity Scheduled Automation Sidecar (read-only check)
    Write-Host "[1/3] Antigravity Scheduled Automation Sidecar ($SidecarId)" -ForegroundColor Cyan
    if (Test-Path $SidecarPath) {
        $sidecar = Get-Content -Raw -Encoding UTF8 $SidecarPath | ConvertFrom-Json
        $cronSpec = if ($sidecar.args -and $sidecar.args.Count -gt 0) { $sidecar.args[0] } else { "(missing)" }
        $grantCount = if ($sidecar.agent_permissions -and $sidecar.agent_permissions.access_grants) {
            $sidecar.agent_permissions.access_grants.Count
        } else {
            0
        }

        $enabledState = "Managed in Antigravity Automations Dashboard (sidecar://dashboard)"
        if (Test-Path $UserConfigPath) {
            try {
                $uCfg = Get-Content -Raw -Encoding UTF8 $UserConfigPath | ConvertFrom-Json
                if ($uCfg.PSObject.Properties.Name -contains "sidecars") {
                    $scEntry = $uCfg.sidecars.$SidecarId
                    if ($null -ne $scEntry -and ($scEntry.PSObject.Properties.Name -contains "enabled")) {
                        $enabledState = if ($scEntry.enabled) { "ENABLED (true)" } else { "DISABLED (enable in sidecar://dashboard)" }
                    }
                }
            } catch {
                # Keep non-intrusive fallback description if user_config.json structure differs
            }
        }

        Write-Host ("  Sidecar File   : Present ({0})" -f $SidecarPath) -ForegroundColor Green
        Write-Host ("  Display Name   : {0}" -f $sidecar.display_name)
        Write-Host ("  Builtin / Mode : {0} (restart_policy={1})" -f $sidecar.builtin, $sidecar.restart_policy)
        Write-Host ("  Cron Schedule  : {0}" -f $cronSpec)
        Write-Host ("  Scoped Grants  : {0} verified permission grant(s)" -f $grantCount)
        Write-Host ("  Dashboard State: {0}" -f $enabledState)
    } else {
        Write-Host ("  Sidecar config not found at {0}" -f $SidecarPath) -ForegroundColor Yellow
    }
    Write-Host ""

    # 2. Optional Windows Task Scheduler status
    Write-Host "[2/3] Optional Windows Task Scheduler Fallback (setup-automation.ps1)" -ForegroundColor Cyan
    if (Test-Path $SetupAutoScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $SetupAutoScript -Status
    } else {
        Write-Host "  setup-automation.ps1 not found." -ForegroundColor Yellow
    }
    Write-Host ""

    # 3. Read-only Static Archive Summary
    Write-Host "[3/3] Static Archive Summary (Read-Only)" -ForegroundColor Cyan
    if (Test-Path $EpisodesJsonPath) {
        $rawEp = Get-Content -Raw -Encoding UTF8 $EpisodesJsonPath | ConvertFrom-Json
        $episodes = if ($rawEp -is [System.Array]) { $rawEp } elseif ($rawEp.episodes) { $rawEp.episodes } else { @($rawEp) }
        Write-Host ("  Produced Episodes (data/episodes.json) : {0}" -f $episodes.Count)
        if ($episodes.Count -gt 0) {
            $latest = $episodes | Sort-Object -Property episode_number | Select-Object -Last 1
            Write-Host ("  Latest Episode                         : {0} (EP.{1} - {2}, #{3})" -f `
                $latest.episode_id, $latest.episode_number, $latest.title, $latest.source_post_no)
        }
    } else {
        Write-Host "  data/episodes.json not found." -ForegroundColor Yellow
    }

    if (Test-Path $SiteIndexPath) {
        $siteDir = Split-Path -Parent $SiteIndexPath
        $epHtmlCount = @(Get-ChildItem -Path (Join-Path $siteDir "episodes") -Filter "*.html" -ErrorAction SilentlyContinue).Count
        Write-Host ("  Static Site (site/index.html)          : Present ({0} episode HTML page(s))" -f $epHtmlCount) -ForegroundColor Green
    } else {
        Write-Host "  Static Site (site/index.html)          : Missing (run .\run-factory.ps1 -BuildSite)" -ForegroundColor Yellow
    }
}

$hasActionSwitch = $Scout -or $DryRun -or $BuildSite -or $Watermark -or $Deploy

Push-Location $RootDir
try {
    if ($Status -or (-not $hasActionSwitch)) {
        Show-FactoryStatus
    }

    if ($Scout) {
        Write-Host ""
        Write-Host ">>> Scouting unproduced wowforever recommend posts (pages=$Pages, limit=$Limit)..." -ForegroundColor Cyan
        python -m wow_sloptoon.cli --project-root $RootDir scout --pages $Pages --limit $Limit
        if ($LASTEXITCODE -ne 0) { throw "scout command failed with exit code $LASTEXITCODE" }
    }

    if ($DryRun) {
        Write-Host ""
        Write-Host ">>> Running autopilot dry-run preview..." -ForegroundColor Cyan
        python -m wow_sloptoon.cli --project-root $RootDir autopilot --dry-run --pages $Pages
        if ($LASTEXITCODE -ne 0) { throw "autopilot --dry-run failed with exit code $LASTEXITCODE" }
    }

    if ($Watermark) {
        Write-Host ""
        Write-Host ">>> Applying bottom slopwow.github.io watermark banner..." -ForegroundColor Cyan
        python -m wow_sloptoon.cli --project-root $RootDir watermark
        if ($LASTEXITCODE -ne 0) { throw "watermark command failed with exit code $LASTEXITCODE" }
    }

    if ($BuildSite -and (-not $Deploy)) {
        Write-Host ""
        Write-Host ">>> Building static archive (site/)..." -ForegroundColor Cyan
        python -m wow_sloptoon.cli --project-root $RootDir build-site
        if ($LASTEXITCODE -ne 0) { throw "build-site failed with exit code $LASTEXITCODE" }
    }

    if ($Deploy) {
        Write-Host ""
        Write-Host ">>> Deploying static archive & main branch to https://slopwow.github.io/ ..." -ForegroundColor Cyan
        & powershell -NoProfile -ExecutionPolicy Bypass -File $DeployScript
        if ($LASTEXITCODE -ne 0) { throw "deploy-pages.ps1 failed with exit code $LASTEXITCODE" }
    }
} finally {
    Pop-Location
}
