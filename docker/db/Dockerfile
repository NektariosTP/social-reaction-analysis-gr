FROM postgis/postgis:16-3.4
RUN apt-get update -o Acquire::Check-Valid-Until=false && \
    apt-get install -y postgresql-16-pgvector && \
    rm -rf /var/lib/apt/lists/*
