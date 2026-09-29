from job_mentor.config.sites import DEFAULT_SITES
from job_mentor.config.keywords import ELASTOMER_KEYWORDS


def test_sites_config_has_portals():
    assert isinstance(DEFAULT_SITES, list)
    assert len(DEFAULT_SITES) > 0
    assert all("name" in site and "base_url" in site for site in DEFAULT_SITES)


def test_keywords_include_material_terms():
    flattened = " ".join(ELASTOMER_KEYWORDS).lower()
    assert any(term in flattened for term in ["elastomer", "rubber", "polymer", "materials"])
