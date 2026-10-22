# =============================================================================
# GELISMIS METRIKLER ANALIZI (ADVANCED EVALUATION METRICS)
# ROC-AUC, Specificity (Ozgulluk), MCC, Log-Loss
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (matthews_corrcoef, confusion_matrix, 
                             roc_auc_score, log_loss, f1_score)

from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from catboost import CatBoostClassifier

os.makedirs('tablolar', exist_ok=True)
os.makedirs('grafikler', exist_ok=True)

print("=" * 70)
print("Gelismis Metrikler Analizi Baslatiliyor...")
print("Hesaplanacak Metrikler: ROC-AUC, Specificity, MCC, Log-Loss")
print("=" * 70)

# 1. VERI HAZIRLIGI
df = pd.read_csv('sleep_health_dataset.csv')
drop_cols = ['person_id', 'cognitive_performance_score', 'felt_rested']
df_clean = df.drop(columns=drop_cols)

# KLINIK OZELLIK MUHENDISLIGI (AASM & PSQI UYUMLU)
df_clean['sleep_fragmentation_index'] = (df_clean['wake_episodes_per_night'] / df_clean['sleep_duration_hrs']).round(4)
df_clean['restorative_sleep_ratio'] = (df_clean['deep_sleep_percentage'] + df_clean['rem_percentage']).round(4)

kategorik_sutunlar = ['gender', 'occupation', 'country', 'chronotype', 'mental_health_condition', 'season', 'day_type']
for col in kategorik_sutunlar:
    le = LabelEncoder()
    df_clean[col] = le.fit_transform(df_clean[col])

le_target = LabelEncoder()
df_clean['sleep_disorder_risk'] = le_target.fit_transform(df_clean['sleep_disorder_risk'])

X_all = df_clean.drop('sleep_disorder_risk', axis=1)
y_all = df_clean['sleep_disorder_risk']

# Hizli ve dengeli analiz icin 20.000 satirlik orneklem (CPU ve RAM'i yormaz)
SAMPLE_SIZE = 20000
X, _, y, _ = train_test_split(X_all, y_all, train_size=SAMPLE_SIZE, random_state=42, stratify=y_all)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

# 2. OZEL SPECIFICITY (OZGULLUK) HESAPLAMA FONKSIYONU
def calculate_specificity(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred)
    specs = []
    weights = []
    total = len(y_true)
    for i in range(len(cm)):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = cm.sum() - (tp + fn + fp)
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        specs.append(spec)
        weights.append(cm[i, :].sum() / total)
    return sum(s * w for s, w in zip(specs, weights))

# 3. MODELLER (Olasilik tahmini - predict_proba destekli)
models = {
    'CatBoost': CatBoostClassifier(iterations=100, random_state=42, verbose=0, thread_count=2),
    'XGBoost': XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, eval_metric='mlogloss', verbosity=0, n_jobs=2),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=2),
    'MLP (Sinir Agi)': Pipeline([('scaler', StandardScaler()), ('model', MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=300, random_state=42, early_stopping=True))]),
    'Logistic Regression': Pipeline([('scaler', StandardScaler()), ('model', LogisticRegression(max_iter=1000, random_state=42))]),
    'kNN': Pipeline([('scaler', StandardScaler()), ('model', KNeighborsClassifier(n_neighbors=12, weights='distance', p=1))]),
    'Naive Bayes': Pipeline([('scaler', StandardScaler()), ('model', GaussianNB())]),
    'LSVM': Pipeline([('scaler', StandardScaler()), ('model', CalibratedClassifierCV(LinearSVC(max_iter=2000, random_state=42)))])
}

sonuclar = {}

print("\nModeller Egitiliyor ve Gelismis Metrikler Olculuyor...")
print("-" * 70)

for name, model in models.items():
    print(f">> {name} analiz ediliyor... ", end='', flush=True)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_pred = np.ravel(y_pred)
    y_prob = model.predict_proba(X_test)
    
    # Metrik Hesaplamalari
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    mcc = matthews_corrcoef(y_test, y_pred)
    spec = calculate_specificity(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob, multi_class='ovr', average='weighted')
    loss = log_loss(y_test, y_prob)
    
    sonuclar[name] = {
        'ROC_AUC': auc,
        'Specificity': spec,
        'MCC': mcc,
        'Log_Loss': loss,
        'F1_Score': f1
    }
    print(f"Tamam! (AUC: {auc:.4f} | Spec: {spec:.4f} | MCC: {mcc:.4f} | Loss: {loss:.4f})")

print("=" * 70)

# 4. TABLO OLUSTURMA VE DISA AKTARMA
df_gelismis = pd.DataFrame(sonuclar).T.sort_values('ROC_AUC', ascending=False)

df_formatli = pd.DataFrame(index=df_gelismis.index)
df_formatli['ROC-AUC (Ayırt Etme)'] = df_gelismis['ROC_AUC'].round(4)
df_formatli['Specificity (Özgüllük - Temiz Bilme)'] = df_gelismis['Specificity'].round(4)
df_formatli['MCC (Matthews Korelasyonu)'] = df_gelismis['MCC'].round(4)
df_formatli['Log-Loss (Belirsizlik Kaybı - Düşük İyi)'] = df_gelismis['Log_Loss'].round(4)
df_formatli['F1-Score (Ağırlıklı Denge)'] = df_gelismis['F1_Score'].round(4)

df_formatli.to_csv('tablolar/gelismis_metrikler_tablosu.csv')
print("Tablo 'tablolar/gelismis_metrikler_tablosu.csv' dosyasina kaydedildi.")

# 5. GORSELLESTIRME (2x2 IZGARA GRAFIK)
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
model_names = list(df_gelismis.index)

# 1. ROC-AUC
axes[0, 0].bar(model_names, df_gelismis['ROC_AUC'], color='#3498db', edgecolor='black', alpha=0.85)
axes[0, 0].set_title("ROC-AUC Skoru (Ayırt Etme Gücü - 1.0 Kusursuz)", fontsize=13, weight='bold')
axes[0, 0].set_ylim(0.7, 1.0)
axes[0, 0].tick_params(axis='x', rotation=30)
axes[0, 0].grid(axis='y', linestyle='--', alpha=0.5)

# 2. Specificity
axes[0, 1].bar(model_names, df_gelismis['Specificity'], color='#2ecc71', edgecolor='black', alpha=0.85)
axes[0, 1].set_title("Specificity (Özgüllük - Sağlamı Bilme Oranı)", fontsize=13, weight='bold')
axes[0, 1].set_ylim(0.7, 1.0)
axes[0, 1].tick_params(axis='x', rotation=30)
axes[0, 1].grid(axis='y', linestyle='--', alpha=0.5)

# 3. MCC
axes[1, 0].bar(model_names, df_gelismis['MCC'], color='#9b59b6', edgecolor='black', alpha=0.85)
axes[1, 0].set_title("MCC (Matthews Korelasyon Katsayısı - En Dürüst Metrik)", fontsize=13, weight='bold')
axes[1, 0].set_ylim(0.5, 1.0)
axes[1, 0].tick_params(axis='x', rotation=30)
axes[1, 0].grid(axis='y', linestyle='--', alpha=0.5)

# 4. Log-Loss
axes[1, 1].bar(model_names, df_gelismis['Log_Loss'], color='#e74c3c', edgecolor='black', alpha=0.85)
axes[1, 1].set_title("Log-Loss (Entropi Kaybı - Daha Düşük Olan Daha İyi!)", fontsize=13, weight='bold')
axes[1, 1].tick_params(axis='x', rotation=30)
axes[1, 1].grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('grafikler/grafik_gelismis_metrikler.png', dpi=150)
plt.close()
print("Grafik 'grafikler/grafik_gelismis_metrikler.png' olarak kaydedildi.")

print("=" * 70)
print("Gelismis Metrikler Analizi Basariyla Tamamlandi!")
print("=" * 70)
