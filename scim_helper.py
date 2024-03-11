from sync_app.client import ClientConfiguration, SCIMClient
from sync_app.scim.patchop import PatchOp, Operation
from sync_app.scim.user import User, Name, Email
from sync_app.scim.group import Group
from sync_app.scim.resource import ResourceMeta
from uuid import uuid5, NAMESPACE_X500


def create_user_with_group(name, group, client):
    first_name = name.split()[0].capitalize()
    last_name = name.split()[1].capitalize()
    uuid = uuid5(
        NAMESPACE_X500,
        "uid={}.{},DC=dundermifflin,DC=com".format(first_name, last_name),
    )

    new_user = User(
        meta=ResourceMeta.create_meta(
            "User",
            "https://duo.local/Users/{}".format(
                str(uuid),
            ),
        ),
        user_id=uuid,
        displayName="{} {}".format(first_name, last_name),
        active=True,
        userName="{}{}".format(first_name[0].lower(), last_name.lower()),
        name=Name(givenName=first_name, familyName=last_name),
        emails=[
            Email(
                value="{}.{}@dundermifflin.com".format(
                    first_name.lower(), last_name.lower()
                ),
                type="work",
                primary=True,
            )
        ],
        groups=[group],
    )
    response = client.create_user(new_user)
    return response.to_dict()


def create_group(displayName, client):
    new_group = Group(
        displayName=displayName,
        group_id=uuid5(NAMESPACE_X500, "cn={},DC={},DC=com".format(displayName, ''.join(displayName.split()).lower())),
        meta=ResourceMeta.create_meta(
            "Group",
            "https://duo.local/Groups/{}".format(
                str(uuid5(NAMESPACE_X500, "cn={},DC={},DC=com".format(displayName,''.join(displayName.split()).lower())))
            ),
        ),
    )
    response = client.create_group(new_group)

    return response.to_dict()


def course_setup(auth_token):
    server_url = "https://api.scim.dev/scim/v2/"

    scim_dev_client_config = ClientConfiguration(
        server_url=server_url, auth_token=auth_token
    )
    scim_dev_client = SCIMClient(scim_dev_client_config)

    # First create the group
    group = create_group("Dunder Mifflin", scim_dev_client)

    group_id = group["id"]

    # Now create the users
    users = [
        "Micheal Scott",
        "Jim Halpert",
        "Dwight Schrute",
        "Pam Beesly",
        "Ryan Howard",
        "Andy Bernard",
        "Kevin Malone",
        "Oscar Martinez",
        "Angela Martin",
        "Stanley Hudson",
        "Phyllis Vance",
        "Meredith Palmer",
        "Creed Bratton",
        "Kelly Kapoor",
        "Toby Flenderson",
    ]
    user_ids = {}

    for user in users:
        response = create_user_with_group(user, group, scim_dev_client)
        user_ids[user] = response["id"]

    return group_id, user_ids
