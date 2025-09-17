fields @timestamp, status, reason, client_id, sourceIp, request_id
| filter event = "jwt_issue" and status = "approved"
| sort @timestamp desc
| dedup request_id
| limit 500