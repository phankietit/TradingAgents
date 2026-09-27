"""Strict whole-message JSON parsing shared by initial output and repair."""

import json


def validated_json_object(content):
    if not isinstance(content, str):
        raise ValueError("structured content must be text")
    candidate = content.strip()
    if candidate.startswith("```json\n") and candidate.endswith("\n```"):
        candidate = candidate[8:-4]

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    def reject_constant(_):
        raise ValueError("non-JSON numeric constant")

    payload = json.loads(candidate, object_pairs_hook=unique_object, parse_constant=reject_constant)
    if not isinstance(payload, dict):
        raise ValueError("structured content must be one JSON object")
    return candidate


def parse_structured_content(schema, content):
    candidate = validated_json_object(content)
    # Keep Pydantic's JSON-mode semantics (notably strict date/UUID schemas),
    # after independently rejecting ambiguous/non-JSON envelopes above.
    return schema.model_validate_json(candidate)
