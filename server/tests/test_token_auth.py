from app.auth.token_auth import is_token_valid


def test_no_expected_token_means_auth_disabled(monkeypatch):
    monkeypatch.delenv("VCA_SHARED_TOKEN", raising=False)

    assert is_token_valid(None) is True
    assert is_token_valid("anything") is True


def test_matching_token_is_valid(monkeypatch):
    monkeypatch.setenv("VCA_SHARED_TOKEN", "secret")

    assert is_token_valid("secret") is True


def test_mismatched_or_missing_token_is_invalid(monkeypatch):
    monkeypatch.setenv("VCA_SHARED_TOKEN", "secret")

    assert is_token_valid("wrong") is False
    assert is_token_valid(None) is False
