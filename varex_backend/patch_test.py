import sqlalchemy.dialects.postgresql as pg
from sqlalchemy.types import JSON, Uuid

class DummyArray(JSON):
    def __init__(self, *args, **kwargs):
        super().__init__()

pg.UUID = Uuid
pg.JSONB = JSON
pg.ARRAY = DummyArray

from app.models.team import TeamMember
print("patched successfully!")
