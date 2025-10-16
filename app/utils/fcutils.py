import requests
from fastapi import HTTPException
from requests import RequestException
from shapely import wkt, errors

from core import settings


def fetch_parcel_by_id(
        access_token: str,
        parcel_id: str
):

    try:
        response_json = requests.get(
            url=str(settings.GATEKEEPER_BASE_URL).strip("/") + "/api/proxy/farmcalendar/api/v1/FarmParcels/{}/?format=json".format(parcel_id),
            headers={"Content-Type": "application/json", "Authorization": "Bearer {}".format(access_token)}
        )
    except RequestException:
        raise HTTPException(
            status_code=400,
            detail="Error during proxy call via gk"
        )

    if response_json.status_code == 404:
        return None

    return response_json.json()


def fetch_parcel_lat_lon(
        parcel: dict
):

    # First check if the pair (lat,lon) exists, we can use these if they do
    if parcel["location"]["lat"] and parcel["location"]["long"]:
        return parcel["location"]["lat"], parcel["location"]["long"]

    # if (lat,lon) is set to (None,None) then calculate the centroid from the WKT object and use that as
    wkt_polygon = parcel["hasGeometry"]["asWKT"]

    # Parse the POLYGON(...) object
    try:
        base_geometry = wkt.loads(wkt_polygon)
    except errors.ShapelyError as se:
        raise HTTPException(
            status_code=400,
            detail="Error during WKT parsing, provided WKT format has issues: {}".format(se)
        )

    c_latitude = base_geometry.centroid.x
    c_longitude = base_geometry.centroid.y

    return c_latitude, c_longitude
