# =============================================================================
# VERI SETI ILK INCELEME GRAFIKLERI (EDA) - TURKCE GRAFIKLER
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs('grafikler', exist_ok=True)
df = pd.read_csv('sleep_health_dataset.csv')

# Turkce Kolon Isimleri Sozlugu (Korelasyon Haritasi Icin)
turkce_kolonlar = {
    'age': 'Yaş (age)',
    'bmi': 'Vücut Kitle İndeksi (bmi)',
    'sleep_duration_hrs': 'Uyku Süresi - Saat (sleep_duration)',
    'sleep_quality_score': 'Uyku Kalite Puanı (sleep_quality)',
    'rem_percentage': 'REM Uykusu Yüzdesi % (rem_perc)',
    'deep_sleep_percentage': 'Derin Uyku Yüzdesi % (deep_sleep)',
    'sleep_latency_mins': 'Uykuya Dalma Süresi - Dk (latency)',
    'wake_episodes_per_night': 'Gece Uyanma Sayısı (wakeups)',
    'caffeine_mg_before_bed': 'Uykudan Önce Kafein - mg (caffeine)',
    'alcohol_units_before_bed': 'Uykudan Önce Alkol - Birim (alcohol)',
    'screen_time_before_bed_mins': 'Yatmadan Önce Ekran - Dk (screen_time)',
    'exercise_day': 'Egzersiz Yapıldı mı (exercise)',
    'steps_that_day': 'Günlük Adım Sayısı (steps)',
    'nap_duration_mins': 'Gündüz Şekerleme - Dk (nap)',
    'stress_score': 'Stres Skoru 1-10 (stress)',
    'work_hours_that_day': 'Günlük Çalışma Saati (work_hours)',
    'heart_rate_resting_bpm': 'Dinlenme Kalp Nabzı - BPM (heart_rate)',
    'sleep_aid_used': 'Uyku İlacı Kullanımı (sleep_aid)',
    'shift_work': 'Vardiyalı Çalışma (shift_work)',
    'room_temperature_celsius': 'Oda Sıcaklığı - °C (temp)',
    'weekend_sleep_diff_hrs': 'Hafta Sonu Uyku Farkı - Saat (weekend_diff)'
}

# -----------------------------------------------------------------------------
# GRAFIK 1: HEDEF DEGISKEN DAGILIMI (Turkce)
# -----------------------------------------------------------------------------
plt.figure(figsize=(9, 6))
hedef_sirasi = ['Healthy', 'Mild', 'Moderate', 'Severe']
turkce_hedef_etiketleri = {
    'Healthy': 'Sağlıklı\n(Healthy)',
    'Mild': 'Hafif Risk\n(Mild)',
    'Moderate': 'Orta Risk\n(Moderate)',
    'Severe': 'Ağır Risk\n(Severe)'
}

counts = df['sleep_disorder_risk'].value_counts()[hedef_sirasi]
renkler = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']

bars = plt.bar([turkce_hedef_etiketleri[k] for k in hedef_sirasi], counts, color=renkler, edgecolor='black', alpha=0.85)

for bar in bars:
    yval = bar.get_height()
    yuzde = (yval / len(df)) * 100
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1000, f"{yval:,}\n(%{yuzde:.1f})", ha='center', va='bottom', fontsize=11, weight='bold')

plt.title("Uyku Bozukluğu Riski Sınıf Dağılımı (Hedef Değişken)", fontsize=14, weight='bold', pad=15)
plt.xlabel("Hastalık Risk Seviyesi", fontsize=12)
plt.ylabel("Hasta / Kişi Sayısı", fontsize=12)
plt.ylim(0, max(counts) * 1.18)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('grafikler/grafik_1_hedef_dagilimi.png', dpi=150)
plt.close()
print("Grafik 1 (Turkce Hedef Dagilimi) 'grafikler/grafik_1_hedef_dagilimi.png' olarak olusturuldu.")

# -----------------------------------------------------------------------------
# GRAFIK 2: KORELASYON ISI HARITASI (Turkce)
# -----------------------------------------------------------------------------
# Sayisal sutunlari al ve Turkce isimleriyle yeniden adlandir
num_cols = list(turkce_kolonlar.keys())
df_corr = df[num_cols].rename(columns=turkce_kolonlar)

plt.figure(figsize=(18, 15))
corr_matrix = df_corr.corr()

# Ust ucgeni maskelemek daha temiz ve profesyonel gosterir
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

sns.heatmap(
    corr_matrix, 
    mask=mask,
    annot=True, 
    fmt='.2f', 
    cmap='coolwarm', 
    vmin=-1, vmax=1, 
    linewidths=0.5,
    cbar_kws={'label': 'Korelasyon Katsayısı (-1 = Ters Orantı, +1 = Doğru Orantı)'}
)

plt.title("Sağlık ve Yaşam Tarzı Özellikleri Arasındaki Korelasyon Matrisi (İlişki Haritası)", fontsize=16, weight='bold', pad=20)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(fontsize=10)
plt.tight_layout()
out_path = os.path.join('grafikler', 'grafik_2_korelasyon_matrisi.png')
if os.path.exists(out_path):
    os.remove(out_path)
plt.savefig(out_path, dpi=150)
plt.close()
print("Grafik 2 (Turkce Korelasyon Matrisi) kaydedildi.")
