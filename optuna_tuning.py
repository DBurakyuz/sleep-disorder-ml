# =============================================================================
# OPTUNA HIPERPARAMETRE OPTIMIZASYONU - MODEL: kNN
# =============================================================================

import pandas as pd
import optuna
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import f1_score
from sklearn.neighbors import KNeighborsClassifier
import warnings
warnings.filterwarnings('ignore')

# 1. Veri Hazirlik
print("Veri Hazirlaniyor...")
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

# kNN icin ayirmadan sonra MUTLAKA StandardScaler kullanilmalidir (Mesafe olctugu icin)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 2. Fabrika Ayari (Eski Durum)
base_model = KNeighborsClassifier(n_neighbors=5)
base_model.fit(X_train_scaled, y_train)
base_preds = base_model.predict(X_test_scaled)
base_f1 = f1_score(y_test, base_preds, average='weighted')
print(f"\n--- FABRIKA AYARI F1-SCORE: {base_f1:.4f} ---\n")

# 3. Optuna Zekasi
def objective(trial):
    param = {
        # Komsu sayisini 1 ile 30 arasinda dene
        'n_neighbors': trial.suggest_int('n_neighbors', 1, 30),
        # Oylar esit mi olsun, mesafeye gore mi?
        'weights': trial.suggest_categorical('weights', ['uniform', 'distance']),
        # Mesafe kus ucusu mu (2) yoksa manhattan mi (1)?
        'p': trial.suggest_categorical('p', [1, 2])
    }
    
    model = KNeighborsClassifier(**param)
    model.fit(X_train_scaled, y_train)
    preds = model.predict(X_test_scaled)
    return f1_score(y_test, preds, average='weighted')

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=30)

print("\n🏆 KAZANAN AYARLAR:")
for key, value in study.best_params.items():
    print(f"  -> {key}: {value}")
print(f"YENI SKOR: {study.best_value:.4f}")
