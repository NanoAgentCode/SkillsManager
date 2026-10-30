---
name: technical-cognition-framework
description: Use when systematically learning or comparing a technology through connected definitions, concepts, mechanisms, implementation methods, scenarios, boundaries, and LLM/agent relationships. Produces an evidence-based Chinese framework; scales down for narrow questions.
---

# Technical Cognition Framework

## Overview

Turn a technology topic into a connected, decision-useful mental model instead of a flat glossary. Link definition, concepts, motivation, methods, scenarios, boundaries, and AI-system relationships into one causal framework.

## Workflow

### 1. Resolve the topic and learning goal

1. Normalize the topic name and expand important acronyms on first use.
2. Disambiguate overloaded terms before explaining them. Infer the intended meaning from context when safe; otherwise state the selected meaning and briefly name the alternatives.
3. Identify the user's goal: rapid orientation, systematic learning, architecture selection, implementation planning, or comparison.
4. Match depth to the request. If the user only names a topic or supplies a question cluster, default to the full framework.
5. Produce every final deliverable in Simplified Chinese. Translate headings, explanations, tables, conclusions, and uncertainty notes into Chinese. Preserve code identifiers, standard names, product names, and other proper nouns; for important English technical terms, use `中文术语（English term）` on first mention. Use another output language only when the user explicitly overrides this rule.

For `Ontology`, distinguish at least knowledge-representation/semantic-web ontology, philosophical ontology, and the Ontology blockchain project. Default to knowledge representation when the surrounding questions mention concepts, construction, knowledge graphs, LLMs, or agents.

### 2. Build the question map

For a full framework, read [references/framework-template.md](references/framework-template.md) and cover these linked questions:

1. What is it, and what is outside its boundary?
2. What are its core concepts, and how do they relate?
3. What problem makes it necessary, and when is it worth the cost?
4. What construction or implementation methods exist, and how are they selected?
5. What application scenarios fit, and which do not?
6. Which adjacent concepts are easily confused with it?
7. How does it relate to LLMs and agents in both directions?

Do not answer the seven questions as independent encyclopedia entries. Establish the dependency chain:

```text
problem -> definition and boundary -> concepts and mechanisms -> methods -> scenarios
        -> comparison with alternatives -> LLM/Agent integration -> adoption decision
```

If the user asks only one or two questions, answer those directly and include only the surrounding concepts needed to prevent misunderstanding.

### 3. Establish an evidence base

1. Separate stable foundations from fast-changing ecosystem claims.
2. Prefer standards and specifications, original papers, official project documentation, and authoritative academic material. Use secondary summaries only for orientation or triangulation.
3. Verify current products, model capabilities, benchmarks, standards status, and ecosystem adoption with live sources when browsing is available.
4. Place citations near the claims they support. Label deductions as analysis rather than sourced fact.
5. State uncertainty or the lack of live verification instead of inventing precision.
6. Never treat an implementation, vendor product, serialization, or popular library as the definition of the underlying concept.

### 4. Construct the concept skeleton

Start with a one-sentence mental model, then define the minimum concept set needed to explain how the technology works. For each concept, give:

- a precise role;
- its relationship to other concepts;
- one concrete example when useful;
- the layer it belongs to, such as conceptual, representation, implementation, runtime, or governance.

Use a compact concept map or table when three or more relationships would be harder to follow in prose. Avoid listing terms with no relationships.

### 5. Explain motivation and tradeoffs

Derive benefits from the original problem instead of listing generic advantages. Cover:

- the failure mode without the technology;
- the mechanism by which the technology helps;
- the measurable or observable benefit;
- the added cost, rigidity, maintenance, or operational risk;
- the threshold at which a simpler alternative is sufficient.

### 6. Compare construction methods

Present methods as lifecycle choices, not as an unranked name list. For each method or method family, compare:

- suitable context and prerequisites;
- main steps and deliverables;
- degree of formality and automation;
- validation or quality gates;
- collaboration, reuse, and evolution support;
- cost and failure modes.

Translate named methodologies into a practical loop such as scope -> requirements -> reuse -> modeling -> implementation -> verification -> release -> governance. Recommend a method only after stating the selection criteria.

### 7. Test scenarios and boundaries

Describe scenarios with the pattern `problem -> mechanism -> benefit -> constraint`. Include at least one poor-fit or overengineering case. A scenario is not evidence of suitability unless the mechanism is explicit.

### 8. Distinguish adjacent concepts

Use the same comparison axes for every concept: purpose, abstraction level, semantic strength, representation, inference or validation capability, runtime role, and typical output. State whether two concepts are alternatives, layers, complements, or one possible implementation of the other.

### 9. Analyze the LLM and Agent relationship

Cover both directions when they are meaningful:

- **Technology -> LLM/Agent:** grounding, structured context, tool or data contracts, planning, memory, retrieval, validation, interoperability, or policy support.
- **LLM/Agent -> Technology:** extraction, construction, mapping, enrichment, migration, querying, maintenance, or user interaction.
- **Division of responsibility:** identify what remains probabilistic and what should be enforced by deterministic validators, databases, reasoners, type systems, or human review.
- **Risks:** hallucination, semantic drift, stale knowledge, provenance loss, evaluation gaps, and operational complexity.

Do not manufacture a strong relationship when the connection is indirect. Explain the absence of a meaningful relationship when appropriate.

For an Ontology request, read [references/ontology-example.md](references/ontology-example.md) completely. Use it as a worked reference and accuracy guardrail, then adapt the answer to the user's depth and goal rather than copying it verbatim.

### 10. Synthesize the framework

End with a compact synthesis that answers:

- What is the minimum correct mental model?
- What decision does this framework enable?
- What should the user learn, model, or prototype next?

## Default Chinese Output

Use this order for a full response:

1. **30-second mental model**
2. **Definition and boundary**
3. **Core concept map**
4. **Why it exists and when it is worth using**
5. **Construction or implementation methods**
6. **Application scenarios and poor-fit cases**
7. **Commonly confused concepts**
8. **Relationship with LLMs and agents**
9. **Adoption checklist or learning path**
10. **Sources and uncertainty notes**

Compress or expand sections according to the request. Prefer one strong comparison table over several repetitive lists.

Write all section titles and explanatory prose in Simplified Chinese. Source titles and URLs may retain their original language in the references section.

## Quality Gate

Before returning the answer, verify that:

- the definition excludes at least one nearby concept;
- the concept section explains relationships, not just vocabulary;
- every claimed benefit is tied to a mechanism;
- construction methods include deliverables and validation;
- scenarios include constraints and a non-fit case;
- comparisons use consistent axes;
- LLM/Agent claims separate generation from deterministic verification;
- current claims are sourced or explicitly marked as unverified;
- the conclusion helps the user decide or act.

## Example Requests

- "用 Ontology 为例，帮我建立完整的技术认知框架。"
- "系统解释 RAG：它解决什么问题、核心组件如何协作、有哪些实现路线、什么时候不该用？"
- "对比 Ontology、Knowledge Graph、Taxonomy 和数据库 Schema，并说明它们与 Agent 的关系。"
- "我准备在企业数据平台中引入语义层，请按选型模式分析收益、成本、替代方案和落地步骤。"
