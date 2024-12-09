from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TarjetaCredito(db.Model):
    __tablename__ = 'tarjeta_credito'

    id = db.Column(db.Integer, primary_key=True)
    numero_tarjeta = db.Column(db.String(16), nullable=False)
    fecha_expiracion = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    titular = db.Column(db.String(100), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    usuario = db.relationship('Usuario', backref=db.backref('tarjetas', lazy=True))
