# Env variables
$Subject = $env:Subject
$Shared_Secret = $env:ClientSecret
$Audience = $env:Audience
$AuthUrl = $env:AuthUrl
$ApiUrl = $env:ApiUrl

# Get JWT token
$AuthBody = @{
    client_id = $Subject
    client_secret = $Shared_Secret
    audience = $Audience
} | ConvertTo-Json

$Token = Invoke-RestMethod -Method POST -Uri $AuthUrl -Body $AuthBody -ContentType "application/json" -ErrorAction Stop

# Send event
$Headers = @{
    Authorization = "Bearer $($Token.access_token)"
    'X-Subject' = $Subject
}

$EventBody = @{
    event_type = 'join'
    player_id = '123'
    server_id = $Subject
    ts = '2025-09-12T18:04:00Z'
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri $ApiUrl -Headers $Headers -Body $EventBody -ContentType "application/json"