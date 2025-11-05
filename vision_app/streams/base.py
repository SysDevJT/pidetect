from abc import ABC, abstractmethod

class VideoStream(ABC):
    """
    Abstract base class for video streams.
    Defines a common interface for different video sources.
    """
    @abstractmethod
    def __enter__(self):
        """Initializes and returns the video capture object."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Releases the video capture object."""
        pass

    @abstractmethod
    def read(self):
        """Reads a frame from the video stream."""
        pass

    @abstractmethod
    def release(self):
        """Releases the video capture object."""
        pass
