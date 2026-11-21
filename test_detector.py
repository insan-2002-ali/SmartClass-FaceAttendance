import cv2

from services.camera_service import CameraService
from services.face_detector import FaceDetector


camera = CameraService()

camera.start()

detector = FaceDetector()

while True:

    success, frame = camera.read()

    if not success:
        break

    faces = detector.detect(frame)

    for face in faces:

        detector.draw(frame, face)

    cv2.imshow(
        "Face Detector",
        frame
    )

    key = cv2.waitKey(1)

    if key == 27:
        break

camera.stop()