import numpy as np
import json
import os
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Reproducibility
SEED = 42
np.random.seed(SEED)

# Parameters
C_values = [0.01, 0.1, 1, 10, 100]
TEST_SIZE = 0.3
DROP_RATE = 0.1  # Dropout rate simulated as Gaussian noise std dev

# Load data
iris = load_iris()
X = iris.data
y = iris.target

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=SEED, stratify=y)

# Function to add Gaussian noise simulating dropout
# applies noise only during training phase
def apply_dropout(X, drop_rate, seed=SEED):
    rng = np.random.RandomState(seed)
    noise = rng.normal(loc=0.0, scale=drop_rate, size=X.shape)
    X_noisy = X + noise
    return X_noisy

results = {}

# Baseline model: very large C (no regularization)
clf_baseline = LogisticRegression(C=1e6, penalty='l2', solver='lbfgs', multi_class='auto', max_iter=2000, random_state=SEED)
clf_baseline.fit(X_train, y_train)
acc_baseline = accuracy_score(y_test, clf_baseline.predict(X_test))
results['baseline'] = acc_baseline

# Hypothesis 1: L2 regularization effect
h1_accuracies = []
for C in C_values:
    clf = LogisticRegression(C=C, penalty='l2', solver='lbfgs', multi_class='auto', max_iter=2000, random_state=SEED)
    clf.fit(X_train, y_train)
    acc = accuracy_score(y_test, clf.predict(X_test))
    h1_accuracies.append(acc)
results['hypothesis_1'] = {"C_values": C_values, "accuracies": h1_accuracies}

# Hypothesis 2: L2 + dropout (Gaussian noise on features during training)
h2_accuracies = []
for C in C_values:
    X_train_noisy = apply_dropout(X_train, DROP_RATE, seed=SEED)
    clf = LogisticRegression(C=C, penalty='l2', solver='lbfgs', multi_class='auto', max_iter=2000, random_state=SEED)
    clf.fit(X_train_noisy, y_train)
    acc = accuracy_score(y_test, clf.predict(X_test))
    h2_accuracies.append(acc)

results['hypothesis_2'] = {"C_values": C_values, "accuracies": h2_accuracies}

# Save results
os.makedirs('./experiments/d5068c16', exist_ok=True)
with open('./experiments/d5068c16/results.json', 'w') as f:
    json.dump(results, f, indent=4)

# Plot results
plt.figure(figsize=(10,6))
plt.plot(C_values, h1_accuracies, marker='o', label='L2 Regularization')
plt.plot(C_values, h2_accuracies, marker='o', label='L2 + Dropout (Gaussian noise)')
plt.axhline(y=acc_baseline, color='r', linestyle='--', label='Baseline (No Reg)')
plt.xscale('log')
plt.xlabel('Regularization Parameter C (log scale)')
plt.ylabel('Test Accuracy')
plt.title('Accuracy vs C for Logistic Regression on Iris Dataset')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('./experiments/d5068c16/accuracy_vs_C.png')
plt.close()

# End of script
