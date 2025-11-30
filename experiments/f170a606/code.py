import numpy as np
import json
import os
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

# Set fixed random seed for reproducibility
SEED = 42
np.random.seed(SEED)

# Create output directory if not exists
OUTPUT_DIR = './experiments/f170a606'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Iris dataset
from sklearn.utils import shuffle
iris = load_iris()
X, y = iris.data, iris.target
# Shuffle to ensure random distribution
X, y = shuffle(X, y, random_state=SEED)

# Define logistic regression baseline function
# Note: sklearn LogisticRegression default penalty='l2', for no regularization use penalty='none'
# penalty='none' requires solver='lbfgs' with sklearn >=0.22
# Also, we fix max_iter for convergence

def logistic_regression_cv(X, y, penalty, C=1.0, dropout_rate=0.0, n_splits=5, random_state=SEED):
    """
    Runs logistic regression with given penalty and parameters using k-fold CV.
    dropout_rate simulates input dropout at the train time only.
    Returns list of accuracy scores for each fold.
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    acc_scores = []

    for train_index, test_index in kf.split(X):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]

        # Simulate dropout in input layer if dropout_rate > 0
        if dropout_rate > 0:
            # For each training sample, randomly drop input features with dropout_rate
            dropout_mask = np.random.binomial(1, 1 - dropout_rate, size=X_train.shape)
            X_train_dropped = X_train * dropout_mask
        else:
            X_train_dropped = X_train

        # Set solver and penalty
        if penalty == 'none':
            clf = LogisticRegression(penalty='none', solver='lbfgs', max_iter=1000, random_state=random_state)
        else:
            clf = LogisticRegression(penalty=penalty, C=C, solver='lbfgs', max_iter=1000, random_state=random_state)

        clf.fit(X_train_dropped, y_train)
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        acc_scores.append(acc)

    return acc_scores


# Experimental conditions and parameters
C_values = [0.001, 0.01, 0.1, 1, 10]
results = {
    'baseline': None,
    'l2': {},
    'dropout': None,
    'l2_dropout': {}
}

# Baseline: Logistic Regression no regularization (penalty='none')
baseline_accs = logistic_regression_cv(X, y, penalty='none')
baseline_mean_acc = np.mean(baseline_accs)
results['baseline'] = {'fold_accuracies': baseline_accs, 'mean_accuracy': baseline_mean_acc}

# Dropout only: dropout_rate=0.1, no L2 regularization
dropout_accs = logistic_regression_cv(X, y, penalty='none', dropout_rate=0.1)
dropout_mean_acc = np.mean(dropout_accs)
results['dropout'] = {'fold_accuracies': dropout_accs, 'mean_accuracy': dropout_mean_acc}

# L2 only: penalty='l2' with C in C_values
for C in C_values:
    l2_accs = logistic_regression_cv(X, y, penalty='l2', C=C)
    l2_mean_acc = np.mean(l2_accs)
    results['l2'][str(C)] = {'fold_accuracies': l2_accs, 'mean_accuracy': l2_mean_acc}

# L2 + dropout combined models
for C in C_values:
    l2_dropout_accs = logistic_regression_cv(X, y, penalty='l2', C=C, dropout_rate=0.1)
    l2_dropout_mean_acc = np.mean(l2_dropout_accs)
    results['l2_dropout'][str(C)] = {'fold_accuracies': l2_dropout_accs, 'mean_accuracy': l2_dropout_mean_acc}

# Check if any combined model achieves at least 0.02 improvement over baseline
improved = False
improvements = {}
for C in C_values:
    delta = results['l2_dropout'][str(C)]['mean_accuracy'] - baseline_mean_acc
    improvements[str(C)] = delta
    if delta >= 0.02:
        improved = True

results['improvements_over_baseline'] = improvements
results['combined_improves_over_baseline'] = improved

# Prepare plot: Accuracy vs C for the four conditions
# For plotting, baseline and dropout are constant (no varying C), plot as horizontal lines
plt.figure(figsize=(8,6))
xs = C_values
l2_means = [results['l2'][str(C)]['mean_accuracy'] for C in C_values]
l2_dropout_means = [results['l2_dropout'][str(C)]['mean_accuracy'] for C in C_values]

plt.plot(xs, l2_means, label='L2 Regularization', marker='o')
plt.plot(xs, l2_dropout_means, label='L2 + Dropout (0.1)', marker='o')
plt.axhline(y=baseline_mean_acc, color='r', linestyle='--', label='Baseline (No reg)')
plt.axhline(y=dropout_mean_acc, color='g', linestyle='--', label='Dropout only (0.1)')

plt.xscale('log')
plt.xlabel('Regularization parameter C (log scale)')
plt.ylabel('Mean Accuracy (5-fold CV)')
plt.title('Model Accuracy vs L2 Regularization parameter C\nNode f170a606 on Iris dataset')
plt.legend()
plt.grid(True)

plot_path = os.path.join(OUTPUT_DIR, 'accuracy_vs_C.png')
plt.savefig(plot_path)
plt.close()

# Save results in JSON
results_path = os.path.join(OUTPUT_DIR, 'results.json')
with open(results_path, 'w') as f:
    json.dump(results, f, indent=4)


if __name__ == '__main__':
    print(f"Baseline mean accuracy: {baseline_mean_acc:.4f}")
    print(f"Dropout only mean accuracy: {dropout_mean_acc:.4f}")
    print("L2 mean accuracies:")
    for C in C_values:
        print(f"  C={C}: {results['l2'][str(C)]['mean_accuracy']:.4f}")
    print("L2+Dropout mean accuracies:")
    for C in C_values:
        print(f"  C={C}: {results['l2_dropout'][str(C)]['mean_accuracy']:.4f}")
    if improved:
        print(f"At least one combined L2+Dropout model improved at least 0.02 over baseline")
    else:
        print(f"No combined model achieved 0.02 improvement over baseline")
    print(f"Plot saved to: {plot_path}")
    print(f"Results saved to: {results_path}")