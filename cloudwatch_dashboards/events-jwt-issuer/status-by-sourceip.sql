filter event = "jwt_issue" and ispresent(sourceIp) and ispresent(sourceIp) and sourceIp != "test-invoke-source-ip"
| stats 
    count(if(status = "approved", 1, null)) as approved,
    count(if(status = "rejected", 1, null)) as rejected
  by sourceIp
| sort rejected desc
| limit 20