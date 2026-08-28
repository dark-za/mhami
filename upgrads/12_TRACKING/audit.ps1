$sections = @{
  '01_CRITICAL_FIXES'     = 14
  '02_HIGH_PRIORITY'      = 8
  '03_FRONTEND_REBUILD'   = 6
  '04_BACKEND_HARDENING'  = 6
  '05_INFRASTRUCTURE'     = 5
  '06_QUALITY_ASSURANCE'  = 5
  '07_COMPLIANCE_LEGAL'   = 6
  '08_PILOT_OPERATIONS'   = 6
  '09_DOCUMENTATION'      = 5
  '10_PHASE13_PREP'       = 4
}

$totalPlanned = 0
$totalDirs    = 0
$totalFull    = 0
$totalPartial = 0
$totalNone    = 0
$totalMissingFiles = 0
$totalMissingPackages = 0

foreach ($s in $sections.GetEnumerator()) {
  $dir = "e:\APP\mhame\mhami-main\upgrads\$($s.Key)"
  $pkgs = @(Get-ChildItem $dir -Directory -ErrorAction SilentlyContinue)
  $full = 0; $partial = 0; $none = 0; $sectionMissing = 0
  foreach ($p in $pkgs) {
    $files = @(Get-ChildItem $p.FullName -File -ErrorAction SilentlyContinue)
    $has = @{ d = $false; v = $false; g = $false; i = $false; t = $false; r = $false }
    foreach ($f in $files) {
      switch -Regex ($f.Name) {
        '^00_DISCOVERY\.md$'     { $has.d = $true }
        '^01_VERIFICATION\.md$'  { $has.v = $true }
        '^02_GOAL\.md$'          { $has.g = $true }
        '^03_IMPLEMENTATION\.md$' { $has.i = $true }
        '^04_TESTING\.md$'       { $has.t = $true }
        '^04_RESULTS\.md$'       { $has.r = $true }
      }
    }
    $count = @($has.d, $has.v, $has.g, $has.i, $has.t, $has.r) | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
    if     ($count -eq 6) { $full++ }
    elseif ($count -ge 1) { $partial++ ; $missing = 6 - $count ; $totalMissingFiles += $missing ; $sectionMissing += $missing }
    else                  { $none++    ; $totalMissingFiles += 6 ; $sectionMissing += 6 }
  }
  $missingPkgs = $s.Value - $pkgs.Count
  $totalMissingPackages += $missingPkgs
  $totalMissingFiles    += ($missingPkgs * 6)
  $totalPlanned += $s.Value
  $totalDirs    += $pkgs.Count
  $totalFull    += $full
  $totalPartial += $partial
  $totalNone    += $none
  [PSCustomObject]@{
    Section        = $s.Key
    Planned        = $s.Value
    Dirs           = $pkgs.Count
    Full           = $full
    Partial        = $partial
    None           = $none
    MissingPkgs    = $missingPkgs
    MissingFiles   = $sectionMissing + ($missingPkgs * 6)
  } | Format-Table -AutoSize | Out-String
}

"==="
"PLANNED:           $totalPlanned"
"DIRS:              $totalDirs"
"FULL:              $totalFull"
"PARTIAL:           $totalPartial"
"BLANK:             $totalNone"
"MISSING PACKAGES:  $totalMissingPackages"
"REMAINING FILES:   $totalMissingFiles"
