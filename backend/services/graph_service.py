from neo4j import GraphDatabase
from backend.core.config import settings
from backend.utils.logger import logger

class GraphService:
    def __init__(self):
        try:
            uri = settings.NEO4J_URI
            auth = ("neo4j", "testpassword") 
            self.driver = GraphDatabase.driver(uri, auth=auth)
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j Knowledge Graph successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def get_company_relationships(self, ticker: str) -> dict:
        """
        Retrieves graph relationships for a specific company ticker.
        e.g., (Person)-[:DIRECTOR_OF]->(Company)
        """
        if not self.driver:
            logger.warning("Neo4j not available. Returning empty relationships.")
            return {}

        query = """
        MATCH (p:Person)-[r:DIRECTOR_OF|INVESTOR_IN]->(c:Company {ticker: $ticker})
        RETURN p.name AS person, type(r) AS relationship, c.name AS company
        LIMIT 10
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, ticker=ticker)
                records = [record.data() for record in result]
                return {"relationships": records}
        except Exception as e:
            logger.error(f"Error querying Neo4j for {ticker}: {e}")
            return {}

    def seed_mock_data(self):
        """Seeds the Knowledge Graph with mock prototype data."""
        if not self.driver:
            return
        
        query = """
        MERGE (c:Company {ticker: 'AAPL', name: 'Apple Inc.'})
        MERGE (p1:Person {name: 'Tim Cook'})
        MERGE (p2:Person {name: 'Arthur Levinson'})
        MERGE (p1)-[:DIRECTOR_OF]->(c)
        MERGE (p2)-[:INVESTOR_IN]->(c)
        """
        try:
            with self.driver.session() as session:
                session.run(query)
                logger.info("Seeded Neo4j with mock relationships.")
        except Exception as e:
            logger.error(f"Failed to seed Neo4j: {e}")

graph_service = GraphService()
