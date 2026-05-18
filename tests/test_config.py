"""Unit tests for Config — settings-mode and root_dir-mode path resolution."""

from pathlib import Path

import pytest
import yaml

from AOTaccess.config import Config
from AOTaccess.errors import ConfigError


@pytest.fixture
def settings_file(tmp_path):
    path = tmp_path / "settings.yml"
    path.write_text(
        yaml.safe_dump(
            {
                "paths": {"roi": "/data/roi", "glmsingle": "/data/glm"},
                "parameters": {"run_number": 10},
            }
        )
    )
    return path


def test_settings_mode_resolves_path(settings_file):
    cfg = Config(settings_path=settings_file)
    assert cfg.path("roi") == Path("/data/roi")
    assert cfg.path("glmsingle") == Path("/data/glm")


def test_settings_mode_unknown_key_raises(settings_file):
    cfg = Config(settings_path=settings_file)
    with pytest.raises(ConfigError):
        cfg.path("does-not-exist")


def test_param_lookup(settings_file):
    cfg = Config(settings_path=settings_file)
    assert cfg.param("run_number") == 10
    assert cfg.param("absent", default=7) == 7


def test_root_dir_mode_uses_canonical_layout():
    cfg = Config(root_dir="/ds")
    assert cfg.path("roi") == Path("/ds/derivatives/roi")
    assert cfg.path("glmsingle") == Path("/ds/derivatives/glmsingle")
    assert cfg.path("localizers") == Path("/ds/derivatives/localizers")


def test_root_dir_mode_unknown_key_raises():
    cfg = Config(root_dir="/ds")
    with pytest.raises(ConfigError):
        cfg.path("not-a-store")


def test_missing_settings_file_raises(tmp_path):
    cfg = Config(settings_path=tmp_path / "nope.yml")
    with pytest.raises(ConfigError):
        _ = cfg.settings


def test_env_var_overrides_settings_path(settings_file, monkeypatch):
    monkeypatch.setenv("AOT_SETTINGS", str(settings_file))
    cfg = Config()
    assert cfg.path("glmsingle") == Path("/data/glm")


def test_packaged_settings_has_required_keys():
    # the shipped settings.yml must define every store the API uses
    cfg = Config()
    for key in ("glmsingle", "preproced", "bids", "roi", "localizers"):
        assert isinstance(cfg.path(key), Path)
