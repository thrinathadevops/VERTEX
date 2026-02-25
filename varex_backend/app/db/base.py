# PATH: varex_backend/app/db/base.py
# FIX: Import from interview_models (not interview) — Bug 1.10

from app.db.base_class import Base  # noqa: F401

# Import all models so Alembic can detect them for autogenerate
from app.models.user         import User          # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.content      import Content       # noqa: F401
from app.models.lead         import ConsultationLead  # noqa: F401
from app.models.workshop     import Workshop, WorkshopRegistration  # noqa: F401
from app.models.portfolio    import Project       # noqa: F401
from app.models.team         import TeamMember    # noqa: F401
from app.models.certification import Certification, Achievement  # noqa: F401
from app.models.faq          import FAQ           # noqa: F401
from app.models.interview_models import (         # noqa: F401  FIX: was interview.py
    JobDescription,
    CandidateProfile,
    InterviewSession,
    InterviewTurn,
    ScoreReport,
)
