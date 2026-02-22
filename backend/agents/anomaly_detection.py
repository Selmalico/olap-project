import pandas as pd
import numpy as np
from agents.base_agent import BaseAgent


class AnomalyDetectionAgent(BaseAgent):
    name = "anomaly_detection"
    description = "Detects statistical outliers using Z-score analysis"

    def run(self, query: str, params: dict) -> dict:
        data = params.get("data", [])
        if not data or len(data) < 4:
            return {"anomalies": [], "flagged_rows": []}

        df = pd.DataFrame(data)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        anomalies = []
        flagged_rows = []

        for col in numeric_cols:
            if df[col].std() == 0:
                continue
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            outlier_mask = z_scores > 2.5
            outlier_indices = df[outlier_mask].index.tolist()

            for idx in outlier_indices:
                val = df[col].iloc[idx]
                mean = df[col].mean()
                pct_diff = abs(val - mean) / mean * 100
                # Get a label column if available
                label_cols = [c for c in df.columns if c in
                              ["region", "country", "category", "year", "quarter", "month"]]
                label = str(df[label_cols[0]].iloc[idx]) if label_cols else f"row {idx}"
                anomalies.append(
                    f"{col} for {label}: {val:,.2f} is {pct_diff:.1f}% from mean ({mean:,.2f})"
                )
                flagged_rows.append(idx)

        return {
            "anomalies": anomalies[:5],  # Cap at 5 most notable
            "flagged_rows": list(set(flagged_rows)),
            "columns_analyzed": numeric_cols
        }
