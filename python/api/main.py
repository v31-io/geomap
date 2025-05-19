import copy
import uvicorn
from fastapi import FastAPI, Depends, Query
from fastapi_utils.tasks import repeat_every
from typing import Optional
from datetime import datetime

from api.services.glad import update_layers, get_meta, filter_dates
from api.services.keycloak import TokenVerifier
from api.services.cookie import SessionIDCookieMiddleware


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.state.layers_cache = {}

# SessionID Cookie 
app.add_middleware(SessionIDCookieMiddleware)

# Tasks
@app.on_event("startup")
@repeat_every(seconds=86400)
def task_update_tiles() -> None:
  app.state.layers_cache = update_layers()

# Routes
@app.head("/")
def head_root():
  return {"status": "OK"}

@app.get("/")
def get_root(_: dict = Depends(TokenVerifier(roles=['access']))):
  return get_meta()

@app.get("/layers")
def get_geojson(_: dict = Depends(TokenVerifier(roles=['access'])), 
                date: Optional[datetime] = Query(None)):
  layers = copy.deepcopy(app.state.layers_cache)
  layers = filter_dates(layers, date=date)
  return layers

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, reload=True)