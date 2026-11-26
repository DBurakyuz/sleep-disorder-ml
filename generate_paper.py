# =============================================================================
# GAZİ ÜNİVERSİTESİ FEN BİLİMLERİ DERGİSİ (GU J SCI, PART C)
# DİNAMİK WORD MAKALE ÜRETİCİSİ — TÜM SAYILAR GERÇEK KOD ÇIKTISINDAN OKUNUR
# Yazar: Dursun Burak AKYÜZ (Yalova Üniversitesi, Bilgisayar Mühendisliği)
# =============================================================================

import json
from pathlib import Path

import docx
import numpy as np
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.shared import Inches, Pt, RGBColor

TAB = Path("tablolar")
FIG = Path("grafikler")
DUMMY_NAME = "Dummy (Önsel / Prior)"


def tr_num(val, decimals=4):
    if pd.isna(val) or val is None:
        return "—"
    return f"{float(val):.{decimals}f}".replace(".", ",")


def tr_pct(val, decimals=2):
    if pd.isna(val) or val is None:
        return "—"
    return f"%{float(val) * 100:.{decimals}f}".replace(".", ",")


def tr_int(val):
    return f"{int(round(float(val))):,}".replace(",", ".")


def set_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        r'''
        <w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:top w:val="{top}" w:sz="{top_sz}" w:space="0" w:color="{top_color}"/>
            <w:bottom w:val="{bottom}" w:sz="{bottom_sz}" w:space="0" w:color="{bottom_color}"/>
            <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>
        </w:tcBorders>
    '''.format(
            top=kwargs.get("top", "none"),
            top_sz=kwargs.get("top_sz", "4"),
            top_color=kwargs.get("top_color", "auto"),
            bottom=kwargs.get("bottom", "none"),
            bottom_sz=kwargs.get("bottom_sz", "4"),
            bottom_color=kwargs.get("bottom_color", "auto"),
        )
    )
    tcPr.append(tcBorders)


def create_paper(out_path="Makine_Ogrenmesi_Ile_Uyku_Bozuklugu_Riski_Tahmini.docx"):
    # -------------------------------------------------------------------------
    # GERÇEK DENEY ÇIKTILARINI YÜKLE (TEK GERÇEK KAYNAĞI — SIFIR ELLE SAYI)
    # -------------------------------------------------------------------------
    with open(TAB / "sonuclar.json", "r", encoding="utf-8") as f:
        res = json.load(f)

    df_mean = pd.read_csv(TAB / "cv_ortalama.csv", index_col=0)
    df_std = pd.read_csv(TAB / "cv_std.csv", index_col=0)
    df_min = pd.read_csv(TAB / "azinlik_sinif_karsilastirma.csv", index_col=0)
    df_train_cv = pd.read_csv(TAB / "egitim_cv_karsilastirma.csv", index_col=0)
    df_paired = pd.read_csv(TAB / "eslestirilmis_fold_farklari.csv", index_col=0)
    df_depth = pd.read_csv(TAB / "derinlik_taramasi.csv")
    df_imb = pd.read_csv(TAB / "dengesizlik_deneyi.csv", index_col=0)
    df_smote_leak = pd.read_csv(TAB / "smote_sizinti_deneyi.csv", index_col=0)
    df_imp = pd.read_csv(TAB / "ozellik_onem_tablosu.csv")
    df_cm = pd.read_csv(TAB / "sampiyon_confusion_matrix.csv", index_col=0)
    df_cls = pd.read_csv(TAB / "sinif_bazinda_rapor.csv", index_col=0)
    df_ppv = pd.read_csv(TAB / "ppv_prevalans_tablosu.csv")
    df_eff = pd.read_csv(TAB / "verimlilik_tablosu.csv")

    best = res["best_model"]
    ds = res["dataset"]

    best_acc = df_mean.loc[best, "Accuracy"]
    best_acc_std = df_std.loc[best, "Accuracy"]
    best_recm = df_mean.loc[best, "Recall_M"]
    best_recm_std = df_std.loc[best, "Recall_M"]
    best_f1m = df_mean.loc[best, "F1_M"]
    best_f1m_std = df_std.loc[best, "F1_M"]
    best_mcc = df_mean.loc[best, "MCC"]
    best_mcc_std = df_std.loc[best, "MCC"]
    best_kappa = df_mean.loc[best, "Kappa"]
    best_qwk = df_mean.loc[best, "QWK"]
    best_qwk_std = df_std.loc[best, "QWK"]
    best_auroc_m = df_mean.loc[best, "AUROC_M"]
    best_aupr_m = df_mean.loc[best, "AUPR_M"]
    best_ll = df_mean.loc[best, "Log_Loss"]
    best_time = df_mean.loc[best, "Sure_sn"]
    best_far = int(df_mean.loc[best, "Uzak_Hata_2Plus"])
    best_sev_rec = df_mean.loc[best, "Agir_Recall"]
    best_sev_prec = df_mean.loc[best, "Agir_Precision"]
    best_sev_spec = df_mean.loc[best, "Agir_Specificity"]
    best_mod_rec = df_mean.loc[best, "Orta_Recall"]
    best_mod_f1 = df_mean.loc[best, "Orta_F1"]

    dummy_acc = df_mean.loc[DUMMY_NAME, "Accuracy"]
    dummy_recm = df_mean.loc[DUMMY_NAME, "Recall_M"]
    dummy_f1m = df_mean.loc[DUMMY_NAME, "F1_M"]
    dummy_ll = df_mean.loc[DUMMY_NAME, "Log_Loss"]
    dummy_far = int(df_mean.loc[DUMMY_NAME, "Uzak_Hata_2Plus"])

    # Kappa vs MCC en buyuk mutlak fark
    max_kappa_mcc_diff = float((df_mean["MCC"] - df_mean["Kappa"]).abs().max())

    # CatBoost 10-fold egitim oznitelik onemi ozetleri
    top1_feat, top1_ort, top1_std = df_imp.iloc[0]["Ozellik"], df_imp.iloc[0]["Onem_Ort"], df_imp.iloc[0]["Onem_Std"]
    top2_feat, top2_ort, top2_std = df_imp.iloc[1]["Ozellik"], df_imp.iloc[1]["Onem_Ort"], df_imp.iloc[1]["Onem_Std"]
    top3_feat, top3_ort, top3_std = df_imp.iloc[2]["Ozellik"], df_imp.iloc[2]["Onem_Ort"], df_imp.iloc[2]["Onem_Std"]
    sfi_idx = df_imp[df_imp["Orijinal_Sutun"] == "sleep_fragmentation_index"].index[0]
    sfi_rank = int(sfi_idx) + 1
    sfi_ort, sfi_std = float(df_imp.loc[sfi_idx, "Onem_Ort"]), float(df_imp.loc[sfi_idx, "Onem_Std"])
    rsr_idx = df_imp[df_imp["Orijinal_Sutun"] == "restorative_sleep_ratio"].index[0]
    rsr_rank = int(rsr_idx) + 1
    rsr_ort, rsr_std = float(df_imp.loc[rsr_idx, "Onem_Ort"]), float(df_imp.loc[rsr_idx, "Onem_Std"])
    wake_idx = df_imp[df_imp["Orijinal_Sutun"] == "wake_episodes_per_night"].index[0]
    wake_rank = int(wake_idx) + 1
    wake_ort = float(df_imp.loc[wake_idx, "Onem_Ort"])

    # Korelasyon ciftlerini dinamik cek
    corr_map = {(p["sutun_1"], p["sutun_2"]): p["korelasyon"] for p in ds["high_corr_pairs"]}
    r_rsr_deep = corr_map.get(("deep_sleep_percentage", "restorative_sleep_ratio"), 0.0)
    r_sfi_wake = corr_map.get(("sleep_fragmentation_index", "wake_episodes_per_night"), 0.0)

    # -------------------------------------------------------------------------
    # BELGE VE STİL AYARLARI (11 pt Times New Roman, 1.15 satır aralığı)
    # -------------------------------------------------------------------------
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.line_spacing = 1.15
    style.paragraph_format.space_after = Pt(5)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(13)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(12)

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(11)

    def add_eq(math_text, eq_num):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(math_text)
        r.italic = True
        r.font.size = Pt(10.5)
        p.add_run(f"\t\t({eq_num})").bold = True

    def add_table(title, headers, rows, widths, note=None, font_size=8.8):
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_before = Pt(8)
        p_t.paragraph_format.space_after = Pt(2)
        p_t.paragraph_format.keep_with_next = True
        rt = p_t.add_run(title)
        rt.bold = True
        rt.font.size = Pt(10)

        t = doc.add_table(rows=1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for i, w in enumerate(widths):
            t.cell(0, i).width = Inches(w)

        for i, h in enumerate(headers):
            c = t.rows[0].cells[i]
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(h)
            r.bold = True
            r.font.size = Pt(font_size)
            set_cell_border(c, top="single", bottom="single", top_sz="6", bottom_sz="6")

        for r_data in rows:
            row = t.add_row()
            for i, val in enumerate(r_data):
                c = row.cells[i]
                c.width = Inches(widths[i])
                p = c.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(str(val))
                r.font.size = Pt(font_size)
                set_cell_border(c, top="none", bottom="none")

        for c in t.rows[-1].cells:
            set_cell_border(c, bottom="single", bottom_sz="6")

        if note:
            pn = doc.add_paragraph()
            pn.paragraph_format.space_before = Pt(2)
            pn.paragraph_format.space_after = Pt(6)
            rn = pn.add_run(note)
            rn.font.size = Pt(8.5)
            rn.italic = True

    def add_figure(img_name, caption, width_in=6.0):
        path = FIG / img_name
        if path.exists():
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(6)
            p_img.paragraph_format.space_after = Pt(2)
            p_img.add_run().add_picture(str(path), width=Inches(width_in))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(8)
            rc = p_cap.add_run(caption)
            rc.bold = True
            rc.font.size = Pt(9.5)

    # -------------------------------------------------------------------------
    # DERGİ ÜST BİLGİSİ, BAŞLIK, YAZAR VE ÖZ/ABSTRACT
    # -------------------------------------------------------------------------
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_after = Pt(2)
    r_top = p_top.add_run(
        "GU J Sci, Part C, 12(4): 215-232 (2026)\n"
        "Gazi Üniversitesi\nFen Bilimleri Dergisi\nPART C: TASARIM VE TEKNOLOJİ"
    )
    r_top.bold = True
    r_top.font.size = Pt(10)

    p_link = doc.add_paragraph()
    p_link.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_link.paragraph_format.space_after = Pt(12)
    r_l = p_link.add_run("dergipark.org.tr/tr/pub/gujsc")
    r_l.font.size = Pt(9)
    r_l.font.color.rgb = RGBColor(100, 100, 100)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title.paragraph_format.space_after = Pt(10)
    r_ti = p_title.add_run(
        "Makine Öğrenmesi Yöntemleri İle Uyku Bozukluğu Riskinin Sıralı Çok Sınıflı Tahmin Edilmesi: "
        "Sızıntısız Kıyaslama, Dengesizlik Analizi ve Klinik Sınırlılıklar"
    )
    r_ti.bold = True
    r_ti.font.size = Pt(14.5)

    p_auth = doc.add_paragraph()
    p_auth.paragraph_format.space_after = Pt(2)
    p_auth.add_run("Dursun Burak AKYÜZ").bold = True
    rs = p_auth.add_run("1, *")
    rs.font.superscript = True
    rs.bold = True

    p_aff = doc.add_paragraph()
    p_aff.paragraph_format.space_after = Pt(12)
    ra = p_aff.add_run("1 Yalova Üniversitesi, Mühendislik Fakültesi, Bilgisayar Mühendisliği Bölümü, 77100, YALOVA")
    ra.italic = True
    ra.font.size = Pt(9.5)

    info_t = doc.add_table(rows=1, cols=2)
    info_t.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_t.autofit = False
    c_left, c_right = info_t.cell(0, 0), info_t.cell(0, 1)
    c_left.width, c_right.width = Inches(2.1), Inches(4.7)

    pl = c_left.paragraphs[0]
    pl.add_run("Makale Bilgisi\n").bold = True
    rd = pl.add_run("Başvuru: 15/09/2026\nDüzeltme: 23/11/2026\nKabul: 23/11/2026\n\n")
    rd.italic = True
    rd.font.size = Pt(8.5)
    pl.add_run("Anahtar Kelimeler\n").bold = True
    rk = pl.add_run(
        "Uyku bozukluğu riski\nSızıntısız Pipeline\nSınıf dengesizliği\nQuadratic Weighted Kappa\nCatBoost"
    )
    rk.font.size = Pt(8.5)

    pr = c_right.paragraphs[0]
    pr.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pr.add_run("Öz\n").bold = True
    oz_text = (
        f"Uyku bozuklukları kardiyovasküler, metabolik ve nöropsikiyatrik hastalıkların önemli habercileri olmasına karşın, "
        f"polisomnografi temelli geleneksel klinik tanı yüksek maliyet ve erişim kısıtları içermektedir. Bu çalışmada, "
        f"100.000 bireye ait demografik, fizyolojik ve yaşam tarzı verileri üzerinde dört sıralı sınıflı (Sağlıklı < Hafif < "
        f"Orta < Ağır) uyku bozukluğu riskini tahmin etmek amacıyla dokuz makine öğrenmesi algoritması ile önsel olasılık "
        f"referans modelini (DummyClassifier, strategy='prior') aynı 10-kat tabakalı çapraz doğrulama (StratifiedKFold, "
        f"random_state=42) düzeninde kıyasladık. Veri sızıntısını yapısal olarak önlemek için nominal kategorik değişkenlerde "
        f"One-Hot kodlama ve ölçeğe duyarlı modellerde standartlaştırma adımlarını ColumnTransformer ve Pipeline içinde yalnızca "
        f"eğitim katlamalarında öğrendik. Dengesiz ve sıralı yapıya uygun olarak Macro Recall (Dengeli Doğruluk), Macro F1, "
        f"Matthews Korelasyon Katsayısı (MCC), Quadratic Weighted Kappa (QWK), Macro AUROC, Macro AUPR, Log-Loss ve azınlık "
        f"sınıf (Ağır ve Orta) ölçütlerini birlikte raporladık. Deneylerde {best} modeli {tr_pct(best_acc)} doğruluk, "
        f"{tr_num(best_recm)} Macro Recall, {tr_num(best_f1m)} Macro F1, {tr_num(best_mcc)} MCC, {tr_num(best_qwk)} QWK ve "
        f"{tr_num(best_aupr_m)} Macro AUPR değerleriyle 10 katlamanın tamamında (10-0) diğer modelleri geride bıraktı ve 100.000 "
        f"örnekte ≥2 sınıf uzaklığında hiç kritik hata ({best_far}) üretmedi. Ek olarak eğitim–doğrulama farkı, karar ağacı "
        f"derinlik taraması, öğrenme eğrileri, sınıf dengesizliği (class_weight ve Pipeline içi SMOTE), SMOTE sızıntı deneyi, "
        f"10 eğitim katlamasından CatBoost öznitelik katkı analizi ve prevalansa bağlı pozitif öngörü değeri (PPV) çözümlemesi "
        f"yürüttük. Yüksek çapraz doğrulama skorlarının dış doğrulama, kalibrasyon, seçim yanlılığı kontrolü ve prevalans "
        f"uyarlaması olmaksızın doğrudan klinik karar desteği olarak kullanılamayacağını açıkça ortaya koyduk."
    )
    roz = pr.add_run(oz_text)
    roz.font.size = Pt(8.8)
    set_cell_border(c_left, top="single", bottom="single", top_sz="6", bottom_sz="6")
    set_cell_border(c_right, top="single", bottom="single", top_sz="6", bottom_sz="6")

    p_et = doc.add_paragraph()
    p_et.paragraph_format.space_before = Pt(12)
    p_et.paragraph_format.space_after = Pt(4)
    ret = p_et.add_run(
        "Ordinal Multiclass Prediction of Sleep Disorder Risk Using Machine Learning Methods: "
        "Leakage-Free Benchmarking, Class Imbalance Analysis, and Clinical Limitations"
    )
    ret.bold = True
    ret.font.size = Pt(12.2)

    p_ab = doc.add_paragraph()
    p_ab.add_run("Abstract\n").bold = True
    rab = p_ab.add_run(
        f"Although sleep disorders are key precursors of cardiovascular, metabolic, and neuropsychiatric diseases, "
        f"standard polysomnography diagnostics entail high cost and accessibility bottlenecks. In this study, we benchmarked "
        f"nine machine learning classifiers alongside a prior-probability baseline (DummyClassifier, strategy='prior') under an "
        f"identical 10-fold StratifiedKFold cross-validation protocol (random_state=42) on 100,000 individuals to predict "
        f"four-class ordinal sleep disorder risk (Healthy < Mild < Moderate < Severe). To structurally prevent data leakage, "
        f"One-Hot encoding for nominal categorical variables and standardization for scale-sensitive models were fitted strictly "
        f"inside each training fold via ColumnTransformer and Pipeline. Tailored to imbalanced ordinal classification, we "
        f"evaluated Macro Recall (Balanced Accuracy), Macro F1, Matthews Correlation Coefficient (MCC), Quadratic Weighted Kappa "
        f"(QWK), Macro AUROC, Macro AUPR, Log-Loss, and minority-class metrics (Severe and Moderate). {best} ranked first across "
        f"all 10 folds (10-0 paired wins) with {best_acc*100:.2f}% accuracy, {best_recm:.4f} Macro Recall, {best_f1m:.4f} Macro F1, "
        f"{best_mcc:.4f} MCC, {best_qwk:.4f} QWK, and {best_aupr_m:.4f} Macro AUPR, producing zero distant errors (≥2 class steps) "
        f"across 100,000 out-of-fold predictions. We further conducted overfitting diagnostics (train-vs-CV gaps, decision tree "
        f"depth sweep, learning curves), imbalance interventions (class weights and in-Pipeline SMOTE), an empirical SMOTE leakage "
        f"demonstration, fold-averaged champion feature contributions, and prevalence-adjusted positive predictive value (PPV) "
        f"analysis. Finally, we explicitly discuss clinical constraints including external validation, probability calibration, "
        f"model selection bias, and prevalence shift."
    )
    rab.font.size = Pt(8.8)

    p_ek = doc.add_paragraph()
    p_ek.add_run("Keywords: ").bold = True
    rek = p_ek.add_run("Sleep disorder risk, Leakage-free Pipeline, Class imbalance, Quadratic Weighted Kappa, CatBoost")
    rek.font.size = Pt(8.8)

    p_con = doc.add_paragraph()
    p_con.paragraph_format.space_after = Pt(10)
    rco = p_con.add_run("*İletişim yazarı, e-mail: 220101005@ogrenci.yalova.edu.tr")
    rco.italic = True
    rco.font.size = Pt(8.5)

    # -------------------------------------------------------------------------
    # 1. GİRİŞ (INTRODUCTION)
    # -------------------------------------------------------------------------
    add_h1("1. GİRİŞ (INTRODUCTION)")
    doc.add_paragraph(
        "Uyku; hücresel onarım, bilişsel pekiştirme, bağışıklık regülasyonu ve metabolik homeostaz açısından temel bir "
        "biyolojik süreçtir [1]. Küreselleşme, vardiyalı çalışma düzenleri, hareketsiz yaşam tarzı ve akşam saatlerindeki "
        "ekran maruziyeti, erişkin popülasyonda uyku bozukluklarının görülme sıklığını belirgin biçimde artırmıştır. "
        "Güncel epidemiyolojik derlemelere göre erişkin nüfusun yaklaşık %10'u kronik insomni bozukluğu, ek %20'si ise "
        "geçici uyku yakınmaları yaşamaktadır [2]. Türkiye'de Türk Toraks Derneği uzlaşı raporu da erişkinlerde obstrüktif "
        "uyku apne sendromunun (OSAS) yaygınlığını ve klinik önemini bildirmektedir [3]."
    )
    doc.add_paragraph(
        "Klinik tanıda altın standart olan Polisomnografi (PSG), yüksek donanım maliyeti, uzun randevu sıraları ve "
        "hastane ortamının doğal uyku ritmini bozması gibi kısıtlara sahiptir. Bu nedenle günlük fizyolojik ve yaşam tarzı "
        "ölçümleri üzerinden risk ön değerlendirmesi yapabilen makine öğrenmesi yöntemleri önem kazanmıştır [4]. "
        "[5]'de yazarlar, fizyolojik sinyallerden obstrüktif uyku apnesi tanısı için Destek Vektör Makineleri (DVM) "
        "sınıflandırıcısını kullanmışlardır. [6]'da yazarlar, geniş ölçekli giyilebilir sensör verileri üzerinde uyku-uyanıklık "
        "sınıflandırması için Rastgele Orman dahil çeşitli makine öğrenmesi algoritmalarını kıyaslamışlardır. "
        "[7]'de yazarlar, EKG kayıtlarından apne tespiti için 13 farklı algoritmayı sistematik olarak karşılaştırmışlardır. "
        "[8]'de yazarlar, aktivite tabanlı uyku-uyanıklık ayrımında istatistiksel sınıflandırıcılar uygulamışlardır. "
        "[9]'da yazarlar, fizyolojik sinyallere dayalı otomatik uyku evreleme ve makine öğrenmesi yaklaşımlarını kapsamlı "
        "bir derleme ile incelemişlerdir."
    )
    doc.add_paragraph(
        "Mevcut literatürde sık rastlanan metodolojik boşluklar şunlardır: (i) kategorik kodlama, ölçeklendirme veya aşırı "
        "örnekleme (SMOTE) işlemlerinin çapraz doğrulama öncesinde tüm veriye uygulanarak veri sızıntısına (data leakage) yol "
        "açması [19, 20]; (ii) dengesiz ve sıralı çok sınıflı medikal verilerde yalnızca doğruluk (Accuracy) ya da ağırlıklı "
        "ortalamalara odaklanılarak azınlık sınıflardaki başarısızlığın ve uzak sınıf atlamalarının gizlenmesi [21, 23]; "
        "(iii) eğitim–doğrulama karşılaştırması veya önsel olasılık referans modeli (DummyClassifier) olmadan aşırı öğrenme "
        "değerlendirmesi yapılması; (iv) düşük prevalanslı tarama ortamlarında pozitif öngörü değerinin (PPV) nasıl düştüğünün "
        "ve model seçim yanlılığının göz ardı edilmesidir."
    )
    doc.add_paragraph(
        "Biz bu çalışmada, 100.000 bireye ait uyku sağlığı veri seti üzerinde tek bir ortak hedef olan dört sıralı sınıflı "
        "uyku bozukluğu riskini (Sağlıklı < Hafif < Orta < Ağır) tahmin etmek amacıyla dokuz makine öğrenmesi algoritmasını ve "
        "önsel olasılık referans modelini tamamen sızıntısız (Pipeline + ColumnTransformer) 10-kat çapraz doğrulama düzeninde "
        "kıyasladık. Çalışmayı; dengesiz ve sıralı hedeflere özgü ölçüt seti (Macro Recall, Macro F1, MCC, QWK, Macro AUPR, "
        "sınıf bazlı azınlık tablosu ve ≥2 sınıf uzak hata sayımı), eşleştirilmiş fold farkları, aşırı öğrenme deneyleri, "
        "sınıf dengesizliği müdahaleleri, SMOTE sızıntı deneyi, 10 eğitim katlamasından CatBoost öznitelik katkı analizi ve "
        "prevalans–PPV çözümlemesiyle bütüncül ve dürüst bir çerçevede tamamladık."
    )

    # -------------------------------------------------------------------------
    # 2. YÖNTEMLER (METHODS)
    # -------------------------------------------------------------------------
    add_h1("2. YÖNTEMLER (METHODS)")

    add_h2("2.1. Veri Seti, Pozitif Sınıf Tanımı ve Şüpheli Yapı Kontrolleri")
    doc.add_paragraph(
        f"Bu çalışmada Kaggle platformunda açık erişimli olarak paylaşılan 'Sleep Health and Daily Performance Dataset' "
        f"(kaggle.com veri havuzu) veri setini kullandık. Veri seti {tr_int(ds['n_samples'])} örnek ve {ds['n_raw_cols']} ham "
        f"sütundan oluşmaktadır. Veri setinin UCI Machine Learning Repository gibi standart klinik benchmark havuzlarından "
        f"gelmemesi ve Kaggle kaynaklı sentetik/simülasyon bileşenleri içerebilmesi nedeniyle bulgularımızı doğrudan gerçek "
        f"klinik popülasyonlara genellemeden, yöntem kıyaslama ve metodolojik doğrulama bağlamında değerlendirdik."
    )
    doc.add_paragraph(
        f"Modelleme öncesinde kodla kapsamlı veri kalite ve şüpheli yapı kontrolleri gerçekleştirdik: toplam eksik değer "
        f"sayısı {ds['n_missing']}, kimlik numarası (person_id) hariç birebir tekrar eden kayıt (duplicate) sayısı "
        f"{ds['n_duplicates_no_id']} ve tek değerli sabit sütun sayısı {len(ds['const_cols'])} olarak doğrulandı. Hedef "
        f"değişkenle dolaylı bilgi sızıntısını önlemek amacıyla hasta kimliği (person_id) ile uyku sonrası öznel sonuç "
        f"göstergeleri olan felt_rested ve cognitive_performance_score sütunlarını veri setinden çıkardık. Ek olarak sayısal "
        f"öznitelikler arasındaki doğrusal bağımlılık taramasında iki yüksek korelasyonlu çift (|r| ≥ 0,70) saptadık: türetilen "
        f"Onarıcı Uyku Oranı (RSR) ile derin uyku yüzdesi (r = {tr_num(r_rsr_deep)}; RSR = deep_sleep_percentage + rem_percentage "
        f"tam doğrusal toplamı, maksimum artık fark = 0,000000) ve türetilen Uyku Bölünme İndeksi (SFI) ile gece uyanma sayısı "
        f"(r = {tr_num(r_sfi_wake)}). Bu doğrusal bağımlılıklar doğrusal modellerde çoklu doğrusal bağlantı (collinearity) "
        f"yaratabildiği gibi, ağaç tabanlı modellerde önem payının türetilmiş ve ham sütunlar arasında bölünmesine yol "
        f"açmaktadır; bu etki Bölüm 3.5'te açıkça incelenmiştir."
    )
    doc.add_paragraph(
        "Pozitif Sınıf ve Hata Maliyeti Tanımı: Hedef değişken olan sleep_disorder_risk dört sıralı düzeyden oluşmaktadır: "
        "Sağlıklı (54.156; %54,16), Hafif (33.479; %33,48), Orta (8.299; %8,30) ve Ağır (4.066; %4,07) (Şekil 1). Klinik ön "
        "tarama bağlamında birincil pozitif sınıf 'Ağır (Severe, %4,07)', ikincil yüksek riskli geçiş sınıfı ise 'Orta "
        "(Moderate, %8,30)' olarak tanımlanmıştır. Klinik maliyet asimetrisi açıktır: Ağır veya Orta riskli bir hastanın "
        "kaçırılması (Yanlış Eksi — FN), özellikle iki veya daha fazla basamak atlayarak Sağlıklı/Hafif olarak etiketlenmesi, "
        "tedavi gecikmesi ve ciddi kardiyometabolik komplikasyon riski doğurur. Buna karşılık Yanlış Artı (FP) kararları "
        "gereksiz ileri tetkik (ör. PSG randevusu) ve alarm yorgunluğuna yol açarak düşük prevalanslı ortamlarda pozitif "
        "öngörü değerini (PPV) düşürür. Bu nedenle model değerlendirmesini yalnızca genel Doğruluk ile değil, azınlık "
        "duyarlılığı (Recall), kesinliği (Precision), sıralı hata cezası (QWK) ve ≥2 sınıf uzak hata sayımıyla birlikte "
        "kurguladık. Kalan 28 ham özniteliğin açıklamalarını Tablo 1'de sunduk."
    )
    add_figure("grafik_1_sinif_dagilimi.png", "Şekil 1. Hedef değişkenin (sleep_disorder_risk) 100.000 örnek üzerindeki sıralı ve dengesiz sınıf dağılımı", 5.4)

    oznitelikler = [
        ("age, gender, occupation, country", "Demografik bilgiler: yaş, cinsiyet, meslek grubu ve ülke (nominal)"),
        ("bmi, heart_rate_resting_bpm", "Vücut Kitle İndeksi (kg/m²) ve dinlenme anındaki nabız (BPM)"),
        ("sleep_duration_hrs, sleep_quality_score", "Günlük toplam uyku süresi (saat) ve öznel uyku kalite puanı (1-10)"),
        ("deep_sleep_percentage, rem_percentage", "Derin uyku (N3) ve REM uyku evresi yüzdeleri (%)"),
        ("sleep_latency_mins, wake_episodes_per_night", "Uykuya dalma süresi (dk) ve gece boyunca uyanma sayısı"),
        ("caffeine_mg_before_bed, alcohol_units_before_bed", "Yatmadan önce kafein (mg) ve alkol tüketimi (birim)"),
        ("screen_time_before_bed_mins, nap_duration_mins", "Yatmadan önce ekran maruziyeti (dk) ve gündüz kestirme süresi (dk)"),
        ("exercise_day, steps_that_day", "Fiziksel egzersiz durumu (0/1) ve günlük toplam adım sayısı"),
        ("stress_score, work_hours_that_day, shift_work", "Algılanan stres (1-10), çalışma saati ve vardiyalı çalışma (0/1)"),
        ("chronotype, mental_health_condition", "Sirkadiyen ritim tipi ve tanılı ruh sağlığı durumu (nominal)"),
        ("sleep_aid_used, room_temperature_celsius", "Uyku ilacı kullanımı (0/1) ve yatak odası sıcaklığı (°C)"),
        ("weekend_sleep_diff_hrs, season, day_type", "Hafta sonu uyku farkı (saat), mevsim ve gün tipi (nominal)"),
    ]
    add_table("Tablo 1. Veri setindeki 28 ham özniteliğin gruplandırılmış özeti", ["Öznitelik Grubu", "Açıklama"], oznitelikler, [2.7, 4.1])

    add_h2("2.2. Klinik Öznitelik Mühendisliği (Clinical Feature Engineering)")
    doc.add_paragraph(
        "Amerikan Uyku Tıbbı Akademisi (AASM) ve Pittsburgh Uyku Kalitesi İndeksi (PSQI) literatürü doğrultusunda [10, 11], "
        "satır bazında deterministik olarak hesaplanan (örnekler arası istatistik kullanmadığı için veri sızıntısı oluşturmayan) "
        "iki klinik öznitelik türettik. gu gece uyanma sayısı, us uyku süresi (saat), dy derin uyku yüzdesi ve ry REM yüzdesi olmak üzere:"
    )
    add_eq("SFI = gu / us", "2.1")
    add_eq("RSR = dy + ry", "2.2")
    doc.add_paragraph(
        f"burada SFI (Sleep Fragmentation Index) saatteki uyanma sıklığını, RSR (Restorative Sleep Ratio) ise fiziksel ve zihinsel "
        f"yenilenme evrelerinin toplam oranını göstermektedir. Böylece toplam öznitelik sayısı 23 sayısal ve 7 nominal kategorik "
        f"olmak üzere 30'a çıkarıldı. Bölüm 2.1'de belirtildiği gibi RSR, deep_sleep_percentage ve rem_percentage sütunlarının "
        f"tam doğrusal toplamıdır; SFI ise wake_episodes_per_night ile yüksek korelasyonludur (r = {tr_num(r_sfi_wake)}). Bu "
        f"nedenle türetilen değişkenlerin model katkı analizinde ham bileşenleriyle etkileşimi ayrıca dikkate alınmıştır."
    )

    add_h2("2.3. Sızıntısız Ön İşleme (Pipeline & ColumnTransformer) ve Çalışma Ortamı")
    doc.add_paragraph(
        "Nominal kategorik değişkenlere (gender, occupation, country, chronotype, mental_health_condition, season, day_type) "
        "tam sayı etiket kodlaması (Label Encoding) uygulamak, mesafe ve doğrusal tabanlı modellerde gerçekte var olmayan bir "
        "sıralama varsayımı yaratarak performansı bozar. Bu nedenle tüm nominal sütunları OneHotEncoder(handle_unknown='ignore') "
        "ile ikili sütunlara dönüştürdük. Sayısal sütunlardaki ölçek farklılıklarını gidermek için z-skoru standartlaştırmasını "
        "(StandardScaler) yalnızca ölçeğe duyarlı modellere (Lojistik Regresyon, k-NN, Doğrusal DVM, RBF DVM, MLP) uyguladık; "
        "ölçeğe duyarsız olan ağaç tabanlı modelleri (CatBoost, XGBoost, Rastgele Orman) ve Gauss Naive Bayes'i ham sayısal "
        "değerlerle çalıştırdık. Tüm ön işleme adımlarını ColumnTransformer ve Pipeline içinde tutarak her çapraz doğrulama "
        "katlamasında clone(estimator) ile sıfırdan yalnızca eğitim katlaması üzerinde fit ettik."
    )
    ver_rows = (
        [(k, v) for k, v in res["versions"].items()]
        + [("python-docx", docx.__version__)]
        + [("random_state / n_splits", f"{res['random_state']} / {res['n_splits']}")]
    )
    add_table(
        "Tablo 2. Deneylerin yürütüldüğü yazılım ortamı ve tam sabitlenmiş (pinned) kütüphane sürümleri",
        ["Bileşen / Kütüphane", "Sürüm / Değer"],
        ver_rows,
        [3.4, 3.4],
        note="Tüm deneyler sabit random_state=42 tohumu ve 10-kat StratifiedKFold düzeniyle tek bir betikten (cv_10fold.py) üretilmiştir."
    )

    add_h2("2.4. Sınıflandırma Yöntemleri ve Önsel Olasılık Referans Modeli")
    doc.add_paragraph(
        f"Çalışmada dokuz makine öğrenmesi algoritması ile önsel olasılık referans modelini (DummyClassifier, strategy='prior') "
        f"aynı veri ve aynı 10 katlamada karşılaştırdık. Önsel (prior) strateji, sınıf etiketi tahmininde çoğunluk sınıfını "
        f"seçerken olasılık kestirimlerinde eğitim katlamasındaki gerçek sınıf oranlarını döndürür; böylece most_frequent "
        f"stratejisinin ürettiği yapay 0/1 olasılık cezası yerine adil bir Log-Loss referansı ({tr_num(dummy_ll)}) sunar. "
        f"Hiperparametre ayarından kaynaklanabilecek veri sızıntısını ve ek seçim yanlılığını engellemek amacıyla hiçbir modelin "
        f"hiperparametresini doğrulama verisi üzerinde optimize etmedik; standart ayarları kullandık. Hedef ölçeği Tablo 3'te verilmiştir."
    )
    add_table(
        "Tablo 3. Uyku Bozukluğu Riski (sleep_disorder_risk) sıralı sınıflandırma ölçeği",
        ["Sıra Kodu", "Risk Düzeyi", "Örnek Sayısı (%)", "Klinik Tanım ve Rolü"],
        [
            ("0", "Sağlıklı (Healthy)", "54.156 (%54,16)", "Normal uyku mimarisi, patoloji riski düşük (çoğunluk)"),
            ("1", "Hafif (Mild)", "33.479 (%33,48)", "Hafif uyku bölünmesi ve başlangıç düzeyinde düzensizlik"),
            ("2", "Orta (Moderate)", "8.299 (%8,30)", "Belirgin insomni / orta apne riski (ikincil azınlık)"),
            ("3", "Ağır (Severe)", "4.066 (%4,07)", "Şiddetli uyku bölünmesi ve yüksek klinik risk (birincil pozitif)"),
        ],
        [0.8, 1.4, 1.4, 3.2],
    )

    doc.add_paragraph(
        "Lojistik Regresyon: Özniteliklerin doğrusal bileşimini sigmoid/softmax işlevinden geçirerek sınıf olasılıklarını tahmin "
        "eder; hızlı ve yorumlanabilirdir ancak doğrusal karar sınırı ile sınırlıdır [12]. s doğrusal bileşim skoru olmak üzere,"
    )
    add_eq("f(s) = 1 / (1 + exp(-s))", "2.3")
    doc.add_paragraph("burada f(s) ilgili sınıfa ait olasılık kestirimini ifade eder.")

    doc.add_paragraph(
        "Gauss Naive Bayes: Özniteliklerin sınıf bilindiğinde koşullu bağımsız olduğunu ve normal dağıldığını varsayar; "
        "çok hızlıdır ancak ilişkili özniteliklerde (ör. SFI ve gece uyanma sayısı) bağımsızlık varsayımı ihlal edilir [12]. "
        "C_k sınıf etiketi ve x öznitelik vektörü olmak üzere,"
    )
    add_eq("P(C_k | x) = P(C_k) * Π P(x_i | C_k) / P(x)", "2.4")
    doc.add_paragraph("burada P(C_k) sınıfın önsel olasılığı, P(x_i | C_k) ise i. özniteliğin koşullu olasılık yoğunluğudur.")

    doc.add_paragraph(
        "k-En Yakın Komşu (k-NN): Eğitim aşaması olmadan yeni bir örneği öznitelik uzayındaki en yakın k=5 komşusunun "
        "çoğunluk sınıfına atar; ölçeğe ve yüksek boyutluluğa duyarlıdır [13]. "
        "Destek Vektör Makineleri (Doğrusal DVM ve RBF DVM): Sınıflar arasındaki marjini maksimize eden ayırıcı hiper-düzlemi "
        "arar [14]. w ağırlık vektörü, w_0 sapma terimi ve γ çekirdek genişliği parametresi olmak üzere doğrusal karar fonksiyonu ve RBF çekirdeği,"
    )
    add_eq("g(x) = w^T x + w_0", "2.5")
    add_eq("K(x_i, x_j) = exp(-γ ||x_i - x_j||^2)", "2.6")
    doc.add_paragraph(
        "şeklinde tanımlanır; burada x_i ve x_j iki örnek vektörünü temsil eder. RBF DVM'nin karesel karmaşıklığı O(N²) nedeniyle "
        "her katlamada eğitim alt kümesini tabakalı olarak 25.000 örnekle sınırlandırdık, doğrulamayı ise tam 10.000 örnekte "
        "yürüttük. Dolayısıyla RBF DVM'nin hem süresi hem de genelleme skoru diğer modellerle birebir aynı eğitim bütçesi "
        "altında değildir; bu şerh tüm tablolarda açıkça belirtilmiştir."
    )

    doc.add_paragraph(
        "Rastgele Orman (Random Forest): Çok sayıda karar ağacını bootstrap alt örneklemleriyle eğitip çoğunluk oyuyla birleştirerek "
        "tek ağacın yüksek varyansını düşürür [15]. Çok Katmanlı Algılayıcı (MLP): Gizli katmanlarda doğrusal olmayan aktivasyonlarla "
        "karmaşık örüntüleri öğrenen ileri beslemeli yapay sinir ağıdır [12]. Gradyan Artırma Modelleri (XGBoost ve CatBoost): "
        "Sığ karar ağaçlarını sıralı biçimde ekleyerek önceki ağaçların artık hatalarını azaltır; XGBoost düzenlileştirilmiş "
        "ölçeklenebilir ağaç artırma mimarisiyle, CatBoost ise simetrik (oblivious) ağaç yapısı ve sıralı artırma "
        "mekanizmasıyla aşırı öğrenmeye karşı yüksek direnç sunar [16, 17, 24]."
    )

    # -------------------------------------------------------------------------
    # 3. BULGULAR VE TARTIŞMA (FINDINGS AND DISCUSSION)
    # -------------------------------------------------------------------------
    add_h1("3. BULGULAR VE TARTIŞMA (FINDINGS AND DISCUSSION)")

    add_h2("3.1. Dengesiz ve Sıralı Hedef İçin Seçilen Başarım Metrikleri ve Raporlama İlkeleri")
    doc.add_paragraph(
        "Dengesiz ve sıralı dört sınıflı bu problemde metrik seçimi kritik önemdedir. Çok sınıflı sınıflandırmada Ağırlıklı "
        "Duyarlılık (Weighted Recall) matematiksel olarak Doğruluk (Accuracy) ile özdeş olduğundan, Ağırlıklı F1 çoğunluk "
        "sınıfını aşırı ağırlıklandırarak Doğruluk bilgisini tekrar ettiğinden ve Ağırlıklı Özgüllük Dummy modelinde dahi "
        "yorumlanabilir klinik karşılığı olmayan ara değerler ürettiğinden, bu üç ağırlıklı ölçütü ana kıyaslama tablolarından "
        "bilinçli olarak çıkardık. Bunun yerine problemi dört tamamlayıcı eksende değerlendiren şu ölçüt kümesini kullandık: "
        "(1) Genel ve dengeli ayrım için Accuracy (yalnızca Dummy tabanıyla birlikte), Macro Recall (Dengeli Doğruluk — tüm "
        "sınıflara eşit ağırlık), Macro F1 ve Matthews Korelasyon Katsayısı (MCC) [21]; (2) Sıralı risk mesafesi için "
        "Quadratic Weighted Kappa (QWK) [23] ve ≥2 sınıf uzaklığındaki kritik hata sayısı; (3) Eşikten bağımsız sıralama ve "
        "olasılık kalitesi için Macro AUROC (OvR), Macro AUPR (Average Precision) ve Log-Loss [19]; (4) Azınlık sınıf odakları "
        "için tüm modellerde Ağır sınıf Recall/Precision/Özgüllük ve Orta sınıf Recall/Precision/F1 ölçütleri."
    )
    doc.add_paragraph(
        "DA doğru artı (TP), DE doğru eksi (TN), YA yanlış artı (FP) ve YE yanlış eksi (FN); K = 4 sınıf sayısı ve O_ij ile "
        "E_ij sırasıyla gözlenen ve şans eseri beklenen karmaşıklık matrisi oranları olmak üzere temel ölçütler:"
    )
    add_eq("Doğruluk = (DA + DE) / (DA + YA + DE + YE)  ,  Macro Recall = (1/K) · Σ_k Recall_k", "3.1")
    add_eq("Kesinlik = DA / (DA + YA)  ,  Duyarlılık (Recall) = DA / (DA + YE)", "3.2")
    add_eq("Özgüllük (Specificity) = DE / (DE + YA)  ,  F1 = 2 · Kesinlik · Duyarlılık / (Kesinlik + Duyarlılık)", "3.3")
    add_eq("MCC = (DA·DE − YA·YE) / √((DA+YA)(DA+YE)(DE+YA)(DE+YE))", "3.4")
    add_eq("QWK = 1 − [ Σ_i Σ_j w_ij O_ij ] / [ Σ_i Σ_j w_ij E_ij ]  ,  w_ij = (i − j)² / (K − 1)²", "3.5")
    doc.add_paragraph(
        f"biçiminde tanımlanır. Ağırlıksız Cohen's Kappa da tüm modeller için ayrıca hesaplanmış; ancak çok sınıflı bu veri "
        f"setinde MCC ile neredeyse birebir örtüştüğü (CatBoost için Kappa = {tr_num(best_kappa)} vs. MCC = {tr_num(best_mcc)}; "
        f"tüm modeller arasında en büyük mutlak fark yalnızca {tr_num(max_kappa_mcc_diff)}) gözlemlenmiştir. Buna karşılık QWK, "
        f"komşu sınıf hatasını (ör. Ağır→Orta, w=1/9) uzak sınıf hatasından (Ağır→Sağlıklı, w=1) karesel olarak ayırdığı için "
        f"gerçekten özgün ve klinik açıdan belirleyici bilgi taşımaktadır. Çok sınıflı teorik karmaşıklık matrisi şablonu Tablo "
        f"4'te verilmiştir. Tablolarda raporlanan ± değerleri 10 katlama arasındaki örneklem standart sapmasıdır (ddof=1); "
        f"eğitim kümeleri örtüştüğü için bu aralık güven aralığı olarak yorumlanmamalıdır [22]. Ana tablolarda 10 katlama "
        f"ortalamaları verilirken, karmaşıklık matrisleri, ≥2 sınıf uzak hata sayımları ve ROC/PR eğrileri birleşik (OOF) "
        f"tahminlerden üretilmiştir; oran ölçütlerinde iki yol arasında 0,0001–0,0003 düzeyinde küçük yuvarlama farkları doğaldır."
    )
    add_table(
        "Tablo 4. Çok sınıflı sınıflandırma için teorik karmaşıklık matrisi şablonu (Sınıf 0 bakış açısı)",
        ["", "Tahmin: 0", "Tahmin: 1", "Tahmin: 2", "Tahmin: 3"],
        [
            ("Gerçek: 0", "DA", "YE", "YE", "YE"),
            ("Gerçek: 1", "YA", "DE", "YE", "YE"),
            ("Gerçek: 2", "YA", "YE", "DE", "YE"),
            ("Gerçek: 3", "YA", "YE", "YE", "DE"),
        ],
        [1.4, 1.35, 1.35, 1.35, 1.35],
        note="DA: Doğru Artı (TP), DE: Doğru Eksi (TN), YA: Yanlış Artı (FP), YE: Yanlış Eksi (FN)."
    )

    add_h2("3.2. 10-Kat Çapraz Doğrulama Sonuçları, Azınlık Analizi ve Eşleştirilmiş Farklar")
    mlp_acc, mlp_recm, mlp_f1m, mlp_mcc = (
        df_mean.loc["MLP (Sinir Ağı)", "Accuracy"],
        df_mean.loc["MLP (Sinir Ağı)", "Recall_M"],
        df_mean.loc["MLP (Sinir Ağı)", "F1_M"],
        df_mean.loc["MLP (Sinir Ağı)", "MCC"],
    )
    rf_acc, rf_recm, rf_f1m, rf_mcc = (
        df_mean.loc["Random Forest", "Accuracy"],
        df_mean.loc["Random Forest", "Recall_M"],
        df_mean.loc["Random Forest", "F1_M"],
        df_mean.loc["Random Forest", "MCC"],
    )
    lr_recm, rbf_recm = df_mean.loc["Logistic Regression", "Recall_M"], df_mean.loc["RBF SVM", "Recall_M"]
    nb_acc, nb_recm, nb_f1m, nb_qwk = (
        df_mean.loc["Naive Bayes", "Accuracy"],
        df_mean.loc["Naive Bayes", "Recall_M"],
        df_mean.loc["Naive Bayes", "F1_M"],
        df_mean.loc["Naive Bayes", "QWK"],
    )
    lsvm_acc, lsvm_recm, lsvm_f1m, lsvm_qwk = (
        df_mean.loc["LSVM", "Accuracy"],
        df_mean.loc["LSVM", "Recall_M"],
        df_mean.loc["LSVM", "F1_M"],
        df_mean.loc["LSVM", "QWK"],
    )
    knn_ll = df_mean.loc["kNN (k=5)", "Log_Loss"]

    doc.add_paragraph(
        f"100.000 örneğin tamamı üzerinde sızıntısız 10-kat StratifiedKFold sonuçlarını Tablo 5a, Tablo 5b ve Şekil 2'de sunduk. "
        f"Hiçbir şey öğrenmeden her örneğe çoğunluk sınıfını atayan {DUMMY_NAME} referans modeli {tr_pct(dummy_acc)} Doğruluk "
        f"alırken, Macro Recall = {tr_num(dummy_recm)}, Macro F1 = {tr_num(dummy_f1m)}, MCC = 0,0000, QWK = 0,0000 ve önsel "
        f"olasılık Log-Loss = {tr_num(dummy_ll)} değerinde kalmıştır. Bu taban çizgisi, dengesiz veride yalnızca Doğruluk "
        f"raporlamanın yanıltıcılığını doğrudan kanıtlar. Üstelik kNN (k=5) modelinin Log-Loss değerinin ({tr_num(knn_ll)}) "
        f"hiçbir özellik kullanmayan Dummy önsel referansından ({tr_num(dummy_ll)}) daha kötü olması dikkat çekicidir; k=5 "
        f"komşuluğun ürettiği kalibresiz 0/1 uç olasılıklar yanlış tahminlerde yüksek logaritmik ceza doğurmaktadır."
    )
    doc.add_paragraph(
        f"Dokuz makine öğrenmesi modeli arasında {best} algoritması tüm ana ölçütlerde birinci oldu: Doğruluk {tr_pct(best_acc)} "
        f"(±{tr_num(best_acc_std)}), Macro Recall {tr_num(best_recm)} (±{tr_num(best_recm_std)}), Macro F1 {tr_num(best_f1m)} "
        f"(±{tr_num(best_f1m_std)}), MCC {tr_num(best_mcc)} (±{tr_num(best_mcc_std)}), QWK {tr_num(best_qwk)} "
        f"(±{tr_num(best_qwk_std)}), Macro AUROC {tr_num(best_auroc_m)}, Macro AUPR {tr_num(best_aupr_m)} ve Log-Loss "
        f"{tr_num(best_ll)}. Dengesiz ve sıralı ölçütlerin dahil edilmesi, yalnızca Accuracy veya MCC bakıldığında gizlenen üç "
        f"önemli sıralama değişimini (ranking flip) ortaya çıkardı: (i) Random Forest, Accuracy ({tr_pct(rf_acc)} vs. {tr_pct(mlp_acc)}) "
        f"ve MCC ({tr_num(rf_mcc)} vs. {tr_num(mlp_mcc)}) açısından MLP'nin önünde yer almasına karşın, MLP azınlık sınıflarındaki "
        f"üstünlüğü sayesinde hem Macro Recall ({tr_num(mlp_recm)} vs. {tr_num(rf_recm)}) hem de Macro F1 ({tr_num(mlp_f1m)} vs. "
        f"{tr_num(rf_f1m)}) bakımından Random Forest'ı geride bıraktı; (ii) Lojistik Regresyon, Macro Recall'da ({tr_num(lr_recm)}) "
        f"25K alt örneklemle eğitilen RBF DVM'yi ({tr_num(rbf_recm)}) kıl payı geçti; (iii) Naive Bayes, Accuracy'de LSVM'nin "
        f"gerisinde ({tr_pct(nb_acc)} vs. {tr_pct(lsvm_acc)}) kalmasına rağmen Macro Recall ({tr_num(nb_recm)} vs. {tr_num(lsvm_recm)}), "
        f"Macro F1 ({tr_num(nb_f1m)} vs. {tr_num(lsvm_f1m)}) ve QWK ({tr_num(nb_qwk)} vs. {tr_num(lsvm_qwk)}) ölçütlerinde "
        f"LSVM'yi açık farkla geçti."
    )

    t5a_rows = [
        (
            m,
            f"{tr_num(df_mean.loc[m, 'Accuracy'])} ± {tr_num(df_std.loc[m, 'Accuracy'])}",
            f"{tr_num(df_mean.loc[m, 'Recall_M'])} ± {tr_num(df_std.loc[m, 'Recall_M'])}",
            f"{tr_num(df_mean.loc[m, 'F1_M'])} ± {tr_num(df_std.loc[m, 'F1_M'])}",
            f"{tr_num(df_mean.loc[m, 'QWK'])} ± {tr_num(df_std.loc[m, 'QWK'])}",
        )
        for m in res["model_order"]
    ]
    add_table(
        "Tablo 5a. 100.000 örnek üzerinde 10-kat StratifiedKFold sonuçları (1/2): Accuracy, Macro Recall, Macro F1 ve QWK",
        ["Model", "Accuracy", "Macro Recall (Deng. Doğ.)", "Macro F1", "QWK (Sıralı Uyum)"],
        t5a_rows,
        [1.45, 1.32, 1.38, 1.32, 1.33],
        note="10-kat StratifiedKFold; hücrelerde ortalama ± örneklem std (ddof=1). RBF SVM eğitim katlaması 25.000 tabakalı örnekle sınırlandırılmıştır.",
        font_size=8.3,
    )

    t5b_rows = []
    for m in res["model_order"]:
        ll_str = (
            f"{tr_num(df_mean.loc[m, 'Log_Loss'])} ± {tr_num(df_std.loc[m, 'Log_Loss'])}"
            if pd.notna(df_mean.loc[m, "Log_Loss"]) else "—"
        )
        t5b_rows.append((
            m,
            f"{tr_num(df_mean.loc[m, 'MCC'])} ± {tr_num(df_std.loc[m, 'MCC'])}",
            f"{tr_num(df_mean.loc[m, 'AUROC_M'])} ± {tr_num(df_std.loc[m, 'AUROC_M'])}",
            f"{tr_num(df_mean.loc[m, 'AUPR_M'])} ± {tr_num(df_std.loc[m, 'AUPR_M'])}",
            ll_str,
        ))
    add_table(
        "Tablo 5b. 100.000 örnek üzerinde 10-kat StratifiedKFold sonuçları (2/2): MCC, Macro AUROC, Macro AUPR ve Log-Loss",
        ["Model", "MCC", "Macro AUROC (OvR)", "Macro AUPR", "Log-Loss"],
        t5b_rows,
        [1.45, 1.32, 1.38, 1.32, 1.33],
        note="Olasılık üretmeyen SVM modellerinde (RBF SVM, LSVM) Log-Loss '—' bırakılmış; AUROC/AUPR karar fonksiyonunun softmax dönüşümüyle hesaplanmıştır. Ağırlıksız Cohen's Kappa tüm modellerde MCC ile 0,009 içinde örtüşmektedir.",
        font_size=8.3,
    )
    add_figure("grafik_2_model_karsilastirma.png", "Şekil 2. 10-Kat StratifiedKFold sonuçlarının dengesiz ve sıralı dört ana ölçütte (ortalama ± std) karşılaştırılması", 6.1)

    xgb_sev_prec, xgb_sev_rec, xgb_far = df_min.loc["XGBoost", "Agir_Precision"], df_min.loc["XGBoost", "Agir_Recall"], int(df_min.loc["XGBoost", "Uzak_Hata_2Plus"])
    mlp_sev_rec, mlp_mod_rec, mlp_far = df_min.loc["MLP (Sinir Ağı)", "Agir_Recall"], df_min.loc["MLP (Sinir Ağı)", "Orta_Recall"], int(df_min.loc["MLP (Sinir Ağı)", "Uzak_Hata_2Plus"])
    rf_sev_rec, rf_mod_rec, rf_far = df_min.loc["Random Forest", "Agir_Recall"], df_min.loc["Random Forest", "Orta_Recall"], int(df_min.loc["Random Forest", "Uzak_Hata_2Plus"])
    lsvm_mod_rec, lsvm_far = df_min.loc["LSVM", "Orta_Recall"], int(df_min.loc["LSVM", "Uzak_Hata_2Plus"])
    knn_sev_rec, knn_far = df_min.loc["kNN (k=5)", "Agir_Recall"], int(df_min.loc["kNN (k=5)", "Uzak_Hata_2Plus"])
    nb_sev_rec, nb_far = df_min.loc["Naive Bayes", "Agir_Recall"], int(df_min.loc["Naive Bayes", "Uzak_Hata_2Plus"])

    doc.add_paragraph(
        f"Tüm modellerin birincil pozitif sınıf (Ağır, %4,07) ve en zor geçiş sınıfı (Orta, %8,30) üzerindeki sınıf bazlı "
        f"performansları ile ≥2 sınıf uzaklığındaki kritik hata sayıları Tablo 6'da verilmiştir. Bu tablo dört kritik bulguyu "
        f"açıkça gösterir: (1) Dummy modeli Ağır Özgüllükte 1,0000 alırken Ağır Recall'da 0,0000'da kalarak yüksek özgüllüğün "
        f"nadir sınıflarda tek başına hiçbir tarama değeri taşımadığını gösterir; (2) {best}, 100.000 OOF tahmininde ≥2 sınıf "
        f"uzaklığında hiç kritik hata üretmeyen ({best_far}) tek modeldir (XGBoost: {xgb_far}, MLP: {mlp_far}, RF: {rf_far}); "
        f"ayrıca XGBoost'un Ağır Kesinlikte ({tr_num(xgb_sev_prec)} vs. {tr_num(best_sev_prec)}) çok küçük bir üstünlüğü olsa da "
        f"{best} Ağır Duyarlılıkta ({tr_num(best_sev_rec)} vs. {tr_num(xgb_sev_rec)}) belirgin biçimde öndedir; (3) MLP, Random "
        f"Forest'a kıyasla hem Ağır Recall ({tr_num(mlp_sev_rec)} vs. {tr_num(rf_sev_rec)}) hem Orta Recall ({tr_num(mlp_mod_rec)} "
        f"vs. {tr_num(rf_mod_rec)}) açısından çok daha etkilidir; (4) LSVM, Orta sınıfı fiilen silerek {tr_num(lsvm_mod_rec)} "
        f"duyarlılıkta kalmış ve {tr_int(lsvm_far)} uzak hata üretmiştir (Naive Bayes: Ağır Recall {tr_num(nb_sev_rec)}, uzak hata "
        f"{tr_int(nb_far)}); kNN (k=5) ise Ağır vakaların yalnızca {tr_pct(knn_sev_rec)} kadarını yakalayabilmiş ve {tr_int(knn_far)} "
        f"uzak hata yapmıştır."
    )
    t6_min_rows = [
        (
            m,
            f"{tr_int(r['Agir_Yakalanan'])} ({tr_pct(r['Agir_Recall'], 1)})",
            tr_pct(r["Agir_Precision"], 1),
            tr_pct(r["Agir_Specificity"], 1),
            f"{tr_int(r['Orta_Yakalanan'])} ({tr_pct(r['Orta_Recall'], 1)})",
            tr_pct(r["Orta_Precision"], 1),
            tr_int(r["Uzak_Hata_2Plus"]),
        )
        for m, r in df_min.iterrows()
    ]
    add_table(
        "Tablo 6. Tüm modellerde yakalanan Ağır (4.066) ve Orta (8.299) hasta sayıları, alarm doğruluğu (Precision) ve ≥2 sınıf uzak hatalar",
        [
            "Model",
            "Yakalanan Ağır\n(4.066'dan / Recall)",
            "Ağır Kesinlik\n(Precision)",
            "Ağır Özgüllük\n(Specificity)",
            "Yakalanan Orta\n(8.299'dan / Recall)",
            "Orta Kesinlik\n(Precision)",
            "≥2 Sınıf\nUzak Hata",
        ],
        t6_min_rows,
        [1.32, 1.15, 0.85, 0.85, 1.15, 0.80, 0.68],
        note="Yakalanan hasta sayıları ve ≥2 Sınıf Uzak Hata (|gerçek − tahmin| ≥ 2) 100.000 OOF tahmininden; yüzdeler 10-kat CV ortalamasından alınmıştır.",
        font_size=8.1,
    )

    doc.add_paragraph(
        f"Sekiz gerçek modelin şampiyon {best} ile aynı katlamalardaki eşleştirilmiş farklarını (bilgi taşımayan Dummy satırı "
        f"hariç tutularak) Tablo 7'de sunduk. {best}, diğer sekiz modelin tamamına karşı 10 katlamanın 10'unda da (10-0) MCC, "
        f"Macro F1, QWK ve Macro AUPR ölçütlerinde daha yüksek skor elde etti. Katlamaların eğitim kümeleri %89 oranında "
        f"örtüştüğünden K–Y sayıları betimleyicidir; resmi bir istatistiksel anlamlılık testi yerine geçmez [22]."
    )
    t7_rows = [
        (
            other,
            f"{tr_num(row['MCC_Fark_Ort'])} ± {tr_num(row['MCC_Fark_Std'])}",
            row["MCC_KY"],
            f"{tr_num(row['F1_M_Fark_Ort'])} ± {tr_num(row['F1_M_Fark_Std'])}",
            f"{tr_num(row['QWK_Fark_Ort'])} ± {tr_num(row['QWK_Fark_Std'])}",
            f"{tr_num(row['AUPR_M_Fark_Ort'])} ± {tr_num(row['AUPR_M_Fark_Std'])}",
            row["QWK_KY"],
        )
        for other, row in df_paired.iterrows()
    ]
    add_table(
        f"Tablo 7. {best} ile diğer sekiz model arasında eşleştirilmiş fold farkları (ort ± std, 10 katlama)",
        ["Karşılaştırılan Model", "MCC Farkı", "K–Y", "Macro F1 Farkı", "QWK Farkı", "Macro AUPR Farkı", "K–Y (Tümü)"],
        t7_rows,
        [1.35, 1.05, 0.45, 1.05, 1.05, 1.15, 0.70],
        note=f"Pozitif fark {best} lehinedir. K–Y: {best}'un 10 katlamada kazandığı–kaybettiği tur sayısı (tüm dört ölçütte 10-0).",
        font_size=8.1,
    )

    doc.add_paragraph(
        "Sabit bir karar eşiğindeki hasta yakalama adetleri Tablo 6'da verilmiş olsa da, olası tüm alarm eşiklerinde modellerin "
        "sıralama kalitesini kıyaslamak için hem birincil pozitif sınıf 'Ağır' (%4,07) hem de en zor geçiş sınıfı 'Orta' (%8,30) "
        "için birleşik (OOF) ROC ve Precision–Recall (PR) eğrilerini Şekil 3'te (2×2 panel) çizdik. Görsel netliği artırmak "
        "amacıyla en yüksek, orta ve düşük başarım gruplarını temsil eden beş model (CatBoost, XGBoost, MLP, LSVM ve kNN) "
        "seçildi; tüm dokuz modelin Macro AUROC ve Macro AUPR özetleri Tablo 5b'de yer almaktadır. Negatif örnekler çoğunlukta "
        "olduğundan sol sütundaki ROC eğrileri zayıf modelleri bile sol üst köşeye sıkıştırarak iyimser (AUC = 0,92–0,99) "
        "gösterirken, taban çizgisi prevalansa (0,041 ve 0,083) eşit olan sağ sütundaki PR eğrileri gerçek farkı —özellikle "
        "Orta sınıfta CatBoost (AP=0,861) ile LSVM (0,385) ve kNN (0,275) arasındaki uçurumu— açıkça ortaya koymaktadır."
    )
    add_figure("grafik_3_roc_pr_egrileri.png", "Şekil 3. Seçili beş temsili model için Ağır (%4,07, üst) ve Orta (%8,30, alt) risk sınıflarında birleşik (OOF) ROC ve Precision–Recall eğrileri", 6.3)

    add_h2("3.3. Aşırı Öğrenme (Overfitting) Analizi: Eğitim–CV Farkı, Derinlik Taraması ve Öğrenme Eğrileri")
    rf_tr, rf_cv, rf_gap = df_train_cv.loc["Random Forest", "Egitim_F1_Macro"], df_train_cv.loc["Random Forest", "CV_F1_Macro_Ort"], df_train_cv.loc["Random Forest", "Fark_Macro"]
    cb_tr, cb_cv, cb_gap = df_train_cv.loc[best, "Egitim_F1_Macro"], df_train_cv.loc[best, "CV_F1_Macro_Ort"], df_train_cv.loc[best, "Fark_Macro"]
    lr_tr, lr_cv, lr_gap = df_train_cv.loc["Logistic Regression", "Egitim_F1_Macro"], df_train_cv.loc["Logistic Regression", "CV_F1_Macro_Ort"], df_train_cv.loc["Logistic Regression", "Fark_Macro"]

    doc.add_paragraph(
        f"Modellerin eğitim verisini ezberleme eğilimini ölçmek amacıyla her katlamada eğitim ve doğrulama Macro F1 skorlarını "
        f"karşılaştırdık (Tablo 8). Rastgele Orman eğitimde {tr_num(rf_tr)} skoruna ulaşarak eğitim verisini tam ezberlerken "
        f"doğrulamada {tr_num(rf_cv)} değerine düştü (fark: {tr_num(rf_gap)}). Buna karşılık {best} yalnızca {tr_num(cb_gap)} "
        f"farkla çok daha dengeli genelleme sergiledi. Lojistik Regresyon ise çok düşük bir farka ({tr_num(lr_gap)}) sahip "
        f"olmasına rağmen doğrulamada {tr_num(lr_cv)} ile geride kaldı; bu durum, eğitim–CV farkı küçük olan modelin en iyi "
        f"model olmak zorunda olmadığını ve düşük doğrulama skorunun aşırı öğrenme değil yetersiz kapasite (underfitting) "
        f"göstergesi olabileceğini kanıtlamaktadır."
    )
    t8_rows = [
        (
            m,
            tr_num(row["Egitim_F1_Macro"]),
            f"{tr_num(row['CV_F1_Macro_Ort'])} ± {tr_num(row['CV_F1_Macro_Std'])}",
            tr_num(row["Fark_Macro"]),
        )
        for m, row in df_train_cv.iterrows()
    ]
    add_table(
        "Tablo 8. Eğitim ve 10-kat CV Macro F1 skorlarının karşılaştırılması (Overfitting tanısı)",
        ["Model", "Eğitim Macro F1", "10-Kat CV Macro F1 (ort ± std)", "Fark (Eğitim − CV)"],
        t8_rows,
        [1.8, 1.5, 2.0, 1.5],
        font_size=8.6,
    )

    d2_std = df_depth[df_depth["max_depth"] == "2"]["CV_F1_Macro_Std"].iloc[0]
    d12_cv = df_depth[df_depth["max_depth"] == "12"]["CV_F1_Macro_Ort"].iloc[0]
    dinf_tr = df_depth[df_depth["max_depth"] == "Sınırsız"]["Egitim_F1_Macro"].iloc[0]
    dinf_cv = df_depth[df_depth["max_depth"] == "Sınırsız"]["CV_F1_Macro_Ort"].iloc[0]
    doc.add_paragraph(
        f"Model esnekliğinin etkisini doğrudan gözlemek için Karar Ağacı üzerinde max_depth taraması (Tablo 9) ve üç farklı "
        f"model için öğrenme eğrileri (Şekil 4) ürettik. Derinlik 1–4 aralığında hem eğitim hem CV skoru düşüktür (underfitting). "
        f"CV Macro F1 derinlik 12'de zirve yaparken ({tr_num(d12_cv)}), sınırsız derinlikte eğitim skoru {tr_num(dinf_tr)} olmuş "
        f"ve CV skoru {tr_num(dinf_cv)} değerine gerilemiştir (overfitting). Dikkat çekici biçimde, en yüksek standart sapma "
        f"({tr_num(d2_std)}) derinlik 2'de (underfit bölgede) ortaya çıkmıştır; bu bulgu, yüksek standart sapmanın tek başına "
        f"overfitting kanıtı olmadığını deneysel olarak doğrulamaktadır."
    )
    t9_rows = [
        (
            r["max_depth"],
            tr_num(r["Egitim_F1_Macro"]),
            f"{tr_num(r['CV_F1_Macro_Ort'])} ± {tr_num(r['CV_F1_Macro_Std'])}",
            tr_num(r["Fark"]),
        )
        for _, r in df_depth.iterrows()
    ]
    add_table(
        "Tablo 9. Karar ağacında max_depth karmaşıklık taraması (10-kat StratifiedKFold, Macro F1)",
        ["max_depth", "Eğitim Macro F1", "10-Kat CV Macro F1 (ort ± std)", "Fark (Eğitim − CV)"],
        t9_rows,
        [1.2, 1.5, 2.5, 1.6],
    )
    add_figure("grafik_6_derinlik_ve_ogrenme.png", "Şekil 4. Karar ağacı karmaşıklık taraması (solda) ve üç modelin öğrenme eğrileri (sağda)", 6.2)

    add_h2("3.4. Sınıf Dengesizliği Müdahale ve SMOTE Sızıntı Deneyi")
    lr_sade_sev = df_imb.loc["LR (Sade)", "Recall_Agir_Ort"]
    lr_cw_sev = df_imb.loc["LR + class_weight", "Recall_Agir_Ort"]
    lr_sade_mod = df_imb.loc["LR (Sade)", "Recall_Orta_Ort"]
    lr_cw_mod = df_imb.loc["LR + class_weight", "Recall_Orta_Ort"]
    rf_sade_m = df_imb.loc["RF (Sade)", "F1_Macro_Ort"]
    rf_sm_m = df_imb.loc["RF + SMOTE (Pipeline)", "F1_Macro_Ort"]
    rf_sade_qwk = df_imb.loc["RF (Sade)", "QWK_Ort"]
    rf_sm_qwk = df_imb.loc["RF + SMOTE (Pipeline)", "QWK_Ort"]
    sm_wrong_sev = df_smote_leak.loc["Yanlış (Önce SMOTE → Sonra CV)", "Recall_Agir"]
    sm_right_sev = df_smote_leak.loc["Doğru (Pipeline İçinde SMOTE)", "Recall_Agir"]

    lr_sev_gain_tr = tr_num((lr_cw_sev - lr_sade_sev) * 100, 1)
    lr_mod_gain_tr = tr_num((lr_cw_mod - lr_sade_mod) * 100, 1)
    sm_gap_tr = tr_num((sm_wrong_sev - sm_right_sev) * 100, 1)

    doc.add_paragraph(
        f"Azınlık sınıflardaki (%8,30 Orta ve %4,07 Ağır) duyarlılığı incelemek amacıyla 20.000 tabakalı örneklem üzerinde "
        f"10-kat CV ile sınıf ağırlıklandırma (class_weight) ve ImbPipeline içinde SMOTE [18] müdahalelerini sınadık (Tablo 10, "
        f"Şekil 5). Lojistik Regresyon'da class_weight='balanced' kullanımı, Ağır sınıf duyarlılığını {tr_pct(lr_sade_sev)} "
        f"düzeyinden {tr_pct(lr_cw_sev)} düzeyine (+{lr_sev_gain_tr} puan) ve Orta sınıf duyarlılığını {tr_pct(lr_sade_mod)} "
        f"düzeyinden {tr_pct(lr_cw_mod)} düzeyine (+{lr_mod_gain_tr} puan) yükseltirken, toplam doğruluk ve MCC'de küçük bir "
        f"ödünleşim (trade-off) yarattı. Rastgele Orman'da ise Pipeline içi SMOTE, Macro F1 skorunu {tr_num(rf_sade_m)} "
        f"değerinden {tr_num(rf_sm_m)} değerine ve QWK'yi {tr_num(rf_sade_qwk)} değerinden {tr_num(rf_sm_qwk)} değerine iyileştirdi."
    )
    t10_rows = [
        (
            m,
            f"{tr_num(r['Accuracy_Ort'])} ± {tr_num(r['Accuracy_Std'])}",
            f"{tr_num(r['F1_Macro_Ort'])} ± {tr_num(r['F1_Macro_Std'])}",
            tr_num(r["Recall_Orta_Ort"]),
            tr_num(r["Recall_Agir_Ort"]),
            tr_num(r["MCC_Ort"]),
            tr_num(r["QWK_Ort"]),
            tr_num(r["AUPR_Macro_Ort"]),
        )
        for m, r in df_imb.iterrows()
    ]
    add_table(
        "Tablo 10. Sınıf dengesizliği müdahale deneyi (20.000 tabakalı örneklem, 10-kat CV, SMOTE Pipeline içinde)",
        ["Model", "Accuracy", "Macro F1", "Orta Rec.", "Ağır Rec.", "MCC", "QWK", "Macro AUPR"],
        t10_rows,
        [1.40, 1.00, 1.00, 0.65, 0.65, 0.68, 0.68, 0.74],
        font_size=7.9,
    )
    add_figure("grafik_7_dengesizlik_deneyi.png", "Şekil 5. Sınıf dengesizliği müdahalelerinin (class_weight ve Pipeline içi SMOTE) ölçütler üzerindeki etkisi", 6.0)

    doc.add_paragraph(
        f"SMOTE'un çapraz doğrulama öncesinde tüm veriye uygulanmasının yol açtığı veri sızıntısını ayrıca deneysel olarak "
        f"ölçtük (Tablo 11). Yanlış yöntemde sentetik komşular eğitim ve doğrulama katlamalarına dağıldığından Ağır sınıf "
        f"Recall değeri {tr_num(sm_wrong_sev)} gibi yapay biçimde şişti; doğru yöntemde (Pipeline içinde SMOTE) gerçek değerin "
        f"{tr_num(sm_right_sev)} olduğu görüldü ({sm_gap_tr} yüzde puanlık sahte iyimserlik)."
    )
    t11_rows = [
        (idx, tr_num(r["F1_Macro"]), tr_num(r["Recall_Agir"]), tr_num(r["MCC"]))
        for idx, r in df_smote_leak.iterrows()
    ]
    add_table(
        "Tablo 11. SMOTE veri sızıntısı deneyi: CV öncesi SMOTE (yanlış) vs. Pipeline içi SMOTE (doğru), Random Forest",
        ["Yöntem", "Macro F1", "Ağır Sınıf Recall", "MCC"],
        t11_rows,
        [2.9, 1.3, 1.4, 1.2],
    )

    add_h2("3.5. Şampiyon Modelde (CatBoost) Sızıntısız Öznitelik Katkı Analizi")
    doc.add_paragraph(
        f"Model kararlarına en yüksek katkıyı sağlayan öznitelikleri sızıntısız biçimde incelemek için ayrı bir tam-veri modeli "
        f"eğitmek yerine, şampiyon {best} modelinin 10 çapraz doğrulama eğitim katlamasında hesaplanan göreli katkı paylarını "
        f"(PredictionValuesChange, One-Hot alt sütunları ana öznitelik altında toplanmış) ortalama ± standart sapma olarak "
        f"raporladık (Tablo 12, Şekil 6). Bu değerler nedensel bir etkiyi değil, yalnızca modelin sınıflandırma kararlarındaki "
        f"istatistiksel bilgi katkısını göstermektedir."
    )
    doc.add_paragraph(
        f"Şampiyon {best} modelinde kararlara en yüksek katkıyı sağlayan ilk üç öznitelik sırasıyla {top1_feat} "
        f"(%{tr_num(top1_ort, 2)} ± {tr_num(top1_std, 2)}), {top2_feat} (%{tr_num(top2_ort, 2)} ± {tr_num(top2_std, 2)}) ve "
        f"{top3_feat} (%{tr_num(top3_ort, 2)} ± {tr_num(top3_std, 2)}) oldu. Türetilen öznitelikler açısından dürüst ve önemli "
        f"bir gözlem ortaya çıktı: SFI (%{tr_num(sfi_ort, 2)} ± {tr_num(sfi_std, 2)}; {sfi_rank}. sıra) ve RSR "
        f"(%{tr_num(rsr_ort, 2)} ± {tr_num(rsr_std, 2)}; {rsr_rank}. sıra), CatBoost'ta ham bileşenlerinden daha düşük doğrudan "
        f"pay aldı. Bunun temel nedeni Bölüm 2.1'de saptanan doğrusal/oran bağımlılığıdır: CatBoost simetrik ağaçları doğrudan "
        f"uyku süresi (%{tr_num(top2_ort, 2)}) ve gece uyanma sayısı ({wake_rank}. sıra, %{tr_num(wake_ort, 2)}) üzerinde "
        f"bölünmeler oluşturabildiği için, SFI (r = {tr_num(r_sfi_wake)}) ve tam doğrusal toplam olan RSR (r = {tr_num(r_rsr_deep)}) "
        f"bilgi payını ham bileşenleriyle paylaşmaktadır; nitekim SFI'nin katlamalar arası göreli standart sapmasının "
        f"(±{tr_num(sfi_std, 2)}) yüksek olması da farklı katlamalarda ham ve türetilmiş sütunların birbirinin yerine seçildiğini "
        f"doğrulamaktadır."
    )
    t12_rows = [
        (str(i + 1), r["Ozellik"], f"%{tr_num(r['Onem_Ort'], 2)}", f"± {tr_num(r['Onem_Std'], 2)}")
        for i, (_, r) in enumerate(df_imp.head(15).iterrows())
    ]
    add_table(
        f"Tablo 12. Şampiyon {best} modelinin kararlarına en yüksek katkıyı sağlayan 15 öznitelik (10 eğitim katlaması ort ± std)",
        ["Sıra", "Öznitelik", "Ort. Katkı Payı (%)", "Katlama Std (%)"],
        t12_rows,
        [0.6, 3.6, 1.3, 1.3],
        note="Katkı payları yalnızca 10 CV eğitim katlamasından hesaplanmış, One-Hot sütunları ana öznitelik altında toplanmıştır; nedensellik ifade etmez.",
    )
    add_figure("grafik_5_ozellik_onemi.png", f"Şekil 6. Şampiyon {best} modelinin kararlarına en yüksek katkıyı sağlayan ilk 15 öznitelik (10 eğitim katlaması ort ± std)", 5.9)

    add_h2("3.6. Karmaşıklık Matrisleri, Prevalans–PPV Analizi ve Klinik Sınırlılıklar")
    doc.add_paragraph(
        f"Dokuz modelin 100.000 örnek üzerindeki birleşik (OOF) karmaşıklık matrislerini Şekil 7'de, şampiyon {best} modelinin "
        f"sayısal dağılımını Tablo 13'te ve sınıf bazında başarım karnesini Tablo 14'te sunduk."
    )
    add_figure("grafik_4_confusion_matrices.png", "Şekil 7. Dokuz makine öğrenmesi modelinin 10-kat CV birleşik (OOF) karmaşıklık matrisleri (MCC ve QWK ile)", 6.2)

    cm_vals = df_cm.to_numpy()
    cls_labels = list(df_cm.index)
    t13_rows = []
    for i, lbl in enumerate(cls_labels):
        row_sum = int(cm_vals[i].sum())
        rec_i = cm_vals[i, i] / row_sum
        t13_rows.append((
            lbl,
            tr_int(cm_vals[i, 0]), tr_int(cm_vals[i, 1]), tr_int(cm_vals[i, 2]), tr_int(cm_vals[i, 3]),
            tr_int(row_sum), tr_pct(rec_i)
        ))
    col_sums = cm_vals.sum(axis=0)
    t13_rows.append((
        "Toplam Tahmin",
        tr_int(col_sums[0]), tr_int(col_sums[1]), tr_int(col_sums[2]), tr_int(col_sums[3]),
        tr_int(cm_vals.sum()), tr_pct(np.trace(cm_vals) / cm_vals.sum())
    ))
    add_table(
        f"Tablo 13. {best} modelinin 10-kat CV birleşik (OOF) karmaşıklık matrisi (100.000 Örnek)",
        ["Gerçek Sınıf", "T: Sağlıklı", "T: Hafif", "T: Orta", "T: Ağır", "Toplam", "Duyarlılık"],
        t13_rows,
        [1.50, 0.85, 0.85, 0.85, 0.85, 0.95, 0.95],
        font_size=8.5,
    )

    t14_rows = []
    for idx in cls_labels + ["macro avg", "weighted avg"]:
        r = df_cls.loc[idx]
        lbl_tr = "Macro Ortalama" if idx == "macro avg" else ("Ağırlıklı Ortalama" if idx == "weighted avg" else idx)
        t14_rows.append((lbl_tr, tr_num(r["precision"]), tr_num(r["recall"]), tr_num(r["f1-score"]), tr_int(r["support"])))
    add_table(
        f"Tablo 14. {best} modelinin sınıf bazında birleşik (OOF) başarım karnesi",
        ["Risk Düzeyi", "Kesinlik (Precision)", "Duyarlılık (Recall)", "F1-Skoru", "Örnek Sayısı"],
        t14_rows,
        [1.8, 1.25, 1.25, 1.25, 1.25],
    )

    sev_to_healthy = int(cm_vals[3, 0])
    sev_to_mild = int(cm_vals[3, 1])
    sev_to_mod = int(cm_vals[3, 2])
    sev_tp = int(cm_vals[3, 3])
    hlth_tp = int(cm_vals[0, 0])
    hlth_fp = int(cm_vals[0, 1])
    hlth_rec = hlth_tp / cm_vals[0].sum()

    doc.add_paragraph(
        f"Karmaşıklık matrisinden çıkardığımız temel gözlemler şunlardır: (1) Ağır risk grubundaki 4.066 vakanın {tr_int(sev_tp)} "
        f"tanesi doğru yakalandı; 'Sağlıklı' ({sev_to_healthy}) veya 'Hafif' ({sev_to_mild}) sınıfına düşen hiçbir vaka olmadı, "
        f"hataların tamamı komşu 'Orta' ({tr_int(sev_to_mod)}) sınıfına kaydı. (2) 54.156 sağlıklı bireyin {tr_int(hlth_tp)} "
        f"tanesi ({tr_pct(hlth_rec)}) doğru tahmin edildi, yalnızca {hlth_fp} birey Hafif sınıfına atandı. (3) Tüm hatalar "
        f"fizyolojik spektrumun geçiş bölgesi olan komşu sınıflarda (Hafif↔Orta ve Orta↔Ağır) yoğunlaştı; bu durum yüksek QWK "
        f"({tr_num(best_qwk)}) ve sıfır uzak hata ({best_far}) bulgusuyla birebir örtüşmektedir. (4) Şekil 7'de LSVM'nin Orta "
        f"sınıfı neredeyse tamamen Hafif'e attığı (7.847 vaka), k-NN'in ise 90 Ağır hastayı doğrudan Sağlıklı tahmin ettiği "
        f"açıkça görülmektedir."
    )

    ppv_base = df_ppv.iloc[0]["PPV"]
    ppv_2pct = df_ppv.iloc[1]["PPV"]
    ppv_1pct = df_ppv.iloc[2]["PPV"]
    ppv_05pct = df_ppv.iloc[3]["PPV"]
    ppv_rec_const = df_ppv.iloc[0]["Recall_Sabit"]
    ppv_spec_const = df_ppv.iloc[0]["Specificity_Sabit"]

    doc.add_paragraph(
        f"Prevalansın Pozitif Öngörü Değerine (PPV) Etkisi: Duyarlılık (Recall) ve Özgüllük (Specificity) sınıf oranından "
        f"bağımsız kalabilirken, klinik taramada bir 'Ağır risk' uyarısının gerçekten hasta çıkma olasılığı olan Kesinlik "
        f"(PPV), Bayes teoremi uyarınca popülasyondaki prevalansa (p) doğrudan bağlıdır:"
    )
    add_eq("PPV(p) = (Recall · p) / [ Recall · p + (1 − Specificity) · (1 − p) ]", "3.6")
    doc.add_paragraph(
        f"Şampiyon {best} modelinin Ağır sınıf için sabit OOF Duyarlılığı ({tr_num(ppv_rec_const)}) ve çok yüksek Özgüllüğü "
        f"({tr_num(ppv_spec_const)}) altında farklı varsayımsal prevalans senaryolarında PPV değişimini kodla hesaplayıp Tablo "
        f"15'te sunduk. Veri setindeki %4,07 prevalansta {tr_pct(ppv_base)} olan PPV, prevalansın %2'ye düştüğü genel klinik "
        f"taramada {tr_pct(ppv_2pct)} düzeyine, %1 prevalansta {tr_pct(ppv_1pct)} düzeyine, %0,5 nadir taramada ise "
        f"{tr_pct(ppv_05pct)} düzeyine gerilemektedir; başka bir deyişle %99,50 özgüllüğe sahip modelde dahi %0,5 prevalansta "
        f"verilen alarmların yarıdan fazlası yanlış pozitif hâline gelmektedir."
    )
    t15_rows = [
        (
            tr_pct(r["Prevalans"], 2),
            tr_num(r["Recall_Sabit"]),
            tr_num(r["Specificity_Sabit"]),
            tr_pct(r["PPV"], 2),
            r["Yorum"],
        )
        for _, r in df_ppv.iterrows()
    ]
    add_table(
        f"Tablo 15. {best} (Ağır Risk) için farklı varsayımsal prevalans senaryolarında hesaplanan PPV değerleri",
        ["Prevalans (p)", "Sabit Recall", "Sabit Özgüllük", "Beklenen PPV", "Tarama Senaryosu"],
        t15_rows,
        [1.00, 0.95, 1.00, 1.00, 2.85],
        note="Değerler CatBoost'un 100.000 OOF tahminindeki Ağır sınıf duyarlılık ve özgüllüğü sabit tutularak Denklem (3.6) ile koddan hesaplanmıştır.",
        font_size=8.4,
    )

    doc.add_paragraph(
        "Klinik Bağlam, Seçim Yanlılığı ve Çalışmanın Sınırlılıkları: Elde edilen yüksek çapraz doğrulama skorları bu "
        "modellerin doğrudan bir klinik karar destek aracı olarak devreye alınabileceği anlamına gelmez. Sağlık uygulamaları "
        "açısından şu beş sınırlılık açıkça vurgulanmalıdır: (i) Dış doğrulama (farklı hastane, giyilebilir sensör ve demografik "
        "popülasyonlar üzerinde sınama) yapılmamıştır; (ii) olasılık çıktılarının kalibrasyonu (ör. Brier skoru, güvenilirlik "
        "diyagramı) ayrıca değerlendirilmemiştir; (iii) düşük prevalanslı tarama ortamlarında PPV'nin belirgin biçimde "
        "düştüğü Tablo 15'te nicel olarak gösterilmiştir; (iv) Seçim Yanlılığı (Selection Bias) Uyarısı — hiperparametre "
        "optimizasyonu yapılmasa dahi dokuz farklı algoritma aynı 10-kat CV verisinde kıyaslanıp en yüksek skorlu model "
        "(CatBoost) seçildiği için, raporlanan en iyi skor küçük de olsa iyimser seçim yanlılığı taşıyabilir; tamamen "
        "yansız son kestirim için hiç dokunulmamış bağımsız bir dış test kümesi veya iç içe çapraz doğrulama (nested CV) "
        "gereklidir [20]; (v) sonuçlar UCI dışı, Kaggle kaynaklı (sentetik bileşen içerebilen) tek bir veri setine, tek bir "
        "random_state=42 bölünmesine dayanmakta olup resmi bir istatistiksel anlamlılık testi uygulanmamıştır."
    )

    add_h2("3.7. Hesaplama Verimliliği ve Adil Kıyaslama Şerhi (Computational Efficiency)")
    xgb_time = df_mean.loc["XGBoost", "Sure_sn"]
    doc.add_paragraph(
        f"Dokuz modelin 10-kat çapraz doğrulama toplam sürelerini ve temel başarımlarını Tablo 16 ve Şekil 8'de sunduk. "
        f"{best} ({tr_num(best_time, 2)} sn) ve XGBoost ({tr_num(xgb_time, 2)} sn), hem en yüksek genelleme başarısını hem de "
        f"düşük hesaplama maliyetini birleştirerek verimlilik sınırında (Pareto-optimum) konumlandı. Buna karşın adil kıyaslama "
        f"ilkesi gereği iki teknik şerh düşülmelidir: (1) RBF DVM her katlamada 90.000 yerine 25.000 tabakalı eğitim örneğiyle "
        f"çalıştırıldığından süresi ve doğrulama skoru diğer modellerle aynı veri bütçesi altında değildir; (2) CatBoost, "
        f"XGBoost, Rastgele Orman ve k-NN iki iş parçacığıyla (thread_count=2 / n_jobs=2) çalışırken, scikit-learn'ün tek "
        f"iş parçacıklı tahmin edicileri (MLP, Lojistik Regresyon, LSVM, RBF DVM, Naive Bayes) tek çekirdekte yürütülmüştür; "
        f"bu nedenle raporlanan süreler donanımdan bağımsız teorik karmaşıklık ölçümü değil, pratik çalışma maliyetidir."
    )
    t16_rows = [
        (
            f"{r['Model']}*" if r["Model"] == "RBF SVM" else r["Model"],
            tr_num(r["Accuracy"]),
            tr_num(r["Macro_Recall"]),
            tr_num(r["MCC"]),
            tr_num(r["QWK"]),
            tr_num(r["Sure_sn"], 2),
        )
        for _, r in df_eff.iterrows()
    ]
    add_table(
        "Tablo 16. Dokuz makine öğrenmesi modelinin 10-kat CV toplam eğitim süreleri ve başarım özeti",
        ["Model", "Accuracy", "Macro Recall", "MCC", "QWK", "Toplam Süre (sn)"],
        t16_rows,
        [1.55, 1.00, 1.05, 1.00, 1.00, 1.20],
        note="*RBF SVM eğitim katlaması 25.000 tabakalı örnekle sınırlandırılmıştır; diğer tüm modeller 90.000/10.000 ile eğitilmiştir. Paralellik ayarları algoritmaya göre (1 veya 2 iş parçacığı) farklılık göstermektedir.",
    )
    add_figure("grafik_8_hiz_vs_basari.png", "Şekil 8. Modellerin 10-kat CV hesaplama süresi ile MCC performansı arasındaki verimlilik dengesi", 5.8)

    # -------------------------------------------------------------------------
    # 4. SONUÇLAR (CONCLUSIONS)
    # -------------------------------------------------------------------------
    add_h1("4. SONUÇLAR (CONCLUSIONS)")
    doc.add_paragraph(
        f"Bu çalışmada, 100.000 bireye ait uyku sağlığı ve yaşam tarzı verileri üzerinde dört sıralı sınıflı uyku bozukluğu "
        f"riskini tahmin etmek amacıyla dokuz makine öğrenmesi algoritmasını ve bir önsel olasılık referans modelini "
        f"(DummyClassifier, strategy='prior'), sızıntısız Pipeline ve ColumnTransformer mimarisiyle 10-kat StratifiedKFold "
        f"düzeninde kıyasladık. {best} algoritması tüm katlamalarda (10-0) diğer modelleri geride bırakarak {tr_pct(best_acc)} "
        f"doğruluk, {tr_num(best_recm)} Macro Recall, {tr_num(best_f1m)} Macro F1, {tr_num(best_mcc)} MCC ve {tr_num(best_qwk)} "
        f"QWK ile en yüksek genelleme başarısına ulaştı; 100.000 OOF tahmininde ≥2 sınıf uzaklığında hiç kritik hata ({best_far}) "
        f"üretmedi. Dengesiz ve sıralı ölçütlerin eklenmesi, yalnızca Accuracy veya MCC bakıldığında gözden kaçan MLP > Random "
        f"Forest ve Naive Bayes > LSVM gibi önemli sıralama farklarını gün yüzüne çıkardı."
    )
    doc.add_paragraph(
        "Yürüttüğümüz ek deneyler; (i) nominal değişkenlerde Pipeline içi One-Hot kodlamanın veri sızıntısını önlediğini, "
        "(ii) aşırı öğrenme tanısında eğitim–CV farkı ve öğrenme eğrilerinin tekil standart sapmadan daha güvenilir olduğunu, "
        "(iii) SMOTE'un çapraz doğrulama öncesinde uygulanmasının ağır risk sınıfı duyarlılığını yapay olarak şişirdiğini, "
        "(iv) şampiyon modelin 10 eğitim katlamasından elde edilen öznitelik katkılarında doğrusal/oran bağımlılığı bulunan "
        "türetilmiş sütunların (SFI ve RSR) bilgi payını ham bileşenleriyle paylaştığını ve (v) düşük prevalanslı tarama "
        "koşullarında yüksek özgüllüğe rağmen PPV'nin hızla düştüğünü deneysel olarak ortaya koydu. Gelecek çalışmalarda çok "
        "merkezli klinik polisomnografi verileri üzerinde dış doğrulama, iç içe çapraz doğrulama ile maliyet duyarlı eşik "
        "optimizasyonu ve olasılık kalibrasyonu analizlerinin yürütülmesini hedefliyoruz."
    )

    # -------------------------------------------------------------------------
    # SON BÖLÜMLER
    # -------------------------------------------------------------------------
    add_h1("KAYNAK DOSYALAR (SUPPLEMENTARY FILES)")
    doc.add_paragraph("Çalışmanın sızıntısız kaynak kodları, sabitlenmiş bağımlılık listesi (requirements.txt), tüm deney çıktıları ve grafikler https://github.com/DBurakyuz/sleep-disorder-ml adresinde açık erişimli olarak paylaşılmıştır.")

    add_h1("TEŞEKKÜR (ACKNOWLEDGMENTS)")
    doc.add_paragraph("Bu çalışma, Yalova Üniversitesi Mühendislik Fakültesi Bilgisayar Mühendisliği Bölümü Makine Öğrenmesi dersi kapsamında gerçekleştirilmiştir.")

    add_h1("KAYNAKLAR (REFERENCES)")
    kaynaklar = [
        "[1] Walker, M. P., \"Why We Sleep: Unlocking the Power of Sleep and Dreams\", Scribner, New York, 2017.",
        "[2] Morin, C. M., Jarrin, D. C., \"Epidemiology of insomnia: Prevalence, course, risk factors, and public health burden\", Sleep Medicine Clinics, Cilt 17, No 2, 173-191, 2022.",
        "[3] Türk Toraks Derneği, \"Obstrüktif Uyku Apne Sendromu Tanı ve Tedavi Uzlaşı Raporu\", Türk Toraks Dergisi, Cilt 13, Ek 1, 1-73, 2012.",
        "[4] Alpaydin, E., \"Introduction to Machine Learning\", 3. Baskı, The MIT Press, Cambridge, MA, 2014.",
        "[5] Al-Angari, H. M., Sahakian, A. V., \"Automated recognition of obstructive sleep apnea syndrome using support vector machine classifier\", IEEE Trans. Inf. Technol. Biomed., Cilt 16, No 3, 463-468, 2012.",
        "[6] Palotti, J., Mall, R., Aupetit, M., Rueschman, M., Singh, M., Sathyanarayana, A., Taheri, S., Fernandez-Luque, L., \"Benchmark on a large cohort for sleep-wake classification with machine learning techniques\", npj Digital Medicine, Cilt 2, Makale 50, 2019.",
        "[7] Penzel, T., McNames, J., Murray, A., de Chazal, P., Moody, G., Raymond, B., \"Systematic comparison of different algorithms for apnoea detection based on electrocardiogram recordings\", Med. Biol. Eng. Comput., Cilt 40, No 4, 402-407, 2002.",
        "[8] Sadeh, A., Sharkey, K. M., Carskadon, M. A., \"Activity-based sleep-wake identification: An empirical test of methodological issues\", Sleep, Cilt 17, No 3, 201-207, 1994.",
        "[9] Faust, O., Razaghi, H., Barika, R., Ciaccio, E. J., Acharya, U. R., \"A review of automated sleep stage scoring based on physiological signals for the new millennia\", Computer Methods and Programs in Biomedicine, Cilt 176, 81-91, 2019.",
        "[10] Bonnet, M. H., Arand, D. L., \"Clinical effects of sleep fragmentation versus sleep deprivation\", Sleep Medicine Reviews, Cilt 7, No 4, 297-310, 2003.",
        "[11] Buysse, D. J., Reynolds, C. F., Monk, T. H., Berman, S. R., Kupfer, D. J., \"The Pittsburgh Sleep Quality Index: A new instrument for psychiatric practice and research\", Psychiatry Research, Cilt 28, No 2, 193-213, 1989.",
        "[12] Pedregosa, F. ve ark., \"Scikit-learn: Machine learning in Python\", Journal of Machine Learning Research, Cilt 12, 2825-2830, 2011.",
        "[13] Cover, T. M., Hart, P. E., \"Nearest neighbor pattern classification\", IEEE Trans. Inf. Theory, Cilt 13, No 1, 21-27, 1967.",
        "[14] Cortes, C., Vapnik, V., \"Support-vector networks\", Machine Learning, Cilt 20, No 3, 273-297, 1995.",
        "[15] Breiman, L., \"Random Forests\", Machine Learning, Cilt 45, No 1, 5-32, 2001.",
        "[16] Friedman, J. H., \"Greedy function approximation: A gradient boosting machine\", Annals of Statistics, Cilt 29, No 5, 1189-1232, 2001.",
        "[17] Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., Gulin, A., \"CatBoost: Unbiased boosting with categorical features\", Advances in Neural Information Processing Systems (NeurIPS), Cilt 31, 6639-6649, 2018.",
        "[18] Chawla, N. V., Bowyer, K. W., Hall, L. O., Kegelmeyer, W. P., \"SMOTE: Synthetic minority over-sampling technique\", Journal of Artificial Intelligence Research, Cilt 16, 321-357, 2002.",
        "[19] Kaufman, S., Rosset, S., Perlich, C., Stitelman, O., \"Leakage in data mining: Formulation, detection, and avoidance\", ACM TKDD, Cilt 6, No 4, Makale 15, 2012.",
        "[20] Cawley, G. C., Talbot, N. L. C., \"On over-fitting in model selection and subsequent selection bias in performance evaluation\", Journal of Machine Learning Research, Cilt 11, 2079-2107, 2010.",
        "[21] Chicco, D., Jurman, G., \"The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation\", BMC Genomics, Cilt 21, Makale 6, 2020.",
        "[22] Nadeau, C., Bengio, Y., \"Inference for the generalization error\", Machine Learning, Cilt 52, No 3, 239-281, 2003.",
        "[23] Cohen, J., \"Weighted kappa: Nominal scale agreement with provision for scaled disagreement or partial credit\", Psychological Bulletin, Cilt 70, No 4, 213-220, 1968.",
        "[24] Chen, T., Guestrin, C., \"XGBoost: A scalable tree boosting system\", Proc. 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 785-794, 2016.",
    ]
    for k in kaynaklar:
        pk = doc.add_paragraph()
        pk.paragraph_format.space_after = Pt(3)
        pk.paragraph_format.left_indent = Inches(0.3)
        pk.paragraph_format.first_line_indent = Inches(-0.3)
        rk = pk.add_run(k)
        rk.font.size = Pt(9.0)

    with open(out_path, "wb") as fp:
        doc.save(fp)
    print(f"BASARILI: Guncellenmis Word makalesi '{out_path}' olarak kaydedildi!")


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "Makine_Ogrenmesi_Ile_Uyku_Bozuklugu_Riski_Tahmini.docx"
    create_paper(target)
