param([string]$DataDirectory = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$fmErrors = [System.Collections.Generic.List[string]]::new()
function Check([bool]$Condition, [string]$Message) { if (-not $Condition) { $fmErrors.Add($Message) } }
$fmRawPages = @(Get-ChildItem -LiteralPath $DataDirectory -Filter 'raw_page_*.json' | Sort-Object Name | ForEach-Object { Get-Content -Raw -Encoding UTF8 -LiteralPath $_.FullName | ConvertFrom-Json })
$fmObservations = @(Import-Csv -Encoding UTF8 -LiteralPath (Join-Path $DataDirectory 'observations.csv'))
$fmProductsCsv = @(Import-Csv -Encoding UTF8 -LiteralPath (Join-Path $DataDirectory 'products.csv'))
$fmPackage = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $DataDirectory 'products.json') | ConvertFrom-Json
$fmProductsJson = @($fmPackage.products)
$fmIssues = @(Import-Csv -Encoding UTF8 -LiteralPath (Join-Path $DataDirectory 'data_issues.csv'))
Check ($fmRawPages.Count -eq 10) 'Expected 10 raw pages'
Check ($fmObservations.Count -eq 100) 'Expected 100 observations'
Check ($fmProductsCsv.Count -eq 95 -and $fmProductsJson.Count -eq 95) 'Expected 95 unique products'
Check (@($fmProductsCsv.product_id | Sort-Object -Unique).Count -eq 95) 'Duplicate exported product IDs'
$fmRawMap = @{}
foreach ($fmPage in $fmRawPages) {
  foreach ($fmRow in $fmPage.rows) {
    $fmRecordId = 'p{0:00}-r{1:00}' -f $fmPage.page, $fmRow.page_position
    $fmRawMap[$fmRecordId] = @{ Page = $fmPage; Row = $fmRow }
  }
}
foreach ($fmObs in $fmObservations) {
  $fmRaw = $fmRawMap[$fmObs.record_id]
  Check ($null -ne $fmRaw) ('Unknown raw record ' + $fmObs.record_id)
  if ($null -eq $fmRaw) { continue }
  $fmCells = @($fmRaw.Row.cells)
  Check ($fmObs.product_id -cmatch '^\d{19}$') ('Product ID format ' + $fmObs.record_id)
  Check ($fmObs.shop_id -cmatch '^\d{19}$') ('Shop ID format ' + $fmObs.record_id)
  Check ($fmObs.fastmoss_product_url -ceq ('https://www.fastmoss.com' + $fmRaw.Row.product_path)) ('Product URL ' + $fmObs.record_id)
  Check ($fmObs.product_id -ceq ($fmRaw.Row.product_path.Split('/')[-1])) ('Product ID mismatch ' + $fmObs.record_id)
  Check ($fmObs.shop_id -ceq ($fmRaw.Row.shop_path.Split('/')[-1])) ('Shop ID mismatch ' + $fmObs.record_id)
  $fmReconstructed = @(
    $fmObs.display_rank_raw,
    ($fmObs.title + [char]10 + '售价：' + $fmObs.price_raw + [char]10 + '上架时间：' + $fmObs.listing_date),
    $fmObs.country_display,
    ($fmObs.shop_name + [char]10 + '店铺销量：' + $fmObs.shop_sales_raw),
    $fmObs.source_category_name,
    $fmObs.commission_raw,
    $fmObs.sales_3d_raw,
    $fmObs.gmv_3d_raw,
    $fmObs.total_sales_raw,
    $fmObs.total_gmv_raw,
    ''
  )
  for ($fmColumn = 0; $fmColumn -lt 11; $fmColumn++) {
    Check ([string]$fmCells[$fmColumn] -ceq [string]$fmReconstructed[$fmColumn]) ('Raw field mismatch ' + $fmObs.record_id + ' column ' + $fmColumn)
  }
  Check ($fmObs.source_url -ceq $fmRaw.Page.source_url) ('Source URL ' + $fmObs.record_id)
  Check ([int]$fmObs.source_page -eq [int]$fmRaw.Page.page) ('Source page ' + $fmObs.record_id)
  Check ([int]$fmObs.page_position -eq [int]$fmRaw.Row.page_position) ('Row position ' + $fmObs.record_id)
  Check (([datetimeoffset]$fmObs.collected_at_utc).UtcTicks -eq ([datetimeoffset]$fmRaw.Page.collected_at_utc).UtcTicks) ('Capture timestamp ' + $fmObs.record_id)
}
$fmCsvMap = @{}
foreach ($fmCsv in $fmProductsCsv) { $fmCsvMap[$fmCsv.product_id] = $fmCsv }
foreach ($fmJson in $fmProductsJson) {
  Check ($fmJson.product_id -is [string]) ('JSON ID must remain string ' + $fmJson.product_id)
  $fmCsv = $fmCsvMap[$fmJson.product_id]
  Check ($null -ne $fmCsv) ('Missing CSV product ' + $fmJson.product_id)
  foreach ($fmProperty in $fmJson.PSObject.Properties) {
    $fmName = $fmProperty.Name
    $fmValue = $fmProperty.Value
    $fmCsvValue = [string]$fmCsv.$fmName
    if ($fmName -in @('quality_flags', 'occurrences')) {
      $fmParsedCsv = ConvertFrom-Json -InputObject $fmCsvValue
      $fmLeft = ConvertTo-Json -InputObject @($fmValue) -Depth 12 -Compress
      $fmRight = ConvertTo-Json -InputObject @($fmParsedCsv) -Depth 12 -Compress
      Check ($fmLeft -ceq $fmRight) ('JSON array vs CSV ' + $fmJson.product_id + ' ' + $fmName)
    } elseif ($fmValue -is [datetime] -or $fmValue -is [datetimeoffset]) {
      Check (([datetimeoffset]$fmValue).UtcTicks -eq ([datetimeoffset]$fmCsvValue).UtcTicks) ('JSON date vs CSV ' + $fmJson.product_id + ' ' + $fmName)
    } else {
      $fmExpected = if ($null -eq $fmValue) { '' } elseif ($fmValue -is [System.IFormattable]) { $fmValue.ToString($null, [System.Globalization.CultureInfo]::InvariantCulture) } else { [string]$fmValue }
      Check ($fmExpected -ceq $fmCsvValue) ('JSON field vs CSV ' + $fmJson.product_id + ' ' + $fmName)
    }
  }
  $fmOccurrences = @($fmObservations | Where-Object product_id -CEQ $fmJson.product_id)
  Check ($fmOccurrences.Count -eq [int]$fmJson.observation_count) ('Occurrence count ' + $fmJson.product_id)
  $fmLatest = $fmOccurrences | Sort-Object collected_at_utc | Select-Object -Last 1
  Check ($fmLatest.record_id -ceq $fmJson.record_id) ('Latest observation policy ' + $fmJson.product_id)
  foreach ($fmProperty in $fmLatest.PSObject.Properties) {
    if ($fmProperty.Name -eq 'quality_flags') { continue }
    Check ([string]$fmCsv.($fmProperty.Name) -ceq [string]$fmProperty.Value) ('Unique row vs latest observation ' + $fmJson.product_id + ' ' + $fmProperty.Name)
  }
  Check ($null -eq $fmJson.product_impressions -and $null -eq $fmJson.product_clicks -and $null -eq $fmJson.click_attributed_order_numerator -and $null -eq $fmJson.ctr -and $null -eq $fmJson.click_to_order_rate) ('Unavailable funnel metrics must be null ' + $fmJson.product_id)
  if ($fmJson.commission_raw -eq '-') { Check ($null -eq $fmJson.commission_percent_display) ('Missing commission must be null ' + $fmJson.product_id) }
}
Check ($fmIssues.Count -eq 20) 'Expected 20 issue entries (12 metric, 3 scope, 5 duplicate)'
$fmResult = [ordered]@{
  checked_at_utc = [datetime]::UtcNow.ToString('o')
  raw_pages = $fmRawPages.Count
  observations_csv = $fmObservations.Count
  products_csv = $fmProductsCsv.Count
  products_json = $fmProductsJson.Count
  data_issue_entries = $fmIssues.Count
  checked_raw_cells = $fmObservations.Count * 11
  errors = @($fmErrors)
  passed = $fmErrors.Count -eq 0
}
ConvertTo-Json -InputObject $fmResult -Depth 8
if ($fmErrors.Count -gt 0) { exit 1 }

