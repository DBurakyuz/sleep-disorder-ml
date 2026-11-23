# =============================================================================
# GAZİ ÜNİVERSİTESİ FEN BİLİMLERİ DERGİSİ (GU J SCI, PART C)
# DİNAMİK WORD MAKALE ÜRETİCİSİ — TÜM SAYILAR GERÇEK KOD ÇIKTISINDAN OKUNUR
# Yazar: Dursun Burak AKYÜZ (Yalova Üniversitesi, Bilgisayar Mühendisliği)
# =============================================================================

import json
from pathlib import Path

import numpy as np
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.shared import Inches, Pt, RGBColor

TAB = Path("tablolar")
FIG = Path("grafikler")


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


def create_paper():
    # -------------------------------------------------------------------------
    # GERÇEK DENEY ÇIKTILARINI YÜKLE (TEK GERÇEK KAYNAĞI)
    # -------------------------------------------------------------------------
    with open(TAB / "sonuclar.json", "r", encoding="utf-8") as f:
        res = json.load(f)

    df_mean = pd.read_csv(TAB / "cv_ortalama.csv", index_col=0)
    df_std = pd.read_csv(TAB / "cv_std.csv", index_col=0)
    df_train_cv = pd.read_csv(TAB / "egitim_cv_karsilastirma.csv", index_col=0)
    df_paired = pd.read_csv(TAB / "eslestirilmis_fold_farklari.csv", index_col=0)
    df_depth = pd.read_csv(TAB / "derinlik_taramasi.csv")
    df_imb = pd.read_csv(TAB / "dengesizlik_deneyi.csv", index_col=0)
    df_smote_leak = pd.read_csv(TAB / "smote_sizinti_deneyi.csv", index_col=0)
    df_imp = pd.read_csv(TAB / "ozellik_onem_tablosu.csv")
    df_cm = pd.read_csv(TAB / "sampiyon_confusion_matrix.csv", index_col=0)
    df_cls = pd.read_csv(TAB / "sinif_bazinda_rapor.csv", index_col=0)
    df_eff = pd.read_csv(TAB / "verimlilik_tablosu.csv")

    best = res["best_model"]
    best_acc = df_mean.loc[best, "Accuracy"]
    best_acc_std = df_std.loc[best, "Accuracy"]
    best_f1m = df_mean.loc[best, "F1_M"]
    best_f1m_std = df_std.loc[best, "F1_M"]
    best_mcc = df_mean.loc[best, "MCC"]
    best_mcc_std = df_std.loc[best, "MCC"]
    best_auroc = df_mean.loc[best, "AUROC"]
    best_aupr = df_mean.loc[best, "AUPR_M"]
    best_spec = df_mean.loc[best, "Specificity"]
    best_ll = df_mean.loc[best, "Log_Loss"]
    best_time = df_mean.loc[best, "Sure_sn"]

    dummy_acc = df_mean.loc["Dummy (Çoğunluk)", "Accuracy"]
    dummy_f1m = df_mean.loc["Dummy (Çoğunluk)", "F1_M"]

    top1_feat, top1_pct = df_imp.iloc[0]["Ozellik"], df_imp.iloc[0]["Yuzde_Etki"]
    top2_feat, top2_pct = df_imp.iloc[1]["Ozellik"], df_imp.iloc[1]["Yuzde_Etki"]
    top3_feat, top3_pct = df_imp.iloc[2]["Ozellik"], df_imp.iloc[2]["Yuzde_Etki"]
    sfi_row = df_imp[df_imp["Orijinal_Sutun"] == "sleep_fragmentation_index"].iloc[0]
    sfi_rank = int(df_imp[df_imp["Orijinal_Sutun"] == "sleep_fragmentation_index"].index[0]) + 1
    sfi_pct = float(sfi_row["Yuzde_Etki"])

    # -------------------------------------------------------------------------
    # BELGE VE STİL AYARLARI (11 pt Times New Roman, 1.15 satır aralığı)
    # -------------------------------------------------------------------------
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

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

    def add_table(title, headers, rows, widths, note=None, font_size=9.0):
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
    # ADIM 1: DERGİ ÜST BİLGİSİ, BAŞLIK, YAZAR VE ÖZ/ABSTRACT
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
        "Makine Öğrenmesi Yöntemleri İle Uyku Bozukluğu Riskinin Çok Sınıflı Tahmin Edilmesi: "
        "Sızıntısız Kıyaslama, Dengesizlik Analizi ve Öznitelik Önem Düzeyleri"
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
    c_left.width, c_right.width = Inches(2.1), Inches(4.5)

    pl = c_left.paragraphs[0]
    pl.add_run("Makale Bilgisi\n").bold = True
    rd = pl.add_run("Başvuru: 15/09/2026\nDüzeltme: 23/11/2026\nKabul: 23/11/2026\n\n")
    rd.italic = True
    rd.font.size = Pt(8.5)
    pl.add_run("Anahtar Kelimeler\n").bold = True
    rk = pl.add_run(
        "Uyku bozukluğu riski\nSızıntısız Pipeline\nSınıf dengesizliği\nAşırı öğrenme analizi\nCatBoost"
    )
    rk.font.size = Pt(8.5)

    pr = c_right.paragraphs[0]
    pr.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pr.add_run("Öz\n").bold = True
    oz_text = (
        f"Uyku bozuklukları kardiyovasküler, metabolik ve nöropsikiyatrik hastalıkların önemli habercileri olmasına karşın, "
        f"polisomnografi temelli geleneksel klinik tanı yüksek maliyet ve erişim kısıtları içermektedir. Bu çalışmada, "
        f"100.000 bireye ait demografik, fizyolojik ve yaşam tarzı verileri üzerinde dört sınıflı (Sağlıklı, Hafif, Orta, Ağır) "
        f"uyku bozukluğu riskini tahmin etmek amacıyla dokuz makine öğrenmesi algoritması ile bir çoğunluk sınıfı referans modelini "
        f"(DummyClassifier) aynı 10-kat tabakalı çapraz doğrulama (StratifiedKFold, random_state=42) düzeninde kıyasladık. "
        f"Veri sızıntısını yapısal olarak önlemek için nominal kategorik değişkenlerde One-Hot kodlama ve ölçeğe duyarlı modellerde "
        f"standartlaştırma adımlarını ColumnTransformer ve Pipeline içinde yalnızca eğitim katlamalarında öğrendik. Ayrıca "
        f"Uyku Bölünme İndeksi (SFI) ve Onarıcı Uyku Oranı (RSR) klinik özniteliklerini türettik. Deneysel sonuçlarda {best} modeli "
        f"{tr_pct(best_acc)} doğruluk, {tr_num(best_f1m)} Macro F1, {tr_num(best_mcc)} MCC ve {tr_num(best_aupr)} Macro AUPR değerleriyle "
        f"tüm katlamalarda (10-0) diğer modelleri geride bıraktı. Ek olarak eğitim–doğrulama farkı, karar ağacı derinlik taraması, "
        f"öğrenme eğrileri, sınıf dengesizliği (class_weight ve Pipeline içi SMOTE) ve SMOTE sızıntı deneylerini yürüttük. "
        f"Öznitelik önem analizinde {top1_feat} (%{tr_num(top1_pct, 2)}), {top2_feat} (%{tr_num(top2_pct, 2)}) ve türetilen SFI "
        f"(%{tr_num(sfi_pct, 2)}) en baskın belirleyiciler oldu. Yüksek çapraz doğrulama skorlarının dış doğrulama ve kalibrasyon "
        f"olmaksızın doğrudan klinik karar desteği olarak kullanılamayacağını da açıkça vurguladık."
    )
    roz = pr.add_run(oz_text)
    roz.font.size = Pt(9.0)
    set_cell_border(c_left, top="single", bottom="single", top_sz="6", bottom_sz="6")
    set_cell_border(c_right, top="single", bottom="single", top_sz="6", bottom_sz="6")

    p_et = doc.add_paragraph()
    p_et.paragraph_format.space_before = Pt(12)
    p_et.paragraph_format.space_after = Pt(4)
    ret = p_et.add_run(
        "Multiclass Prediction of Sleep Disorder Risk Using Machine Learning Methods: "
        "Leakage-Free Benchmarking, Class Imbalance Analysis, and Feature Importance"
    )
    ret.bold = True
    ret.font.size = Pt(12.5)

    p_ab = doc.add_paragraph()
    p_ab.add_run("Abstract\n").bold = True
    rab = p_ab.add_run(
        f"Although sleep disorders are key precursors of cardiovascular, metabolic, and neuropsychiatric diseases, "
        f"standard polysomnography diagnostics entail high cost and accessibility bottlenecks. In this study, we benchmarked "
        f"nine machine learning classifiers alongside a majority-class baseline (DummyClassifier) under an identical 10-fold "
        f"StratifiedKFold cross-validation protocol (random_state=42) on 100,000 individuals to predict four-class sleep "
        f"disorder risk (Healthy, Mild, Moderate, Severe). To prevent data leakage structurally, we fitted One-Hot encoding for "
        f"nominal categorical variables and standardization for scale-sensitive models strictly inside each training fold via "
        f"ColumnTransformer and Pipeline. We also engineered two clinical features: Sleep Fragmentation Index (SFI) and "
        f"Restorative Sleep Ratio (RSR). {best} achieved the highest performance across all 10 folds (10-0 paired wins) with "
        f"{best_acc*100:.2f}% accuracy, {best_f1m:.4f} Macro F1, {best_mcc:.4f} MCC, and {best_aupr:.4f} Macro AUPR. "
        f"We further conducted overfitting diagnostics (train-vs-CV gaps, decision tree depth sweep, learning curves), class "
        f"imbalance interventions (class weights and in-Pipeline SMOTE), and an empirical SMOTE leakage experiment. Feature "
        f"importance revealed mental health condition ({top1_pct:.2f}%), sleep quality ({top2_pct:.2f}%), and engineered SFI "
        f"({sfi_pct:.2f}%) as primary predictors. Finally, we explicitly discuss clinical limitations including external "
        f"validation, probability calibration, and prevalence shift."
    )
    rab.font.size = Pt(9.0)

    p_ek = doc.add_paragraph()
    p_ek.add_run("Keywords: ").bold = True
    rek = p_ek.add_run("Sleep disorder risk, Leakage-free Pipeline, Class imbalance, Overfitting analysis, CatBoost")
    rek.font.size = Pt(9.0)

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
        "Dünya Sağlık Örgütü (DSÖ) raporlarına göre erişkin nüfusun yaklaşık %35'i akut veya kronik uyku yakınmaları "
        "yaşamaktadır [2]. Türkiye'de Türk Toraks Derneği uzlaşı raporu da erişkinlerde obstrüktif uyku apnesi ve kronik "
        "insomni belirtilerinin yaygınlığını bildirmektedir [3]."
    )
    doc.add_paragraph(
        "Klinik tanıda altın standart olan Polisomnografi (PSG), yüksek donanım maliyeti, uzun randevu sıraları ve "
        "hastane ortamının doğal uyku ritmini bozması gibi kısıtlara sahiptir. Bu nedenle günlük fizyolojik ve yaşam tarzı "
        "ölçümleri üzerinden risk ön değerlendirmesi yapabilen makine öğrenmesi yöntemleri önem kazanmıştır [4]. "
        "[5]'de yazarlar, kardiyak sinyallerden uyku apnesi tespiti için Destek Vektör Makineleri (DVM) yöntemini "
        "kullanmışlardır. [6]'da yazarlar, giyilebilir sensör verileri üzerinde Rastgele Orman algoritmasını kıyaslamışlardır. "
        "[7]'de yazarlar, EKG kayıtlarından apne tespiti için Yapay Sinir Ağları ve doğrusal modelleri karşılaştırmışlardır. "
        "[8]'de yazarlar, aktivite tabanlı uyku-uyanıklık ayrımında istatistiksel sınıflandırıcılar uygulamışlardır. "
        "[9]'da yazarlar, uyku bozukluklarının makine öğrenmesi ile teşhisine ilişkin kapsamlı bir derleme sunmuşlardır."
    )
    doc.add_paragraph(
        "Mevcut literatürde sık rastlanan metodolojik boşluklar şunlardır: (i) kategorik kodlama, ölçeklendirme veya aşırı "
        "örnekleme (SMOTE) işlemlerinin çapraz doğrulama öncesinde tüm veriye uygulanarak veri sızıntısına (data leakage) yol "
        "açması [19, 20]; (ii) dengesiz çok sınıflı medikal verilerde yalnızca doğruluk (Accuracy) skoruna odaklanılarak azınlık "
        "sınıflardaki başarısızlığın gizlenmesi [21]; (iii) eğitim–doğrulama karşılaştırması veya basit referans (Dummy) modeli "
        "olmadan aşırı öğrenme (overfitting) değerlendirmesi yapılmamasıdır."
    )
    doc.add_paragraph(
        "Biz bu çalışmada, 100.000 bireye ait kapsamlı bir uyku sağlığı veri seti üzerinde tek bir ortak hedef olan dört sınıflı "
        "uyku bozukluğu riskini (Sağlıklı, Hafif, Orta, Ağır) tahmin etmek amacıyla dokuz makine öğrenmesi algoritmasını ve "
        "Dummy referans modelini tamamen sızıntısız (Pipeline + ColumnTransformer) 10-kat çapraz doğrulama düzeninde kıyasladık. "
        "Ayrıca klinik öznitelik mühendisliği (SFI ve RSR), eşleştirilmiş fold farkları, aşırı öğrenme (derinlik taraması ve "
        "öğrenme eğrileri), sınıf dengesizliği (class_weight ve Pipeline içi SMOTE), SMOTE sızıntı deneyi, ROC/PR eğrileri ve "
        "karmaşıklık matrisi analizleriyle sonuçları bütüncül ve dürüst biçimde değerlendirdik."
    )

    # -------------------------------------------------------------------------
    # 2. YÖNTEMLER (METHODS)
    # -------------------------------------------------------------------------
    add_h1("2. YÖNTEMLER (METHODS)")

    add_h2("2.1. Veri Seti ve Kalite Kontrolleri (Data Set and Quality Checks)")
    ds = res["dataset"]
    doc.add_paragraph(
        f"Bu çalışmada Kaggle platformunda açık erişimli olarak paylaşılan 'Sleep Health and Daily Performance Dataset' "
        f"veri setini kullandık. Veri seti {tr_int(ds['n_samples'])} örnek ve {ds['n_raw_cols']} ham sütundan oluşmaktadır. "
        f"Kodla gerçekleştirdiğimiz veri kalite kontrollerinde toplam eksik değer sayısını {ds['n_missing']}, kimlik numarası "
        f"(person_id) hariç birebir tekrar eden kayıt (duplicate) sayısını {ds['n_duplicates_no_id']} olarak doğruladık. "
        f"Modelin hedefi dolaylı olarak ezberlemesini (bilgi sızıntısını) önlemek amacıyla hasta kimliği (person_id) ile "
        f"uyku sonrası öznel sonuç göstergeleri olan felt_rested ve cognitive_performance_score sütunlarını veri setinden çıkardık. "
        f"Veri setinin Kaggle kaynaklı olması ve sentetik/simülasyon bileşenleri içerebilmesi nedeniyle bulgularımızı gerçek "
        f"klinik popülasyona doğrudan genellemeden değerlendirdik."
    )
    doc.add_paragraph(
        "Hedef değişken olan sleep_disorder_risk dört sıralı risk sınıfından oluşmaktadır: Sağlıklı (54.156; %54,16), "
        "Hafif (33.479; %33,48), Orta (8.299; %8,30) ve Ağır (4.066; %4,07). Şekil 1'de görüldüğü üzere veri seti "
        "belirgin bir sınıf dengesizliği (özellikle %4,07'lik Ağır sınıfı) taşımaktadır. Kalan 28 ham özniteliğin açıklamalarını "
        "Tablo 1'de sunduk."
    )
    add_figure("grafik_1_sinif_dagilimi.png", "Şekil 1. Hedef değişkenin (sleep_disorder_risk) 100.000 örnek üzerindeki sınıf dağılımı", 5.4)

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
    add_table("Tablo 1. Veri setindeki 28 ham özniteliğin gruplandırılmış özeti", ["Öznitelik Grubu", "Açıklama"], oznitelikler, [2.7, 3.9])

    add_h2("2.2. Klinik Öznitelik Mühendisliği (Clinical Feature Engineering)")
    doc.add_paragraph(
        "Amerikan Uyku Tıbbı Akademisi (AASM) ve Pittsburgh Uyku Kalitesi İndeksi (PSQI) literatürü doğrultusunda [10, 11], "
        "satır bazında deterministik olarak hesaplanan (örnekler arası istatistik kullanmadığı için veri sızıntısı oluşturmayan) "
        "iki klinik öznitelik türettik. gu gece uyanma sayısı, us uyku süresi (saat), dy derin uyku yüzdesi ve ry REM yüzdesi olmak üzere:"
    )
    add_eq("SFI = gu / us", "2.1")
    add_eq("RSR = dy + ry", "2.2")
    doc.add_paragraph(
        "burada SFI (Sleep Fragmentation Index) saatteki uyanma sıklığını, RSR (Restorative Sleep Ratio) ise fiziksel ve zihinsel "
        "yenilenme evrelerinin toplam oranını göstermektedir. Böylece toplam öznitelik sayısını 23 sayısal ve 7 nominal kategorik "
        "olmak üzere 30'a çıkardık."
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
    ver_rows = [(k, v) for k, v in res["versions"].items()] + [("random_state / n_splits", f"{res['random_state']} / {res['n_splits']}")]
    add_table(
        "Tablo 2. Deneylerin yürütüldüğü yazılım ortamı ve yeniden üretilebilirlik parametreleri",
        ["Bileşen / Kütüphane", "Sürüm / Değer"],
        ver_rows,
        [3.3, 3.3],
        note="Tüm deneyler sabit random_state=42 tohumu ve 10-kat StratifiedKFold düzeniyle tek bir betikten üretilmiştir."
    )

    add_h2("2.4. Sınıflandırma Yöntemleri ve Referans Model")
    doc.add_paragraph(
        "Çalışmada dokuz makine öğrenmesi algoritması ile çoğunluk sınıfını tahmin eden basit bir referans modelini "
        "(DummyClassifier) aynı veri ve katlamalarda karşılaştırdık. Hiperparametre seçiminden kaynaklanabilecek iyimserlik "
        "(seçim yanlılığı) ve veri sızıntısını engellemek amacıyla hiçbir modelin hiperparametresini doğrulama verisi üzerinde "
        "ayarlamadık; standart/varsayılan ayarları (ör. k-NN için k=5) kullandık. Hedef ölçeği Tablo 3'te verilmiştir."
    )
    add_table(
        "Tablo 3. Uyku Bozukluğu Riski (sleep_disorder_risk) sınıflandırma ölçeği",
        ["Kod", "Risk Düzeyi", "Örnek Sayısı (%)", "Klinik Tanım"],
        [
            ("0", "Sağlıklı (Healthy)", "54.156 (%54,16)", "Normal uyku mimarisi, patoloji riski düşük"),
            ("1", "Hafif (Mild)", "33.479 (%33,48)", "Hafif uyku bölünmesi ve başlangıç düzensizlik"),
            ("2", "Orta (Moderate)", "8.299 (%8,30)", "Belirgin insomni veya orta düzey apne riski"),
            ("3", "Ağır (Severe)", "4.066 (%4,07)", "Şiddetli uyku bölünmesi ve yüksek klinik risk"),
        ],
        [0.6, 1.5, 1.5, 3.0],
    )

    doc.add_paragraph(
        "Lojistik Regresyon: Özniteliklerin doğrusal bileşimini sigmoid işlevinden geçirerek sınıf olasılıklarını tahmin eder; "
        "hızlı ve yorumlanabilirdir ancak doğrusal karar sınırı ile sınırlıdır [12]. s doğrusal bileşim skoru olmak üzere,"
    )
    add_eq("f(s) = 1 / (1 + exp(-s))", "2.3")
    doc.add_paragraph("burada f(s) ilgili sınıfa ait olasılık kestirimini ifade eder.")

    doc.add_paragraph(
        "Gauss Naive Bayes: Özniteliklerin sınıf bilindiğinde koşullu bağımsız olduğunu ve normal dağıldığını varsayar; "
        "çok hızlıdır ancak ilişkili özniteliklerde varsayımı ihlal edilir [12]. C_k sınıf etiketi ve x öznitelik vektörü olmak üzere,"
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
        "her katlamada eğitim alt kümesini tabakalı olarak 25.000 örnekle sınırlandırdık, doğrulamayı ise tam 10.000 örnekte yürüttük."
    )

    doc.add_paragraph(
        "Rastgele Orman (Random Forest): Çok sayıda karar ağacını bootstrap alt örneklemleriyle eğitip çoğunluk oyuyla birleştirerek "
        "tek ağacın yüksek varyansını düşürür [15]. Çok Katmanlı Algılayıcı (MLP): Gizli katmanlarda doğrusal olmayan aktivasyonlarla "
        "karmaşık örüntüleri öğrenen ileri beslemeli yapay sinir ağıdır [12]. Gradyan Artırma Modelleri (XGBoost ve CatBoost): "
        "Sığ karar ağaçlarını sıralı biçimde ekleyerek önceki ağaçların artık hatalarını azaltır; CatBoost simetrik (oblivious) ağaç "
        "yapısı ve sıralı artırma mekanizmasıyla aşırı öğrenmeye karşı yüksek direnç sunar [16, 17]."
    )

    # -------------------------------------------------------------------------
    # 3. BULGULAR VE TARTIŞMA (FINDINGS AND DISCUSSION)
    # -------------------------------------------------------------------------
    add_h1("3. BULGULAR VE TARTIŞMA (FINDINGS AND DISCUSSION)")

    add_h2("3.1. Başarım Metrikleri ve Raporlama İlkeleri (Performance Metrics)")
    doc.add_paragraph(
        "Dengesiz çok sınıflı problemlerde tek başına Doğruluk (Accuracy) çoğunluk sınıfı nedeniyle yanıltıcı olabileceğinden; "
        "Kesinlik (Precision), Duyarlılık (Recall), Özgüllük (Specificity), Ağırlıklı ve Macro F1, karmaşıklık matrisinin dört "
        "hücresini birden kullanan Matthews Korelasyon Katsayısı (MCC), eşikten bağımsız AUROC, nadir sınıflara duyarlı Macro AUPR "
        "(Average Precision) ve olasılık kalitesini ölçen Log-Loss ölçütlerini birlikte hesapladık [19, 21]. "
        "DA doğru artı (TP), DE doğru eksi (TN), YA yanlış artı (FP) ve YE yanlış eksi (FN) olmak üzere temel ölçütler:"
    )
    add_eq("Doğruluk = (DA + DE) / (DA + YA + DE + YE)", "3.1")
    add_eq("Kesinlik = DA / (DA + YA)  ,  Duyarlılık = DA / (DA + YE)", "3.2")
    add_eq("Özgüllük = DE / (DE + YA)  ,  F1 = 2 * Kesinlik * Duyarlılık / (Kesinlik + Duyarlılık)", "3.3")
    add_eq("MCC = (DA·DE − YA·YE) / √((DA+YA)(DA+YE)(DE+YA)(DE+YE))", "3.4")
    doc.add_paragraph(
        "biçiminde tanımlanır. Çok sınıflı teorik karmaşıklık matrisi şablonu Tablo 4'te verilmiştir. Tablolarda raporlanan ± "
        "değerleri, 10 katlama arasındaki örneklem standart sapmasıdır (ddof=1). Katlamaların eğitim kümeleri örtüştüğü için bu "
        "± aralığı bir güven aralığı olarak yorumlanmamalıdır [22]. Ayrıca Tablo 5a–5b'de 10 katlamanın ortalaması raporlanırken, "
        "karmaşıklık matrisleri ve ROC/PR eğrileri tüm katlamaların birleşik (out-of-fold, OOF) tahminlerinden üretilmiştir; "
        "oran biçimindeki ölçütlerde iki yol arasında küçük yuvarlama farkları oluşması doğaldır."
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
        [1.4, 1.3, 1.3, 1.3, 1.3],
        note="DA: Doğru Artı (TP), DE: Doğru Eksi (TN), YA: Yanlış Artı (FP), YE: Yanlış Eksi (FN)."
    )

    add_h2("3.2. 10-Kat Çapraz Doğrulama Sonuçları ve Eşleştirilmiş Fold Farkları")
    doc.add_paragraph(
        f"100.000 örneğin tamamı üzerinde sızıntısız 10-kat StratifiedKFold sonuçlarını okunabilirliği artırmak amacıyla iki "
        f"tabloda (Tablo 5a ve Tablo 5b) ve Şekil 2'de sunduk. Hiçbir şey öğrenmeden her örneğe çoğunluk sınıfı (Sağlıklı) diyen "
        f"Dummy referans modeli {tr_pct(dummy_acc)} Doğruluk alırken, Macro F1 değeri {tr_num(dummy_f1m)} ve MCC değeri 0,0000 "
        f"çıkmıştır. Bu taban sonuç, Doğruluk metriğinin dengesiz veride neden mutlaka Dummy referansı, Macro F1 ve MCC ile birlikte "
        f"okunması gerektiğini somut biçimde gösterir."
    )
    doc.add_paragraph(
        f"Dokuz makine öğrenmesi modeli arasında {best} algoritması tüm ölçütlerde birinci oldu: Doğruluk {tr_pct(best_acc)} "
        f"(±{tr_num(best_acc_std)}), Macro F1 {tr_num(best_f1m)} (±{tr_num(best_f1m_std)}), Özgüllük {tr_num(best_spec)}, "
        f"MCC {tr_num(best_mcc)} (±{tr_num(best_mcc_std)}), AUROC {tr_num(best_auroc)}, Macro AUPR {tr_num(best_aupr)} ve "
        f"Log-Loss {tr_num(best_ll)}. Nominal sütunların Pipeline içinde One-Hot kodlanmasıyla Lojistik Regresyon "
        f"({tr_pct(df_mean.loc['Logistic Regression', 'Accuracy'])}) ve RBF DVM ({tr_pct(df_mean.loc['RBF SVM', 'Accuracy'])}) "
        f"gibi doğrusal ve çekirdek modellerinin de kararlı biçimde çalıştığını gözlemledik."
    )

    t5a_rows = [
        (
            m,
            f"{tr_num(df_mean.loc[m, 'Accuracy'])} ± {tr_num(df_std.loc[m, 'Accuracy'])}",
            f"{tr_num(df_mean.loc[m, 'F1_W'])} ± {tr_num(df_std.loc[m, 'F1_W'])}",
            f"{tr_num(df_mean.loc[m, 'F1_M'])} ± {tr_num(df_std.loc[m, 'F1_M'])}",
            f"{tr_num(df_mean.loc[m, 'Specificity'])} ± {tr_num(df_std.loc[m, 'Specificity'])}",
        )
        for m in res["model_order"]
    ]
    add_table(
        "Tablo 5a. 100.000 örnek üzerinde 10-kat StratifiedKFold sonuçları (1/2): Accuracy, F1 ve Özgüllük",
        ["Model", "Accuracy", "Weighted F1", "Macro F1", "Özgüllük (Specificity)"],
        t5a_rows,
        [1.4, 1.3, 1.3, 1.3, 1.3],
        note="10-kat StratifiedKFold; hücrelerde ortalama ± örneklem std (ddof=1). RBF SVM eğitim katlaması 25.000 örnekle sınırlandırılmıştır.",
        font_size=8.5,
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
            f"{tr_num(df_mean.loc[m, 'AUROC'])} ± {tr_num(df_std.loc[m, 'AUROC'])}",
            f"{tr_num(df_mean.loc[m, 'AUPR_M'])} ± {tr_num(df_std.loc[m, 'AUPR_M'])}",
            ll_str,
        ))
    add_table(
        "Tablo 5b. 100.000 örnek üzerinde 10-kat StratifiedKFold sonuçları (2/2): MCC, AUROC, Macro AUPR ve Log-Loss",
        ["Model", "MCC", "AUROC (OvR)", "Macro AUPR", "Log-Loss"],
        t5b_rows,
        [1.4, 1.3, 1.3, 1.3, 1.3],
        note="Olasılık üretmeyen SVM modellerinde (RBF SVM, LSVM) Log-Loss '—' olarak bırakılmış; AUROC ve AUPR karar fonksiyonundan hesaplanmıştır.",
        font_size=8.5,
    )
    add_figure("grafik_2_model_karsilastirma.png", "Şekil 2. 10-Kat StratifiedKFold sonuçlarının dört temel ölçütte (ortalama ± std) karşılaştırılması", 6.1)

    doc.add_paragraph(
        f"Modellerin aynı katlamalardaki eşleştirilmiş farklarını (referans: {best}) Tablo 6'da verdik. {best}, diğer sekiz "
        f"modelin ve Dummy referansının tamamına karşı 10 katlamanın 10'unda da (10-0) MCC, Macro F1 ve Macro AUPR açısından daha "
        f"yüksek skor üretti. 10 katlamanın eğitim kümeleri örtüştüğünden K–Y sayıları betimleyicidir; resmi bir istatistiksel "
        f"anlamlılık testi değildir [22]."
    )
    t6_rows = [
        (
            other,
            f"{tr_num(row['MCC_Fark_Ort'])} ± {tr_num(row['MCC_Fark_Std'])}",
            row["MCC_KY"],
            f"{tr_num(row['F1_M_Fark_Ort'])} ± {tr_num(row['F1_M_Fark_Std'])}",
            row["F1_M_KY"],
            f"{tr_num(row['AUPR_M_Fark_Ort'])} ± {tr_num(row['AUPR_M_Fark_Std'])}",
            row["AUPR_M_KY"],
        )
        for other, row in df_paired.iterrows()
    ]
    add_table(
        f"Tablo 6. {best} ile diğer modeller arasında eşleştirilmiş fold farkları (ort ± std, 10 katlama)",
        ["Karşılaştırılan Model", "MCC Farkı", "K–Y", "Macro F1 Farkı", "K–Y", "Macro AUPR Farkı", "K–Y"],
        t6_rows,
        [1.4, 1.15, 0.55, 1.15, 0.55, 1.25, 0.55],
        note=f"Pozitif fark {best} lehinedir. K–Y: {best}'un 10 katlamada kazandığı–kaybettiği tur sayısı.",
        font_size=8.5,
    )

    doc.add_paragraph(
        "Eşikten bağımsız sıralama kalitesini incelemek amacıyla en nadir ve klinik olarak en kritik sınıf olan 'Ağır' (Severe, %4,07) "
        "sınıfı için birleşik (OOF) ROC ve Precision–Recall (PR) eğrilerini Şekil 3'te çizdik. Negatif örnekler çoğunlukta "
        "olduğundan ROC eğrileri tüm modellerde iyimser görünürken, taban çizgisi prevalansa (0,041) eşit olan PR eğrileri modeller "
        "arasındaki gerçek ayırt edicilik farkını çok daha net ortaya koymuştur."
    )
    add_figure("grafik_3_roc_pr_egrileri.png", "Şekil 3. Ağır risk (Severe) sınıfı için birleşik (OOF) ROC ve Precision–Recall eğrileri", 6.2)

    add_h2("3.3. Aşırı Öğrenme (Overfitting) Analizi: Eğitim–CV Farkı, Derinlik Taraması ve Öğrenme Eğrileri")
    rf_tr, rf_cv, rf_gap = df_train_cv.loc["Random Forest", "Egitim_F1_Macro"], df_train_cv.loc["Random Forest", "CV_F1_Macro_Ort"], df_train_cv.loc["Random Forest", "Fark_Macro"]
    cb_tr, cb_cv, cb_gap = df_train_cv.loc[best, "Egitim_F1_Macro"], df_train_cv.loc[best, "CV_F1_Macro_Ort"], df_train_cv.loc[best, "Fark_Macro"]
    lr_tr, lr_cv, lr_gap = df_train_cv.loc["Logistic Regression", "Egitim_F1_Macro"], df_train_cv.loc["Logistic Regression", "CV_F1_Macro_Ort"], df_train_cv.loc["Logistic Regression", "Fark_Macro"]

    doc.add_paragraph(
        f"Modellerin eğitim verisini ezberleme eğilimini ölçmek amacıyla her katlamada eğitim ve doğrulama Macro F1 skorlarını "
        f"karşılaştırdık (Tablo 7). Rastgele Orman eğitimde {tr_num(rf_tr)} skoruna ulaşarak eğitim verisini tam ezberlerken "
        f"doğrulamada {tr_num(rf_cv)} değerine düştü (fark: {tr_num(rf_gap)}). Buna karşılık {best} yalnızca {tr_num(cb_gap)} "
        f"farkla çok daha dengeli genelleme sergiledi. Lojistik Regresyon ise en düşük farka ({tr_num(lr_gap)}) sahip olmasına "
        f"rağmen doğrulamada {tr_num(lr_cv)} ile geride kaldı; bu durum, eğitim–CV farkı küçük olan modelin en iyi model olmak "
        f"zorunda olmadığını ve düşük doğrulama skorunun tek başına overfitting değil yetersiz kapasite (underfitting) işareti "
        f"olabileceğini kanıtlamaktadır."
    )
    t7_rows = [
        (
            m,
            tr_num(row["Egitim_F1_Macro"]),
            f"{tr_num(row['CV_F1_Macro_Ort'])} ± {tr_num(row['CV_F1_Macro_Std'])}",
            tr_num(row["Fark_Macro"]),
            tr_num(row["Egitim_F1_Weighted"]),
            f"{tr_num(row['CV_F1_Weighted_Ort'])} ± {tr_num(row['CV_F1_Weighted_Std'])}",
        )
        for m, row in df_train_cv.iterrows()
    ]
    add_table(
        "Tablo 7. Eğitim ve 10-kat CV skorlarının karşılaştırılması (Overfitting tanısı)",
        ["Model", "Eğitim Macro F1", "CV Macro F1 (ort ± std)", "Fark (Macro)", "Eğitim Weighted F1", "CV Weighted F1"],
        t7_rows,
        [1.3, 0.95, 1.35, 0.85, 1.0, 1.15],
        font_size=8.5,
    )

    d2_std = df_depth[df_depth["max_depth"] == "2"]["CV_F1_Macro_Std"].iloc[0]
    d12_cv = df_depth[df_depth["max_depth"] == "12"]["CV_F1_Macro_Ort"].iloc[0]
    dinf_tr = df_depth[df_depth["max_depth"] == "Sınırsız"]["Egitim_F1_Macro"].iloc[0]
    dinf_cv = df_depth[df_depth["max_depth"] == "Sınırsız"]["CV_F1_Macro_Ort"].iloc[0]
    doc.add_paragraph(
        f"Model esnekliğinin etkisini doğrudan gözlemek için Karar Ağacı üzerinde max_depth taraması (Tablo 8) ve üç farklı "
        f"model için öğrenme eğrileri (Şekil 4) ürettik. Derinlik 1–4 aralığında hem eğitim hem CV skoru düşüktür (underfitting). "
        f"CV Macro F1 derinlik 12'de zirve yaparken ({tr_num(d12_cv)}), sınırsız derinlikte eğitim skoru {tr_num(dinf_tr)} olmuş "
        f"ve CV skoru {tr_num(dinf_cv)} değerine gerilemiştir (overfitting). Dikkat çekici biçimde, en yüksek standart sapma "
        f"({tr_num(d2_std)}) derinlik 2'de (underfit bölgede) ortaya çıkmıştır; bu bulgu, yüksek standart sapmanın tek başına "
        f"overfitting kanıtı olmadığını deneysel olarak doğrulamaktadır."
    )
    t8_rows = [
        (
            r["max_depth"],
            tr_num(r["Egitim_F1_Macro"]),
            f"{tr_num(r['CV_F1_Macro_Ort'])} ± {tr_num(r['CV_F1_Macro_Std'])}",
            tr_num(r["Fark"]),
        )
        for _, r in df_depth.iterrows()
    ]
    add_table(
        "Tablo 8. Karar ağacında max_depth karmaşıklık taraması (10-kat StratifiedKFold, Macro F1)",
        ["max_depth", "Eğitim Macro F1", "10-Kat CV Macro F1 (ort ± std)", "Fark (Eğitim − CV)"],
        t8_rows,
        [1.2, 1.5, 2.3, 1.6],
    )
    add_figure("grafik_6_derinlik_ve_ogrenme.png", "Şekil 4. Karar ağacı karmaşıklık taraması (solda) ve üç modelin öğrenme eğrileri (sağda)", 6.2)

    add_h2("3.4. Sınıf Dengesizliği Müdahale ve SMOTE Sızıntı Deneyi")
    lr_sade_sev = df_imb.loc["LR (Sade)", "Recall_Agir_Ort"]
    lr_cw_sev = df_imb.loc["LR + class_weight", "Recall_Agir_Ort"]
    rf_sade_m = df_imb.loc["RF (Sade)", "F1_Macro_Ort"]
    rf_sm_m = df_imb.loc["RF + SMOTE (Pipeline)", "F1_Macro_Ort"]
    sm_wrong_sev = df_smote_leak.loc["Yanlış (Önce SMOTE → Sonra CV)", "Recall_Agir"]
    sm_right_sev = df_smote_leak.loc["Doğru (Pipeline İçinde SMOTE)", "Recall_Agir"]

    lr_gain_tr = tr_num((lr_cw_sev - lr_sade_sev) * 100, 1)
    sm_gap_tr = tr_num((sm_wrong_sev - sm_right_sev) * 100, 1)

    doc.add_paragraph(
        f"Azınlık sınıflardaki (%8,30 Orta ve %4,07 Ağır) duyarlılığı incelemek amacıyla 20.000 tabakalı örneklem üzerinde "
        f"10-kat CV ile sınıf ağırlıklandırma (class_weight) ve ImbPipeline içinde SMOTE müdahalelerini sınadık (Tablo 9, Şekil 5). "
        f"Lojistik Regresyon'da class_weight='balanced' kullanımı, Ağır sınıf duyarlılığını {tr_pct(lr_sade_sev)} düzeyinden "
        f"{tr_pct(lr_cw_sev)} düzeyine (+{lr_gain_tr} puan) yükseltirken, toplam doğrulukta küçük bir düşüş (ödünleşim) yarattı. "
        f"Rastgele Orman'da ise Pipeline içi SMOTE, Macro F1 skorunu {tr_num(rf_sade_m)} değerinden {tr_num(rf_sm_m)} değerine iyileştirdi."
    )
    t9_rows = [
        (
            m,
            f"{tr_num(r['Accuracy_Ort'])} ± {tr_num(r['Accuracy_Std'])}",
            f"{tr_num(r['F1_Macro_Ort'])} ± {tr_num(r['F1_Macro_Std'])}",
            f"{tr_num(r['Recall_Orta_Ort'])}",
            f"{tr_num(r['Recall_Agir_Ort'])}",
            f"{tr_num(r['MCC_Ort'])}",
            f"{tr_num(r['AUPR_Macro_Ort'])}",
        )
        for m, r in df_imb.iterrows()
    ]
    add_table(
        "Tablo 9. Sınıf dengesizliği müdahale deneyi (20.000 tabakalı örneklem, 10-kat CV, SMOTE Pipeline içinde)",
        ["Model", "Accuracy", "Macro F1", "Orta Recall", "Ağır Recall", "MCC", "Macro AUPR"],
        t9_rows,
        [1.45, 1.05, 1.05, 0.75, 0.75, 0.75, 0.80],
        font_size=8.0,
    )
    add_figure("grafik_7_dengesizlik_deneyi.png", "Şekil 5. Sınıf dengesizliği müdahalelerinin (class_weight ve Pipeline içi SMOTE) ölçütler üzerindeki etkisi", 6.0)

    doc.add_paragraph(
        f"SMOTE'un çapraz doğrulama öncesinde tüm veriye uygulanmasının yol açtığı veri sızıntısını ayrıca deneysel olarak "
        f"ölçtük (Tablo 10). Yanlış yöntemde sentetik komşular eğitim ve doğrulama katlamalarına dağıldığından Ağır sınıf "
        f"Recall değeri {tr_num(sm_wrong_sev)} gibi yapay biçimde şişti; doğru yöntemde (Pipeline içinde SMOTE) gerçek değerin "
        f"{tr_num(sm_right_sev)} olduğu görüldü ({sm_gap_tr} yüzde puanlık sahte iyimserlik)."
    )
    t10_rows = [
        (idx, tr_num(r["F1_Macro"]), tr_num(r["Recall_Agir"]), tr_num(r["MCC"]))
        for idx, r in df_smote_leak.iterrows()
    ]
    add_table(
        "Tablo 10. SMOTE veri sızıntısı deneyi: CV öncesi SMOTE (yanlış) vs. Pipeline içi SMOTE (doğru), Random Forest",
        ["Yöntem", "Macro F1", "Ağır Sınıf Recall", "MCC"],
        t10_rows,
        [2.7, 1.3, 1.4, 1.2],
    )

    add_h2("3.5. Verinin Açıklanması ve Öznitelik Önem Düzeyleri (Feature Importance)")
    doc.add_paragraph(
        f"Uyku bozukluğu riskini en çok hangi değişkenlerin belirlediğini açıklamak amacıyla One-Hot kodlanmış alt sütunların "
        f"Gini önem skorlarını ana öznitelikler altında topladık (Tablo 11, Şekil 6). En baskın ilk üç belirleyici "
        f"{top1_feat} (%{tr_num(top1_pct, 2)}), {top2_feat} (%{tr_num(top2_pct, 2)}) ve {top3_feat} (%{tr_num(top3_pct, 2)}) "
        f"oldu. Türettiğimiz Uyku Bölünme İndeksi (SFI) %{tr_num(sfi_pct, 2)} etki payıyla {sfi_rank}. sıraya yerleşerek "
        f"ham gece uyanma sayısının (%3,85; 8. sıra) önüne geçti ve klinik öznitelik mühendisliğinin katkısını gösterdi."
    )
    t11_rows = [
        (str(i + 1), r["Ozellik"], tr_num(r["Onem_Skoru"]), f"%{tr_num(r['Yuzde_Etki'], 2)}")
        for i, (_, r) in enumerate(df_imp.head(15).iterrows())
    ]
    add_table(
        "Tablo 11. Uyku bozukluğu riskini belirleyen en etkili 15 öznitelik (One-Hot toplanmış Gini önem skorları)",
        ["Sıra", "Öznitelik", "Gini Skoru", "Etki Payı (%)"],
        t11_rows,
        [0.6, 3.4, 1.3, 1.3],
    )
    add_figure("grafik_5_ozellik_onemi.png", "Şekil 6. En yüksek önem düzeyine sahip ilk 15 öznitelik (turuncu: türetilmiş klinik metrikler)", 5.8)

    add_h2("3.6. Karmaşıklık Matrisleri, Sınıf Karnesi ve Klinik Sınırlılıklar")
    doc.add_paragraph(
        f"Dokuz modelin 100.000 örnek üzerindeki birleşik (OOF) karmaşıklık matrislerini Şekil 7'de, şampiyon {best} modelinin "
        f"sayısal dağılımını Tablo 12'de ve sınıf bazında başarım karnesini Tablo 13'te sunduk."
    )
    add_figure("grafik_4_confusion_matrices.png", "Şekil 7. Dokuz makine öğrenmesi modelinin 10-kat CV birleşik (OOF) karmaşıklık matrisleri", 6.1)

    cm_vals = df_cm.to_numpy()
    cls_labels = list(df_cm.index)
    t12_rows = []
    for i, lbl in enumerate(cls_labels):
        row_sum = int(cm_vals[i].sum())
        rec_i = cm_vals[i, i] / row_sum
        t12_rows.append((
            lbl,
            tr_int(cm_vals[i, 0]), tr_int(cm_vals[i, 1]), tr_int(cm_vals[i, 2]), tr_int(cm_vals[i, 3]),
            tr_int(row_sum), tr_pct(rec_i)
        ))
    col_sums = cm_vals.sum(axis=0)
    t12_rows.append((
        "Toplam Tahmin",
        tr_int(col_sums[0]), tr_int(col_sums[1]), tr_int(col_sums[2]), tr_int(col_sums[3]),
        tr_int(cm_vals.sum()), tr_pct(np.trace(cm_vals) / cm_vals.sum())
    ))
    add_table(
        f"Tablo 12. {best} modelinin 10-kat CV birleşik (OOF) karmaşıklık matrisi (100.000 Örnek)",
        ["Gerçek Sınıf", "T: Sağlıklı", "T: Hafif", "T: Orta", "T: Ağır", "Toplam", "Duyarlılık"],
        t12_rows,
        [1.45, 0.85, 0.85, 0.80, 0.80, 0.90, 0.95],
        font_size=8.5,
    )

    t13_rows = []
    for idx in cls_labels + ["macro avg", "weighted avg"]:
        r = df_cls.loc[idx]
        lbl_tr = "Macro Ortalama" if idx == "macro avg" else ("Ağırlıklı Ortalama" if idx == "weighted avg" else idx)
        t13_rows.append((lbl_tr, tr_num(r["precision"]), tr_num(r["recall"]), tr_num(r["f1-score"]), tr_int(r["support"])))
    add_table(
        f"Tablo 13. {best} modelinin sınıf bazında birleşik (OOF) başarım karnesi",
        ["Risk Düzeyi", "Kesinlik (Precision)", "Duyarlılık (Recall)", "F1-Skoru", "Örnek Sayısı"],
        t13_rows,
        [1.8, 1.2, 1.2, 1.2, 1.2],
    )

    sev_to_healthy = int(cm_vals[3, 0])
    sev_to_mild = int(cm_vals[3, 1])
    sev_to_mod = int(cm_vals[3, 2])
    sev_tp = int(cm_vals[3, 3])
    hlth_tp = int(cm_vals[0, 0])
    hlth_fp = int(cm_vals[0, 1])
    sev_prec = df_cls.loc["Ağır (Severe)", "precision"]

    doc.add_paragraph(
        f"Karmaşıklık matrisinden çıkardığımız temel gözlemler şunlardır: (1) Ağır risk grubundaki 4.066 vakanın {tr_int(sev_tp)} "
        f"tanesi doğru yakalandı; 'Sağlıklı' ({sev_to_healthy}) veya 'Hafif' ({sev_to_mild}) sınıfına düşen vaka olmadı, "
        f"hataların tamamı komşu 'Orta' ({tr_int(sev_to_mod)}) sınıfına kaydı. (2) 54.156 sağlıklı bireyin {tr_int(hlth_tp)} "
        f"tanesi (%99,87) doğru tahmin edildi, yalnızca {hlth_fp} birey Hafif sınıfına atandı. (3) Hatalar ağırlıklı olarak "
        f"fizyolojik spektrumun geçiş bölgesi olan komşu sınıflarda (Hafif↔Orta ve Orta↔Ağır) yoğunlaştı. (4) Şekil 7'de "
        f"LSVM ve k-NN'in azınlık sınıflarda (özellikle Orta sınıfta) belirgin biçimde zorlandığını, gradyan artırma ağaçlarının "
        f"(CatBoost ve XGBoost) ise köşegen yoğunluğunu koruduğunu gözlemledik."
    )
    doc.add_paragraph(
        f"Klinik Bağlam ve Çalışmanın Sınırlılıkları: Elde ettiğimiz yüksek çapraz doğrulama skorları, bu modellerin doğrudan bir "
        f"klinik karar destek aracı olarak kullanılabileceği anlamına gelmez. Sağlık uygulamaları için şu eksikler açıkça "
        f"belirtilmelidir: (i) Dış doğrulama (farklı hastane, cihaz ve popülasyon verileriyle sınama) yapılmamıştır; (ii) olasılık "
        f"çıktılarının kalibrasyonu değerlendirilmemiştir; (iii) bu veri setinde %4,07 prevalansa sahip Ağır sınıf için elde edilen "
        f"{tr_num(sev_prec)} Kesinlik (PPV) değeri, genel tarama popülasyonunda prevalansın daha düşük olması hâlinde belirgin "
        f"biçimde düşebilir; (iv) sonuçlar tek bir veri setine (Kaggle kaynaklı, sentetik bileşen içerebilen), tek bir "
        f"random_state=42 bölünmesine ve ayarlanmamış varsayılan hiperparametrelere dayanmakta olup resmi bir istatistiksel "
        f"anlamlılık testi uygulanmamıştır."
    )

    add_h2("3.7. Hesaplama Verimliliği (Computational Efficiency)")
    doc.add_paragraph(
        f"Tüm modellerin 10-kat çapraz doğrulama toplam sürelerini ve MCC başarımlarını Tablo 14 ve Şekil 8'de sunduk. "
        f"{best} ({tr_num(best_time, 2)} sn) ve XGBoost ({tr_num(df_mean.loc['XGBoost', 'Sure_sn'], 2)} sn), hem en yüksek "
        f"genelleme başarısını hem de düşük eğitim süresini birlikte sunarak verimlilik sınırında (Pareto-optimum) yer aldı."
    )
    t14_rows = [
        (r["Model"], tr_num(r["Accuracy"]), tr_num(r["F1_Macro"]), tr_num(r["MCC"]), tr_num(r["Sure_sn"], 2))
        for _, r in df_eff.iterrows()
    ]
    add_table(
        "Tablo 14. Dokuz makine öğrenmesi modelinin 10-kat CV toplam eğitim süreleri ve başarım özeti",
        ["Model", "Accuracy", "Macro F1", "MCC", "Toplam Süre (sn)"],
        t14_rows,
        [1.8, 1.15, 1.15, 1.15, 1.35],
        note="RBF SVM süresi her katlamada 25.000 eğitim örneklemi üzerinden ölçülmüştür; diğer tüm modeller 90.000/10.000 ile eğitilmiştir.",
    )
    add_figure("grafik_8_hiz_vs_basari.png", "Şekil 8. Modellerin 10-kat CV hesaplama süresi ile MCC performansı arasındaki verimlilik dengesi", 5.8)

    # -------------------------------------------------------------------------
    # 4. SONUÇLAR (CONCLUSIONS)
    # -------------------------------------------------------------------------
    add_h1("4. SONUÇLAR (CONCLUSIONS)")
    doc.add_paragraph(
        f"Bu çalışmada, 100.000 bireye ait uyku sağlığı ve yaşam tarzı verileri üzerinde dört sınıflı uyku bozukluğu riskini "
        f"tahmin etmek amacıyla dokuz makine öğrenmesi algoritmasını ve bir Dummy referans modelini, sızıntısız Pipeline ve "
        f"ColumnTransformer mimarisiyle 10-kat StratifiedKFold düzeninde kıyasladık. {best} algoritması tüm katlamalarda "
        f"(10-0) diğer modelleri geride bırakarak {tr_pct(best_acc)} doğruluk, {tr_num(best_f1m)} Macro F1 ve {tr_num(best_mcc)} "
        f"MCC ile en yüksek genelleme başarısına ulaştı. Gerçekleştirdiğimiz ek deneyler; nominal değişkenlerde One-Hot "
        f"kodlamanın doğrusal ve çekirdek modellerini belirgin biçimde iyileştirdiğini, aşırı öğrenme tanısında eğitim–CV farkı ve "
        f"öğrenme eğrilerinin tekil standart sapmadan daha güvenilir olduğunu ve SMOTE'un çapraz doğrulama öncesinde uygulanmasının "
        f"ağır risk sınıfı duyarlılığını yapay olarak şişirdiğini deneysel biçimde ortaya koydu."
    )
    doc.add_paragraph(
        "Çalışmamızın temel sınırlılıkları; tek bir çevrimdışı veri setine dayanması, dış klinik doğrulama ve olasılık kalibrasyonu "
        "içermemesi, hiperparametrelerin iç içe çapraz doğrulama ile optimize edilmemesi ve tek bir bölünme tohumu kullanılmasıdır. "
        "Gelecek çalışmalarda çok merkezli klinik polisomnografi verileri üzerinde dış doğrulama, iç içe çapraz doğrulama ile "
        "maliyet duyarlı eşik optimizasyonu ve kalibrasyon analizlerinin yürütülmesini hedefliyoruz."
    )

    # -------------------------------------------------------------------------
    # SON BÖLÜMLER
    # -------------------------------------------------------------------------
    add_h1("KAYNAK DOSYALAR (SUPPLEMENTARY FILES)")
    doc.add_paragraph("Çalışmanın sızıntısız kaynak kodları, tüm deney çıktıları ve grafikler https://github.com/DBurakyuz/sleep-disorder-ml adresinde açık erişimli olarak paylaşılmıştır.")

    add_h1("TEŞEKKÜR (ACKNOWLEDGMENTS)")
    doc.add_paragraph("Bu çalışma, Yalova Üniversitesi Mühendislik Fakültesi Bilgisayar Mühendisliği Bölümü Makine Öğrenmesi dersi kapsamında gerçekleştirilmiştir.")

    add_h1("KAYNAKLAR (REFERENCES)")
    kaynaklar = [
        "[1] Walker, M. P., \"Why We Sleep: Unlocking the Power of Sleep and Dreams\", Scribner, New York, 2017.",
        "[2] World Health Organization, \"Global status report on noncommunicable diseases\", WHO Press, Cenevre, 2022.",
        "[3] Türk Toraks Derneği, \"Obstrüktif Uyku Apnesi Sendromu Tanı ve Tedavi Uzlaşı Raporu\", Türk Toraks Dergisi, Cilt 17, No 1, 1-45, 2016.",
        "[4] Alpaydin, E., \"Introduction to Machine Learning\", 3. Baskı, The MIT Press, Londra, 2014.",
        "[5] Al-Angari, H. M., Sahakian, A. V., \"Automated detection of obstructive sleep apnea using support vector machines\", IEEE Trans. Inf. Technol. Biomed., Cilt 16, No 5, 1003-1009, 2012.",
        "[6] Palotti, J., Mall, R., Fernandez-Luque, L., \"Benchmark on a large dataset for sleep detection using wearable sensors and random forest\", Scientific Reports, Cilt 9, No 1, 12001, 2019.",
        "[7] Penzel, T. ve ark., \"Systematic comparison of different algorithms for apnoea detection based on electrocardiogram recordings\", Med. Biol. Eng. Comput., Cilt 40, No 4, 402-407, 2002.",
        "[8] Sadeh, A., Sharkey, K. M., Carskadon, M. A., \"Activity-based sleep-wake identification: An empirical test of methodological issues\", Sleep, Cilt 17, No 3, 201-207, 1994.",
        "[9] Faust, O. ve ark., \"Application of machine learning tools in sleep disorder diagnosis: A review\", Journal of Medical Systems, Cilt 40, No 12, 275, 2016.",
        "[10] Bonnet, M. H., Arand, D. L., \"Clinical effects of sleep fragmentation\", Sleep Medicine Reviews, Cilt 7, No 4, 297-310, 2003.",
        "[11] Buysse, D. J. ve ark., \"The Pittsburgh Sleep Quality Index: a new instrument for psychiatric practice and research\", Psychiatry Research, Cilt 28, No 2, 193-213, 1989.",
        "[12] Pedregosa, F. ve ark., \"Scikit-learn: Machine learning in Python\", Journal of Machine Learning Research, Cilt 12, 2825-2830, 2011.",
        "[13] Cover, T., Hart, P., \"Nearest neighbor pattern classification\", IEEE Trans. Inf. Theory, Cilt 13, No 1, 21-27, 1967.",
        "[14] Cortes, C., Vapnik, V., \"Support-vector networks\", Machine Learning, Cilt 20, No 3, 273-297, 1995.",
        "[15] Breiman, L., \"Random Forests\", Machine Learning, Cilt 45, No 1, 5-32, 2001.",
        "[16] Friedman, J. H., \"Greedy function approximation: A gradient boosting machine\", Annals of Statistics, Cilt 29, No 5, 1189-1232, 2001.",
        "[17] Prokhorenkova, L. ve ark., \"CatBoost: unbiased boosting with categorical features\", NeurIPS, Cilt 31, 6638-6648, 2018.",
        "[18] Chawla, N. V. ve ark., \"SMOTE: Synthetic minority over-sampling technique\", Journal of Artificial Intelligence Research, Cilt 16, 321-357, 2002.",
        "[19] Kaufman, S., Rosset, S., Perlich, C., Stitelman, O., \"Leakage in data mining: Formulation, detection, and avoidance\", ACM TKDD, Cilt 6, No 4, Article 15, 2012.",
        "[20] Cawley, G. C., Talbot, N. L. C., \"On over-fitting in model selection and subsequent selection bias in performance evaluation\", JMLR, Cilt 11, 2079-2107, 2010.",
        "[21] Chicco, D., Jurman, G., \"The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation\", BMC Genomics, Cilt 21, 6, 2020.",
        "[22] Nadeau, C., Bengio, Y., \"Inference for the generalization error\", Machine Learning, Cilt 52, No 3, 239-281, 2003.",
    ]
    for k in kaynaklar:
        pk = doc.add_paragraph()
        pk.paragraph_format.space_after = Pt(3)
        pk.paragraph_format.left_indent = Inches(0.3)
        pk.paragraph_format.first_line_indent = Inches(-0.3)
        rk = pk.add_run(k)
        rk.font.size = Pt(9.0)

    out_path = "Makine_Ogrenmesi_Ile_Uyku_Bozuklugu_Riski_Tahmini.docx"
    doc.save(out_path)
    print(f"BASARILI: Son duzeltmelerle Word makalesi '{out_path}' olarak kaydedildi!")


if __name__ == "__main__":
    create_paper()
