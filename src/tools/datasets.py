from dataclasses import dataclass

@dataclass
class Dataset:
    X_train: list
    X_test: list
    y_train: list
    y_test: list
    name: str

class DatasetTool:
    name = "dataset_tool"

    def load(self, name: str = "iris", test_size: float = 0.25, seed: int = 42) -> Dataset:
        try:
            from sklearn import datasets as skds
            from sklearn.model_selection import train_test_split
            if name == "iris":
                data = skds.load_iris()
            else:
                raise ValueError(f"Dataset '{name}' não suportado no boilerplate.")
            X_train, X_test, y_train, y_test = train_test_split(
                data.data, data.target, test_size=test_size, random_state=seed
            )
            return Dataset(X_train, X_test, y_train, y_test, name)
        except Exception:
            # Fallback leve sem scikit-learn: dataset sintético pequeno
            import random
            random.seed(seed)
            X = [[random.random(), random.random()] for _ in range(40)]
            y = [1 if (a + b) > 1.0 else 0 for a, b in X]
            split = int(len(X) * (1.0 - test_size))
            return Dataset(X[:split], X[split:], y[:split], y[split:], f"synthetic-{name}")
