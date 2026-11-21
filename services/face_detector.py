import cv2
from insightface.app import FaceAnalysis


class FaceDetector:

    def __init__(self):

        self.app = FaceAnalysis(
            name="buffalo_l"
        )

        self.app.prepare(
            ctx_id=0,
            det_size=(640, 640)
        )

    def detect(self, frame):

        return self.app.get(frame)

    def largest_face(self, faces):

        if len(faces) == 0:
            return None

        return max(
            faces,
            key=lambda face:
            (face.bbox[2] - face.bbox[0]) *
            (face.bbox[3] - face.bbox[1])
        )

    def draw(self, frame, face):

        x1, y1, x2, y2 = map(
            int,
            face.bbox
        )

        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            2

        )

        return frame