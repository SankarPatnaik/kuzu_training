// KuzuDB schema for a KYC onboarding knowledge graph and evidence retrieval graph.
// Run with: python src/build_graph.py --reset

CREATE NODE TABLE PolicyDocument(
  document_id STRING,
  title STRING,
  source STRING,
  region STRING,
  client_type STRING,
  risk_rating STRING,
  version STRING,
  effective_date STRING,
  text_summary STRING,
  PRIMARY KEY(document_id)
);

CREATE NODE TABLE Chunk(
  chunk_id STRING,
  document_id STRING,
  sequence INT64,
  text STRING,
  section STRING,
  token_count INT64,
  PRIMARY KEY(chunk_id)
);

CREATE NODE TABLE Country(
  code STRING,
  name STRING,
  region STRING,
  PRIMARY KEY(code)
);

CREATE NODE TABLE ClientType(
  client_type_id STRING,
  name STRING,
  description STRING,
  PRIMARY KEY(client_type_id)
);

CREATE NODE TABLE RiskLevel(
  risk_id STRING,
  name STRING,
  score INT64,
  PRIMARY KEY(risk_id)
);

CREATE NODE TABLE Topic(
  topic_id STRING,
  name STRING,
  description STRING,
  PRIMARY KEY(topic_id)
);

CREATE NODE TABLE Requirement(
  requirement_id STRING,
  description STRING,
  normalized_question STRING,
  region STRING,
  client_type STRING,
  risk_rating STRING,
  priority STRING,
  PRIMARY KEY(requirement_id)
);

CREATE NODE TABLE Control(
  control_id STRING,
  name STRING,
  control_type STRING,
  severity STRING,
  description STRING,
  PRIMARY KEY(control_id)
);

CREATE NODE TABLE System(
  system_id STRING,
  name STRING,
  system_type STRING,
  owner STRING,
  description STRING,
  PRIMARY KEY(system_id)
);

CREATE NODE TABLE UseCase(
  use_case_id STRING,
  name STRING,
  business_goal STRING,
  owner STRING,
  maturity STRING,
  PRIMARY KEY(use_case_id)
);

// Context graph nodes: runtime retrieval state, not just business domain knowledge.
CREATE NODE TABLE UserQuery(
  query_id STRING,
  user_role STRING,
  question STRING,
  timestamp STRING,
  PRIMARY KEY(query_id)
);

CREATE NODE TABLE RetrievalContext(
  context_id STRING,
  query_id STRING,
  strategy STRING,
  rank INT64,
  summary STRING,
  PRIMARY KEY(context_id)
);

CREATE NODE TABLE Answer(
  answer_id STRING,
  query_id STRING,
  summary STRING,
  confidence DOUBLE,
  PRIMARY KEY(answer_id)
);

CREATE REL TABLE HAS_CHUNK(FROM PolicyDocument TO Chunk, position INT64);
CREATE REL TABLE APPLIES_TO_COUNTRY(FROM PolicyDocument TO Country, rule STRING);
CREATE REL TABLE APPLIES_TO_CLIENT_TYPE(FROM PolicyDocument TO ClientType, rule STRING);
CREATE REL TABLE APPLIES_TO_RISK(FROM PolicyDocument TO RiskLevel, rule STRING);
CREATE REL TABLE MENTIONS_TOPIC(FROM Chunk TO Topic, weight DOUBLE);
CREATE REL TABLE GENERATES_REQUIREMENT(FROM PolicyDocument TO Requirement, confidence DOUBLE);
CREATE REL TABLE REQUIREMENT_FROM_CHUNK(FROM Requirement TO Chunk, evidence_score DOUBLE);
CREATE REL TABLE MAPPED_TO_CONTROL(FROM Requirement TO Control, mapping_type STRING);
CREATE REL TABLE IMPLEMENTED_IN(FROM Requirement TO System, implementation_status STRING);
CREATE REL TABLE DEPENDS_ON(FROM Requirement TO Requirement, dependency_type STRING);
CREATE REL TABLE USE_CASE_USES_DOCUMENT(FROM UseCase TO PolicyDocument, usage_type STRING);
CREATE REL TABLE USE_CASE_USES_SYSTEM(FROM UseCase TO System, usage_type STRING);

CREATE REL TABLE QUERY_RETRIEVES_CONTEXT(FROM UserQuery TO RetrievalContext, latency_ms INT64);
CREATE REL TABLE CONTEXT_USES_CHUNK(FROM RetrievalContext TO Chunk, rank INT64);
CREATE REL TABLE CONTEXT_SUPPORTS_REQUIREMENT(FROM RetrievalContext TO Requirement, rank INT64);
CREATE REL TABLE ANSWER_USES_CONTEXT(FROM Answer TO RetrievalContext, groundedness_score DOUBLE);
