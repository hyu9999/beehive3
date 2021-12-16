DISC_LOGIN_RESPONSE = {
    "data": {
        "type": "token",
        "id": "1",
        "attributes": {
            "token_type": "Bearer",
            "expires_in": 2592000,
            "access_token": "eyJ0eXAiOiJKV1Qi......dj3H9CCSPib6MQtnaT6VNrw",
            "refresh_token": "def50200a26b6a9......10ccbf3c1694084c2d2d276",
        },
    }
}

DISC_THREAD_CREATE_RESPONSE = {
    "data": {
        "type": "threads",
        "attributes": {
            "id": 1,
            "price": 10,
            "attachment_price": 10,
            "title": "title",
            "type": 5,
            "longitude": "116.397469",
            "latitude": "39.908821",
            "location": "北京市",
            "content": "{{$randomWords}} == {{$randomColor}} == {{$randomWords}}",
            "is_anonymous": True,
        },
        "relationships": {
            "category": {"data": {"type": "categories", "id": 6}},
            "attachments": {
                "data": [
                    {"type": "attachments", "id": 1},
                    {"type": "attachments", "id": 2},
                ]
            },
            "question": {
                "data": {
                    "be_user_id": 1,
                    "order_id": "20200918*****1554956",
                    "price": 100,
                    "is_onlooker": True,
                }
            },
        },
    }
}

DISC_USER_GET_RESPONSE = {
    "links": {
        "first": "https://discuz.chat/api/users?filter%5Busername%5D=a%2A%2C%2Ad&page%5Blimit%5D=2",
        "next": "https://discuz.chat/api/users?filter%5Busername%5D=a%2A%2C%2Ad&page%5Blimit%5D=2&page%5Boffset%5D=2",
        "last": "https://discuz.chat/api/users?filter%5Busername%5D=a%2A%2C%2Ad&page%5Blimit%5D=2&page%5Boffset%5D=6",
    },
    "data": [
        {
            "type": "users",
            "id": "1",
            "attributes": {
                "id": 1,
                "username": "username",
                "mobile": "mobile",
                "avatarUrl": "",
                "threadCount": 17,
                "registerIp": "127.0.0.1",
                "lastLoginIp": "127.0.0.1",
                "status": 1,
                "joinedAt": None,
                "expiredAt": None,
                "createdAt": "2019-12-25T17:22:52+08:00",
                "updatedAt": "2019-12-27T16:15:20+08:00",
                "originalMobile": "mobilez",
            },
            "relationships": {"groups": {"data": [{"type": "groups", "id": "1"}]}},
        },
    ],
    "included": [
        {
            "type": "groups",
            "id": "1",
            "attributes": {
                "name": "管理员",
                "type": "",
                "color": "",
                "icon": "",
                "default": 0,
            },
        },
    ],
    "meta": {"total": 7, "size": 2},
}


DISC_USER_PATCH_RESPONSE = {
    "data": {
        "type": "users",
        "id": "1",
        "attributes": {
            "id": 1,
            "username": "username",
            "mobile": "mobile",
            "avatarUrl": "",
            "threadCount": 30,
            "followCount": 0,
            "fansCount": 0,
            "follow": None,
            "status": 0,
            "signature": "这是签名",
            "loginAt": "2020-02-13T11:42:27+08:00",
            "joinedAt": "2019-12-16T19:41:17+08:00",
            "expiredAt": "2020-02-19T18:26:52+08:00",
            "createdAt": "2019-12-16T19:41:17+08:00",
            "updatedAt": "2020-02-13T15:45:15+08:00",
            "canEdit": True,
            "canDelete": True,
            "canWalletPay": True,
            "registerReason": "",
            "banReason": "",
            "originalMobile": "mobile",
            "registerIp": "192.168.10.1",
            "lastLoginIp": "192.168.10.1",
            "identity": "",
            "realname": "",
            "paid": None,
            "payTime": None,
            "unreadNotifications": 8,
            "usernameBout": 0,
            "typeUnreadNotifications": {"replied": 8},
        },
    }
}
