from typing import Literal

import redis
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.cache import build_task_list_cache_key, get_redis, invalidate_task_list_cache
from app.config import settings
from app.database import get_db
from app.models.task import TaskPriority, TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskDependencyCreate,
    TaskListResponse,
    TaskRead,
    TaskTreeNode,
    TaskUpdate,
)
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_task_or_404(db: Session, task_id: int):
    task = task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    tags: list[str] | None = Query(default=None),
    sort_by: Literal["created_at", "updated_at", "title", "priority", "status"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    cache: redis.Redis = Depends(get_redis),
):
    cache_key = build_task_list_cache_key(
        status=status,
        priority=priority,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return TaskListResponse.model_validate_json(cached)

    items, total_count = task_service.get_tasks(
        db,
        status=status,
        priority=priority,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )
    response = TaskListResponse(items=items, total_count=total_count, limit=limit, offset=offset)
    cache.set(cache_key, response.model_dump_json(), ex=settings.task_list_cache_ttl_seconds)
    return response


@router.post("/", response_model=TaskRead, status_code=201)
def create_task(
    task_in: TaskCreate, db: Session = Depends(get_db), cache: redis.Redis = Depends(get_redis)
):
    task = task_service.create_task(db, task_in)
    invalidate_task_list_cache(cache)
    return task


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return _get_task_or_404(db, task_id)


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    cache: redis.Redis = Depends(get_redis),
):
    task = _get_task_or_404(db, task_id)
    try:
        updated = task_service.update_task(db, task, task_in)
    except task_service.IncompleteDependenciesError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    invalidate_task_list_cache(cache)
    return updated


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int, db: Session = Depends(get_db), cache: redis.Redis = Depends(get_redis)
):
    task = _get_task_or_404(db, task_id)
    task_service.delete_task(db, task)
    invalidate_task_list_cache(cache)


@router.post("/{task_id}/dependencies", response_model=TaskRead, status_code=201)
def add_task_dependency(
    task_id: int,
    dependency_in: TaskDependencyCreate,
    db: Session = Depends(get_db),
    cache: redis.Redis = Depends(get_redis),
):
    task = _get_task_or_404(db, task_id)
    depends_on = _get_task_or_404(db, dependency_in.depends_on_id)
    try:
        updated = task_service.add_dependency(db, task, depends_on)
    except (task_service.SelfDependencyError, task_service.CircularDependencyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except task_service.DuplicateDependencyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    invalidate_task_list_cache(cache)
    return updated


@router.delete("/{task_id}/dependencies/{depends_on_id}", status_code=204)
def remove_task_dependency(
    task_id: int,
    depends_on_id: int,
    db: Session = Depends(get_db),
    cache: redis.Redis = Depends(get_redis),
):
    task = _get_task_or_404(db, task_id)
    depends_on = _get_task_or_404(db, depends_on_id)
    try:
        task_service.remove_dependency(db, task, depends_on)
    except task_service.DependencyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    invalidate_task_list_cache(cache)


@router.get("/{task_id}/dependencies/tree", response_model=TaskTreeNode)
def get_task_dependency_tree(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id)
    return task_service.build_dependency_tree(task)
