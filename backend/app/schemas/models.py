"""
Shotto Songroho - Pydantic Schemas
Request/response models for the API layer.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, List, Literal


# Request Models

class VerifyRequest(BaseModel):
    """Request body for the /api/verify endpoint."""
    text: Optional[str] = Field(None, description="Claim text to verify")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image")
    url: Optional[str] = Field(None, description="Social post URL to extract claim from")
    lang: Literal["bn", "en"] = Field("en", description="Output language")


class TestimonyRequest(BaseModel):
    """Request body for moderated testimony intake."""
    text: str = Field(..., min_length=10, max_length=5000)
    contact_optional: Optional[str] = Field(None, max_length=300)
    lang: Literal["bn", "en"] = "en"


class TestimonyResponse(BaseModel):
    """Response body for testimony intake."""
    status: Literal["queued_for_review"] = "queued_for_review"
    id: str


class ShareCardRequest(BaseModel):
    """Request body for generating a shareable verdict PNG."""
    verdict: Literal["verified", "disputed", "unverifiable", "false"]
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    summary: str = ""
    sources: List[dict] = Field(default_factory=list)


class CorpusSearchParams(BaseModel):
    """Query parameters for the /api/corpus endpoint."""
    query: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    location: Optional[str] = None
    verdict_label: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)


# Internal Pipeline Models

class ExtractedClaim(BaseModel):
    """Output from the Claim Extraction Agent."""
    event: str = ""
    date: Optional[str] = None
    location: Optional[str] = None
    entities: List[str] = Field(default_factory=list)
    claim_type: str = "factual"  # factual, image, mixed
    original_text: str = ""
    language_detected: str = "en"


class SourceCitation(BaseModel):
    """A cited source in a verdict or corpus entry."""
    title: str = ""
    url: Optional[str] = None
    excerpt: str = ""
    relevance: Optional[float] = None
    source_org: Optional[str] = None


class RetrievedEvidence(BaseModel):
    """A single piece of retrieved evidence from the corpus."""
    id: str
    description: str
    event_date: Optional[str] = None
    location: Optional[str] = None
    sources: List[SourceCitation] = Field(default_factory=list)
    verdict_label: Optional[str] = None
    relevance_score: float = 0.0

class CrossVerificationResult(BaseModel):
    """Output from the Cross-Verification Agent."""
    assessment: Literal["supports", "contradicts", "insufficient", "partially_supports"] = "insufficient"
    reasoning: str = ""
    key_matches: List[str] = Field(default_factory=list)
    key_contradictions: List[str] = Field(default_factory=list)


class ImageCheckResult(BaseModel):
    """Output from the Image Reuse Agent."""
    matched: bool = False
    original_source: Optional[str] = None
    original_date: Optional[str] = None
    original_context: Optional[str] = None
    hash_distance: Optional[int] = None


class ReasoningTrace(BaseModel):
    """Intermediate output from an agent for glass-box transparency."""
    agent: str
    output: Any


class PipelineStep(BaseModel):
    """A single step in the agent pipeline for transparency."""
    agent: str
    status: Literal["running", "completed", "failed", "skipped"] = "completed"
    summary: str = ""
    duration_ms: Optional[int] = None


# Response Models


class ChainReceipt(BaseModel):
    """Hash-chain receipt for a corpus entry or generated verdict."""
    entry_hash: str = ""
    prev_chain_hash: str = ""
    chain_hash: str = ""
    ots_proof_ref: Optional[str] = None


class ChainProofStatus(BaseModel):
    """Latest OpenTimestamps proof status."""
    status: str = "missing"
    proof_path: Optional[str] = None
    detail: str = ""


class ChainVerifyResponse(BaseModel):
    """Response body for /api/chain/verify."""
    valid: bool = False
    chain_length: int = 0
    chain_hash: str = ""
    errors: List[str] = Field(default_factory=list)
    latest_ots_proof: ChainProofStatus = Field(default_factory=ChainProofStatus)


class VerifyResponse(BaseModel):
    """Response body for the /api/verify endpoint."""
    verdict: Literal["verified", "disputed", "unverifiable", "false"]
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    summary: str = ""
    sources: List[SourceCitation] = Field(default_factory=list)
    image_match: Optional[ImageCheckResult] = None
    pipeline_steps: List[PipelineStep] = Field(default_factory=list)
    reasoning_trace: List[ReasoningTrace] = Field(default_factory=list)
    claim_extracted: Optional[ExtractedClaim] = None
    chain_receipt: Optional[ChainReceipt] = None


class CorpusEntryResponse(BaseModel):
    """A single corpus entry in search results."""
    id: str
    event_date: Optional[str] = None
    location: Optional[str] = None
    description_bn: str = ""
    description_en: str = ""
    verdict_label: str = ""
    sources: List[SourceCitation] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    related_image_hashes: List[str] = Field(default_factory=list)


class AccountabilityIncident(BaseModel):
    """A cited incident included in the accountability index."""
    id: str
    date: Optional[str] = None
    location: Optional[str] = None
    description: str = ""
    sources: List[SourceCitation] = Field(default_factory=list)


class AccountabilityIndexEntry(BaseModel):
    """Incidents grouped by documented org/unit entity."""
    entity: str
    incidents: List[AccountabilityIncident] = Field(default_factory=list)


class AccountabilityIndexResponse(BaseModel):
    """Response body for /api/accountability-index."""
    results: List[AccountabilityIndexEntry] = Field(default_factory=list)
    total_entities: int = 0


class CorpusSearchResponse(BaseModel):
    """Response body for the /api/corpus endpoint."""
    results: List[CorpusEntryResponse] = Field(default_factory=list)
    total: int = 0


class HealthResponse(BaseModel):
    """Response body for the /api/health endpoint."""
    status: str = "ok"
    corpus_size: int = 0
    version: str = "1.0.0"



