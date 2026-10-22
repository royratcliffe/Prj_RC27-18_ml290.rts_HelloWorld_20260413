<#
.SYNOPSIS
    Exports the visible worksheets of .xlsx workbooks to UTF-8 CSV files.

.DESCRIPTION
    Uses Microsoft Excel (COM automation) to open each workbook read-only and save
    every visible worksheet as a UTF-8 CSV next to the workbook. Hidden and
    very-hidden sheets are skipped.

    Output naming:
      - Workbook with one visible sheet:  <Workbook>.csv
      - Workbook with several:            <Workbook>_<Sheet>.csv

    Existing CSV files are overwritten. Requires Excel to be installed.

.PARAMETER Path
    Folder containing .xlsx files, or a single .xlsx file.
    Defaults to the repository's _easyConfig_import folder.

.PARAMETER Recurse
    Search subfolders for .xlsx files.

.PARAMETER WhatIf
    Preview which CSV files would be written without writing them.

.EXAMPLE
    .\scripts\Convert-XlsxToCsv.ps1

.EXAMPLE
    .\scripts\Convert-XlsxToCsv.ps1 -Path .\_easyConfig_import\DTC-import_template.xlsx
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Path = (Join-Path (Split-Path $PSScriptRoot -Parent) '_easyConfig_import'),
    [switch]$Recurse
)

$ErrorActionPreference = 'Stop'

$xlCSVUTF8 = 62
$xlSheetVisible = -1

$workbooks = Get-ChildItem -LiteralPath $Path -Filter '*.xlsx' -File -Recurse:$Recurse |
    Where-Object { -not $_.Name.StartsWith('~$') }

if (-not $workbooks) {
    Write-Host "No .xlsx files found under '$Path'."
    return
}

$written = 0
$failed = 0

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    foreach ($file in $workbooks) {
        $book = $null
        try {
            $book = $excel.Workbooks.Open($file.FullName, 0, $true)
            $sheets = @($book.Worksheets | Where-Object { $_.Visible -eq $xlSheetVisible })

            if ($sheets.Count -eq 0) {
                Write-Warning "No visible worksheets in '$($file.FullName)'."
                continue
            }

            $baseName = [IO.Path]::GetFileNameWithoutExtension($file.Name)
            foreach ($sheet in $sheets) {
                $csvName = if ($sheets.Count -eq 1) { "$baseName.csv" } else { "${baseName}_$($sheet.Name).csv" }
                $csvPath = Join-Path $file.DirectoryName $csvName

                if (-not $PSCmdlet.ShouldProcess($csvPath, "Export sheet '$($sheet.Name)'")) {
                    continue
                }

                # Copying the sheet into a new workbook keeps the source workbook untouched.
                $sheet.Copy()
                $csvBook = $excel.ActiveWorkbook
                try {
                    $csvBook.SaveAs($csvPath, $xlCSVUTF8)
                    Write-Host "Created $csvPath"
                    $written++
                }
                finally {
                    $csvBook.Close($false)
                    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($csvBook)
                }
            }
        }
        catch {
            Write-Warning "Failed to convert '$($file.FullName)': $($_.Exception.Message)"
            $failed++
        }
        finally {
            if ($null -ne $book) {
                $book.Close($false)
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)
            }
        }
    }
}
finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Host "Done. CSV files written: $written, Workbooks failed: $failed"
if ($failed -gt 0) { exit 1 }
