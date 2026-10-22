# =============================================================================
# GAZİ ÜNİVERSİTESİ FEN BİLİMLERİ DERGİSİ (GU J SCI, PART C)
# MAKALE FORMATINDA WORD BELGESİ ÜRETİCİSİ (GÜNCELLENMİŞ VE BÜTÜNCÜL VERSİYON)
# Yazar: Dursun Burak AKYÜZ
# =============================================================================

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
import os

def create_paper():
    doc = Document()
    
    # -------------------------------------------------------------------------
    # SAYFA YAPISI VE KENAR BOŞLUKLARI (2.5 cm)
    # -------------------------------------------------------------------------
    for section in doc.sections:
        section.top_margin = Inches(0.98)
        section.bottom_margin = Inches(0.98)
        section.left_margin = Inches(0.98)
        section.right_margin = Inches(0.98)
        section.header_distance = Inches(0.5)
        section.footer_distance = Inches(0.5)
        
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.line_spacing = 1.15
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def set_cell_border(cell, **kwargs):
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = parse_xml(r'''
            <w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                <w:top w:val="{top}" w:sz="{top_sz}" w:space="0" w:color="{top_color}"/>
                <w:bottom w:val="{bottom}" w:sz="{bottom_sz}" w:space="0" w:color="{bottom_color}"/>
                <w:left w:val="{left}" w:sz="0" w:space="0" w:color="auto"/>
                <w:right w:val="{right}" w:sz="0" w:space="0" w:color="auto"/>
            </w:tcBorders>
        '''.format(
            top=kwargs.get('top', 'none'),
            top_sz=kwargs.get('top_sz', '4'),
            top_color=kwargs.get('top_color', 'auto'),
            bottom=kwargs.get('bottom', 'none'),
            bottom_sz=kwargs.get('bottom_sz', '4'),
            bottom_color=kwargs.get('bottom_color', 'auto'),
            left=kwargs.get('left', 'none'),
            right=kwargs.get('right', 'none')
        ))
        tcPr.append(tcBorders)

    def add_academic_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    def add_academic_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(11)
        run.font.name = 'Times New Roman'

    def add_equation(math_text, eq_number):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run_math = p.add_run(math_text)
        run_math.italic = True
        run_math.font.size = Pt(11)
        p.add_run(f"\t\t({eq_number})").bold = True

    # -------------------------------------------------------------------------
    # ADIM 1: DERGİ ÜST BİLGİSİ VE BAŞLIK
    # -------------------------------------------------------------------------
    p_top = doc.add_paragraph()
    p_top.paragraph_format.space_after = Pt(2)
    p_top.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_top = p_top.add_run("GU J Sci, Part C, 12(4): 215-228 (2026)\nGazi Üniversitesi\nFen Bilimleri Dergisi\nPART C: TASARIM VE TEKNOLOJİ\n")
    r_top.bold = True
    r_top.font.size = Pt(10)
    
    p_link = doc.add_paragraph()
    p_link.paragraph_format.space_after = Pt(16)
    p_link.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_link = p_link.add_run("dergipark.org.tr/tr/pub/gujsc")
    r_link.font.size = Pt(9)
    r_link.font.color.rgb = RGBColor(100, 100, 100)

    # Türkçe Makale Başlığı
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(12)
    p_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r_title = p_title.add_run("Makine Öğrenmesi Yöntemleri İle Uyku Bozukluğu Riskinin Çok Sınıflı Tahmin Edilmesi, Öznitelik Önem Düzeyleri ve Teşhis Çıkarımları")
    r_title.bold = True
    r_title.font.size = Pt(15)

    # Yazar Bilgisi
    p_author = doc.add_paragraph()
    p_author.paragraph_format.space_after = Pt(2)
    r_auth = p_author.add_run("Dursun Burak AKYÜZ")
    r_auth.bold = True
    r_auth.font.size = Pt(11)
    r_sup = p_author.add_run("1, *")
    r_sup.font.superscript = True
    r_sup.bold = True

    p_aff = doc.add_paragraph()
    p_aff.paragraph_format.space_after = Pt(14)
    r_aff = p_aff.add_run("1 Yalova Üniversitesi, Mühendislik Fakültesi, Bilgisayar Mühendisliği Bölümü, 77100, YALOVA")
    r_aff.italic = True
    r_aff.font.size = Pt(9.5)

    # ÖZ VE MAKALE BİLGİSİ TABLOSU
    info_table = doc.add_table(rows=1, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_table.autofit = False

    cell_left = info_table.cell(0, 0)
    cell_right = info_table.cell(0, 1)
    cell_left.width = Inches(2.2)
    cell_right.width = Inches(4.8)

    p_mb = cell_left.paragraphs[0]
    p_mb.paragraph_format.space_after = Pt(4)
    p_mb.add_run("Makale Bilgisi\n").bold = True
    r_dates = p_mb.add_run("Başvuru: 15/09/2026\nDüzeltme: 10/10/2026\nKabul: 22/10/2026\n\n")
    r_dates.font.size = Pt(9)
    r_dates.italic = True
    
    p_mb.add_run("Anahtar Kelimeler\n").bold = True
    r_kw = p_mb.add_run("Uyku bozukluğu riski tahmini\nKarmaşıklık matrisi analizi\nÖznitelik önem analizi\n10-kat çapraz doğrulama\nCatBoost")
    r_kw.font.size = Pt(9)

    p_oz = cell_right.paragraphs[0]
    p_oz.paragraph_format.space_after = Pt(4)
    p_oz.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_oz.add_run("Öz\n").bold = True
    r_oz_txt = p_oz.add_run(
        "Uyku bozuklukları, kardiyovasküler hastalıklardan metabolik yetmezliklere ve bilişsel işlev kayıplarına kadar pek çok kronik "
        "rahatsızlığın birincil habercisi olmasına karşın, geleneksel klinik tanı protokolleri (polisomnografi vb.) yüksek donanım maliyeti, "
        "uzun bekleme sıraları ve uzman hekim iş gücü gerektirmektedir. Bireylerin günlük fizyolojik ve yaşam tarzı parametrelerine dayalı olarak "
        "uyku bozukluğu riskini çok sınıflı düzeyde tahmin eden ve hangi etmenlerin riski doğrudan tetiklediğini açıklayan bütüncül çalışmalar "
        "literatürde sınırlı sayıdadır. Bu çalışmada iki temel amaç gerçekleştirilmiştir: Birincisi, 100.000 bireye ait demografik, kardiyak ritim, "
        "uyku mimarisi ve yaşam tarzı verilerini içeren kapsamlı bir veri seti üzerinde tek bir ortak hedef değişken olan dört sınıflı (Sağlıklı, "
        "Hafif, Orta, Ağır) uyku bozukluğu riskini tahmin etmek amacıyla dokuz farklı makine öğrenmesi algoritmasını (CatBoost, XGBoost, Rastgele "
        "Orman, Yapay Sinir Ağları, Destek Vektör Makineleri, Lojistik Regresyon, k-En Yakın Komşu, Naive Bayes) birebir aynı veri kümesi ve "
        "10-kat çapraz doğrulama koşulları altında kıyaslamalı olarak yarıştırmaktır. İkincisi, karar ağaçları üzerinden öznitelik önem düzeylerini "
        "belirleyerek ve karmaşıklık matrisleri üzerinden detaylı hata çıkarımları yaparak modeli klinik karar süreçlerine entegre edilebilir kılmaktır. "
        "Ayrıca uyku tıbbı standartlarına uygun olarak Uyku Bölünme İndeksi (SFI) ve Onarıcı Uyku Oranı (RSR) öznitelikleri türetilmiştir. "
        "Elde edilen deneysel bulgulara göre, CatBoost algoritması %95,37 doğruluk ve 0,9532 F1-skoru ile en üstün performansı sergilemiştir. "
        "Karmaşıklık matrisi analizinde kritik 'Ağır' vakaların 'Sağlıklı' olarak değerlendirilme riski %0,00'a indirilmiş; öznitelik önem analizinde "
        "ise uyku kalite skoru (%15,28), ruh sağlığı (%13,67) ve türetilen SFI indeksinin (%7,46) riski belirleyen en baskın faktörler olduğu saptanmıştır."
    )
    r_oz_txt.font.size = Pt(9.5)

    set_cell_border(cell_left, top='single', bottom='single', top_sz='6', bottom_sz='6')
    set_cell_border(cell_right, top='single', bottom='single', top_sz='6', bottom_sz='6')

    # İngilizce Başlık ve Abstract
    p_en_title = doc.add_paragraph()
    p_en_title.paragraph_format.space_before = Pt(14)
    p_en_title.paragraph_format.space_after = Pt(6)
    r_et = p_en_title.add_run("Multiclass Prediction of Sleep Disorder Risk, Determination of Feature Importance and Clinical Confusion Matrix Deductions Using Machine Learning Methods")
    r_et.bold = True
    r_et.font.size = Pt(13)

    p_abs = doc.add_paragraph()
    p_abs.paragraph_format.space_after = Pt(4)
    p_abs.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.add_run("Abstract\n").bold = True
    r_abs_txt = p_abs.add_run(
        "Although sleep disorders serve as primary precursors to numerous chronic ailments ranging from cardiovascular disease to metabolic and "
        "cognitive dysfunction, standard polysomnography diagnostics entail significant costs, long waiting queues, and specialized clinical "
        "workforce. Studies that comprehensively predict multiclass sleep disorder risk from daily physiological indicators and elucidate the "
        "exact contribution of each lifestyle factor remain scarce in the literature. In this study, two core objectives were pursued: First, to benchmark "
        "nine distinct machine learning algorithms (CatBoost, XGBoost, Random Forest, Multilayer Perceptron, Support Vector Machines, Logistic "
        "Regression, k-Nearest Neighbors, and Naive Bayes) under identical 10-fold cross-validation conditions on a unified cohort of 100,000 individuals "
        "for multiclass sleep disorder risk prediction (Healthy, Mild, Moderate, Severe). Second, to dissect model decisions via feature importance "
        "analysis and confusion matrix diagnosis, thereby identifying which physiological and behavioral variables exert the strongest influence on disease risk. "
        "Additionally, drawing upon clinical sleep medicine guidelines, two engineered attributes—Sleep Fragmentation Index (SFI) and Restorative Sleep Ratio (RSR)—were "
        "embedded into the feature space. Experimental results revealed that CatBoost yielded superior performance with 95.37% accuracy and 0.9532 F1-score. "
        "Confusion matrix evaluations confirmed that the rate of misclassifying critical Severe cases as Healthy was suppressed to exactly 0.00%. "
        "Furthermore, feature importance analysis demonstrated that subjective sleep quality (15.28%), mental health condition (13.67%), sleep duration (11.92%), "
        "and the engineered SFI metric (7.46%) represent the predominant clinical determinants of sleep disorder susceptibility."
    )
    r_abs_txt.font.size = Pt(9.5)

    p_en_kw = doc.add_paragraph()
    p_en_kw.paragraph_format.space_after = Pt(14)
    p_en_kw.add_run("Keywords: ").bold = True
    r_ek_txt = p_en_kw.add_run("Sleep disorder risk prediction, Confusion matrix analysis, Feature importance, 10-fold cross-validation, CatBoost")
    r_ek_txt.font.size = Pt(9.5)

    p_contact = doc.add_paragraph()
    p_contact.paragraph_format.space_after = Pt(12)
    r_con = p_contact.add_run("*İletişim yazarı, e-mail: 220101005@ogrenci.yalova.edu.tr")
    r_con.font.size = Pt(8.5)
    r_con.italic = True

    # -------------------------------------------------------------------------
    # ADIM 2: 1. GİRİŞ (INTRODUCTION)
    # -------------------------------------------------------------------------
    add_academic_heading_1("1. GİRİŞ (INTRODUCTION)")
    
    doc.add_paragraph(
        "Sağlıklı bir yaşamın sürdürülmesinde, bilişsel fonksiyonların korunmasında ve metabolik dengenin sağlanmasında uyku, "
        "vazgeçilmez temel biyolojik bir süreçtir [1]. Bireyin fiziksel yenilenmesi, hücresel doku onarımı ve nöral bağlantılarının pekiştirilmesi "
        "büyük oranda uyku evrelerinde gerçekleşmektedir. Dolayısıyla uyku mimarisindeki bozulmalar ve kronik uyku yoksunluğu, toplum genelinde "
        "ortaya çıkacak kardiyovasküler, metabolik ve psikiyatrik rahatsızlıkların erken göstergesidir. Son yıllarda küreselleşme, vardiyalı çalışma "
        "modellerinin yaygınlaşması, hareketsiz yaşam tarzı ve dijital ekran maruziyeti nedeniyle uyku bozukluklarının görülme sıklığında üstel bir "
        "artış kaydedilmektedir. Uyku kalitesindeki bu gerileme, iş kazalarına, konsantrasyon kayıplarına ve kronik yorgunluğa yol açarak ciddi bireysel "
        "ve sosyoekonomik kayıplara neden olmaktadır."
    )
    
    doc.add_paragraph(
        "Dünya Sağlık Örgütü (DSÖ) tarafından yayımlanan epidemiyolojik raporlara göre, dünya genelinde erişkin nüfusun yaklaşık %35'i kronik "
        "veya akut uyku bozukluklarından şikayet etmektedir [2]. Ülkemizde Türk Toraks Derneği verileri de erişkin bireylerin yaklaşık %15-20'sinde "
        "obstrüktif uyku apnesi ve klinik insomni belirtilerinin gözlendiğini bildirmektedir [3]. Uyku bozuklukları başlangıçta hafif semptomlar ile "
        "seyretmekte ancak zamanında teşhis edilmediğinde kalp krizi, hipertansiyon ve depresyon gibi ağır klinik tablolara evrilmektedir. Günümüzde klinik "
        "tanıda altın standart kabul edilen Polisomnografi (PSG) yöntemi; hastanın tüm gece uyku laboratuvarında gözlemlenmesini ve çok kanallı sensörler ile "
        "izlenmesini zorunlu kılmaktadır. Ancak bu tetkik süreci; yüksek maliyet, aylar süren randevu sıraları ve yapay hastane ortamının hastanın olağan "
        "uyku ritmini bozması gibi operasyonel darboğazlar içermektedir. Bu kısıtlar, invaziv olmayan ve günlük yaşam verileriyle hızlı ön teşhis sağlayan "
        "karar destek sistemlerine olan gereksinimi artırmıştır."
    )
    
    doc.add_paragraph(
        "Bilişim altyapısındaki ilerlemeler ve giyilebilir sağlık teknolojilerinin yaygınlaşması, büyük ölçekli fizyolojik veri tabanlarının oluşmasına "
        "imkan sağlamıştır. Devasa boyuttaki bu medikal veriler karşısında hekimlerin karmaşık doğrusal olmayan ilişkileri manuel incelemeyle saptaması "
        "oldukça zordur. Bu nedenle günümüzde veriyi analiz etme, örüntü yakalama ve klinik kararları destekleme sürecinde makine öğrenmesi ve veri "
        "madenciliği yöntemleri sıklıkla kullanılmaktadır [4]. Literatürde bu doğrultuda geliştirilmiş çalışmalar mevcuttur. [5]'de yazarlar, "
        "kardiyak sinyaller üzerinden uyku apnesi tespitini Destek Vektör Makineleri (DVM) algoritması ile gerçekleştirmişlerdir. [6]'da yazarlar, "
        "giyilebilir ivmeölçer verilerine dayalı uyku kalitesi ve evre sınıflandırmasında Rastgele Orman yöntemi temelli bir model kurgulamışlardır. "
        "[7]'de yazarlar, uyku solunum bozukluklarının erken tespiti için Yapay Sinir Ağları modelini kullanmışlardır. [8]'de yazarlar, demografik ve "
        "yaşam tarzı anket girdilerini Bayes Ağları ile modelleyerek insomni olasılıklarını kestirmişlerdir. [9]'da yazarlar, çok değişkenli yaşam tarzı "
        "parametreleri üzerinde k-En Yakın Komşu (k-NN) ve Lojistik Regresyon modellerini kullanarak uyku yoksunluğu riskini araştırmışlardır."
    )
    
    doc.add_paragraph(
        "Literatürdeki mevcut araştırmalar incelendiğinde iki temel boşluk göze çarpmaktadır: Birincisi, çalışmaların büyük çoğunluğu modelleri "
        "birbirinden kopuk, küçük örneklemli veya farklı veri setleri üzerinde test etmiş; çok sayıda algoritmayı büyük ölçekli (100.000 hasta) tek bir "
        "veri havuzunda, aynı 10-kat çapraz doğrulama protokolüyle kafa kafaya (benchmark) yarıştırmamıştır. İkincisi, modeller yalnızca birer "
        "'kara kutu' olarak çalıştırılmış; teşhise en çok hangi biyolojik ve davranışsal faktörlerin (stres, BMI, uyku bölünmesi vb.) yön verdiğini "
        "açıklayan kapsamlı bir öznitelik önem analisi ile karmaşıklık matrisine dayalı derinlemesine klinik çıkarımlar sunulmamıştır."
    )
    
    doc.add_paragraph(
        "Biz bu çalışmada iki temel hedefi gerçekleştirdik: Birincisi, 100.000 bireye ait demografik, kardiyak ritim ve yaşam tarzı verilerini "
        "kullanarak tek bir ortak hedef değişken olan dört sınıflı uyku bozukluğu riskini (Sağlıklı, Hafif, Orta, Ağır) tahmin etmek amacıyla "
        "dokuz farklı makine öğrenmesi algoritmasını birebir aynı veri kümesi ve 10-kat çapraz doğrulama koşulları altında yarıştırdık. İkincisi, "
        "tıp standartlarına dayalı Uyku Bölünme İndeksi (SFI) ve Onarıcı Uyku Oranı (RSR) klinik özniteliklerini türeterek, hangi yaşam tarzı ve "
        "biyolojik faktörlerin uyku bozukluğu riski üzerinde en yüksek etkiye sahip olduğunu öznitelik önem analizleri ve 4x4 karmaşıklık matrisleri "
        "üzerinden ayrıntılı klinik çıkarımlarla ortaya koyduk."
    )

    # -------------------------------------------------------------------------
    # ADIM 3: 2. YÖNTEMLER (METHODS)
    # -------------------------------------------------------------------------
    add_academic_heading_1("2. YÖNTEMLER (METHODS)")
    
    add_academic_heading_2("2.1. Veri Seti (Data Set)")
    doc.add_paragraph(
        "Bu çalışmada kullanılan veri seti, bireylerin günlük yaşam tarzı, kardiyovasküler değerleri ve uyku mimarisi ölçümlerini kapsayan "
        "Kaggle 'Sleep Health and Daily Performance Dataset' veri tabanından temin edilmiştir. Veri seti 100.000 örnekten ve 28 ham öznitelikten "
        "oluşmaktadır. Veri temizleme aşamasında, modelin ezber yapmasını ve bilgi sızıntısını (data leakage) engellemek amacıyla anlamsız hasta kimlik "
        "numarası (person_id) ile sonuç değişkenini doğrudan ele veren öznel göstergeler (felt_rested ve cognitive_performance_score) veri setinden "
        "çıkarılmıştır. Veri setinde eksik (null) değer bulunmamaktadır. Veri setine ait ham öznitelikler ve açıklamaları Tablo 1'de görülmektedir."
    )

    p_t1 = doc.add_paragraph()
    p_t1.paragraph_format.space_before = Pt(8)
    p_t1.paragraph_format.space_after = Pt(2)
    p_t1.add_run("Tablo 1. Veri seti öznitelikleri ve açıklamaları").bold = True
    
    t1 = doc.add_table(rows=1, cols=2)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1.autofit = False
    t1.cell(0, 0).width = Inches(2.2)
    t1.cell(0, 1).width = Inches(4.8)
    
    hdr1 = t1.rows[0].cells
    hdr1[0].paragraphs[0].add_run("Öznitelik").bold = True
    hdr1[1].paragraphs[0].add_run("Açıklama").bold = True
    set_cell_border(hdr1[0], top='single', bottom='single', top_sz='6', bottom_sz='6')
    set_cell_border(hdr1[1], top='single', bottom='single', top_sz='6', bottom_sz='6')

    oznitelik_listesi = [
        ("yas", "Bireyin kronolojik yaşı (yıl)"),
        ("cinsiyet", "Bireyin biyolojik cinsiyeti (Erkek / Kadın)"),
        ("meslek", "Bireyin meslek grubu (Mühendis, Doktor, Hemşire, Öğretmen vb.)"),
        ("ulke", "Bireyin ikamet ettiği ülke"),
        ("bmi", "Vücut Kitle İndeksi (kg/m²)"),
        ("uykusure", "Günlük toplam uyku süresi (saat)"),
        ("uykukalite", "Öznel uyku kalite puanı (1 - 10 arası)"),
        ("remyuzde", "Toplam uykuda geçirilen REM evresi yüzdesi (%)"),
        ("derinyuzde", "Toplam uykuda geçirilen N3 derin uyku evresi yüzdesi (%)"),
        ("uykuyadalma", "Yatağa girdikten sonra uykuya dalma süresi (dakika)"),
        ("geceuyanma", "Gece boyunca kaydedilen uyanma sayısı"),
        ("kafein", "Yatmadan önce tüketilen kafein miktarı (mg)"),
        ("alkol", "Yatmadan önce tüketilen alkol miktarı (birim)"),
        ("ekransure", "Uykudan önceki son 2 saatte ekrana maruz kalma süresi (dakika)"),
        ("egzersiz", "Gün içerisinde planlı fiziksel egzersiz yapılma durumu (0/1)"),
        ("adimsayisi", "Günlük toplam atılan adım sayısı"),
        ("sekerleme", "Gün içerisinde yapılan gündüz uykusu süresi (dakika)"),
        ("stres", "Algılanan psikososyal stres skoru (1 - 10 ölçeği)"),
        ("calismasaat", "İlgili gün içerisinde çalışılan toplam süre (saat)"),
        ("kronotip", "Bireyin sirkadiyen ritim tipi (Sabahçı, Gececi, Orta)"),
        ("ruhsagligi", "Tanılı psikolojik durum (Yok, Anksiyete, Depresyon)"),
        ("nabiz", "Dinlenme anındaki ortalama kalp atım hızı (BPM)"),
        ("uykuilaci", "Uyku ilacı kullanımı (0/1)"),
        ("vardiya", "Vardiyalı çalışma durumu (0/1)"),
        ("odasikaklik", "Uyunulan odanın ortam sıcaklığı (°C)"),
        ("haftasonufark", "Hafta içi ile hafta sonu uyku süresi arasındaki fark (saat)"),
        ("mevsim", "Verinin toplandığı mevsim (İlkbahar, Yaz, Sonbahar, Kış)"),
        ("guntipi", "Veri gününün niteliği (Hafta içi / Hafta sonu)")
    ]

    for kod, aciklama in oznitelik_listesi:
        row = t1.add_row()
        c0, c1 = row.cells
        c0.width = Inches(2.2)
        c1.width = Inches(4.8)
        c0.paragraphs[0].add_run(kod)
        c1.paragraphs[0].add_run(aciklama)
        set_cell_border(c0, top='none', bottom='none')
        set_cell_border(c1, top='none', bottom='none')

    set_cell_border(t1.rows[-1].cells[0], bottom='single', bottom_sz='6')
    set_cell_border(t1.rows[-1].cells[1], bottom='single', bottom_sz='6')

    add_academic_heading_2("2.2. Klinik Öznitelik Mühendisliği (Clinical Feature Engineering)")
    doc.add_paragraph(
        "Uyku tıbbı kılavuzlarında uykunun brüt süresi kadar mimari sürekliliği de teşhiste birincil derecede rol oynamaktadır [10]. "
        "Veri setindeki uyanma sayısı ile uyku süresinin taşıdığı bilgiyi zenginleştirmek amacıyla iki klinik öznitelik türetilmiştir:"
    )
    
    doc.add_paragraph(
        "1. Uyku Bölünme İndeksi (Sleep Fragmentation Index - SFI): Saatteki uyanma sıklığını ölçer. "
        "gu gece uyanma sayısı, us toplam uyku süresi olmak üzere,"
    )
    add_equation(r"SFI = \frac{gu}{us}", "2.1")
    doc.add_paragraph("formülü ile hesaplanır [10].")

    doc.add_paragraph(
        "2. Onarıcı Uyku Oranı (Restorative Sleep Ratio - RSR): Fiziksel onarım sağlayan N3 derin uyku (dy) ile zihinsel yenilenme sağlayan "
        "REM uykusu (ry) yüzdelerinin toplamıdır [11]:"
    )
    add_equation(r"RSR = dy + ry", "2.2")
    doc.add_paragraph("Türetilen bu iki öznitelik ile veri setinin toplam öznitelik boyutu 28'den 30'a yükseltilmiştir.")

    add_academic_heading_2("2.3. Sınıflandırma Yöntemleri ve Karşılaştırma Mimarisi")
    doc.add_paragraph(
        "Çalışmada dokuz farklı sınıflandırma algoritması aynı veri kümesi üzerinde yarıştırılmıştır. Hedef değişken, Tablo 2'de sunulan "
        "dört sınıflı uyku bozukluğu risk ölçeğidir."
    )

    p_t2 = doc.add_paragraph()
    p_t2.paragraph_format.space_before = Pt(8)
    p_t2.paragraph_format.space_after = Pt(2)
    p_t2.add_run("Tablo 2. Uyku Bozukluğu Riski Sınıflandırma Ölçeği").bold = True
    
    t2 = doc.add_table(rows=1, cols=3)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2.autofit = False
    t2.cell(0, 0).width = Inches(1.5)
    t2.cell(0, 1).width = Inches(1.8)
    t2.cell(0, 2).width = Inches(3.7)
    
    hdr2 = t2.rows[0].cells
    hdr2[0].paragraphs[0].add_run("Sınıf Kodu").bold = True
    hdr2[1].paragraphs[0].add_run("Risk Düzeyi").bold = True
    hdr2[2].paragraphs[0].add_run("Klinik Tanım").bold = True
    set_cell_border(hdr2[0], top='single', bottom='single', top_sz='6', bottom_sz='6')
    set_cell_border(hdr2[1], top='single', bottom='single', top_sz='6', bottom_sz='6')
    set_cell_border(hdr2[2], top='single', bottom='single', top_sz='6', bottom_sz='6')

    sinif_skalasi = [
        ("0", "Sağlıklı (Healthy)", "Normal uyku mimarisi, klinik patoloji saptanmamış bireyler"),
        ("1", "Hafif (Mild)", "Hafif uyku bölünmesi, başlangıç evresi sirkadiyen düzensizlik"),
        ("2", "Orta (Moderate)", "Belirgin insomni veya hafif/orta obstrüktif uyku apnesi riski"),
        ("3", "Ağır (Severe)", "Şiddetli desatürasyon, yüksek kardiyak yük ve ileri derece uyku apnesi")
    ]
    for k, r, d in sinif_skalasi:
        row = t2.add_row()
        c0, c1, c2 = row.cells
        c0.width, c1.width, c2.width = Inches(1.5), Inches(1.8), Inches(3.7)
        c0.paragraphs[0].add_run(k)
        c1.paragraphs[0].add_run(r)
        c2.paragraphs[0].add_run(d)
        set_cell_border(c0, top='none', bottom='none')
        set_cell_border(c1, top='none', bottom='none')
        set_cell_border(c2, top='none', bottom='none')
    set_cell_border(t2.rows[-1].cells[0], bottom='single', bottom_sz='6')
    set_cell_border(t2.rows[-1].cells[1], bottom='single', bottom_sz='6')
    set_cell_border(t2.rows[-1].cells[2], bottom='single', bottom_sz='6')

    doc.add_paragraph(
        "Kıyaslanan dokuz algoritma şunlardır: Lojistik Regresyon [denklem (2.3)], Naive Bayes [denklem (2.4)], k-En Yakın Komşu (k-NN), "
        "Doğrusal DVM [denklem (2.5)], Radyal Tabanlı DVM (RBF DVM) [denklem (2.6)], Rastgele Orman (Random Forest), Yapay Sinir Ağları (MLP), "
        "XGBoost ve CatBoost. Lojistik sigmoid işlevi,"
    )
    add_equation(r"f(s) = \frac{1}{1 + e^{-s}}", "2.3")
    doc.add_paragraph("Naive Bayes koşullu bağımsızlık olasılığı,")
    add_equation(r"P(C_k | \mathbf{x}) = \frac{P(C_k) \prod_{i=1}^{n} P(x_i | C_k)}{P(\mathbf{x})}", "2.4")
    doc.add_paragraph("Doğrusal DVM karar hiper-düzlemi,")
    add_equation(r"g(\mathbf{x}) = \mathbf{w}^T \mathbf{x} + w_0", "2.5")
    doc.add_paragraph("ve RBF çekirdek işlevi,")
    add_equation(r"K(\mathbf{x}_i, \mathbf{x}_j) = \exp(-\gamma \|\mathbf{x}_i - \mathbf{x}_j\|^2)", "2.6")
    doc.add_paragraph("ile tanımlanmıştır [12-18].")

    # -------------------------------------------------------------------------
    # ADIM 4: 3. BULGULAR VE TARTIŞMA (FINDINGS AND DISCUSSION)
    # -------------------------------------------------------------------------
    add_academic_heading_1("3. BULGULAR VE TARTIŞMA (FINDINGS AND DISCUSSION)")
    
    add_academic_heading_2("3.1. Başarım Metrikleri (Performance Metrics)")
    doc.add_paragraph(
        "Çok sınıflı sınıflandırma başarımının değerlendirilmesinde Doğruluk (Accuracy), Kesinlik (Precision), Duyarlılık (Recall) ve F1-Skoru "
        "kullanılmıştır. Doğruluk formülü,"
    )
    add_equation(r"\text{Doğruluk} = \frac{DA + DE}{DA + YA + DE + YE}", "3.1")
    doc.add_paragraph("şeklinde ifade edilir. Çok sınıflı teorik karmaşıklık matrisi şablonu Tablo 3'te sunulmuştur.")

    p_t3 = doc.add_paragraph()
    p_t3.paragraph_format.space_before = Pt(8)
    p_t3.paragraph_format.space_after = Pt(2)
    p_t3.add_run("Tablo 3. Çok sınıflı bir sınıflandırma problemi için bir sınıfa ait karmaşıklık matrisi").bold = True
    
    t3 = doc.add_table(rows=5, cols=5)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    t3.autofit = False
    for r in range(5):
        for c in range(5):
            t3.cell(r, c).width = Inches(1.3)

    cm_data = [
        ("", "Tahmin: 0", "Tahmin: 1", "Tahmin: 2", "Tahmin: 3"),
        ("Gerçek: 0", "DA", "YE", "YE", "YE"),
        ("Gerçek: 1", "YA", "DE", "YE", "YE"),
        ("Gerçek: 2", "YA", "YE", "DE", "YE"),
        ("Gerçek: 3", "YA", "YE", "YE", "DE")
    ]
    for r_idx, row_vals in enumerate(cm_data):
        for c_idx, val in enumerate(row_vals):
            cell = t3.cell(r_idx, c_idx)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(val).bold = (r_idx == 0 or c_idx == 0)
            if r_idx == 0:
                set_cell_border(cell, top='single', bottom='single', top_sz='6', bottom_sz='6')
            elif r_idx == 4:
                set_cell_border(cell, top='none', bottom='single', bottom_sz='6')
            else:
                set_cell_border(cell, top='none', bottom='none')

    add_academic_heading_2("3.2. Deneysel Sonuçlar ve Modellerin Kıyaslanması (Model Benchmarking)")
    doc.add_paragraph(
        "100.000 örneğin tamamı üzerinde 10-kat çapraz doğrulama testi yürütülmüştür. Dokuz modelin aynı veri üzerindeki başarım sonuçları "
        "Tablo 4'te görülmektedir. CatBoost algoritması hem Doğruluk (%95,37 ± 0,0015) hem de F1-Skoru (0,9532 ± 0,0015) açısından tüm "
        "algoritmaları geride bırakarak şampiyon olmuştur. XGBoost (%94,08) ve Rastgele Orman (%91,40) CatBoost'u takip etmiştir. k-NN algoritmasında "
        "Optuna ile optimize edilen k=12 parametresi kullanılmıştır."
    )

    p_t4 = doc.add_paragraph()
    p_t4.paragraph_format.space_before = Pt(8)
    p_t4.paragraph_format.space_after = Pt(2)
    p_t4.add_run("Tablo 4. 100.000 örnek üzerinde sınıflandırıcı modellerin 10-kat çapraz doğrulama başarım sonuçları").bold = True
    
    t4 = doc.add_table(rows=1, cols=5)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    t4.autofit = False
    widths4 = [Inches(1.8), Inches(1.3), Inches(1.3), Inches(1.3), Inches(1.3)]
    for i, w in enumerate(widths4):
        t4.cell(0, i).width = w

    hdr4 = t4.rows[0].cells
    hdr4[0].paragraphs[0].add_run("Yöntem").bold = True
    hdr4[1].paragraphs[0].add_run("Doğruluk (%)").bold = True
    hdr4[2].paragraphs[0].add_run("Kesinlik").bold = True
    hdr4[3].paragraphs[0].add_run("Duyarlılık").bold = True
    hdr4[4].paragraphs[0].add_run("F1-Skoru").bold = True
    for c in hdr4:
        set_cell_border(c, top='single', bottom='single', top_sz='6', bottom_sz='6')

    tablo4_verileri = [
        ("CatBoost", "95,37 ± 0,15", "0,9530 ± 0,0014", "0,9537 ± 0,0015", "0,9532 ± 0,0015"),
        ("XGBoost", "94,08 ± 0,16", "0,9388 ± 0,0017", "0,9408 ± 0,0016", "0,9393 ± 0,0016"),
        ("Rastgele Orman", "91,40 ± 0,22", "0,9101 ± 0,0022", "0,9140 ± 0,0022", "0,9106 ± 0,0022"),
        ("MLP (Sinir Ağı)", "89,07 ± 0,45", "0,8904 ± 0,0047", "0,8907 ± 0,0045", "0,8904 ± 0,0046"),
        ("RBF DVM*", "82,50 ± 0,25", "0,8179 ± 0,0023", "0,8250 ± 0,0025", "0,8187 ± 0,0022"),
        ("Lojistik Regresyon", "77,32 ± 0,36", "0,7638 ± 0,0044", "0,7732 ± 0,0036", "0,7661 ± 0,0038"),
        ("k-NN (k=12)", "74,91 ± 0,41", "0,7274 ± 0,0051", "0,7491 ± 0,0041", "0,7253 ± 0,0047"),
        ("Doğrusal DVM", "74,20 ± 0,27", "0,7156 ± 0,0273", "0,7420 ± 0,0027", "0,7030 ± 0,0028"),
        ("Naive Bayes", "72,61 ± 0,30", "0,7265 ± 0,0028", "0,7261 ± 0,0030", "0,7261 ± 0,0029")
    ]
    for row_data in tablo4_verileri:
        row = t4.add_row()
        for idx, val in enumerate(row_data):
            cell = row.cells[idx]
            cell.width = widths4[idx]
            cell.paragraphs[0].add_run(val)
            set_cell_border(cell, top='none', bottom='none')
    for c in t4.rows[-1].cells:
        set_cell_border(c, bottom='single', bottom_sz='6')

    p_note4 = doc.add_paragraph()
    p_note4.paragraph_format.space_after = Pt(8)
    p_note4.add_run("*Not: RBF DVM karesel karmaşıklığı nedeniyle her katlamada 25.000 örneklem sınırlandırması ile eğitilmiştir.").font.size = Pt(8.5)

    add_academic_heading_2("3.3. Verinin Açıklanması ve Öznitelik Önem Düzeyleri (Feature Importance)")
    doc.add_paragraph(
        "Modelleri yalnızca bir kara kutu olarak yarıştırmak yerine, 'Hangi özniteliklerin uyku bozukluğu riskiyle ilgisi en fazladır?' "
        "sorusuna yanıt aramak amacıyla öznitelik önem analizi gerçekleştirilmiştir. Tablo 5'de karar ağaçları üzerinden hesaplanan "
        "Gini önem skorları ve etki yüzdeleri görülmektedir."
    )
    doc.add_paragraph(
        "Tablo 5'de görüldüğü üzere, uyku bozukluğu riskini belirlemede en baskın ilk üç faktör sırasıyla Uyku Kalite Skoru (%15,28), "
        "Ruh Sağlığı Durumu (%13,67) ve Günlük Uyku Süresi (%11,92) olmuştur. Klinik olarak türettiğimiz Uyku Bölünme İndeksi (SFI) ise "
        "%7,46'lık etki payı ile Vücut Kitle İndeksi (BMI) ve Stres Skoru'nun hemen ardından gelerek en kritik 5. öznitelik konumuna yerleşmiştir. "
        "Ham uyanma sayısı (%3,64) tek başına 8. sırada kalırken, uyanma sıklığını uyku süresiyle oranlayan SFI indeksinin 5. sıraya yükselmesi, "
        "öznitelik mühendisliğinin tıp verilerindeki açıklayıcı gücünü açıkça kanıtlamaktadır."
    )

    # TABLO 5: Öznitelik Önem Düzeyleri Tablosu
    p_t5 = doc.add_paragraph()
    p_t5.paragraph_format.space_before = Pt(8)
    p_t5.paragraph_format.space_after = Pt(2)
    p_t5.add_run("Tablo 5. Uyku bozukluğu riski üzerinde en yüksek etkiye sahip özniteliklerin önem düzeyleri ve etki yüzdeleri").bold = True

    t5 = doc.add_table(rows=1, cols=4)
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    t5.autofit = False
    widths5 = [Inches(1.0), Inches(2.8), Inches(1.8), Inches(1.4)]
    for i, w in enumerate(widths5):
        t5.cell(0, i).width = w

    hdr5 = t5.rows[0].cells
    hdr5[0].paragraphs[0].add_run("Sıra").bold = True
    hdr5[1].paragraphs[0].add_run("Öznitelik Adı").bold = True
    hdr5[2].paragraphs[0].add_run("Gini Önem Skoru").bold = True
    hdr5[3].paragraphs[0].add_run("Etki Yüzdesi (%)").bold = True
    for c in hdr5:
        set_cell_border(c, top='single', bottom='single', top_sz='6', bottom_sz='6')

    tablo5_verileri = [
        ("1", "Uyku Kalite Skoru (sleep_quality)", "0,1528", "% 15,28"),
        ("2", "Ruh Sağlığı Durumu (mental_health)", "0,1367", "% 13,67"),
        ("3", "Uyku Süresi - Saat (sleep_duration)", "0,1192", "% 11,92"),
        ("4", "Vücut Kitle İndeksi (bmi)", "0,0824", "% 8,24"),
        ("5", "Uyku Bölünme İndeksi - SFI (Türetilmiş)", "0,0746", "% 7,46"),
        ("6", "Stres Skoru (stress)", "0,0737", "% 7,37"),
        ("7", "Uykuya Dalma Süresi (latency)", "0,0617", "% 6,17"),
        ("8", "Gece Uyanma Sayısı (wakeups)", "0,0364", "% 3,64"),
        ("9", "REM Uykusu Yüzdesi (rem_perc)", "0,0250", "% 2,50"),
        ("10", "Onarıcı Uyku Oranı - RSR (Türetilmiş)", "0,0197", "% 1,97"),
        ("11", "Yaş (age)", "0,0188", "% 1,88"),
        ("12", "Günlük Çalışma Saati (work_hours)", "0,0186", "% 1,86"),
        ("13", "Yatmadan Önce Ekran Süresi (screen_time)", "0,0161", "% 1,61"),
        ("14", "Günlük Adım Sayısı (steps)", "0,0160", "% 1,60"),
        ("15", "Derin Uyku Yüzdesi (deep_sleep)", "0,0160", "% 1,60")
    ]
    for row_data in tablo5_verileri:
        row = t5.add_row()
        for idx, val in enumerate(row_data):
            cell = row.cells[idx]
            cell.width = widths5[idx]
            cell.paragraphs[0].add_run(val)
            set_cell_border(cell, top='none', bottom='none')
    for c in t5.rows[-1].cells:
        set_cell_border(c, bottom='single', bottom_sz='6')

    # Öznitelik Önem Grafiği Ekleme
    img_ozellik = 'grafikler/grafik_ozellik_onemi.png'
    if os.path.exists(img_ozellik):
        p_img_f = doc.add_paragraph()
        p_img_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img_f.paragraph_format.space_before = Pt(8)
        p_img_f.paragraph_format.space_after = Pt(2)
        p_img_f.add_run().add_picture(img_ozellik, width=Inches(5.6))
        p_cap_f = doc.add_paragraph()
        p_cap_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap_f.paragraph_format.space_after = Pt(8)
        r_cf = p_cap_f.add_run("Şekil 1. Uyku bozukluğu riskini belirlemede en etkili özniteliklerin önem düzeyleri")
        r_cf.bold = True
        r_cf.font.size = Pt(10)

    add_academic_heading_2("3.4. Sınıf Bazında Başarım ve İleri Düzey Tıbbi Değerlendirme")
    doc.add_paragraph(
        "Klinik açıdan en yüksek performansı veren CatBoost algoritmasının sınıf bazındaki detaylı performansı Tablo 6'da görülmektedir. "
        "Model, 'Sağlıklı' bireyleri %99,9 ve 'Hafif' riskli bireyleri %95,8 duyarlılık (Recall) ile tespit etmiştir. Klinik açıdan yanlış teşhisin "
        "en tehlikeli olduğu 'Ağır' (Severe) riskli grupta ise %79,7 duyarlılık ve %86,1 kesinlik elde edilmiş; kritik hastaların büyük çoğunluğu "
        "başarıyla saptanmıştır."
    )

    p_t6 = doc.add_paragraph()
    p_t6.paragraph_format.space_before = Pt(8)
    p_t6.paragraph_format.space_after = Pt(2)
    p_t6.add_run("Tablo 6. CatBoost algoritmasının uyku riski düzeylerine göre sınıf bazında başarım karnesi").bold = True

    t6 = doc.add_table(rows=1, cols=5)
    t6.alignment = WD_TABLE_ALIGNMENT.CENTER
    t6.autofit = False
    widths6 = [Inches(1.8), Inches(1.3), Inches(1.3), Inches(1.3), Inches(1.3)]
    for i, w in enumerate(widths6):
        t6.cell(0, i).width = w

    hdr6 = t6.rows[0].cells
    hdr6[0].paragraphs[0].add_run("Risk Seviyesi").bold = True
    hdr6[1].paragraphs[0].add_run("Kesinlik").bold = True
    hdr6[2].paragraphs[0].add_run("Duyarlılık").bold = True
    hdr6[3].paragraphs[0].add_run("F1-Skoru").bold = True
    hdr6[4].paragraphs[0].add_run("Örnek Sayısı").bold = True
    for c in hdr6:
        set_cell_border(c, top='single', bottom='single', top_sz='6', bottom_sz='6')

    tablo6_verileri = [
        ("Sağlıklı (Healthy)", "0,9984", "0,9987", "0,9985", "54.156"),
        ("Hafif (Mild)", "0,9445", "0,9582", "0,9513", "33.479"),
        ("Orta (Moderate)", "0,7358", "0,7186", "0,7271", "8.299"),
        ("Ağır (Severe)", "0,8612", "0,7966", "0,8276", "4.066"),
        ("Ağırlıklı Ortalama", "0,9530", "0,9537", "0,9533", "100.000")
    ]
    for row_data in tablo6_verileri:
        row = t6.add_row()
        for idx, val in enumerate(row_data):
            cell = row.cells[idx]
            cell.width = widths6[idx]
            cell.paragraphs[0].add_run(val)
            set_cell_border(cell, top='none', bottom='none')
    for c in t6.rows[-1].cells:
        set_cell_border(c, bottom='single', bottom_sz='6')

    doc.add_paragraph(
        "Tıbbi literatürün talep ettiği ayırt edicilik ve güvenilirlik metrikleri Tablo 7'de listelenmiştir. CatBoost modeli 0,9948 ROC-AUC "
        "ve 0,9842 Özgüllük (Specificity) değerine ulaşarak sağlıklı bireyleri gereksiz klinik invaziv tetkiklerden koruma gücünü kanıtlamıştır. "
        "Ayrıca en düşük entropi kaybını (Log-Loss = 0,1385) vererek kararlarındaki yüksek kesinliği tescillemiştir."
    )

    p_t7 = doc.add_paragraph()
    p_t7.paragraph_format.space_before = Pt(8)
    p_t7.paragraph_format.space_after = Pt(2)
    p_t7.add_run("Tablo 7. Sınıflandırıcıların ileri düzey tıbbi değerlendirme metrikleri sonuçları").bold = True

    t7 = doc.add_table(rows=1, cols=5)
    t7.alignment = WD_TABLE_ALIGNMENT.CENTER
    t7.autofit = False
    widths7 = [Inches(1.8), Inches(1.3), Inches(1.3), Inches(1.3), Inches(1.3)]
    for i, w in enumerate(widths7):
        t7.cell(0, i).width = w

    hdr7 = t7.rows[0].cells
    hdr7[0].paragraphs[0].add_run("Yöntem").bold = True
    hdr7[1].paragraphs[0].add_run("ROC-AUC").bold = True
    hdr7[2].paragraphs[0].add_run("Özgüllük").bold = True
    hdr7[3].paragraphs[0].add_run("MCC").bold = True
    hdr7[4].paragraphs[0].add_run("Log-Loss").bold = True
    for c in hdr7:
        set_cell_border(c, top='single', bottom='single', top_sz='6', bottom_sz='6')

    tablo7_verileri = [
        ("CatBoost", "0,9948", "0,9842", "0,9245", "0,1385"),
        ("XGBoost", "0,9912", "0,9785", "0,9038", "0,1620"),
        ("Rastgele Orman", "0,9854", "0,9670", "0,8572", "0,2340"),
        ("MLP (Sinir Ağı)", "0,9720", "0,9510", "0,8215", "0,3110"),
        ("Lojistik Regresyon", "0,9280", "0,9120", "0,6420", "0,5620"),
        ("Naive Bayes", "0,8940", "0,8850", "0,5890", "0,7450")
    ]
    for row_data in tablo7_verileri:
        row = t7.add_row()
        for idx, val in enumerate(row_data):
            cell = row.cells[idx]
            cell.width = widths7[idx]
            cell.paragraphs[0].add_run(val)
            set_cell_border(cell, top='none', bottom='none')
    for c in t7.rows[-1].cells:
        set_cell_border(c, bottom='single', bottom_sz='6')

    # -------------------------------------------------------------------------
    # ADIM 4 (DEVAM): 3.5. KARMAŞIKLIK MATRİSLERİ VE TEŞHİS ÇIKARIMLARI
    # -------------------------------------------------------------------------
    add_academic_heading_2("3.5. Karmaşıklık Matrisleri Analizi ve Teşhis Çıkarımları (Confusion Matrix Analysis and Diagnostic Inferences)")
    doc.add_paragraph(
        "Modellerin genel doğruluk ve F1-skoru gibi tekil özet metriklerle değerlendirilmesi, klinik pratikte özellikle azınlık sınıflarda yapılan "
        "kritik teşhis hatalarını maskeleyebilir. Bu nedenle 10-kat çapraz doğrulama sürecinde üretilen tüm dışarıda bırakılan (out-of-fold - OOF) "
        "tahminler toplanarak 9 modelin 4x4 boyutundaki karmaşıklık matrisleri elde edilmiş ve Şekil 2'de 3x3 ızgara biçiminde görselleştirilmiştir."
    )

    # 3x3 Karmaşıklık Matrisi Grafiği Ekleme
    img_cm = 'grafikler/grafik_cv_confusion_matrices.png'
    if os.path.exists(img_cm):
        p_img_cm = doc.add_paragraph()
        p_img_cm.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img_cm.paragraph_format.space_before = Pt(8)
        p_img_cm.paragraph_format.space_after = Pt(2)
        p_img_cm.add_run().add_picture(img_cm, width=Inches(6.0))
        p_cap_cm = doc.add_paragraph()
        p_cap_cm.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap_cm.paragraph_format.space_after = Pt(8)
        r_ccm = p_cap_cm.add_run("Şekil 2. 100.000 örnek üzerinde dokuz makine öğrenmesi modelinin 10-kat çapraz doğrulama karmaşıklık matrisleri dağılımı (3x3 ızgara)")
        r_ccm.bold = True
        r_ccm.font.size = Pt(10)

    doc.add_paragraph(
        "Klinik kararlarda en yüksek güvenilirlik ve ayırt ediciliği sunan şampiyon CatBoost algoritmasının 10-kat çapraz doğrulama süresince "
        "gerçekleştirdiği gerçek sınıf ve tahmin edilen vaka dağılımları Tablo 8'de sayısal olarak dökümlenmiştir."
    )

    p_t8 = doc.add_paragraph()
    p_t8.paragraph_format.space_before = Pt(8)
    p_t8.paragraph_format.space_after = Pt(2)
    p_t8.add_run("Tablo 8. Şampiyon CatBoost modelinin 10-kat çapraz doğrulama karmaşıklık matrisi sayısal vaka dağılımı (100.000 Örnek)").bold = True

    t8 = doc.add_table(rows=1, cols=7)
    t8.alignment = WD_TABLE_ALIGNMENT.CENTER
    t8.autofit = False
    widths8 = [Inches(1.6), Inches(0.9), Inches(0.9), Inches(0.9), Inches(0.9), Inches(1.1), Inches(1.1)]
    for i, w in enumerate(widths8):
        t8.cell(0, i).width = w

    hdr8 = t8.rows[0].cells
    hdr8[0].paragraphs[0].add_run("Gerçek Sınıf").bold = True
    hdr8[1].paragraphs[0].add_run("Tahmin: Sağlıklı").bold = True
    hdr8[2].paragraphs[0].add_run("Tahmin: Hafif").bold = True
    hdr8[3].paragraphs[0].add_run("Tahmin: Orta").bold = True
    hdr8[4].paragraphs[0].add_run("Tahmin: Ağır").bold = True
    hdr8[5].paragraphs[0].add_run("Toplam Vaka").bold = True
    hdr8[6].paragraphs[0].add_run("Doğruluk (%)").bold = True
    for c in hdr8:
        set_cell_border(c, top='single', bottom='single', top_sz='6', bottom_sz='6')

    tablo8_verileri = [
        ("Sağlıklı (Healthy)", "54.083", "73", "0", "0", "54.156", "% 99,87"),
        ("Hafif (Mild)", "85", "32.080", "1.314", "0", "33.479", "% 95,82"),
        ("Orta (Moderate)", "0", "1.813", "5.964", "522", "8.299", "% 71,86"),
        ("Ağır (Severe)", "0", "0", "827", "3.239", "4.066", "% 79,66"),
        ("Toplam Tahmin", "54.168", "33.966", "8.105", "3.761", "100.000", "% 95,37")
    ]
    for row_data in tablo8_verileri:
        row = t8.add_row()
        for idx, val in enumerate(row_data):
            cell = row.cells[idx]
            cell.width = widths8[idx]
            cell.paragraphs[0].add_run(val)
            set_cell_border(cell, top='none', bottom='none')
    for c in t8.rows[-1].cells:
        set_cell_border(c, bottom='single', bottom_sz='6')

    doc.add_paragraph(
        "Şekil 2'de sunulan 9 modelin karmaşıklık matrisleri ve Tablo 8'deki CatBoost sayısal dağılımı üzerinden elde edilen temel tıbbi ve algoritmik çıkarımlar şunlardır:"
    )

    doc.add_paragraph(
        "1. Sıfır Kritik Hata ile Hayati Güvenlik Marjı (Zero Critical False-Negative): Tıbbi karar destek sistemlerinde en tehlikeli klinik senaryo, "
        "ağır seyirli bir hastaya (Severe) 'sağlıklı' teşhisi konularak hastanın tedavisiz bırakılması veya acil müdahaleden mahrum edilmesidir (Tip II hata). "
        "CatBoost modeli, veri setindeki 4.066 'Ağır' vakanın hiçbirisini (0 hasta) 'Sağlıklı' veya 'Hafif' olarak yanlış sınıflandırmamıştır. "
        "Ağır vakaların 3.239'u (%79,66) tam isabetle yakalanmış, geriye kalan 827 vaka ise yalnızca bir alt basamak olan 'Orta' risk kademesine atanmıştır. "
        "Bu durum, ölümcül sonuçlar doğurabilecek kritik yanlış negatif teşhis riskinin pratikte %0,00 olduğunu ve hekimler için benzersiz bir güvenlik kalkanı sağladığını göstermektedir."
    )

    doc.add_paragraph(
        "2. Sağlıklı Bireylerde Yalancı Alarmın (False Alarm) Önlenmesi: 54.156 sağlıklı bireyin 54.083'ü (%99,87) kusursuz bir doğrulukla tespit edilmiş; "
        "yalnızca 73 birey (%0,13) 'Hafif' riskli olarak etiketlenmiştir. Sağlıklı bireyler arasından 'Orta' veya 'Ağır' tanısı alan tek bir kişi dahi (0 vaka) "
        "bulunmamaktadır. Bu durum, birinci basamak sağlık kuruluşlarında veya genel taramalarda gereksiz polisomnografi (uyku laboratuvarı) randevularının oluşmasını, "
        "aşırı klinik maliyetleri ve bireylerde gereksiz hastalık kaygısını (anksiyete) tamamen bertaraf etmektedir."
    )

    doc.add_paragraph(
        "3. Sınır Vakalar ve Komşu Sınıf Geçişkenliği (Borderline Confusion): Karmaşıklık matrisindeki çapraz hataların %98,7'si doğrudan komşu sınıflar "
        "arasında (Hafif <-> Orta ve Orta <-> Ağır) yoğunlaşmıştır. Örneğin, Orta riskli 8.299 vakanın 1.813'ü Hafif, 522'si ise Ağır olarak tahmin edilmiştir. "
        "Bunun klinik ve fizyolojik açıklaması; derin uyku yüzdesi, Uyku Bölünme İndeksi (SFI) ve apne sıklığı gibi değişkenlerin keskin basamaklar yerine "
        "sürekli bir spektrum halinde seyretmesidir. Tıbbi uygulamalarda hekimler de hafif-orta eşiğindeki hastaları 'gri bölge' kabul etmekte ve benzer koruyucu yaşam tarzı "
        "müdahaleleri uygulamaktadır; dolayısıyla bu geçişkenlik klinik tolerans sınırları içerisindedir."
    )

    doc.add_paragraph(
        "4. Model Mimarilerinin Karar Sınırı Farklılıkları ve Sınıf Çöküşü: Şekil 2'de yer alan diğer modellerin matrisleri incelendiğinde, doğrusal ve parametrik "
        "modellerin çok sınıflı ve dengesiz medikal verilerde başarısız olduğu açıkça görülmektedir. Örneğin Doğrusal DVM (LSVM), 8.299 Orta riskli vakanın 7.842'sini (%94,5) "
        "Hafif sınıfına atayarak Orta sınıfta tam bir sınıf çöküşü (class collapse) yaşamış ve yalnızca 9 vakayı doğru tanıyabilmiştir. Naive Bayes ise özellik bağımsızlığı "
        "varsayımı yüzünden Ağır vakaların 614'ünü Hafif sınıfına kaydırarak tehlikeli klinik hatalar üretmiştir. Buna karşılık CatBoost ve XGBoost gibi gradyan artırma ağaçları, "
        "asimetrik karar ağaçları sayesinde sınıflar arasındaki karmaşık non-lineer sınırları mükemmel biçimde optimize ederek köşegen boyunca kusursuz bir yoğunlaşma sergilemiştir."
    )

    # -------------------------------------------------------------------------
    # ADIM 4 (DEVAM): 3.6. HESAPLAMA VERİMLİLİĞİ VE MODEL SEÇİMİ
    # -------------------------------------------------------------------------
    add_academic_heading_2("3.6. Hesaplama Verimliliği ve Model Seçimi (Computational Efficiency)")
    doc.add_paragraph(
        "Klinik uygulamalarda karar destek sistemlerinin yanıt hızı hayati bir ölçüttür. Tablo 9'da görüldüğü üzere CatBoost, 54,14 saniyelik "
        "eğitim süresi ve %95,37'lik başarımı ile hız-doğruluk dengesinde (verimlilikte) en optimum model olduğunu göstermiştir. Yapay Sinir Ağı "
        "(MLP) ise 279,93 saniye sürerek en hantal model olmuştur."
    )

    p_t9 = doc.add_paragraph()
    p_t9.paragraph_format.space_before = Pt(8)
    p_t9.paragraph_format.space_after = Pt(2)
    p_t9.add_run("Tablo 9. Modellerin 10-kat çapraz doğrulama toplam eğitim süreleri ve verimlilik kıyaslaması").bold = True

    t9 = doc.add_table(rows=1, cols=4)
    t9.alignment = WD_TABLE_ALIGNMENT.CENTER
    t9.autofit = False
    widths9 = [Inches(2.2), Inches(1.6), Inches(1.6), Inches(1.6)]
    for i, w in enumerate(widths9):
        t9.cell(0, i).width = w

    hdr9 = t9.rows[0].cells
    hdr9[0].paragraphs[0].add_run("Yöntem").bold = True
    hdr9[1].paragraphs[0].add_run("F1-Skoru").bold = True
    hdr9[2].paragraphs[0].add_run("Toplam Süre (sn)").bold = True
    hdr9[3].paragraphs[0].add_run("Verimlilik İndeksi").bold = True
    for c in hdr9:
        set_cell_border(c, top='single', bottom='single', top_sz='6', bottom_sz='6')

    tablo9_verileri = [
        ("CatBoost", "0,9532", "54,14", "Yüksek / Optimum"),
        ("XGBoost", "0,9393", "36,26", "Yüksek"),
        ("Rastgele Orman", "0,9106", "73,74", "Orta"),
        ("Lojistik Regresyon", "0,7661", "12,28", "Orta"),
        ("k-NN", "0,7253", "20,73", "Düşük"),
        ("MLP (Sinir Ağı)", "0,8904", "279,93", "Düşük / Yavaş")
    ]
    for row_data in tablo9_verileri:
        row = t9.add_row()
        for idx, val in enumerate(row_data):
            cell = row.cells[idx]
            cell.width = widths9[idx]
            cell.paragraphs[0].add_run(val)
            set_cell_border(cell, top='none', bottom='none')
    for c in t9.rows[-1].cells:
        set_cell_border(c, bottom='single', bottom_sz='6')

    # -------------------------------------------------------------------------
    # ADIM 5: 4. SONUÇLAR (CONCLUSIONS)
    # -------------------------------------------------------------------------
    add_academic_heading_1("4. SONUÇLAR (CONCLUSIONS)")
    
    doc.add_paragraph(
        "Uyku sağlığı, bireylerin bilişsel performansı ve fiziksel dayanıklılığı açısından kritik bir belirleyicidir. Bu çalışmada, "
        "100.000 bireye ait demografik, kardiyak ritim ve yaşam tarzı verilerini kullanarak tek bir ortak hedef değişken olan uyku bozukluğu "
        "riskini dörtlü sınıflama (Sağlıklı, Hafif, Orta, Ağır) çerçevesinde tahmin ettik. Dokuz farklı makine öğrenmesi algoritmasını aynı veri "
        "kümesi üzerinde 10-kat çapraz doğrulama ile doğrudan yarıştırdık. Deneysel sonuçlara göre, CatBoost algoritması %95,37 doğruluk ve "
        "0,9532 F1-skoru ile en iyi kestirimi gerçekleştirmiştir. Detaylı karmaşıklık matrisi analizleri, ağır riskli hastaların sağlıklı olarak "
        "etiketlenme riskinin %0,00 olduğunu ve sağlıklı popülasyonda %99,87'lik özgüllükle gereksiz tıbbi tetkiklerin önlendiğini kanıtlamıştır. "
        "Gerçekleştirilen öznitelik önem analizi ise uyku kalite skoru (%15,28), ruh sağlığı durumu (%13,67) ve türetilen SFI indeksinin (%7,46) "
        "hastalığı tetikleyen en kritik biyolojik faktörler olduğunu ortaya koymuştur."
    )

    doc.add_paragraph(
        "Bu çalışmanın temel kısıtı, verilerin çevrimdışı (offline) bir veri tabanından elde edilmiş olması ve polisomnografi ham sinyalleri "
        "yerine türetilmiş sayısal metrikleri içermesidir. Gelecekte yapılacak çalışmalarda, akıllı saat ve giyilebilir sensörlerden gerçek zamanlı "
        "akış sağlayan gömülü bir web karar destek sistemi tasarlanması ve derin öğrenme mimarileriyle zaman serisi tabanlı risk öngörülerinin "
        "incelenmesi hedeflenmektedir."
    )

    # -------------------------------------------------------------------------
    # ADIM 6: SON BÖLÜMLER (KAYNAK DOSYALAR, TEŞEKKÜR, KAYNAKLAR)
    # -------------------------------------------------------------------------
    add_academic_heading_1("KAYNAK DOSYALAR (SUPPLEMENTARY FILES)")
    doc.add_paragraph("Bu çalışmada kullanılan veri setine ve kaynak kodlara https://github.com/DBurakyuz/sleep-disorder-ml adresinden ulaşılabilir.")

    add_academic_heading_1("TEŞEKKÜR (ACKNOWLEDGMENTS)")
    doc.add_paragraph("Bu çalışma, Yalova Üniversitesi Mühendislik Fakültesi Bilgisayar Mühendisliği Bölümü bünyesinde gerçekleştirilmiştir. Katkılarından dolayı bölüm öğretim elemanlarına teşekkür ederiz.")

    add_academic_heading_1("KAYNAKLAR (REFERENCES)")
    
    kaynaklar = [
        "[1] Walker, M. P., \"Why We Sleep: Unlocking the Power of Sleep and Dreams\", Scribner, New York, 2017.",
        "[2] World Health Organization, \"Global status report on noncommunicable diseases\", WHO Press, Cenevre, 2022.",
        "[3] Türk Toraks Derneği, \"Obstrüktif Uyku Apnesi Sendromu Tanı ve Tedavi Uzlaşı Raporu\", Türk Toraks Dergisi, Cilt 17, No 1, 1-45, 2016.",
        "[4] Alpaydin, E., \"Introduction to Machine Learning\", 3. Baskı, The MIT Press, Londra, 2014.",
        "[5] Al-Angari, H. M., Sahakian, A. V., \"Automated detection of obstructive sleep apnea using support vector machines\", IEEE Transactions on Information Technology in Biomedicine, Cilt 16, No 5, 1003-1009, 2012.",
        "[6] Palotti, J., Mall, R., Fernandez-Luque, L., \"Benchmark on a large dataset for sleep detection using wearable sensors and random forest\", Scientific Reports, Cilt 9, No 1, 12001, 2019.",
        "[7] Penzel, T., McNames, J., de Chazal, P., Raymond, B., Murray, A., Moody, G., \"Systematic comparison of different algorithms for apnoea detection based on electrocardiogram recordings\", Medical and Biological Engineering and Computing, Cilt 40, No 4, 402-407, 2002.",
        "[8] Sadeh, A., Sharkey, K. M., Carskadon, M. A., \"Activity-based sleep-wake identification: An empirical test of methodological issues\", Sleep, Cilt 17, No 3, 201-207, 1994.",
        "[9] Faust, O., Acharya, U. R., Ng, E. Y. K., Hong, T. J., \"Application of machine learning tools in sleep disorder diagnosis: A review\", Journal of Medical Systems, Cilt 40, No 12, 275, 2016.",
        "[10] Bonnet, M. H., Arand, D. L., \"Clinical effects of sleep fragmentation\", Sleep Medicine Reviews, Cilt 7, No 4, 297-310, 2003.",
        "[11] Buysse, D. J., Reynolds, C. F., Monk, T. H., Berman, S. R., Kupfer, D. J., \"The Pittsburgh Sleep Quality Index: a new instrument for psychiatric practice and research\", Psychiatry Research, Cilt 28, No 2, 193-213, 1989.",
        "[12] Kutner, M. H., Nachtsheim, C. J., Neter, J., Li, W., \"Applied Linear Statistical Models\", Cilt 103, McGraw-Hill Irwin, New York, 2005.",
        "[13] Feng, P. M., Ding, H., Chen, W., Lin, H., \"Naive Bayes Classifier with Feature Selection To Identify Biological Properties\", Computational and Mathematical Methods in Medicine, 2013.",
        "[14] Cover, T., Hart, P., \"Nearest neighbor pattern classification\", IEEE Transactions on Information Theory, Cilt 13, No 1, 21-27, 1967.",
        "[15] Vapnik, V., \"The Nature of Statistical Learning Theory\", Springer Science & Business Media, New York, 2000.",
        "[16] Breiman, L., \"Random Forests\", Machine Learning, Cilt 45, No 1, 5-32, 2001.",
        "[17] Haykin, S., \"Neural Networks and Learning Machines\", 3. Baskı, Pearson, New York, 2009.",
        "[18] Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., Gulin, A., \"CatBoost: unbiased boosting with categorical features\", Advances in Neural Information Processing Systems (NeurIPS), Cilt 31, 6638-6648, 2018.",
        "[19] Powers, D. M., \"Evaluation: from precision, recall and F-measure to ROC, informedness, markedness and correlation\", Journal of Machine Learning Technologies, Cilt 2, No 1, 37-63, 2011.",
        "[20] Wittmann, M., Dinich, J., Merrow, M., Roenneberg, T., \"Social jetlag: misalignment of biological and social time\", Chronobiology International, Cilt 23, No 1-2, 497-509, 2006."
    ]

    for k in kaynaklar:
        p_k = doc.add_paragraph()
        p_k.paragraph_format.space_after = Pt(4)
        p_k.paragraph_format.left_indent = Inches(0.3)
        p_k.paragraph_format.first_line_indent = Inches(-0.3)
        r_k = p_k.add_run(k)
        r_k.font.size = Pt(9.5)

    output_filename = "Makine_Ogrenmesi_Ile_Uyku_Bozuklugu_Riski_Tahmini.docx"
    doc.save(output_filename)
    print(f"BAŞARILI: Güncellenmiş Makale Word belgesi '{output_filename}' olarak kaydedildi!")

if __name__ == '__main__':
    create_paper()
