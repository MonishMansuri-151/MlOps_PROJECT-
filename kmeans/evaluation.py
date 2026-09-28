import sys

from sklearn.metrics import silhouette_score

from src.logger import logging
from src.exception import CustomException


def evaluate_clustering(
    scaled_features,
    labels
):
    try:

        unique_labels = set(labels)

        if len(unique_labels) < 2:
            return {
                "silhouette_score": None,
                "message": (
                    "Silhouette score requires "
                    "at least two clusters."
                )
            }

        if len(scaled_features) <= len(unique_labels):
            return {
                "silhouette_score": None,
                "message": (
                    "Not enough samples for "
                    "silhouette evaluation."
                )
            }

        score = silhouette_score(
            scaled_features,
            labels
        )

        logging.info(
            f"K-Means silhouette score: {score:.4f}"
        )

        return {
            "silhouette_score": round(
                float(score),
                4
            )
        }

    except Exception as e:

        logging.error(
            f"K-Means evaluation failed: {e}"
        )

        raise CustomException(e, sys)