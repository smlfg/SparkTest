"""
Text-to-Knowledge-Graph (txt2kg) Pipeline
Extracts entities and relationships from text to build knowledge graphs

Dependencies: Agent 4/5 (inference)
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an entity in the knowledge graph"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Entity) and self.id == other.id


@dataclass
class Relationship:
    """Represents a relationship between entities"""
    source: Entity
    target: Entity
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_triple(self) -> Tuple[str, str, str]:
        """Convert to (subject, predicate, object) triple"""
        return (self.source.name, self.relation_type, self.target.name)


@dataclass
class KnowledgeGraph:
    """Knowledge graph structure"""
    entities: Dict[str, Entity] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_entity(self, entity: Entity):
        """Add an entity to the graph"""
        self.entities[entity.id] = entity

    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the graph"""
        # Ensure entities exist
        if relationship.source.id not in self.entities:
            self.add_entity(relationship.source)
        if relationship.target.id not in self.entities:
            self.add_entity(relationship.target)

        self.relationships.append(relationship)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)

    def get_relationships_for_entity(self, entity_id: str) -> List[Relationship]:
        """Get all relationships involving an entity"""
        return [
            rel for rel in self.relationships
            if rel.source.id == entity_id or rel.target.id == entity_id
        ]

    def get_neighbors(self, entity_id: str) -> Set[Entity]:
        """Get neighboring entities"""
        neighbors = set()
        for rel in self.get_relationships_for_entity(entity_id):
            if rel.source.id == entity_id:
                neighbors.add(rel.target)
            else:
                neighbors.add(rel.source)
        return neighbors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "entities": [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.type,
                    "properties": entity.properties
                }
                for entity in self.entities.values()
            ],
            "relationships": [
                {
                    "source": rel.source.id,
                    "target": rel.target.id,
                    "type": rel.relation_type,
                    "properties": rel.properties,
                    "confidence": rel.confidence
                }
                for rel in self.relationships
            ],
            "metadata": self.metadata
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        entity_types = defaultdict(int)
        for entity in self.entities.values():
            entity_types[entity.type] += 1

        relation_types = defaultdict(int)
        for rel in self.relationships:
            relation_types[rel.relation_type] += 1

        return {
            "num_entities": len(self.entities),
            "num_relationships": len(self.relationships),
            "entity_types": dict(entity_types),
            "relation_types": dict(relation_types)
        }


class NERService:
    """
    Named Entity Recognition service using Agent 4/5 inference
    """

    def __init__(self, agent_url: str = "http://localhost:8000"):
        self.agent_url = agent_url

    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text

        Args:
            text: Input text

        Returns:
            List of extracted entities with type and span information
        """
        # Build prompt for entity extraction
        prompt = f"""Extract named entities from the following text. For each entity, provide:
- Entity name
- Entity type (PERSON, ORGANIZATION, LOCATION, TECHNOLOGY, CONCEPT, etc.)

Text: {text}

Format your response as JSON array:
[{{"name": "entity_name", "type": "ENTITY_TYPE"}}, ...]"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_url}/generate",
                    json={
                        "prompt": prompt,
                        "model": "gpt-4",
                        "max_tokens": 500,
                        "temperature": 0.3
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_text = data.get("text", "[]")

                        # Parse JSON response
                        try:
                            # Extract JSON from markdown code blocks if present
                            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', result_text, re.DOTALL)
                            if json_match:
                                result_text = json_match.group(1)
                            elif result_text.strip().startswith('['):
                                # Direct JSON response
                                pass
                            else:
                                # Try to find JSON array
                                json_match = re.search(r'\[.*?\]', result_text, re.DOTALL)
                                if json_match:
                                    result_text = json_match.group(0)

                            entities = json.loads(result_text)
                            return entities if isinstance(entities, list) else []
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse entity extraction result: {result_text}")
                            return []
                    else:
                        logger.error(f"Entity extraction failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"NER service error: {e}")
            return []


class RelationExtractor:
    """
    Service for extracting relationships between entities
    """

    def __init__(self, agent_url: str = "http://localhost:8000"):
        self.agent_url = agent_url

    async def extract_relationships(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Tuple[str, str, str]]:
        """
        Extract relationships between entities in text

        Args:
            text: Input text
            entities: List of entities found in the text

        Returns:
            List of (source_entity, relation, target_entity) triples
        """
        if len(entities) < 2:
            return []

        entity_names = [e.name for e in entities]

        prompt = f"""Given the following text and entities, extract relationships between them.

Text: {text}

Entities: {', '.join(entity_names)}

For each relationship, provide:
- Source entity
- Relationship type (e.g., WORKS_FOR, LOCATED_IN, PART_OF, USES, CREATES, etc.)
- Target entity

Format as JSON array:
[{{"source": "entity1", "relation": "RELATION_TYPE", "target": "entity2"}}, ...]"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_url}/generate",
                    json={
                        "prompt": prompt,
                        "model": "gpt-4",
                        "max_tokens": 500,
                        "temperature": 0.3
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_text = data.get("text", "[]")

                        try:
                            # Extract JSON from markdown code blocks if present
                            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', result_text, re.DOTALL)
                            if json_match:
                                result_text = json_match.group(1)
                            elif result_text.strip().startswith('['):
                                pass
                            else:
                                json_match = re.search(r'\[.*?\]', result_text, re.DOTALL)
                                if json_match:
                                    result_text = json_match.group(0)

                            relationships = json.loads(result_text)
                            if isinstance(relationships, list):
                                return [
                                    (rel["source"], rel["relation"], rel["target"])
                                    for rel in relationships
                                    if all(k in rel for k in ["source", "relation", "target"])
                                ]
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"Failed to parse relationship extraction: {e}")
                            return []
                    return []
        except Exception as e:
            logger.error(f"Relationship extraction error: {e}")
            return []


class Text2KGPipeline:
    """
    Complete pipeline for converting text to knowledge graph
    """

    def __init__(self, agent_url: str = "http://localhost:8000"):
        self.agent_url = agent_url
        self.ner_service = NERService(agent_url)
        self.relation_extractor = RelationExtractor(agent_url)

    def _create_entity_id(self, name: str, entity_type: str) -> str:
        """Generate entity ID from name and type"""
        clean_name = re.sub(r'\W+', '_', name.lower())
        return f"{entity_type.lower()}_{clean_name}"

    async def process_text(self, text: str) -> KnowledgeGraph:
        """
        Process text and build knowledge graph

        Args:
            text: Input text

        Returns:
            KnowledgeGraph extracted from text
        """
        kg = KnowledgeGraph(metadata={"source_text": text[:200]})

        # Step 1: Extract entities
        logger.info("Extracting entities...")
        entity_data = await self.ner_service.extract_entities(text)

        entities = []
        for ent_data in entity_data:
            entity = Entity(
                id=self._create_entity_id(ent_data["name"], ent_data["type"]),
                name=ent_data["name"],
                type=ent_data["type"]
            )
            kg.add_entity(entity)
            entities.append(entity)

        logger.info(f"Extracted {len(entities)} entities")

        if not entities:
            return kg

        # Step 2: Extract relationships
        logger.info("Extracting relationships...")
        relationship_triples = await self.relation_extractor.extract_relationships(
            text, entities
        )

        # Build entity name to entity mapping
        entity_map = {e.name.lower(): e for e in entities}

        for source_name, relation_type, target_name in relationship_triples:
            source_entity = entity_map.get(source_name.lower())
            target_entity = entity_map.get(target_name.lower())

            if source_entity and target_entity:
                relationship = Relationship(
                    source=source_entity,
                    target=target_entity,
                    relation_type=relation_type,
                    confidence=0.8
                )
                kg.add_relationship(relationship)

        logger.info(f"Extracted {len(kg.relationships)} relationships")

        return kg

    async def process_documents(self, documents: List[str]) -> KnowledgeGraph:
        """
        Process multiple documents and build unified knowledge graph

        Args:
            documents: List of text documents

        Returns:
            Unified knowledge graph
        """
        kg = KnowledgeGraph(metadata={"num_documents": len(documents)})

        for i, doc in enumerate(documents):
            logger.info(f"Processing document {i+1}/{len(documents)}")
            doc_kg = await self.process_text(doc)

            # Merge into main graph
            for entity in doc_kg.entities.values():
                if entity.id not in kg.entities:
                    kg.add_entity(entity)

            for relationship in doc_kg.relationships:
                kg.add_relationship(relationship)

        return kg


class KnowledgeGraphVisualizer:
    """
    Service for visualizing knowledge graphs
    """

    def to_cytoscape_format(self, kg: KnowledgeGraph) -> Dict[str, Any]:
        """
        Convert knowledge graph to Cytoscape.js format

        Args:
            kg: Knowledge graph

        Returns:
            Cytoscape.js compatible data structure
        """
        elements = []

        # Add nodes
        for entity in kg.entities.values():
            elements.append({
                "data": {
                    "id": entity.id,
                    "label": entity.name,
                    "type": entity.type,
                    "properties": entity.properties
                },
                "classes": entity.type.lower()
            })

        # Add edges
        for i, rel in enumerate(kg.relationships):
            elements.append({
                "data": {
                    "id": f"edge_{i}",
                    "source": rel.source.id,
                    "target": rel.target.id,
                    "label": rel.relation_type,
                    "confidence": rel.confidence
                },
                "classes": "relationship"
            })

        return {"elements": elements}

    def to_graphviz_dot(self, kg: KnowledgeGraph) -> str:
        """
        Convert knowledge graph to GraphViz DOT format

        Args:
            kg: Knowledge graph

        Returns:
            DOT format string
        """
        lines = ["digraph KnowledgeGraph {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=rounded];")

        # Add nodes
        for entity in kg.entities.values():
            label = f"{entity.name}\\n({entity.type})"
            lines.append(f'  "{entity.id}" [label="{label}"];')

        # Add edges
        for rel in kg.relationships:
            lines.append(
                f'  "{rel.source.id}" -> "{rel.target.id}" [label="{rel.relation_type}"];'
            )

        lines.append("}")
        return "\n".join(lines)


async def main():
    """Demo txt2kg pipeline"""
    print("Text-to-Knowledge-Graph (txt2kg) Pipeline")
    print("=" * 50)

    # Initialize pipeline
    pipeline = Text2KGPipeline(agent_url="http://localhost:8000")

    # Sample text
    sample_text = """
    Apache Spark is a unified analytics engine developed by the Apache Software Foundation.
    Spark was originally created at UC Berkeley by Matei Zaharia.
    The framework provides high-level APIs in Java, Scala, Python and R.
    Spark uses a distributed computing architecture based on resilient distributed datasets (RDDs).
    MLlib is Spark's machine learning library, which includes various algorithms for classification,
    regression, and clustering. Spark SQL is another component that enables structured data processing.
    """

    print("\nInput Text:")
    print("-" * 50)
    print(sample_text.strip())

    print("\n" + "=" * 50)
    print("Processing...")
    print("=" * 50)

    # Build knowledge graph
    kg = await pipeline.process_text(sample_text)

    # Display results
    print("\nExtracted Knowledge Graph:")
    print("-" * 50)

    stats = kg.get_statistics()
    print(f"\nStatistics:")
    print(f"  Entities: {stats['num_entities']}")
    print(f"  Relationships: {stats['num_relationships']}")

    print(f"\nEntity Types:")
    for entity_type, count in stats['entity_types'].items():
        print(f"  {entity_type}: {count}")

    print(f"\nRelationship Types:")
    for rel_type, count in stats['relation_types'].items():
        print(f"  {rel_type}: {count}")

    print("\nEntities:")
    for entity in list(kg.entities.values())[:10]:
        print(f"  - {entity.name} ({entity.type})")

    print("\nRelationships (triples):")
    for rel in kg.relationships[:10]:
        print(f"  - {rel.to_triple()}")

    # Visualizations
    visualizer = KnowledgeGraphVisualizer()

    print("\n" + "=" * 50)
    print("GraphViz DOT Format:")
    print("=" * 50)
    print(visualizer.to_graphviz_dot(kg))

    print("\n" + "=" * 50)
    print("JSON Export:")
    print("=" * 50)
    print(json.dumps(kg.to_dict(), indent=2)[:500] + "...")


if __name__ == "__main__":
    asyncio.run(main())
