[CmdletBinding()]
param (
  [Parameter(Mandatory = $true, Position = 0)]
  [String]
  $Command
)

function StartMongo() {
  docker run --name mongo -p 27017:27017 -d mongo
}

function StopMongo() {
  docker stop mongo
  docker rm mongo
}

switch ($Command) {
  "start" { StartMongo }
  "stop" { StopMongo }
  "restart" { StopMongo; StartMongo }
  default { Write-Error "Unknown command: $Command" }
}

