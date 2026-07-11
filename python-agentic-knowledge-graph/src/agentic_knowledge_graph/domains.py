"""Compact schemas and progressive Cypher queries for five training domains."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class NodeSpec:
    name: str
    primary_key: str
    columns: tuple[tuple[str, str], ...]
    def create_statement(self) -> str:
        fields = ", ".join(f"{n} {t}" for n, t in self.columns)
        return f"CREATE NODE TABLE {self.name}({fields}, PRIMARY KEY({self.primary_key}))"

@dataclass(frozen=True)
class RelationshipSpec:
    name: str
    from_node: str
    to_node: str
    columns: tuple[tuple[str, str], ...] = ()
    def create_statement(self) -> str:
        props = "" if not self.columns else ", " + ", ".join(f"{n} {t}" for n, t in self.columns)
        return f"CREATE REL TABLE {self.name}(FROM {self.from_node} TO {self.to_node}{props})"

@dataclass(frozen=True)
class QuerySpec:
    title: str
    cypher: str
    teaching_point: str

@dataclass(frozen=True)
class DomainSpec:
    name: str
    description: str
    nodes: tuple[NodeSpec, ...]
    relationships: tuple[RelationshipSpec, ...]
    queries: tuple[QuerySpec, ...]
    keywords: tuple[str, ...]
    default_query: int = 1
    @property
    def node_map(self) -> Mapping[str, NodeSpec]: return {x.name: x for x in self.nodes}
    @property
    def relationship_map(self) -> Mapping[str, RelationshipSpec]: return {x.name: x for x in self.relationships}

def N(name: str, key: str, *columns: tuple[str, str]) -> NodeSpec: return NodeSpec(name, key, columns)
def R(name: str, source: str, target: str, *columns: tuple[str, str]) -> RelationshipSpec: return RelationshipSpec(name, source, target, columns)
def Q(title: str, cypher: str, point: str) -> QuerySpec: return QuerySpec(title, cypher, point)

YOGA = DomainSpec("yoga", "Yoga poses, benefits, instructors and studios.", (
 N("YogaStyle","name",("name","STRING"),("origin","STRING"),("description","STRING"),("difficulty_level","INT64")),
 N("Pose","name",("name","STRING"),("sanskrit_name","STRING"),("difficulty","INT64"),("description","STRING"),("target_time","STRING")),
 N("Benefit","name",("name","STRING"),("category","STRING"),("description","STRING")), N("BodyPart","name",("name","STRING"),("description","STRING")),
 N("Instructor","name",("name","STRING"),("experience_years","INT64"),("specialization","STRING"),("certification","STRING")),
 N("Studio","name",("name","STRING"),("city","STRING"),("capacity","INT64"),("opening_year","INT64")), N("PoseType","name",("name","STRING"),("description","STRING"))), (
 R("BelongsToStyle","Pose","YogaStyle"), R("TargetsBenefit","Pose","Benefit",("intensity","INT64")), R("EngagesBodyPart","Pose","BodyPart",("engagement_level","INT64")),
 R("Teaches","Instructor","YogaStyle",("years_teaching","INT64")), R("WorksAt","Instructor","Studio",("start_year","INT64")), R("RecommendsFor","YogaStyle","Benefit"), R("HasType","Pose","PoseType")), (
 Q("Styles and poses","MATCH (p:Pose)-[:BelongsToStyle]->(s:YogaStyle) RETURN s.name,p.name,p.sanskrit_name,p.difficulty ORDER BY s.name,p.difficulty","One-hop traversal"),
 Q("Pose benefits","MATCH (p:Pose)-[r:TargetsBenefit]->(b:Benefit) RETURN p.name,b.name,b.category,r.intensity ORDER BY r.intensity DESC","Relationship properties"),
 Q("Body parts engaged","MATCH (p:Pose)-[r:EngagesBodyPart]->(b:BodyPart) RETURN p.name,b.name,r.engagement_level ORDER BY r.engagement_level DESC","Edge context"),
 Q("Advanced poses","MATCH (p:Pose) WHERE p.difficulty>=7 RETURN p.name,p.sanskrit_name,p.difficulty ORDER BY p.difficulty DESC","Filtering"),
 Q("Complete pose profiles","MATCH (p:Pose)-[:BelongsToStyle]->(s:YogaStyle),(p)-[:TargetsBenefit]->(b:Benefit),(p)-[:HasType]->(t:PoseType) RETURN p.name,s.name,b.name,t.name","Multi-path matching"),
 Q("Instructor specialisms","MATCH (i:Instructor)-[r:Teaches]->(s:YogaStyle) RETURN i.name,i.specialization,s.name,r.years_teaching","People relationships"),
 Q("Studios and instructors","MATCH (i:Instructor)-[r:WorksAt]->(s:Studio) RETURN s.name,s.city,i.name,i.experience_years,r.start_year","Operational traversal"),
 Q("Recommended benefits","MATCH (s:YogaStyle)-[:RecommendsFor]->(b:Benefit) RETURN s.name,b.name,b.category","Recommendation paths"),
 Q("Beginner poses","MATCH (p:Pose)-[:BelongsToStyle]->(s:YogaStyle) WHERE p.difficulty<=3 RETURN p.name,s.name,p.difficulty ORDER BY p.difficulty","User filtering"),
 Q("Body-part aggregation","MATCH (p:Pose)-[r:EngagesBodyPart]->(b:BodyPart) WITH b,COUNT(p) AS poses,AVG(r.engagement_level) AS avg RETURN b.name,poses,avg ORDER BY poses DESC","Aggregation")), ("yoga","pose","flexibility","studio","instructor","body"))

FRAUD = DomainSpec("fraud", "Fraud methods, indicators and data sources.", (
 N("FraudType","name",("name","STRING"),("severity","STRING"),("description","STRING")), N("DetectionMethod","name",("name","STRING"),("method_type","STRING"),("description","STRING")),
 N("Indicator","name",("name","STRING"),("category","STRING"),("description","STRING")), N("DataSource","name",("name","STRING"),("freshness","STRING"),("description","STRING"))), (
 R("Detects","DetectionMethod","FraudType",("confidence","DOUBLE")), R("Uses","DetectionMethod","Indicator",("weight","DOUBLE")), R("Analyzes","DetectionMethod","DataSource",("priority","INT64"))), (
 Q("Methods and fraud types","MATCH (m:DetectionMethod)-[r:Detects]->(f:FraudType) RETURN m.name,f.name,r.confidence ORDER BY r.confidence DESC","Confidence"),
 Q("Methods and indicators","MATCH (m:DetectionMethod)-[r:Uses]->(i:Indicator) RETURN m.name,i.name,i.category,r.weight","Feature mapping"),
 Q("Detection workflow","MATCH (i:Indicator)<-[:Uses]-(m:DetectionMethod)-[r:Detects]->(f:FraudType) RETURN i.name,m.name,f.name,r.confidence","Multi-hop path"),
 Q("Method data sources","MATCH (m:DetectionMethod)-[r:Analyzes]->(d:DataSource) RETURN m.name,d.name,d.freshness,r.priority","Lineage"),
 Q("High-confidence detections","MATCH (m:DetectionMethod)-[r:Detects]->(f:FraudType) WHERE r.confidence>=0.85 RETURN m.name,f.name,r.confidence ORDER BY r.confidence DESC","Threshold"),
 Q("Fraud coverage","MATCH (m:DetectionMethod)-[:Detects]->(f:FraudType) WITH f,COUNT(m) AS methods RETURN f.name,f.severity,methods ORDER BY methods DESC","Coverage"),
 Q("Methods by indicators","MATCH (m:DetectionMethod)-[:Uses]->(i:Indicator) WITH m,COUNT(i) AS indicators RETURN m.name,m.method_type,indicators ORDER BY indicators DESC","Ranking"),
 Q("Complete pipeline","MATCH (d:DataSource)<-[:Analyzes]-(m:DetectionMethod)-[:Uses]->(i:Indicator),(m)-[r:Detects]->(f:FraudType) RETURN d.name,m.name,i.name,f.name,r.confidence","Four entities"),
 Q("Shared indicators","MATCH (m:DetectionMethod)-[:Uses]->(i:Indicator) WITH i,COUNT(m) AS reuse WHERE reuse>1 RETURN i.name,i.category,reuse ORDER BY reuse DESC","Reuse"),
 Q("Source coverage","MATCH (m:DetectionMethod)-[:Analyzes]->(d:DataSource) WITH d,COUNT(m) AS methods RETURN d.name,d.freshness,methods ORDER BY methods DESC","Source coverage")), ("fraud","indicator","detection","confidence","risk","source"))

CYCLE = DomainSpec("cycle", "Accounts, transactions and circular money flows.", (
 N("Account","account_id",("account_id","STRING"),("account_type","STRING"),("risk_score","DOUBLE")), N("Transaction","transaction_id",("transaction_id","STRING"),("amount","DOUBLE"),("timestamp","STRING")),
 N("CyclePattern","pattern_id",("pattern_id","STRING"),("pattern_name","STRING"),("description","STRING"),("risk_level","STRING")), N("Algorithm","name",("name","STRING"),("description","STRING"),("time_complexity","STRING"))), (
 R("Transfers","Account","Account",("transaction_id","STRING"),("amount","DOUBLE"),("timestamp","STRING")), R("Involves","Transaction","Account",("role","STRING")), R("DetectsPattern","Algorithm","CyclePattern",("confidence","DOUBLE"))), (
 Q("All transfers","MATCH (a:Account)-[r:Transfers]->(b:Account) RETURN a.account_id,b.account_id,r.transaction_id,r.amount,r.timestamp","Directed edges"),
 Q("High-risk accounts","MATCH (a:Account) WHERE a.risk_score>0.70 RETURN a.account_id,a.account_type,a.risk_score ORDER BY a.risk_score DESC","Risk filter"),
 Q("Two-step cycles","MATCH (a:Account)-[:Transfers]->(b:Account)-[:Transfers]->(a) RETURN a.account_id,b.account_id","Two-hop cycle"),
 Q("Three-step cycles","MATCH (a:Account)-[:Transfers]->(b:Account)-[:Transfers]->(c:Account)-[:Transfers]->(a) RETURN a.account_id,b.account_id,c.account_id","Three-hop cycle"),
 Q("Four-step cycles","MATCH (a:Account)-[r1:Transfers]->(b:Account)-[r2:Transfers]->(c:Account)-[r3:Transfers]->(d:Account)-[r4:Transfers]->(a) RETURN a.account_id,b.account_id,c.account_id,d.account_id,r1.amount+r2.amount+r3.amount+r4.amount AS total","Known typology"),
 Q("Transfer summary","MATCH (a:Account)-[r:Transfers]->(b:Account) WITH a,COUNT(b) AS count,SUM(r.amount) AS amount RETURN a.account_id,a.risk_score,count,amount ORDER BY amount DESC","Aggregation"),
 Q("Patterns and algorithms","MATCH (a:Algorithm)-[r:DetectsPattern]->(p:CyclePattern) RETURN a.name,a.time_complexity,p.pattern_name,p.risk_level,r.confidence","Algorithm knowledge"),
 Q("High-risk transfers","MATCH (a:Account)-[r:Transfers]->(b:Account) WHERE a.risk_score>0.70 OR b.risk_score>0.70 RETURN a.account_id,b.account_id,a.risk_score,b.risk_score,r.amount","Risk-aware paths"),
 Q("Transaction participants","MATCH (t:Transaction)-[r:Involves]->(a:Account) RETURN t.transaction_id,t.amount,a.account_id,r.role","Event linkage"),
 Q("Cycle risk evidence","MATCH (a:Account)-[:Transfers]->(b:Account)-[:Transfers]->(c:Account)-[:Transfers]->(d:Account)-[:Transfers]->(a) RETURN a.account_id,a.risk_score,b.account_id,b.risk_score,c.account_id,c.risk_score,d.account_id,d.risk_score","Explainability")), ("cycle","transfer","account","money laundering","aml","transaction"), 5)

MIGRATION = DomainSpec("migration", "Bird routes, seasons and environmental context.", (
 N("BirdSpecies","name",("name","STRING"),("migration_distance","INT64"),("flight_duration","INT64")), N("Location","name",("name","STRING"),("location_type","STRING"),("habitat_quality","INT64")),
 N("Season","name",("name","STRING"),("month_range","STRING"),("temperature_range","STRING")), N("EnvironmentalFactor","name",("name","STRING"),("description","STRING"),("impact_level","INT64"))), (
 R("MigratesFrom","BirdSpecies","Location",("departure_month","STRING")), R("MigratesTo","BirdSpecies","Location",("arrival_month","STRING")), R("ActiveIn","Location","Season"), R("InfluencedBy","BirdSpecies","EnvironmentalFactor",("influence_strength","INT64"))), (
 Q("Species distances","MATCH (b:BirdSpecies) RETURN b.name,b.migration_distance,b.flight_duration ORDER BY b.migration_distance DESC","Entity analytics"),
 Q("Departure routes","MATCH (b:BirdSpecies)-[r:MigratesFrom]->(l:Location) RETURN b.name,l.name,l.location_type,r.departure_month","Origin"),
 Q("Arrival routes","MATCH (b:BirdSpecies)-[r:MigratesTo]->(l:Location) RETURN b.name,l.name,l.location_type,r.arrival_month","Destination"),
 Q("Long-distance migrants","MATCH (b:BirdSpecies) WHERE b.migration_distance>8000 RETURN b.name,b.migration_distance,b.flight_duration","Threshold"),
 Q("Important locations","MATCH (b:BirdSpecies)-[:MigratesFrom]->(l:Location) RETURN l.name,l.location_type,l.habitat_quality,COUNT(b) AS species","Location aggregation"),
 Q("Environmental influences","MATCH (b:BirdSpecies)-[r:InfluencedBy]->(f:EnvironmentalFactor) RETURN b.name,f.name,f.impact_level,r.influence_strength","Context"),
 Q("Seasonal activity","MATCH (l:Location)-[:ActiveIn]->(s:Season) RETURN l.name,l.location_type,s.name,s.month_range","Temporal context"),
 Q("Complete routes","MATCH (b:BirdSpecies)-[f:MigratesFrom]->(o:Location),(b)-[t:MigratesTo]->(d:Location) RETURN b.name,o.name,f.departure_month,d.name,t.arrival_month,b.migration_distance","Lifecycle"),
 Q("Most influenced species","MATCH (b:BirdSpecies)-[:InfluencedBy]->(f:EnvironmentalFactor) WITH b,COUNT(f) AS factors RETURN b.name,factors ORDER BY factors DESC","Aggregation"),
 Q("Migration efficiency","MATCH (b:BirdSpecies) RETURN b.name,b.migration_distance,b.flight_duration,b.migration_distance/b.flight_duration AS miles_per_day ORDER BY miles_per_day DESC","Derived metric")), ("bird","migration","season","habitat","environment","route"), 8)

PROFESSIONAL = DomainSpec("professional", "Professional skills, organizations and achievements.", (
 N("Person","name",("name","STRING"),("title","STRING"),("experience_years","INT64"),("summary","STRING")), N("Skill","name",("name","STRING"),("category","STRING"),("description","STRING")),
 N("Organization","name",("name","STRING"),("industry","STRING"),("description","STRING")), N("Location","name",("name","STRING"),("region","STRING"),("description","STRING")), N("Achievement","name",("name","STRING"),("category","STRING"),("description","STRING"))), (
 R("HasSkill","Person","Skill",("proficiency","INT64"),("last_used_year","INT64")), R("WorksFor","Person","Organization",("years_of_service","INT64")), R("LivesIn","Person","Location"), R("BornIn","Person","Location"),
 R("HasAchievement","Person","Achievement",("count","INT64")), R("LocatedIn","Organization","Location"), R("RelatedTo","Skill","Skill",("relationship_type","STRING"))), (
 Q("Profile summary","MATCH (p:Person) RETURN p.name,p.title,p.experience_years,p.summary","Profile"),
 Q("Skills and proficiency","MATCH (p:Person)-[r:HasSkill]->(s:Skill) RETURN p.name,s.name,s.category,r.proficiency,r.last_used_year ORDER BY r.proficiency DESC","Evidence"),
 Q("Related skills","MATCH (s:Skill)-[r:RelatedTo]->(t:Skill) RETURN s.name,r.relationship_type,t.name","Ontology"),
 Q("Work experience","MATCH (p:Person)-[r:WorksFor]->(o:Organization) RETURN p.name,o.name,o.industry,r.years_of_service","Organization"),
 Q("Geographic context","MATCH (p:Person)-[:LivesIn]->(l:Location) RETURN p.name,'lives in' AS relation,l.name,l.region UNION ALL MATCH (p:Person)-[:BornIn]->(l:Location) RETURN p.name,'born in' AS relation,l.name,l.region","Multiple edges"),
 Q("Achievements","MATCH (p:Person)-[r:HasAchievement]->(a:Achievement) RETURN p.name,a.name,a.category,r.count ORDER BY r.count DESC","Achievements"),
 Q("Skills by category","MATCH (p:Person)-[r:HasSkill]->(s:Skill) WITH s.category AS category,COUNT(s) AS skills,AVG(r.proficiency) AS avg RETURN category,skills,avg ORDER BY avg DESC","Aggregation"),
 Q("Organizations and locations","MATCH (p:Person)-[:WorksFor]->(o:Organization)-[:LocatedIn]->(l:Location) RETURN p.name,o.name,l.name,l.region","Three-node path"),
 Q("Profile metrics","MATCH (p:Person)-[r:HasSkill]->(s:Skill) WITH p,COUNT(s) AS skills,AVG(r.proficiency) AS avg RETURN p.name,p.experience_years,skills,avg","Metrics"),
 Q("Expertise classification","MATCH (p:Person)-[r:HasSkill]->(s:Skill) RETURN p.name,s.name,s.category,r.proficiency,CASE WHEN r.proficiency>=90 THEN 'Expert' WHEN r.proficiency>=80 THEN 'Advanced' ELSE 'Intermediate' END AS level ORDER BY r.proficiency DESC","Classification")), ("skill","expert","engineer","professional","organization","achievement","python","graph"), 10)

DOMAINS = {d.name: d for d in (YOGA, FRAUD, CYCLE, MIGRATION, PROFESSIONAL)}
def get_domain(name: str) -> DomainSpec:
    try: return DOMAINS[name.strip().lower()]
    except KeyError as exc: raise ValueError(f"Unknown domain '{name}'. Choose one of: {', '.join(sorted(DOMAINS))}") from exc
