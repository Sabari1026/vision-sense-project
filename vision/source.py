import cv2
import os
import time
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Generator, Dict, Any

class CameraSource(ABC):
    """Abstract Camera Source interface preparing VisionSense for MP4, RTSP, and Webcams."""

    def __init__(self, source_path: str, name: str = "Camera"):
        self.source_path = source_path
        self.name = name
        self.is_opened = False

    @abstractmethod
    def open(self) -> bool:
        pass

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[Any]]:
        pass

    @abstractmethod
    def release(self):
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        pass

class FileCameraSource(CameraSource):
    """Camera source implementation reading video files (MP4, AVI, MOV, MKV). Loopable for demo live feeds."""

    def __init__(self, source_path: str, name: str = "File Camera", loop: bool = True):
        super().__init__(source_path, name)
        self.loop = loop
        self.cap: Optional[cv2.VideoCapture] = None
        self.fps = 25
        self.width = 1280
        self.height = 720
        self.total_frames = 0

    def open(self) -> bool:
        if not os.path.exists(self.source_path):
            print(f"[FileCameraSource] Video file not found: {self.source_path}")
            self.is_opened = False
            return False

        self.cap = cv2.VideoCapture(self.source_path)
        if not self.cap.isOpened():
            self.is_opened = False
            return False

        self.is_opened = True
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 25
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        return True

    def read_frame(self) -> Tuple[bool, Optional[Any]]:
        if not self.is_opened or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            if self.loop:
                # Loop back to beginning for continuous CCTV simulation
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    # If seek failed on Windows OpenCV, cleanly reopen video capture
                    self.cap.release()
                    self.cap = cv2.VideoCapture(self.source_path)
                    ret, frame = self.cap.read()
            else:
                return False, None

        return ret, frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "file",
            "path": self.source_path,
            "fps": self.fps,
            "resolution": f"{self.width}x{self.height}",
            "is_opened": self.is_opened
        }

class RTSPCameraSource(CameraSource):
    """RTSP/IP-Camera source implementation for real physical CCTV network streams."""

    def __init__(self, rtsp_url: str, name: str = "RTSP Camera"):
        super().__init__(rtsp_url, name)
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        # Set OpenCV RTSP buffer flags to avoid latency accumulation
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        self.cap = cv2.VideoCapture(self.source_path, cv2.CAP_FFMPEG)
        self.is_opened = self.cap.isOpened()
        return self.is_opened

    def read_frame(self) -> Tuple[bool, Optional[Any]]:
        if not self.is_opened or self.cap is None:
            return False, None
        return self.cap.read()

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "rtsp",
            "path": self.source_path,
            "is_opened": self.is_opened
        }

class WebCameraSource(CameraSource):
    """USB/Webcam source implementation (device index e.g. 0, 1)."""

    def __init__(self, device_index: int = 0, name: str = "Webcam"):
        super().__init__(str(device_index), name)
        self.device_index = device_index
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.device_index)
        self.is_opened = self.cap.isOpened()
        return self.is_opened

    def read_frame(self) -> Tuple[bool, Optional[Any]]:
        if not self.is_opened or self.cap is None:
            return False, None
        return self.cap.read()

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "webcam",
            "index": self.device_index,
            "is_opened": self.is_opened
        }
