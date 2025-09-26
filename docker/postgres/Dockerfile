FROM postgres:16

# Install extension build dependencies
RUN apt-get update && \
    apt-get install -y git build-essential flex bison postgresql-server-dev-16

# Clone and build Apache AGE
RUN git clone https://github.com/apache/age.git && \
    cd age && \
    make PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config && \
    make install

# Clone and build pgvector
RUN git clone https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /age /pgvector

# Create initialization script
COPY init.sql /docker-entrypoint-initdb.d/