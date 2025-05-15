# Geo Map

A satellite image processing application with a Vue frontend to see the Cloud Optimized GeoTIFF image layers. The satellite imagery is used from [Landsat Analysis Ready Data (GLAD ARD)](https://glad.umd.edu/ard/home). 

This is a docker compose application with different components -

- frontend - Made using [Vue](https://vuejs.org/) & [OpenLayers](https://vue3openlayers.netlify.app/).

- python - This has 2 sub components -
  - api - [FastAPI](https://fastapi.tiangolo.com/) is used to create an HTTP API and provide meta information to the frontend for the map layers.

  - worker - This is the image processing wrapper. It is run via GitHub Actions.

  The [GLAD](lib/glad.py) class contains the main processing and ingestion logic of data. [example.ipynb](example.ipynb) Jupyter Notebook can be used to understand the working of this class.

- nginx - Reverse proxy to have a single server for the frontend and backend components. Config is in [nginx.conf](nginx.conf).

- External services - Data is stored in S3 and [Postgres](https://www.postgresql.org/) is used for tracking internal run statistics. [Keycloak](https://www.keycloak.org/) is used as an IDP.


## Treecover Analysis

The Jupyter notebook [treecover-analysis.ipynb](treecover-analysis.ipynb) shows how the Treecover layer is computed using NDVI.
- NDVI is computed as (NIR-Red)/(NIR+Red)
- Missing values are imputed with forward fill and back fill along the time axis and outliers are clipped to known NDVI values = (-1, 1).
- NDVI values are smoothened to account for seasonal/temporal variance along the time axis (3 periods).
- If the differnce between NDVI for a single time point is greater than a known value (0.25) (max NDVI along time axis - current NDVI), then this usually indicates that trees have been cut down. This check is also clipped to a lower bound of known NDVI value for tree (0.7).
- If a pixel is marked as tree loss then it will be marked as tree loss for all future time points unless re-growth (tree) is detected for 3 periods.

The values for NDVI difference for tree and cut tree (0.25) & and the NDVI lower bound for trees (0.7) is a configurable value per Tile ID as this may vary based on the geographical location of the Tile.


## Screenshots

The treecover (green = trees, red = no tress) can be seen for different dates -
![](docs/2025%20treecover.png)
![](docs/2000%20treecover.png)

The TCI layer can also be seen for different dates - 
![](docs/2025%20tci.png)
![](docs/2000%20tci.png)

The GLAD ARD Grid can also be overlayed to see the Tile IDs on click - 
![](docs/glad%20tile%20grid.png)


## Local Development

A `.devcontainer` configuration is enabled which provides a docker environment. This also initializes a venv `base` for Python development.
Maintain the credentials in the `sample.env` file (rename it to `.env`). And then run - 
```
docker compose up --build
``` 
Watch and local development parameters are enabled in the `docker-compose.override.yml` file. The applciation is served on `http://localhost:80`.


## Attributions

- Landsat Analysis Ready Data (GLAD ARD) -

  > Potapov, P., Hansen, M.C., Kommareddy, I., Kommareddy, A., Turubanova, S., Pickens, A., Adusei, B., Tyukavina A., and Ying, Q., 2020.
  > 
  > Landsat analysis ready data for global land cover and land cover change mapping.
  > 
  > Remote Sens. 2020, 12, 426; doi:10.3390/rs12030426.
