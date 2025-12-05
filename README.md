# Irrigation service

:eu: *"This service was created in the context of OpenAgri project (https://horizon-openagri.eu/). OpenAgri has received funding from the EU’s Horizon Europe research and innovation programme under Grant Agreement no. 101134083."*
# Description

The OpenAgri Irrigation service provides the calculation of referent evapotranspiration (ETo) as well as the analysis of \
the soil moisture of parcels/plots of land. \
These functionalities can be used via the REST APIs, which provide these them in a linked data format (using JSON-LD). \
This service conforms to the OpenAgri Common Semantic Model (OCSM).

## Roadmap

High-level next steps for the Weather Service:

- [ ] Integrate with FarmCalendar 
- [ ] Database models for time-series soil moisture analysis engine
- [ ] Predictive models  


# Prerequisites

<ul>
    <li>git</li>
    <li>docker</li>
    <li>docker-compose</li>
</ul>

Docker version used during development: 27.0.3

Before you start, make sure Docker and Docker Compose are installed on your system.
Later versions of Docker also include now Docker Compose, but it is used as `docker compose` instead of `docker-compose`.

## Service Setup

### Setting up Configurations (.env file)

If you wish to start up this Irrigation Management Service from this repository, you'll need to first copy the `.env.example` file into a new file called `.env`, which will be the source of all configurations for this service, and its database.

In this new `.env` file you should change the configurations of the service to meet your deployment scenario. We strongly suggest changing configurations for the default usernames and passwords of the services used.

The details for the configuration variables that are not self-explanatory are:
* **RAIN_THRESHOLD_MM**: Variable used to identify how many events have precipitations higher that expected. It differs from country to country (field to field).
* **FIELD_CAPACITY_WINDOW_HOURS**: Period to detect amplitudes.
* **STRESS_THRESHOLD_FRACTION**: Fraction to detect stress events.
* **LOW_DOSE_THRESHOLD_MM**: Similar to `RAIN_THRESHOLD_MM`.
* **HIGH_DOSE_THRESHOLD_MM**: Similar to `RAIN_THRESHOLD_MM`.

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


A full list of APIs can be viewed [here](https://editor-next.swagger.io/?url=https://gist.githubusercontent.com/prske/9654d16f45f8ec030d40807586597c0c/raw/3162cb021916f8e5935eea9838204c908f422f64/gistfile1.txt).


For a more detailed view of the APIs, checkout [API.md](API.md).

# Quick Start Guide

## Evapotranspiration (ETo) Workflow

 - **Register your location**: Use `POST /api/v1/location/` or `POST /api/v1/location/parcel-wkt/` to register single or multiple parcels. The system automatically fetches weather data daily at midnight.

 - **Retrieve ETo Calculations**: Call `POST /api/v1/eto/get-calculations/{location_id}` to get ETo calculations for your registered location across available dates. 

[Here](scripts/eto.md) you can find more documentation about evapotraspiration analysis as well as working exampls under `scripts/` directory.

## Soil Moisture Analysis

 - **Upload Dataset**: Use `POST /api/v1/dataset/` to upload your soil moisture data.

 - **Manage Your Data**: Use `GET /api/v1/dataset/` to fetch all datasets. To fetch full dataset use `GET /api/v1/dataset/{dataset_id}`, and for removing it use `DELETE /api/v1/dataset/{dataset_id}`.

 - **Generate Analysis**: Call `GET /api/v1/dataset/{dataset_id}/analysis` to get detailed soil moisture analysis from your uploaded dataset.

[Here](scripts/soil_analysis.md) you can find more documentation about soil analysis as well as working exampls under `scripts/` directory.

# Contribution

We welcome first-time contributions!

See our [Contributing Guide](CONTRIBUTE.md)

You can also open an issue to discuss ideas.

Irrigation Management Service is part of OpenAgri project. Your contribution helps farmers and researchers.

<a href="https://github.com/agstack/OpenAgri-IrrigationManagement/graphs/contributors">
    <img src="https://avatars.githubusercontent.com/u/19305816?v=4&s=80" width="60px;" alt="@prske's Avatar"/><img src="https://avatars.githubusercontent.com/u/173052838?v=4&s=80" width="60px;" alt="@vlf-stefan-drobic's Avatar"/><img src="https://avatars.githubusercontent.com/u/1727181?v=4&s=80" width="60px;" alt="@fedjo's Avatar"/></a>

# License
This project code is licensed under the EUPL 1.2 license, see the [LICENSE](https://github.com/agstack/OpenAgri-IrrigationManagement/blob/main/LICENSE) file for more details.
Please note that each service may have different licenses, which can be found their specific source code repository.
