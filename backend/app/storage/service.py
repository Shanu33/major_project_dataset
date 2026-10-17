import os
import shutil
from typing import BinaryIO
from abc import ABC, abstractmethod
from app.core.config import settings

class StorageService(ABC):
    @abstractmethod
    def save(self, storage_key: str, file_obj: BinaryIO) -> None:
        pass
        
    @abstractmethod
    def get(self, storage_key: str) -> str: # Returns path or URL
        pass
        
    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        pass
        
    @abstractmethod
    def delete(self, storage_key: str) -> None:
        pass

class LocalFileSystemStorage(StorageService):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
    def _get_full_path(self, storage_key: str) -> str:
        # Prevent path traversal
        clean_key = os.path.basename(storage_key)
        return os.path.join(self.base_dir, clean_key)

    def save(self, storage_key: str, file_obj: BinaryIO) -> None:
        path = self._get_full_path(storage_key)
        with open(path, 'wb') as f:
            file_obj.seek(0)
            shutil.copyfileobj(file_obj, f)

    def get(self, storage_key: str) -> str:
        return self._get_full_path(storage_key)
        
    def exists(self, storage_key: str) -> bool:
        return os.path.exists(self._get_full_path(storage_key))
        
    def delete(self, storage_key: str) -> None:
        path = self._get_full_path(storage_key)
        if os.path.exists(path):
            os.remove(path)

storage = LocalFileSystemStorage(settings.STORAGE_DIR)
