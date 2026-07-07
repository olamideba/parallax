"""Hand-labeled synthetic corpus + outreach for the single-agent-vs-society benchmark.

Two synthetic professors, each with a few short "publications" (real text, tiny
and cheap to embed) that form the RAG yardstick. Then ~16 outreach cases, each
carrying a designed failure mode and a ground-truth `expected_label` assigned by
construction — we know the right verdict because we wrote the trap.

Labels are deliberately spread so the benchmark can't be gamed by a decline-biased
society: the clean-strong-fit cases must come back `invite` from both paths, or a
society that just rejects everything would score a spurious accuracy win.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.models.outreach import (
    ExtractedClaim,
    ExtractedProfile,
    Outreach,
    OutreachStatus,
)
from src.domain.models.professor import Capacity, Professor

# --- Synthetic professors + their indexed corpus ------------------------------


@dataclass
class SyntheticPublication:
    title: str
    text: str


@dataclass
class SyntheticProfessor:
    key: str
    professor: Professor
    publications: list[SyntheticPublication]


def _prof_mata() -> SyntheticProfessor:
    """Prof. Mata — geometric deep learning, capacity OPEN (2 slots)."""
    pid = UUID("11111111-1111-1111-1111-111111111111")
    professor = Professor(
        id=pid,
        email="mata@geodl.edu",
        display_name="Dr. Ada Mata",
        capacity=Capacity(
            open_slots=2,
            students_committed=1,
            funding_source="NSF geometric-learning grant",
            recruiting_topics=["equivariant networks", "graph neural networks"],
            hold_when_at_capacity=True,
        ),
        institution="Institute for Geometric Learning",
        institution_country="United States",
    )
    pubs = [
        SyntheticPublication(
            title="Gauge-Equivariant Message Passing on Meshes",
            text=(
                "We introduce a gauge-equivariant message passing scheme for signals "
                "defined on discrete surface meshes. By parallel-transporting feature "
                "vectors along mesh edges and constraining the message function to commute "
                "with the structure group of the tangent bundle, the network's predictions "
                "are invariant to the arbitrary choice of local coordinate frame at each "
                "vertex. On the FAUST correspondence benchmark our gauge-equivariant meshes "
                "reduce geodesic error by 31% over anisotropic CNN baselines. The central "
                "lesson is that respecting the local symmetry group, not just global "
                "rotation, is what yields sample efficiency on curved domains."
            ),
        ),
        SyntheticPublication(
            title="Spectral Bias in Graph Neural Networks",
            text=(
                "This paper characterizes the spectral bias of graph neural networks: "
                "message-passing GNNs preferentially fit the low-frequency eigenvectors of "
                "the graph Laplacian and struggle to represent high-frequency signals such "
                "as those on the boundary between two densely connected communities. We "
                "prove a frequency-dependent convergence bound and show that adding a "
                "learnable high-pass filter to each layer closes most of the gap on "
                "heterophilous node-classification datasets. We deliberately do NOT study "
                "reinforcement learning or robotic control; our scope is spectral analysis "
                "of static graphs."
            ),
        ),
        SyntheticPublication(
            title="Equivariance Without Group Convolutions",
            text=(
                "Group convolutions are the standard route to equivariant networks but "
                "scale poorly with the size of the symmetry group. We propose a "
                "frame-averaging alternative that attains exact equivariance for arbitrary "
                "finite groups at a fraction of the compute, by averaging an ordinary "
                "backbone over a small stabilizer-selected set of frames. The method is a "
                "drop-in wrapper and requires no specialized equivariant layers."
            ),
        ),
    ]
    return SyntheticProfessor(key="mata", professor=professor, publications=pubs)


def _prof_okoye() -> SyntheticProfessor:
    """Prof. Okoye — clinical NLP, capacity CLOSED (0 slots, holds at capacity)."""
    pid = UUID("22222222-2222-2222-2222-222222222222")
    professor = Professor(
        id=pid,
        email="okoye@clinnlp.edu",
        display_name="Dr. Chidi Okoye",
        capacity=Capacity(
            open_slots=0,
            students_committed=4,
            funding_source="departmental teaching lines only",
            recruiting_topics=["clinical NLP", "de-identification"],
            hold_when_at_capacity=True,
        ),
        institution="School of Biomedical Informatics",
        institution_country="United States",
    )
    pubs = [
        SyntheticPublication(
            title="Robust De-Identification of Clinical Notes Under Distribution Shift",
            text=(
                "We study protected-health-information de-identification when a model "
                "trained on one hospital's notes is deployed at another. Naive NER taggers "
                "lose up to 12 F1 points across institutions because note templates and "
                "abbreviation conventions differ. We show that a lightweight "
                "domain-adversarial objective plus a hand-curated abbreviation lexicon "
                "recovers most of the lost recall on rare entity types like non-standard "
                "date formats. Recall on PHI, not precision, is the metric that matters "
                "clinically, because a single leaked identifier is a reportable breach."
            ),
        ),
        SyntheticPublication(
            title="Weak Supervision for Adverse-Drug-Event Extraction",
            text=(
                "Labeling adverse drug events in discharge summaries is expensive. We build "
                "a weak supervision pipeline that combines pattern-based labeling functions "
                "with a generative label model to produce probabilistic training labels, "
                "then train a downstream extractor on them. The approach reaches 88% of "
                "fully-supervised performance using no manually labeled training notes, "
                "only a validation set."
            ),
        ),
    ]
    return SyntheticProfessor(key="okoye", professor=professor, publications=pubs)


_PROF_MATA = _prof_mata()
_PROF_OKOYE = _prof_okoye()


def synthetic_professors() -> list[SyntheticProfessor]:
    return [_PROF_MATA, _PROF_OKOYE]


# --- Labeled outreach cases ---------------------------------------------------

# Failure-mode tags. The `_ACCEPT_TRAP_MODES` set below are the ones a single
# agent tends to rubber-stamp: a false-accept there (predicting invite or
# request_more_info when the ground truth is decline) is exactly the miss the
# society is meant to catch.
FABRICATED_CITATION = "fabricated_citation"
INFLATED_ALIGNMENT = "inflated_alignment"
CAPACITY_MISMATCH = "capacity_mismatch"
CLEAN_STRONG_FIT = "clean_strong_fit"
CLEAN_WEAK_FIT = "clean_weak_fit"

# HARD adversarial modes — designed so a single retrieval + one pass gets the wrong
# answer, but multi-round cross-examination (retrieve a SECOND paper, reason across
# two facts) gets it right. These are the "high-difficulty tasks where errors are
# expensive" a society is supposed to earn its cost on.
HARD_BURIED_CONTRADICTION = "hard_buried_contradiction"  # topical match; a 2nd paper disavows it
HARD_FALSE_EXTENSION = "hard_false_extension"  # claim extends a method in an incoherent way
HARD_FUNDING_OVERRIDE = "hard_funding_override"  # 0 slots, but external funding sidesteps the hold
HARD_VALUE_INVERSION = "hard_value_inversion"  # right topic, optimizes the metric the prof rejects

# Modes where the correct verdict is a rejection *and* the trap is a claim/fit
# problem a lone agent plausibly accepts — these define a "false accept".
_ACCEPT_TRAP_MODES = {
    FABRICATED_CITATION,
    INFLATED_ALIGNMENT,
    HARD_BURIED_CONTRADICTION,
    HARD_FALSE_EXTENSION,
    HARD_VALUE_INVERSION,
}


@dataclass
class BenchmarkCase:
    case_id: str
    professor_key: str
    expected_label: str  # DecisionLabel value: invite | request_more_info | decline
    failure_mode: str
    sender_name: str
    sender_email: str
    subject: str
    body: str
    interests: list[str] = field(default_factory=list)
    credentials: list[str] = field(default_factory=list)
    country: str | None = None
    funding_context: str | None = None
    claims: list[str] = field(default_factory=list)

    def is_accept_trap(self) -> bool:
        """A rejection-truth case whose trap a single agent tends to rubber-stamp."""
        return self.failure_mode in _ACCEPT_TRAP_MODES

    def to_outreach(self, professor_id: UUID) -> Outreach:
        return Outreach(
            id=uuid4(),
            professor_id=professor_id,
            sender_email=self.sender_email,
            sender_name=self.sender_name,
            subject=self.subject,
            body=self.body,
            received_at=datetime.now(UTC),
            status=OutreachStatus.PENDING_TRIAGE,
            extracted_profile=ExtractedProfile(
                name=self.sender_name,
                email=self.sender_email,
                interests=self.interests,
                credentials=self.credentials,
                country=self.country,
                funding_context=self.funding_context,
            ),
            extracted_claims=[ExtractedClaim(text=c) for c in self.claims],
        )


CASES: list[BenchmarkCase] = [
    # --- Prof. Mata (capacity OPEN) ------------------------------------------
    BenchmarkCase(
        case_id="mata-fab-1",
        professor_key="mata",
        expected_label="decline",
        failure_mode=FABRICATED_CITATION,
        sender_name="Ravi Sunder",
        sender_email="ravi@student.edu",
        country="United States",
        subject="Building on your reinforcement learning for robotics work",
        body=(
            "Dear Dr. Mata, I was inspired by your 2023 paper 'Deep Reinforcement "
            "Learning for Dexterous Robotic Manipulation' and would love to extend its "
            "sim-to-real transfer results in your lab."
        ),
        interests=["reinforcement learning", "robotics", "sim-to-real"],
        claims=[
            "Dr. Mata authored 'Deep Reinforcement Learning for Dexterous Robotic "
            "Manipulation' (2023).",
            "My work directly extends her sim-to-real transfer results.",
        ],
    ),
    BenchmarkCase(
        case_id="mata-fab-2",
        professor_key="mata",
        expected_label="decline",
        failure_mode=FABRICATED_CITATION,
        sender_name="Elin Park",
        sender_email="elin@student.edu",
        country="United States",
        subject="Your NeurIPS 2024 diffusion paper",
        body=(
            "Hello Professor, your NeurIPS 2024 paper on diffusion models for protein "
            "folding changed how I think about generative biology. I would like to "
            "continue that exact line of research with you."
        ),
        interests=["diffusion models", "protein folding", "generative biology"],
        claims=[
            "Dr. Mata published a NeurIPS 2024 paper on diffusion models for protein "
            "folding.",
        ],
    ),
    BenchmarkCase(
        case_id="mata-inflated-1",
        professor_key="mata",
        expected_label="decline",
        failure_mode=INFLATED_ALIGNMENT,
        sender_name="Tom Bright",
        sender_email="tom@student.edu",
        country="United States",
        subject="Huge fan of your groundbreaking AI research",
        body=(
            "Dear Professor Mata, I have read all of your groundbreaking work and I am "
            "deeply aligned with your vision for the future of artificial intelligence. "
            "I am passionate about AI and would be a perfect fit for your lab."
        ),
        interests=["artificial intelligence", "machine learning"],
        claims=["I am deeply aligned with all of your research."],
    ),
    BenchmarkCase(
        case_id="mata-inflated-2",
        professor_key="mata",
        expected_label="request_more_info",
        failure_mode=INFLATED_ALIGNMENT,
        sender_name="Sara Vance",
        sender_email="sara@student.edu",
        country="United States",
        subject="Interested in graph learning",
        body=(
            "Dear Dr. Mata, I am interested in graph neural networks and think your work "
            "is relevant to my interests. I would like to join your lab. I have some "
            "coursework in the area but have not published yet."
        ),
        interests=["graph neural networks"],
        credentials=["MSc coursework in ML"],
        claims=["I am interested in graph neural networks."],
    ),
    BenchmarkCase(
        case_id="mata-strong-1",
        professor_key="mata",
        expected_label="invite",
        failure_mode=CLEAN_STRONG_FIT,
        sender_name="Nadia Farouk",
        sender_email="nadia@student.edu",
        country="United States",
        subject="Frame-averaging for equivariance without group convolutions",
        body=(
            "Dear Dr. Mata, your work on attaining exact equivariance via frame averaging "
            "rather than group convolutions directly motivated my MSc thesis, where I "
            "extended the stabilizer-selection idea to continuous Lie groups. I have a "
            "NeurIPS workshop paper on gauge-equivariant mesh operators and would love to "
            "push the geodesic-error results on FAUST further with you."
        ),
        interests=["equivariant networks", "gauge equivariance", "mesh geometry"],
        credentials=["MSc thesis on equivariance", "NeurIPS workshop paper"],
        claims=[
            "My thesis extended frame-averaging equivariance to continuous Lie groups.",
            "I have a workshop paper on gauge-equivariant mesh operators.",
        ],
    ),
    BenchmarkCase(
        case_id="mata-strong-2",
        professor_key="mata",
        expected_label="invite",
        failure_mode=CLEAN_STRONG_FIT,
        sender_name="Ken Ito",
        sender_email="ken@student.edu",
        country="United States",
        subject="Spectral bias and high-pass GNN filters",
        body=(
            "Dear Professor Mata, I read your analysis of spectral bias in GNNs and "
            "implemented the learnable high-pass filter on three additional heterophilous "
            "benchmarks, reproducing your frequency-dependent convergence gap. I would "
            "like to work with you on extending the bound to directed graphs."
        ),
        interests=["graph neural networks", "spectral methods", "heterophily"],
        credentials=["reproduced published GNN spectral-bias results"],
        claims=["I reproduced your high-pass GNN filter results on new benchmarks."],
    ),
    BenchmarkCase(
        case_id="mata-weak-1",
        professor_key="mata",
        expected_label="decline",
        failure_mode=CLEAN_WEAK_FIT,
        sender_name="Owen Blake",
        sender_email="owen@student.edu",
        country="United States",
        subject="PhD in natural language processing",
        body=(
            "Dear Dr. Mata, I want to do a PhD on large language models for dialogue "
            "systems and conversational agents. I have built several chatbots. I am "
            "honestly not sure your lab works on this but wanted to reach out."
        ),
        interests=["large language models", "dialogue systems", "chatbots"],
        credentials=["built dialogue chatbots"],
        claims=["My research is on LLM dialogue systems."],
    ),
    BenchmarkCase(
        case_id="mata-weak-2",
        professor_key="mata",
        expected_label="decline",
        failure_mode=CLEAN_WEAK_FIT,
        sender_name="Priya Nair",
        sender_email="priya@student.edu",
        country="United States",
        subject="Computer vision for autonomous driving",
        body=(
            "Dear Professor, my focus is real-time object detection for self-driving cars "
            "using camera-lidar fusion. I would like to join your group to continue this "
            "applied perception work."
        ),
        interests=["object detection", "autonomous driving", "sensor fusion"],
        claims=["I work on real-time perception for autonomous vehicles."],
    ),
    BenchmarkCase(
        case_id="mata-inflated-3",
        professor_key="mata",
        expected_label="decline",
        failure_mode=INFLATED_ALIGNMENT,
        sender_name="Bao Nguyen",
        sender_email="bao@student.edu",
        country="United States",
        subject="Your amazing deep learning research",
        body=(
            "Dear Professor Mata, your deep learning research is amazing and I resonate "
            "with it completely. I am confident I would thrive in your lab working on "
            "cutting-edge AI."
        ),
        interests=["deep learning", "AI"],
        claims=["I resonate completely with your research."],
    ),
    # --- Prof. Okoye (capacity CLOSED — 0 slots, holds at capacity) ----------
    BenchmarkCase(
        case_id="okoye-cap-1",
        professor_key="okoye",
        expected_label="request_more_info",
        failure_mode=CAPACITY_MISMATCH,
        sender_name="Marta Silva",
        sender_email="marta@student.edu",
        country="United States",
        subject="De-identification under distribution shift",
        body=(
            "Dear Dr. Okoye, your work on cross-institution PHI de-identification and the "
            "domain-adversarial recall recovery is exactly my area. I built on your "
            "abbreviation-lexicon idea for a hospital-transfer setting in my thesis and "
            "would love a PhD slot."
        ),
        interests=["clinical NLP", "de-identification", "domain adaptation"],
        credentials=["thesis on cross-hospital de-identification"],
        claims=["I extended your abbreviation-lexicon de-identification approach."],
    ),
    BenchmarkCase(
        case_id="okoye-cap-2",
        professor_key="okoye",
        expected_label="request_more_info",
        failure_mode=CAPACITY_MISMATCH,
        sender_name="Diego Alvarez",
        sender_email="diego@student.edu",
        country="United States",
        subject="Weak supervision for adverse drug events",
        body=(
            "Dear Professor Okoye, I reproduced your weak-supervision pipeline for "
            "adverse-drug-event extraction and reached similar performance without "
            "labeled notes. I am fully funded by a national fellowship and hoped to join "
            "your lab this fall."
        ),
        interests=["clinical NLP", "weak supervision", "information extraction"],
        credentials=["reproduced weak-supervision ADE pipeline"],
        funding_context="Fully funded by a national fellowship",
        claims=["I reproduced your weak-supervision ADE extraction results."],
    ),
    BenchmarkCase(
        case_id="okoye-fab-1",
        professor_key="okoye",
        expected_label="decline",
        failure_mode=FABRICATED_CITATION,
        sender_name="Lena Fischer",
        sender_email="lena@student.edu",
        country="United States",
        subject="Your JAMA paper on GPT-4 clinical diagnosis",
        body=(
            "Dear Dr. Okoye, your JAMA 2024 paper showing GPT-4 outperforms physicians at "
            "differential diagnosis was a landmark. I want to extend that benchmark to "
            "pediatric cases in your lab."
        ),
        interests=["clinical LLMs", "diagnosis benchmarks"],
        claims=["Dr. Okoye published a JAMA 2024 paper on GPT-4 clinical diagnosis."],
    ),
    BenchmarkCase(
        case_id="okoye-inflated-1",
        professor_key="okoye",
        expected_label="decline",
        failure_mode=INFLATED_ALIGNMENT,
        sender_name="Hassan Ali",
        sender_email="hassan@student.edu",
        country="United States",
        subject="Passionate about healthcare AI",
        body=(
            "Dear Professor, I am extremely passionate about using AI to transform "
            "healthcare and I admire everything your lab does. I would bring energy and "
            "dedication and would be an ideal addition to your team."
        ),
        interests=["healthcare AI"],
        claims=["I admire everything your lab does."],
    ),
    BenchmarkCase(
        case_id="okoye-weak-1",
        professor_key="okoye",
        expected_label="decline",
        failure_mode=CLEAN_WEAK_FIT,
        sender_name="Grace Lin",
        sender_email="grace@student.edu",
        country="United States",
        subject="Reinforcement learning for game playing",
        body=(
            "Dear Dr. Okoye, my research is on deep reinforcement learning for strategy "
            "games and self-play. I would like to pursue a PhD in your group on this topic."
        ),
        interests=["reinforcement learning", "self-play", "games"],
        claims=["I work on RL for game playing."],
    ),
    BenchmarkCase(
        case_id="okoye-cap-3",
        professor_key="okoye",
        expected_label="request_more_info",
        failure_mode=CAPACITY_MISMATCH,
        sender_name="Yuki Tanaka",
        sender_email="yuki@student.edu",
        country="United States",
        subject="Recall-first PHI de-identification",
        body=(
            "Dear Dr. Okoye, I share your view that PHI recall matters more than precision "
            "clinically. My work on rare-entity date-format recall directly complements "
            "your distribution-shift de-identification results, and I would be thrilled to "
            "join for a PhD."
        ),
        interests=["clinical NLP", "de-identification", "named entity recognition"],
        credentials=["published on rare-entity recall in clinical NER"],
        claims=["My rare-entity recall work complements your de-identification results."],
    ),
    # --- HARD adversarial cases (single-pass should fail; society should catch) ---
    BenchmarkCase(
        # Topical match on "equivariant networks" (Mata's area) — BUT the candidate's
        # actual work is RL, and Mata's spectral-bias paper EXPLICITLY disavows RL /
        # robotic control. A single top-k retrieval hits the equivariance chunk and
        # sees a fit; catching the mismatch needs retrieving the SECOND paper's
        # scope-disavowal and reasoning across both. Truth: decline.
        case_id="mata-hard-contradiction",
        professor_key="mata",
        expected_label="decline",
        failure_mode=HARD_BURIED_CONTRADICTION,
        sender_name="Victor Roth",
        sender_email="victor@student.edu",
        country="United States",
        subject="Equivariant policy networks for robotic manipulation",
        body=(
            "Dear Dr. Mata, your work on equivariant networks is the perfect home for "
            "my research: I build equivariant reinforcement-learning policies for "
            "robotic manipulation, using symmetry to improve sample efficiency in "
            "control. Your equivariance results are exactly the foundation I want to "
            "build on for sim-to-real robotic RL."
        ),
        interests=["equivariant networks", "reinforcement learning", "robotic control"],
        credentials=["MSc on equivariant RL for manipulation"],
        claims=[
            "My equivariant RL for robotic control builds directly on your equivariance work.",
        ],
    ),
    BenchmarkCase(
        # The candidate claims to extend Mata's frame-averaging equivariance to
        # INFINITE / continuous groups — but the paper's method is explicitly for
        # FINITE groups (frame averaging over a finite stabilizer set); the claimed
        # extension is methodologically incoherent as stated. A single pass sees the
        # exact-topic match and the confident claim and accepts; catching it needs
        # retrieving the method detail ("arbitrary finite groups") and reasoning about
        # compatibility. Truth: decline (the headline claim is false as stated).
        case_id="mata-hard-false-extension",
        professor_key="mata",
        expected_label="decline",
        failure_mode=HARD_FALSE_EXTENSION,
        sender_name="Ingrid Vasquez",
        sender_email="ingrid@student.edu",
        country="United States",
        subject="Extending your frame-averaging to infinite symmetry groups",
        body=(
            "Dear Dr. Mata, I have generalized your frame-averaging equivariance method "
            "so that it attains exact equivariance for arbitrary INFINITE continuous "
            "groups by averaging over the full uncountable group orbit in closed form, "
            "removing the finite-stabilizer restriction entirely. I would like to make "
            "this the core of my PhD with you."
        ),
        interests=["equivariant networks", "frame averaging", "group theory"],
        credentials=["preprint on infinite-group frame averaging"],
        claims=[
            "I extended your finite-group frame averaging to exact equivariance over "
            "arbitrary infinite continuous groups by averaging the full uncountable orbit.",
        ],
    ),
    BenchmarkCase(
        # Okoye has 0 open slots and holds at capacity — BUT the hold's funding_source
        # is "departmental teaching lines only", and this candidate brings a FULL
        # EXTERNAL fellowship that doesn't draw on those lines, plus a genuine de-id
        # fit. The single-hop read ("0 slots -> decline/park") misses that external
        # funding sidesteps the specific constraint. Truth: request_more_info (a real,
        # fundable fit worth engaging — not a flat decline).
        case_id="okoye-hard-funding",
        professor_key="okoye",
        expected_label="request_more_info",
        failure_mode=HARD_FUNDING_OVERRIDE,
        sender_name="Amara Okonkwo",
        sender_email="amara@student.edu",
        country="United States",
        subject="Externally-funded PhD on cross-hospital de-identification",
        body=(
            "Dear Dr. Okoye, I hold a full national fellowship that covers my stipend and "
            "tuition for four years, so I would not draw on any departmental teaching "
            "line. My work directly extends your cross-institution PHI de-identification "
            "under distribution shift. Given the external funding, could we discuss a "
            "supervised PhD even outside your usual departmental intake?"
        ),
        interests=["clinical NLP", "de-identification", "domain adaptation"],
        credentials=["national PhD fellowship (external, fully funded)"],
        funding_context="Full external national fellowship, does not use departmental lines",
        claims=[
            "My work extends your cross-institution de-identification under distribution shift.",
        ],
    ),
    BenchmarkCase(
        # Exact-topic match on de-identification — BUT the candidate's whole pitch is
        # optimizing PRECISION, while Okoye's paper explicitly argues RECALL matters
        # more clinically (a missed identifier is a reportable breach). A single pass
        # sees "de-id + strong method -> fit" and invites/parks; catching the values
        # inversion needs retrieving the paper's recall-over-precision stance and
        # recognizing the candidate optimizes the wrong objective. Truth: decline.
        case_id="okoye-hard-value-inversion",
        professor_key="okoye",
        expected_label="decline",
        failure_mode=HARD_VALUE_INVERSION,
        sender_name="Boris Lindgren",
        sender_email="boris@student.edu",
        country="United States",
        subject="Precision-first de-identification of clinical notes",
        body=(
            "Dear Dr. Okoye, my de-identification research is built around maximizing "
            "PRECISION: I aggressively suppress false-positive redactions so that almost "
            "nothing useful is over-redacted, accepting lower recall as the trade-off. I "
            "think this precision-first philosophy is the future of clinical de-id and "
            "aligns perfectly with your de-identification work."
        ),
        interests=["clinical NLP", "de-identification"],
        credentials=["thesis on precision-optimized redaction"],
        claims=[
            "My precision-first, lower-recall de-identification aligns with your de-id work.",
        ],
    ),
]


def case_by_id(case_id: str) -> BenchmarkCase:
    for c in CASES:
        if c.case_id == case_id:
            return c
    raise KeyError(case_id)


def professor_for_case(case: BenchmarkCase) -> SyntheticProfessor:
    for sp in synthetic_professors():
        if sp.key == case.professor_key:
            return sp
    raise KeyError(case.professor_key)
