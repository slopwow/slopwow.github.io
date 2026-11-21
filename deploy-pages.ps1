param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$RootDir = $PSScriptRoot
$SiteDir = Join-Path $RootDir "site"
$Owner = "slopwow"
$Repo = "slopwow.github.io"
$RemoteUrl = "https://github.com/$Owner/$Repo.git"
$LiveUrl = "https://$Owner.github.io"

Push-Location $RootDir
try {
    if (-not $SkipBuild) {
        Write-Host "[1/4] Building static archive for $LiveUrl ..." -ForegroundColor Cyan
        python -m wow_sloptoon.cli build-site
        if ($LASTEXITCODE -ne 0) { throw "build-site failed" }
    }

    if (-not (Test-Path (Join-Path $SiteDir "index.html"))) {
        throw "site/index.html not found."
    }

    Write-Host "[2/4] Pushing source branch (main) ..." -ForegroundColor Cyan
    git add -A
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "chore: update wow-forever-sloptoon archive ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
    }
    git push -u origin main

    Write-Host "[3/4] Publishing site/ to gh-pages branch ..." -ForegroundColor Cyan
    $TempDir = Join-Path $env:TEMP ("slopwow-pages-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
    New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
    try {
        Copy-Item -Path (Join-Path $SiteDir "*") -Destination $TempDir -Recurse -Force
        if (Test-Path (Join-Path $SiteDir ".nojekyll")) {
            Copy-Item -Path (Join-Path $SiteDir ".nojekyll") -Destination $TempDir -Force
        }
        Push-Location $TempDir
        try {
            git -c core.autocrlf=false init -q -b gh-pages
            git remote add origin $RemoteUrl
            git -c core.autocrlf=false add -A
            git commit -q -m "deploy: publish slopwow.github.io ($(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))"
            git push -q -u origin gh-pages --force
        } finally {
            Pop-Location
        }
    } finally {
        Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    }

    Write-Host "[4/4] Ensuring GitHub Pages is active on gh-pages (/) ..." -ForegroundColor Cyan
    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    gh api "repos/$Owner/$Repo/pages" 2>&1 | Out-Null
    $pagesExists = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $oldEap

    if (-not $pagesExists) {
        gh api "repos/$Owner/$Repo/pages" -X POST -f "source[branch]=gh-pages" -f "source[path]=/" | Out-Null
    } else {
        gh api "repos/$Owner/$Repo/pages" -X PUT -f "source[branch]=gh-pages" -f "source[path]=/" | Out-Null
    }
    gh api "repos/$Owner/$Repo/pages/builds" -X POST | Out-Null

    Write-Host "Deployed to $LiveUrl !" -ForegroundColor Green
} finally {
    Pop-Location
}
