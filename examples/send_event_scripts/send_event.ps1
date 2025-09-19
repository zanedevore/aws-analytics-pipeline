# Env variables
$Subject = $env:Subject
$Shared_Secret = $env:ClientSecret
$Audience = $env:Audience
$AuthUrl = $env:AuthUrl
$ApiUrl = $env:ApiUrl

# Get JWT token
$AuthBody = @{
    client_id = $Subject
    audience = $Audience
} | ConvertTo-Json

$Headers = @{
    'x-client-secret' = $Shared_Secret
    'Content-Type' = 'application/json'
}

Write-Host "Requesting token..."

$Token = Invoke-RestMethod -Method POST -Uri $AuthUrl -Body $AuthBody -Headers $Headers -ErrorAction Stop

Write-Host "Token received: $($Token.access_token.Substring(0, 10))..."

# Send event
$Headers = @{
    Authorization = "Bearer $($Token.access_token)"
    'X-Subject' = $Subject
}

$EventBody = @{
    device = 'pc'
    event_id = "$Subject-000001"
    event_type = 'join'
    player_id = '123'
    server_id = $Subject
    server_version = '1.0.0'
    ts = '2025-09-19T18:04:00Z'
    properties = @{
        player_action = 'purchase'
        item = 'truck'
        player_server_duration = "1200"
    }
} | ConvertTo-Json

Write-Host "Sending event..."

Invoke-RestMethod -Method POST -Uri $ApiUrl -Headers $Headers -Body $EventBody -ContentType "application/json"

Write-Host "Event sent successfully: $($EventBody | ConvertFrom-Json | ConvertTo-Json -Depth 10)"