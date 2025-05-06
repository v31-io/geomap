FROM python:3.11 AS base

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

EXPOSE 4000

################################################################################
# Local development
################################################################################
FROM base AS development

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "4000", "--workers", "1"]
################################################################################


################################################################################
# Production build
################################################################################
FROM base AS production

CMD ["uvicorn", "api.main:app", "-k", "uvicorn.workers.UvicornWorker", "--host", "0.0.0.0", "--port", "4000", "--workers", "1"]
################################################################################