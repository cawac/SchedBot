#!/bin/bash
set -e

echo "=========================================="
echo "SchedBot Deployment Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Build and start containers
echo -e "${YELLOW}Step 1: Building and starting Docker containers...${NC}"
docker-compose build
docker-compose up -d

echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep 5

# Step 2: Check OLTP database
echo -e "${YELLOW}Step 2: Checking OLTP database...${NC}"
OLTP_TABLES=$(docker-compose exec -T db psql -U user -d db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "OLTP tables count: $OLTP_TABLES"

if [ "$OLTP_TABLES" -lt 8 ]; then
    echo -e "${RED}✗ Not enough OLTP tables. Expected at least 8.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ OLTP database OK${NC}"
echo ""

# Step 3: Apply manual migration if needed
echo -e "${YELLOW}Step 3: Checking if migration needed...${NC}"
HAS_AUDITORIUM_ID=$(docker-compose exec -T db psql -U user -d db -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'lessons' AND column_name = 'auditorium_id';")

if [ "$HAS_AUDITORIUM_ID" -eq 0 ]; then
    echo -e "${YELLOW}Applying migration manually...${NC}"
    docker-compose exec -T db psql -U user -d db << 'EOF'
ALTER TABLE lessons ADD COLUMN auditorium_id INTEGER REFERENCES auditoriums(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
UPDATE lessons l SET auditorium_id = a.id FROM auditoriums a WHERE l.auditorium = a.number OR l.auditorium = a.name;
ALTER TABLE lessons DROP COLUMN IF EXISTS auditorium;
EOF
    echo -e "${GREEN}✓ Migration applied${NC}"
else
    echo -e "${GREEN}✓ Migration already applied${NC}"
fi
echo ""

# Step 4: Create OLAP database
echo -e "${YELLOW}Step 4: Creating OLAP database...${NC}"
docker-compose exec -T db psql -U user -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname = 'db_olap';" | grep -q 1 || \
docker-compose exec -T db psql -U user -d postgres -c "CREATE DATABASE db_olap;"
echo -e "${GREEN}✓ OLAP database created${NC}"
echo ""

# Step 5: Load OLAP schema
echo -e "${YELLOW}Step 5: Loading OLAP schema...${NC}"
docker-compose exec -T db psql -U user -d db_olap < src/etl/olap_schema.sql
echo -e "${GREEN}✓ OLAP schema loaded${NC}"
echo ""

# Step 6: Setup Foreign Data Wrapper
echo -e "${YELLOW}Step 6: Setting up Foreign Data Wrapper...${NC}"

# Create extension
docker-compose exec -T db psql -U user -d db_olap << 'EOF'
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
EOF

# Create server
docker-compose exec -T db psql -U user -d db_olap << 'EOF'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_foreign_server WHERE srvname = 'oltp_server') THEN
        CREATE SERVER oltp_server
        FOREIGN DATA WRAPPER postgres_fdw
        OPTIONS (host 'db', dbname 'db', port '5432');
    END IF;
END $$;
EOF

# Create user mapping
docker-compose exec -T db psql -U user -d db_olap << 'EOF'
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_user_mappings
        WHERE srvname = 'oltp_server' AND usename = 'user'
    ) THEN
        CREATE USER MAPPING FOR user
        SERVER oltp_server
        OPTIONS (user 'user', password 'secret_pass');
    END IF;
END $$;
EOF

# Create schema and enum
docker-compose exec -T db psql -U user -d db_olap << 'EOF'
CREATE SCHEMA IF NOT EXISTS schedbot;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lesson_type') THEN
        CREATE TYPE lesson_type AS ENUM ('UNKNOWN', 'LECTURE', 'PRACTICE', 'SEMINAR', 'LAB', 'EXAM');
    END IF;
END $$;
EOF

# Import foreign tables
docker-compose exec -T db psql -U user -d db_olap << 'EOF'
DROP SCHEMA IF EXISTS schedbot CASCADE;
CREATE SCHEMA schedbot;
IMPORT FOREIGN SCHEMA public FROM SERVER oltp_server INTO schedbot;
EOF

echo -e "${GREEN}✓ Foreign Data Wrapper configured${NC}"
echo ""

# Step 7: Run ETL
echo -e "${YELLOW}Step 7: Running ETL process...${NC}"
docker-compose exec -T bot python3 /src/etl/etl_oltp_to_olap.py
echo -e "${GREEN}✓ ETL completed${NC}"
echo ""

# Step 8: Verify deployment
echo -e "${YELLOW}Step 8: Verifying deployment...${NC}"

# Check containers
RUNNING_CONTAINERS=$(docker-compose ps --services --filter "status=running" | wc -l)
if [ "$RUNNING_CONTAINERS" -lt 2 ]; then
    echo -e "${RED}✗ Not all containers are running${NC}"
    docker-compose ps
    exit 1
fi

# Check OLAP data
OLAP_DIM_TIME=$(docker-compose exec -T db psql -U user -d db_olap -t -c "SELECT COUNT(*) FROM dim_time;")
OLAP_BRIDGE=$(docker-compose exec -T db psql -U user -d db_olap -t -c "SELECT COUNT(*) FROM bridge_lesson_groups;")

echo "OLAP data:"
echo "  - dim_time records: $OLAP_DIM_TIME"
echo "  - bridge_lesson_groups records: $OLAP_BRIDGE"

if [ "$OLAP_BRIDGE" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Warning: No data in bridge_lesson_groups${NC}"
fi

echo -e "${GREEN}✓ Deployment verified${NC}"
echo ""

# Step 9: Show status
echo -e "${YELLOW}Step 9: Current status...${NC}"
docker-compose ps
echo ""

# Final message
echo "=========================================="
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Check bot logs: docker-compose logs bot"
echo "  2. Test bot commands in Telegram"
echo "  3. Run analytics: docker-compose exec db psql -U user -d db_olap -f /src/queries/olap_queries.sql"
echo ""
echo "For more information, see DEPLOYMENT.md"
