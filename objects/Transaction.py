import json

from objects.Object import Object


class Transaction(Object):
    def __init__(self, outputs: list[json], height: int = None, inputs: list[json] = None):  # type: ignore
        super().__init__("transaction")

        if height is None and not inputs:
            raise ValueError("Transaction(): Either height or inputs needs to be defined")

        self.outputs = outputs
        self.height = height
        self.inputs = inputs

        # Hash the whole instance and set its object_id
        self.generate_obj_id()

    @classmethod
    def load_from_json(cls, json_data: json):  # type: ignore
        if "height" in json_data:  # type: ignore
            return cls(
                outputs=json_data["outputs"],  # type: ignore
                height=json_data["height"]  # type: ignore
            )

        return cls(
            outputs=json_data["outputs"],  # type: ignore
            inputs=json_data["inputs"]  # type: ignore
        )
