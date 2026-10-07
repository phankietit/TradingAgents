"""Explicit synthetic model responses, never runtime citation inference."""

from copy import deepcopy


def summary_response(raw, snapshot_ids):
    response = deepcopy(raw)
    response["report_contract_version"] = "2.0"
    response["summary_evidence"] = {"claim": response["executive_summary"],
                                    "snapshot_ids": list(snapshot_ids)}
    return response
