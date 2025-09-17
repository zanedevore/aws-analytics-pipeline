filter event = "jwt_issue" and status = "rejected"
| stats count() as rejects by sourceIp
| sort rejects desc
| limit 20