from typing import Mapping, Literal, Optional, Iterable, Any
from sync_app.scim.resource import Resource
from dataclasses import dataclass, asdict

PATCHOP_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"


@dataclass
class Operation:
    op: Literal["add", "remove", "replace"]
    path: Optional[str]
    value: Any


class PatchOp(Resource):
    operations: Iterable[Operation]

    def __init__(self, operations: Iterable[Operation]):
        super().__init__([PATCHOP_SCHEMA])
        self.operations = operations

    @staticmethod
    def from_dict(resource: Mapping) -> "PatchOp":
        return PatchOp(operations=[Operation(**o) for o in resource["Operations"]])

    def to_dict(self) -> Mapping:
        return {
            "schemas": [PATCHOP_SCHEMA],
            "Operations": [asdict(o) for o in self.operations],
        }
