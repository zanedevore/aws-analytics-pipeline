Param (
    [Parameter(Mandatory)][string]$function
)

$env:AWS_SHARED_CREDENTIALS_FILE = "..\..\aws-credentials\credentials.txt"
$env:AWS_CONFIG_FILE = "..\..\aws-credentials\config.txt"

$Path = "../lambda/$function"

Set-Location $Path

Compress-Archive -Path (gci -path . -File -Recurse) -DestinationPath "function.zip" -Force

aws lambda update-function-code --function-name $function --zip-file fileb://function.zip