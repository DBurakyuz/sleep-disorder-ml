# =============================================================================
# MAKINE OGRENMESI: SIZINTISIZ 10-KAT CAPRAZ DOGRULAMA VE KAPSAMLI DENEYLER
# Uyku Sagligi ve Gunluk Performans - Cok Sinifli (Sirali) Uyku Bozuklugu Riski
# Yalova Universitesi - Bilgisayar Muhendisligi (Uygulamali Ders Notu Uyumlu)
# =============================================================================

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import catboost
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
    cohen_kappa_score,
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

def save_fig(fig, path: Path, dpi: int = 200):
    with open(path, "wb") as fp:
        fig.savefig(fp, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

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

print("=" * 76)
print("SIZINTISIZ 10-KAT CV — SIRALI/DENGESIZ METRIKLER VE DENEYLER BASLIYOR")
print("=" * 76)
for k, v in VERSIONS.items():
    print(f"  {k:18s}: {v}")
print("-" * 76)

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
# 2. VERI YUKLEME, KALITE VE SUPHELI YAPI KONTROLLERI
# -----------------------------------------------------------------------------
df_raw = pd.read_csv("sleep_health_dataset.csv")
n_missing = int(df_raw.isna().sum().sum())
n_dup_full = int(df_raw.duplicated().sum())
n_dup_no_id = int(df_raw.drop(columns=["person_id"]).duplicated().sum())

# Kimlik ve hedef sonucu (post-hoc target proxy) sutunlarini cikar
drop_cols = ["person_id", "cognitive_performance_score", "felt_rested"]
df = df_raw.drop(columns=drop_cols).copy()

# Satir bazli deterministik klinik ozellik muhendisligi
df["sleep_fragmentation_index"] = (df["wake_episodes_per_night"] / df["sleep_duration_hrs"]).round(4)
df["restorative_sleep_ratio"] = (df["deep_sleep_percentage"] + df["rem_percentage"]).round(4)

# Sirali hedef kodlamasi: Saglikli (0) < Hafif (1) < Orta (2) < Agir (3)
CLASS_MAP = {"Healthy": 0, "Mild": 1, "Moderate": 2, "Severe": 3}
CLASS_NAMES_TR = ["Sağlıklı (Healthy)", "Hafif (Mild)", "Orta (Moderate)", "Ağır (Severe)"]
y = df["sleep_disorder_risk"].map(CLASS_MAP).astype(int)
X = df.drop(columns=["sleep_disorder_risk"])

cat_cols = [
    "gender", "occupation", "country", "chronotype",
    "mental_health_condition", "season", "day_type"
]
num_cols = [c for c in X.columns if c not in cat_cols]

# Supheli yapi kontrolu: sabit sutunlar ve dogrusal bagimliliklar (Bölüm 3.7 / s. 93)
const_cols = [c for c in X.columns if X[c].nunique() <= 1]
corr_mat = X[num_cols].corr().abs()
high_corr_pairs = []
for c1 in num_cols:
    for c2 in num_cols:
        if c1 < c2 and corr_mat.loc[c1, c2] >= 0.70:
            high_corr_pairs.append({
                "sutun_1": c1, "sutun_2": c2, "korelasyon": round(float(corr_mat.loc[c1, c2]), 4)
            })
rsr_max_diff = float((X["restorative_sleep_ratio"] - (X["deep_sleep_percentage"] + X["rem_percentage"])).abs().max())

counts = y.value_counts().sort_index()
pcts = (y.value_counts(normalize=True).sort_index() * 100).round(2)

print(f"Ham veri boyutu             : {df_raw.shape}")
print(f"Eksik / Duplicate (ID haric): {n_missing} / {n_dup_no_id}")
print(f"Sabit sutun sayisi          : {len(const_cols)}")
print(f"RSR = deep + rem max fark   : {rsr_max_diff:.6f} (tam dogrusal toplam!)")
print(f"Yuksek korelasyonlu cift (>=0.70): {high_corr_pairs}")
print(f"Sayisal: {len(num_cols)} | Nominal kategorik: {len(cat_cols)}")

RESULTS["dataset"] = {
    "source": "Kaggle — Sleep Health and Daily Performance Dataset (not UCI; sentetik bileşen içerebilir)",
    "n_samples": int(len(df)),
    "n_raw_cols": int(df_raw.shape[1]),
    "n_features_before_ohe": int(X.shape[1]),
    "n_numeric": len(num_cols),
    "n_categorical": len(cat_cols),
    "n_missing": n_missing,
    "n_duplicates_no_id": n_dup_no_id,
    "const_cols": const_cols,
    "rsr_exact_linear_max_diff": rsr_max_diff,
    "high_corr_pairs": high_corr_pairs,
    "class_counts": {CLASS_NAMES_TR[i]: int(counts[i]) for i in range(4)},
    "class_pcts": {CLASS_NAMES_TR[i]: float(pcts[i]) for i in range(4)},
}

# Grafik 1: Sinif Dagilimi
fig, ax = plt.subplots(figsize=(7.5, 4.0))
bars = ax.bar(CLASS_NAMES_TR, [counts[i] for i in range(4)], color=PALETTE[:4], width=0.55)
for bar, i in zip(bars, range(4)):
    cnt_tr = f"{counts[i]:,}".replace(",", ".")
    pct_tr = f"{pcts[i]:.2f}".replace(".", ",")
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 900,
        f"{cnt_tr}\n(%{pct_tr})",
        ha="center", va="bottom", fontsize=9, fontweight="bold"
    )
ax.set_ylabel("Örnek Sayısı")
ax.set_title("Hedef Değişken Sınıf Dağılımı (100.000 Birey — Sıralı ve Dengesiz Yapı)")
ax.set_ylim(0, max(counts) * 1.18)
ax.grid(axis="x", visible=False)
plt.tight_layout()
save_fig(fig, OUT_FIG / "grafik_1_sinif_dagilimi.png", dpi=200)

# -----------------------------------------------------------------------------
# 3. SIZINTISIZ ON ISLEME VE MODELLER
# -----------------------------------------------------------------------------
def make_preprocessor(scale_numeric: bool) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler() if scale_numeric else "passthrough", num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ]
    )

def build_models():
    """
    Dummy (Onsel / prior): predict() icin cogunluk sinifini, predict_proba() icin
    egitim fold'undaki gercek sinif oranlarini dondurur (adil Log-Loss referansi).
    """
    return {
        "Dummy (Önsel / Prior)": Pipeline([
            ("clf", DummyClassifier(strategy="prior"))
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
# 4. METRIK HESAPLAMA (AGIRLIKLI FAZLALIKLAR YOK; SIRALI QWK & SINIF BAZLI VAR)
# -----------------------------------------------------------------------------
def class_specificity(y_true, y_pred, target_class: int) -> float:
    """Belirli bir pozitif sinif icin OvR Ozgulluk = TN / (TN + FP)."""
    y_t = (y_true == target_class).astype(int)
    y_p = (y_pred == target_class).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_t, y_p, labels=[0, 1]).ravel()
    return float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

def get_scores(fitted_model, X_eval):
    if hasattr(fitted_model, "predict_proba"):
        return fitted_model.predict_proba(X_eval), True
    df_scores = fitted_model.decision_function(X_eval)
    return softmax(df_scores, axis=1), False

def compute_fold_metrics(y_true, y_pred, y_score, is_prob):
    y_bin = label_binarize(y_true, classes=[0, 1, 2, 3])
    prec_c = precision_score(y_true, y_pred, labels=[0, 1, 2, 3], average=None, zero_division=0)
    rec_c = recall_score(y_true, y_pred, labels=[0, 1, 2, 3], average=None, zero_division=0)
    f1_c = f1_score(y_true, y_pred, labels=[0, 1, 2, 3], average=None, zero_division=0)

    auroc_macro = roc_auc_score(y_true, y_score, multi_class="ovr", average="macro")
    aupr_macro = average_precision_score(y_bin, y_score, average="macro")
    ll = log_loss(y_true, y_score, labels=[0, 1, 2, 3]) if is_prob else np.nan

    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Recall_M": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "F1_M": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "MCC": matthews_corrcoef(y_true, y_pred),
        "Kappa": cohen_kappa_score(y_true, y_pred),
        "QWK": cohen_kappa_score(y_true, y_pred, weights="quadratic"),
        "AUROC_M": auroc_macro,
        "AUPR_M": aupr_macro,
        "Log_Loss": ll,
        # Birincil pozitif sinif: Agir (Severe = 3) ve en zor sinif: Orta (Moderate = 2)
        "Agir_Recall": float(rec_c[3]),
        "Agir_Precision": float(prec_c[3]),
        "Agir_Specificity": class_specificity(y_true, y_pred, 3),
        "Agir_F1": float(f1_c[3]),
        "Orta_Recall": float(rec_c[2]),
        "Orta_Precision": float(prec_c[2]),
        "Orta_F1": float(f1_c[2]),
    }

cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
models = build_models()

fold_results = {}
oof_preds = {}
oof_scores = {}
train_cv_rows = []
elapsed_times = {}
catboost_fold_importances = []  # Sizintisiz: 10 egitim katlamasindan CatBoost onemi!

print("\n[ADIM 1/4] 10-Kat Stratified CV Basliyor (100.000 Satir, Pipeline + OneHotEncoder)...")
print("-" * 76)

for name, est in models.items():
    print(f">> {name:22s} ... ", end="", flush=True)
    t0 = time.time()
    rows = []
    oof_p = np.zeros(len(y), dtype=int)
    oof_s = np.zeros((len(y), 4), dtype=float)
    tr_f1_m_list = []

    for fold, (tr_idx, te_idx) in enumerate(cv.split(X, y), start=1):
        X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
        y_tr, y_te = y.iloc[tr_idx], y.iloc[te_idx]

        if name == "RBF SVM" and len(X_tr) > 25000:
            X_tr, _, y_tr, _ = train_test_split(
                X_tr, y_tr, train_size=25000, random_state=RANDOM_STATE, stratify=y_tr
            )

        fitted = clone(est).fit(X_tr, y_tr)

        # CatBoost oznitelik onemini yalnizca egitim fold'undan topla (sizintisiz!)
        if name == "CatBoost":
            f_names = fitted.named_steps["prep"].get_feature_names_out()
            f_imps = fitted.named_steps["clf"].get_feature_importance()
            agg = {}
            for fn, iv in zip(f_names, f_imps):
                if fn.startswith("num__"):
                    orig = fn.replace("num__", "")
                elif fn.startswith("cat__"):
                    rest = fn.replace("cat__", "")
                    orig = next((c for c in cat_cols if rest.startswith(c + "_")), rest)
                else:
                    orig = fn
                agg[orig] = agg.get(orig, 0.0) + float(iv)
            catboost_fold_importances.append(agg)

        tr_pred = np.ravel(fitted.predict(X_tr))
        tr_f1_m_list.append(f1_score(y_tr, tr_pred, average="macro", zero_division=0))

        te_pred = np.ravel(fitted.predict(X_te))
        te_score, is_prob = get_scores(fitted, X_te)

        oof_p[te_idx] = te_pred
        oof_s[te_idx] = te_score

        m = compute_fold_metrics(y_te.to_numpy(), te_pred, te_score, is_prob)
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
    })

    print(
        f"Tamam ({elapsed:5.1f}s) | Acc: {df_f['Accuracy'].mean():.4f} | "
        f"MacroRec: {df_f['Recall_M'].mean():.4f} | MacroF1: {df_f['F1_M'].mean():.4f} | "
        f"MCC: {df_f['MCC'].mean():.4f} | QWK: {df_f['QWK'].mean():.4f}"
    )

# Ozet Tablolar (ddof=1 orneklem standart sapmasi)
METRIC_COLS = [
    "Accuracy", "Recall_M", "F1_M", "MCC", "Kappa", "QWK",
    "AUROC_M", "AUPR_M", "Log_Loss",
    "Agir_Recall", "Agir_Precision", "Agir_Specificity", "Agir_F1",
    "Orta_Recall", "Orta_Precision", "Orta_F1",
]
summary_mean = pd.DataFrame({n: f[METRIC_COLS].mean() for n, f in fold_results.items()}).T
summary_std = pd.DataFrame({n: f[METRIC_COLS].std(ddof=1) for n, f in fold_results.items()}).T
summary_mean["Sure_sn"] = pd.Series(elapsed_times)

DUMMY_NAME = "Dummy (Önsel / Prior)"
real_models_sorted = (
    summary_mean.drop(index=[DUMMY_NAME])
    .sort_values("MCC", ascending=False)
    .index.tolist()
)
ordered_all = real_models_sorted + [DUMMY_NAME]
summary_mean = summary_mean.loc[ordered_all]
summary_std = summary_std.loc[ordered_all]

# >= 2 sinif uzak kritik hata sayisi (OOF)
y_arr = y.to_numpy()
summary_mean["Uzak_Hata_2Plus"] = [
    int((np.abs(y_arr - oof_preds[m]) >= 2).sum()) for m in ordered_all
]

summary_mean.round(4).to_csv(OUT_TAB / "cv_ortalama.csv", encoding="utf-8-sig")
summary_std.round(4).to_csv(OUT_TAB / "cv_std.csv", encoding="utf-8-sig")
pd.concat(fold_results, names=["Model"]).to_csv(OUT_TAB / "cv_fold_detaylari.csv", encoding="utf-8-sig")

# Azinlik Sinif Karsilastirma Tablosu (Tum Modeller: Agir + Orta + >=2 Sinif Uzak Hata)
df_min = pd.DataFrame(index=ordered_all)
for col in ["Agir_Recall", "Agir_Precision", "Agir_Specificity", "Orta_Recall", "Orta_Precision", "Orta_F1"]:
    df_min[col] = summary_mean[col].round(4)
df_min["Uzak_Hata_2Plus"] = summary_mean["Uzak_Hata_2Plus"].astype(int)
df_min.to_csv(OUT_TAB / "azinlik_sinif_karsilastirma.csv", encoding="utf-8-sig")

# Egitim vs CV (Overfitting) tablosu
df_train_cv = pd.DataFrame(train_cv_rows).set_index("Model").loc[ordered_all]
df_train_cv.round(4).to_csv(OUT_TAB / "egitim_cv_karsilastirma.csv", encoding="utf-8-sig")

# Eslestirilmis Fold Farklari (Yalnizca gercek modeller — Dummy haric!)
best_model = real_models_sorted[0]
paired_rows = []
for other in real_models_sorted:
    if other == best_model:
        continue
    row = {"Diger_Model": other}
    for m in ["MCC", "F1_M", "QWK", "AUPR_M"]:
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
pd.DataFrame(cm_best, index=CLASS_NAMES_TR, columns=CLASS_NAMES_TR).to_csv(
    OUT_TAB / "sampiyon_confusion_matrix.csv", encoding="utf-8-sig"
)

# Prevalansa Gore Varsayimsal PPV Tablosu (Ders Notu Bolum 8.6, Tablo 47 — Koddan Hesapli!)
y_sev_true = (y_arr == 3).astype(int)
y_sev_pred = (oof_preds[best_model] == 3).astype(int)
tn_s, fp_s, fn_s, tp_s = confusion_matrix(y_sev_true, y_sev_pred, labels=[0, 1]).ravel()
sev_rec_oof = tp_s / (tp_s + fn_s)
sev_spec_oof = tn_s / (tn_s + fp_s)
actual_prev = float(y_sev_true.mean())

ppv_rows = []
for p_val, aciklama in [
    (actual_prev, "Veri setindeki oran (OOF Precision ile uyumlu)"),
    (0.02, "Varsayımsal genel klinik tarama (%2)"),
    (0.01, "Varsayımsal düşük prevalanslı tarama (%1)"),
    (0.005, "Varsayımsal nadir tarama (%0,5)"),
]:
    ppv = (sev_rec_oof * p_val) / (sev_rec_oof * p_val + (1.0 - sev_spec_oof) * (1.0 - p_val))
    ppv_rows.append({
        "Prevalans": p_val,
        "Recall_Sabit": sev_rec_oof,
        "Specificity_Sabit": sev_spec_oof,
        "PPV": ppv,
        "Yorum": aciklama,
    })
df_ppv = pd.DataFrame(ppv_rows)
df_ppv.round(4).to_csv(OUT_TAB / "ppv_prevalans_tablosu.csv", index=False, encoding="utf-8-sig")
print("\nPrevalansa Gore Varsayimsal PPV (CatBoost — Agir Sinif):")
print(df_ppv[["Prevalans", "PPV", "Yorum"]].round(4).to_string(index=False))

# Verimlilik tablosu
df_eff = pd.DataFrame({
    "Model": real_models_sorted,
    "Accuracy": [summary_mean.loc[m, "Accuracy"] for m in real_models_sorted],
    "Macro_Recall": [summary_mean.loc[m, "Recall_M"] for m in real_models_sorted],
    "MCC": [summary_mean.loc[m, "MCC"] for m in real_models_sorted],
    "QWK": [summary_mean.loc[m, "QWK"] for m in real_models_sorted],
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
pd.DataFrame(lc_rows).round(4).to_csv(OUT_TAB / "ogrenme_egrileri.csv", index=False, encoding="utf-8-sig")

# -----------------------------------------------------------------------------
# 6. [ADIM 3/4] SINIF DENGESIZLIGI DENEYI + SMOTE SIZINTI DENEYI
# -----------------------------------------------------------------------------
print("\n[ADIM 3/4] Sinif Dengesizligi Deneyi (20.000 Tabakali Orneklem, 10-Kat CV)...")
X_imb, _, y_imb, _ = train_test_split(
    X, y, train_size=20000, random_state=RANDOM_STATE, stratify=y
)
X_imb, y_imb = X_imb.reset_index(drop=True), y_imb.reset_index(drop=True)

imb_models = {
    DUMMY_NAME: Pipeline([("clf", DummyClassifier(strategy="prior"))]),
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
        ("prep", make_preprocessor(True)),
        ("smote", SMOTE(random_state=RANDOM_STATE)),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=2)),
    ]),
}

imb_rows = []
for name, est in imb_models.items():
    accs, f1m, rec_mod, rec_sev, mccs, qwks, auprs = [], [], [], [], [], [], []
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
        qwks.append(cohen_kappa_score(y_te, pred, weights="quadratic"))
        auprs.append(average_precision_score(y_bin, prob, average="macro"))
    imb_rows.append({
        "Model": name,
        "Accuracy_Ort": np.mean(accs), "Accuracy_Std": np.std(accs, ddof=1),
        "F1_Macro_Ort": np.mean(f1m), "F1_Macro_Std": np.std(f1m, ddof=1),
        "Recall_Orta_Ort": np.mean(rec_mod), "Recall_Agir_Ort": np.mean(rec_sev),
        "MCC_Ort": np.mean(mccs), "QWK_Ort": np.mean(qwks),
        "AUPR_Macro_Ort": np.mean(auprs),
    })
df_imb = pd.DataFrame(imb_rows).set_index("Model")
df_imb.round(4).to_csv(OUT_TAB / "dengesizlik_deneyi.csv", encoding="utf-8-sig")

# SMOTE Sizinti Deneyi
prep_all = make_preprocessor(True)
X_imb_enc = prep_all.fit_transform(X_imb)
X_res, y_res = SMOTE(random_state=RANDOM_STATE).fit_resample(X_imb_enc, y_imb)
y_res_arr = np.asarray(y_res)
n_orig = len(y_imb)
is_orig = np.arange(len(y_res_arr)) < n_orig

leak_f1m, leak_rec_sev, leak_mcc = [], [], []
for tr_idx, te_idx in cv.split(X_res, y_res_arr):
    rf_leak = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=2).fit(
        X_res[tr_idx], y_res_arr[tr_idx]
    )
    te_real = te_idx[is_orig[te_idx]]
    pred_l = rf_leak.predict(X_res[te_real])
    y_te_real = y_res_arr[te_real]
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

# -----------------------------------------------------------------------------
# 7. [ADIM 4/4] SAMPIYON MODEL (CATBOOST) 10-KAT EGITIM FOLD OZNITELIK ONEMI
# -----------------------------------------------------------------------------
print("\n[ADIM 4/4] CatBoost 10-Kat Egitim Fold Oznitelik Onemi ve Grafikler Uretiliyor...")
df_cb_imp_folds = pd.DataFrame(catboost_fold_importances)
cb_imp_mean = df_cb_imp_folds.mean(axis=0)
cb_imp_std = df_cb_imp_folds.std(axis=0, ddof=1)

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
        "Onem_Ort": float(cb_imp_mean[k]),
        "Onem_Std": float(cb_imp_std[k]),
    }
    for k in cb_imp_mean.index
]).sort_values("Onem_Ort", ascending=False).reset_index(drop=True)
df_imp.round(4).to_csv(OUT_TAB / "ozellik_onem_tablosu.csv", index=False, encoding="utf-8-sig")
print("CatBoost En Etkili Ilk 8 Oznitelik (10 Egitim Fold Ort +/- Std):")
print(df_imp.head(8)[["Ozellik", "Onem_Ort", "Onem_Std"]].round(2).to_string(index=False))

# -----------------------------------------------------------------------------
# 8. GRAFIKLER
# -----------------------------------------------------------------------------

# Grafik 2: Model Karsilastirma (2x2 Errorbar: Macro Recall, Macro F1, MCC, QWK)
fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2), sharey=True)
ypos = np.arange(len(ordered_all))
for ax, (col, title) in zip(
    axes.ravel(),
    [
        ("Recall_M", "Macro Recall / Dengeli Doğruluk (ort ± std)"),
        ("F1_M", "Macro F1-Skoru (ort ± std)"),
        ("MCC", "Matthews Korelasyon Katsayısı — MCC (ort ± std)"),
        ("QWK", "Quadratic Weighted Kappa — Sıralı Uyum (ort ± std)"),
    ],
):
    mu = summary_mean.loc[ordered_all, col].to_numpy()
    sd = summary_std.loc[ordered_all, col].to_numpy()
    ax.errorbar(mu, ypos, xerr=sd, fmt="o", color=PALETTE[0], ms=6, elinewidth=1.2, capsize=3)
    ax.set_yticks(ypos, ordered_all)
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
axes[0, 0].invert_yaxis()
fig.suptitle("10-Kat Stratified CV: 9 Model ve Önsel Dummy Referans Karşılaştırması (100.000 Satır)", fontweight="bold")
plt.tight_layout()
save_fig(fig, OUT_FIG / "grafik_2_model_karsilastirma.png", dpi=200)

# Grafik 3: 2x2 ROC ve Precision-Recall Egrileri (Hem AGIR %4,07 hem ORTA %8,30!)
y_bin_all = label_binarize(y, classes=[0, 1, 2, 3])
fig, axes = plt.subplots(2, 2, figsize=(11.8, 9.0))
for r_idx, (cls_id, cls_tr) in enumerate([(3, "Ağır Risk (Severe, %4,07)"), (2, "Orta Risk (Moderate, %8,30)")]):
    for idx, name in enumerate(real_models_sorted):
        s = oof_scores[name]
        fpr, tpr, _ = roc_curve(y_bin_all[:, cls_id], s[:, cls_id])
        auc_c = roc_auc_score(y_bin_all[:, cls_id], s[:, cls_id])
        auc_str = f"{auc_c:.3f}".replace(".", ",")
        axes[r_idx, 0].plot(fpr, tpr, color=PALETTE[idx % len(PALETTE)], label=f"{name} (AUC={auc_str})")

        prec_c, rec_c, _ = precision_recall_curve(y_bin_all[:, cls_id], s[:, cls_id])
        ap_c = average_precision_score(y_bin_all[:, cls_id], s[:, cls_id])
        ap_str = f"{ap_c:.3f}".replace(".", ",")
        axes[r_idx, 1].plot(rec_c, prec_c, color=PALETTE[idx % len(PALETTE)], label=f"{name} (AP={ap_str})")

    axes[r_idx, 0].plot([0, 1], [0, 1], color=RULE, linestyle="--", lw=1, label="Rastgele (0,500)")
    axes[r_idx, 0].set(xlabel="Yanlış Pozitif Oranı (FPR)", ylabel="Doğru Pozitif Oranı (Recall)",
                       title=f"ROC Eğrileri — {cls_tr}")
    axes[r_idx, 0].legend(loc="lower right", fontsize=7.2)

    prev_c = float((y == cls_id).mean())
    prev_str = f"{prev_c:.3f}".replace(".", ",")
    axes[r_idx, 1].axhline(prev_c, color=RULE, linestyle="--", lw=1, label=f"Prevalans ({prev_str})")
    axes[r_idx, 1].set(xlabel="Duyarlılık (Recall)", ylabel="Kesinlik (Precision)",
                       title=f"Precision–Recall Eğrileri — {cls_tr}")
    axes[r_idx, 1].legend(loc="lower left", fontsize=7.2)

plt.tight_layout()
save_fig(fig, OUT_FIG / "grafik_3_roc_pr_egrileri.png", dpi=200)

# Grafik 4: 3x3 OOF Karmasiklik Matrisleri
short_labels = ["Sağlıklı", "Hafif", "Orta", "Ağır"]
fig, axes = plt.subplots(3, 3, figsize=(15.5, 13.5))
for ax, name in zip(axes.ravel(), real_models_sorted):
    cm = confusion_matrix(y, oof_preds[name], labels=[0, 1, 2, 3])
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax,
        xticklabels=short_labels, yticklabels=short_labels, annot_kws={"size": 9}
    )
    mcc_s = f"{summary_mean.loc[name, 'MCC']:.3f}".replace(".", ",")
    qwk_s = f"{summary_mean.loc[name, 'QWK']:.3f}".replace(".", ",")
    ax.set_title(f"{name} (MCC={mcc_s} | QWK={qwk_s})", fontweight="bold")
    ax.set_xlabel("Tahmin Edilen Sınıf")
    ax.set_ylabel("Gerçek Sınıf")
fig.suptitle("10-Kat Çapraz Doğrulama Birleşik (Out-of-Fold) Karmaşıklık Matrisleri (100.000 Örnek)", fontsize=13, fontweight="bold", y=0.995)
plt.tight_layout()
save_fig(fig, OUT_FIG / "grafik_4_confusion_matrices.png", dpi=180)

# Grafik 5: CatBoost Oznitelik Onem Duzeyleri (10 Egitim Fold Ort +/- Std)
top15 = df_imp.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(9.0, 5.8))
colors_imp = ["#eb6834" if "Türetilmiş" in x else "#2a78d6" for x in top15["Ozellik"]]
bars = ax.barh(
    top15["Ozellik"], top15["Onem_Ort"], xerr=top15["Onem_Std"],
    color=colors_imp, capsize=2.5, error_kw={"elinewidth": 1.0}
)
for bar, val, sd in zip(bars, top15["Onem_Ort"], top15["Onem_Std"]):
    ax.text(val + sd + 0.30, bar.get_y() + bar.get_height() / 2, f"%{val:.2f}".replace(".", ","), va="center", fontsize=8.5)
ax.set_xlabel("CatBoost Göreli Katkı Payı (%) — 10 Eğitim Katlaması Ort. ± Std")
ax.set_title("Şampiyon Model (CatBoost) Kararlarına En Yüksek Katkıyı Sağlayan 15 Öznitelik")
ax.set_xlim(0, (top15["Onem_Ort"] + top15["Onem_Std"]).max() * 1.18)
ax.grid(axis="y", visible=False)
plt.tight_layout()
save_fig(fig, OUT_FIG / "grafik_5_ozellik_onemi.png", dpi=200)

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
axes[1].legend(loc="center right", fontsize=8)
plt.tight_layout()
save_fig(fig, OUT_FIG / "grafik_6_derinlik_ve_ogrenme.png", dpi=200)

# Grafik 7: Sinif Dengesizligi Deneyi
fig, ax = plt.subplots(figsize=(9.0, 4.6))
shown_imb = ["Accuracy_Ort", "F1_Macro_Ort", "Recall_Agir_Ort", "MCC_Ort", "QWK_Ort"]
labels_imb = ["Accuracy", "Macro F1", "Ağır Sınıf Recall", "MCC", "QWK"]
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
save_fig(fig, OUT_FIG / "grafik_7_dengesizlik_deneyi.png", dpi=200)

# Grafik 8: Verimlilik (Hiz vs MCC)
fig, ax = plt.subplots(figsize=(8.5, 4.8))
for idx, m in enumerate(real_models_sorted):
    t_s = summary_mean.loc[m, "Sure_sn"]
    mcc_v = summary_mean.loc[m, "MCC"]
    ax.scatter(t_s, mcc_v, color=PALETTE[idx % len(PALETTE)], s=95, edgecolors="black", zorder=4)
    lbl = f"{m}*" if m == "RBF SVM" else m
    ax.annotate(lbl, (t_s, mcc_v), textcoords="offset points", xytext=(7, 4), fontsize=8.5, fontweight="bold")
ax.set(xlabel="Toplam 10-Kat CV Süresi (Saniye) — *RBF SVM 25K alt örneklemle eğitilmiştir",
       ylabel="10-Kat Ortalama MCC",
       title="Model Verimliliği: Hesaplama Süresi vs. MCC Performansı")
plt.tight_layout()
save_fig(fig, OUT_FIG / "grafik_8_hiz_vs_basari.png", dpi=200)

# JSON Kaydet (Tek Gercek Kaynagi)
RESULTS["best_model"] = best_model
RESULTS["model_order"] = ordered_all
RESULTS["summary_mean"] = summary_mean.round(4).astype(object).where(pd.notna(summary_mean), None).to_dict(orient="index")
RESULTS["summary_std"] = summary_std.round(4).astype(object).where(pd.notna(summary_std), None).to_dict(orient="index")
RESULTS["ppv_prevalans"] = df_ppv.round(4).to_dict(orient="records")
RESULTS["smote_leak"] = df_smote_leak.round(4).to_dict(orient="index")

with open(OUT_TAB / "sonuclar.json", "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 76)
print("TUM GUNCEL DENEYLER VE GRAFIKLER BASARIYLA TAMAMLANDI!")
print(f"Sampiyon Model: {best_model} | MCC={summary_mean.loc[best_model, 'MCC']:.4f} | QWK={summary_mean.loc[best_model, 'QWK']:.4f}")
print("=" * 76)
