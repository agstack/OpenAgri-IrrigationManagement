# ETo (Reference Evapotranspiration)

This page documents how to:
1) Create a parcel using a WKT polygon,
2) Discover its corresponding location, and
3) Retrieve ETo calculations for a date range — then plot the results.

> **Auth:** Obtain a JWT and include it in all requests as:
>
> ```
> Authorization: Bearer JWT_TOKEN
> ```

## Base URL

Assume the Irrigation service is available at:

```
http://localhost:8004
```

All endpoints below are relative to this base.

---

## 1) Create a Parcel from WKT

**Endpoint:**  
`POST /api/v1/location/parcel-wkt/`

**Body:**
```json
{
  "coordinates": "POLYGON((...your WKT polygon...))"
}
```

**Example `curl`:**
```bash
curl -X POST "http://localhost:8004/api/v1/location/parcel-wkt/"   -H "Authorization: Bearer $JWT_TOKEN"   -H "Content-Type: application/json"   -d '{"coordinates":"POLYGON((23.90788293506056 37.98810424577469,23.907381957300185 37.988277198315174,23.90688901661618 37.988336255186866,23.906776497547003 37.98810002741493,23.907880256035103 37.987969258142684,23.90788293506056 37.98810424577469))"}'
```

---

## 2) List Locations

**Endpoint:**  
`GET /api/v1/location/`

**Example `curl`:**
```bash
curl -X GET "http://localhost:8004/api/v1/location/"   -H "Authorization: Bearer $JWT_TOKEN"   -H "Accept: application/json"
```

---

## 3) Get ETo Calculations

**Endpoint:**  
```
GET /api/v1/eto/get-calculations/{location_id}/from/{from_date}/to/{to_date}/
```

- `location_id` → `LOCATION_ID` from the previous step  
- `from_date`, `to_date` → `YYYY-MM-DD`  

**Example `curl`:**
```bash
curl -X GET   "http://localhost:8004/api/v1/eto/get-calculations/${LOCATION_ID}/from/2025-09-24/to/2025-10-08/"   -H "Authorization: Bearer $JWT_TOKEN"   -H "Accept: application/json"
```

**Response shape:**
```json
{
  "calculations": [
    {"date":"2025-09-24","value":7.03},
    {"date":"2025-09-25","value":6.43},
    ...
  ]
}
```

---

## 4) Plotting the Result

An [example script](calculate_eto.py) that implements the above flow and plots the results can be found here: `eto_pipeline.py`.

### What the graph shows
- **X-axis:** Dates (formatted **MM-DD**).
- **Y-axis:** Daily ETo value (mm/day).
- **Points:** Each `(date, value)` pair from the API.  
  The line connects points to reveal trends in evaporative demand across the selected period.
