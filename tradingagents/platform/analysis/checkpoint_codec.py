"""Restricted JSON transport for snapshot checkpoints, not a recovery authority.

No storage, saver, API or retry is enabled here. The caller must separately
validate the full research fingerprint and owner/lease before using these bytes.
Messages are removed at encode, including start/pending writes; decode rejects
them. No pickle, object import, typed-object hook or arbitrary metadata is used.
"""

import json
import math
from datetime import datetime
from uuid import UUID

from langgraph.checkpoint.base import CheckpointTuple

from tradingagents.agents.research_schemas import (
    SnapshotPortfolioDecision,
    SnapshotPortfolioDecisionV2,
    SnapshotReportDraft,
    SnapshotReportDraftV2,
)
from tradingagents.agents.utils.agent_states import InvestDebateState, RiskDebateState

MAX_CHECKPOINT_BYTES = 16 * 1024 * 1024
MAX_TEXT = 1_000_000
TEXT_CHANNELS = frozenset({"company_of_interest", "asset_type", "instrument_context", "trade_date",
    "sender", "market_report", "sentiment_report", "news_report", "fundamentals_report",
    "investment_plan", "trader_investment_plan", "final_trade_decision", "past_context",
    "portfolio_context"})
STATE_CHANNELS = TEXT_CHANNELS | {"messages", "research_only", "structured_diagnostics",
    "investment_debate_state", "risk_debate_state", "structured_decision", "structured_draft",
    "rejected_structured_decision"}


class CheckpointCodecError(ValueError):
    """Safe fixed diagnostic; never includes checkpoint/model contents."""


def _reject():
    raise CheckpointCodecError("snapshot checkpoint is invalid or incompatible")


def _keys(value, allowed, required=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or not value.keys() <= allowed:
        _reject()


def _text(value, limit=MAX_TEXT):
    if type(value) is not str or len(value) > limit:
        _reject()
    return value


def _plain(value, depth=0):
    """Validate JSON primitives without converting arbitrary Python objects."""
    if depth > 24:
        _reject()
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is str:
        return _text(value)
    if type(value) in (list, tuple):
        if len(value) > 4096:
            _reject()
        return [_plain(item, depth + 1) for item in value]
    if type(value) is dict:
        if len(value) > 4096:
            _reject()
        return {_text(key, 256): _plain(item, depth + 1) for key, item in value.items()}
    _reject()


class SnapshotCheckpointCodec:
    """Native routing/version fidelity with a bounded, fail-closed JSON envelope.

    A supplied digest is only a binding assertion, not proof it was constructed
    from all required inputs. There is deliberately no default fingerprint.
    """

    def __init__(self, *, fingerprint: str, nodes):
        if (type(fingerprint) is not str or len(fingerprint) != 64
                or any(ch not in "0123456789abcdef" for ch in fingerprint)):
            _reject()
        self.fingerprint = fingerprint
        self.nodes = frozenset(nodes)
        if not self.nodes or any(type(node) is not str or not node or node.startswith("__")
                                 or len(node) > 100 for node in self.nodes):
            _reject()

    def _channel_name(self, name):
        if name in STATE_CHANNELS or name == "__start__":
            return
        if type(name) is str and name.startswith("branch:to:") and name[10:] in self.nodes:
            return
        _reject()

    def _diagnostics(self, value):
        if not isinstance(value, list) or len(value) > 256:
            _reject()
        result = _plain(value)
        for row in result:
            _keys(row, {"agent", "phase", "error_type", "fields", "checks", "binding_keys"},
                  {"agent", "phase", "error_type", "fields"})
            for key in ("agent", "phase", "error_type"):
                _text(row[key], 100)
            if type(row["fields"]) is not list or len(row["fields"]) > 32:
                _reject()
            for field in row["fields"]:
                _keys(field, {"field", "code"}, {"field", "code"})
                _text(field["field"], 512)
                _text(field["code"], 100)
            for key in ("checks", "binding_keys"):
                if key in row:
                    if type(row[key]) is not list or len(row[key]) > 100:
                        _reject()
                    for item in row[key]:
                        _text(item, 200)
        return result

    def _state_value(self, name, value, *, encoding):
        if name == "messages":
            if not encoding and value != []:
                _reject()
            return []  # Do not inspect/serialize arbitrary model message objects.
        if name in TEXT_CHANNELS:
            if name == "past_context" and value != "":
                _reject()  # Snapshot recovery cannot import CLI memory lessons.
            return _text(value)
        if name == "research_only":
            if value is not True:
                _reject()
            return True
        if name == "structured_diagnostics":
            return self._diagnostics(value)
        if name in {"investment_debate_state", "risk_debate_state"}:
            fields = (InvestDebateState if name == "investment_debate_state" else RiskDebateState).__annotations__
            # Original debate nodes replace the whole dict and omit the judge
            # field until a manager has run. Preserve that absence exactly.
            _keys(value, set(fields), set(fields) - {"judge_decision"})
            for key, item in value.items():
                if key == "count":
                    if type(item) is not int or not 0 <= item <= 10000:
                        _reject()
                else:
                    _text(item)
            return dict(value)
        if name in {"structured_decision", "structured_draft", "rejected_structured_decision"}:
            if value is None:
                return None
            # All rejected candidates reaching the native state are schema-valid
            # narrative/draft objects, not provider fallback text or exceptions.
            if not isinstance(value, dict):
                _reject()
            v2 = value.get("report_contract_version") == "2.0"
            draft = SnapshotReportDraftV2 if v2 else SnapshotReportDraft
            report = SnapshotPortfolioDecisionV2 if v2 else SnapshotPortfolioDecision
            schemas = (draft,) if name == "structured_draft" else (
                (draft, report) if name == "rejected_structured_decision" else (report,))
            for schema in schemas:
                try:
                    if not isinstance(value, dict):
                        _reject()
                    normalized = schema.model_validate(value).model_dump(mode="json")
                    # Nested typed field conversion is restricted to known schemas.
                    _plain(normalized)
                    return normalized
                except (ValueError, TypeError):
                    continue
            _reject()
        _reject()

    def _values(self, values, *, encoding):
        if not isinstance(values, dict):
            _reject()
        result = {}
        for name, value in values.items():
            self._channel_name(name)
            if name in STATE_CHANNELS:
                result[name] = self._state_value(name, value, encoding=encoding)
            elif name == "__start__":
                _keys(value, STATE_CHANNELS, {"research_only"})
                result[name] = {key: self._state_value(key, item, encoding=encoding)
                                for key, item in value.items()}
            else:
                if value is not None:
                    _reject()
                result[name] = None
        return result

    def _versions(self, versions):
        if not isinstance(versions, dict):
            _reject()
        for name, version in versions.items():
            self._channel_name(name)
            if type(version) not in (str, int, float) or (type(version) is float and not math.isfinite(version)):
                _reject()
            if isinstance(version, str):
                _text(version, 256)
        return dict(versions)

    def _config(self, config):
        _keys(config, {"configurable"}, {"configurable"})
        fields = config["configurable"]
        _keys(fields, {"thread_id", "checkpoint_ns", "checkpoint_id"}, {"thread_id"})
        if not _text(fields["thread_id"], 200) or fields.get("checkpoint_ns", "") != "":
            _reject()  # No nested graph/subgraph checkpoint contract yet.
        if "checkpoint_id" in fields:
            UUID(fields["checkpoint_id"])
        return {"configurable": dict(fields)}

    def _validate(self, envelope, *, encoding):
        _keys(envelope, {"schema_version", "fingerprint", "config", "checkpoint", "metadata",
                         "parent_config", "pending_writes"},
              {"schema_version", "fingerprint", "config", "checkpoint", "metadata", "parent_config", "pending_writes"})
        if envelope["schema_version"] != "snapshot-checkpoint-json-v1" or envelope["fingerprint"] != self.fingerprint:
            _reject()
        config = self._config(envelope["config"])
        parent = self._config(envelope["parent_config"]) if envelope["parent_config"] is not None else None
        if parent and parent["configurable"]["thread_id"] != config["configurable"]["thread_id"]:
            _reject()
        cp = envelope["checkpoint"]
        keys = {"v", "id", "ts", "channel_values", "channel_versions", "versions_seen", "updated_channels"}
        _keys(cp, keys, keys)
        if type(cp["v"]) is not int or cp["v"] != 4:
            _reject()
        UUID(cp["id"])
        if config["configurable"].get("checkpoint_id") != cp["id"]:
            _reject()
        if datetime.fromisoformat(cp["ts"]).tzinfo is None:
            _reject()
        versions = self._versions(cp["channel_versions"])
        values = self._values(cp["channel_values"], encoding=encoding)
        if (set(values) & STATE_CHANNELS and values.get("research_only") is not True
                or not (values.get("research_only") is True or "__start__" in values)):
            _reject()
        if not values.keys() <= versions.keys():
            _reject()
        seen = cp["versions_seen"]
        if not isinstance(seen, dict) or not seen.keys() <= self.nodes | {"__input__", "__interrupt__", "__start__"}:
            _reject()
        seen = {key: self._versions(item) for key, item in seen.items()}
        if any(not item.keys() <= versions.keys() for item in seen.values()):
            _reject()
        updated = cp["updated_channels"]
        if updated is not None:
            if type(updated) is not list:
                _reject()
            for channel in updated:
                self._channel_name(channel)
        metadata = envelope["metadata"]
        _keys(metadata, {"source", "step", "parents", "thread_id", "run_id"}, {"source", "step", "parents"})
        if metadata["source"] not in {"input", "loop", "update", "fork"} or type(metadata["step"]) is not int:
            _reject()
        if metadata["parents"] != {}:
            _reject()
        if "thread_id" in metadata and metadata["thread_id"] != config["configurable"]["thread_id"]:
            _reject()
        if "run_id" in metadata:
            UUID(metadata["run_id"])
        writes = envelope["pending_writes"]
        if type(writes) not in (list, tuple) or len(writes) > 4096:
            _reject()
        clean_writes = []
        write_keys = set()
        for row in writes:
            if type(row) not in (list, tuple) or len(row) != 3:
                _reject()
            task, channel, value = row
            UUID(task)
            if (task, channel) in write_keys:
                _reject()
            write_keys.add((task, channel))
            clean_writes.append([task, channel, self._values({channel: value}, encoding=encoding)[channel]])
        return {**envelope, "config": config, "parent_config": parent,
            "checkpoint": {**cp, "channel_values": values, "channel_versions": versions, "versions_seen": seen},
            "metadata": dict(metadata), "pending_writes": clean_writes}

    def encode(self, checkpoint: CheckpointTuple) -> bytes:
        try:
            envelope = self._validate({"schema_version": "snapshot-checkpoint-json-v1",
                "fingerprint": self.fingerprint, "config": checkpoint.config,
                "checkpoint": checkpoint.checkpoint, "metadata": checkpoint.metadata,
                "parent_config": checkpoint.parent_config, "pending_writes": checkpoint.pending_writes or []}, encoding=True)
            raw = json.dumps(envelope, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
            if len(raw) > MAX_CHECKPOINT_BYTES:
                _reject()
            return raw
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            raise CheckpointCodecError("snapshot checkpoint is invalid or incompatible") from None

    def decode(self, raw: bytes) -> CheckpointTuple:
        def pairs(items):
            result = {}
            for key, item in items:
                if key in result:
                    _reject()
                result[key] = item
            return result

        try:
            if type(raw) is not bytes or len(raw) > MAX_CHECKPOINT_BYTES:
                _reject()
            envelope = self._validate(json.loads(raw, object_pairs_hook=pairs), encoding=False)
            return CheckpointTuple(config=envelope["config"], checkpoint=envelope["checkpoint"],
                metadata=envelope["metadata"], parent_config=envelope["parent_config"],
                pending_writes=[tuple(row) for row in envelope["pending_writes"]])
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            raise CheckpointCodecError("snapshot checkpoint is invalid or incompatible") from None
