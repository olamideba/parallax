from __future__ import annotations

from uuid6 import uuid7

from sqlmodel import select

from src.adapters.storage.models import ProfessorRecord, PublicationRecord
from src.domain.models.professor import PublicationStatus
from src.entrypoints.api.main import app
from src.entrypoints.api.dependencies import get_current_professor, get_object_storage


class FakeObjectStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, str]] = []

    async def upload(self, storage_key: str, data: bytes, content_type: str = "application/pdf"):
        self.uploads.append((storage_key, data, content_type))
        return storage_key


async def test_upload_pdf_creates_publication_row(
    test_client,
    db_session,
    monkeypatch,
):
    professor = ProfessorRecord(
        id=uuid7(),
        email="professor@example.edu",
        display_name="Professor Example",
    )
    db_session.add(professor)
    await db_session.commit()

    fake_storage = FakeObjectStorage()

    async def override_current_professor():
        return professor

    app.dependency_overrides[get_current_professor] = override_current_professor
    app.dependency_overrides[get_object_storage] = lambda: fake_storage
    monkeypatch.setattr(
        "src.entrypoints.api.v1.endpoints.professors.ingest_publication.delay",
        lambda *_args, **_kwargs: None,
    )
    try:
        response = await test_client.post(
            "/api/v1/professors/me/publications/upload",
            files={"file": ("paper.pdf", b"%PDF-1.4\n%test\n", "application/pdf")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["publication"] is not None

        storage_key = body["data"]["storage_key"]
        publication = body["data"]["publication"]
        assert publication["storage_key"] == storage_key
        assert publication["status"] == PublicationStatus.PENDING.value
        assert publication["title"] == "paper"

        result = await db_session.exec(
            select(PublicationRecord).where(PublicationRecord.storage_key == storage_key)
        )
        saved = result.one()
        assert saved.professor_id == professor.id
        assert saved.storage_key == storage_key
        assert saved.title == "paper"
        assert saved.status == PublicationStatus.PENDING.value
        assert saved.indexed is False
        assert len(fake_storage.uploads) == 1
    finally:
        app.dependency_overrides.pop(get_current_professor, None)
        app.dependency_overrides.pop(get_object_storage, None)
