import os
import pickle
import cv2
import numpy as np

from insightface.app import FaceAnalysis


class FaceEncoder:

    def __init__(self):

        # =================================================
        # DATASET
        # =================================================

        self.dataset_path = (
            "face_data/dataset"
        )

        # =================================================
        # EMBEDDING DATABASE
        # =================================================

        self.embedding_path = (
            "face_data/embeddings/embeddings.pkl"
        )

        # =================================================
        # INSIGHTFACE
        # =================================================

        self.app = FaceAnalysis(
            name="buffalo_l"
        )

        self.app.prepare(
            ctx_id=0,
            det_size=(640, 640)
        )

    # =====================================================
    # ENCODE DATASET
    # =====================================================

    def encode_dataset(self):

        database = {}

        # =================================================
        # CHECK DATASET
        # =================================================

        if not os.path.exists(
            self.dataset_path
        ):

            print(
                "Dataset folder not found:"
            )

            print(
                self.dataset_path
            )

            return

        # =================================================
        # GET STUDENT FOLDERS
        # =================================================

        students = sorted(
            os.listdir(
                self.dataset_path
            )
        )

        if len(students) == 0:

            print(
                "No student dataset found."
            )

            return

        print()
        print(
            "=" * 60
        )

        print(
            "FACE ENCODING"
        )

        print(
            "=" * 60
        )

        print(
            f"Students found : {len(students)}"
        )

        # =================================================
        # PROCESS EACH STUDENT
        # =================================================

        for student_id in students:

            student_folder = os.path.join(
                self.dataset_path,
                student_id
            )

            # -------------------------------------------------
            # Ignore files
            # -------------------------------------------------

            if not os.path.isdir(
                student_folder
            ):

                continue

            print()
            print(
                "-" * 60
            )

            print(
                f"Student : {student_id}"
            )

            print(
                "-" * 60
            )

            embeddings = []

            # =================================================
            # GET IMAGES
            # =================================================

            images = sorted(
                os.listdir(
                    student_folder
                )
            )

            if len(images) == 0:

                print(
                    "No images found."
                )

                continue

            # =================================================
            # PROCESS IMAGES
            # =================================================

            for image_name in images:

                image_path = os.path.join(
                    student_folder,
                    image_name
                )

                # -------------------------------------------------
                # Only image files
                # -------------------------------------------------

                if not image_name.lower().endswith(
                    (
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".webp"
                    )
                ):

                    continue

                image = cv2.imread(
                    image_path
                )

                if image is None:

                    print(
                        f"Skipped : "
                        f"{image_name} "
                        f"(cannot read)"
                    )

                    continue

                # =================================================
                # FACE DETECTION
                # =================================================

                try:

                    faces = self.app.get(
                        image
                    )

                except Exception as error:

                    print(
                        f"Skipped : "
                        f"{image_name} "
                        f"(error: {error})"
                    )

                    continue

                # -------------------------------------------------
                # No face
                # -------------------------------------------------

                if len(faces) == 0:

                    print(
                        f"Skipped : "
                        f"{image_name} "
                        f"(no face)"
                    )

                    continue

                # =================================================
                # SELECT LARGEST FACE
                # =================================================

                face = max(
                    faces,
                    key=lambda f:
                    (
                        f.bbox[2]
                        - f.bbox[0]
                    )
                    *
                    (
                        f.bbox[3]
                        - f.bbox[1]
                    )
                )

                # =================================================
                # GET EMBEDDING
                # =================================================

                embedding = (
                    face.embedding
                )

                if embedding is None:

                    print(
                        f"Skipped : "
                        f"{image_name} "
                        f"(no embedding)"
                    )

                    continue

                # =================================================
                # NORMALIZE EMBEDDING
                # =================================================

                norm = np.linalg.norm(
                    embedding
                )

                if norm == 0:

                    print(
                        f"Skipped : "
                        f"{image_name} "
                        f"(invalid embedding)"
                    )

                    continue

                embedding = (
                    embedding / norm
                )

                embeddings.append(
                    embedding
                )

                print(
                    f"Encoded : "
                    f"{image_name}"
                )

            # =================================================
            # NO VALID EMBEDDING
            # =================================================

            if len(embeddings) == 0:

                print(
                    f"No valid face "
                    f"embedding for "
                    f"{student_id}"
                )

                continue

            # =================================================
            # AVERAGE EMBEDDING
            # =================================================

            mean_embedding = np.mean(
                embeddings,
                axis=0
            )

            # =================================================
            # NORMALIZE FINAL EMBEDDING
            # =================================================

            norm = np.linalg.norm(
                mean_embedding
            )

            if norm == 0:

                print(
                    f"Invalid final "
                    f"embedding for "
                    f"{student_id}"
                )

                continue

            mean_embedding = (
                mean_embedding / norm
            )

            # =================================================
            # SAVE
            # =================================================

            database[
                str(student_id)
            ] = mean_embedding

            print()
            print(
                f"SUCCESS : "
                f"{student_id}"
            )

            print(
                f"Valid images : "
                f"{len(embeddings)}"
            )

        # =================================================
        # NO STUDENTS ENCODED
        # =================================================

        if len(database) == 0:

            print()
            print(
                "No valid student "
                "embeddings were created."
            )

            return

        # =================================================
        # CREATE EMBEDDING DIRECTORY
        # =================================================

        embedding_directory = (
            os.path.dirname(
                self.embedding_path
            )
        )

        os.makedirs(
            embedding_directory,
            exist_ok=True
        )

        # =================================================
        # SAVE EMBEDDINGS
        # =================================================

        with open(
            self.embedding_path,
            "wb"
        ) as file:

            pickle.dump(
                database,
                file
            )

        # =================================================
        # RESULT
        # =================================================

        print()
        print(
            "=" * 60
        )

        print(
            "EMBEDDING COMPLETE"
        )

        print(
            "=" * 60
        )

        print(
            f"Students encoded : "
            f"{len(database)}"
        )

        print(
            f"Embedding file : "
            f"{self.embedding_path}"
        )

        print(
            "=" * 60
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=" * 60
    )

    print(
        "AI Face Encoder"
    )

    print(
        "=" * 60
    )

    encoder = FaceEncoder()

    encoder.encode_dataset()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()