FROM python:3.11.16-slim-bookworm

LABEL org.opencontainers.image.title="Chico Ciencia experiment runner"
LABEL org.opencontainers.image.description="Offline, non-root scientific Python runner"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg

COPY docker/runner-requirements.txt /tmp/runner-requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check \
        -r /tmp/runner-requirements.txt \
    && rm /tmp/runner-requirements.txt

WORKDIR /work
USER 65532:65532

CMD ["python"]
