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
