# =============================================================================
# MAKINE OGRENIMI ODEVI
# Uyku Sagligi ve Gunluk Performans - Uyku Bozuklugu Riski Tahmini
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, classification_report, confusion_matrix)

from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from catboost import CatBoostClassifier
import time

print("=" * 70)
print("Tum kutuphaneler basariyla yuklendi! (Hafifletilmis 9 Model)")
print("=" * 70)

# Veri Yukleme ve Temizleme
df = pd.read_csv('sleep_health_dataset.csv')
drop_cols = ['person_id', 'cognitive_performance_score', 'felt_rested']
df_clean = df.drop(columns=drop_cols)

kategorik_sutunlar = ['gender', 'occupation', 'country', 'chronotype', 'mental_health_condition', 'season', 'day_type']
for col in kategorik_sutunlar:
    le = LabelEncoder()
    df_clean[col] = le.fit_transform(df_clean[col])

le_target = LabelEncoder()
df_clean['sleep_disorder_risk'] = le_target.fit_transform(df_clean['sleep_disorder_risk'])

X = df_clean.drop('sleep_disorder_risk', axis=1)
y = df_clean['sleep_disorder_risk']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Model Egitimi
sonuclar = {}

# SVM cok yavas oldugu icin sadece ona ozel kucuk bir orneklem aliyoruz
np.random.seed(42)
sample_idx = np.random.choice(len(X_train_scaled), size=15000, replace=False)
X_train_sample = X_train_scaled[sample_idx]
y_train_sample = y_train.iloc[sample_idx]

def train_and_eval(model_name, model, X_tr, y_tr, X_te, y_te):
    print(f"\n--- {model_name} Egitiliyor ---")
    start = time.time()
    model.fit(X_tr, y_tr)
    train_time = time.time() - start
    
    y_pred = model.predict(X_te)
    
    acc = accuracy_score(y_te, y_pred)
    prec = precision_score(y_te, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_te, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_te, y_pred, average='weighted', zero_division=0)
    
    sonuclar[model_name] = {'Accuracy': acc, 'Precision': prec, 'Recall': rec, 'F1-Score': f1, 'Sure': train_time, 'Preds': y_pred}
    print(f"Basarili! Sure: {train_time:.2f} sn | F1-Score: {f1:.4f}")

# 9 MODEL (Hafifletilmis)
train_and_eval('kNN', KNeighborsClassifier(n_neighbors=12, weights='distance', p=1), X_train_scaled, y_train, X_test_scaled, y_test)
train_and_eval('Naive Bayes', GaussianNB(), X_train_scaled, y_train, X_test_scaled, y_test)
train_and_eval('LSVM', LinearSVC(max_iter=2000, random_state=42), X_train_scaled, y_train, X_test_scaled, y_test)
train_and_eval('RBF SVM', SVC(kernel='rbf', random_state=42), X_train_sample, y_train_sample, X_test_scaled, y_test)
train_and_eval('Random Forest', RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1), X_train_scaled, y_train, X_test_scaled, y_test)
train_and_eval('MLP (Sinir Agi)', MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=300, random_state=42, early_stopping=True), X_train_scaled, y_train, X_test_scaled, y_test)
train_and_eval('XGBoost', XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, eval_metric='mlogloss', verbosity=0), X_train_scaled, y_train, X_test_scaled, y_test)
train_and_eval('Logistic Regression', LogisticRegression(max_iter=1000, random_state=42), X_train_scaled, y_train, X_test_scaled, y_test)
train_and_eval('CatBoost', CatBoostClassifier(iterations=100, random_state=42, verbose=0), X_train_scaled, y_train, X_test_scaled, y_test)

# Sonuclar ve Grafikler
print("\n" + "=" * 70)
print("Sonuclar ve Karsilastirma Kaydediliyor...")

model_names = list(sonuclar.keys())

# Bar chart (Grafik 3)
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
metrics_list = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
colors_list = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#ff9ff3', '#feca57']

for idx, metric in enumerate(metrics_list):
    ax = axes[idx // 2][idx % 2]
    values = [sonuclar[m][metric] for m in model_names]
    bars = ax.bar(model_names, values, color=colors_list, edgecolor='black', alpha=0.85)
    ax.set_title(metric, fontsize=14)
    ax.set_ylim(0, 1.0)
    ax.tick_params(axis='x', rotation=45, labelsize=10)
import os
os.makedirs('tablolar', exist_ok=True)
os.makedirs('grafikler', exist_ok=True)
plt.tight_layout()
plt.savefig('grafikler/grafik3.png', dpi=150)
plt.close()

# Confusion Matrices (3x3 izgara = 9 model)
fig, axes = plt.subplots(3, 3, figsize=(20, 18))
for idx, model_name in enumerate(model_names):
    row = idx // 3
    col = idx % 3
    ax = axes[row][col]
    cm = confusion_matrix(y_test, sonuclar[model_name]['Preds'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax, xticklabels=le_target.classes_, yticklabels=le_target.classes_)
    ax.set_title(model_name)
plt.tight_layout()
plt.savefig('grafikler/grafik4.png', dpi=150)
plt.close()

# Export CSV (Preds haric)
export_data = {k: {m: v for m, v in metrics.items() if m != 'Preds'} for k, metrics in sonuclar.items()}
df_sonuc = pd.DataFrame(export_data).T
df_sonuc = df_sonuc.sort_values('F1-Score', ascending=False)
df_sonuc[['Accuracy', 'Recall', 'Precision', 'F1-Score']].round(4).to_csv('tablolar/sonuc_tablosu.csv')

print("Islem tamamlandi! (LightGBM kaldirildi)")
