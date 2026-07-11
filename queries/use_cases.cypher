// Run these queries in Kuzu Explorer, Python, or the Kuzu CLI.

// 1) Explore the whole graph in an explorer UI.
MATCH p=()-->() RETURN p LIMIT 100;

// 2) Find all policy questions for high-risk US corporate clients.
MATCH (d:PolicyDocument)-[:APPLIES_TO_COUNTRY]->(country:Country),
      (d)-[:APPLIES_TO_CLIENT_TYPE]->(ct:ClientType),
      (d)-[:APPLIES_TO_RISK]->(risk:RiskLevel),
      (d)-[:GENERATES_REQUIREMENT]->(r:Requirement)
WHERE (country.code = 'GLOBAL' OR country.code = 'US')
  AND (ct.client_type_id = 'ALL' OR ct.client_type_id = 'CORP')
  AND (risk.risk_id = 'ALL' OR risk.risk_id = 'HIGH')
RETURN d.title, d.version, r.requirement_id, r.normalized_question, r.priority;

// 3) Explain one requirement using its source chunk.
MATCH (r:Requirement)-[:REQUIREMENT_FROM_CHUNK]->(c:Chunk)<-[:HAS_CHUNK]-(d:PolicyDocument)
WHERE r.requirement_id = 'R004'
RETURN r.description, d.title, d.version, c.section, c.text;

// 4) Find critical requirements and their preventive controls.
MATCH (r:Requirement)-[:MAPPED_TO_CONTROL]->(ctrl:Control)
WHERE r.priority = 'Critical' AND ctrl.control_type = 'Preventive'
RETURN r.requirement_id, r.description, ctrl.name, ctrl.severity;

// 5) Show context graph evidence for a runtime user question.
MATCH (q:UserQuery)-[:QUERY_RETRIEVES_CONTEXT]->(ctx:RetrievalContext)-[:CONTEXT_SUPPORTS_REQUIREMENT]->(r:Requirement),
      (ctx)-[:CONTEXT_USES_CHUNK]->(chunk:Chunk)<-[:HAS_CHUNK]-(doc:PolicyDocument)
WHERE q.query_id = 'Q001'
RETURN q.question, ctx.strategy, r.requirement_id, r.normalized_question, doc.title, chunk.section;
