import requests
from datetime import datetime
import json
import pytest
from uuid import uuid1

# TODO app will have to take a DB path as a parameter
# TODO assertions

SCIMBaseURL = "http://localhost:13289/scim/v2"

GET_headers = {
    "Accept-Charset": "utf-8",
    "Content-Type": "application/scim+json; charset=utf-8",
    "Accept": "application/scim+json",
    # "Authorization": "{{auth}}",
    "User-Agent": "OKTA SCIM Integration",
}
POST_headers = {
    "Content-Type": "application/json",
    # "Authorization": "{{auth}}",
    "Accept": "application/scim+json; charset=utf-8",
}


@pytest.fixture
def new_test_user():
    given_name = "Test"
    family_name = "User"
    user_name = "newTestUser"
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": user_name,
        "name": {
            "givenName": given_name,
            "familyName": family_name,
        },
        "emails": [
            {
                "primary": True,
                "value": "newTestUser@example.com",
                "type": "work",
            }
        ],
        "displayName": "Test User",
        "active": True,
    }


@pytest.fixture
def new_test_group():
    return {
        "id": str(uuid1()),
        "meta": {
            "resourceType": "Group",
            "created": str(datetime.now()),
            "lastModified": str(datetime.now()),
            "version": "1",
            "location": "http://example.com",
        },
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "test group",
        "members": [],
    }


def assert_not_empty(d: dict, s: str):
    assert s in d
    assert d[s]


scim = {}


@pytest.mark.order(0)
def test_create_user(new_test_user):
    r = requests.post(
        f"{SCIMBaseURL}/Users",
        data=json.dumps(new_test_user),
        headers=POST_headers,
    )
    assert r.status_code == 201
    response_json = r.json()
    assert response_json["active"] == True
    assert_not_empty(response_json, "id")
    assert response_json["name"]["familyName"] == new_test_user["name"]["familyName"]
    assert response_json["name"]["givenName"] == new_test_user["name"]["givenName"]
    assert "urn:ietf:params:scim:schemas:core:2.0:User" in response_json["schemas"]
    assert response_json["userName"] == new_test_user["userName"]

    scim["idUserOne"] = response_json["id"]
    scim["testUserEmail"] = response_json["emails"][0]["value"]


@pytest.mark.order(1)
def test_get_first_user(new_test_user):
    r = requests.get(
        f"{SCIMBaseURL}/Users",
        params={"count": 1, "startIndex": 1},
        headers=GET_headers,
    )
    assert r.status_code == 200
    response_json = r.json()
    assert len(response_json["Resources"]) > 0
    assert ["urn:ietf:params:scim:api:messages:2.0:ListResponse"] == response_json[
        "schemas"
    ]
    assert isinstance(response_json["itemsPerPage"], int)
    assert isinstance(response_json["startIndex"], int)
    assert isinstance(response_json["totalResults"], int)

    first_user = response_json["Resources"][0]

    for field in ["id", "userName", "active"]:
        assert_not_empty(first_user, field)

    for field in ["givenName", "familyName"]:
        assert_not_empty(first_user["name"], field)

    assert_not_empty(first_user["emails"][0], "value")

    scim["ISVUserid"] = first_user["id"]


@pytest.mark.order(2)
def test_get_user_by_id():
    user_id = scim["ISVUserid"]
    r = requests.get(
        f"{SCIMBaseURL}/Users/{user_id}",
        headers=GET_headers,
    )
    assert r.status_code == 200
    response_json = r.json()
    assert_not_empty(response_json, "id")
    assert "name" in response_json
    assert_not_empty(response_json["name"], "familyName")
    assert_not_empty(response_json["name"], "givenName")
    assert_not_empty(response_json, "userName")
    assert_not_empty(response_json, "active")
    assert_not_empty(response_json["emails"][0], "value")
    assert response_json["id"] == scim["ISVUserid"]


# TODO we may not use this since I don't know if we'll be implementing filtering
@pytest.mark.order(3)
def test_get_bad_email():
    r = requests.get(
        f"{SCIMBaseURL}/Users",
        params={"filter": 'userName eq "notvalidemail@example.com"'},
        headers=GET_headers,
    )
    assert r.status_code == 200
    response_json = r.json()
    assert ["urn:ietf:params:scim:api:messages:2.0:ListResponse"] == response_json[
        "schemas"
    ]
    assert response_json["totalResults"] == 0


def test_get_nonexistent_user():
    r = requests.get(
        f"{SCIMBaseURL}/Users/null",
        headers=GET_headers,
    )
    assert r.status_code == 404
    response_json = r.json()
    assert_not_empty(response_json, "detail")
    assert ["urn:ietf:params:scim:api:messages:2.0:Error"] == response_json["schemas"]


# TODO we may not use this since I don't know if we'll be implementing filtering
@pytest.mark.order(4)
def test_get_random_email_user():
    r = requests.get(
        f"{SCIMBaseURL}/Users",
        params={"filter": 'userName eq "randomEmail@example.com"'},
        headers=GET_headers,
    )
    assert r.status_code == 200
    response_json = r.json()
    assert response_json["totalResults"] == 0
    assert ["urn:ietf:params:scim:api:messages:2.0:ListResponse"] == response_json[
        "schemas"
    ]


@pytest.mark.order(6)
def test_fetch_created_user():
    user_email = scim["ISVUserid"]
    r = requests.get(
        f"{SCIMBaseURL}/Users/{user_email}",
        headers=GET_headers,
    )
    assert r.status_code == 200
    response_json = r.json()
    assert response_json["userName"] == "newTestUser"
    assert response_json["name"]["familyName"] == "User"
    assert response_json["name"]["givenName"] == "Test"


@pytest.mark.order(7)
def test_create_duplicate_user():
    r = requests.post(
        f"{SCIMBaseURL}/Users",
        data=json.dumps(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "newTestUser",
                "name": {
                    "givenName": "Test",
                    "familyName": "User",
                },
                "emails": [
                    {
                        "primary": True,
                        "value": "newTestUser@example.com",
                        "type": "work",
                    }
                ],
                "displayName": "Test User",
                "active": True,
            }
        ),
        headers=POST_headers,
    )
    assert r.status_code == 409


# TODO we may not use this since I don't know if we'll be implementing filtering
@pytest.mark.order(8)
def test_user_case_sensitivity():
    user_email = scim["testUserEmail"]
    r = requests.get(
        f"{SCIMBaseURL}/Users",
        params={"filter": f'userName eq "{user_email}"'},
        headers=GET_headers,
    )
    assert r.status_code == 200


@pytest.mark.order(9)
def test_create_group(new_test_group):
    r = requests.post(
        f"{SCIMBaseURL}/Groups",
        data=json.dumps(new_test_group),
        headers=POST_headers,
    )
    assert r.status_code == 201
    response_json = r.json()
    assert_not_empty(response_json, "id")
    assert response_json["members"] == []
    assert response_json["displayName"] == new_test_group["displayName"]
    assert "urn:ietf:params:scim:schemas:core:2.0:Group" in response_json["schemas"]

    scim["idGroupOne"] = response_json["id"]


@pytest.mark.order(10)
def test_groups():
    r = requests.get(
        f"{SCIMBaseURL}/Groups",
        headers=GET_headers,
    )
    assert r.status_code == 200
    assert r.elapsed.total_seconds() < 600
    response_json = r.json()
    max = response_json["totalResults"]
    assert max >= 1 and isinstance(response_json["Resources"], list)


if __name__ == "__main__":
    import sys
    from pytest import main

    main(sys.argv)
