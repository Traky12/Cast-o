# Demo ingest para stand ICEX (no saturar: DEMO_INTERVAL_SEC)
$Base = if ($env:CASTUO_API) { $env:CASTUO_API } else { "http://127.0.0.1:8000" }
$Interval = if ($env:DEMO_INTERVAL_SEC) { [int]$env:DEMO_INTERVAL_SEC } else { 2 }
while ($true) {
    $t = 20 + (Get-Random -Maximum 15)
    $h = 50 + (Get-Random -Maximum 30)
    $r = 500 + (Get-Random -Maximum 400)
    $c = 350 + (Get-Random -Maximum 150)
    $at = @("agrovoltaico", "hidroponico", "medicinal")[(Get-Random -Maximum 3)]
    $body = @{
        agent_type = $at
        sensor_data = @{
            temperature = $t
            humidity = $h
            radiation = $r
            co2 = $c
        }
    } | ConvertTo-Json -Compress
    try {
        Invoke-RestMethod -Uri "$Base/agents/gemelo/ingest" -Method Post -ContentType "application/json" -Body $body
    } catch {
        Write-Warning $_
    }
    Start-Sleep -Seconds $Interval
}
