import os
import pickle
import cv2
import numpy as np

from insightface.app import FaceAnalysis


BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "static",
    "face_data",
    "students"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "face_data",
    "model"
)

MODEL_FILE = os.path.join(
    MODEL_PATH,
    "encodings.pkl"
)


def generate_encodings():

    os.makedirs(
        MODEL_PATH,
        exist_ok=True
    )

    app = FaceAnalysis(
        name="buffalo_l"
    )

    app.prepare(
        ctx_id=0,
        det_size=(640,640)
    )

    known_embeddings = []

    known_student_ids = []

    print("="*60)
    print("Generating Face Embeddings")
    print("="*60)

    for student_id in os.listdir(DATASET_PATH):

        student_folder = os.path.join(
            DATASET_PATH,
            student_id
        )

        if not os.path.isdir(student_folder):

            continue

        print(f"\nStudent : {student_id}")

        for image_name in os.listdir(student_folder):

            image_path = os.path.join(
                student_folder,
                image_name
            )

            image = cv2.imread(
                image_path
            )

            if image is None:

                continue

            faces = app.get(image)

            if len(faces)==0:

                print(f"Skipped : {image_name}")

                continue

            embedding = faces[0].embedding

            known_embeddings.append(
                embedding
            )

            known_student_ids.append(
                student_id
            )

            print(f"Encoded : {image_name}")

    data = {

        "embeddings":known_embeddings,

        "student_ids":known_student_ids

    }

    with open(
        MODEL_FILE,
        "wb"
    ) as file:

        pickle.dump(
            data,
            file
        )

    print("\n")
    print("="*60)
    print("Encoding Completed")
    print(f"Total Faces : {len(known_embeddings)}")
    print("="*60)


if __name__=="__main__":

    generate_encodings()