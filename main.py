from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_seeder import FlaskSeeder
from flask_restx import Api

app = Flask(__name__)
api = Api(app)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

seeder = FlaskSeeder()
seeder.init_app(app, db)

from app.controller import HarmonisasiController
from app.controller import UndangController

from flask import request
from flask_restx import Resource


@app.route('/undang', methods=['POST'])
def ekstrak():
    if request.method == 'POST':
        return UndangController.ekstrak()


@app.route('/undang/tambahUU', methods=['POST'])
def tambahUU():
    if request.method == 'POST':
        return UndangController.tambahUU()


@app.route('/undang/ubahUU', methods=['POST'])
def ubahUU():
    if request.method == 'POST':
        return UndangController.ubahUU()


@app.route('/undang/prep', methods=['GET'])
def prep():
    if request.method == 'GET':
        return UndangController.prep()


@app.route('/undang/prep_pasal', methods=['GET'])
def prep_pasal():
    if request.method == 'GET':
        return UndangController.prep_pasal()


@app.route('/undang/tambahPasal', methods=['POST'])
def tambahPasal():
    if request.method == 'POST':
        return UndangController.tambahPasal()


@app.route('/undang/ubahPasal', methods=['POST'])
def ubahPasal():
    if request.method == 'POST':
        return UndangController.ubahPasal()


@app.route('/harmonisasi/file/<namaFile>', methods=['GET'])
def harmonisasi(namaFile):
    if request.method == 'GET':
        return HarmonisasiController.test(namaFile)


@app.route('/harmonisasi/wordvec/<namaFile>', methods=['GET'])
def wordvec(namaFile):
    if request.method == 'GET':
        return HarmonisasiController.wordvec(namaFile)


@app.route('/harmonisasi/coba', methods=['GET'])
def coba():
    if request.method == 'GET':
        return HarmonisasiController.coba()


@app.route('/harmonisasi/detail/<rank>', methods=['GET'])
def detail(rank):
    if request.method == 'GET':
        return HarmonisasiController.detail(rank)


@app.route('/drafting/<search>', methods=['GET'])
def drafting(search):
    return HarmonisasiController.drafting(search)


@app.route('/harmonisasiPasal', methods=['POST'])
def harmonisasiPasal():
    if request.method == 'POST':
        return HarmonisasiController.harmonisasiPasal()


@app.route('/wordvecPasal', methods=['POST'])
def wordvecPasal():
    if request.method == 'POST':
        return HarmonisasiController.wordvecPasal_new()


@app.route('/undang/tambahPasal_Bulk', methods=['POST'])
def tambahPasal_Bulk():
    if request.method == 'POST':
        return UndangController.tambahPasal_Bulk()


@app.route('/harmonisasi/wordvec_detail/<id>', methods=['GET'])
def wordvecDetail(id):
    if request.method == 'GET':
        return HarmonisasiController.wordvecDetail(id)


@app.route('/v1/harmonisasi/keyword', methods=['GET'])
def harmonisasiKeyword():
    if request.method == 'GET':
        return HarmonisasiController.harmonisasiKeyword()


@app.route('/v1/harmonisasi/show/<id>', methods=['GET'])
def showDetail(id):
    if request.method == 'GET':
        return HarmonisasiController.showDetail(id)

if __name__ == "__main__":
    app.run()