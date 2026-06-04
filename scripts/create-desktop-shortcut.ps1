$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path ".").Path
$assetsDir = Join-Path $repoRoot "assets"
$iconPath = Join-Path $assetsDir "trainer-icon.ico"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "SQL-Python Analyst Practice.lnk"

New-Item -ItemType Directory -Force -Path $assetsDir | Out-Null

Add-Type -AssemblyName System.Drawing

function New-RoundedRectanglePath {
    param(
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $diameter = $Radius * 2
    $path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $path.AddArc($X + $Width - $diameter, $Y + $Height - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

function New-IconPngBytes {
    $scale = 4
    $size = 256 * $scale
    $bitmap = New-Object System.Drawing.Bitmap $size, $size, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $graphics.ScaleTransform($scale, $scale)

    $backgroundPath = New-RoundedRectanglePath 18 18 220 220 48
    $backgroundBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush `
        ([System.Drawing.RectangleF]::new(18, 18, 220, 220)),
        ([System.Drawing.Color]::FromArgb(255, 31, 111, 155)),
        ([System.Drawing.Color]::FromArgb(255, 31, 122, 87)),
        45
    $graphics.FillPath($backgroundBrush, $backgroundPath)

    $goldBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(230, 240, 184, 79))
    $graphics.FillEllipse($goldBrush, 166, 166, 48, 48)

    $shadowBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(42, 16, 34, 48))
    $shadowPath = New-RoundedRectanglePath 69 70 144 144 27
    $graphics.FillPath($shadowBrush, $shadowPath)

    $cardPath = New-RoundedRectanglePath 64 58 144 144 25
    $cardBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush `
        ([System.Drawing.RectangleF]::new(64, 58, 144, 144)),
        ([System.Drawing.Color]::White),
        ([System.Drawing.Color]::FromArgb(255, 238, 246, 248)),
        90
    $graphics.FillPath($cardBrush, $cardPath)

    $headerPath = New-RoundedRectanglePath 64 58 144 43 25
    $headerBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 21, 52, 71))
    $graphics.FillPath($headerBrush, $headerPath)
    $graphics.FillRectangle($headerBrush, 64, 82, 144, 22)

    foreach ($circle in @(@(86, 78, 240, 107, 107), @(105, 78, 240, 184, 79), @(124, 78, 70, 192, 134))) {
        $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, $circle[2], $circle[3], $circle[4]))
        $graphics.FillEllipse($brush, $circle[0], $circle[1], 10, 10)
        $brush.Dispose()
    }

    $linePen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 199, 214, 223)), 9
    $linePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $linePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $graphics.DrawLine($linePen, 92, 123, 181, 123)
    $graphics.DrawLine($linePen, 92, 151, 163, 151)
    $graphics.DrawLine($linePen, 92, 178, 142, 178)

    $bluePen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 31, 111, 155)), 13
    $bluePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $bluePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $bluePen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $greenPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 31, 122, 87)), 13
    $greenPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $greenPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $greenPen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $slashPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 240, 184, 79)), 12
    $slashPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $slashPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round

    $graphics.DrawLines($bluePen, @(
        [System.Drawing.PointF]::new(111, 133),
        [System.Drawing.PointF]::new(89, 150),
        [System.Drawing.PointF]::new(111, 167)
    ))
    $graphics.DrawLines($greenPen, @(
        [System.Drawing.PointF]::new(165, 133),
        [System.Drawing.PointF]::new(187, 150),
        [System.Drawing.PointF]::new(165, 167)
    ))
    $graphics.DrawLine($slashPen, 145, 127, 125, 176)

    $memory = New-Object System.IO.MemoryStream
    $bitmap.Save($memory, [System.Drawing.Imaging.ImageFormat]::Png)
    $pngBytes = $memory.ToArray()

    $graphics.Dispose()
    $bitmap.Dispose()
    $memory.Dispose()
    return $pngBytes
}

function Write-IcoFromPng {
    param(
        [byte[]]$PngBytes,
        [string]$Path
    )
    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write)
    $writer = New-Object System.IO.BinaryWriter $stream
    $writer.Write([UInt16]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]1)
    $writer.Write([byte]0)
    $writer.Write([byte]0)
    $writer.Write([byte]0)
    $writer.Write([byte]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]32)
    $writer.Write([UInt32]$PngBytes.Length)
    $writer.Write([UInt32]22)
    $writer.Write($PngBytes)
    $writer.Dispose()
    $stream.Dispose()
}

Write-IcoFromPng -PngBytes (New-IconPngBytes) -Path $iconPath

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = (Join-Path $repoRoot "start-trainer.cmd")
$shortcut.WorkingDirectory = $repoRoot
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = "SQL/Python analyst one-week self-test bank"
$shortcut.Save()

$desktopCmdFiles = Get-ChildItem -LiteralPath $desktop -Filter "*.cmd" -File -ErrorAction SilentlyContinue
foreach ($cmdFile in $desktopCmdFiles) {
    $oldContent = Get-Content -LiteralPath $cmdFile.FullName -Raw -ErrorAction SilentlyContinue
    if ($oldContent -and $oldContent.Contains($repoRoot) -and $oldContent.Contains("start-trainer.cmd")) {
        Remove-Item -LiteralPath $cmdFile.FullName -Force
    }
}

Write-Host "Created desktop shortcut: $shortcutPath"
