# SciAgent 开发环境启动脚本 (PowerShell)
# 一键启动前后端开发服务器

Write-Host "=== SciAgent 开发环境启动 ===" -ForegroundColor Cyan
Write-Host "目标：同时启动前端 (Next.js) 和后端 (FastAPI)" -ForegroundColor Gray

# 检查端口占用
function Test-Port($port) {
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# 检查依赖
Write-Host "检查依赖..." -ForegroundColor Yellow
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js 未安装" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python 未安装" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Node.js $(node --version)" -ForegroundColor Green
Write-Host "✅ Python $(python --version)" -ForegroundColor Green

# 检查端口
$ports = @(3000, 8000)
foreach ($port in $ports) {
    if (Test-Port $port) {
        Write-Host "⚠️  端口 $port 已被占用" -ForegroundColor Yellow
    }
}

# 启动后端
Write-Host "`n启动后端 (FastAPI)..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -WorkingDirectory "backend" -PassThru -WindowStyle Hidden

# 等待后端启动
Write-Host "等待后端启动..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 检查后端健康
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ 后端启动成功 (PID: $($backendProcess.Id))" -ForegroundColor Green
    Write-Host "   API 文档: http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host "   健康检查: http://localhost:8000/api/v1/health" -ForegroundColor Gray
} catch {
    Write-Host "❌ 后端启动失败" -ForegroundColor Red
    Write-Host "错误: $_" -ForegroundColor Red
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# 启动前端
Write-Host "`n启动前端 (Next.js)..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "frontend" -PassThru -WindowStyle Hidden

# 等待前端启动
Write-Host "等待前端启动..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 检查前端
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ 前端启动成功 (PID: $($frontendProcess.Id))" -ForegroundColor Green
    Write-Host "   前端地址: http://localhost:3000" -ForegroundColor Gray
    Write-Host "   Next.js 开发工具: http://localhost:3000/_next" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  前端启动可能较慢，请稍后访问" -ForegroundColor Yellow
    Write-Host "   前端地址: http://localhost:3000" -ForegroundColor Gray
}

# 显示汇总信息
Write-Host "`n=== 开发环境启动完成 ===" -ForegroundColor Cyan
Write-Host "前端: http://localhost:3000" -ForegroundColor White
Write-Host "后端: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n进程信息:" -ForegroundColor Gray
Write-Host "  后端 PID: $($backendProcess.Id)" -ForegroundColor Gray
Write-Host "  前端 PID: $($frontendProcess.Id)" -ForegroundColor Gray
Write-Host "`n停止服务: 按 Ctrl+C 或关闭此窗口" -ForegroundColor Yellow

# 保持脚本运行
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # 清理进程
    Write-Host "`n正在停止服务..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "服务已停止" -ForegroundColor Green
}