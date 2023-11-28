# Protocol

## Request schema
```{json}
{
    "header": "fetch" | "publish" | "download" | "ping",
    "type": 0,
    "payload": {
        ...
    }
}
```

## Response schema
```{json}
{
    "header": "fetch" | "publish" | "download" | "ping",
    "type": 1,
    "payload": {
        "success": True | False,
        "message": string
        ...
    }
}
```

## Scenarios
### Publish
#### client -request-> server
```{json}
{
    "header": "publish",
    "type": 0,
    "payload": {
        "local_filename": string,
        "remote_filename": string
    }
}
```
#### server -response-> client
```{json}
{
    "header": "publish",
    "type": 1,
    "payload": {
        "success": True | False,
        "message": string,
        "local_filename": string,
        "remote_filename": string
    }
}
```

### Ping
#### server -request-> client
```{json}
{
    "header": "ping",
    "type": 0,
}
```
#### client -response-> server
```{json}
{
    "header": "ping",
    "type": 1,
    "payload": {
        "success": True | False,
        "message": string
    }
}
```

### Fetch
#### client -request-> server
```{json}
{
    "header": "fetch",
    "type": 0,
    "payload": {
        "filename": string
    }
}
```
#### server -response-> client
```{json}
{
    "header": "fetch",
    "type": 1,
    "payload": {
        "success": True | False,
        "message": string,
        "available_clients": [
            {
                "address": string,
            },
            ...
        ]
    }
}
```

### Connect
#### client 1 -request-> client 2
```{json}
{
    "header": "download",
    "type": 0,
    "payload": {
        "filename": string (use file's name on server),
    }
}
```

#### client 2 -response-> client 1
```{json}
{
    "header": "download",
    "type": 1,
    "payload": {
        "success": True | False,
        "message": string,
        "length": int,
    }
}
```