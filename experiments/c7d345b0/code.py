import os
import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
from scipy.stats import ttest_rel

# Fixed seed for reproducibility
SEED = 42
np.random.seed(SEED)

# Experiment directory
EXP_DIR = './experiments/c7d345b0'
os.makedirs(EXP_DIR, exist_ok=True)

# Load Iris dataset
data = load_iris()
X = data.data
y = data.target

# 5-fold CV
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

# Baseline logistic regression parameters
baseline_clf = LogisticRegression(random_state=SEED, max_iter=1000)

# L2 regularization Cs to test
Cs = [0.001, 0.01, 0.1, 1, 10, 100]

# Function: apply light dropout (0.1 dropout rate) to input features during training only
# Input: X_train (np.array), dropout_rate (float), random_state (int)
def apply_dropout(X_train, dropout_rate=0.1, random_state=None):
    if random_state is not None:
        rng = np.random.RandomState(random_state)
    else:
        rng = np.random
    mask = rng.binomial(1, 1 - dropout_rate, size=X_train.shape)
    return X_train * mask

# Evaluate a model using StratifiedKFold
# model_factory is a function that takes train indices and returns a fitted classifier
def evaluate_model(model_factory):
    accuracies = []
    for train_idx, test_idx in kf.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        clf = model_factory(X_train, y_train)
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        accuracies.append(acc)
    return np.array(accuracies)

# Baseline model factory
def baseline_factory(X_train, y_train):
    clf = LogisticRegression(random_state=SEED, max_iter=1000)
    clf.fit(X_train, y_train)
    return clf

# L2 model factory with given C
def l2_factory(C):
    def factory(X_train, y_train):
        clf = LogisticRegression(penalty='l2', C=C, solver='lbfgs', random_state=SEED, max_iter=1000)
        clf.fit(X_train, y_train)
        return clf
    return factory

# Dropout model factory
def dropout_factory(X_train, y_train):
    # Apply dropout only during training, fixed random seed + train_idx to keep reproducibility
    X_train_dropout = apply_dropout(X_train, dropout_rate=0.1, random_state=SEED)
    clf = LogisticRegression(random_state=SEED, max_iter=1000)
    clf.fit(X_train_dropout, y_train)
    return clf

# L2 + dropout model factory
def l2_dropout_factory(C):
    def factory(X_train, y_train):
        X_train_dropout = apply_dropout(X_train, dropout_rate=0.1, random_state=SEED)
        clf = LogisticRegression(penalty='l2', C=C, solver='lbfgs', random_state=SEED, max_iter=1000)
        clf.fit(X_train_dropout, y_train)
        return clf
    return factory

# Collect results
results = {}

# Baseline evaluation
baseline_accuracies = evaluate_model(baseline_factory)
results['baseline'] = {
    'parameters': {},
    'mean_accuracy': float(np.mean(baseline_accuracies)),
    'std_accuracy': float(np.std(baseline_accuracies)),
    'accuracies': baseline_accuracies.tolist()
}

# L2 regularization results
l2_results = {}
for C in Cs:
    accuracies = evaluate_model(l2_factory(C))
    l2_results[str(C)] = {
        'mean_accuracy': float(np.mean(accuracies)),
        'std_accuracy': float(np.std(accuracies)),
        'accuracies': accuracies.tolist()
    }
results['l2'] = l2_results

# Dropout only
dropout_accuracies = evaluate_model(dropout_factory)
dropout_mean = float(np.mean(dropout_accuracies))
dropout_std = float(np.std(dropout_accuracies))
results['dropout'] = {
    'parameters': {'dropout_rate': 0.1},
    'mean_accuracy': dropout_mean,
    'std_accuracy': dropout_std,
    'accuracies': dropout_accuracies.tolist()
}

# L2 + dropout
l2_dropout_results = {}
for C in Cs:
    accuracies = evaluate_model(l2_dropout_factory(C))
    l2_dropout_results[str(C)] = {
        'mean_accuracy': float(np.mean(accuracies)),
        'std_accuracy': float(np.std(accuracies)),
        'accuracies': accuracies.tolist()
    }
results['l2_dropout'] = l2_dropout_results

# Statistical tests: paired t-test comparing baseline accuracies vs other method accuracies
# p-values stored in results
# For L2
l2_pvalues = {}
for C in Cs:
    l2_acc = np.array(l2_results[str(C)]['accuracies'])
    t_stat, p_val = ttest_rel(baseline_accuracies, l2_acc)
    l2_pvalues[str(C)] = float(p_val)
results['l2_pvalues'] = l2_pvalues

# Dropout
t_stat, p_val = ttest_rel(baseline_accuracies, dropout_accuracies)
results['dropout_pvalue'] = float(p_val)

# L2 + dropout
l2_dropout_pvalues = {}
for C in Cs:
    ld_acc = np.array(l2_dropout_results[str(C)]['accuracies'])
    t_stat, p_val = ttest_rel(baseline_accuracies, ld_acc)
    l2_dropout_pvalues[str(C)] = float(p_val)
results['l2_dropout_pvalues'] = l2_dropout_pvalues

# Save results.json
with open(os.path.join(EXP_DIR, 'results.json'), 'w') as f:
    json.dump(results, f, indent=4)

# Generate plots
# 1) Lineplot accuracy vs C (L2 only)
mean_accuracies = [l2_results[str(C)]['mean_accuracy'] for C in Cs]
std_accuracies = [l2_results[str(C)]['std_accuracy'] for C in Cs]

plt.figure(figsize=(8,6))
plt.errorbar(Cs, mean_accuracies, yerr=std_accuracies, fmt='-o', label='L2 Regularization')
plt.xscale('log')
plt.xlabel('Regularization Strength C (log scale)')
plt.ylabel('Accuracy')
plt.title('Accuracy vs L2 Regularization Strength (C)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(EXP_DIR, 'accuracy_vs_C.png'))
plt.close()

# 2) Barplot comparing baseline, dropout, best L2, and combo
best_l2_C = max(Cs, key=lambda C: l2_results[str(C)]['mean_accuracy'])
best_l2_mean = l2_results[str(best_l2_C)]['mean_accuracy']
best_l2_std = l2_results[str(best_l2_C)]['std_accuracy']

best_l2_dropout_C = max(Cs, key=lambda C: l2_dropout_results[str(C)]['mean_accuracy'])
best_l2_dropout_mean = l2_dropout_results[str(best_l2_dropout_C)]['mean_accuracy']
best_l2_dropout_std = l2_dropout_results[str(best_l2_dropout_C)]['std_accuracy']

labels = ['Baseline', 'Dropout', f'Best L2 (C={best_l2_C})', f'Combo L2+Dropout (C={best_l2_dropout_C})']
means = [results['baseline']['mean_accuracy'], dropout_mean, best_l2_mean, best_l2_dropout_mean]
stds = [results['baseline']['std_accuracy'], dropout_std, best_l2_std, best_l2_dropout_std]

x_pos = np.arange(len(labels))

plt.figure(figsize=(8,6))
plt.bar(x_pos, means, yerr=stds, capsize=5, color=['blue', 'orange', 'green', 'red'])
plt.xticks(x_pos, labels, rotation=15)
plt.ylabel('Accuracy')
plt.title('Comparison of Models')
plt.tight_layout()
plt.savefig(os.path.join(EXP_DIR, 'model_comparison.png'))
plt.close()

if __name__ == '__main__':
    print('Experiment completed. Results and figures saved in', EXP_DIR)
