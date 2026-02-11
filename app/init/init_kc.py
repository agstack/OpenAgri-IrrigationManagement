from models import CropKc

from core.config import INITIAL_KC
from db.session import SessionLocal
from api import deps


def insert_crop_kc_into_db():
    """
    Inserts default KC values into DB only if missing.
    """
    db = SessionLocal()

    try:
        for crop_name, kc_values in INITIAL_KC.items():
            kc_init, kc_mid, kc_end = kc_values

            exists = db.query(CropKc).filter_by(crop=crop_name).first()
            if exists:
                continue

            entry = CropKc(
                crop=crop_name,
                kc_init=kc_init,
                kc_mid=kc_mid,
                kc_end=kc_end
            )
            db.add(entry)

        db.commit()
    finally:
        db.close()