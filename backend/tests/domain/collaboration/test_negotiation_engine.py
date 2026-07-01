import pytest

from src.domain.collaboration.negotiation_engine import NegotiationEngine


def test_negotiation_engine_is_abstract():
    with pytest.raises(TypeError):
        NegotiationEngine(round_cap=3)  # type: ignore[abstract]


def test_subclass_carries_round_cap():
    class _Dummy(NegotiationEngine):
        async def run(self, outreach, professor):  # noqa: ANN001
            raise NotImplementedError

    engine = _Dummy(round_cap=5)
    assert engine.round_cap == 5
