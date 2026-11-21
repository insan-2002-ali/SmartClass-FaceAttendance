
import cv2


class CameraService:

    def __init__(self, source=0):

        self.camera = None
        self.source = self._normalize_source(source)

    # ==========================================
    # NORMALIZE CAMERA SOURCE
    # ==========================================

    @staticmethod
    def _normalize_source(source):

        if isinstance(source, str):

            source = source.strip()

            if source.isdigit():
                return int(source)

            # RTSP / IP camera URL
            return source

        return source

    # ==========================================
    # START CAMERA
    # ==========================================

    def start(self):

        if self.is_open():
            return True

        self.camera = cv2.VideoCapture(self.source)

        if not self.camera.isOpened():

            self.camera.release()
            self.camera = None

            raise RuntimeError(
                f"Cannot open camera: {self.source}"
            )

        print(f"Camera started: {self.source}")

        return True

    # ==========================================
    # READ FRAME
    # ==========================================

    def read(self):

        if not self.is_open():
            return False, None

        success, frame = self.camera.read()

        if not success or frame is None:
            return False, None

        return True, frame

    # ==========================================
    # STOP CAMERA
    # ==========================================

    def stop(self):

        if self.camera is not None:

            if self.camera.isOpened():
                self.camera.release()

            self.camera = None

            print(f"Camera stopped: {self.source}")

    # ==========================================
    # CAMERA STATUS
    # ==========================================

    def is_open(self):

        if self.camera is None:
            return False

        return self.camera.isOpened()

    # ==========================================
    # CHANGE CAMERA SOURCE
    # ==========================================

    def set_source(self, source):

        self.stop()

        self.source = self._normalize_source(source)

    # ==========================================
    # GET CAMERA SOURCE
    # ==========================================

    def get_source(self):

        return self.source
