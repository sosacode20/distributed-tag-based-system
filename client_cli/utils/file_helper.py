from pathlib import Path
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import math
from enum import Enum


class SizeUnit(Enum):
    """The possible file size units"""

    Bytes = 0
    KB = 1
    MB = 2
    GB = 3
    TB = 4
    PB = 5


class FileMetadata(BaseModel):
    """Metadata of the file"""

    size: int = Field(ge=0, lt=1024**6)
    """The file size in bytes"""
    creation_date: datetime
    """The creation date of the file in UTC"""
    modification_date: datetime
    """The modification date of the file in UTC"""

    def get_formatted_size(self) -> str:
        """Get the size and the size unit"""
        size = abs(self.size)
        unit_index = min(math.floor(math.log(size, 1024)), 5)
        new_size = size / 1024**unit_index
        return f"{new_size:.2f} {SizeUnit(unit_index).name}"

    def get_size(self, unit: SizeUnit = SizeUnit.Bytes) -> str:
        """Get the size in the specified unit"""
        return f"{self.size / 1024**int(unit):.2f} {str(unit)}"


class FileHelper(object):
    def __init__(self, file_path: Path):
        self.file_path: Path = file_path
        """The path of the file"""

    def get_file_size(self) -> int:
        """Returns the file size in bytes"""
        return self.file_path.stat().st_size

    def get_metadata(self) -> FileMetadata:
        """Returns the file metadata."""
        stats = self.file_path.stat()
        metadata = FileMetadata(
            size=stats.st_size,
            creation_date=datetime.fromtimestamp(stats.st_ctime, timezone.utc),
            modification_date=datetime.fromtimestamp(stats.st_mtime, timezone.utc),
        )
        return metadata

    def get_chunk(self, offset: int, chunk_size: int) -> bytes:
        """
        Retrieves a chunk of data from the file starting at the specified offset.

        This method reads a single chunk of data of size 'chunk_size' from the file, beginning 
        at the given 'offset'. If the offset exceeds the file size, an exception is raised. 
        The method ensures that the file is opened in binary read mode.

        Args:
            offset (int): The starting position in the file from which to read the chunk (in bytes).
            chunk_size (int): The size of the chunk to be read (in bytes).

        Returns:
            bytes: The data of the specified chunk.

        Raises:
            Exception: If the specified offset exceeds the total size of the file.

        Example:
        >>> helper = FileHelper('path/to/your/file.txt')
        >>> # Give me a chunk of at most 1024 bytes in size starting at the byte offset 32
        >>> # An error will be raised if the offset is greater than the file size
        >>> chunk = helper.get_chunk(32, 1024)
        >>> print(chunk)
        """
        size: int = self.get_file_size()
        if offset > size:
            raise Exception(f"The file '{self.file_path}' has {size} bytes and the \\
                            bytes offset is {offset} which is greater than the size of the file.")
        with self.file_path.open("rb") as file:
            file.seek(
                offset
            )  # if you want to read from the end, then `file.seek(-offset, os.SEEK_END)`
            fragment = file.read(chunk_size)
        return fragment

    def get_chunks(self, offset: int, chunk_size: int, n_chunks: int) -> list[bytes]:
        """
        Retrieves a specified number of chunks of data from the file, starting from a given offset.

        This method reads a maximum of 'n_chunks' from the file, each of size 'chunk_size', 
        beginning at the specified 'offset'. If the offset is beyond the file size, an exception 
        is raised. The method ensures that it does not attempt to read beyond the end of the file.

        Args:
            offset (int): The starting position in the file from which to read chunks (in bytes).
            chunk_size (int): The size of each chunk to be read (in bytes).
            n_chunks (int): The maximum number of chunks to retrieve.

        Returns:
            list[bytes]: A list containing the retrieved chunks of data, 
                         which may contain fewer than 'n_chunks' if the end of the file is reached.

        Raises:
            Exception: If the specified offset exceeds the total size of the file.

        Example:
        >>> helper = FileHelper('path/to/your/file.txt')
        >>> # Get 5 chunks of size 1024 bytes starting at the byte offset 32
        >>> # An error will be raised if the offset (32 in this example) is greater than the total size of the file
        >>> chunks = helper.get_chunks(32, 1024, 5)
        >>> for i, chunk in enumerate(chunks):
        >>>     print(f"Chunk {i}: {chunk}")
        """
        size:int = self.get_file_size()
        if offset > size:
            raise Exception(f"The file '{self.file_path}' has {size} bytes and the \\
                            bytes offset is {offset} which is greater than the size of the file.")
        with self.file_path.open("rb") as file:
            file.seek(offset)
            fragment = file.read(n_chunks * chunk_size)
            fragments = []
            for i in range(n_chunks):
                if offset + i * chunk_size > size:
                    break
                fragments.append(fragment[i * chunk_size : (i + 1) * chunk_size])
        return fragments

    def get_index_chunk(self, chunk_size: int, chunk_index: int):
        """
        Retrieves a specific chunk of data from the file based on the provided chunk size and index.

        This method calculates the total number of chunks in the file by dividing the file size by the 
        specified chunk size. It raises an exception if the requested chunk index is out of bounds. 
        If valid, it seeks to the appropriate position in the file and reads the specified chunk of data.

        Args:
            chunk_size (int): The size of each chunk in bytes.
            chunk_index (int): The index of the chunk to retrieve (0-based).

        Returns:
            bytes: The data of the specified chunk.

        Raises:
            Exception: If the requested chunk index exceeds the total number of available chunks.

        Example:
        >>> helper = FileHelper('path/to/your/file.txt')
        >>> # Give me the 3rd chunk of size 1024 bytes from the file. If the file has less than 3 chunks of size 1024, then an error will be raised
        >>> # NOTE: This method gives you a chunk of 'chunk_size' bytes if you are NOT asking for the last chunk. The last chunk could have less than 'chunk_size' bytes
        >>> chunk = helper.get_index_chunk(1024, 3)
        >>> print(chunk)
        """
        with self.file_path.open("rb") as file:
            size: int = self.get_file_size()
            total_chunks = math.ceil(size / chunk_size)
            if chunk_index >= total_chunks:
                raise Exception(
                    f"The file '{self.file_path.name}' only has {total_chunks} of at \\
                    most {chunk_size} bytes. You are asking for the {chunk_index} chunk which doesn't exist"
                )
            file.seek(chunk_size * chunk_index)
            return file.read(chunk_size)
        
    
