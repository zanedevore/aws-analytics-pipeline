filter event = "jwt_auth" and ispresent(source_ip) and source_ip != "test-invoke-source-ip"
| stats 
    count(if(status = "allowed", 1, null)) as allowed,
    count(if(status = "denied", 1, null)) as denied
  by source_ip
| sort rejected desc
| limit 20