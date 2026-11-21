<#
.SYNOPSIS
    Register, inspect, or remove the Windows Task Scheduler job for WOW Forever Sloptoon.

.DESCRIPTION
    Creates a policy-compliant Windows Scheduled Task ("WowForeverSloptoonAuto") that runs
    every 6 hours to execute:
        python -m wow_sloptoon.cli autopilot --deploy

    The autopilot pipeline automatically scouts new recommend posts, generates episodes when
    GEMINI_API_KEY is configured, rebuilds & deploys https://slopwow.github.io, refreshes
    data/publish_queue.json + upload_pack/, and displays a non-blocking notification when
    an episode is ready. DCInside publishing always remains manual human review/CAPTCHA/submit
    via `python -m wow_sloptoon.cli publish-next --open-folder --open-browser --copy-body`.

.EXAMPLE
    .\setup-automation.ps1
    Registers or updates the 6-hour recurring scheduled task.

.EXAMPLE
    .\setup-automation.ps1 -Status
    Shows current registration state, schedule, and last run info.

.EXAMPLE
    .\setup-automation.ps1 -Remove
    Unregisters and removes the scheduled task.
#>
[CmdletBinding()]
param(
    [switch]$Status,
    [switch]$Remove,
    [ValidateRange(1, 168)]
    [int]$IntervalHours = 6,
    [string]$TaskName = "WowForeverSloptoonAuto"
)

$ErrorActionPreference = "Stop"
$RootDir = $PSScriptRoot
$CliArgs = "-m wow_sloptoon.cli autopilot --deploy"

function Show-TaskStatus {
    param([string]$Name)

    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "Scheduled task '$Name' is NOT registered." -ForegroundColor Yellow
        Write-Host "Run '.\setup-automation.ps1' to register the ${IntervalHours}-hour autopilot schedule."
        return
    }

    $info = Get-ScheduledTaskInfo -TaskName $Name -ErrorAction SilentlyContinue
    $action = $task.Actions | Select-Object -First 1

    Write-Host "=== Windows Task Scheduler Status: $Name ===" -ForegroundColor Cyan
    Write-Host ("  State           : {0}" -f $task.State)
    if ($action) {
        Write-Host ("  Execute         : {0}" -f $action.Execute)
        Write-Host ("  Arguments       : {0}" -f $action.Arguments)
        Write-Host ("  WorkingDir      : {0}" -f $action.WorkingDirectory)
    }
    if ($info) {
        Write-Host ("  Last Run Time   : {0}" -f $info.LastRunTime)
        Write-Host ("  Last Run Result : 0x{0:X}" -f $info.LastTaskResult)
        Write-Host ("  Next Run Time   : {0}" -f $info.NextRunTime)
    }
}

if ($Status -and $Remove) {
    throw "Specify either -Status or -Remove, not both."
}

if ($Status) {
    Show-TaskStatus -Name $TaskName
    exit 0
}

if ($Remove) {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $existing) {
        Write-Host "Scheduled task '$TaskName' is already absent." -ForegroundColor Yellow
        exit 0
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task '$TaskName'." -ForegroundColor Green
    exit 0
}

# Resolve Python executable cleanly (Windows Store Python 3.11 editable install supported)
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    throw "Could not locate 'python' on PATH. Install Python 3.11+ and ensure it is on PATH."
}
$PythonExe = $PythonCmd.Source

Write-Host "Registering Windows Scheduled Task '$TaskName' (every $IntervalHours hours)..." -ForegroundColor Cyan
Write-Host "  Project Root : $RootDir"
Write-Host "  Command      : $PythonExe $CliArgs"

$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument $CliArgs `
    -WorkingDirectory $RootDir

$StartTime = (Get-Date).AddMinutes(2)
$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At $StartTime `
    -RepetitionInterval (New-TimeSpan -Hours $IntervalHours) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew

$CurrentUser = if ($env:USERDOMAIN) { "$($env:USERDOMAIN)\$($env:USERNAME)" } else { $env:USERNAME }
$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType Interactive `
    -RunLevel Limited

$Description = (
    "WOW Forever Sloptoon autopilot (every ${IntervalHours}h): " +
    "scout -> generate -> build-site -> pack-dc -> sync publish_queue -> deploy slopwow.github.io. " +
    "DCInside upload remains strictly manual human review/CAPTCHA/submit."
)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description $Description `
    -Force | Out-Null

Write-Host "Registered '$TaskName' successfully!" -ForegroundColor Green
Show-TaskStatus -Name $TaskName
Write-Host ""
Write-Host "Manual DCInside upload workflow when notified:" -ForegroundColor DarkCyan
Write-Host "  python -m wow_sloptoon.cli queue"
Write-Host "  python -m wow_sloptoon.cli publish-next --open-folder --open-browser --copy-body"
Write-Host "  python -m wow_sloptoon.cli mark-published <episode_id> --dc-url <POST_URL>"
