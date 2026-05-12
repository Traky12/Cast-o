# Verifica DNS (A), HTTPS /health y datos básicos del certificado (emisor, caducidad).
# Uso: .\scripts\windows\verify-dns-ssl.ps1 -PrimaryDomain castuo.tudominio.eu -N8nDomain n8n.castuo.tudominio.eu -HetznerIP 1.2.3.4

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [Alias("Domain")]
    [string] $PrimaryDomain,

    [Parameter(Mandatory)]
    [string] $N8nDomain,

    [string] $HetznerIP = ""
)

$ErrorActionPreference = "Continue"
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
} catch {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}

function Write-Section($t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }

Write-Section "DNS A"
try {
    $a1 = (Resolve-DnsName -Name $PrimaryDomain -Type A -ErrorAction Stop | Where-Object { $_.Type -eq "A" } | Select-Object -First 1).IPAddress
    $a2 = (Resolve-DnsName -Name $N8nDomain -Type A -ErrorAction Stop | Where-Object { $_.Type -eq "A" } | Select-Object -First 1).IPAddress
    Write-Host "$PrimaryDomain -> $a1"
    Write-Host "$N8nDomain -> $a2"
    if ($HetznerIP) {
        if ($a1 -ne $HetznerIP) { Write-Warning "Primary A ($a1) != HetznerIP ($HetznerIP)" }
        if ($a2 -ne $HetznerIP) { Write-Warning "n8n A ($a2) != HetznerIP ($HetznerIP)" }
    }
} catch {
    Write-Error "DNS: $_"
}

function Test-HttpsHealth([string] $HostName, [string] $Path = "/health") {
    $url = "https://$HostName$Path"
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 25 -ErrorAction Stop
        Write-Host "OK $url -> $($resp.StatusCode)"
        if ($resp.Content.Length -lt 500) { Write-Host $resp.Content }
    } catch {
        Write-Warning "FAIL $url -> $_"
    }
}

function Show-CertInfo([string] $HostName) {
    try {
        $req = [System.Net.HttpWebRequest]::Create("https://$HostName/")
        $req.Method = "HEAD"
        $req.Timeout = 20000
        $null = $req.GetResponse()
        $cert = $req.ServicePoint.Certificate
        if ($cert) {
            $c2 = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($cert)
            $days = [math]::Round(($c2.NotAfter - (Get-Date)).TotalDays, 1)
            Write-Host "Cert subject: $($c2.Subject)"
            Write-Host "Issuer: $($c2.Issuer)"
            Write-Host "Válido hasta: $($c2.NotAfter) (~$days días)"
        }
        $req.Abort()
    } catch {
        Write-Warning "Cert $HostName : $_"
    }
}

Write-Section "HTTPS API ($PrimaryDomain)"
Test-HttpsHealth $PrimaryDomain
Show-CertInfo $PrimaryDomain

Write-Section "HTTPS n8n ($N8nDomain)"
try {
    $r = Invoke-WebRequest -Uri "https://$N8nDomain/" -UseBasicParsing -TimeoutSec 25
    Write-Host "OK https://$N8nDomain/ -> $($r.StatusCode)"
} catch {
    Write-Warning "n8n root: $_"
}
Show-CertInfo $N8nDomain

Write-Section "SSL Labs (manual)"
Write-Host "https://www.ssllabs.com/ssltest/analyze.html?d=$PrimaryDomain"
Write-Host "https://www.ssllabs.com/ssltest/analyze.html?d=$N8nDomain"

Write-Host "`nListo." -ForegroundColor Green
