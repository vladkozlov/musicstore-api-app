# musicstoreapi-test-task

Musicstore asynchronous example based on Python 3.6, aiohttp and asyncpg.

## **Requirements**

* Postgres 9.6 or above with extensions support (uuid-ossp required)
* Python 3.6
* aiohttp 3.3.2
* asyncpg 0.16
* json
* jsonschema 2.6
* yaml 3.12

## **Installation**

1. Edit configuration files in ```config``` folder where ```app.yaml``` is used for server configuration and ```posgres_cfg.yaml``` is for database connection.
2. You can manage config files in ```settings.py``` file.
3. To initialize database execute ```init_db.py``` file.
4. To run server loop execute ```main.py``` file.

## **API**

## Api key validation

### Key is valid

```json
{
    "email" : "email@email.com",
    "first_name" : "Name",
    "last_name" : "Surname"
}
```

### Validation failed

```json
{
    "err" : "error message"
}
```

## User

### User information request

#### Request

```http
GET users?api_key=296c7f23-cb66-4dad-bc99-36a0c796dabb
```

#### JSON response

```json
{
    "email" : "email@email.com",
    "first_name" : "Name",
    "last_name" : "Surname"
}
```

### Create new user

#### Request POST

```http
POST users?email=email@email.com&first_name=Name&last_name=Surname
```

#### Response success

```json
{
    "api_key" : "296c7f23-cb66-4dad-bc99-36a0c796dabb"
}
```

#### Response error

``` json
{
    "err" : "error message"
}
```

### Delete user

#### Request DELETE

```http
DELETE users?api_key=296c7f23-cb66-4dad-bc99-36a0c796dabb
```

#### Response success

```json
{
    "status" : true
}
```

#### Response error

``` json
{
    "err" : "error message"
}
```

## Tracks

### Get all user tracks using api_key

#### Request POST

```http
GET tracks?api_key=296c7f23-cb66-4dad-bc99-36a0c796dabb
```

#### Response success

```json
[
    {
        "id": "17",
        "name": "One more new track",
        "album_id": "9",
        "created": "2018-07-08 11:36:51.118071",
        "updated": "2018-07-08 11:36:51.118071"
    },
    {
        "id": "18",
        "name": "My little pig",
        "album_id": "9",
        "created": "2018-07-08 12:08:51.105279",
        "updated": "2018-07-08 12:08:51.105279"
    }
]
```

#### Response error

```json
{
    "err" : "error message"
}
```

### Add track to user by api_key

#### Request POST

```http
POST tracks?api_key=296c7f23-cb66-4dad-bc99-36a0c796dabb&name=My New Track&album_id=1
```

#### Response success

```json
{
    "status": true
}
```

#### Response error

```json
{
    "err" : "error message"
}
```

### Delete track from user lib

#### Request POST

```http
DELETE tracks?api_key=296c7f23-cb66-4dad-bc99-36a0c796dabb&id=1
```

#### Response success

```json
{
    "status": true
}
```

#### Response error

```json
{
    "err" : "error message"
}
```

### Update track in user lib

#### Request POST

```http
PUT tracks?api_key=296c7f23-cb66-4dad-bc99-36a0c796dabb&id=1&name=My New New Track&album_id=2
```

#### Response success

```json
{
    "status": true
}
```

#### Response error

```json
{
    "err" : "error message"
}
```

## Albums

### Create album

```http
POST albums?api_key=296c7f23-cb66-4dad-bc99-36a0c796dabb

&name=My new album
&metadata={
        "release_year" : 1984,
        "awards" : [
            "Grammy",
            "MTV music awards"
        ],
        "publisher": "Warner music",
        "ost": [
             "Silent Hill",
             "Supernatural"  
        ]
}
```

```INFO``` Metadata is a json string and validated in ```models/albums.py``` using json schema

#### Response success


```json
{
    "status": true
}
```

#### Response error

```json
{
    "err" : "error message"
}
```

### Get all user albums by api_key

```http
GET albums?api_key=296c7f23-cb66-4dad-bc99-36a0c796dabb
```

#### Response success


```json
[
    {
        "id": "1",
        "name": "My new album",
        "metadata": {
            "ost": [
                "Silent hill",
                "Supernatural"
            ],
            "awards": [
                "Grammy",
                "MTV music awards"
            ],
            "publisher": "Warner music",
            "release_year": 1984
        },
        "created": "2018-07-06 21:03:56.347246",
        "updated": "2018-07-08 10:52:08.806811"
    }
]
```

#### Response error

```json
{
    "err" : "error message"
}
```

