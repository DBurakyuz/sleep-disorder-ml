# =============================================================================
# MAKINE OGRENIMI: 10-FOLD CROSS-VALIDATION (CAPRAZ DOGRULAMA)
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
import time

from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, confusion_matrix)

from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC, SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from catboost import CatBoostClassifier

print("=" * 70)
print("10-Fold Cross-Validation Sistemi Baslatiliyor...")
print("=" * 70)

# 1. VERI YUKLEME VE ON ISLEME
df = pd.read_csv('sleep_health_dataset.csv')
drop_cols = ['person_id', 'cognitive_performance_score', 'felt_rested']
df_clean = df.drop(columns=drop_cols)

# =============================================================================
# KLINIK OZELLIK MUHENDISLIGI (FEATURE ENGINEERING - AASM & PSQI UYUMLU)
# =============================================================================
# 1. Uyku Bolunme Indeksi (SFI - Sleep Fragmentation Index): Saatteki uyanma sikligi
df_clean['sleep_fragmentation_index'] = (df_clean['wake_episodes_per_night'] / df_clean['sleep_duration_hrs']).round(4)

# 2. Onarici Uyku Orani (RSR - Restorative Sleep Ratio): Derin + REM uykusu toplami
df_clean['restorative_sleep_ratio'] = (df_clean['deep_sleep_percentage'] + df_clean['rem_percentage']).round(4)
print("Klinik Ozellikler Eklendi: 'sleep_fragmentation_index' ve 'restorative_sleep_ratio'")

kategorik_sutunlar = ['gender', 'occupation', 'country', 'chronotype', 'mental_health_condition', 'season', 'day_type']
for col in kategorik_sutunlar:
    le = LabelEncoder()
    df_clean[col] = le.fit_transform(df_clean[col])

le_target = LabelEncoder()
df_clean['sleep_disorder_risk'] = le_target.fit_transform(df_clean['sleep_disorder_risk'])

X_all = df_clean.drop('sleep_disorder_risk', axis=1)
y_all = df_clean['sleep_disorder_risk']

# 100.000 verinin TAMAMI kullaniliyor.
# RBF SVM karesel karmasiklik (O(N^2)) yuzunden 25.000 ile sinirlandirilarak CPU korunur.
SAMPLE_SIZE = None

if SAMPLE_SIZE and SAMPLE_SIZE < len(df_clean):
    print(f"Bilgi: 10-Fold CV icin {SAMPLE_SIZE} satirlik temsili orneklem secildi.")
    X, _, y, _ = train_test_split(X_all, y_all, train_size=SAMPLE_SIZE, random_state=42, stratify=y_all)
    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)
else:
    print(f"Bilgi: 10-Fold CV TUM VERI SETI ({len(df_clean):,} satir) ile calistiriliyor!")
    X, y = X_all.reset_index(drop=True), y_all.reset_index(drop=True)

# 2. 10-FOLD CV PROTOKOLU
cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

# 3. MODELLER (Islemciyi korumak icin n_jobs=2 ve thread_count=2 dengelendi)
models = {
    'CatBoost': CatBoostClassifier(iterations=100, random_state=42, verbose=0, thread_count=2),
    'XGBoost': XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, eval_metric='mlogloss', verbosity=0, n_jobs=2),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=2),
    'Naive Bayes': Pipeline([('scaler', StandardScaler()), ('model', GaussianNB())]),
    'Logistic Regression': Pipeline([('scaler', StandardScaler()), ('model', LogisticRegression(max_iter=1000, random_state=42))]),
    'LSVM': Pipeline([('scaler', StandardScaler()), ('model', LinearSVC(max_iter=2000, random_state=42))]),
    'MLP (Sinir Agi)': Pipeline([('scaler', StandardScaler()), ('model', MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=300, random_state=42, early_stopping=True))]),
    'kNN': Pipeline([('scaler', StandardScaler()), ('model', KNeighborsClassifier(n_neighbors=12, weights='distance', p=1, n_jobs=2))]),
    'RBF SVM': Pipeline([('scaler', StandardScaler()), ('model', SVC(kernel='rbf', random_state=42))])
}

cv_sonuclari = {}
oof_predictions = {}

print("\n10-Fold Cross-Validation Egitimleri Basliyor (100.000 Satir)...")
print("-" * 70)

for name, model in models.items():
    print(f">> {name} (10 Katlama Calistiriliyor)... ", end='', flush=True)
    t0 = time.time()
    
    fold_acc, fold_prec, fold_rec, fold_f1 = [], [], [], []
    oof_pred = np.zeros(len(y), dtype=int)
    
    # Tek bir 10-katlama dongusu
    for train_idx, val_idx in cv.split(X, y):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # RBF SVM icin karesel karmasiklik (O(N^2)) yuzunden egitimi 25.000 ile sinirliyoruz
        if name == 'RBF SVM' and len(X_tr) > 25000:
            X_tr, _, y_tr, _ = train_test_split(X_tr, y_tr, train_size=25000, random_state=42, stratify=y_tr)
        
        model.fit(X_tr, y_tr)
        preds = np.ravel(model.predict(X_val))
        
        oof_pred[val_idx] = preds
        fold_acc.append(accuracy_score(y_val, preds))
        fold_prec.append(precision_score(y_val, preds, average='weighted', zero_division=0))
        fold_rec.append(recall_score(y_val, preds, average='weighted', zero_division=0))
        fold_f1.append(f1_score(y_val, preds, average='weighted', zero_division=0))
    
    elapsed = time.time() - t0
    oof_predictions[name] = oof_pred
    
    acc_mean, acc_std = np.mean(fold_acc), np.std(fold_acc)
    prec_mean, prec_std = np.mean(fold_prec), np.std(fold_prec)
    rec_mean, rec_std = np.mean(fold_rec), np.std(fold_rec)
    f1_mean, f1_std = np.mean(fold_f1), np.std(fold_f1)
    
    cv_sonuclari[name] = {
        'Accuracy_Mean': acc_mean, 'Accuracy_Std': acc_std,
        'Precision_Mean': prec_mean, 'Precision_Std': prec_std,
        'Recall_Mean': rec_mean, 'Recall_Std': rec_std,
        'F1_Mean': f1_mean, 'F1_Std': f1_std,
        'Sure_sn': elapsed
    }
    
    print(f"Tamamlandi ({elapsed:.1f} sn) -> Ort. F1: {f1_mean:.4f} (+/- {f1_std:.4f})")

print("=" * 70)

import os
os.makedirs('tablolar', exist_ok=True)
os.makedirs('grafikler', exist_ok=True)

# Guvenli CSV Kaydetme Fonksiyonu (Excel aciksa kodun cokmesini engeller)
def safe_to_csv(dataframe, filepath, **kwargs):
    try:
        dataframe.to_csv(filepath, **kwargs)
        print(f"Tablo basariyla kaydedildi: '{filepath}'")
    except PermissionError:
        alt_path = filepath.replace('.csv', '_guncel.csv')
        dataframe.to_csv(alt_path, **kwargs)
        print(f"UYARI: '{filepath}' Excel veya baska programda acik oldugu icin '{alt_path}' olarak kaydedildi! Lutfen Excel'i kapatin.")

# 4. SONUC TABLOSU VE DIŞA AKTARMA
df_cv_tablo = pd.DataFrame(cv_sonuclari).T
df_cv_tablo = df_cv_tablo.sort_values('F1_Mean', ascending=False)

df_formatli = pd.DataFrame()
df_formatli['Accuracy (Ort +/- Std)'] = df_cv_tablo.apply(lambda r: f"{r['Accuracy_Mean']:.4f} +/- {r['Accuracy_Std']:.4f}", axis=1)
df_formatli['Precision (Ort +/- Std)'] = df_cv_tablo.apply(lambda r: f"{r['Precision_Mean']:.4f} +/- {r['Precision_Std']:.4f}", axis=1)
df_formatli['Recall (Ort +/- Std)'] = df_cv_tablo.apply(lambda r: f"{r['Recall_Mean']:.4f} +/- {r['Recall_Std']:.4f}", axis=1)
df_formatli['F1-Score (Ort +/- Std)'] = df_cv_tablo.apply(lambda r: f"{r['F1_Mean']:.4f} +/- {r['F1_Std']:.4f}", axis=1)
df_formatli['Toplam Sure (sn)'] = df_cv_tablo['Sure_sn'].round(2)

safe_to_csv(df_formatli, 'tablolar/cv_sonuc_tablosu.csv')

# 5. SPLIT ILE 10-FOLD CV KARSILASTIRMA TABLOSU
try:
    df_split = pd.read_csv('tablolar/sonuc_tablosu.csv', index_col=0)
    df_karsilastirma = pd.DataFrame(index=df_cv_tablo.index)
    df_karsilastirma['Tekli Split F1-Score'] = df_split['F1-Score']
    df_karsilastirma['10-Fold CV Ort. F1-Score'] = df_cv_tablo['F1_Mean'].round(4)
    df_karsilastirma['Standart Sapma (+/-)'] = df_cv_tablo['F1_Std'].round(4)
    df_karsilastirma['Fark (CV - Split)'] = (df_karsilastirma['10-Fold CV Ort. F1-Score'] - df_karsilastirma['Tekli Split F1-Score']).round(4)
    safe_to_csv(df_karsilastirma, 'tablolar/karsilastirma_split_vs_cv.csv')
except Exception as e:
    pass

# 6. GORSELLESTIRME: 4 TEMEL METRIK (Accuracy, Precision, Recall, F1) 2x2 IZGARA
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
metrics_map = [
    ('Accuracy', 'Accuracy_Mean', 'Accuracy_Std'),
    ('Precision', 'Precision_Mean', 'Precision_Std'),
    ('Recall', 'Recall_Mean', 'Recall_Std'),
    ('F1-Score', 'F1_Mean', 'F1_Std')
]
colors_palette = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#ff9ff3', '#feca57']

for idx, (m_label, mean_col, std_col) in enumerate(metrics_map):
    ax = axes[idx // 2, idx % 2]
    means = df_cv_tablo[mean_col].values
    stds = df_cv_tablo[std_col].values
    bars = ax.bar(model_names, means, yerr=stds, capsize=4, color=colors_palette, edgecolor='black', alpha=0.85)
    ax.set_title(f"{m_label} (10-Fold CV Ortalama +/- Standart Sapma)", fontsize=13, weight='bold')
    ax.set_ylim(0.6, 1.0)
    ax.tick_params(axis='x', rotation=30)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    for bar, mean in zip(bars, means):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.01, f"{mean:.3f}", ha='center', va='bottom', fontsize=8, weight='bold')

plt.suptitle("10-Fold Cross-Validation: 4 Temel Metrik Karsilastirmasi (100.000 Satir)", fontsize=16, weight='bold', y=0.99)
plt.tight_layout()
plt.savefig('grafikler/grafik_3_tum_metrikler_karsilastirma.png', dpi=150)
plt.close()
print("Grafik 1 (4 Temel Metrik 2x2 Izgara: Accuracy, Precision, Recall, F1) kaydedildi.")

# Ayrica tekli F1 grafigi de kaydedilir
plt.figure(figsize=(14, 7))
bars = plt.bar(model_names, f1_means, yerr=f1_stds, capsize=5, color='#3498db', edgecolor='black', alpha=0.85)
plt.title("10-Fold Cross-Validation: Modellerin F1-Skorlari ve Kararliliklari (Ortalama +/- Standart Sapma)", fontsize=14, weight='bold')
plt.xlabel("Model", fontsize=12)
plt.ylabel("Weighted F1-Score", fontsize=12)
plt.ylim(0.5, 1.0)
plt.xticks(rotation=30, ha='right', fontsize=11)
plt.grid(axis='y', linestyle='--', alpha=0.5)

for bar, mean, std in zip(bars, f1_means, f1_stds):
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f"{mean:.3f}\n(+/-{std:.3f})", ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('grafikler/grafik_cv_f1_karsilastirma.png', dpi=150)
plt.close()
print("Grafik 1 (F1 Hata Cubuklu Karsilastirma) 'grafikler/grafik_cv_f1_karsilastirma.png' olarak kaydedildi.")

# 7. GORSELLESTIRME: 10-FOLD CV CONFUSION MATRICES (3x3 IZGARA - TURKCE)
turkce_siniflar = ['Sağlıklı (Healthy)', 'Hafif (Mild)', 'Orta (Moderate)', 'Ağır (Severe)']
fig, axes = plt.subplots(3, 3, figsize=(20, 18))
for idx, model_name in enumerate(model_names):
    row = idx // 3
    col = idx % 3
    ax = axes[row][col]
    cm = confusion_matrix(y, oof_predictions[model_name])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax, 
                xticklabels=turkce_siniflar, yticklabels=turkce_siniflar)
    ax.set_title(f"{model_name} (10-Fold Toplam)", fontsize=13, weight='bold')
    ax.set_xlabel("Tahmin Edilen Sınıf", fontsize=10)
    ax.set_ylabel("Gerçek Sınıf", fontsize=10)
    ax.tick_params(axis='x', rotation=30)
plt.tight_layout()
plt.savefig('grafikler/grafik_cv_confusion_matrices.png', dpi=150)
plt.close()
print("Grafik 2 (Confusion Matrices - Turkce) 'grafikler/grafik_cv_confusion_matrices.png' olarak kaydedildi.")

# 8. YENI: SINIF BAZINDA DETAY TABLOSU (Sampiyon Model Icin)
top_model_name = df_cv_tablo.index[0]
from sklearn.metrics import classification_report
report_dict = classification_report(y, oof_predictions[top_model_name], target_names=turkce_siniflar, output_dict=True)
df_class_report = pd.DataFrame(report_dict).T.round(4)
safe_to_csv(df_class_report, 'tablolar/sinif_bazinda_rapor.csv')

# 9. YENI: MODEL VERIMLILIK (HIZ VS BASARI) TABLOSU VE GRAFIGI
df_verimlilik = pd.DataFrame({
    'Model': df_cv_tablo.index,
    'F1-Score': df_cv_tablo['F1_Mean'].round(4),
    'Sure_sn': df_cv_tablo['Sure_sn'].round(2),
    'Verimlilik_Skoru': (df_cv_tablo['F1_Mean'] / df_cv_tablo['Sure_sn']).round(4)
}).sort_values('Verimlilik_Skoru', ascending=False)
safe_to_csv(df_verimlilik, 'tablolar/verimlilik_tablosu.csv', index=False)

plt.figure(figsize=(10, 6))
plt.scatter(df_cv_tablo['Sure_sn'], df_cv_tablo['F1_Mean'], color='#e74c3c', s=120, edgecolors='black', zorder=5)
for m_name in df_cv_tablo.index:
    plt.annotate(m_name, (df_cv_tablo.loc[m_name, 'Sure_sn'], df_cv_tablo.loc[m_name, 'F1_Mean']),
                 textcoords="offset points", xytext=(8, 4), fontsize=10, weight='bold')
plt.title("Model Verimliligi: Egitim Suresi (sn) vs 10-Fold F1-Score", fontsize=14, weight='bold')
plt.xlabel("Toplam Egitim Suresi (Saniye) [Sola Dogru = Daha Hizli]", fontsize=11)
plt.ylabel("10-Fold Ortalama F1-Score [Yukari Dogru = Daha Basarili]", fontsize=11)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('grafikler/grafik_hiz_vs_basari.png', dpi=150)
plt.close()
print("Grafik 3 (Hiz vs Basari Serpme Grafigi) 'grafikler/grafik_hiz_vs_basari.png' olarak kaydedildi.")

# 10. YENI: OZELLIK ONEM TABLOSU VE GRAFIGI (Turkce Etiketli)
turkce_kolonlar_harita = {
    'age': 'Yaş (age)',
    'bmi': 'Vücut Kitle İndeksi (bmi)',
    'gender': 'Cinsiyet (gender)',
    'occupation': 'Meslek (occupation)',
    'country': 'Ülke (country)',
    'chronotype': 'Biyolojik Ritim (chronotype)',
    'mental_health_condition': 'Ruh Sağlığı (mental_health)',
    'season': 'Mevsim (season)',
    'day_type': 'Gün Tipi (day_type)',
    'sleep_duration_hrs': 'Uyku Süresi (sleep_duration)',
    'sleep_quality_score': 'Uyku Kalite Skoru (sleep_quality)',
    'rem_percentage': 'REM Uykusu % (rem_perc)',
    'deep_sleep_percentage': 'Derin Uyku % (deep_sleep)',
    'sleep_latency_mins': 'Uykuya Dalma Süresi (latency)',
    'wake_episodes_per_night': 'Gece Uyanma Sayısı (wakeups)',
    'caffeine_mg_before_bed': 'Kafein Miktarı (caffeine)',
    'alcohol_units_before_bed': 'Alkol Miktarı (alcohol)',
    'screen_time_before_bed_mins': 'Yatmadan Önce Ekran (screen_time)',
    'exercise_day': 'Egzersiz Yapıldı mı (exercise)',
    'steps_that_day': 'Günlük Adım Sayısı (steps)',
    'nap_duration_mins': 'Gündüz Şekerleme (nap)',
    'stress_score': 'Stres Skoru (stress)',
    'work_hours_that_day': 'Çalışma Saati (work_hours)',
    'heart_rate_resting_bpm': 'Dinlenme Kalp Nabzı (heart_rate)',
    'sleep_aid_used': 'Uyku İlacı (sleep_aid)',
    'shift_work': 'Vardiyalı Çalışma (shift_work)',
    'room_temperature_celsius': 'Oda Sıcaklığı (temp)',
    'weekend_sleep_diff_hrs': 'Hafta Sonu Farkı (weekend_diff)',
    'sleep_fragmentation_index': 'Uyku Bölünme İndeksi - SFI (frag_idx)',
    'restorative_sleep_ratio': 'Onarıcı Uyku Oranı - RSR (restorative)'
}

print("Ozellik Onem Analizi Hesaplaniyor...")
rf_imp = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=2)
rf_imp.fit(X, y)
importances = rf_imp.feature_importances_

ozellik_turkce = [turkce_kolonlar_harita.get(col, col) for col in X.columns]

df_importance = pd.DataFrame({
    'Ozellik': ozellik_turkce,
    'Orijinal_Sutun': X.columns,
    'Onem_Skoru': importances,
    'Yuzde_Etki (%)': (importances * 100).round(2)
}).sort_values('Onem_Skoru', ascending=False).reset_index(drop=True)
safe_to_csv(df_importance, 'tablolar/ozellik_onem_tablosu.csv', index=False)

plt.figure(figsize=(13, 8))
top15 = df_importance.head(15).iloc[::-1]
plt.barh(top15['Ozellik'], top15['Yuzde_Etki (%)'], color='#2ecc71', edgecolor='black', alpha=0.85)
plt.title("Hastalık Riskini En Çok Etkileyen İlk 15 Özellik (Feature Importance)", fontsize=14, weight='bold')
plt.xlabel("Modelin Kararına Etki Yüzdesi (%)", fontsize=11)
plt.tight_layout()
plt.savefig('grafikler/grafik_ozellik_onemi.png', dpi=150)
plt.close()
print("Grafik 4 (Ozellik Onemi Grafigi - Turkce) 'grafikler/grafik_ozellik_onemi.png' olarak kaydedildi.")

print("=" * 70)
print("Tum 10-Fold ve Ek Analiz Islemleri Basariyla Tamamlandi!")
print("=" * 70)
