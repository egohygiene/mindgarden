"""Optional proposal producers; no provider owns review, execution or permissions."""

from copy import deepcopy
from typing import Protocol


class ExtractionProducer(Protocol):
    descriptor: dict
    execution: str

    def extract(self, evidence: dict) -> dict: ...


class RecordedExtractionProducer:
    """Authored outputs keyed by exact selected-input digest, useful without AI."""

    execution = "offline"

    def __init__(self, descriptor: dict, outputs: dict):
        self.descriptor = deepcopy(descriptor)
        self.outputs = deepcopy(outputs)

    def extract(self, evidence: dict) -> dict:
        return deepcopy(self.outputs[evidence["input_sha256"]])
