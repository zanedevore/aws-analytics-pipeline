-- Athena query to find players with server duration greater than 10 minutes (600 seconds)

SELECT 
    event_id,  
    player_id, 
    event_type, 
    ts, 
    CAST(properties['player_server_duration'] AS integer) AS duration
FROM "{DATABASE}"."{TABLE}"
WHERE CAST(properties['player_server_duration'] AS integer) > 600