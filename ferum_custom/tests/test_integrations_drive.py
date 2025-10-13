from __future__ import annotations

from ferum_custom.ferum_custom.integrations import drive


def test_upload_bytes_disabled(monkeypatch):
	monkeypatch.setattr(drive, "is_feature_enabled", lambda flag: False)
	assert drive.upload_bytes(["Project"], "file.txt", b"data") is None


def test_drive_healthcheck_disabled(monkeypatch):
	monkeypatch.setattr(drive, "is_feature_enabled", lambda flag: False)
	result = drive.healthcheck()
	assert result["status"] == "disabled"


def test_drive_healthcheck_success(monkeypatch):
	monkeypatch.setattr(drive, "is_feature_enabled", lambda flag: True)
	monkeypatch.setattr(drive, "build", object())
	monkeypatch.setattr(drive, "MediaInMemoryUpload", object())
	monkeypatch.setattr(
		drive,
		"get_setting",
		lambda field, default=None: "root-folder" if field == "google_drive_root_folder_id" else None,
	)

	class FakeFiles:
		def get(self, fileId, fields):
			assert fileId == "root-folder"
			self._fields = fields
			return self

		def execute(self):
			return {
				"id": "root-folder",
				"name": "Root",
				"trashed": False,
				"webViewLink": "https://example.test",
				"owners": [{"displayName": "Ferum"}],
			}

	class FakeService:
		def files(self):
			return FakeFiles()

	monkeypatch.setattr(drive, "_drive_service", lambda: FakeService())

	result = drive.healthcheck()
	assert result["status"] == "ok"
	assert result["details"]["id"] == "root-folder"


def test_upload_bytes_creates_file(monkeypatch):
	monkeypatch.setattr(drive, "is_feature_enabled", lambda flag: True)
	monkeypatch.setattr(drive, "MediaInMemoryUpload", lambda data, mimetype, resumable=False: ("media", data))
	monkeypatch.setattr(
		drive,
		"get_setting",
		lambda field, default=None: "root-folder" if field == "google_drive_root_folder_id" else None,
	)

	class FakeResponse:
		def __init__(self, payload):
			self.payload = payload

		def execute(self):
			return self.payload

	class FakeFiles:
		def list(self, **kwargs):
			return FakeResponse({"files": []})

		def create(self, **kwargs):
			return FakeResponse({"id": "drive-id"})

	class FakeDrive:
		def files(self):
			return FakeFiles()

	monkeypatch.setattr(drive, "_drive_service", lambda: FakeDrive())
	monkeypatch.setattr(drive, "_ensure_folder", lambda service, name, parent: f"{parent}/{name}")

	assert drive.upload_bytes(["Customer", "Project"], "report.pdf", b"bytes") == "drive-id"
