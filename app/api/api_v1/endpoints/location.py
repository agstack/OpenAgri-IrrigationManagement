import requests
from fastapi import APIRouter, Depends, HTTPException
from requests import RequestException
from shapely import wkt, errors
from sqlalchemy.orm import Session

from api.deps import get_jwt, get_db
from schemas import Message, LocationCreate, NewLocationWKT, LocationsDB, LocationDB
from crud import location

router = APIRouter()

@router.post("/parcel-wkt/", response_model=Message, dependencies=[Depends(get_jwt)])
def add_location_wkt(
    location_information: NewLocationWKT,
    db: Session = Depends(get_db)
) -> Message:
    """
    Add a new location based on parcel information (wkt format)

    An example of a parcel represented with wkt:
    POLYGON ((40.2 21.2, 40.3 21.3, 40.5 25.2, 36.1 23.1, 40.2 21.2))
    """

    try:
        base_geometry = wkt.loads(location_information.coordinates)
    except errors.ShapelyError as se:
        raise HTTPException(
            status_code=400,
            detail="Error during WKT parsing, please check format, floats,"
                   " that it encompasses a closed structure. Specific exception information: [{}]".format(se)
        )

    c_latitude = base_geometry.centroid.x
    c_longitude = base_geometry.centroid.y

    # Check whether opentopo returns an elevation
    try:
        response_otd = requests.get(
            url="https://api.opentopodata.org/v1/{}?locations={},{}".format("eudem25m", c_latitude, c_longitude)
        )
    except RequestException:
        raise HTTPException(
            status_code=400,
            detail="Error, can't check topographical location of wkt parcel, please try again later."
        )

    if (response_otd.status_code / 100) != 2:
        raise HTTPException(
            status_code=400,
            detail="Error, topographical api issue, please try again later."
        )

    body = response_otd.json()

    if "results" not in body:
        raise HTTPException(
            status_code=400,
            detail="Error, topographical api failed to return a result, please try again later."
        )

    if len(body["results"]) == 0:
        raise HTTPException(
            status_code=400,
            detail="Error, topographical api returned an empty results set, please try again later."
        )

    if "elevation" not in body["results"][0]:
        raise HTTPException(
            status_code=400,
            detail="Error, elevation data missing from topographical api call, please try again later."
        )

    if not body["results"][0]["elevation"]:
        raise HTTPException(
            status_code=400,
            detail="Error, wkt coordinates do not point to a European location, only European continental parcels "
                   "are supported currently."
        )

    location.create(db=db, obj_in=LocationCreate(latitude=float(c_latitude), longitude=float(c_longitude)))

    return Message(message="Successfully created new location!")


@router.delete("/{location_id}", response_model=Message, dependencies=[Depends(get_jwt)])
def remove_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove a location via ID (this also removes all recordings stored in database for this location)
    """

    location_db = location.get(db=db, id=location_id)

    if location_db is None:
        raise HTTPException(
            status_code=400,
            detail="Location with ID:{} does not exist.".format(location_id)
        )

    location.remove(db=db, id=location_id)

    return Message(
        message="Successfully deleted the location"
    )

@router.get("/{location_id}", response_model=LocationDB, dependencies=[Depends(get_jwt)])
def get_location(
    location_id: int,
    db: Session = Depends(get_db)
):

    """
    View a location by ID.
    """

    location_db = location.get(db=db, id=location_id)

    if location_db is None:
        raise HTTPException(
            status_code=400,
            detail="Error, Location with ID:{} does not exist.".format(location_id)
        )

    return location_db

@router.get("/", response_model=LocationsDB, dependencies=[Depends(get_jwt)])
def get_all(
    db: Session = Depends(get_db)
):
    """
    Get all locations
    """

    locations = location.get_all(db=db)

    return LocationsDB(locations=locations)
