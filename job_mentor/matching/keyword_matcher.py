class JobMatcher:
    """Placeholder keyword and relevance matcher for materials-related roles."""

    def __init__(self, keywords=None):
        self.keywords = keywords or []

    def matches(self, text: str) -> bool:
        if not text:
            return False
        normalized = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in normalized:
                return True
        return False

    def score(self, text: str) -> int:
        if not text:
            return 0
        normalized = text.lower()
        return sum(1 for keyword in self.keywords if keyword.lower() in normalized)
