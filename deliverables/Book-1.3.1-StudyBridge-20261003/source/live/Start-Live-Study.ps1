param(
  [int]$Port = 8767,
  [string]$RuntimeSource = '$env:LIVE_RUNTIME_SOURCE',
  [string]$RuntimeDirectory = '',
  [switch]$PrepareOnly
)
$ErrorActionPreference = 'Stop'
if ($Port -lt 1 -or $Port -gt 65535) { throw 'Port must be in 1..65535.' }
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
if (-not $RuntimeDirectory) { $RuntimeDirectory = Join-Path $workspace 'work\step3-20261003\live-runtime' }
$runtime = [IO.Path]::GetFullPath($RuntimeDirectory)
$source = [IO.Path]::GetFullPath($RuntimeSource)
if ($runtime -eq $source -or $runtime.StartsWith($source + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Runtime copy must not overwrite the original Live installation.' }
if (-not $runtime.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Use a disposable runtime directory inside this workspace.' }
$exe = Join-Path $runtime 'Live.exe'
# A second launch must not overwrite or silently attach to an existing runtime.
# Inspect only; never stop a pre-existing process, including another Live copy.
foreach ($running in @(Get-Process -Name Live -ErrorAction SilentlyContinue)) {
  try { $runningPath = $running.Path } catch { $runningPath = $null }
  if ($runningPath -and [string]::Equals($runningPath, $exe, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'This disposable Live runtime is already running. Close that instance before preparing or starting another.'
  }
}
if (-not $PrepareOnly -and @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue).Count) {
  throw 'Requested Live port is already occupied. The existing listener was not stopped or reused.'
}
if (-not (Test-Path -LiteralPath (Join-Path $source 'Live.exe'))) { throw 'Existing Live Electron runtime not found. Pass -RuntimeSource; do not download private character assets.' }
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'provenance.json') -Raw | ConvertFrom-Json
foreach ($file in $manifest.files) {
  $original = Join-Path (Join-Path $source 'resources\app') $file.path
  if (-not (Test-Path -LiteralPath $original) -or (Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash.ToLower() -ne $file.sha256) {
    throw ('Original Live source differs from the recorded baseline: ' + $file.path)
  }
}
if (-not (Test-Path -LiteralPath $runtime)) {
  Copy-Item -LiteralPath $source -Destination $runtime -Recurse
}
$appDir = Join-Path $runtime 'resources\app'
New-Item -ItemType Directory -Force -Path $appDir | Out-Null
Get-ChildItem -LiteralPath $PSScriptRoot | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $appDir -Recurse -Force }
$private = Join-Path $runtime 'study-private'
New-Item -ItemType Directory -Force -Path $private | Out-Null
$tokenFile = Join-Path $private 'live-token.txt'
if (-not $env:LIVE_STUDY_TOKEN) {
  if (Test-Path -LiteralPath $tokenFile) { $env:LIVE_STUDY_TOKEN = [IO.File]::ReadAllText($tokenFile).Trim() }
  else {
    $bytes = New-Object byte[] 36
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $env:LIVE_STUDY_TOKEN = [Convert]::ToBase64String($bytes)
    [IO.File]::WriteAllText($tokenFile, $env:LIVE_STUDY_TOKEN, [Text.UTF8Encoding]::new($false))
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    & icacls.exe $tokenFile '/inheritance:r' '/grant:r' ($identity + ':(F)') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not restrict local credential file permissions.' }
  }
}
if ($env:LIVE_STUDY_TOKEN.Length -lt 32 -or $env:LIVE_STUDY_TOKEN.Length -gt 256 -or $env:LIVE_STUDY_TOKEN -notmatch '^[\x21-\x7e]+$') { throw 'LIVE_STUDY_TOKEN must be a random 32..256 ASCII non-whitespace credential.' }
$env:LIVE_STUDY_PORT = [string]$Port
$env:LIVE_STUDY_USER_DATA = Join-Path $runtime 'study-user-data'
if ($PrepareOnly) {
  [ordered]@{ event='live_study_runtime_prepared'; executable=$exe; source_unchanged=$true; app=$appDir; port=$Port; model_calls=0; tts_calls=0 } | ConvertTo-Json -Compress
  return
}
if ($env:LIVE_STUDY_TEST_MODE -eq '1') { throw 'Normal launcher does not run hidden test mode. Use the recorded test harness separately.' }
$process = $null
$ready = $false
try {
  $process = Start-Process -FilePath $exe -WorkingDirectory $runtime -WindowStyle Hidden -PassThru
  $deadline = [DateTime]::UtcNow.AddSeconds(15)
  while ([DateTime]::UtcNow -lt $deadline) {
    $process.Refresh()
    if ($process.HasExited) { throw 'The new Live process exited before its authenticated endpoint was ready.' }
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    if (@($listeners | Where-Object { $_.OwningProcess -ne $process.Id }).Count) {
      throw 'Live port ownership changed during startup. The unrelated listener was not stopped or reused.'
    }
    if (@($listeners | Where-Object { $_.LocalAddress -eq '127.0.0.1' -and $_.OwningProcess -eq $process.Id }).Count -eq 1) {
      $response = $null
      try {
        $request = [Net.HttpWebRequest]::Create(('http://127.0.0.1:' + $Port + '/study/health'))
        $request.Proxy = $null
        $request.AllowAutoRedirect = $false
        $request.Timeout = 1000
        $request.ReadWriteTimeout = 1000
        $request.Headers['Authorization'] = 'Bearer ' + $env:LIVE_STUDY_TOKEN
        $response = $request.GetResponse()
        if ([int]$response.StatusCode -ne 200 -or $response.ContentType.Split(';')[0].Trim() -ne 'application/json') { throw 'Invalid Live readiness response.' }
        $stream = $response.GetResponseStream()
        $buffer = New-Object byte[] 4097
        $count = 0
        while ($count -lt $buffer.Length) {
          $read = $stream.Read($buffer, $count, $buffer.Length - $count)
          if ($read -eq 0) { break }
          $count += $read
        }
        if ($count -gt 4096) { throw 'Live readiness response exceeds the limit.' }
        $health = [Text.Encoding]::UTF8.GetString($buffer, 0, $count) | ConvertFrom-Json
        if ($health.status -ne 'local_live_chat' -or $health.renderer_mode -ne 'visible' -or
            $health.model_calls -ne 0 -or $health.tts_calls -ne 0 -or
            -not ($health.generation -is [int] -or $health.generation -is [long]) -or $health.generation -lt 0) {
          throw 'Live readiness contract did not match this normal launcher.'
        }
        $process.Refresh()
        $owned = @(Get-NetTCPConnection -State Listen -LocalAddress '127.0.0.1' -LocalPort $Port -ErrorAction SilentlyContinue |
          Where-Object { $_.OwningProcess -eq $process.Id })
        if (-not $process.HasExited -and $owned.Count -eq 1) { $ready = $true; break }
      } catch {
        # Bounded retry: never include tokens or server-controlled text in diagnostics.
      } finally {
        if ($response) { $response.Close() }
      }
    }
    Start-Sleep -Milliseconds 100
  }
  if (-not $ready) { throw 'The new Live process did not expose its own authenticated visible-mode endpoint within 15 seconds.' }
  [ordered]@{ event='live_study_started'; pid=$process.Id; origin=('http://127.0.0.1:' + $Port); endpoint_ready=$true; listener_owner_verified=$true; renderer_mode='visible'; model_calls=0; tts_calls=0; original_unchanged=$true } | ConvertTo-Json -Compress
} finally {
  if (-not $ready -and $process) {
    try { $process.Refresh(); if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit(3000) | Out-Null } } catch { }
  }
}

