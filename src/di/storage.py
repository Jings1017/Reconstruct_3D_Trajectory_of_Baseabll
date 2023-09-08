from pathlib import Path

from attr import define
from injector import Module, provider, singleton
from trendup_storage.file_storage import FileStorage
from trendup_storage.local_storage import FileStorageLocal


@define
class StorageModuleLocal(Module):
    storage_path: Path

    @provider
    @singleton
    def file_storage(self) -> FileStorage:
        return FileStorageLocal(self.storage_path)
