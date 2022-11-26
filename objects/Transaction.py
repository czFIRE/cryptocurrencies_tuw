import json

from objects.Object import Object

class Transaction(Object):
    def __init__(self, outputs: list[json], height: int = None, inputs: list[json] = None):
        super().__init__("transaction")

        if height is None and not inputs:
            raise ValueError("Transaction(): Either height or inputs needs to be defined")

        self.outputs = outputs
        self.height = height
        self.inputs = inputs

        # Hash the whole instance and set its object_id
        self.generate_obj_id()

    @classmethod
    def load_from_json(cls, json_data: json):
        if "height" in json_data:
            return cls(
                outputs=json_data["outputs"],
                height=json_data["height"]
            )

        return cls(
            outputs=json_data["outputs"],
            inputs=json_data["inputs"]
        )
