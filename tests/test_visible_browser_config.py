import os


def test_visible_browser_env_flag(monkeypatch):
    monkeypatch.setenv("COINARB_BROWSER_HEADLESS", "0")
    assert os.getenv("COINARB_BROWSER_HEADLESS", "1") != "1"
