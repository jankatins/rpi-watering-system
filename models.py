import os
import sys
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensor_readings.db'


db = SQLAlchemy(app)


class SensorReadings(db.Model):
    __tablename__ = 'sensorreadings'
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(250), nullable=False)
    creation_date = db.Column('creation_time', db.DateTime, default=datetime.utcnow)
    value = db.Column('value', db.Integer)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'           : self.id,
           'source'       : self.source,
           'creation_date': self.creation_date.strftime('%Y-%m-%dT%H:%M:%S+0000'),
           'value'        : self.value
       } 
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
if not os.path.exists("sensor_readings.db"):
    db.create_all()