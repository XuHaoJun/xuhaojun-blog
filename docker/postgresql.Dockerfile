FROM pgvector/pgvector:pg18

# Set environment variables
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=test
ENV POSTGRES_DB=blog_agent

# Expose PostgreSQL port
EXPOSE 5432

# Create initialization script directory
RUN mkdir -p /docker-entrypoint-initdb.d

# The pgvector extension is already included in the base image
# No additional setup needed

