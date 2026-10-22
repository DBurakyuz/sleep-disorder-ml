# =============================================================================
# SHAP ANALIZI: MODELIN KARA KUTUSUNU ACMAK
# Hangi ozellik (feature) kararlari ne kadar etkiliyor?
# =============================================================================

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("Veri ve Model SHAP Analizi Icin Hazirlaniyor...")

# 1. Veri Hazirligi (Ayni sekilde)
df = pd.read_csv('sleep_health_dataset.csv')
df_clean = df.drop(columns=['person_id', 'cognitive_performance_score', 'felt_rested'])

kategorik_sutunlar = ['gender', 'occupation', 'country', 'chronotype', 'mental_health_condition', 'season', 'day_type']
for col in kategorik_sutunlar:
    le = LabelEncoder()
    df_clean[col] = le.fit_transform(df_clean[col])

le_target = LabelEncoder()
df_clean['sleep_disorder_risk'] = le_target.fit_transform(df_clean['sleep_disorder_risk'])

X = df_clean.drop('sleep_disorder_risk', axis=1)
y = df_clean['sleep_disorder_risk']

# Test verisini biraz kucuk tutalim ki SHAP hizli calissin (%10)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.10, random_state=42, stratify=y)

# Agac modellerinde StandardScaler'a gerek yoktur, SHAP da orjinal sayilari sever.
print("Random Forest Egitiliyor...")
model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# =============================================================================
# 2. SHAP (RÖNTGEN) KISMI
# =============================================================================
print("SHAP Degerleri Hesaplaniyor (Bu islem bilgisayari biraz yorabilir, lutfen bekleyin)...")

# Agac tabanli modeller icin TreeExplainer kullanilir
explainer = shap.TreeExplainer(model)

# Test verisindeki hastalarin sonuclarini acikliyoruz
shap_values = explainer.shap_values(X_test)

# Grafik Olusturma: Hangi ozellik daha onemli? (Bar Plot)
plt.figure(figsize=(12, 8))
# 4 farkli sinif oldugu icin (Healthy, Mild, Moderate, Severe) cok renkli bir bar cizecek
shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)

plt.title("SHAP: Hastalik Riskini Etkileyen En Onemli Ozellikler", fontsize=14)
plt.tight_layout()
plt.savefig('grafik_5_shap_onem_sirasi.png', dpi=150)
plt.close()

print("=" * 70)
print("Islem Tamam! Lutfen klasordeki 'grafik_5_shap_onem_sirasi.png' dosyasina bakin.")
print("=" * 70)
