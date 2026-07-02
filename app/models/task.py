import enum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("depends_on_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    CheckConstraint("task_id != depends_on_id", name="ck_task_dependencies_no_self_reference"),
)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    completed = Column(Boolean, nullable=False, default=False)
    status = Column(
        Enum(TaskStatus, native_enum=False),
        nullable=False,
        default=TaskStatus.pending,
        server_default=TaskStatus.pending.value,
        index=True,
    )
    priority = Column(
        Enum(TaskPriority, native_enum=False),
        nullable=False,
        default=TaskPriority.medium,
        server_default=TaskPriority.medium.value,
        index=True,
    )
    tags = Column(JSON, nullable=False, default=list)
    due_date = Column(Date, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    dependencies = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=id == task_dependencies.c.task_id,
        secondaryjoin=id == task_dependencies.c.depends_on_id,
        backref="dependents",
    )

    @property
    def dependency_ids(self) -> list[int]:
        return [dep.id for dep in self.dependencies]
