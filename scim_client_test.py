from sync_app.client import ClientConfiguration, SCIMClient
from sync_app.scim.patchop import PatchOp, Operation

scim_dev_client_config = ClientConfiguration(
    server_url="https://api.scim.dev/scim/v2/",
    auth_token="B1H3dQcwtO0vZ2AdJ1wVo80uV7S7N6eFWZWQuEOIrhSMxD5L9911sd77fPks"
)


scim_dev_client = SCIMClient(scim_dev_client_config)

# full_users = scim_dev_client.get_users().to_dict()

# print(full_users)

#get yshi user by id
yshi = scim_dev_client.get_user("9b7c6121-fb19-4842-9fbc-b86c26cb1b94").to_dict()

print(yshi)

yshi_active_status = yshi["active"]

#update yshi
update_yshi_op = PatchOp([Operation(op="replace", path="active", value=not yshi_active_status)])

updated_yshi = scim_dev_client.update_user("9b7c6121-fb19-4842-9fbc-b86c26cb1b94", update_yshi_op).to_dict()

print(updated_yshi)