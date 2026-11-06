param(
    [Parameter(Mandatory=$true)][string]$Executable,
    [Parameter(Mandatory=$true)][string]$EvidenceDirectory
)
$ErrorActionPreference='Stop'
$exe=(Resolve-Path -LiteralPath $Executable).Path
$null=New-Item -ItemType Directory -Path $EvidenceDirectory -Force
$evidence=(Resolve-Path -LiteralPath $EvidenceDirectory).Path
$runId=[guid]::NewGuid().ToString('N')
$report=Join-Path $evidence ($runId+'.json')
$log=Join-Path $evidence ($runId+'.log')
$arguments=@('-unattended','-nosplash','-NoSound','-windowed','-ResX=960','-ResY=540',('-StudioEvidence="'+$report+'"'),('-StudioRunId='+$runId),('-abslog="'+$log+'"'))
$started=Get-Date
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory (Split-Path -Parent $exe) -WindowStyle Hidden -PassThru
Write-Output (@{pid=$p.Id;run_id=$runId;report=$report;log=$log}|ConvertTo-Json -Compress)
$exited=$p.WaitForExit(180000)
if (-not $exited) {
    Stop-Process -Id $p.Id -ErrorAction SilentlyContinue
    throw 'Task-owned packaged process exceeded 180-second smoke timeout.'
}
$p.Refresh()
$exitCode=$p.ExitCode
if (-not (Test-Path -LiteralPath $report)) { throw "No runtime report; packaged process exited with $exitCode. Inspect $log" }
$result=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
$screenshot=[IO.Path]::ChangeExtension($report,'.png')
$errorLines=@(Select-String -LiteralPath $log -Pattern ': Error:|Fatal error:|Ensure condition failed:' | ForEach-Object {$_.Line})
$warningLines=@(Select-String -LiteralPath $log -Pattern ': Warning:' | ForEach-Object {$_.Line})
$passed=($exitCode -eq 0 -and $result.status -eq 'passed' -and $result.run_id -eq $runId -and $result.is_editor -eq $false -and $result.frames -eq 90 -and $result.health -eq 75 -and $result.movement_x -eq 300 -and (Test-Path -LiteralPath $screenshot))
$passed=$passed -and $errorLines.Count -eq 0
$summary=@{status=$(if($passed){'passed'}else{'failed'});exit_code=$exitCode;run_id=$runId;seconds=[math]::Round(((Get-Date)-$started).TotalSeconds,2);executable=$exe;executable_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash;report=$report;log=$log;screenshot=$screenshot;runtime=$result;log_error_count=$errorLines.Count;log_warning_count=$warningLines.Count;log_errors=$errorLines;log_warnings=$warningLines}
$summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $evidence 'summary.json') -Encoding utf8
$summary|ConvertTo-Json -Depth 8
if (-not $passed) {exit 1}
