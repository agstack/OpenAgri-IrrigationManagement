from sqlalchemy import Column, Integer, Float, Date, String

from db.base_class import Base


class Dataset(Base):
    __tablename__ = "dataset"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(String)
    date = Column(Date)
    soil_moisture_10 = Column(Float)
    soil_moisture_20 = Column(Float)
    soil_moisture_30 = Column(Float)
    soil_moisture_40 = Column(Float)
    soil_moisture_50 = Column(Float)
    soil_moisture_60 = Column(Float)
    rain = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
