import pytest


@pytest.fixture(autouse=True)
def isolated_live_dir(tmp_path_factory, monkeypatch):
    """Testy API nie zapisują doby live do repozytorium (Z-09)."""
    monkeypatch.setenv("HEMS_LIVE_DIR", str(tmp_path_factory.mktemp("live")))
