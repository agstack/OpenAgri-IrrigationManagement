# Documentation

# ETO

The service provides ETo calculations for different parcels/locations. \
In order to do this, the service requires one or more locations to be added. \
You can add locations via the following API:

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

<h3>GET</h3>

```
/api/v1/eto/get-calculations/{location_id}/from/{from_date}/to/{to_date}/?formatting=JSON
```

Path parameters:
1. location_id: the location id for which you want to get the calculated ETo values.
2. from_date: start date (inclusive)
3. to_date: end date (inclusive)

Query parameters:
1. formatting: accepts either JSON or JSON-LD. Defines the format of the data that the API will respond with.

Response example:

```json
{
  "@context": [
    "https://w3id.org/ocsm/main-context.jsonld"
  ],
  "@graph": [
    {
      "@id": "urn:openagri:evaporation:calculation:652337ea-0c08-467d-a9f4-2a0699e97b23",
      "@type": "Observation",
      "description": "Measurement or calculation of the evaporation of the soil on a parcel on a specific date",
      "resultTime": "2025-02-10",
      "observedProperty": {
        "@id": "urn:openagri:evaporation:op:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "ObservableProperty",
          "Evaporation"
        ]
      },
      "hasFeatureOfInterest": {
        "@id": "urn:openagri:soil:foi:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "FeatureOfInterest",
          "Soil"
        ]
      },
      "hasSimpleResult": "2.43"
    },
    {
      "@id": "urn:openagri:evaporation:calculation:652337ea-0c08-467d-a9f4-2a0699e97b23",
      "@type": "Observation",
      "description": "Measurement or calculation of the evaporation of the soil on a parcel on a specific date",
      "resultTime": "2025-02-10",
      "observedProperty": {
        "@id": "urn:openagri:evaporation:op:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "ObservableProperty",
          "Evaporation"
        ]
      },
      "hasFeatureOfInterest": {
        "@id": "urn:openagri:soil:foi:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "FeatureOfInterest",
          "Soil"
        ]
      },
      "hasSimpleResult": "2.43"
    },
    {
      "@id": "urn:openagri:evaporation:calculation:652337ea-0c08-467d-a9f4-2a0699e97b23",
      "@type": "Observation",
      "description": "Measurement or calculation of the evaporation of the soil on a parcel on a specific date",
      "resultTime": "2025-02-10",
      "observedProperty": {
        "@id": "urn:openagri:evaporation:op:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "ObservableProperty",
          "Evaporation"
        ]
      },
      "hasFeatureOfInterest": {
        "@id": "urn:openagri:soil:foi:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "FeatureOfInterest",
          "Soil"
        ]
      },
      "hasSimpleResult": "2.43"
    },
    {
      "@id": "urn:openagri:evaporation:calculation:652337ea-0c08-467d-a9f4-2a0699e97b23",
      "@type": "Observation",
      "description": "Measurement or calculation of the evaporation of the soil on a parcel on a specific date",
      "resultTime": "2025-02-10",
      "observedProperty": {
        "@id": "urn:openagri:evaporation:op:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "ObservableProperty",
          "Evaporation"
        ]
      },
      "hasFeatureOfInterest": {
        "@id": "urn:openagri:soil:foi:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "FeatureOfInterest",
          "Soil"
        ]
      },
      "hasSimpleResult": "2.43"
    },
    {
      "@id": "urn:openagri:evaporation:calculation:652337ea-0c08-467d-a9f4-2a0699e97b23",
      "@type": "Observation",
      "description": "Measurement or calculation of the evaporation of the soil on a parcel on a specific date",
      "resultTime": "2025-02-10",
      "observedProperty": {
        "@id": "urn:openagri:evaporation:op:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "ObservableProperty",
          "Evaporation"
        ]
      },
      "hasFeatureOfInterest": {
        "@id": "urn:openagri:soil:foi:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "FeatureOfInterest",
          "Soil"
        ]
      },
      "hasSimpleResult": "2.43"
    },
    {
      "@id": "urn:openagri:evaporation:calculation:652337ea-0c08-467d-a9f4-2a0699e97b23",
      "@type": "Observation",
      "description": "Measurement or calculation of the evaporation of the soil on a parcel on a specific date",
      "resultTime": "2025-02-10",
      "observedProperty": {
        "@id": "urn:openagri:evaporation:op:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "ObservableProperty",
          "Evaporation"
        ]
      },
      "hasFeatureOfInterest": {
        "@id": "urn:openagri:soil:foi:652337ea-0c08-467d-a9f4-2a0699e97b23",
        "@type": [
          "FeatureOfInterest",
          "Soil"
        ]
      },
      "hasSimpleResult": "2.43"
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

<h3>POST</h3>

```
/api/v1/dataset/weights/
```

Input JSON:

```json
{
    "10": 0.125,
    "20": 0.4,
    "30": 0.15,
    "40": 0.05,
    "50": 0.025,
    "60": 0.025
}
```

```json
{
  "message": "Successfully uploaded weights per depths"
}
```

This allows the user to insert weights per depths in order to calculate field capacity and soil moisture analysis.
Some depths have more impact on this calculation. 
This also allows some depths in the datasets to be left out, i.e., weight for that depth(s) is zero (0).

<h3>GET/DELETE</h3>

```
/api/v1/dataset/{dataset_id}/
```

Example responses for GET and DELETE respectively:

```json
[
  {
    "dataset_id": "dataset_name",
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
   "dataset_id": "dataset_name",
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
  "dataset_id": "dataset_name",
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
  "dataset_id": "dataset_name",
  "time_period": [
    "2024-10-17T13:24:35.198Z", "2024-10-19T13:24:35.198Z"
  ],
  "irrigation_events_detected": 12,
  "precipitation_events": 10,
  "high_dose_irrigation_events": 3,
  "high_dose_irrigation_events_dates": [
    "2024-10-17T13:24:35.198Z", "2024-10-17T19:33:44.245Z", "2024-10-18T11:11:45.198Z"
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
    "2024-10-18T10:10:10.198Z"
  ],
  "no_of_stress_days": 1,
  "stress_dates": [
    "2024-10-18T13:24:35.198Z"
  ]
}
```