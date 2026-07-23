from netmap.discovery import resolve_hostname

def test_resolve_localhost():
    result = resolve_hostname("127.0.0.1")
    assert result is not None

def test_resolve_invalid():
    result = resolve_hostname("999.999.999.999")
    assert result is None
