from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import json
from pathlib import Path

class MetricsTool:
    name = "metrics_tool"

    def train_eval_logreg(self, dataset, l2: float = 1.0, max_iter: int = 200, out_path: str = "./results.json"):
        clf = LogisticRegression(C=1.0/l2 if l2>0 else 1e6, max_iter=max_iter)
        clf.fit(dataset.X_train, dataset.y_train)
        preds = clf.predict(dataset.X_test)
        acc = accuracy_score(dataset.y_test, preds)
        Path(out_path).write_text(json.dumps({"accuracy": float(acc)}, indent=2))
        return {"accuracy": float(acc), "results_path": out_path}
