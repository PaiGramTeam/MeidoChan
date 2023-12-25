from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from meido.base_service import BaseService
from meido.dependence.database import Database
from meido.services.task.models import Task, TaskTypeEnum

__all__ = ("TaskRepository",)


class TaskRepository(BaseService.Component):
    def __init__(self, database: Database):
        self.engine = database.engine

    async def add(self, task: Task):
        async with AsyncSession(self.engine) as session:
            session.add(task)
            await session.commit()

    async def remove(self, task: Task):
        async with AsyncSession(self.engine) as session:
            await session.delete(task)
            await session.commit()

    async def update(self, task: Task) -> Task:
        async with AsyncSession(self.engine) as session:
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def get_by_user_id(self, user_id: int, task_type: TaskTypeEnum) -> Optional[Task]:
        async with AsyncSession(self.engine) as session:
            statement = select(Task).where(Task.user_id == user_id).where(Task.type == task_type)
            results = await session.exec(statement)
            return results.first()

    async def get_by_chat_id(self, chat_id: int, task_type: TaskTypeEnum) -> Optional[List[Task]]:
        async with AsyncSession(self.engine) as session:
            statement = select(Task).where(Task.chat_id == chat_id).where(Task.type == task_type)
            results = await session.exec(statement)
            return results.all()

    async def get_all(self, task_type: TaskTypeEnum) -> List[Task]:
        async with AsyncSession(self.engine) as session:
            query = select(Task).where(Task.type == task_type)
            results = await session.exec(query)
            return results.all()

    async def get_all_by_user_id(self, user_id: int) -> List[Task]:
        async with AsyncSession(self.engine) as session:
            query = select(Task).where(Task.user_id == user_id)
            results = await session.exec(query)
            return results.all()
