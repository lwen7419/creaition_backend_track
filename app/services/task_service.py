from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskTreeNode, TaskUpdate


class TaskDependencyError(Exception):
    """Base class for task-dependency business rule violations."""


class SelfDependencyError(TaskDependencyError):
    pass


class CircularDependencyError(TaskDependencyError):
    pass


class DuplicateDependencyError(TaskDependencyError):
    pass


class DependencyNotFoundError(TaskDependencyError):
    pass


class IncompleteDependenciesError(TaskDependencyError):
    pass


SORTABLE_FIELDS = {
    "created_at": Task.created_at,
    "updated_at": Task.updated_at,
    "title": Task.title,
    "priority": Task.priority,
    "status": Task.status,
}


def get_tasks(
    db: Session,
    *,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    tags: list[str] | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Task], int]:
    query = db.query(Task)
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)

    sort_column = SORTABLE_FIELDS[sort_by]
    query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))

    if not tags:
        total_count = query.count()
        page = query.offset(offset).limit(limit).all()
        return page, total_count

    # Tags are stored as JSON, so SQLite can't filter/count them in SQL; filter in Python instead.
    matching = [task for task in query.all() if task.tags and any(tag in task.tags for tag in tags)]
    total_count = len(matching)
    page = matching[offset : offset + limit]
    return page, total_count


def get_task(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def create_task(db: Session, task_in: TaskCreate) -> Task:
    task = Task(
        title=task_in.title,
        description=task_in.description,
        completed=task_in.completed,
        status=task_in.status,
        priority=task_in.priority,
        tags=task_in.tags,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, task_in: TaskUpdate) -> Task:
    updates = task_in.model_dump(exclude_unset=True)

    marking_complete = updates.get("status") == TaskStatus.completed or updates.get("completed") is True
    if marking_complete:
        incomplete = [dep for dep in task.dependencies if dep.status != TaskStatus.completed]
        if incomplete:
            raise IncompleteDependenciesError(
                f"Cannot complete task: dependencies not completed: {[dep.id for dep in incomplete]}"
            )

    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    task.dependencies.clear()
    task.dependents.clear()
    db.delete(task)
    db.commit()


def _depends_on_transitively(start: Task, target_id: int, visited: set[int] | None = None) -> bool:
    visited = visited if visited is not None else set()
    if start.id in visited:
        return False
    visited.add(start.id)
    if start.id == target_id:
        return True
    return any(_depends_on_transitively(dep, target_id, visited) for dep in start.dependencies)


def add_dependency(db: Session, task: Task, depends_on: Task) -> Task:
    if task.id == depends_on.id:
        raise SelfDependencyError("A task cannot depend on itself")
    if depends_on in task.dependencies:
        raise DuplicateDependencyError("Dependency already exists")
    if _depends_on_transitively(depends_on, task.id):
        raise CircularDependencyError("Adding this dependency would create a circular dependency")

    task.dependencies.append(depends_on)
    db.commit()
    db.refresh(task)
    return task


def remove_dependency(db: Session, task: Task, depends_on: Task) -> Task:
    if depends_on not in task.dependencies:
        raise DependencyNotFoundError("Dependency not found")

    task.dependencies.remove(depends_on)
    db.commit()
    db.refresh(task)
    return task


def build_dependency_tree(task: Task, _visited: frozenset[int] = frozenset()) -> TaskTreeNode:
    visited = _visited | {task.id}
    return TaskTreeNode(
        id=task.id,
        title=task.title,
        status=task.status,
        dependencies=[
            build_dependency_tree(dep, visited) for dep in task.dependencies if dep.id not in visited
        ],
    )
