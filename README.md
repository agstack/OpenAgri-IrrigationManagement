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

# A List of APIs
A full list of APIs can be viewed [here](https://editor-next.swagger.io/?url=https://gist.githubusercontent.com/vlf-stefan-drobic/bf78e620b5a9c5ea22498fd26edb70e5/raw/b0133afe634660791da12af93d251658e08e834f/gistfile1.txt).

For a more detailed view of the APIs, checkout [API.md](https://github.com/openagri-eu/irrigation-management/blob/main/API.md).

# Quick Start Guide

## Evapotranspiration (ETo) Workflow

 - **Register your location**: Use `POST /api/v1/location/` or `POST /api/v1/location/parcel-wkt/` to register single or multiple parcels. The system automatically fetches weather data daily at midnight.

 - **Retrieve ETo Calculations**: Call `POST /api/v1/eto/get-calculations/{location_id}` to get ETo calculations for your registered location across available dates. 


## Soil Moisture Analysis

 - **Upload Dataset**: Use `POST /api/v1/dataset/` to upload your soil moisture data.

 - **Manage Your Data**: Use `GET /api/v1/dataset/` to fetch all datasets. To fetch full dataset use `GET /api/v1/dataset/{dataset_id}`, and for removing it use `DELETE /api/v1/dataset/{dataset_id}`.

 - **Generate Analysis**: Call `GET /api/v1/dataset/{dataset_id}/analysis` to get detailed soil moisture analysis from your uploaded dataset. 


# Contribution
Please contact the maintainer of this repository.

# License
[European Union Public License 1.2](https://github.com/openagri-eu/irrigation-management/blob/main/LICENSE)
