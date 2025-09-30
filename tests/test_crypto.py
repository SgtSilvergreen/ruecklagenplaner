import base64

from core.crypto import wrap_key, unwrap_key


def test_wrap_key_returns_base64_string_roundtrip():
    data_key = bytes(range(32))
    kek = bytes(reversed(range(32)))

    wrapped = wrap_key(data_key, kek)

    assert isinstance(wrapped, str)
    assert unwrap_key(wrapped, kek) == data_key


def test_unwrap_key_accepts_raw_bytes_payload():
    data_key = b"a" * 32
    kek = b"b" * 32

    wrapped_str = wrap_key(data_key, kek)
    wrapped_bytes = base64.b64decode(wrapped_str.encode("ascii"))

    assert unwrap_key(wrapped_bytes, kek) == data_key
