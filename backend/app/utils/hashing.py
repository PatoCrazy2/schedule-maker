import hashlib


def compute_file_hash(content: bytes) -> str:
    """Calcula el hash SHA256 de los bytes del archivo."""
    return hashlib.sha256(content).hexdigest()
