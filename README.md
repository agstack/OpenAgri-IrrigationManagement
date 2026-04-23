# Irrigation service

:eu: *"This service was created in the context of OpenAgri project (https://horizon-openagri.eu/). OpenAgri has received funding from the EU's Horizon Europe research and innovation programme under Grant Agreement no. 101134083."*

# Description

The OpenAgri Irrigation service provides the calculation of referent evapotranspiration (ETo) as well as the analysis of the soil moisture of parcels/plots of land. These functionalities can be used via the REST APIs, which provide these them in a linked data format (using JSON-LD). This service conforms to the OpenAgri Common Semantic Model (OCSM).

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

#### Rain & Irrigation Settings

| Variable | Default | Description |
|---|---|---|
| `RAIN_THRESHOLD_MM` | `5` | Minimum total rain (mm) for a single event to qualify for field capacity calculation. Calibrated against tipping-bucket sensor data where maximum decoded event totals are 8–17 mm. |
| `LOW_DOSE_THRESHOLD_MM` | `5` | Daily rain totals below this value are classified as low-dose irrigation events. |
| `HIGH_DOSE_THRESHOLD_MM` | `5` | Daily rain totals at or above this value are classified as high-dose irrigation events. Combined with SM-response detection (see below) to catch gauge-missed events. |
| `RAIN_ZERO_TOLERANCE` | `0.1` | Rain readings at or below this value (mm) are treated as zero / no rain. |
| `RAIN_GAP_TOLERANCE_HOURS` | `3` | Maximum gap (hours) between readings within the same rain event before it is split into two separate events. |

#### Field Capacity Settings

| Variable | Default | Description |
|---|---|---|
| `FIELD_CAPACITY_WINDOW_HOURS` | `24` | Hours after the end of a qualifying rain event in which the peak soil moisture reading is recorded as a field capacity candidate. |

#### Stress & Wilting Point Settings

| Variable | Default | Description |
|---|---|---|
| `STRESS_THRESHOLD_FRACTION` | `0.5` | Fraction of field capacity below which soil moisture is flagged as a stress condition. Auto-tuned per dataset using the 5th percentile of historical moisture. |

#### Soil Moisture Response Detection Settings

| Variable | Default | Description |
|---|---|---|
| `SM_IRRIGATION_JUMP_PCT` | `3.0` | Minimum day-over-day rise in weighted soil moisture (percentage points) required to flag a gauge-missed irrigation event via SM-response detection. Calibrated across 6 sensor datasets: confirmed missed events show rises of 3.2–10.3 %, while noise stays below 2.5 %. |
| `SM_GAUGE_BLACKOUT_DAYS` | `2` | Number of days following a rain gauge high-dose event during which SM-response detection is suppressed. Prevents double-counting the next-day sensor response to rainfall as a separate irrigation event. |

#### Sensor Weights

| Variable | Description |
|---|---|
| `GLOBAL_WEIGHTS` | Dictionary mapping soil depth (cm) to its contribution weight in the weighted moisture average, e.g. `{10: 0.10, 20: 0.15, 30: 0.20, 40: 0.25, 50: 0.20, 60: 0.10}`. Weights are automatically re-normalized to whichever depths actually have sensor data, so partial sensor coverage (e.g. only 10 cm and 30 cm installed) is handled correctly. |

# Installation

There are two ways to install this service, via docker (preferred) or directly from source.

<h3> Deploying from source </h3>

When deploying from source, use python 3:11. Also, you should use a [venv](https://peps.python.org/pep-0405/) when doing this.

A list of libraries that are required for this service is present in the "requirements.txt" file. This service uses FastAPI as a web framework to serve APIs, alembic for database migrations and sqlalchemy for database ORM mapping.

<h3> Deploying via docker </h3>

After installing <code>docker compose</code> you can run the following commands to run the application:

```
docker compose build
docker compose up
```

# A List of APIs

A full list of APIs can be viewed [here](https://editor-next.swagger.io/?url=https://gist.githubusercontent.com/vlf-stefan-drobic/c740120c05eab877212fceb945bb3b08/raw/0b99438e4cb46ec55e91c90d7610d73bb98e6b2c/gistfile1.txt).

For a more detailed view of the APIs, checkout [API.md](API.md).

# Quick Start Guide

## Evapotranspiration (ETo) Workflow

- **Register your location**: Use `POST /api/v1/location/` or `POST /api/v1/location/parcel-wkt/` to register single or multiple parcels. The system automatically fetches weather data daily at midnight.

- **Retrieve ETo Calculations**: Call `POST /api/v1/eto/get-calculations/{location_id}` to get ETo calculations for your registered location across available dates.

[Here](scripts/eto.md) you can find more documentation about evapotranspiration analysis as well as working examples under `scripts/` directory.

## Soil Moisture Analysis

- **Upload Dataset**: Use `POST /api/v1/dataset/` to upload your soil moisture data.

- **Manage Your Data**: Use `GET /api/v1/dataset/` to fetch all datasets. To fetch full dataset use `GET /api/v1/dataset/{dataset_id}`, and for removing it use `DELETE /api/v1/dataset/{dataset_id}`.

- **Generate Analysis**: Call `GET /api/v1/dataset/{dataset_id}/analysis` to get detailed soil moisture analysis from your uploaded dataset.

[Here](scripts/soil_analysis.md) you can find more documentation about soil analysis as well as working examples under `scripts/` directory.

### Supported Dataset Formats

The soil moisture analysis engine accepts datasets with the following column naming conventions — all are handled automatically:

| Format | Example column names |
|---|---|
| Snake case with depth | `soil_moisture_10`, `soil_moisture_30` |
| Numbered sensor index | `soil_moisture1_percent`, `soil_moisture2_percent` |
| Titled with units | `Soil Moisture 10cm (%)` |
| CamelCase | `soilMoisture10` |

Rain columns are accepted as `rain` or `Rain`. Missing depth columns (all-zero or all-null) are automatically excluded from all calculations.

### How the Analysis Works

#### Rain Sensor Decoding

This service is designed to work with tipping-bucket rain sensors that broadcast their cumulative counter value at each polling interval (typically every 30 minutes). The analysis engine automatically detects this pattern and decodes the raw data into per-interval increments before any calculation. Without this step, daily rain totals would be overcounted by 2–50×.

If a dataset uses true per-interval rain readings instead (each value is a fresh measurement), the engine detects this automatically and skips decoding.

#### Field Capacity

Field capacity is calculated by finding qualifying rain events (total ≥ `RAIN_THRESHOLD_MM`) and recording the peak soil moisture reached within `FIELD_CAPACITY_WINDOW_HOURS` after each event. The median of all candidate peaks per depth is used (robust to sensor spike artifacts), then combined into a single value using depth-weighted averaging.

#### Wilting Point & Stress Level

Both are derived automatically from the field capacity and the historical distribution of weighted soil moisture in the dataset. The wilting point is anchored at the 1st percentile of observed moisture; the stress threshold is placed above the wilting point using the 5th percentile, ensuring there is always a meaningful gap between the two.

#### Irrigation Event Detection

High-dose irrigation events are detected using two complementary signals:

1. **Rain gauge**: days where decoded daily rain totals ≥ `HIGH_DOSE_THRESHOLD_MM`.
2. **Soil moisture response**: days where the weighted daily SM rises ≥ `SM_IRRIGATION_JUMP_PCT` percentage points and no gauge event occurred within the preceding `SM_GAUGE_BLACKOUT_DAYS` days. This captures drip lines, subsurface emitters, and pivot irrigators that wet the soil sensors without triggering the rain gauge.

The two sources are merged and deduplicated by date.

#### Partial Sensor Coverage

Datasets with fewer than 6 depth sensors are handled transparently. The `GLOBAL_WEIGHTS` are re-normalized to the depths that have real data, so a dataset with only 10 cm and 30 cm sensors produces the same quality of output as a fully-equipped one — the effective weight split simply reflects the available sensors.

#### Missing Depth Sentinel Values

When a sensor depth is not installed, some data pipelines serialize the missing value as `0` rather than `null`. Because 0 % soil moisture is physically impossible for real soil, the engine treats any soil moisture reading of exactly `0.0` as missing data (`NaN`) before performing any calculation.

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