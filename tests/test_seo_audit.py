import unittest
from heros_cloud.seo_audit import PageAuditInput, SEOAuditEngine


class TestSEOAuditEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SEOAuditEngine()

    def test_clean_page_passes(self):
        page = PageAuditInput(
            url="https://example.com/blog/ai-search-optimization",
            status_code=200,
            title="AI Search Optimization: Technical Best Practices",
            meta_description="Comprehensive guide to AI search engine optimization, technical crawls, and structured semantic data implementation.",
            canonical_url="https://example.com/blog/ai-search-optimization",
            h1_tags=["AI Search Optimization: Technical Best Practices"],
            h2_tags=["Crawler Discovery", "Structured Metadata"],
            images=[{"src": "/assets/diagram.png", "alt": "System Architecture Diagram"}],
            has_json_ld=True,
            word_count=1200
        )
        res = self.engine.evaluate(page)
        self.assertTrue(res.passed)
        self.assertEqual(res.score, 100)
        self.assertEqual(len(res.issues), 0)

    def test_missing_critical_elements_flags_and_generates_patches(self):
        page = PageAuditInput(
            url="https://example.com/products/automation-toolkit",
            status_code=200,
            title="",
            meta_description="",
            canonical_url="",
            h1_tags=[],
            images=[{"src": "/assets/hero.jpg", "alt": ""}]
        )
        res = self.engine.evaluate(page)
        self.assertFalse(res.passed)
        self.assertLess(res.score, 50)

        # Check critical issues
        rule_ids = [i.rule_id for i in res.issues]
        self.assertIn("MISSING_TITLE", rule_ids)
        self.assertIn("MISSING_META_DESCRIPTION", rule_ids)
        self.assertIn("MISSING_CANONICAL", rule_ids)
        self.assertIn("MISSING_H1", rule_ids)
        self.assertIn("MISSING_IMAGE_ALT", rule_ids)

        # Check patch synthesis
        self.assertIn("title", res.generated_patches)
        self.assertIn("meta_description", res.generated_patches)
        self.assertIn("canonical", res.generated_patches)
        self.assertIn("h1", res.generated_patches)
        self.assertIn("schema_json_ld", res.generated_patches)

    def test_heading_violations(self):
        page = PageAuditInput(
            url="https://example.com/docs/guide",
            title="Complete Platform Integration Guide & API",
            meta_description="A full reference document covering API integration endpoints, authentication tokens, and rate limits.",
            canonical_url="https://example.com/docs/guide",
            h1_tags=["First Heading", "Second Duplicate Heading"],
            has_json_ld=True
        )
        res = self.engine.evaluate(page)
        self.assertIn("MULTIPLE_H1", [i.rule_id for i in res.issues])
        self.assertEqual(res.score, 90)

    def test_non_200_status_code(self):
        page = PageAuditInput(
            url="https://example.com/broken-link",
            status_code=404,
            title="Page Not Found",
            meta_description="The requested resource was not located.",
            canonical_url="https://example.com/broken-link"
        )
        res = self.engine.evaluate(page)
        self.assertFalse(res.passed)
        self.assertIn("HTTP_STATUS_NOT_OK", [i.rule_id for i in res.issues])


if __name__ == "__main__":
    unittest.main()
