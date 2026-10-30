---
name: website-rebuild
description: Use when reconstructing, studying, or offline-archiving an authorized existing website from a URL, including WebGL and animation recovery with source tracing and parity checks. Excludes greenfield design and access-control bypass.
---

# Website Rebuild

Reconstruct an authorized public website as a reproducible engineering project. Treat the captured site and its client-delivered code as evidence, preserve traceability, and close the work with verification gates instead of visual guesswork.

This repository adapts the upstream `website-rebuild` v0.2.3 methodology for the Skills Manager layout. The bundled code is MIT-licensed; third-party website content, media, fonts, trademarks, and data retain their own rights.

## Preconditions And Boundaries

- Require Node.js 22 or newer, `npx`, and a local Chrome or Chromium before running the bundled browser tooling.
- Work only on sites the user owns, is authorized to reproduce, or may lawfully study from anonymous public access.
- Do not bypass authentication, paywalls, CAPTCHAs, signed-access controls, or technical restrictions.
- Inspect the target site's terms, `robots.txt`, and other published policy signals before crawling. If their meaning or the user's authority is material and unclear, present the evidence and ask the user before collecting more than minimal reconnaissance data.
- Keep crawling low-rate and limited to the confirmed scope. Do not submit transactions, forms, or other state-changing actions unless separately authorized.
- Default to a private repository, `noindex`, no public deployment, and no redistribution. Public deployment requires an explicit user decision after the asset-rights review described in [legal-and-deploy.md](references/legal-and-deploy.md).
- Never treat this skill as legal advice. Record facts and uncertainty; the user owns publication and redistribution decisions.

## Establish Scope Before Collection

Read [scope-and-fingerprint.md](references/scope-and-fingerprint.md) and perform only the minimal Step 0 reconnaissance needed to classify the target:

- **A:** client-delivered behavior and static assets are available; the standard pipeline applies.
- **B:** the pipeline applies with platform or runtime-data handling, such as Shopify, SSG payloads, or third-party asset hosts.
- **C:** the behavior source is not delivered to the client, such as server-only React components; explain the limitation instead of inventing an equivalent implementation.
- **D:** the requested behavior depends primarily on server state, private APIs, inventory, personalization, or experiments; do not claim a deterministic static reconstruction.
- **X:** the original is gone or materially replaced; request an authorized archive snapshot or another target.

For A or B, read [recon-and-rating.md](references/recon-and-rating.md), report the evidence, estimate the major difficulty dimensions, and confirm both the page scope and one endpoint:

- **L1 — Mirror archive:** stop after a verified offline mirror.
- **L2 — Engineered rebuild:** deliver a traceable, deployable reconstruction with parity gates and rights review.
- **L3 — Readable source:** after L2 is green, derive self-contained, human-readable source without weakening existing gates.

Lower levels are prefixes of higher levels. Do not start collection beyond the confirmed scope or endpoint.

## Invariants

1. Keep `mirror/` immutable. Apply localization and compatibility rewrites in a generated site or serving layer.
2. Use captured HTML, CSS, assets, bundles, and runtime observations as evidence. Do not tune behavior by eye when an implementation fact can be recovered.
3. Do not invent compensating CSS, JavaScript, animation, or content. Preserve source quirks when they affect parity.
4. Register every intentional difference with the source behavior, local behavior, reason, and reconsideration condition.
5. Give ported code a stable source coordinate, such as the beautified bundle path and line interval or the original module identifier.
6. Keep producers separate from verifiers. A verification gate must not import the transformation it audits.
7. Store generated artifacts under `output/website-rebuild/<project>/` unless the user supplies another project directory.

## Workflow

### 1. Mirror And Prove The Mirror

Read [mirroring.md](references/mirroring.md) before collection.

- Capture through the BFS mirror, browser network recording, runtime/static reference discovery, and closure checking appropriate to the site.
- Maintain one manifest with URL, local path, status, content type, size, and SHA-256 evidence.
- Run `scripts/verify-mirror.mjs` before downstream rendering checks. A successful HTTP status alone does not prove that the response is the intended asset.
- Serve through `scripts/serve.mjs`, then verify zero unexpected 404 responses, console errors, failed requests, or unregistered external requests.

Passing this stage completes L1.

### 2. Build The Reverse-Engineering Coordinate System

Read [reverse-engineering.md](references/reverse-engineering.md).

- Identify whether each bundle is flat, module-container based, scope-hoisted, or split across chunks before selecting a slicer or module mapper.
- Beautify with the pinned tool only when needed and keep `_pretty/` stable after creating source coordinates.
- Complete `docs/engine-notes.md` from [engine-notes.md](assets/templates/engine-notes.md) before porting behavior.
- Create `REBUILD_PLAN.md` from [rebuild-plan.md](assets/templates/rebuild-plan.md), including the manifest gaps, architecture evidence, milestones, quirks, and intentional-difference register.

### 3. Port In Dependency Order

Read [porting-discipline.md](references/porting-discipline.md).

- Start with one thin end-to-end vertical slice, then expand by dependency order.
- Prefer deterministic extraction or byte slicing over retyping minified code, shader text, constants, or baked data.
- Record source coordinates in each derived file.
- Close each milestone with a cold-start run and the relevant CLEAN, route, payload, numeric, or rendering gate.

Load only the references selected by reconnaissance:

| Finding | Reference |
|---|---|
| Any DOM shell | [dom-shell-strategies.md](references/dom-shell-strategies.md) |
| WebGL, Canvas, three.js, or GLSL | [webgl-scenes.md](references/webgl-scenes.md) |
| GSAP, baked timelines, CSS-variable animation, or input state machines | [animation-recovery.md](references/animation-recovery.md) |
| GLB timelines or private binary formats | [binary-formats.md](references/binary-formats.md) |
| Shopify platform behavior | [shopify-platform.md](references/shopify-platform.md) |
| Large media or licensed fonts | [asset-management.md](references/asset-management.md) |
| Headless/runtime anomalies | [environment-traps.md](references/environment-traps.md) |

### 4. Select And Calibrate Verification Gates

Read [verification-gates.md](references/verification-gates.md) and, for live animation or nondeterminism, [determinism.md](references/determinism.md).

- Establish byte or structural gates for SSR, static DOM, payloads, and routing where applicable.
- For live WebGL, video, random phases, or animation, measure each side's self-variance before interpreting cross-side residuals.
- Verify the captured frame is non-empty and that test cases, routes, scroll positions, and states are genuinely distinct.
- Use `scripts/sweep-routes.mjs` for breadth and focused probes or pixel walks for depth.
- Keep CLEAN and zero-external-request checks as baseline gates throughout.
- Treat unclassified residuals, stale generated output, unmeasured coverage, and silent tool degradation as failures.

The tool catalog, expected inputs, and maturity notes are in [scripts/README.md](scripts/README.md). Copy the required scripts into the rebuild project when the project must retain its own executable gates.

### 5. Close L2

- Perform a cold inventory against the bundle/module census; runtime tests alone cannot detect an entirely omitted subsystem.
- Verify every intentional difference is registered and every manifest gap is closed or explicitly classified.
- Read [legal-and-deploy.md](references/legal-and-deploy.md), complete the per-asset provenance and license evidence, scan for third-party identifiers, and present publication options to the user.
- Unless the user explicitly approves publication, retain the private, `noindex`, non-deployed default.

### 6. Derive Readable Source For L3

Read [readable-source.md](references/readable-source.md) only after all L2 gates are green.

- Preserve `mirror/` and `port/`; derive `src/` separately.
- For module containers, name and extract modules using evidence. Preserve lazy `require` semantics and module identifier types.
- For scope-hoisted output, prefer byte-preserving slices and prove exact reassembly.
- Use parser-backed tooling from `tools/` only at this stage. Earlier scripts and gates remain zero-dependency.
- Reuse all L2 gates without relaxing tolerance, then add symbol/module mapping, freshness, and standalone-copy checks.
- Do not merge algorithms, deduplicate behavior, or fix apparent source bugs unless the user explicitly starts a separate derivative project. See [beyond-the-rebuild.md](references/beyond-the-rebuild.md).

## Windows Entrypoint

From the Skills Manager repository root, resolve the skill once and pass its absolute script paths to Node:

```powershell
$SkillRoot = (Resolve-Path ".\skills\engineering-operations\website-rebuild").Path
node "$SkillRoot\scripts\fingerprint.mjs" --help
node "$SkillRoot\scripts\verify-zerodep.mjs"
```

Do not assume POSIX utilities are installed on Windows. Prefer the bundled Node equivalents. Before any command that launches Chrome, verify the target URL, output directory, port allocation, and whether the action performs downloads; review [environment-traps.md](references/environment-traps.md) if a run hangs or leaves unusual browser state.

## Deliverables

At the selected endpoint, report:

- confirmed scope and A/B/C/D/X classification;
- capture manifest and unresolved or registered external dependencies;
- `REBUILD_PLAN.md` plus `docs/engine-notes.md` for L2 or L3;
- gate commands, measured coverage, outputs, and remaining classified differences;
- asset-rights evidence and the user's deployment decision for L2 or L3;
- a self-contained `src/` plus unchanged verification tolerances for L3.

The full upstream workflow is retained in [workflow.md](references/workflow.md) for uncommon branches and historical rationale. Its embedded commands and policy opinions are reference material; this adapted `SKILL.md` controls execution in this repository.
