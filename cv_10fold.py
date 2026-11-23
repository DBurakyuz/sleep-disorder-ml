# =============================================================================
# MAKINE OGRENMESI: SIZINTISIZ 10-KAT CAPRAZ DOGRULAMA VE KAPSAMLI DENEYLER
# Uyku Sagligi ve Gunluk Performans - Cok Sinifli Uyku Bozuklugu Riski Tahmini
# Yalova Universitesi - Bilgisayar Muhendisligi (Uygulamali Ders Notu Uyumlu)
# =============================================================================

import json
import os
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import imblearn
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.special import softmax
import seaborn as sns
import sklearn
import catboost
import xgboost

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, learning_curve, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, label_binarize
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier
from catboost import CatBoostClassifier
from xgboost import XGBClassifier

# -----------------------------------------------------------------------------
# 1. SABITLER, SURUMLER VE GRAFIK STILI
# -----------------------------------------------------------------------------
RANDOM_STATE = 42
N_SPLITS = 10
OUT_TAB = Path("tablolar")
OUT_FIG = Path("grafikler")
OUT_TAB.mkdir(parents=True, exist_ok=True)
OUT_FIG.mkdir(parents=True, exist_ok=True)

VERSIONS = {
    "Python": sys.version.split()[0],
    "numpy": np.__version__,
    "pandas": pd.__version__,
    "scipy": scipy.__version__,
    "scikit-learn": sklearn.__version__,
    "imbalanced-learn": imblearn.__version__,
    "catboost": catboost.__version__,
    "xgboost": xgboost.__version__,
    "matplotlib": matplotlib.__version__,
    "seaborn": sns.__version__,
}

print("=" * 74)
print("SIZINTISIZ 10-KAT CAPRAZ DOGRULAMA VE DENEY SISTEMI BASLATILIYOR")
print("=" * 74)
for k, v in VERSIONS.items():
    print(f"  {k:18s}: {v}")
print("-" * 74)

PALETTE = [
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
    "#008300", "#6250d6", "#e34948", "#17becf", "#7f7f7f"
]
INK, INK2, RULE, GRID = "#0b0b0b", "#52514e", "#c3c2b7", "#e1e0d9"

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.size": 9.5,
    "text.color": INK,
    "axes.labelcolor": INK2,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "axes.edgecolor": RULE,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "axes.titlesize": 10.5,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "lines.linewidth": 1.6,
})

RESULTS = {
    "versions": VERSIONS,
    "random_state": RANDOM_STATE,
    "n_splits": N_SPLITS,
}

# -----------------------------------------------------------------------------
# 2. VERI YUKLEME, KALITE KONTROLLERI VE KLINIK OZELLIK MUHENDISLIGI
# -----------------------------------------------------------------------------
df_raw = pd.read_csv("sleep_health_dataset.csv")
n_missing = int(df_raw.isna().sum().sum())
n_dup_full = int(df_raw.duplicated().sum())
n_dup_no_id = int(df_raw.drop(columns=["person_id"]).duplicated().sum())

print(f"Ham veri boyutu            : {df_raw.shape}")
print(f"Eksik deger (toplam)       : {n_missing}")
print(f"Tekrar eden satir (tam)    : {n_dup_full}")
print(f"Tekrar eden satir (ID haric): {n_dup_no_id}")

# Bilgi sizintisi (target proxy) ve kimlik sutunlarini cikar
drop_cols = ["person_id", "cognitive_performance_score", "felt_rested"]
df = df_raw.drop(columns=drop_cols).copy()

# Satir bazli deterministik klinik ozellik muhendisligi (cross-sample sizinti yok)
df["sleep_fragmentation_index"] = (df["wake_episodes_per_night"] / df["sleep_duration_hrs"]).round(4)
df["restorative_sleep_ratio"] = (df["deep_sleep_percentage"] + df["rem_percentage"]).round(4)

# Hedef degisken: acik sirali kodlama (Healthy=0 < Mild=1 < Moderate=2 < Severe=3)
CLASS_MAP = {"Healthy": 0, "Mild": 1, "Moderate": 2, "Severe": 3}
CLASS_NAMES_TR = ["Sağlıklı (Healthy)", "Hafif (Mild)", "Orta (Moderate)", "Ağır (Severe)"]
y = df["sleep_disorder_risk"].map(CLASS_MAP).astype(int)
X = df.drop(columns=["sleep_disorder_risk"])

cat_cols = [
    "gender", "occupation", "country", "chronotype",
    "mental_health_condition", "season", "day_type"
]
num_cols = [c for c in X.columns if c not in cat_cols]

counts = y.value_counts().sort_index()
pcts = (y.value_counts(normalize=True).sort_index() * 100).round(2)
print(f"Sayisal oznitelik: {len(num_cols)} | Kategorik (nominal) oznitelik: {len(cat_cols)}")
print("Sinif dagilimi:")
for idx, name in enumerate(CLASS_NAMES_TR):
    print(f"  {idx} - {name:20s}: {counts[idx]:6d} (%{pcts[idx]:.2f})")

RESULTS["dataset"] = {
    "n_samples": int(len(df)),
    "n_raw_cols": int(df_raw.shape[1]),
    "n_features_before_ohe": int(X.shape[1]),
    "n_numeric": len(num_cols),
    "n_categorical": len(cat_cols),
    "n_missing": n_missing,
    "n_duplicates_no_id": n_dup_no_id,
    "class_counts": {CLASS_NAMES_TR[i]: int(counts[i]) for i in range(4)},
    "class_pcts": {CLASS_NAMES_TR[i]: float(pcts[i]) for i in range(4)},
}

# Grafik 1: Sinif Dagilimi
fig, ax = plt.subplots(figsize=(7.5, 4.0))
bars = ax.bar(CLASS_NAMES_TR, [counts[i] for i in range(4)], color=PALETTE[:4], width=0.55)
for bar, i in zip(bars, range(4)):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 900,
        f"{counts[i]:,}\n(%{pcts[i]:.2f})",
        ha="center", va="bottom", fontsize=9, fontweight="bold"
    )
ax.set_ylabel("Örnek Sayısı")
ax.set_title("Hedef Değişken Sınıf Dağılımı (100.000 Birey — Dengesiz Çok Sınıflı Yapı)")
ax.set_ylim(0, max(counts) * 1.18)
ax.grid(axis="x", visible=False)
plt.tight_layout()
fig.savefig(OUT_FIG / "grafik_1_sinif_dagilimi.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# -----------------------------------------------------------------------------
# 3. SIZINTISIZ ON ISLEME (ColumnTransformer + Pipeline) VE MODELLER
# -----------------------------------------------------------------------------
def make_preprocessor(scale_numeric: bool) -> ColumnTransformer:
    """
    Sayisal sutunlar: yalnizca olcege duyarli modellerde StandardScaler.
    Nominal kategorik sutunlar: OneHotEncoder (her fold'un egitim kisminda fit edilir).
    """
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler() if scale_numeric else "passthrough", num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ]
    )

def build_models():
    """
    1 Referans (Dummy) + 9 Makine Ogrenmesi modeli.
    Hicbir hiperparametre test/CV verisi uzerinde ayarlanmamistir (sizintisiz).
    GaussianNB ve agac tabanli modeller olceklendirme gerektirmez (Tablo 11).
    """
    return {
        "Dummy (Çoğunluk)": Pipeline([
            ("clf", DummyClassifier(strategy="most_frequent"))
        ]),
        "CatBoost": Pipeline([
            ("prep", make_preprocessor(False)),
            ("clf", CatBoostClassifier(iterations=100, random_state=RANDOM_STATE, verbose=0, thread_count=2)),
        ]),
        "XGBoost": Pipeline([
            ("prep", make_preprocessor(False)),
            ("clf", XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                random_state=RANDOM_STATE, eval_metric="mlogloss", verbosity=0, n_jobs=2
            )),
        ]),
        "Random Forest": Pipeline([
            ("prep", make_preprocessor(False)),
            ("clf", RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=2)),
        ]),
        "MLP (Sinir Ağı)": Pipeline([
            ("prep", make_preprocessor(True)),
            ("clf", MLPClassifier(
                hidden_layer_sizes=(100, 50), max_iter=300,
                random_state=RANDOM_STATE, early_stopping=True
            )),
        ]),
        "RBF SVM": Pipeline([
            ("prep", make_preprocessor(True)),
            ("clf", SVC(kernel="rbf", random_state=RANDOM_STATE)),
        ]),
        "Logistic Regression": Pipeline([
            ("prep", make_preprocessor(True)),
            ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
        ]),
        "LSVM": Pipeline([
            ("prep", make_preprocessor(True)),
            ("clf", LinearSVC(max_iter=2000, random_state=RANDOM_STATE)),
        ]),
        "kNN (k=5)": Pipeline([
            ("prep", make_preprocessor(True)),
            ("clf", KNeighborsClassifier(n_neighbors=5, n_jobs=2)),
        ]),
        "Naive Bayes": Pipeline([
            ("prep", make_preprocessor(False)),
            ("clf", GaussianNB()),
        ]),
    }

# -----------------------------------------------------------------------------
# 4. METRIK HESAPLAMA VE 10-KAT STRATIFIED CROSS-VALIDATION (ddof=1, clone)
# -----------------------------------------------------------------------------
def weighted_specificity(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])
    specs, weights = [], []
    total = cm.sum()
    for i in range(4):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = total - (tp + fn + fp)
        specs.append(tn / (tn + fp) if (tn + fp) > 0 else 0.0)
        weights.append(cm[i, :].sum() / total)
    return float(sum(s * w for s, w in zip(specs, weights)))

def get_scores(fitted_model, X_eval):
    """Olasilik tahmini varsa predict_proba, yoksa (SVM) softmax(decision_function)."""
    if hasattr(fitted_model, "predict_proba"):
        return fitted_model.predict_proba(X_eval), True
    df_scores = fitted_model.decision_function(X_eval)
    return softmax(df_scores, axis=1), False

def compute_fold_metrics(y_true, y_pred, y_score, is_prob):
    y_bin = label_binarize(y_true, classes=[0, 1, 2, 3])
    auroc = roc_auc_score(y_true, y_score, multi_class="ovr", average="weighted")
    aupr_macro = average_precision_score(y_bin, y_score, average="macro")
    aupr_weighted = average_precision_score(y_bin, y_score, average="weighted")
    ll = log_loss(y_true, y_score, labels=[0, 1, 2, 3]) if is_prob else np.nan
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision_W": precision_score(y_true, y_pred, average="weighted", zero_division=0),
        "Recall_W": recall_score(y_true, y_pred, average="weighted", zero_division=0),
        "F1_W": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "Precision_M": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "Recall_M": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "F1_M": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "Specificity": weighted_specificity(y_true, y_pred),
        "MCC": matthews_corrcoef(y_true, y_pred),
        "AUROC": auroc,
        "AUPR_M": aupr_macro,
        "AUPR_W": aupr_weighted,
        "Log_Loss": ll,
    }

cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
models = build_models()

fold_results = {}
oof_preds = {}
oof_scores = {}
train_cv_rows = []
elapsed_times = {}

print("\n[ADIM 1/4] 10-Kat Stratified CV Basliyor (100.000 Satir, Pipeline + OneHotEncoder)...")
print("-" * 74)

for name, est in models.items():
    print(f">> {name:20s} ... ", end="", flush=True)
    t0 = time.time()
    rows = []
    oof_p = np.zeros(len(y), dtype=int)
    oof_s = np.zeros((len(y), 4), dtype=float)
    tr_f1_w_list, tr_f1_m_list = [], []

    for fold, (tr_idx, te_idx) in enumerate(cv.split(X, y), start=1):
        X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
        y_tr, y_te = y.iloc[tr_idx], y.iloc[te_idx]

        # RBF SVM O(N^2) karmasikligi nedeniyle egitim fold'u 25.000 ile sinirlanir
        if name == "RBF SVM" and len(X_tr) > 25000:
            X_tr, _, y_tr, _ = train_test_split(
                X_tr, y_tr, train_size=25000, random_state=RANDOM_STATE, stratify=y_tr
            )

        fitted = clone(est).fit(X_tr, y_tr)

        # Egitim skoru (Overfitting analizi icin)
        tr_pred = np.ravel(fitted.predict(X_tr))
        tr_f1_w_list.append(f1_score(y_tr, tr_pred, average="weighted", zero_division=0))
        tr_f1_m_list.append(f1_score(y_tr, tr_pred, average="macro", zero_division=0))

        # Dogrulama tahmini ve olasilik/skor
        te_pred = np.ravel(fitted.predict(X_te))
        te_score, is_prob = get_scores(fitted, X_te)

        oof_p[te_idx] = te_pred
        oof_s[te_idx] = te_score

        m = compute_fold_metrics(y_te, te_pred, te_score, is_prob)
        m["fold"] = fold
        rows.append(m)

    elapsed = time.time() - t0
    df_f = pd.DataFrame(rows)
    fold_results[name] = df_f
    oof_preds[name] = oof_p
    oof_scores[name] = oof_s
    elapsed_times[name] = round(elapsed, 2)

    train_cv_rows.append({
        "Model": name,
        "Egitim_F1_Macro": float(np.mean(tr_f1_m_list)),
        "CV_F1_Macro_Ort": float(df_f["F1_M"].mean()),
        "CV_F1_Macro_Std": float(df_f["F1_M"].std(ddof=1)),
        "Fark_Macro": float(np.mean(tr_f1_m_list) - df_f["F1_M"].mean()),
        "Egitim_F1_Weighted": float(np.mean(tr_f1_w_list)),
        "CV_F1_Weighted_Ort": float(df_f["F1_W"].mean()),
        "CV_F1_Weighted_Std": float(df_f["F1_W"].std(ddof=1)),
        "Fark_Weighted": float(np.mean(tr_f1_w_list) - df_f["F1_W"].mean()),
    })

    print(
        f"Tamam ({elapsed:5.1f}s) | Acc: {df_f['Accuracy'].mean():.4f} | "
        f"Macro F1: {df_f['F1_M'].mean():.4f} (+/-{df_f['F1_M'].std(ddof=1):.4f}) | "
        f"MCC: {df_f['MCC'].mean():.4f}"
    )

# Ozet Tablolar (ddof=1 orneklem standart sapmasi)
METRIC_COLS = [
    "Accuracy", "Precision_W", "Recall_W", "F1_W",
    "Precision_M", "Recall_M", "F1_M",
    "Specificity", "MCC", "AUROC", "AUPR_M", "AUPR_W", "Log_Loss"
]
summary_mean = pd.DataFrame({n: f[METRIC_COLS].mean() for n, f in fold_results.items()}).T
summary_std = pd.DataFrame({n: f[METRIC_COLS].std(ddof=1) for n, f in fold_results.items()}).T
summary_mean["Sure_sn"] = pd.Series(elapsed_times)

# MCC'ye gore sirala (Dummy en altta)
real_models_sorted = (
    summary_mean.drop(index=["Dummy (Çoğunluk)"])
    .sort_values("MCC", ascending=False)
    .index.tolist()
)
ordered_all = real_models_sorted + ["Dummy (Çoğunluk)"]
summary_mean = summary_mean.loc[ordered_all]
summary_std = summary_std.loc[ordered_all]

summary_mean.round(4).to_csv(OUT_TAB / "cv_ortalama.csv", encoding="utf-8-sig")
summary_std.round(4).to_csv(OUT_TAB / "cv_std.csv", encoding="utf-8-sig")

# Formatli ana tablo
df_fmt = pd.DataFrame(index=ordered_all)
for col in ["Accuracy", "F1_W", "F1_M", "MCC", "Specificity", "AUROC", "AUPR_M", "Log_Loss"]:
    df_fmt[col] = [
        f"{summary_mean.loc[m, col]:.4f} ± {summary_std.loc[m, col]:.4f}"
        if pd.notna(summary_mean.loc[m, col]) else "—"
        for m in ordered_all
    ]
df_fmt["Sure_sn"] = summary_mean["Sure_sn"].round(2)
df_fmt.to_csv(OUT_TAB / "cv_sonuc_tablosu.csv", encoding="utf-8-sig")

# Fold bazinda tum sonuclar
pd.concat(fold_results, names=["Model"]).to_csv(OUT_TAB / "cv_fold_detaylari.csv", encoding="utf-8-sig")

# Egitim vs CV (Overfitting) tablosu
df_train_cv = pd.DataFrame(train_cv_rows).set_index("Model").loc[ordered_all]
df_train_cv.round(4).to_csv(OUT_TAB / "egitim_cv_karsilastirma.csv", encoding="utf-8-sig")

# Eslestirilmis Fold Farklari (Referans: en yuksek MCC'li model)
best_model = real_models_sorted[0]
paired_rows = []
for other in ordered_all:
    if other == best_model:
        continue
    row = {"Diger_Model": other}
    for m in ["MCC", "F1_M", "AUPR_M"]:
        diff = fold_results[best_model][m].to_numpy() - fold_results[other][m].to_numpy()
        wins = int((diff > 1e-12).sum())
        losses = int((diff < -1e-12).sum())
        ties = int(len(diff) - wins - losses)
        ky = f"{wins}-{losses}" if ties == 0 else f"{wins}-{losses}-{ties}"
        row[f"{m}_Fark_Ort"] = float(np.mean(diff))
        row[f"{m}_Fark_Std"] = float(np.std(diff, ddof=1))
        row[f"{m}_KY"] = ky
    paired_rows.append(row)
df_paired = pd.DataFrame(paired_rows).set_index("Diger_Model")
df_paired.round(4).to_csv(OUT_TAB / "eslestirilmis_fold_farklari.csv", encoding="utf-8-sig")

# Sampiyon modelin sinif bazinda raporu ve sayisal karmasiklik matrisi (OOF)
rep_dict = classification_report(
    y, oof_preds[best_model], target_names=CLASS_NAMES_TR, output_dict=True
)
pd.DataFrame(rep_dict).T.round(4).to_csv(OUT_TAB / "sinif_bazinda_rapor.csv", encoding="utf-8-sig")

cm_best = confusion_matrix(y, oof_preds[best_model], labels=[0, 1, 2, 3])
df_cm_best = pd.DataFrame(cm_best, index=CLASS_NAMES_TR, columns=CLASS_NAMES_TR)
df_cm_best.to_csv(OUT_TAB / "sampiyon_confusion_matrix.csv", encoding="utf-8-sig")

# Verimlilik tablosu (tum gercek modeller)
df_eff = pd.DataFrame({
    "Model": real_models_sorted,
    "Accuracy": [summary_mean.loc[m, "Accuracy"] for m in real_models_sorted],
    "F1_Macro": [summary_mean.loc[m, "F1_M"] for m in real_models_sorted],
    "MCC": [summary_mean.loc[m, "MCC"] for m in real_models_sorted],
    "Sure_sn": [summary_mean.loc[m, "Sure_sn"] for m in real_models_sorted],
}).round(4)
df_eff.to_csv(OUT_TAB / "verimlilik_tablosu.csv", index=False, encoding="utf-8-sig")

# -----------------------------------------------------------------------------
# 5. [ADIM 2/4] OVERFITTING DENEYI: max_depth TARAMASI & OGRENME EGRISI
# -----------------------------------------------------------------------------
print("\n[ADIM 2/4] Overfitting Deneyi (max_depth Taramasi ve Ogrenme Egrisi)...")
depths = [1, 2, 4, 6, 8, 12, 16, None]
depth_rows = []
for d in depths:
    dt_pipe = Pipeline([
        ("prep", make_preprocessor(False)),
        ("clf", DecisionTreeClassifier(max_depth=d, random_state=RANDOM_STATE)),
    ])
    tr_scores, va_scores = [], []
    for tr_idx, te_idx in cv.split(X, y):
        m_dt = clone(dt_pipe).fit(X.iloc[tr_idx], y.iloc[tr_idx])
        tr_scores.append(f1_score(y.iloc[tr_idx], m_dt.predict(X.iloc[tr_idx]), average="macro"))
        va_scores.append(f1_score(y.iloc[te_idx], m_dt.predict(X.iloc[te_idx]), average="macro"))
    depth_rows.append({
        "max_depth": "Sınırsız" if d is None else str(d),
        "Egitim_F1_Macro": float(np.mean(tr_scores)),
        "CV_F1_Macro_Ort": float(np.mean(va_scores)),
        "CV_F1_Macro_Std": float(np.std(va_scores, ddof=1)),
        "Fark": float(np.mean(tr_scores) - np.mean(va_scores)),
    })
df_depth = pd.DataFrame(depth_rows)
df_depth.round(4).to_csv(OUT_TAB / "derinlik_taramasi.csv", index=False, encoding="utf-8-sig")
print(df_depth.round(4).to_string(index=False))

# Ogrenme egrisi (5-fold StratifiedKFold, 5 boyut)
cv5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
lc_models = {
    "Karar Ağacı (max_depth=2)": Pipeline([
        ("prep", make_preprocessor(False)),
        ("clf", DecisionTreeClassifier(max_depth=2, random_state=RANDOM_STATE)),
    ]),
    "Karar Ağacı (Sınırsız)": Pipeline([
        ("prep", make_preprocessor(False)),
        ("clf", DecisionTreeClassifier(random_state=RANDOM_STATE)),
    ]),
    "Lojistik Regresyon (Ölçekli)": Pipeline([
        ("prep", make_preprocessor(True)),
        ("clf", LogisticRegression(max_iter=500, random_state=RANDOM_STATE)),
    ]),
}
lc_rows = []
lc_plot_data = {}
for m_name, m_est in lc_models.items():
    sizes, tr_sc, va_sc = learning_curve(
        m_est, X, y, cv=cv5, scoring="f1_macro",
        shuffle=True, random_state=RANDOM_STATE,
        train_sizes=np.linspace(0.1, 1.0, 5), n_jobs=2
    )
    lc_plot_data[m_name] = (sizes, tr_sc, va_sc)
    for s, tr_r, va_r in zip(sizes, tr_sc, va_sc):
        lc_rows.append({
            "Model": m_name,
            "Egitim_Boyutu": int(s),
            "Egitim_F1_Macro": float(tr_r.mean()),
            "CV_F1_Macro_Ort": float(va_r.mean()),
            "CV_F1_Macro_Std": float(va_r.std(ddof=1)),
        })
df_lc = pd.DataFrame(lc_rows)
df_lc.round(4).to_csv(OUT_TAB / "ogrenme_egrileri.csv", index=False, encoding="utf-8-sig")

# -----------------------------------------------------------------------------
# 6. [ADIM 3/4] SINIF DENGESIZLIGI DENEYI (class_weight & SMOTE Pipeline Icinde)
#    + SMOTE SIZINTI DENEYI (Bolum 7.3 - 7.4)
# -----------------------------------------------------------------------------
print("\n[ADIM 3/4] Sinif Dengesizligi Deneyi (20.000 Tabakali Orneklem, 10-Kat CV)...")
X_imb, _, y_imb, _ = train_test_split(
    X, y, train_size=20000, random_state=RANDOM_STATE, stratify=y
)
X_imb = X_imb.reset_index(drop=True)
y_imb = y_imb.reset_index(drop=True)

imb_models = {
    "Dummy (Çoğunluk)": Pipeline([("clf", DummyClassifier(strategy="most_frequent"))]),
    "LR (Sade)": Pipeline([
        ("prep", make_preprocessor(True)),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
    ]),
    "LR + class_weight": Pipeline([
        ("prep", make_preprocessor(True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)),
    ]),
    "LR + SMOTE (Pipeline)": ImbPipeline([
        ("prep", make_preprocessor(True)),
        ("smote", SMOTE(random_state=RANDOM_STATE)),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
    ]),
    "RF (Sade)": Pipeline([
        ("prep", make_preprocessor(False)),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=2)),
    ]),
    "RF + class_weight": Pipeline([
        ("prep", make_preprocessor(False)),
        ("clf", RandomForestClassifier(
            n_estimators=100, class_weight="balanced_subsample", random_state=RANDOM_STATE, n_jobs=2
        )),
    ]),
    "RF + SMOTE (Pipeline)": ImbPipeline([
        ("prep", make_preprocessor(True)),  # SMOTE mesafe kullandigi icin olcekleme once gelir
        ("smote", SMOTE(random_state=RANDOM_STATE)),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=2)),
    ]),
}

imb_rows = []
for name, est in imb_models.items():
    accs, f1m, rec_mod, rec_sev, mccs, auprs = [], [], [], [], [], []
    for tr_idx, te_idx in cv.split(X_imb, y_imb):
        fitted = clone(est).fit(X_imb.iloc[tr_idx], y_imb.iloc[tr_idx])
        pred = fitted.predict(X_imb.iloc[te_idx])
        prob, _ = get_scores(fitted, X_imb.iloc[te_idx])
        y_te = y_imb.iloc[te_idx]
        y_bin = label_binarize(y_te, classes=[0, 1, 2, 3])
        rec_per_class = recall_score(y_te, pred, labels=[0, 1, 2, 3], average=None, zero_division=0)
        accs.append(accuracy_score(y_te, pred))
        f1m.append(f1_score(y_te, pred, average="macro", zero_division=0))
        rec_mod.append(rec_per_class[2])
        rec_sev.append(rec_per_class[3])
        mccs.append(matthews_corrcoef(y_te, pred))
        auprs.append(average_precision_score(y_bin, prob, average="macro"))
    imb_rows.append({
        "Model": name,
        "Accuracy_Ort": np.mean(accs), "Accuracy_Std": np.std(accs, ddof=1),
        "F1_Macro_Ort": np.mean(f1m), "F1_Macro_Std": np.std(f1m, ddof=1),
        "Recall_Orta_Ort": np.mean(rec_mod), "Recall_Orta_Std": np.std(rec_mod, ddof=1),
        "Recall_Agir_Ort": np.mean(rec_sev), "Recall_Agir_Std": np.std(rec_sev, ddof=1),
        "MCC_Ort": np.mean(mccs), "MCC_Std": np.std(mccs, ddof=1),
        "AUPR_Macro_Ort": np.mean(auprs), "AUPR_Macro_Std": np.std(auprs, ddof=1),
    })
df_imb = pd.DataFrame(imb_rows).set_index("Model")
df_imb.round(4).to_csv(OUT_TAB / "dengesizlik_deneyi.csv", encoding="utf-8-sig")
print(df_imb[["Accuracy_Ort", "F1_Macro_Ort", "Recall_Orta_Ort", "Recall_Agir_Ort", "MCC_Ort"]].round(4).to_string())

# SMOTE Sizinti Deneyi (Yanlis: CV oncesi SMOTE vs Dogru: Pipeline icinde SMOTE)
prep_all = make_preprocessor(True)
X_imb_enc = prep_all.fit_transform(X_imb)
X_res, y_res = SMOTE(random_state=RANDOM_STATE).fit_resample(X_imb_enc, y_imb)
n_orig = len(y_imb)
is_orig = np.arange(len(y_res)) < n_orig

leak_f1m, leak_rec_sev, leak_mcc = [], [], []
for tr_idx, te_idx in cv.split(X_res, y_res):
    rf_leak = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=2).fit(
        X_res[tr_idx], y_res.iloc[tr_idx]
    )
    te_real = te_idx[is_orig[te_idx]]
    pred_l = rf_leak.predict(X_res[te_real])
    y_te_real = y_res.iloc[te_real]
    rec_c = recall_score(y_te_real, pred_l, labels=[0, 1, 2, 3], average=None, zero_division=0)
    leak_f1m.append(f1_score(y_te_real, pred_l, average="macro", zero_division=0))
    leak_rec_sev.append(rec_c[3])
    leak_mcc.append(matthews_corrcoef(y_te_real, pred_l))

df_smote_leak = pd.DataFrame([
    {
        "Yontem": "Yanlış (Önce SMOTE → Sonra CV)",
        "F1_Macro": float(np.mean(leak_f1m)),
        "Recall_Agir": float(np.mean(leak_rec_sev)),
        "MCC": float(np.mean(leak_mcc)),
    },
    {
        "Yontem": "Doğru (Pipeline İçinde SMOTE)",
        "F1_Macro": float(df_imb.loc["RF + SMOTE (Pipeline)", "F1_Macro_Ort"]),
        "Recall_Agir": float(df_imb.loc["RF + SMOTE (Pipeline)", "Recall_Agir_Ort"]),
        "MCC": float(df_imb.loc["RF + SMOTE (Pipeline)", "MCC_Ort"]),
    },
]).set_index("Yontem")
df_smote_leak.round(4).to_csv(OUT_TAB / "smote_sizinti_deneyi.csv", encoding="utf-8-sig")
print("\nSMOTE Sizinti Deneyi:")
print(df_smote_leak.round(4).to_string())

# -----------------------------------------------------------------------------
# 7. [ADIM 4/4] OZNITELIK ONEM ANALIZI (One-Hot Toplanmis, Betimleyici)
# -----------------------------------------------------------------------------
print("\n[ADIM 4/4] Oznitelik Onem Analizi ve Grafikler Uretiliyor...")
rf_full = Pipeline([
    ("prep", make_preprocessor(False)),
    ("clf", RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=2)),
]).fit(X, y)

feat_names_out = rf_full.named_steps["prep"].get_feature_names_out()
importances_raw = rf_full.named_steps["clf"].feature_importances_

# One-hot sutunlari ana oznitelik adina geri topla
agg_imp = {}
for fname, imp in zip(feat_names_out, importances_raw):
    if fname.startswith("num__"):
        orig = fname.replace("num__", "")
    elif fname.startswith("cat__"):
        rest = fname.replace("cat__", "")
        orig = next((c for c in cat_cols if rest.startswith(c + "_")), rest)
    else:
        orig = fname
    agg_imp[orig] = agg_imp.get(orig, 0.0) + float(imp)

TR_LABEL_MAP = {
    "sleep_quality_score": "Uyku Kalite Skoru (sleep_quality)",
    "mental_health_condition": "Ruh Sağlığı Durumu (mental_health)",
    "sleep_duration_hrs": "Uyku Süresi - Saat (sleep_duration)",
    "bmi": "Vücut Kitle İndeksi (bmi)",
    "sleep_fragmentation_index": "Uyku Bölünme İndeksi - SFI (Türetilmiş)",
    "stress_score": "Stres Skoru (stress)",
    "sleep_latency_mins": "Uykuya Dalma Süresi (latency)",
    "wake_episodes_per_night": "Gece Uyanma Sayısı (wakeups)",
    "rem_percentage": "REM Uykusu Yüzdesi (rem_perc)",
    "restorative_sleep_ratio": "Onarıcı Uyku Oranı - RSR (Türetilmiş)",
    "age": "Yaş (age)",
    "work_hours_that_day": "Günlük Çalışma Saati (work_hours)",
    "screen_time_before_bed_mins": "Ekran Süresi (screen_time)",
    "steps_that_day": "Günlük Adım Sayısı (steps)",
    "deep_sleep_percentage": "Derin Uyku Yüzdesi (deep_sleep)",
    "weekend_sleep_diff_hrs": "Hafta Sonu Uyku Farkı (weekend_diff)",
    "room_temperature_celsius": "Oda Sıcaklığı (room_temp)",
    "heart_rate_resting_bpm": "Dinlenme Nabzı (heart_rate)",
    "alcohol_units_before_bed": "Alkol Tüketimi (alcohol)",
    "caffeine_mg_before_bed": "Kafein Tüketimi (caffeine)",
    "shift_work": "Vardiyalı Çalışma (shift_work)",
    "occupation": "Meslek (occupation)",
    "country": "Ülke (country)",
    "nap_duration_mins": "Gündüz Şekerleme (nap)",
    "chronotype": "Kronotip (chronotype)",
    "season": "Mevsim (season)",
    "day_type": "Gün Tipi (day_type)",
    "gender": "Cinsiyet (gender)",
    "sleep_aid_used": "Uyku İlacı (sleep_aid)",
    "exercise_day": "Egzersiz (exercise)",
}

df_imp = pd.DataFrame([
    {
        "Ozellik": TR_LABEL_MAP.get(k, k),
        "Orijinal_Sutun": k,
        "Onem_Skoru": v,
        "Yuzde_Etki": v * 100.0,
    }
    for k, v in agg_imp.items()
]).sort_values("Onem_Skoru", ascending=False).reset_index(drop=True)
df_imp.round(4).to_csv(OUT_TAB / "ozellik_onem_tablosu.csv", index=False, encoding="utf-8-sig")

# -----------------------------------------------------------------------------
# 8. GRAFIKLER (Ders Notu Stiline Uygun Yuksek Cozunurluklu Ciktilar)
# -----------------------------------------------------------------------------

# Grafik 2: Model Karsilastirma (2x2 Errorbar: Accuracy, Macro F1, MCC, AUPR_M)
fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2), sharey=True)
ypos = np.arange(len(ordered_all))
for ax, (col, title) in zip(
    axes.ravel(),
    [
        ("Accuracy", "Doğruluk — Accuracy (ort ± std)"),
        ("F1_M", "Macro F1-Skoru (ort ± std)"),
        ("MCC", "Matthews Korelasyon Katsayısı — MCC (ort ± std)"),
        ("AUPR_M", "Macro AUPR / Average Precision (ort ± std)"),
    ],
):
    mu = summary_mean.loc[ordered_all, col].to_numpy()
    sd = summary_std.loc[ordered_all, col].to_numpy()
    ax.errorbar(mu, ypos, xerr=sd, fmt="o", color=PALETTE[0], ms=6, elinewidth=1.2, capsize=3)
    ax.set_yticks(ypos, ordered_all)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
fig.suptitle("10-Kat Stratified CV: 9 Model ve Dummy Referans Karşılaştırması (100.000 Satır)", fontweight="bold")
plt.tight_layout()
fig.savefig(OUT_FIG / "grafik_2_model_karsilastirma.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Grafik 3: ROC ve Precision-Recall Egrileri (OOF — Agir Risk Sinifi & Macro)
y_bin_all = label_binarize(y, classes=[0, 1, 2, 3])
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
for idx, name in enumerate(real_models_sorted):
    s = oof_scores[name]
    # Agir (Severe = sinif 3) icin ROC ve PR (klinik olarak en kritik azinlik sinifi: %4.07)
    fpr, tpr, _ = roc_curve(y_bin_all[:, 3], s[:, 3])
    auc_s3 = roc_auc_score(y_bin_all[:, 3], s[:, 3])
    axes[0].plot(fpr, tpr, color=PALETTE[idx % len(PALETTE)], label=f"{name} (AUC={auc_s3:.3f})")

    prec_c, rec_c, _ = precision_recall_curve(y_bin_all[:, 3], s[:, 3])
    ap_s3 = average_precision_score(y_bin_all[:, 3], s[:, 3])
    axes[1].plot(rec_c, prec_c, color=PALETTE[idx % len(PALETTE)], label=f"{name} (AP={ap_s3:.3f})")

axes[0].plot([0, 1], [0, 1], color=RULE, linestyle="--", lw=1, label="Rastgele (0,500)")
axes[0].set(xlabel="Yanlış Pozitif Oranı (FPR)", ylabel="Doğru Pozitif Oranı (Recall)",
            title="ROC Eğrileri — Ağır Risk (Severe) Sınıfı (OOF)")
axes[0].legend(loc="lower right", fontsize=7.5)

prev_s3 = float((y == 3).mean())
axes[1].axhline(prev_s3, color=RULE, linestyle="--", lw=1, label=f"Taban / Prevalans ({prev_s3:.3f})")
axes[1].set(xlabel="Duyarlılık (Recall)", ylabel="Kesinlik (Precision)",
            title="Precision–Recall Eğrileri — Ağır Risk (Severe) Sınıfı (OOF)")
axes[1].legend(loc="lower left", fontsize=7.5)

plt.tight_layout()
fig.savefig(OUT_FIG / "grafik_3_roc_pr_egrileri.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Grafik 4: 3x3 OOF Karmasiklik Matrisleri (9 gercek model)
short_labels = ["Sağlıklı", "Hafif", "Orta", "Ağır"]
fig, axes = plt.subplots(3, 3, figsize=(15.5, 13.5))
for ax, name in zip(axes.ravel(), real_models_sorted):
    cm = confusion_matrix(y, oof_preds[name], labels=[0, 1, 2, 3])
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax,
        xticklabels=short_labels, yticklabels=short_labels, annot_kws={"size": 9}
    )
    ax.set_title(f"{name} (MCC={summary_mean.loc[name, 'MCC']:.3f})", fontweight="bold")
    ax.set_xlabel("Tahmin Edilen Sınıf")
    ax.set_ylabel("Gerçek Sınıf")
fig.suptitle("10-Kat Çapraz Doğrulama Birleşik (Out-of-Fold) Karmaşıklık Matrisleri (100.000 Örnek)", fontsize=13, fontweight="bold", y=0.995)
plt.tight_layout()
fig.savefig(OUT_FIG / "grafik_4_confusion_matrices.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# Grafik 5: Oznitelik Onem Duzeyleri (Ilk 15)
top15 = df_imp.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(8.8, 5.6))
colors_imp = ["#eb6834" if "Türetilmiş" in x else "#2a78d6" for x in top15["Ozellik"]]
bars = ax.barh(top15["Ozellik"], top15["Yuzde_Etki"], color=colors_imp)
for bar, val in zip(bars, top15["Yuzde_Etki"]):
    ax.text(val + 0.25, bar.get_y() + bar.get_height() / 2, f"%{val:.2f}", va="center", fontsize=8.5)
ax.set_xlabel("Önem Payı (%) — Gini Katsayısı (One-Hot Toplanmış)")
ax.set_title("Uyku Bozukluğu Riskini Belirleyen En Etkili 15 Öznitelik (Turuncu: Türetilmiş Klinik Metrik)")
ax.set_xlim(0, top15["Yuzde_Etki"].max() * 1.16)
ax.grid(axis="y", visible=False)
plt.tight_layout()
fig.savefig(OUT_FIG / "grafik_5_ozellik_onemi.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Grafik 6: Overfitting (max_depth Taramasi + Ogrenme Egrileri)
fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.4))
xs = np.arange(len(df_depth))
axes[0].fill_between(
    xs,
    df_depth["CV_F1_Macro_Ort"] - df_depth["CV_F1_Macro_Std"],
    df_depth["CV_F1_Macro_Ort"] + df_depth["CV_F1_Macro_Std"],
    color=PALETTE[1], alpha=0.18
)
axes[0].plot(xs, df_depth["Egitim_F1_Macro"], color=PALETTE[0], marker="o", label="Eğitim Macro F1")
axes[0].plot(xs, df_depth["CV_F1_Macro_Ort"], color=PALETTE[1], marker="s", label="10-Kat CV Macro F1 (± std)")
axes[0].set_xticks(xs, df_depth["max_depth"])
axes[0].set(xlabel="Karar Ağacı max_depth", ylabel="Macro F1", title="Karmaşıklık Taraması (Overfitting Analizi)")
axes[0].legend(loc="lower right")

for idx, (m_name, (sizes, tr_sc, va_sc)) in enumerate(lc_plot_data.items()):
    va_mu = va_sc.mean(axis=1)
    va_sd = va_sc.std(axis=1, ddof=1)
    axes[1].plot(sizes, va_mu, marker="o", color=PALETTE[idx], label=f"{m_name} (CV)")
    axes[1].fill_between(sizes, va_mu - va_sd, va_mu + va_sd, color=PALETTE[idx], alpha=0.12)
axes[1].set(xlabel="Eğitim Örnek Sayısı", ylabel="Macro F1 (5-Kat CV)", title="Öğrenme Eğrileri (Learning Curves)")
axes[1].legend(loc="lower right", fontsize=8)
plt.tight_layout()
fig.savefig(OUT_FIG / "grafik_6_derinlik_ve_ogrenme.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Grafik 7: Sinif Dengesizligi Deneyi
fig, ax = plt.subplots(figsize=(9.0, 4.6))
shown_imb = ["Accuracy_Ort", "F1_Macro_Ort", "Recall_Agir_Ort", "MCC_Ort", "AUPR_Macro_Ort"]
labels_imb = ["Accuracy", "Macro F1", "Ağır Sınıf Recall", "MCC", "Macro AUPR"]
markers_imb = ["o", "s", "^", "D", "v"]
imb_names = list(df_imb.index)
for k, (col, lab, mk) in enumerate(zip(shown_imb, labels_imb, markers_imb)):
    offs = (k - 2) * 0.13
    ax.scatter(df_imb.loc[imb_names, col], np.arange(len(imb_names)) + offs, s=45, marker=mk, color=PALETTE[k], label=lab, zorder=3)
ax.set_yticks(np.arange(len(imb_names)), imb_names)
ax.invert_yaxis()
ax.set_xlim(-0.04, 1.04)
ax.set_xlabel("10-Kat CV Ortalaması (20.000 Tabakalı Örneklem)")
ax.set_title("Sınıf Dengesizliği Müdahale Deneyi: Sade vs. class_weight vs. SMOTE (Pipeline İçinde)")
ax.grid(axis="y", visible=False)
ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.48, -0.15), fontsize=8)
plt.tight_layout()
fig.savefig(OUT_FIG / "grafik_7_dengesizlik_deneyi.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Grafik 8: Verimlilik (Hiz vs MCC)
fig, ax = plt.subplots(figsize=(8.5, 4.8))
for idx, m in enumerate(real_models_sorted):
    t_s = summary_mean.loc[m, "Sure_sn"]
    mcc_v = summary_mean.loc[m, "MCC"]
    ax.scatter(t_s, mcc_v, color=PALETTE[idx % len(PALETTE)], s=95, edgecolors="black", zorder=4)
    ax.annotate(m, (t_s, mcc_v), textcoords="offset points", xytext=(7, 4), fontsize=8.5, fontweight="bold")
ax.set(xlabel="Toplam 10-Kat CV Süresi (Saniye) — Sola Doğru Daha Hızlı",
       ylabel="10-Kat Ortalama MCC — Yukarı Doğru Daha Başarılı",
       title="Model Verimliliği: Hesaplama Süresi vs. MCC Performansı")
plt.tight_layout()
fig.savefig(OUT_FIG / "grafik_8_hiz_vs_basari.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# JSON Kaydet (Tek Gercek Kaynagi)
RESULTS["best_model"] = best_model
RESULTS["model_order"] = ordered_all
RESULTS["summary_mean"] = summary_mean.round(4).where(pd.notna(summary_mean), None).to_dict(orient="index")
RESULTS["summary_std"] = summary_std.round(4).where(pd.notna(summary_std), None).to_dict(orient="index")
RESULTS["smote_leak"] = df_smote_leak.round(4).to_dict(orient="index")

with open(OUT_TAB / "sonuclar.json", "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 74)
print("TUM DENEYLER VE GRAFIKLER BASARIYLA TAMAMLANDI!")
print(f"Sampiyon Model (MCC'ye gore): {best_model} (MCC={summary_mean.loc[best_model, 'MCC']:.4f}, Macro F1={summary_mean.loc[best_model, 'F1_M']:.4f})")
print("=" * 74)
