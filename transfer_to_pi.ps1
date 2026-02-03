# 📦 Transfer Files to Raspberry Pi
# PowerShell script to copy project files from Windows to Raspberry Pi

param(
    [Parameter(Mandatory=$true)]
    [string]$PiIP,
    
    [Parameter(Mandatory=$false)]
    [string]$PiUser = "pi",
    
    [Parameter(Mandatory=$false)]
    [string]$TargetPath = "~/auto-print"
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "📦 Transfer to Raspberry Pi" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$ProjectPath = $PSScriptRoot

# Check if scp is available
try {
    $null = Get-Command scp -ErrorAction Stop
} catch {
    Write-Host "❌ Error: scp command not found!" -ForegroundColor Red
    Write-Host "Please install OpenSSH Client:" -ForegroundColor Yellow
    Write-Host "  Settings > Apps > Optional Features > Add OpenSSH Client" -ForegroundColor Yellow
    exit 1
}

# Check if serviceAccountKey.json exists
if (-not (Test-Path "$ProjectPath\serviceAccountKey.json")) {
    Write-Host "⚠️  Warning: serviceAccountKey.json not found!" -ForegroundColor Yellow
    Write-Host "You'll need to transfer it separately." -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

Write-Host "📋 Transfer Details:" -ForegroundColor Green
Write-Host "  From: $ProjectPath"
Write-Host "  To: $PiUser@$PiIP`:$TargetPath"
Write-Host ""

# Test connection
Write-Host "🔍 Testing connection to Raspberry Pi..." -ForegroundColor Cyan
$testResult = Test-Connection -ComputerName $PiIP -Count 2 -Quiet

if (-not $testResult) {
    Write-Host "❌ Cannot reach $PiIP" -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "  1. Raspberry Pi is powered on" -ForegroundColor Yellow
    Write-Host "  2. IP address is correct" -ForegroundColor Yellow
    Write-Host "  3. Both devices are on same network" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Connection successful!" -ForegroundColor Green
Write-Host ""

# Create list of files to transfer
$filesToTransfer = @(
    "*.py",
    "*.txt",
    "*.md",
    "*.sh",
    "*.service",
    ".gitignore"
)

if (Test-Path "$ProjectPath\serviceAccountKey.json") {
    $filesToTransfer += "serviceAccountKey.json"
}

Write-Host "📁 Files to transfer:" -ForegroundColor Cyan
foreach ($pattern in $filesToTransfer) {
    $files = Get-ChildItem -Path $ProjectPath -Filter $pattern -File
    foreach ($file in $files) {
        Write-Host "  ✓ $($file.Name)" -ForegroundColor Gray
    }
}
Write-Host ""

# Confirm transfer
$confirm = Read-Host "Proceed with transfer? (y/n)"
if ($confirm -ne "y") {
    Write-Host "❌ Transfer cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting transfer..." -ForegroundColor Cyan
Write-Host ""

# Transfer files
try {
    # Create directory on Pi if it doesn't exist
    Write-Host "📂 Creating directory on Raspberry Pi..." -ForegroundColor Cyan
    ssh "$PiUser@$PiIP" "mkdir -p $TargetPath"
    
    # Transfer each file
    foreach ($pattern in $filesToTransfer) {
        $files = Get-ChildItem -Path $ProjectPath -Filter $pattern -File
        foreach ($file in $files) {
            Write-Host "  Transferring $($file.Name)..." -ForegroundColor Gray
            scp "$($file.FullName)" "${PiUser}@${PiIP}:${TargetPath}/"
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✅ Success" -ForegroundColor Green
            } else {
                Write-Host "    ❌ Failed" -ForegroundColor Red
            }
        }
    }
    
    # Make shell script executable
    Write-Host ""
    Write-Host "🔧 Setting permissions..." -ForegroundColor Cyan
    ssh "$PiUser@$PiIP" "chmod +x $TargetPath/*.sh"
    
    Write-Host ""
    Write-Host "================================" -ForegroundColor Green
    Write-Host "✅ Transfer Complete!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. SSH into your Pi: ssh $PiUser@$PiIP" -ForegroundColor Yellow
    Write-Host "  2. Navigate to project: cd $TargetPath" -ForegroundColor Yellow
    Write-Host "  3. Run setup: ./setup_pi.sh" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ Transfer failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Ensure SSH is enabled on Pi" -ForegroundColor Yellow
    Write-Host "  2. Verify credentials (default password: raspberry)" -ForegroundColor Yellow
    Write-Host "  3. Check network connectivity" -ForegroundColor Yellow
    exit 1
}
