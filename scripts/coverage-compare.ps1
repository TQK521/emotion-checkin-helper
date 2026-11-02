# coverage-compare.ps1 —— 覆盖率回归对比（核心约束十七.2）
# 用法：
#   运行 pnpm test --coverage 之后执行：
#     powershell -File scripts/coverage-compare.ps1            # 仅对比，输出差值
#     powershell -File scripts/coverage-compare.ps1 -Save      # 对比并更新 baseline 为本次结果
#     powershell -File scripts/coverage-compare.ps1 -Threshold 3
# 判定：任一项相对基线下降 >= Threshold 个百分点 => 回归警告（exit 1），否则 exit 0。
param(
  [switch]$Save,
  [int]$Threshold = 5,
  [int]$Tests = 0
)
$ErrorActionPreference = "Stop"

$root     = Split-Path -Parent $PSScriptRoot
$summaryPath  = Join-Path $root "webapp\coverage\coverage-summary.json"
$baselinePath = Join-Path $root "webapp\coverage-baseline.json"

if (-not (Test-Path -LiteralPath $summaryPath)) {
  Write-Error "未找到覆盖率结果 $summaryPath —— 请先在 webapp 下运行 pnpm test --coverage"
  exit 2
}
$summary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
$total   = $summary.total

$metrics = [ordered]@{
  statements = $total.statements.pct
  branches   = $total.branches.pct
  functions  = $total.functions.pct
  lines      = $total.lines.pct
}

if (Test-Path -LiteralPath $baselinePath) {
  $base = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
} else {
  $base = $null
}

$row = "当前结果：Stmts {0:F2}% | Branch {1:F2}% | Funcs {2:F2}% | Lines {3:F2}%" -f `
  $metrics.statements, $metrics.branches, $metrics.functions, $metrics.lines
Write-Host $row

if ($null -eq $base) {
  Write-Host "无基线文件（$baselinePath），本次结果即为基线。可用 -Save 写入。"
  exit 0
}

Write-Host ""
Write-Host ("基线({0} v{1}, {2} 用例): Stmts {3:F2}% | Branch {4:F2}% | Funcs {5:F2}% | Lines {6:F2}%" -f `
  $base.recorded_at, $base.version, $base.tests, $base.statements, $base.branches, $base.functions, $base.lines)
Write-Host ""
Write-Host ("{0,-12} {1,10} {2,10} {3,10}" -f "指标", "基线", "当前", "差值")
$regressed = @()
foreach ($k in $metrics.Keys) {
  $diff = $metrics[$k] - [double]$base.$k
  $flag = if ($diff -lt 0) { " ▼" } else { "" }
  Write-Host ("{0,-12} {1,10:F2} {2,10:F2} {3,10:F2}{4}" -f $k, [double]$base.$k, $metrics[$k], $diff, $flag)
  if ($diff -le -$Threshold) { $regressed += $k }
}

if ($regressed.Count -gt 0) {
  Write-Host ""
  Write-Host ("回归警告（阈值 {0}pp）：{1} 较基线显著下降 —— 视为质量回归（约束十七.2），先复盘再继续。" -f $Threshold, ($regressed -join ", "))
  exit 1
}

if ($Save) {
  $now = Get-Date -Format "yyyy-MM-dd"
  $note = "自动更新于 $now（对比通过）"
  $newBase = [ordered]@{
    version     = $base.version
    recorded_at = $now
    tests       = $Tests
    statements  = [math]::Round($metrics.statements, 2)
    branches    = [math]::Round($metrics.branches, 2)
    functions   = [math]::Round($metrics.functions, 2)
    lines       = [math]::Round($metrics.lines, 2)
    note        = $note
  }
  $json = $newBase | ConvertTo-Json -Depth 3
  [IO.File]::WriteAllText($baselinePath, $json, (New-Object Text.UTF8Encoding $false))
  Write-Host ""
  Write-Host "已更新基线 → $baselinePath"
}
Write-Host "对比通过（无显著下降）。"
exit 0
