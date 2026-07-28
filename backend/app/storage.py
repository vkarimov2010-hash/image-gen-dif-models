"""Абстракция хранилища сгенерированных изображений.

MVP: локальная файловая система. Интерфейс намеренно узкий, чтобы позже
подставить S3/R2-бэкенд без изменений в generation_service.
"""
from __future__ import annotations

import abc
from pathlib import Path

from app.config import get_settings

settings = get_settings()


class StorageBackend(abc.ABC):
    @abc.abstractmethod
    def save(self, relative_path: str, content: bytes) -> str:
        """Сохраняет файл, возвращает путь/идентификатор для последующего чтения."""

    @abc.abstractmethod
    def read(self, relative_path: str) -> bytes:
        ...

    @abc.abstractmethod
    def path_for(self, relative_path: str) -> Path:
        ...


class LocalStorage(StorageBackend):
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, relative_path: str, content: bytes) -> str:
        full_path = self.base_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return relative_path

    def read(self, relative_path: str) -> bytes:
        return self.path_for(relative_path).read_bytes()

    def path_for(self, relative_path: str) -> Path:
        return self.base_dir / relative_path


def get_storage() -> StorageBackend:
    return LocalStorage(settings.storage_dir)
