import hashlib

def calculate_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class ArtifactValidator:
    """Watchdog component for validating ML artifacts to prevent corruption."""
    
    @staticmethod
    def validate_or_raise(filepath: str):
        # In a real enterprise system, we would compare this against a remote DB record.
        # Here, we just verify the file can be read and hashing succeeds.
        try:
            checksum = calculate_checksum(filepath)
            return checksum
        except Exception as e:
            raise RuntimeError(f"Artifact corrupted or missing at {filepath}: {str(e)}")
