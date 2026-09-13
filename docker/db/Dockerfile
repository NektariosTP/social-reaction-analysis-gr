FROM postgres:16
RUN apt-get update -o Acquire::Check-Valid-Until=false && \
    apt-get install -y postgresql-16-postgis-3 postgresql-16-pgvector && \
    rm -rf /var/lib/apt/lists/*
