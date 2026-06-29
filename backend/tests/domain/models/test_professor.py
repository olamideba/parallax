from uuid import uuid4

import pytest

from src.domain.models.professor import Capacity, Professor, Publication, PublicationStatus


def _professor(**kwargs) -> Professor:
    defaults = dict(id=uuid4(), email="prof@university.edu")
    return Professor(**{**defaults, **kwargs})


# --- PublicationStatus ---

def test_publication_status_values():
    assert PublicationStatus.PENDING == "pending"
    assert PublicationStatus.INDEXING == "indexing"
    assert PublicationStatus.INDEXED == "indexed"
    assert PublicationStatus.NEEDS_UPLOAD == "needs_upload"
    assert PublicationStatus.FAILED == "failed"


def test_publication_default_status():
    pub = Publication(id=uuid4(), professor_id=uuid4(), title="Attention Is All You Need")
    assert pub.status == PublicationStatus.PENDING
    assert pub.indexed is False


# --- Capacity ---

def test_capacity_defaults():
    cap = Capacity()
    assert cap.open_slots == 0
    assert cap.students_committed == 0
    assert cap.budget_amount is None
    assert cap.funding_source is None
    assert cap.recruiting_topics == []
    assert cap.auto_resolve_declines is True
    assert cap.hold_when_at_capacity is True


def test_capacity_with_slots():
    cap = Capacity(open_slots=3, students_committed=1, recruiting_topics=["NLP", "CV"])
    assert cap.open_slots == 3
    assert len(cap.recruiting_topics) == 2


# --- Professor ---

def test_professor_defaults():
    prof = _professor()
    assert prof.display_name is None
    assert prof.intake_email is None
    assert prof.publications == []
    assert prof.gatekeeper_aggressiveness == 0.5
    assert isinstance(prof.capacity, Capacity)


def test_professor_gatekeeper_aggressiveness_bounds():
    prof_min = _professor(gatekeeper_aggressiveness=0.0)
    prof_max = _professor(gatekeeper_aggressiveness=1.0)
    assert prof_min.gatekeeper_aggressiveness == 0.0
    assert prof_max.gatekeeper_aggressiveness == 1.0


def test_professor_gatekeeper_aggressiveness_out_of_bounds():
    with pytest.raises(Exception):
        _professor(gatekeeper_aggressiveness=1.5)

    with pytest.raises(Exception):
        _professor(gatekeeper_aggressiveness=-0.1)


def test_professor_with_publications():
    pub = Publication(
        id=uuid4(),
        professor_id=uuid4(),
        title="BERT",
        status=PublicationStatus.INDEXED,
        indexed=True,
    )
    prof = _professor(publications=[pub])
    assert len(prof.publications) == 1
    assert prof.publications[0].status == PublicationStatus.INDEXED
