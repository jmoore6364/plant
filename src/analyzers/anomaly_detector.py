"""Machine learning-based anomaly detection."""

from typing import List, Optional, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta

from src.models.schemas import SystemMetrics, Anomaly, AnomalyType


class AnomalyDetector:
    """ML-based anomaly detector for system metrics."""

    def __init__(self, contamination: float = 0.1) -> None:
        """
        Initialize the anomaly detector.

        Args:
            contamination: Expected proportion of outliers (0.0 to 0.5)
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = [
            "cpu_percent",
            "memory_percent",
            "disk_usage_percent",
            "process_count",
        ]

    def train(self, metrics_history: List[SystemMetrics]) -> None:
        """
        Train the anomaly detection model on historical metrics.

        Args:
            metrics_history: List of historical system metrics
        """
        if len(metrics_history) < 10:
            raise ValueError("Need at least 10 samples to train the model")

        # Extract features
        X = self._extract_features(metrics_history)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model.fit(X_scaled)
        self.is_trained = True

    def detect(self, metrics: SystemMetrics) -> Tuple[bool, float]:
        """
        Detect if given metrics are anomalous.

        Args:
            metrics: System metrics to check

        Returns:
            Tuple of (is_anomaly, anomaly_score)
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before detection")

        # Extract and scale features
        X = self._extract_features([metrics])
        X_scaled = self.scaler.transform(X)

        # Predict
        prediction = self.model.predict(X_scaled)[0]
        score = self.model.score_samples(X_scaled)[0]

        # prediction is -1 for anomaly, 1 for normal
        is_anomaly = prediction == -1

        # Convert score to 0-1 range (more negative = more anomalous)
        # Scores typically range from -0.5 to 0.5
        anomaly_score = max(0, min(1, (-score + 0.5)))

        return is_anomaly, anomaly_score

    def detect_batch(
        self, metrics_list: List[SystemMetrics]
    ) -> List[Tuple[bool, float, SystemMetrics]]:
        """
        Detect anomalies in a batch of metrics.

        Args:
            metrics_list: List of metrics to check

        Returns:
            List of (is_anomaly, score, metrics) tuples
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before detection")

        X = self._extract_features(metrics_list)
        X_scaled = self.scaler.transform(X)

        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)

        results = []
        for i, metrics in enumerate(metrics_list):
            is_anomaly = predictions[i] == -1
            anomaly_score = max(0, min(1, (-scores[i] + 0.5)))
            results.append((is_anomaly, anomaly_score, metrics))

        return results

    def _extract_features(self, metrics_list: List[SystemMetrics]) -> np.ndarray:
        """Extract feature matrix from metrics."""
        features = []
        for m in metrics_list:
            features.append([
                m.cpu_percent,
                m.memory_percent,
                m.disk_usage_percent,
                float(m.process_count),
            ])
        return np.array(features)

    def classify_anomaly(
        self, metrics: SystemMetrics, anomaly_score: float
    ) -> Optional[Anomaly]:
        """
        Classify the type of anomaly based on metrics.

        Args:
            metrics: The anomalous metrics
            anomaly_score: Anomaly confidence score

        Returns:
            Classified Anomaly object or None
        """
        anomaly_type = None
        description = ""
        severity = "medium"
        evidence = []

        # CPU spike
        if metrics.cpu_percent > 90:
            anomaly_type = AnomalyType.CPU_SPIKE
            description = f"CPU usage spike: {metrics.cpu_percent:.1f}%"
            severity = "critical" if metrics.cpu_percent > 95 else "high"
            evidence.append(f"CPU at {metrics.cpu_percent:.1f}%")

        # Memory leak detection (high memory usage)
        elif metrics.memory_percent > 85:
            anomaly_type = AnomalyType.MEMORY_LEAK
            description = f"High memory usage: {metrics.memory_percent:.1f}%"
            severity = "critical" if metrics.memory_percent > 95 else "high"
            evidence.append(f"Memory at {metrics.memory_percent:.1f}%")
            evidence.append(f"Available: {metrics.memory_available_mb:.0f} MB")

        # Disk full
        elif metrics.disk_usage_percent > 90:
            anomaly_type = AnomalyType.DISK_FULL
            description = f"Disk space critical: {metrics.disk_usage_percent:.1f}%"
            severity = "critical" if metrics.disk_usage_percent > 95 else "high"
            evidence.append(f"Disk at {metrics.disk_usage_percent:.1f}%")
            evidence.append(f"Free space: {metrics.disk_free_gb:.2f} GB")

        # General anomaly if specific type not identified
        else:
            anomaly_type = AnomalyType.UNUSUAL_TRAFFIC
            description = "Unusual system behavior detected"
            severity = "medium"
            evidence.append(f"CPU: {metrics.cpu_percent:.1f}%")
            evidence.append(f"Memory: {metrics.memory_percent:.1f}%")

        if anomaly_type:
            return Anomaly(
                id=f"anomaly_{metrics.timestamp.isoformat()}",
                type=anomaly_type,
                severity=severity,
                timestamp=metrics.timestamp,
                description=description,
                affected_component="system",
                confidence_score=anomaly_score,
                evidence=evidence,
                metrics=metrics,
            )

        return None

    def detect_trends(
        self, metrics_history: List[SystemMetrics], window_size: int = 10
    ) -> List[dict]:
        """
        Detect concerning trends in metrics over time.

        Args:
            metrics_history: Historical metrics
            window_size: Window for trend analysis

        Returns:
            List of detected trends
        """
        if len(metrics_history) < window_size:
            return []

        trends = []
        recent = metrics_history[-window_size:]

        # Memory leak detection (steady increase)
        memory_values = [m.memory_percent for m in recent]
        memory_trend = np.polyfit(range(len(memory_values)), memory_values, 1)[0]

        if memory_trend > 1.0:  # Increasing > 1% per sample
            trends.append({
                "type": "memory_leak_suspected",
                "severity": "high",
                "description": f"Memory usage increasing at {memory_trend:.2f}% per interval",
                "evidence": f"Memory went from {memory_values[0]:.1f}% to {memory_values[-1]:.1f}%",
            })

        # CPU trend
        cpu_values = [m.cpu_percent for m in recent]
        cpu_trend = np.polyfit(range(len(cpu_values)), cpu_values, 1)[0]

        if cpu_trend > 2.0:  # Significant CPU increase
            trends.append({
                "type": "cpu_increasing",
                "severity": "medium",
                "description": f"CPU usage trending upward at {cpu_trend:.2f}% per interval",
                "evidence": f"CPU went from {cpu_values[0]:.1f}% to {cpu_values[-1]:.1f}%",
            })

        # Disk space
        disk_values = [m.disk_usage_percent for m in recent]
        disk_trend = np.polyfit(range(len(disk_values)), disk_values, 1)[0]

        if disk_trend > 0.5:  # Disk filling up
            trends.append({
                "type": "disk_filling",
                "severity": "high" if recent[-1].disk_usage_percent > 80 else "medium",
                "description": f"Disk usage increasing at {disk_trend:.2f}% per interval",
                "evidence": f"Disk went from {disk_values[0]:.1f}% to {disk_values[-1]:.1f}%",
            })

        return trends

    def get_feature_importance(self, metrics: SystemMetrics) -> dict:
        """
        Get which features contributed most to anomaly detection.

        Args:
            metrics: The metrics to analyze

        Returns:
            Dictionary of feature importance scores
        """
        if not self.is_trained:
            return {}

        # Get feature values
        feature_values = {
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "disk_usage_percent": metrics.disk_usage_percent,
            "process_count": metrics.process_count,
        }

        # Calculate z-scores for each feature
        X = self._extract_features([metrics])
        X_scaled = self.scaler.transform(X)[0]

        # Higher absolute z-score means more unusual
        feature_scores = {}
        for i, name in enumerate(self.feature_names):
            feature_scores[name] = {
                "value": feature_values[name],
                "z_score": abs(X_scaled[i]),
                "anomalous": abs(X_scaled[i]) > 2.0,
            }

        return feature_scores
