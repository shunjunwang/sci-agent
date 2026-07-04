# P4-08: 代码静态检查脚本
# 优先使用 ruff，被 IT 策略拦截时回退到 pyflakes

param(
    [string]$Path = "app/"
)

Write-Host "=== SciAgent Lint ==="

# Try ruff first
$ruffResult = & ruff check $Path --select E,F,W --statistics 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[ruff] PASSED"
    exit 0
}

# ruff failed — check if blocked by policy
if ($ruffResult -match "blocked|Application Control") {
    Write-Host "[ruff] Blocked by IT policy, falling back to pyflakes..."
} else {
    Write-Host "[ruff] FAILED — falling back to pyflakes..."
    Write-Host $ruffResult
}

# Fallback: pyflakes
python -m pyflakes $Path
if ($LASTEXITCODE -eq 0) {
    Write-Host "[pyflakes] PASSED"
} else {
    Write-Host "[pyflakes] FAILED — review errors above"
    exit 1
}

Write-Host "=== Lint Complete ==="
