# Live progress view for the long-running pipeline steps. Leave it open in a terminal; Ctrl+C to quit.
#   powershell -ExecutionPolicy Bypass -File scripts\watch_progress.ps1
# Refreshes every 5 seconds: clock, last line of each log, finished training runs, GPU usage.

$logs = [ordered]@{
    "question generation" = "gen_questions.log"
    "baselines"           = "baselines.log"
    "mining bge-small"    = "mine_bge.log"
    "mining minilm"       = "mine_minilm.log"
    "training (all runs)" = "train_all.log"
    "style-shift gen"     = "style_gen.log"
    "style-shift check"   = "style_shift.log"
    "forgetting check"    = "forgetting.log"
    "RAG run"             = "rag.log"
}
$root = Split-Path -Parent $PSScriptRoot

function Last-Line($path) {
    if (-not (Test-Path $path)) { return "-" }
    $text = Get-Content $path -Raw -ErrorAction SilentlyContinue
    if (-not $text) { return "(empty)" }
    $line = ($text -split "`r|`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
    if ($line.Length -gt 110) { $line = $line.Substring(0, 110) + "..." }
    return $line
}

while ($true) {
    Clear-Host
    Write-Host ("=== pipeline progress  " + (Get-Date -Format "HH:mm:ss") + " ===") -ForegroundColor Cyan
    foreach ($name in $logs.Keys) {
        $path = Join-Path $env:TEMP $logs[$name]
        $age = ""
        if (Test-Path $path) { $age = "  (updated " + [int]((Get-Date) - (Get-Item $path).LastWriteTime).TotalSeconds + "s ago)" }
        Write-Host ("{0,-20}" -f $name) -NoNewline -ForegroundColor Yellow
        Write-Host ((Last-Line $path) + $age)
    }
    Write-Host ""
    $runs = Join-Path $root "results\runs.csv"
    if (Test-Path $runs) {
        $rows = Import-Csv $runs
        Write-Host ("finished training runs: {0} / 8" -f $rows.Count) -ForegroundColor Green
        $rows | Select-Object run, best_epoch, train_minutes, @{n = "test_ndcg@10"; e = { $_."test_split_ndcg@10" } }, @{n = "test_recall@1"; e = { $_."test_split_recall@1" } } | Format-Table -AutoSize
    } else {
        Write-Host "finished training runs: 0 / 8"
    }
    $gpu = nvidia-smi --query-gpu=utilization.gpu,memory.used,temperature.gpu --format=csv,noheader 2>$null
    if ($gpu) { Write-Host ("GPU (util, memory, temp): " + $gpu) -ForegroundColor DarkGray }
    Start-Sleep -Seconds 5
}
