from sqlalchemy import Column, Integer, String, Float
from geoalchemy2 import Geometry
from app.models.base import TenantBase


class WorkerLocation(TenantBase):
    __tablename__ = "worker_locations"

    worker_id = Column(Integer, index=True, nullable=False)
    name = Column(String(255))

    # PostGIS geometry column for storing GPS coordinates (longitude, latitude)
    # SRID 4326 is the standard WGS 84 coordinate system used by GPS
    location = Column(Geometry("POINT", srid=4326))

    # Fallback/raw columns if needed
    lat = Column(Float)
    lon = Column(Float)
