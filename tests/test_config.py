"""Tests for config module."""

from gnote.config import GnoteConfig, TokenApproach


def test_gnote_config_defaults() -> None:
    """Test default configuration values."""
    config = GnoteConfig()

    assert config.token_approach == TokenApproach.CHARDIV4
    assert config.token_limit == 8000


def test_gnote_config_custom() -> None:
    """Test custom configuration values."""
    config = GnoteConfig(token_approach=TokenApproach.CHARDIV4, token_limit=10000)

    assert config.token_approach == TokenApproach.CHARDIV4
    assert config.token_limit == 10000


def test_gnote_config_validation() -> None:
    """Test configuration validation."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        GnoteConfig(token_limit=0)

    with pytest.raises(ValidationError):
        GnoteConfig(token_limit=-100)
