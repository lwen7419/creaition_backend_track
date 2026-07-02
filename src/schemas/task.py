from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    completed: bool = False
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.medium
    tags: list[str] = Field(default_factory=list)
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    completed: bool | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    tags: list[str] | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    dependency_ids: list[int] = Field(default_factory=list)


class TaskListResponse(BaseModel):
    items: list[TaskRead]
    total_count: int
    limit: int
    offset: int


class TaskDependencyCreate(BaseModel):
    depends_on_id: int


class TaskFromTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class TagSuggestionsResponse(BaseModel):
    tags: list[str]


class PriorityRecommendationResponse(BaseModel):
    priority: TaskPriority


class TaskTreeNode(BaseModel):
    id: int
    title: str
    status: TaskStatus
    dependencies: list["TaskTreeNode"] = Field(default_factory=list)


TaskTreeNode.model_rebuild()
