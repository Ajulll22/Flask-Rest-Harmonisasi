from app import db
from datetime import datetime


class ruu(db.Model):
    id_ruu = db.Column(db.Integer, primary_key=True, autoincrement=True)
    judul_ruu = db.Column(db.String(100), nullable=True)
    keyword_ruu = db.Column(db.String(100), nullable=True)
    tentang_ruu = db.Column(db.String(150), nullable=True)
    file_ruu = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return '<ruu {}>'.format(self.judul_ruu)


class ruu_pasal(db.Model):
    id_ruu_pasal = db.Column(db.Integer, primary_key=True, autoincrement=True)
    section_ruu = db.Column(db.String(100), nullable=True)
    content_ruu = db.Column(db.String(150), nullable=True)
    id_ruu = db.Column(db.Integer, db.ForeignKey('ruu.id_ruu'))

    def __repr__(self):
        return '<ruu_pasal {}>'.format(self.section_ruu)