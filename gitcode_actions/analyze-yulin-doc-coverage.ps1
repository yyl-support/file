$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$workbook = Join-Path $root 'gitcode-pipeline-test-cases.xlsx'
$output = Join-Path $root 'yulin-doc-coverage.csv'

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $book = $excel.Workbooks.Open($workbook)
    $rows = @()

    foreach ($sheet in $book.Worksheets) {
        $used = $sheet.UsedRange
        # Excel COM exposes Chinese headers with the console code page here, so find the
        # unambiguous owner value first and preserve the worksheet's first tabular header row.
        $headerRow = 2
        for ($row = $headerRow + 1; $row -le $used.Rows.Count; $row++) {
            $ownerColumn = 0
            for ($column = 1; $column -le $used.Columns.Count; $column++) {
                if (([string]$sheet.Cells.Item($row, $column).Text).Trim() -ieq 'yulin') {
                    $ownerColumn = $column
                    break
                }
            }
            if ($ownerColumn -gt 0) {
                $record = [ordered]@{ Sheet = $sheet.Name; Row = $row; Owner = 'yulin' }
                for ($column = 1; $column -le $used.Columns.Count; $column++) {
                    $header = ([string]$sheet.Cells.Item($headerRow, $column).Text).Trim()
                    if ([string]::IsNullOrWhiteSpace($header)) { $header = "Column$column" }
                    $record[$header] = ([string]$sheet.Cells.Item($row, $column).Text).Trim()
                }
                $rows += [PSCustomObject]$record
            }
        }
    }

    $rows | Export-Csv -LiteralPath $output -NoTypeInformation -Encoding UTF8
    Write-Output "Rows=$($rows.Count)"
    Write-Output "Output=$output"
    $rows | Format-Table -AutoSize | Out-String -Width 4096
} finally {
    if ($book) { $book.Close($false) }
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
}
