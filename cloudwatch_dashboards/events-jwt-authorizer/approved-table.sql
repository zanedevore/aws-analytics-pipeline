fields @timestamp, status, reason, client_id, source_ip, request_id
| filter event = "jwt_auth" and status = "allowed"
| sort @timestamp desc
| dedup request_id
| limit 500