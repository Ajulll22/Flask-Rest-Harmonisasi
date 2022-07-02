from app import response
from app.model import uud
from app.model.uud import preprocessing, preprocessing_pasal, uu, uu_pasal_html
from main import db
from flask import request, abort
import pickle
import fitz
from nltk.corpus import stopwords as sw
import os
import re
import string
import pandas as pd


dir = "C:/xampp/htdocs/omnilaw/uploads/"


def preproses_tahap1(text):
    text = text.lower()
    text = re.sub('www.peraturan.go.id', ' ', text)
    text = re.sub('www.bphn.go.id', ' ', text)
    text = re.sub('www.hukumonline.com', ' ', text)
    text = re.sub('www.djpp.depkumham.go.iddjpp.depkumham.go.id', ' ', text)
    text = re.sub('www.djpp.depkumham.go.id', ' ', text)
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


def ekstrak():
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

    res = []

    hasil = {'content': UU_df.iloc[0].Content}
    res.append(hasil)

    return response.ok(res, "")


def tambahUU():
    dir = "C:/xampp/htdocs/peraturan-uu/public/assets/pdf/"
    file = request.json['file']
    id_tbl_uu = request.json['id_tbl_uu']

    doc = fitz.open(dir + file)
    Content = ""
    for page in doc:
        Content = Content + " " + page.get_text("text")
    UU_Content = {'Content': [Content]}
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

    res = []

    content = UU_df.iloc[0].Content

    insert = preprocessing(id_tbl_uu=id_tbl_uu, content=content)
    db.session.add(insert)
    db.session.commit()

    hasil = {'text': Content}
    res.append(hasil)

    return response.ok(res, "")


def ubahUU():
    dir = "C:/xampp/htdocs/omnilaw/uploads/"
    file = request.json['file']
    id_tbl_uu = request.json['id_tbl_uu']

    doc = fitz.open(dir + file)
    Content = ""
    for page in doc:
        Content = Content + " " + page.get_text("text")
    UU_Content = {'Content': [Content]}
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

    res = []

    content = UU_df.iloc[0].Content

    insert = preprocessing.query.filter_by(id_tbl_uu=id_tbl_uu).first()
    insert.content = content
    db.session.commit()

    hasil = {'text': Content}
    res.append(hasil)

    return response.ok(res, "")


def tambahPasal():
    id_uu_pasal = request.json['id_uu_pasal']
    uud_content = request.json['uud_content']

    UU_Content = {'Content': [uud_content]}
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

    res = []

    uud_detail = UU_df.iloc[0].Content

    # insert = preprocessing_pasal(
    #     id_uu_pasal=id_uu_pasal, uud_detail=uud_detail)
    # db.session.add(insert)
    # db.session.commit()

    return response.ok(uud_detail, "Data Berhasil Diproses")


def ubahPasal():
    id_uu_pasal = request.json['id_uu_pasal']
    uud_content = request.json['uud_content']

    UU_Content = {'Content': [uud_content]}
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

    res = []

    uud_detail = UU_df.iloc[0].Content

    insert = preprocessing_pasal.query.filter_by(
        id_uu_pasal=id_uu_pasal).first()
    insert.uud_detail = uud_detail
    db.session.commit()

    return response.ok("", "Data Berhasil Diproses")


def prep():
    data = uu.query.all()
    for i in data:
        id_tbl_uu = i.id_tbl_uu
        judul = i.uu
        potong = judul.split()
        tahun = potong[-1]

        insert = uu.query.filter_by(
            id_tbl_uu=id_tbl_uu).first()
        insert.tahun = tahun
        db.session.commit()

    return response.ok("", "berhasil")


def prep_pasal():
    data = uu_pasal_html.query.all()
    for i in data:
        Content = i.uud_content
        id_uu_pasal = i.id
        UU_Content = {'Content': [Content]}
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

        uud_detail = UU_df.iloc[0].Content

        insert = preprocessing_pasal(
            id_uu_pasal=id_uu_pasal, uud_detail=uud_detail)
        db.session.add(insert)
        db.session.commit()

    return response.ok("", "berhasil")


def tambahPasal_Bulk():
    try:
        data = request.json['data']

        if data is None:
            return response.badRequest("", "Request tidak ditemukan")

        UU_df = pd.DataFrame.from_dict(data)
        UU_df.rename(columns={'uud_content': 'uud_detail'}, inplace=True)

        def preptahap1(x): return preproses_tahap1(x)

        UU_df.uud_detail = pd.DataFrame(UU_df.uud_detail.apply(preptahap1))

        UU_df.uud_detail = pd.DataFrame(UU_df.uud_detail.apply(lambda x: ' '.join(
            [word for word in x.split() if len(word) > 3])))
        UU_df.uud_detail = pd.DataFrame(UU_df.uud_detail.apply(lambda x: ' '.join(
            [word for word in x.split() if x.count(word) < 5])))

        s_word_indonesia = sw.words('indonesian')
        s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                                'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat'])
        s_word_indonesia.extend(['januari', 'februari', 'maret', 'april', 'mei',
                                'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])

        UU_df.uud_detail = pd.DataFrame(UU_df.uud_detail.apply(lambda x: ' '.join(
            [word for word in x.split() if word not in (s_word_indonesia)])))

        dict = UU_df.to_dict(orient='records')

        db.engine.execute(preprocessing_pasal.__table__.insert(), dict)

        return response.ok("", "Data Berhasil Diproses")

    except Exception as e:
        return response.serverError("Tidak dapat memproses data")
