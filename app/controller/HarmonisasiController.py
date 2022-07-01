from select import select
from app import response, app
from flask import request, abort
import pickle
import fitz
import re
import string
import pandas as pd
from nltk.corpus import stopwords as sw
from app import db
from sqlalchemy import func
from app.model.ruu import ruu, ruu_pasal
from app.model.uud import preprocessing, preprocessing_pasal, uu, uu_pasal_html
from gensim.models.phrases import Phrases, Phraser
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.models import Word2Vec
from gensim.similarities import WordEmbeddingSimilarityIndex
from gensim.similarities import SparseTermSimilarityMatrix
from gensim.similarities import SoftCosineSimilarity
from itertools import groupby
import os
from config import basedir


UU_Title = []
UU_Content = []


def preproses_tahap1(text):
    text = text.lower()
    text = re.sub('www.peraturan.go.id', '', text)
    text = re.sub('www.bphn.go.id', '', text)
    text = re.sub('www.hukumonline.com', '', text)
    # untuk menghilangkan teks yang berada di dalam []
    text = re.sub('\[.*?\]', '', text)
    # untuk menghilangkan karakter non ascii
    text = text.encode('ascii', 'replace').decode('ascii')
    # Untuk menghilangkan punktuasi (tanda baca) yang berada di dalam teks
    text = re.sub('[%s]' % re.escape(string.punctuation), ' ', text)
    # untuk menghilangkan kata yang terdapat angka di dalammnya
    text = re.sub('\w*\d\w*', '', text)
    text = re.sub('[‘’“”…]', '', text)
    text = re.sub('\n', ' ', text)
    text = re.sub('\t', ' ', text)
    text = text.strip()
    text = re.sub('microsoft word', '', text)
    text = re.sub('�', '', text)
    text = re.sub('\s+', ' ', text)
    # untuk menghilangkan single char
    text = re.sub(r"\b[a-zA-Z]\b", "", text)
    text = re.sub('www.bphn.go.id', '', text)
    text = re.sub('copyright', '', text)
    text = re.sub('menirr', '', text)
    text = re.sub('nomor', '', text)
    text = re.sub('repuel', '', text)
    text = re.sub('indonesta', 'indonesia', text)
    text = re.sub('rtf', '', text)
    text = re.sub('republtk', 'republik', text)
    return text


def test(file):
    namaFile = file
    dir = "C:/xampp/htdocs/omnilaw/uploads/hitung/"
    doc = fitz.open(dir + namaFile + ".pdf")
    UU_Title.append(namaFile)
    Content = ""
    for page in doc:
        Content = Content + " " + page.get_text("text")
    UU_Content.append(Content)
    UU_Title_Content = {UU_Title[0]: [UU_Content[0]]}
    pd.set_option('max_colwidth', 150)
    # uu_df adalah untuk dataframe undang-undang yang dipisahkan berdasarkan kategori yang ada
    UU_Pembanding_df = pd.DataFrame.from_dict(UU_Title_Content).transpose()
    UU_Pembanding_df.columns = ['ISI_UU_Pembanding']
    UU_Pembanding_df = UU_Pembanding_df.sort_index()

    def preptahap1(x): return preproses_tahap1(x)
    UU_Pembanding_Prep = pd.DataFrame(
        UU_Pembanding_df.ISI_UU_Pembanding.apply(preptahap1))
    UU_Pembanding_Prep = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
        lambda x: ' '.join([word for word in x.split() if len(word) > 3])))
    UU_Pembanding_Prep = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
        lambda x: ' '.join([word for word in x.split() if x.count(word) < 5])))
    s_word_indonesia = sw.words('indonesian')
    # print(s_word_indonesia)
    s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                            'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat'])
    s_word_indonesia.extend(['januari', 'februari', 'maret', 'april', 'mei',
                            'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])
    # print(s_word_indonesia)
    # print(UU_1675_S_wordstambah)
    UU_Pembanding_Stoprem = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
        lambda x: ' '.join([word for word in x.split() if word not in (s_word_indonesia)])))
    UU_Content.pop(0)
    UU_Title.pop(0)

    # list UU Pembanding
    UU_Pembanding_Dokumen = []

    def UU_Pembanding_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Pembanding_Dokumen.extend(
                [dataset.ISI_UU_Pembanding[indeks].split()])
    UU_Pembanding_DF2List(UU_Pembanding_Stoprem)

    # list UU pasal
    UU_pasal_Stoprem = pd.read_pickle(
        'C:/xampp/htdocs/Python/Restful/pickle/UU_pasal_Stoprem.pkl')
    UU_pasal_Dokumen = []

    def UU_pasal_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_pasal_Dokumen.extend([dataset.uud_content[indeks].split()])
    UU_pasal_DF2List(UU_pasal_Stoprem)

    # list UU full
    UU_full_Stoprem = pd.read_pickle(
        'C:/xampp/htdocs/Python/Restful/pickle/UU_full_Stoprem.pkl')
    UU_full_Dokumen = []

    def UU_full_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_full_Dokumen.extend([dataset.text[indeks].split()])
    UU_full_DF2List(UU_full_Stoprem)

    # Membuat bigram untuk UU_Pembanding_Dokumen
    UU_Pembanding_Dokumen_phrases = Phrases(
        UU_Pembanding_Dokumen, min_count=10, progress_per=1)
    bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
    UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

    # Membuat bigram untuk UU_pasal_Dokumen
    UU_pasal_Dokumen_phrases = Phrases(
        UU_pasal_Dokumen, min_count=10, progress_per=1)
    bigram_pasal = Phraser(UU_pasal_Dokumen_phrases)
    UU_pasal_Dokumen_bigram = bigram_pasal[UU_pasal_Dokumen]

    # Membuat bigram untuk UU_full_Dokumen
    UU_full_Dokumen_phrases = Phrases(
        UU_full_Dokumen, min_count=10, progress_per=1)
    bigram_full = Phraser(UU_full_Dokumen_phrases)
    UU_full_Dokumen_bigram = bigram_full[UU_full_Dokumen]

    UU_Query_Dictionary = Dictionary.load(
        'C:/xampp/htdocs/Python/Restful/modelMl/1682_dictionary.gensimdict')

    TfIdf_Model = TfidfModel.load(
        'C:/xampp/htdocs/Python/Restful/modelMl/1682_tfidf.model')

    UU_1675_SG = Word2Vec.load(
        'C:/xampp/htdocs/Python/Restful/modelMl/UU_1675_SG_3_190.model')
    indeks_similarity = WordEmbeddingSimilarityIndex(UU_1675_SG.wv)

    matriks_similarity = SparseTermSimilarityMatrix.load(
        'C:/xampp/htdocs/Python/Restful/modelMl/1682_matriks.matrix')

    def softcossim(kueri, dokumen):
        # Compute Soft Cosine Measure between the query and the documents.
        kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
            querry) for querry in kueri]]
        indeks = SoftCosineSimilarity(
            TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=2365, normalized=(True, True))
        similarities = indeks[kueri]
        return similarities

    UU_pasal_res = softcossim(
        UU_Pembanding_Dokumen_bigram, UU_pasal_Dokumen_bigram)

    UU_full_res = softcossim(
        UU_Pembanding_Dokumen_bigram, UU_full_Dokumen_bigram)

    for a, x in enumerate(UU_full_res):
        full = []
        for y in x:
            res_formatter = y[1]*100
            presentase_formatter = float("{:.3f}".format(res_formatter))
            full_dict = {
                'id_tbl_uu': int(UU_full_Stoprem.iloc[y[0]].id_tbl_uu),
                'presentase': (presentase_formatter),
                'uu': UU_full_Stoprem.iloc[y[0]].uu,
                'tentang': UU_full_Stoprem.iloc[y[0]].tentang,
                'file_arsip': UU_full_Stoprem.iloc[y[0]].file_arsip,
                'status': int(UU_full_Stoprem.iloc[y[0]].status)
            }
            full.append(full_dict)

    for a, x in enumerate(UU_pasal_res):
        pasal = []
        for y in x:
            res_formatter = y[1]*100
            presentase_formatter = float("{:.3f}".format(res_formatter))
            pasal_dict = {
                'id': int(UU_pasal_Stoprem.iloc[y[0]].id),
                'hasil': (presentase_formatter),
                'id_tbl_uu': int(UU_pasal_Stoprem.iloc[y[0]].id_tbl_uu),
                'uud_id': UU_pasal_Stoprem.iloc[y[0]].uud_id,
                'uud_section': UU_pasal_Stoprem.iloc[y[0]].uud_section,
                'uud_detail': UU_pasal_Stoprem.iloc[y[0]].uud_detail
            }
            pasal.append(pasal_dict)

    full_df = pd.DataFrame.from_dict(full)
    pasal_df = pd.DataFrame.from_dict(pasal)

    query_df = pd.merge(pasal_df, full_df, on='id_tbl_uu', how='inner')

    hasil_dict = query_df.to_dict('records')

    res = []
    def key_func(k): return k['id_tbl_uu']

    for k, g in groupby(sorted(hasil_dict, key=lambda res: res['presentase'], reverse=True), key=key_func):
        obj = {'id_tbl_uu': k, 'uu': '',
               'jumlah': 0, 'tentang': '', 'presentase': '', 'file_arsip': '', 'status': '', 'pasal': []}
        for group in g:
            if not obj['uu']:
                obj['uu'] = group['uu']
                obj['tentang'] = group['tentang']
                obj['presentase'] = group['presentase']
                obj['file_arsip'] = group['file_arsip']
                obj['status'] = group['status']
            obj['jumlah'] = obj['jumlah'] + 1
            pasal = {
                'id': group['id'],
                'hasil': group['hasil'],
                'uud_id': group['uud_id'],
                'uud_section': group['uud_section'],
                'uud_detail': group['uud_detail']
            }
            obj['pasal'].append(pasal)
        res.append(obj)

    if os.path.exists("C:/xampp/htdocs/Python/Restful/pickle/output.pkl"):
        os.remove("C:/xampp/htdocs/Python/Restful/pickle/output.pkl")
        with open('C:/xampp/htdocs/Python/Restful/pickle/output.pkl', 'wb') as f:
            pickle.dump(res, f)
    else:
        with open('C:/xampp/htdocs/Python/Restful/pickle/output.pkl', 'wb') as f:
            pickle.dump(res, f)
    return response.ok(res, "")


def detail(rank):
    with open('C:/xampp/htdocs/Python/Restful/pickle/output.pkl', 'rb') as f:
        res = pickle.load(f)

    no = int(rank)
    hasil = res[no]

    return response.ok(hasil, "")


def harmonisasiPasal():
    kalimat = request.json['kalimat']
    kategori = request.json['kategori']
    UU_Content = {'Content': [kalimat]}
    UU_df = pd.DataFrame.from_dict(UU_Content)

    def preptahap1(x): return preproses_tahap1(x)

    UU_df = pd.DataFrame(UU_df.Content.apply(preptahap1))

    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if len(word) > 3])))
    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if x.count(word) < 5])))

    s_word_indonesia = sw.words('indonesian')
    s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                            'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat'])
    s_word_indonesia.extend(['januari', 'februari', 'maret', 'april', 'mei',
                            'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])

    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if word not in (s_word_indonesia)])))

    # list UU Pembanding
    UU_Pembanding_Dokumen = []

    def UU_Pembanding_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Pembanding_Dokumen.extend(
                [dataset.Content[indeks].split()])
    UU_Pembanding_DF2List(UU_df)

    # list UU pasal
    UU_Stoprem = pd.read_pickle(
        'C:/xampp/htdocs/Python/Restful/pickle/UU_Stoprem.pkl')
    UU_Dokumen = []

    def UU_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Dokumen.extend([dataset.uud_content[indeks].split()])
    UU_DF2List(UU_Stoprem)

    # Membuat bigram untuk UU_Pembanding_Dokumen
    UU_Pembanding_Dokumen_phrases = Phrases(
        UU_Pembanding_Dokumen, min_count=10, progress_per=1)
    bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
    UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

    # Membuat bigram untuk UU_Dokumen
    UU_Dokumen_phrases = Phrases(
        UU_Dokumen, min_count=10, progress_per=1)
    bigram_pasal = Phraser(UU_Dokumen_phrases)
    UU_Dokumen_bigram = bigram_pasal[UU_Dokumen]

    UU_Query_Dictionary = Dictionary.load(
        'C:/xampp/htdocs/Python/Restful/modelMl/new_dictionary.gensimdict')

    TfIdf_Model = TfidfModel.load(
        'C:/xampp/htdocs/Python/Restful/modelMl/new_tfidf.model')

    UU_1675_SG = Word2Vec.load(
        'C:/xampp/htdocs/Python/Restful/modelMl/UU_1675_SG_3_190.model')
    indeks_similarity = WordEmbeddingSimilarityIndex(UU_1675_SG.wv)

    matriks_similarity = SparseTermSimilarityMatrix.load(
        'C:/xampp/htdocs/Python/Restful/modelMl/new_matriks.matrix')

    def softcossim(kueri, dokumen):
        # Compute Soft Cosine Measure between the query and the documents.
        kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
            querry) for querry in kueri]]
        indeks = SoftCosineSimilarity(
            TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=100, normalized=(True, True))
        similarities = indeks[kueri]
        return similarities

    UU_Query_res = softcossim(
        UU_Pembanding_Dokumen_bigram, UU_Dokumen_bigram)

    for a, x in enumerate(UU_Query_res):
        # print(a)
        array = []
        for y in x:

            # print(y)
            # print(y[0])
            # print("a")
            res_formatter = y[1]*100
            presentase_formatter = float("{:.3f}".format(res_formatter))
            filter = UU_Stoprem.iloc[y[0]].id_kategori
            if kategori:
                if filter == int(kategori):
                    tmp_dict = {
                        # "uu_querry" : UU_Querry_Stoprem_copy.iloc[a].name,
                        'id': int(UU_Stoprem.iloc[y[0]].id),
                        'presentase': (presentase_formatter),
                        'id_tbl_uu': int(UU_Stoprem.iloc[y[0]].id_tbl_uu),
                        'uu': UU_Stoprem.iloc[y[0]].uu,
                        'tentang': UU_Stoprem.iloc[y[0]].tentang,
                        'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                        'uud_section': UU_Stoprem.iloc[y[0]].uud_section,
                        'uud_detail': UU_Stoprem.iloc[y[0]].uud_detail,
                        'file_arsip': UU_Stoprem.iloc[y[0]].file_arsip,
                        'status': int(UU_Stoprem.iloc[y[0]].status),
                        'id_kategori': int(filter)
                    }
                    array.append(tmp_dict)
            else:
                tmp_dict = {
                    'id': int(UU_Stoprem.iloc[y[0]].id),
                    'presentase': (presentase_formatter),
                    'id_tbl_uu': int(UU_Stoprem.iloc[y[0]].id_tbl_uu),
                    'uu': UU_Stoprem.iloc[y[0]].uu,
                    'tentang': UU_Stoprem.iloc[y[0]].tentang,
                    'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                    'uud_section': UU_Stoprem.iloc[y[0]].uud_section,
                    'uud_detail': UU_Stoprem.iloc[y[0]].uud_detail,
                    'file_arsip': UU_Stoprem.iloc[y[0]].file_arsip,
                    'status': int(UU_Stoprem.iloc[y[0]].status),
                    'id_kategori': int(filter)
                }
                array.append(tmp_dict)

    return response.ok(array, "")


def coba():
    return response.badRequest("", "test")


def wordvec(file):
    try:
        namaFile = file
        dir = "C:/xampp/htdocs/peraturan-uu/public/assets/hitung/"
        if not os.path.exists(dir + namaFile + ".pdf"):
            return response.badRequest("", "Nama file salah")
        doc = fitz.open(dir + namaFile + ".pdf")
        UU_Title.append(namaFile)
        Content = ""
        for page in doc:
            Content = Content + " " + page.get_text("text")
        UU_Content.append(Content)
        UU_Title_Content = {UU_Title[0]: [UU_Content[0]]}
        pd.set_option('max_colwidth', 150)
        # uu_df adalah untuk dataframe undang-undang yang dipisahkan berdasarkan kategori yang ada
        UU_Pembanding_df = pd.DataFrame.from_dict(UU_Title_Content).transpose()
        UU_Pembanding_df.columns = ['ISI_UU_Pembanding']
        UU_Pembanding_df = UU_Pembanding_df.sort_index()

        def preptahap1(x): return preproses_tahap1(x)
        UU_Pembanding_Prep = pd.DataFrame(
            UU_Pembanding_df.ISI_UU_Pembanding.apply(preptahap1))
        UU_Pembanding_Prep = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
            lambda x: ' '.join([word for word in x.split() if len(word) > 3])))
        UU_Pembanding_Prep = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
            lambda x: ' '.join([word for word in x.split() if x.count(word) < 5])))
        s_word_indonesia = sw.words('indonesian')
        # print(s_word_indonesia)
        s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                                'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat'])
        s_word_indonesia.extend(['januari', 'februari', 'maret', 'april', 'mei',
                                'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])
        # print(s_word_indonesia)
        # print(UU_1675_S_wordstambah)
        UU_Pembanding_Stoprem = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
            lambda x: ' '.join([word for word in x.split() if word not in (s_word_indonesia)])))
        UU_Content.pop(0)
        UU_Title.pop(0)

        # list UU Pembanding
        UU_Pembanding_Dokumen = []

        def UU_Pembanding_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_Pembanding_Dokumen.extend(
                    [dataset.ISI_UU_Pembanding[indeks].split()])
        UU_Pembanding_DF2List(UU_Pembanding_Stoprem)

        # list UU pasal
        uud = preprocessing.query.join(uu).add_columns(
            uu.uu, uu.tentang, uu.file_arsip, uu.status)
        UU_pasal_Stoprem = pd.read_sql_query(uud.statement, con=db.engine)
        UU_pasal_Dokumen = []

        def UU_pasal_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_pasal_Dokumen.extend([dataset.content[indeks].split()])
        UU_pasal_DF2List(UU_pasal_Stoprem)

        # Membuat bigram untuk UU_Pembanding_Dokumen
        UU_Pembanding_Dokumen_phrases = Phrases(
            UU_Pembanding_Dokumen, min_count=10, progress_per=1)
        bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
        UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

        # Membuat bigram untuk UU_pasal_Dokumen
        UU_pasal_Dokumen_phrases = Phrases(
            UU_pasal_Dokumen, min_count=10, progress_per=1)
        bigram_pasal = Phraser(UU_pasal_Dokumen_phrases)
        UU_pasal_Dokumen_bigram = bigram_pasal[UU_pasal_Dokumen]

        UU_Query_Dictionary = Dictionary.load(basedir +
                                              '/modelMl/new_dictionary.gensimdict')

        TfIdf_Model = TfidfModel.load(basedir +
                                      '/modelMl/new_tfidf.model')

        UU_1675_SG = Word2Vec.load(basedir +
                                   '/modelMl/UU_1675_SG_3_190.model')

        matriks_similarity = SparseTermSimilarityMatrix.load(basedir +
                                                             '/modelMl/new_matriks.matrix')

        def softcossim(kueri, dokumen):
            # Compute Soft Cosine Measure between the query and the documents.
            kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
                querry) for querry in kueri]]
            indeks = SoftCosineSimilarity(
                TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=2000, normalized=(True, True))
            similarities = indeks[kueri]
            return similarities

        UU_pasal_res = softcossim(
            UU_Pembanding_Dokumen_bigram, UU_pasal_Dokumen_bigram)

        res = []

        for a, x in enumerate(UU_pasal_res):
            pasal = []
            for y in x:
                res_formatter = y[1]*100
                presentase_formatter = float("{:.3f}".format(res_formatter))
                full_dict = {
                    'id_tbl_uu': int(UU_pasal_Stoprem.iloc[y[0]].id_tbl_uu),
                    'presentase': (presentase_formatter),
                    'uu': UU_pasal_Stoprem.iloc[y[0]].uu,
                    'tentang': UU_pasal_Stoprem.iloc[y[0]].tentang,
                    'file_arsip': UU_pasal_Stoprem.iloc[y[0]].file_arsip,
                    'status': int(UU_pasal_Stoprem.iloc[y[0]].status)
                }
                res.append(full_dict)

        return response.ok(res, "")

    except:
        return response.serverError("Tidak dapat memproses data")


def wordvecPasal():
    try:
        kalimat = request.json['kalimat']
        kategori = request.json['kategori']
        UU_Content = {'Content': [kalimat]}
        UU_df = pd.DataFrame.from_dict(UU_Content)

        def preptahap1(x): return preproses_tahap1(x)

        UU_df = pd.DataFrame(UU_df.Content.apply(preptahap1))

        UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
            [word for word in x.split() if len(word) > 3])))
        UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
            [word for word in x.split() if x.count(word) < 5])))

        s_word_indonesia = sw.words('indonesian')
        s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                                'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat'])
        s_word_indonesia.extend(['januari', 'februari', 'maret', 'april', 'mei',
                                'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])

        UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
            [word for word in x.split() if word not in (s_word_indonesia)])))

        # list UU Pembanding
        UU_Pembanding_Dokumen = []

        def UU_Pembanding_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_Pembanding_Dokumen.extend(
                    [dataset.Content[indeks].split()])
        UU_Pembanding_DF2List(UU_df)

        # list UU pasal
        uu_pasal = uu_pasal_html.query.join(uu).join(preprocessing_pasal).add_columns(
            uu.uu, uu.tentang, uu.id_kategori, uu.status, uu.file_arsip, preprocessing_pasal.uud_detail)
        UU_Stoprem = pd.read_sql_query(uu_pasal.statement, con=db.engine)

        UU_Dokumen = []

        def UU_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_Dokumen.extend([dataset.uud_detail[indeks].split()])
        UU_DF2List(UU_Stoprem)

        # Membuat bigram untuk UU_Pembanding_Dokumen
        UU_Pembanding_Dokumen_phrases = Phrases(
            UU_Pembanding_Dokumen, min_count=10, progress_per=1)
        bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
        UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

        # Membuat bigram untuk UU_Dokumen
        UU_Dokumen_phrases = Phrases(
            UU_Dokumen, min_count=10, progress_per=1)
        bigram_pasal = Phraser(UU_Dokumen_phrases)
        UU_Dokumen_bigram = bigram_pasal[UU_Dokumen]

        UU_Query_Dictionary = Dictionary.load(basedir +
                                              '/modelMl/new_dictionary.gensimdict')

        TfIdf_Model = TfidfModel.load(basedir +
                                      '/modelMl/new_tfidf.model')

        matriks_similarity = SparseTermSimilarityMatrix.load(basedir +
                                                             '/modelMl/new_matriks.matrix')

        def softcossim(kueri, dokumen):
            # Compute Soft Cosine Measure between the query and the documents.
            kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
                querry) for querry in kueri]]
            indeks = SoftCosineSimilarity(
                TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=100, normalized=(True, True))
            similarities = indeks[kueri]
            return similarities

        UU_Query_res = softcossim(
            UU_Pembanding_Dokumen_bigram, UU_Dokumen_bigram)

        for a, x in enumerate(UU_Query_res):
            # print(a)
            array = []
            for y in x:

                # print(y)
                # print(y[0])
                # print("a")
                res_formatter = y[1]*100
                presentase_formatter = float("{:.3f}".format(res_formatter))
                filter = UU_Stoprem.iloc[y[0]].id_kategori
                if kategori:
                    if filter == int(kategori):
                        tmp_dict = {
                            # "uu_querry" : UU_Querry_Stoprem_copy.iloc[a].name,
                            'test': UU_df.Content.iloc[0],
                            'id': int(UU_Stoprem.iloc[y[0]].id),
                            'presentase': (presentase_formatter),
                            'id_tbl_uu': int(UU_Stoprem.iloc[y[0]].id_tbl_uu),
                            'uu': UU_Stoprem.iloc[y[0]].uu,
                            'tentang': UU_Stoprem.iloc[y[0]].tentang,
                            'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                            'uud_content': UU_Stoprem.iloc[y[0]].uud_content,
                            'file_arsip': UU_Stoprem.iloc[y[0]].file_arsip,
                            'status': int(UU_Stoprem.iloc[y[0]].status),
                            'id_kategori': int(filter)
                        }
                        array.append(tmp_dict)
                else:
                    tmp_dict = {
                        'test': kalimat,
                        'id': int(UU_Stoprem.iloc[y[0]].id),
                        'presentase': (presentase_formatter),
                        'id_tbl_uu': int(UU_Stoprem.iloc[y[0]].id_tbl_uu),
                        'uu': UU_Stoprem.iloc[y[0]].uu,
                        'tentang': UU_Stoprem.iloc[y[0]].tentang,
                        'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                        'uud_content': UU_Stoprem.iloc[y[0]].uud_content,
                        'file_arsip': UU_Stoprem.iloc[y[0]].file_arsip,
                        'status': int(UU_Stoprem.iloc[y[0]].status),
                        'id_kategori': int(filter)
                    }
                    array.append(tmp_dict)

        return response.ok(array, "")

    except:
        return response.serverError("Tidak dapat memproses data")


def wordvecDetail(id):
    row = db.session.query(func.max(ruu.id_ruu)).scalar()

    ruu_query = ruu.query.join(ruu_pasal).add_columns(ruu_pasal.id_ruu_pasal, ruu_pasal.section_ruu, ruu_pasal.content_ruu).filter(ruu.id_ruu == int(row))
    UU_df = pd.read_sql_query(ruu_query.statement, con=db.engine)

    def preptahap1(x): return preproses_tahap1(x)

    UU_df['prep'] = pd.DataFrame(UU_df.content_ruu.apply(preptahap1))

    UU_df.prep = pd.DataFrame(UU_df.prep.apply(lambda x: ' '.join(
        [word for word in x.split() if len(word) > 3])))
    UU_df.prep = pd.DataFrame(UU_df.prep.apply(lambda x: ' '.join(
        [word for word in x.split() if x.count(word) < 5])))

    s_word_indonesia = sw.words('indonesian')
    s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                            'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat'])
    s_word_indonesia.extend(['januari', 'februari', 'maret', 'april', 'mei',
                            'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])

    UU_df.prep = pd.DataFrame(UU_df.prep.apply(lambda x: ' '.join(
        [word for word in x.split() if word not in (s_word_indonesia)])))

    # list RUU
    UU_Pembanding_Dokumen = []

    def UU_Pembanding_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Pembanding_Dokumen.extend(
                [dataset.prep[indeks].split()])
    UU_Pembanding_DF2List(UU_df)

    #list UU
    query = uu_pasal_html.query.join(uu).join(preprocessing_pasal).add_columns(preprocessing_pasal.uud_detail).filter(uu.id_tbl_uu == id)
    UU_Stoprem = pd.read_sql_query(query.statement, con=db.engine)


    UU_Dokumen = []

    def UU_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Dokumen.extend([dataset.uud_detail[indeks].split()])
    UU_DF2List(UU_Stoprem)

    # Membuat bigram untuk UU_Pembanding_Dokumen
    UU_Pembanding_Dokumen_phrases = Phrases(
        UU_Pembanding_Dokumen, min_count=10, progress_per=1)
    bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
    UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

    # Membuat bigram untuk UU_Dokumen
    UU_Dokumen_phrases = Phrases(
        UU_Dokumen, min_count=10, progress_per=1)
    bigram_pasal = Phraser(UU_Dokumen_phrases)
    UU_Dokumen_bigram = bigram_pasal[UU_Dokumen]

    UU_Query_Dictionary = Dictionary.load(basedir +
                                            '/modelMl/new_dictionary.gensimdict')

    TfIdf_Model = TfidfModel.load(basedir +
                                    '/modelMl/new_tfidf.model')

    matriks_similarity = SparseTermSimilarityMatrix.load(basedir +
                                                            '/modelMl/new_matriks.matrix')

    def softcossim(kueri, dokumen):
        # Compute Soft Cosine Measure between the query and the documents.
        kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
            querry) for querry in kueri]]
        indeks = SoftCosineSimilarity(
            TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=5, normalized=(True, True))
        similarities = indeks[kueri]
        return similarities

    UU_Query_res = softcossim(
        UU_Pembanding_Dokumen_bigram, UU_Dokumen_bigram)
    res = []

    for a, x in enumerate(UU_Query_res):
        # print(a)
        
        temp_hasil = {
            'id_ruu_pasal': int(UU_df.iloc[a].id_ruu_pasal),
            'section_ruu': UU_df.iloc[a].section_ruu,
            'content_ruu': UU_df.iloc[a].content_ruu,
            'kata': UU_df.iloc[a].prep,
            'hasil': []
        }

        for y in x:
            res_formatter = y[1]*100
            presentase_formatter = float("{:.3f}".format(res_formatter))
            hasil = {
                'id': int(UU_Stoprem.iloc[y[0]].id),
                'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                'uud_content': UU_Stoprem.iloc[y[0]].uud_content,
                'presentase': (presentase_formatter)
            }
            temp_hasil['hasil'].append(hasil)
        res.append(temp_hasil)


    return response.ok(res, "")


def wordvecPasal_new():
    try:
        kalimat = request.json['kalimat']
        UU_Content = {'Content': [kalimat]}
        UU_df = pd.DataFrame.from_dict(UU_Content)

        def preptahap1(x): return preproses_tahap1(x)

        UU_df = pd.DataFrame(UU_df.Content.apply(preptahap1))

        UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
            [word for word in x.split() if len(word) > 3])))
        UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
            [word for word in x.split() if x.count(word) < 5])))

        s_word_indonesia = sw.words('indonesian')
        s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                                'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat'])
        s_word_indonesia.extend(['januari', 'februari', 'maret', 'april', 'mei',
                                'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])

        UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
            [word for word in x.split() if word not in (s_word_indonesia)])))

        # list UU Pembanding
        UU_Pembanding_Dokumen = []

        def UU_Pembanding_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_Pembanding_Dokumen.extend(
                    [dataset.Content[indeks].split()])
        UU_Pembanding_DF2List(UU_df)

        # list UU pasal
        uu_pasal = uu_pasal_html.query.join(uu).join(preprocessing_pasal).add_columns(
            uu.uu, uu.tentang, uu.id_kategori, uu.status, uu.file_arsip, preprocessing_pasal.uud_detail)
        UU_Stoprem = pd.read_sql_query(uu_pasal.statement, con=db.engine)

        UU_Dokumen = []

        def UU_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_Dokumen.extend([dataset.uud_detail[indeks].split()])
        UU_DF2List(UU_Stoprem)

        # Membuat bigram untuk UU_Pembanding_Dokumen
        UU_Pembanding_Dokumen_phrases = Phrases(
            UU_Pembanding_Dokumen, min_count=10, progress_per=1)
        bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
        UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

        # Membuat bigram untuk UU_Dokumen
        UU_Dokumen_phrases = Phrases(
            UU_Dokumen, min_count=10, progress_per=1)
        bigram_pasal = Phraser(UU_Dokumen_phrases)
        UU_Dokumen_bigram = bigram_pasal[UU_Dokumen]

        UU_Query_Dictionary = Dictionary.load(basedir +
                                              '/modelMl/new_dictionary.gensimdict')

        TfIdf_Model = TfidfModel.load(basedir +
                                      '/modelMl/new_tfidf.model')

        matriks_similarity = SparseTermSimilarityMatrix.load(basedir +
                                                             '/modelMl/new_matriks.matrix')

        def softcossim(kueri, dokumen):
            # Compute Soft Cosine Measure between the query and the documents.
            kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
                querry) for querry in kueri]]
            indeks = SoftCosineSimilarity(
                TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=100, normalized=(True, True))
            similarities = indeks[kueri]
            return similarities

        UU_Query_res = softcossim(
            UU_Pembanding_Dokumen_bigram, UU_Dokumen_bigram)

        for a, x in enumerate(UU_Query_res):
            # print(a)
            array = []
            for y in x:

                # print(y)
                # print(y[0])
                # print("a")
                res_formatter = y[1]*100
                presentase_formatter = float("{:.3f}".format(res_formatter))
                tmp_dict = {
                    'test': kalimat,
                    'id': int(UU_Stoprem.iloc[y[0]].id),
                    'presentase': (presentase_formatter),
                    'id_tbl_uu': int(UU_Stoprem.iloc[y[0]].id_tbl_uu),
                    'uu': UU_Stoprem.iloc[y[0]].uu,
                    'tentang': UU_Stoprem.iloc[y[0]].tentang,
                    'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                    'uud_content': UU_Stoprem.iloc[y[0]].uud_content,
                    'file_arsip': UU_Stoprem.iloc[y[0]].file_arsip,
                    'status': int(UU_Stoprem.iloc[y[0]].status),
                    'id_kategori': int(UU_Stoprem.iloc[y[0]].id_kategori)
                }
                array.append(tmp_dict)

        res = []
        def key_func(k): return k['id_tbl_uu']

        for k, g in groupby(sorted(array, key=key_func), key=key_func):
            obj = {'id_tbl_uu': k, 'uu': '',
                'jumlah': 0, 'tentang': '', 'file_arsip': '', 'status': '', 'id_kategori': '', 'pasal': []}
            for group in g:
                if not obj['uu']:
                    obj['uu'] = group['uu']
                    obj['tentang'] = group['tentang']
                    obj['file_arsip'] = group['file_arsip']
                    obj['status'] = group['status']
                    obj['id_kategori'] = group['id_kategori']
                obj['jumlah'] = obj['jumlah'] + 1
                pasal = {
                    'id': group['id'],
                    'presentase': group['presentase'],
                    'uud_id': group['uud_id'],
                    'uud_content': group['uud_content']
                }
                obj['pasal'].append(pasal)
            res.append(obj)

        hasil = sorted(res, key=lambda res: res['jumlah'], reverse=True)

        return response.ok(hasil, "")

    except:
        return response.serverError("Tidak dapat memproses data")

def harmonisasiKeyword():
    try:
        row = db.session.query(func.max(ruu.id_ruu)).scalar()

        ruu_query = ruu.query.filter(ruu.id_ruu == int(row))
        UU_df = pd.read_sql_query(ruu_query.statement, con=db.engine)

        # list UU Pembanding
        UU_Pembanding_Dokumen = []

        def UU_Pembanding_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_Pembanding_Dokumen.extend(
                    [dataset.keyword_ruu[indeks].split()])
        UU_Pembanding_DF2List(UU_df)

        # list UU pasal
        uud = preprocessing.query.join(uu).filter(uu.status == 3).add_columns(
            uu.uu, uu.tentang, uu.file_arsip, uu.status)
        UU_pasal_Stoprem = pd.read_sql_query(uud.statement, con=db.engine)
        UU_pasal_Dokumen = []

        def UU_pasal_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_pasal_Dokumen.extend([dataset.content[indeks].split()])
        UU_pasal_DF2List(UU_pasal_Stoprem)

        # Membuat bigram untuk UU_Pembanding_Dokumen
        UU_Pembanding_Dokumen_phrases = Phrases(
            UU_Pembanding_Dokumen, min_count=10, progress_per=1)
        bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
        UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

        # Membuat bigram untuk UU_pasal_Dokumen
        UU_pasal_Dokumen_phrases = Phrases(
            UU_pasal_Dokumen, min_count=10, progress_per=1)
        bigram_pasal = Phraser(UU_pasal_Dokumen_phrases)
        UU_pasal_Dokumen_bigram = bigram_pasal[UU_pasal_Dokumen]

        UU_Query_Dictionary = Dictionary.load(basedir +
                                              '/modelMl/new_dictionary.gensimdict')

        TfIdf_Model = TfidfModel.load(basedir +
                                      '/modelMl/new_tfidf.model')

        UU_1675_SG = Word2Vec.load(basedir +
                                   '/modelMl/UU_1675_SG_3_190.model')

        matriks_similarity = SparseTermSimilarityMatrix.load(basedir +
                                                             '/modelMl/new_matriks.matrix')

        def softcossim(kueri, dokumen):
            # Compute Soft Cosine Measure between the query and the documents.
            kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
                querry) for querry in kueri]]
            indeks = SoftCosineSimilarity(
                TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=2000, normalized=(True, True))
            similarities = indeks[kueri]
            return similarities

        UU_pasal_res = softcossim(
            UU_Pembanding_Dokumen_bigram, UU_pasal_Dokumen_bigram)

        res = []

        for a, x in enumerate(UU_pasal_res):
            for y in x:
                res_formatter = y[1]*100
                presentase_formatter = float("{:.3f}".format(res_formatter))
                full_dict = {
                    'id_tbl_uu': int(UU_pasal_Stoprem.iloc[y[0]].id_tbl_uu),
                    'presentase': (presentase_formatter),
                    'uu': UU_pasal_Stoprem.iloc[y[0]].uu,
                    'tentang': UU_pasal_Stoprem.iloc[y[0]].tentang,
                    'file_arsip': UU_pasal_Stoprem.iloc[y[0]].file_arsip,
                    'status': int(UU_pasal_Stoprem.iloc[y[0]].status)
                }
                res.append(full_dict)

        return response.ok(res,"")

    except:
        return response.serverError("Tidak dapat memproses data")

def showDetail(id):
    try:
        row = db.session.query(func.max(ruu.id_ruu)).scalar()

        ruu_query = ruu.query.filter(ruu.id_ruu == int(row))
        UU_df = pd.read_sql_query(ruu_query.statement, con=db.engine)

        # list RUU
        UU_Pembanding_Dokumen = []

        def UU_Pembanding_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_Pembanding_Dokumen.extend(
                    [dataset.keyword_ruu[indeks].split()])
        UU_Pembanding_DF2List(UU_df)

        #list UU
        query = uu_pasal_html.query.join(uu).join(preprocessing_pasal).add_columns(preprocessing_pasal.uud_detail).filter(uu.id_tbl_uu == id)
        UU_Stoprem = pd.read_sql_query(query.statement, con=db.engine)


        UU_Dokumen = []

        def UU_DF2List(dataset):
            for indeks, line in dataset.iterrows():
                # print(indeks)
                UU_Dokumen.extend([dataset.uud_detail[indeks].split()])
        UU_DF2List(UU_Stoprem)

        # Membuat bigram untuk UU_Pembanding_Dokumen
        UU_Pembanding_Dokumen_phrases = Phrases(
            UU_Pembanding_Dokumen, min_count=10, progress_per=1)
        bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
        UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

        # Membuat bigram untuk UU_Dokumen
        UU_Dokumen_phrases = Phrases(
            UU_Dokumen, min_count=10, progress_per=1)
        bigram_pasal = Phraser(UU_Dokumen_phrases)
        UU_Dokumen_bigram = bigram_pasal[UU_Dokumen]

        UU_Query_Dictionary = Dictionary.load(basedir +
                                                '/modelMl/new_dictionary.gensimdict')

        TfIdf_Model = TfidfModel.load(basedir +
                                        '/modelMl/new_tfidf.model')

        matriks_similarity = SparseTermSimilarityMatrix.load(basedir +
                                                                '/modelMl/new_matriks.matrix')

        def softcossim(kueri, dokumen):
            # Compute Soft Cosine Measure between the query and the documents.
            kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
                querry) for querry in kueri]]
            indeks = SoftCosineSimilarity(
                TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=50, normalized=(True, True))
            similarities = indeks[kueri]
            return similarities

        UU_Query_res = softcossim(
            UU_Pembanding_Dokumen_bigram, UU_Dokumen_bigram)
        temp_hasil = {
            'kata': UU_df.iloc[0].keyword_ruu,
            'hasil': []
        }

        for a, x in enumerate(UU_Query_res):

            for y in x:
                res_formatter = y[1]*100
                presentase_formatter = float("{:.3f}".format(res_formatter))
                hasil = {
                    'id': int(UU_Stoprem.iloc[y[0]].id),
                    'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                    'uud_content': UU_Stoprem.iloc[y[0]].uud_content,
                    'presentase': (presentase_formatter)
                }
                temp_hasil['hasil'].append(hasil)

        return response.ok(temp_hasil, "")

    except:
        temp_hasil = {
            'hasil': []
        }
        return response.ok(temp_hasil,"Data Kosong")
