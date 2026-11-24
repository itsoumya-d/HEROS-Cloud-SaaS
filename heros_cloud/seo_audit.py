"""Automated on-page and technical SEO audit engine with policy-driven remediation patches."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import urllib.parse


@dataclass
class PageAuditInput:
    url: str
    status_code: int = 200
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    h1_tags: List[str] = field(default_factory=list)
    h2_tags: List[str] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)  # [{'src': '...', 'alt': '...'}]
    has_json_ld: bool = False
    word_count: int = 0


@dataclass
class AuditIssue:
    rule_id: str
    severity: str  # 'critical', 'warning', 'info'
    message: str
    recommended_fix: str


@dataclass
class AuditResult:
    url: str
    score: int
    passed: bool
    issues: List[AuditIssue]
    generated_patches: Dict[str, str]


class SEOAuditEngine:
    """Evaluates page SEO criteria and generates automated fix patches."""

    MIN_TITLE_LEN = 20
    MAX_TITLE_LEN = 65
    MIN_DESC_LEN = 50
    MAX_DESC_LEN = 160
    MIN_WORD_COUNT = 300

    def evaluate(self, page: PageAuditInput) -> AuditResult:
        issues: List[AuditIssue] = []
        score = 100
        patches: Dict[str, str] = {}

        # 1. HTTP Status check
        if page.status_code != 200:
            issues.append(AuditIssue(
                rule_id="HTTP_STATUS_NOT_OK",
                severity="critical",
                message=f"Returned non-200 status code: {page.status_code}",
                recommended_fix="Ensure URL returns 200 OK or appropriate canonical redirect."
            ))
            score -= 40

        # 2. Page Title check
        if not page.title or not page.title.strip():
            issues.append(AuditIssue(
                rule_id="MISSING_TITLE",
                severity="critical",
                message="Page is missing <title> tag.",
                recommended_fix="Add descriptive, keyword-aligned title between 30-60 characters."
            ))
            score -= 25
            suggested_title = self._synthesize_title_from_url(page.url)
            patches["title"] = f"<title>{suggested_title}</title>"
        elif len(page.title) < self.MIN_TITLE_LEN:
            issues.append(AuditIssue(
                rule_id="TITLE_TOO_SHORT",
                severity="warning",
                message=f"Title length ({len(page.title)}) is below recommended minimum ({self.MIN_TITLE_LEN}).",
                recommended_fix="Expand title with primary keywords and brand suffix."
            ))
            score -= 10
        elif len(page.title) > self.MAX_TITLE_LEN:
            issues.append(AuditIssue(
                rule_id="TITLE_TOO_LONG",
                severity="warning",
                message=f"Title length ({len(page.title)}) exceeds maximum ({self.MAX_TITLE_LEN}).",
                recommended_fix="Shorten title to prevent SERP truncation."
            ))
            score -= 5

        # 3. Meta Description check
        if not page.meta_description or not page.meta_description.strip():
            issues.append(AuditIssue(
                rule_id="MISSING_META_DESCRIPTION",
                severity="critical",
                message="Page is missing meta description.",
                recommended_fix="Provide concise meta description between 70-160 characters."
            ))
            score -= 20
            patches["meta_description"] = '<meta name="description" content="Explore comprehensive resources and insights.">'
        elif len(page.meta_description) < self.MIN_DESC_LEN:
            issues.append(AuditIssue(
                rule_id="META_DESCRIPTION_TOO_SHORT",
                severity="warning",
                message=f"Meta description ({len(page.meta_description)}) is under {self.MIN_DESC_LEN} chars.",
                recommended_fix="Enrich snippet with compelling call-to-action and secondary terms."
            ))
            score -= 10

        # 4. Canonical Link check
        if not page.canonical_url:
            issues.append(AuditIssue(
                rule_id="MISSING_CANONICAL",
                severity="warning",
                message="Page lacks canonical link declaration.",
                recommended_fix="Add self-referential or master canonical tag."
            ))
            score -= 10
            clean_url = page.url.split("?")[0]
            patches["canonical"] = f'<link rel="canonical" href="{clean_url}" />'

        # 5. Heading Structure check
        if len(page.h1_tags) == 0:
            issues.append(AuditIssue(
                rule_id="MISSING_H1",
                severity="critical",
                message="Page contains no H1 headings.",
                recommended_fix="Add exactly one clear, topical H1 heading."
            ))
            score -= 15
            patches["h1"] = f"<h1>{page.title or 'Page Overview'}</h1>"
        elif len(page.h1_tags) > 1:
            issues.append(AuditIssue(
                rule_id="MULTIPLE_H1",
                severity="warning",
                message=f"Page has {len(page.h1_tags)} H1 headings; best practice is exactly one.",
                recommended_fix="Demote secondary H1 tags to H2."
            ))
            score -= 10

        # 6. Image Alt attributes check
        images_missing_alt = [img.get("src", "unknown") for img in page.images if not img.get("alt", "").strip()]
        if images_missing_alt:
            issues.append(AuditIssue(
                rule_id="MISSING_IMAGE_ALT",
                severity="warning",
                message=f"{len(images_missing_alt)} image(s) missing descriptive alt attributes.",
                recommended_fix="Add descriptive alt text to all visual content assets."
            ))
            score -= min(15, len(images_missing_alt) * 5)

        # 7. Structured Data check
        if not page.has_json_ld:
            issues.append(AuditIssue(
                rule_id="MISSING_STRUCTURED_DATA",
                severity="info",
                message="Page does not include Schema.org JSON-LD structured data.",
                recommended_fix="Inject WebPage or Article JSON-LD markup."
            ))
            patches["schema_json_ld"] = (
                '<script type="application/ld+json">\n'
                '{"@context":"https://schema.org","@type":"WebPage","name":"' + (page.title or "Page") + '"}\n'
                '</script>'
            )

        final_score = max(0, min(100, score))
        passed = final_score >= 80 and not any(i.severity == "critical" for i in issues)

        return AuditResult(
            url=page.url,
            score=final_score,
            passed=passed,
            issues=issues,
            generated_patches=patches
        )

    def _synthesize_title_from_url(self, url: str) -> str:
        path = urllib.parse.urlparse(url).path.strip("/").split("/")[-1]
        if not path:
            return "Home Overview & Insights"
        return path.replace("-", " ").replace("_", " ").title() + " | Overview"
