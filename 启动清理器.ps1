# 智能文档清理器 PowerShell 启动脚本
# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# 设置工作目录为脚本所在目录
Set-Location -Path $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           智能文档清理器" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    # 检查Python是否安装
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "错误: 未找到Python，请先安装Python 3.6或更高版本" -ForegroundColor Red
        Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
        Read-Host "按回车键退出"
        exit 1
    }
    
    Write-Host "检测到Python版本: $pythonVersion" -ForegroundColor Green
    Write-Host ""
    
    # 运行Python脚本
    python start_cleaner.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "" 
        Write-Host "程序执行出错，错误代码: $LASTEXITCODE" -ForegroundColor Red
        Read-Host "按回车键退出"
    }
}
catch {
    Write-Host "发生异常: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "按回车键退出"
}