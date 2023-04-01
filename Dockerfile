FROM python:3.9.16-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt

ENV DEPS="build-essential cmake"

RUN apt-get update \
  && apt-get install -y ${DEPS} --no-install-recommends \
  && pip install -r requirements.txt \
  && rm -rf /var/lib/apt/lists/* \
  && rm -rf /usr/share/doc && rm -rf /usr/share/man \
  && apt-get purge -y --auto-remove ${DEPS} \
  && apt-get clean

COPY . .

RUN python setup.py install

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0", "--log-level=DEBUG", "memimto.__main__:app"]