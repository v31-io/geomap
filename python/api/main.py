import uvicorn
from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every

from api.tasks.update_tiles import update_tiles
from api.services.keycloak import TokenVerifier


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.state.tile_cache = {}

# Tasks
@app.on_event("startup")
@repeat_every(seconds=86400)
def task_update_tiles() -> None:
    app.state.tile_cache = update_tiles()

# Routes
@app.head("/")
def head_root():
  return {"status": "OK"}

@app.get("/")
def get_root(_: dict = Depends(TokenVerifier(roles=['access']))):
  return app.state.tile_cache

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, reload=True)