from models import SoilTypeValues

from core.config import SOIL_WILTING_POINTS
from db.session import SessionLocal
from api import deps

def insert_soil_values_into_db():
    """
    Inserts default WP values into DB only if missing.
    """
    db = SessionLocal()

    try:
        for soil_type, soil_values in SOIL_WILTING_POINTS.items():
            fc, wp = soil_values
            exists = db.query(SoilTypeValues).filter_by(soil_type=soil_type).first()
            if exists:
                continue

            entry = SoilTypeValues(
                soil_type=soil_type,
                field_capacity=fc,
                wilting_point=wp
            )
            db.add(entry)

        db.commit()
    finally:
        db.close()