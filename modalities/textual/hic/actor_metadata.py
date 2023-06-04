from typing import List

import marshmallow_dataclass
from marshmallow import pre_load

from datagen.modalities.textual.common.identity_label import IdentityLabel
from datagen.modalities.textual.common.sixdof import SixDOF


@marshmallow_dataclass.dataclass
class ActorMetadata:
    identity_id: str
    identity_label: IdentityLabel
    head_six_dof: SixDOF


@marshmallow_dataclass.dataclass
class Actors:
    identities: List[ActorMetadata]

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        identities = []
        for actor_identity_id, actor_metadata in in_data["identities"].items():
            actor_metadata = {
                "identity_id": actor_identity_id,
                "identity_label": {
                    "age": actor_metadata["age"],
                    "ethnicity": actor_metadata["ethnicity"],
                    "gender": actor_metadata["gender"],
                },
                "head_six_dof": actor_metadata["head_six_dof"],
            }
            identities.append(actor_metadata)
        return {"identities": identities}

    def __getitem__(self, key):
        return next(identity for identity in self.identities if identity.identity_id == key)

    def __iter__(self):
        for identity in self.identities:
            yield identity
