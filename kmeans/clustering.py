import sys

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from kmeans.config import KMEANS_DEFAULT_CLUSTERS
from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)

def cluster_department_demand(
    processed_data,
    n_clusters: int = KMEANS_DEFAULT_CLUSTERS
):
    try:
        if not processed_data:
            return {
                "success": False,
                "message": "No analytics data available.",
                "clusters": []
            }

        df = pd.DataFrame(processed_data)

        # Department-wise appointment count
        # department_data = (
        #     df.groupby(
        #         [
        #             "department_id",
        #             "department_name"
        #         ]
        #     )
        #     .size()
        #     .reset_index(
        #         name="appointment_count"
        #     )
        # )
        department_data = (
            df.groupby(
                ["department_id", "department_name"]
            )
            .agg(
                appointment_count=(
                    "appointment_id",
                    "count"
                ),
                unique_patient_count=(
                    "patient_id",
                    "nunique"
                ),
                unique_doctor_count=(
                    "doctor_id",
                    "nunique"
                )
            )
            .reset_index()
        )

        if len(department_data) < n_clusters:
            n_clusters = len(department_data)

        if n_clusters < 1:
            return {
                "success": False,
                "message": "Not enough data for clustering.",
                "clusters": []
            }

        # features = department_data[
        #     ["appointment_count"]
        # ]
        features = department_data[
                [
                    "appointment_count",
                    "unique_patient_count",
                    "unique_doctor_count"
                ]
            ]

        scaler = StandardScaler()

        scaled_features = scaler.fit_transform(
            features
        )

        model = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )

        department_data["cluster"] = (
            model.fit_predict(scaled_features)
        )

        logger.info(
            "Department demand K-Means clustering completed."
        )

        return {
            "success": True,
            "clusters": department_data.to_dict(
                orient="records"
            )
        }

    except Exception as e:
        logger.error(
            f"K-Means clustering failed: {e}"
        )
        raise CustomException(e, sys)