import datetime
from typing import Optional, Dict, Any

from meido.base_service import BaseService
from meido.services.task.models import Task, TaskTypeEnum
from meido.services.task.repositories import TaskRepository

__all__ = [
    "TaskServices",
    "SignServices",
    "TaskCardServices",
    "TaskResinServices",
    "TaskRealmServices",
    "TaskExpeditionServices",
]


class TaskServices:
    TASK_TYPE: TaskTypeEnum

    def __init__(self, task_repository: TaskRepository) -> None:
        self._repository: TaskRepository = task_repository

    async def add(self, task: Task):
        return await self._repository.add(task)

    async def remove(self, task: Task):
        return await self._repository.remove(task)

    async def update(self, task: Task):
        task.time_updated = datetime.datetime.now()
        return await self._repository.update(task)

    async def get_by_user_id(self, user_id: int):
        return await self._repository.get_by_user_id(user_id, self.TASK_TYPE)

    async def get_all(self):
        return await self._repository.get_all(self.TASK_TYPE)

    async def get_all_by_user_id(self, user_id: int):
        return await self._repository.get_all_by_user_id(user_id)

    def create(self, user_id: int, chat_id: int, status: int, data: Optional[Dict[str, Any]] = None):
        return Task(
            user_id=user_id,
            chat_id=chat_id,
            time_created=datetime.datetime.now(),
            status=status,
            type=self.TASK_TYPE,
            data=data,
        )


class SignServices(BaseService, TaskServices):
    TASK_TYPE = TaskTypeEnum.SIGN


class TaskResinServices(BaseService, TaskServices):
    TASK_TYPE = TaskTypeEnum.RESIN


class TaskRealmServices(BaseService, TaskServices):
    TASK_TYPE = TaskTypeEnum.REALM


class TaskExpeditionServices(BaseService, TaskServices):
    TASK_TYPE = TaskTypeEnum.EXPEDITION


class TaskCardServices(BaseService, TaskServices):
    TASK_TYPE = TaskTypeEnum.CARD
