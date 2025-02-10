# Irrigation service

# Description

The OpenAgri Irrigation service provides the calculation of referent evapotranspiration (ETo) as well as the analysis of \
the soil moisture of parcels/plots of land. \
These functionalities can be used via the REST APIs, which provide these them in a linked data format (using JSON-LD). \
This service conforms to the OpenAgri Common Semantic Model (OCSM).

# Requirements

<ul>
    <li>git</li>
    <li>docker</li>
    <li>docker-compose</li>
</ul>

Docker version used during development: 27.0.3

# Installation

There are two ways to install this service, via docker (preferred) or directly from source.

<h3> Deploying from source </h3>

When deploying from source, use python 3:11.\
Also, you should use a [venv](https://peps.python.org/pep-0405/) when doing this.

A list of libraries that are required for this service is present in the "requirements.txt" file.\
This service uses FastAPI as a web framework to serve APIs, alembic for database migrations and sqlalchemy for database ORM mapping.

<h3> Deploying via docker </h3>

After installing <code>docker-compose</code> you can run the following commands to run the application:

```
docker compose build
docker compose up
```

The application will be served on http://127.0.0.1:80 (I.E. typing localhost/docs in your browser will load the swagger documentation)

# Documentation

# ETO

The service provides ETo calculations for different parcels/locations. \
In order to do this, the service requires one or more locations to be added. \
You can add locations via the following two APIs:

<h3>POST</h3>

```
/api/v1/location/parcel-wkt/

/api/v1/location/
```

The APIs differ in their request bodies, the /parcel-wkt/ api expects a WKT compliant polygon that represents a parcel's geometry.

The /api/v1/location/ API expects the name of the place where the parcel is located, and the country that it's in. \
This API is more of a quality of life one, if a parcel/location is close to a town/village.

<h3>POST</h3>

```
/api/v1/location/parcel-wkt/
```

Request body:

```json
{
  "coordinates": "POLYGON ((16.3918171754758 52.2845776020972, 16.3917494080095 52.2846027134549, 16.3919900323056 52.2850299561796, 16.3924263252882 52.2858045976875, 16.3927582118358 52.286390756684, 16.3930886652367 52.2869743680154, 16.3934208097949 52.28756094944, 16.3934419208883 52.2875983114338, 16.3937337853878 52.2881148407101, 16.3939318041838 52.2884652785805, 16.3941551608466 52.2888605503256, 16.3943586084041 52.2892205826293, 16.3945934888104 52.289636232648, 16.3949241041235 52.2902212836039, 16.3952566311392 52.2908072644052, 16.3955894075119 52.2913936684795, 16.395923637163 52.2919826173955, 16.395949403074 52.2920280190259, 16.4002575057698 52.2910810251215, 16.3988093546172 52.2891372236252, 16.3998210258441 52.2889828598088, 16.399192306522 52.2877635138971, 16.39905146601 52.2875627085851, 16.3989201005977 52.2873703982278, 16.3976834611891 52.2859014266173, 16.3974738832239 52.2857876393351, 16.3922772878688 52.2846333456815, 16.3918171754758 52.2845776020972))"
}
```

You can read more about the WKT format [here](https://libgeos.org/specifications/wkt/). \
A polygon is expected here, since farms/parcels/plots of land are very often divided into irregular geometric shapes.

Response example:
```json
{
  "message": "Successfully created new location!"
}
```

<h3>POST</h3>

```
/api/v1/location/
```

Request body:

```json
{
  "city_name": "Belgrade",
  "country_code": "RS"
}
```

The country_code should be the ISO country code of the country (either 2 or 3 characters). \
The city names can be in any language, for example in Serbian, "Београд" would work here as well.

Response example:
```json
{
  "message": "Successfully created new location!"
}
```

When you've added a couple of locations, you can view them using the following API:

<h3>GET</h3>

```
/api/v1/location/
```

Request body: None

Response example:

```json
{
  "locations": [
    {
      "id": 1,
      "latitude": 12.234543,
      "longitude": 56.123453,
      "city_name": null,
      "country_code": null
    },
    {
      "id": 2,
      "latitude": 37.074448,
      "longitude": 22.430241,
      "city_name": "Sparti",
      "country_code": "GR"
    }
  ]
}
```

Now that you've added a couple of locations to the service, you can request ETo calculations from it using the following API:

<h3>POST</h3>

```
/api/v1/eto/get-calculations/{location_id}
```

Path parameters:
1. location_id: the location id for which you want to get the calculated ETo values.

Request Body:

```json
{
  "from_date": "2024-09-20",
  "to_date": "2024-09-28"
}
```

Response example:

```json
{
  "calculations": [
    {
      "date": "2024-09-20",
      "value": 6.5
    },
    {
      "date": "2024-09-21",
      "value": 6.6
    },
    {
      "date": "2024-09-22",
      "value": 6.8
    },
    {
      "date": "2024-09-23",
      "value": 6.7
    },
    {
      "date": "2024-09-24",
      "value": 5.4
    }
  ]
}
```

The values are represented in millimetres per day of evapotranspiration. \
The system generates these values according to weather data that is collected through the openweathermap API. \
This data is collected each day at around midnight. \

You can also remove a location, alongside it's calculated ETo values using the following API:

<h3>DELETE</h3>

```
/api/v1/location/{location_id}
```

Path parameters:
1. location_id: the id of the location you want to remove.

Request body: None

Response example:

```json
{
    "message": "Successfully deleted location"
}
```

# SOIL MOISTURE

<h3>GET/DELETE</h3>

```
/api/v1/dataset/{dataset_id}
```

Example responses for GET and DELETE respectively:

```json
[
  {
    "dataset_id": 23,
    "date": "2024-10-17T13:18:05.054Z",
    "soil_moisture_10": 7.3,
    "soil_moisture_20": 2.4,
    "soil_moisture_30": 2.2,
    "soil_moisture_40": 1.3,
    "soil_moisture_50": 1.1,
    "soil_moisture_60": 1.1,
    "rain": 0.6,
    "temperature": 22.3,
    "humidity": 66.33
  }
]
```

```json
{
  "status_code":201, 
  "detail": "Successfully deleted"
}
```

<h3>POST</h3>

```
/api/v1/dataset/
```

Input JSON:

```json
{
   "dataset_id": 23,
   "date": "2024-10-17T13:18:05.054Z",
   "soil_moisture_10": 7.3,
   "soil_moisture_20": 2.4,
   "soil_moisture_30": 2.2,
   "soil_moisture_40": 1.3,
   "soil_moisture_50": 1.1,
   "soil_moisture_60": 1.1,
   "rain": 0.6,
   "temperature": 22.3,
   "humidity": 66.33
}
```

```
/api/v1/dataset/
```

Example response:
```json
{
  "dataset_id": 23,
  "date": "2024-10-17T13:18:05.054Z",
  "soil_moisture_10": 7.3,
  "soil_moisture_20": 2.4,
  "soil_moisture_30": 2.2,
  "soil_moisture_40": 1.3,
  "soil_moisture_50": 1.1,
  "soil_moisture_60": 1.1,
  "rain": 0.6,
  "temperature": 22.3,
  "humidity": 66.33 
}
```

<h3>GET</h3>

```
/api/v1/dataset/{dataset_id}/analysis
```

Example response:
```json
{
  "dataset_id": 23,
  "time_period": [
    "2024-10-17T13:24:35.198Z", "2024-10-18T13:24:35.198Z"
  ],
  "irrigation_events_detected": 12,
  "precipitation_events": 10,
  "high_dose_irrigation_events": 3,
  "high_dose_irrigation_events_dates": [
    "2024-10-17T13:24:35.198Z"
  ],
  "field_capacity": [
    [
      10,
      0.17
    ]
  ],
  "stress_level": [
    [
      10,
      0.04
    ]
  ],
  "number_of_saturation_days": 1,
  "saturation_dates": [
    "2024-10-17T13:24:35.198Z"
  ],
  "no_of_stress_days": 1,
  "stress_dates": [
    "2024-10-17T13:24:35.198Z"
  ]
}
```

<h3>Quick start for the ETo:</h3>

A user would input the location of their parcel/plot of land via the POST /api/v1/location/ or POST /api/v1/location/parcel-wkt/ APIs (or multiple parcels). \
The system requests weather data for these locations at around midnight every day. \
Once a user wishes to view ETo values, they may call the POST /api/v1/eto/get-calculations/{location_id} API. \
This API will return a list of calculations, for the given days.

<h3>Example usage for the soil moisture analysis:</h3>

Use POST /api/v1/dataset/ to upload your data to the database.
GET and DELETE requests with the same URL as previously mentioned are for fetching and deleting data from database, respectively.

For obtaining analysis of soil moisture, use GET /api/v1/dataset/{dataset_id}/analysis request. 

# Contribution
Please contact the maintainer of this repository

# License
[European Union Public License 1.2](https://github.com/openagri-eu/irrigation-management/blob/main/LICENSE)
