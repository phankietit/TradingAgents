from uuid import uuid4

import pytest

from tests.test_platform_api import NOW, _login, api_context as api_context
from tradingagents.contracts import ArtifactKind, PortfolioSnapshot
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.portfolio.evidence import ValuationEvidence, evidence_id


@pytest.mark.parametrize("case", ["valid", "foreign", "missing", "mismatch", "invalid_json"])
def test_valuation_evidence_access_and_integrity(api_context, case):
    client = api_context["client"]
    owner = uuid4() if case == "foreign" else api_context["principal"].owner_id
    portfolio = PortfolioSnapshot(portfolio_id=uuid4(), owner_id=owner, as_of=NOW,
        base_currency="USD", cash=(), positions=(), net_asset_value="0", content_hash="sha256:" + "a" * 64)
    with client.app.state.database.session() as session:
        repo = PlatformRepository(session)
        repo.add_portfolio_snapshot(portfolio)
        if case != "missing":
            content = ValuationEvidence(portfolio_id=portfolio.portfolio_id,
                portfolio_content_hash="wrong" if case == "mismatch" else portfolio.content_hash,
                sources=()).model_dump_json().encode()
            ArtifactService(LocalArtifactStore(client.app.state.settings.artifact_root), repo).create(
                owner_id=owner, kind=ArtifactKind.PORTFOLIO_VALUATION_EVIDENCE,
                media_type="application/json", content=b'{"secret":"do-not-echo"}' if case == "invalid_json" else content,
                artifact_id=evidence_id(portfolio.portfolio_id), created_at=NOW)
    path = f"/api/v1/portfolios/{portfolio.portfolio_id}/valuation-evidence"
    assert client.get(path).status_code == 401
    _login(client)
    response = client.get(path)
    assert response.status_code == (200 if case == "valid" else 404 if case in {"foreign", "missing"} else 409)
    assert "do-not-echo" not in response.text
    assert "no-store" in response.headers["cache-control"]
