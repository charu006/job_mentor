class BaseCollector:
    """Abstract-style base class for portal-specific job collectors."""

    portal_name: str = "unknown"

    def __init__(self, portal_name: str | None = None):
        self.portal_name = portal_name or self.portal_name

    def collect(self, **kwargs):
        return {"status": "not_implemented", "portal": self.portal_name, "message": "Collector logic is planned for a later stage."}
