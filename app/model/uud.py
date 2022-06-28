from app import db
from datetime import datetime


class Tbl_uu(db.Model):
    id_tbl_uu = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uu = db.Column(db.String(255), nullable=False)
    tentang = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Tbl_uu {}>'.format(self.uu)


class Tbl_uu_pasal(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_tbl_uu = db.Column(db.Integer, db.ForeignKey('tbl_uu.id_tbl_uu'))
    uud_id = db.Column(db.String(255), nullable=True)
    uud_section = db.Column(db.String(100), nullable=True)
    uud_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return '<Tbl_uu_pasal {}>'.format(self.uud_id)


class uu(db.Model):
    id_tbl_uu = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uu = db.Column(db.String(1000), nullable=False)
    tahun = db.Column(db.Integer, nullable=True)
    tentang = db.Column(db.String(1000), nullable=False)
    file_arsip = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    id_kategori = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<uu {}>'.format(self.uu)


class uu_pasal_html(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_tbl_uu = db.Column(db.Integer, db.ForeignKey('uu.id_tbl_uu'))
    uud_id = db.Column(db.String(255), nullable=True)
    uud_section = db.Column(db.String(100), nullable=True)
    uud_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return '<uu_pasal_html {}>'.format(self.uud_id)


class preprocessing(db.Model):
    id_preprocessing = db.Column(
        db.Integer, primary_key=True, autoincrement=True)
    id_tbl_uu = db.Column(db.Integer, db.ForeignKey('uu.id_tbl_uu'))
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<preprocessing {}>'.format(self.content)


class preprocessing_pasal(db.Model):
    __tablename__ = "preprocessing_pasal"
    id_prep_pasal = db.Column(
        db.Integer, primary_key=True, autoincrement=True)
    id_uu_pasal = db.Column(db.Integer, db.ForeignKey('uu_pasal_html.id'))
    uud_detail = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<preprocessing_pasal {}>'.format(self.uud_detail)
