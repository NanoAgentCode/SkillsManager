---
name: backend-log-contract-trace
description: Use when tracing backend failures from logs through routes, DTO/VO fields, services, MyBatis/SQL, database constraints, and downstream contracts, or verifying that a related fix remains in current files. Returns a concrete trace and verification evidence.
---

# Backend Log Contract Trace

## Overview

Use this skill to turn backend logs into a verified code-and-contract trace. The goal is to answer from the current repository, not memory: identify the real endpoint, method, DTO/VO, entity, mapper XML, SQL, downstream call, and database constraint involved.

## Workflow

1. Capture the exact failure signal.
   - Preserve the log timestamp, request path, HTTP method, exception class, stack frames, SQL error code, parameter values, trace ID, and response body when present.
   - If the user asks whether a fix was rolled back, treat that as a live-file verification task.
2. Re-open current files before making claims.
   - Inspect the controller/router, service, mapper interface, mapper XML, DTO/VO, entity, enum, and config files currently on disk.
   - Do not rely on previous memory of the codebase unless it has been rechecked in this turn.
3. Map the entrypoint.
   - Search by request path, controller annotation, method name, stack frame class, log message, error code, or SQL fragment.
   - Record the concrete route and method, including path variables, query parameters, body object, and validation annotations.
4. Follow the contract chain.
   - API request: parameter names, JSON field names, required/nullability rules, enum values, defaulting, and type conversions.
   - DTO/VO: serialization names, validation annotations, nested objects, response field names, and frontend/backstage naming mismatches.
   - Entity/domain object: field type, length assumptions, enum/code normalization, transient fields, and persistence annotations.
   - Service layer: transformations, cross-service payload construction, fallback behavior, and null handling.
   - Mapper interface/XML: method signature, `@Param` names, `parameterType`, `resultMap`, dynamic SQL branches, selected column aliases, update/insert columns, and collection handling.
   - SQL/database: real table and column names, column lengths, constraints, indexes, not-null/default rules, and vendor-specific errors such as Oracle `ORA-12899`.
5. Check cross-service contracts.
   - When one service calls another, compare outbound parameter names and response fields against the receiver's expected contract.
   - Pay special attention to file and model contracts such as `fileName` versus `downloadName`, code versus display name fields, and numeric/string enum drift such as `1.0` versus `1`.
6. Verify before and after edits.
   - Before editing, reopen every file you will modify and the immediate caller/callee or mapper XML that depends on it.
   - After editing, reopen the changed files from disk and re-check the exact contract points fixed.
   - When available, run focused tests or a compile/lint command. If not available, explain the static verification performed.
7. Report the trace, not just the fix.
   - Name the concrete path: route -> controller -> service -> mapper -> XML/SQL -> table/column/constraint -> downstream service.
   - State the contract mismatch, the evidence, the change made or recommended, and remaining uncertainty.

## Search Hints

Use fast repository search first:

```powershell
rg -n "request-path|ControllerName|methodName|error-code|SQL fragment" .
rg -n "MapperName|resultMap|column_name|dtoField|jsonField" .
```

For Java/Spring/MyBatis projects, check these common patterns:

- `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PathVariable`, `@RequestParam`, `@RequestBody`
- DTO/VO classes, validation annotations, Jackson/FastJSON field annotations
- service implementations and Feign/HTTP client wrappers
- mapper interfaces and matching `*Mapper.xml`
- `resultMap`, `select`, `insert`, `update`, dynamic `<if>`, `<choose>`, `<foreach>`, and SQL aliases

## Output Shape

Prefer a concise structured answer:

```text
Trace:
route -> controller -> service -> mapper -> XML SQL -> table.column/constraint -> downstream contract

Finding:
The failing contract is ...

Evidence:
- file:line ...
- log/SQL clue ...

Change:
...

Verification:
...
```

## Concrete Example Trace

Use this illustrative Java/Spring/MyBatis-style example as the target level of specificity when the user provides a backend failure log. The concrete names below are examples only; adapt the trace to the current repository and do not assume this project shape exists.

```text
Trace:
GET /externalModel/list -> ExternalModelController.list -> ModelServiceImpl.getModelDetailList -> ModelInfoMapper.selectModelDetailList -> ModelInfoMapper.xml selectModelDetailList SQL -> model_software.software_code / model_software.software_name -> frontend expects model rows keyed by software_code

Finding:
The failing contract is the mapper-to-database field contract. The list API filters and joins by model software code, but the current SQL reads or aliases the display-name column as the code field. As a result, the query returns zero rows even though the logs show a valid request and the database has matching model software records.

Evidence:
- log clue: GET /externalModel/list returns Total: 0 for a request that should include external model rows.
- controller/service clue: ExternalModelController.list delegates to ModelServiceImpl.getModelDetailList without rewriting software identity fields.
- mapper clue: ModelInfoMapper.selectModelDetailList receives the same filter object that the controller accepted, so the XML SQL owns the column-name contract.
- SQL clue: ModelInfoMapper.xml must compare/select model_software.software_code for code identity and use model_software.software_name only for display text.

Change:
Update ModelInfoMapper.xml so code comparisons, selected aliases, and resultMap fields use software_code for the model software identifier. Keep software_name mapped only to the display-name VO field. Do not rename the API parameter unless the controller, DTO, frontend caller, and mapper are changed together.

Verification:
Re-open ExternalModelController, ModelServiceImpl, ModelInfoMapper, ModelInfoMapper.xml, the request DTO/VO, and the model_software column definitions after editing. Run the focused module compile or test command when available, for example `mvn -pl zs-service/<module-name> -am -DskipTests compile`, then re-check that the SQL aliases still match the VO fields returned by GET /externalModel/list.
```
