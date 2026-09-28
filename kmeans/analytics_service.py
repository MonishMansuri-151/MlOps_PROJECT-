import sys

from kmeans.data_loader import load_appointment_analytics_data
from kmeans.preprocessing import prepare_appointment_data
from kmeans.clustering import cluster_department_demand
from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)

def get_department_demand_analytics():
    try:
        rows = load_appointment_analytics_data()

        processed_data = prepare_appointment_data(rows)

        clustering_result = cluster_department_demand(
            processed_data,
            n_clusters=3
        )

        if not clustering_result["success"]:
            return clustering_result

        clusters = clustering_result["clusters"]

        total_appointments = len(processed_data)

        department_count = len(clusters)

        return {
            "success": True,
            "total_appointments": total_appointments,
            "department_count": department_count,
            "clusters": clusters
        }

    except Exception as e:
        logger.error(
            f"Department demand analytics failed: {e}"
        )
        raise CustomException(e, sys)