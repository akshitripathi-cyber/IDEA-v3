

class MemoryStore:
    def __init__(self):
        self.store = {}
        self.export_progress = {
            "fetched": 0,
            "total": 0,
            "status": "idle",  # idle, fetching, rate-limited, processing, complete, failed
            "error": None,
            "wait_until": None  # Unix timestamp when rate-limit sleep ends
        }

    def save(self, key, value):
        self.store[key] = value

    def get(self, key, default=None):
        return self.store.get(key, default)
    
    def set_progress(self, fetched=None, total=None, status=None, error=None, wait_until=None):
        """Update export progress safely."""
        if fetched is not None:
            self.export_progress["fetched"] = fetched
        if total is not None:
            self.export_progress["total"] = total
        if status is not None:
            self.export_progress["status"] = status
        if error is not None:
            self.export_progress["error"] = error
        if wait_until is not None:
            self.export_progress["wait_until"] = wait_until
    
    def get_progress(self):
        """Return current export progress."""
        return self.export_progress.copy()
    
    def reset_progress(self):
        """Reset progress for new export."""
        self.export_progress = {
            "fetched": 0,
            "total": 0,
            "status": "idle",
            "error": None,
            "wait_until": None
        }

memory_store = MemoryStore()
