from sklearn import datasets as skds
from sklearn.model_selection import train_test_split
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
        if name == "iris":
            data = skds.load_iris()
        else:
            raise ValueError(f"Dataset '{name}' não suportado no boilerplate.")
        X_train, X_test, y_train, y_test = train_test_split(data.data, data.target, test_size=test_size, random_state=seed)
        return Dataset(X_train, X_test, y_train, y_test, name)
