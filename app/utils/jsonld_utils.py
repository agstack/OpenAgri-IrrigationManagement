from typing import List

import utils
import uuid
from schemas import Dataset, DatasetAnalysis, EToResponse

from datetime import datetime

def jsonld_get_dataset(dataset: list[Dataset]):
    context = utils.context
    graph = []

    uuid4_temp = uuid.uuid4()

    for d in dataset:

        graph_element = {
            "@id": "urn:openagri:soilMoistureMonitoring:{}".format(uuid4_temp),
            "@type": ["ObservationCollection"],
            "description": "Monitoring of soil moisture levels at various depths in the soil of a parcel",
            "resultTime": "{}".format(d.date),
            "observedProperty": {
                "@id": "urn:openagri:Moisture:op:{}".format(uuid4_temp),
                "@type": ["ObservableProperty", "Moisture"],
                "name": "The moisture level in some material"
            },
            "hasFeatureOfInterest": {
                "@id": "urn:openagri:soil:foi:{}".format(uuid4_temp),
                "@type": ["FeatureOfInterest", "Soil"]
            },
            "precipitation": {
                "@id": "urn:openagri:precipitation:{}".format(d.rain),
                "@type": "https://smartdatamodels.org/dataModel.Weather/precipitation",
                "description": "the measured precipitation during monitoring of the soil moisture",
                "value": d.rain
            },
            "temperature": {
                "@id": "urn:openagri:temperature:{}".format(d.temperature),
                "@type": "https://smartdatamodels.org/dataModel.Weather/temperature",
                "description": "the measured temperature during monitoring of the soil moisture",
                "value": d.temperature
            },
            "relativeHumidity": {
                "@id": "urn:openagri:relativeHumidity:{}".format(d.humidity),
                "@type": "https://smartdatamodels.org/dataModel.Weather/relativeHumidity",
                "description": "the measured relative humidity during monitoring of the soil moisture",
                "value": d.humidity
            },
            "hasMember": [
                {
                    "@id": "urn:openagri:soilMoistureVwc:obs1:{}".format(uuid4_temp),
                    "@type": ["Observation"],
                    "hasSimpleResult": "{}".format(d.soil_moisture_10),
                    "atDepth": {
                        "@id": "urn:openagri:depth:10",
                        "@type": "[Measure]",
                        "hasNumericValue": "10",
                        "hasUnit": "om:centimetre"
                    }
                },
                {
                    "@id": "urn:openagri:soilMoistureVwc:obs2:{}".format(uuid4_temp),
                    "@type": ["Observation"],
                    "hasSimpleResult": "{}".format(d.soil_moisture_20),
                    "atDepth": {
                        "@id": "urn:openagri:depth:20",
                        "@type": "[Measure]",
                        "hasNumericValue": "20",
                        "hasUnit": "om:centimetre"
                    }
                },
                {
                    "@id": "urn:openagri:soilMoistureVwc:obs3:{}".format(uuid4_temp),
                    "@type": ["Observation"],
                    "hasSimpleResult": "{}".format(d.soil_moisture_30),
                    "atDepth": {
                        "@id": "urn:openagri:depth:30",
                        "@type": "[Measure]",
                        "hasNumericValue": "30",
                        "hasUnit": "om:centimetre"
                    }
                },
                {
                    "@id": "urn:openagri:soilMoistureVwc:obs4:{}".format(uuid4_temp),
                    "@type": ["Observation"],
                    "hasSimpleResult": "{}".format(d.soil_moisture_40),
                    "atDepth": {
                        "@id": "urn:openagri:depth:40",
                        "@type": "[Measure]",
                        "hasNumericValue": "40",
                        "hasUnit": "om:centimetre"
                    }
                },
                {
                    "@id": "urn:openagri:soilMoistureVwc:obs5:{}".format(uuid4_temp),
                    "@type": ["Observation"],
                    "hasSimpleResult": "{}".format(d.soil_moisture_50),
                    "atDepth": {
                        "@id": "urn:openagri:depth:50",
                        "@type": "[Measure]",
                        "hasNumericValue": "50",
                        "hasUnit": "om:centimetre"
                    }
                },
                {
                    "@id": "urn:openagri:soilMoistureVwc:obs6:{}".format(uuid4_temp),
                    "@type": ["Observation"],
                    "hasSimpleResult": "{}".format(d.soil_moisture_60),
                    "atDepth": {
                        "@id": "urn:openagri:depth:60",
                        "@type": "[Measure]",
                        "hasNumericValue": "60",
                        "hasUnit": "om:centimetre"
                    }
                }
            ]
        }

        graph.append(graph_element)


    doc = {
        "@context": context,
        "@graph": graph
    }
    return doc


def jsonld_analyse_soil_moisture(analysis: DatasetAnalysis):
    context = utils.context
    analysis_uuid = uuid.uuid4()

    def format_xsd_date(d: datetime) -> str:
        return d.strftime("%Y-%m-%dT%H:%M:%SZ")

    def format_dates(date_list: List[datetime]) -> List[str]:
        return [format_xsd_date(d) for d in date_list]


    start_time = format_xsd_date(analysis.time_period[0]) if analysis.time_period else ""
    end_time = format_xsd_date(analysis.time_period[-1]) if analysis.time_period else ""

    has_member = [
        {
            "@id": f"https://example.org/observation/field-capacity-{analysis_uuid}",
            "@type": "Observation",
            "observedProperty": "https://w3id.org/ocsm/property/field_capacity",
            "hasSimpleResult": analysis.field_capacity,
        },
        {
            "@id": f"https://example.org/observation/wilting-point-{analysis_uuid}",
            "@type": "Observation",
            "observedProperty": "https://w3id.org/ocsm/property/wilting_point",
            "hasSimpleResult": analysis.wilting_point,
        },
        {
            "@id": f"https://example.org/observation/stress-level-{analysis_uuid}",
            "@type": "Observation",
            "observedProperty": "https://w3id.org/ocsm/property/stress_level",
            "hasSimpleResult": analysis.stress_level,
        }
    ]

    doc = {
        "@context": context,
        "@id": f"https://example.org/analysis/{analysis.dataset_id}",
        "@type": "DatasetAnalysis",
        "analysisOf": {
            "@id": f"https://example.org/dataset/{analysis.dataset_id}",
            "@type": "dcat:Dataset",
            "identifier": f"{analysis.dataset_id}"
        },
        "period": {
            "@type": "Interval",
            "hasBeginning": {
                "@type": "Instant",
                "inXSDDateTimeStamp": start_time
            },
            "hasEnd": {
                "@type": "Instant",
                "inXSDDateTimeStamp": end_time
            }
        },

        "irrigationEventsDetected": analysis.irrigation_events_detected,
        "irrigationEventsDates": format_dates(analysis.irrigation_events_dates),

        "precipitationEventsCount": analysis.precipitation_events,
        "precipitationEventsDates": format_dates(analysis.precipitation_events_dates),

        "highDoseIrrigationEventsCount": analysis.high_dose_irrigation_events,
        "highDoseIrrigationEventsDates": format_dates(analysis.high_dose_irrigation_events_dates),

        "hasMember": has_member,

        "numberOfSaturationDays": analysis.number_of_saturation_days,
        "saturationDates": format_dates(analysis.saturation_dates),

        "numberOfStressDays": analysis.no_of_stress_days,
        "stressDates": format_dates(analysis.stress_dates)
    }

    return doc


def jsonld_eto_response(eto: EToResponse):
    context = utils.context
    graph = []

    uuid4_temp = uuid.uuid4()

    calculations = eto.calculations

    for c in calculations:

        graph_element =  {
            "@id": "urn:openagri:evaporation:calculation:{}".format(uuid4_temp),
            "@type": "Observation",
            "description": "Measurement or calculation of the evaporation of the soil on a parcel on a specific date",
            "resultTime": "{}".format(c.date),
            "observedProperty": {
                "@id": "urn:openagri:evaporation:op:{}".format(uuid4_temp),
                "@type": ["ObservableProperty", "Evaporation"]
            },
            "hasFeatureOfInterest": {
                "@id": "urn:openagri:soil:foi:{}".format(uuid4_temp),
                "@type": ["FeatureOfInterest", "Soil"]
            },
            "hasSimpleResult": "{}".format(c.value)
        }

        graph.append(graph_element)

    doc = {
        "@context": context,
        "@graph": graph
    }

    return doc
