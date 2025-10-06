# OpenAgri Dataset Uploader

This script automates the workflow of sending sensor data to the OpenAgri IRM service, retrieving analysis results, and (optionally) plotting soil moisture time-series.

## Features
- **CSV Parsing**: Reads a CSV file with soil moisture, rainfall, temperature, and humidity measurements. It permits robustness in the CSV column order and naming (eg soil_moisture_30 or "Soil Moisture 30" or "Soil Moisture 30 %"). Ift permits a depth column is missing by adding internally this column with default value 0 (this behaviour will be altered soon).
- **Payload Builder**: Normalizes soil moisture columns (supports flexible headers like `Soil Moisture 30cm (%)`) and fills missing depths with zeros.
- **API Calls**:
  - Posts the CSV data to `/api/v1/dataset/`.
  - Fetches analysis results from `/api/v1/dataset/{dataset_id}/analysis`.
- **Optional Plotting**: Plots soil moisture vs. date, adding vertical lines for irrigation events (red) and saturation days (blue).
- **No unnecessary dependencies**: Requires only `requests`. If `--plot` is used, then `matplotlib` must be installed.

## Usage

1. Install requirements:
   ```bash
   pip install requests pandas matplotlib
   ```

2. Run the script:

```bash
python soil_analysis.py \
  --csv ./OpenAgriIoTsensorsrecordings2024two.csv \
  --base-url https://irm.test.horizon-openagri.eu \
  --token YOUR_BEARER_TOKEN \
  --dataset-id test_dataset
```

3. To enable plotting:

```bash
python soil_analysis ... --plot
```

## Arguments

`--csv` : Path to the CSV file containing sensor data.
`--base-url` : Base URL of the service (e.g. http://localhost:8005).
`--token` : Bearer token for authentication.
`--dataset-id` : Identifier for the dataset (string).
`--plot` : If given, generate and save plots as PNG files.

## Outputs

Prints POST and GET responses (truncated) to the console.

If `--plot` is enabled, generates two PNG files:
- soil_moisture_irrigation_events.png
- soil_moisture_saturation_days.png

which represent the soil moisture data of the original dataset along with the events
where high dose irrigation and saturation days found.