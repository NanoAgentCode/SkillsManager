# Runtime and build configuration trace

Use for startup failures, datasource authentication errors, configuration discrepancies, or builds that update an unexpected JAR. Collect evidence read-only first; do not start the full application merely to inspect configuration, since startup can run migrations or scheduled jobs.

## Establish the execution object

Record the failing service, machine, failure timestamp, launch command/IDE configuration, working directory, selected Maven POM, and actual classpath or JAR path as available. Ask only for missing details that prevent distinguishing competing explanations; continue independent inspection meanwhile.

Compare three layers instead of treating them as interchangeable:

| Layer | Useful evidence | What it establishes |
|---|---|---|
| Source | Checkout path/revision, source resources | Intended code and defaults |
| Build | Maven source paths, `Building jar`, `target/classes`, packaged resources | What was compiled and packaged |
| Runtime | Process command, loaded property sources, debugger values | What the failing process actually used |

If compilation logs name a temporary release tree while the editor shows the main checkout, inspect the release tree first. Current process state may differ from the failed launch; an absent process cannot establish historical runtime values.

## Trace effective configuration

Follow launch -> packaged/local resources -> remote configuration -> overrides -> effective datasource. Inspect the mechanisms actually present: active profiles, explicit config locations, system properties, command-line arguments, IDE environment, and placeholders. Do not assume a universal precedence order across Spring versions and bootstrap/config-import mechanisms.

- For Nacos, verify server address, namespace, group, exact DataId and extension, profile-specific and shared configurations. Retrieve the relevant published content when authorized and accessible.
- Label repository examples, local server files, client snapshots, online published values, and runtime effective values separately. A cached or published value alone does not prove the failed process used it.
- Compare source resources, compiled resources, and the actual launched JAR. A resource named after the service is not automatically loaded merely because it is on the classpath; inspect how it is selected or imported.
- If remote retrieval fails, state the error and evidence boundary. Use credentials supplied for that service only; a configuration-center login is not a database login.
- Inspect secrets locally only as needed. Do not print access tokens, dump whole process environments, persist credentials in scripts, or add plaintext-password startup logs. Report password match/mismatch or length without its value unless the user specifically requests the value in the authorized context.

Use runtime property-source inspection or a debugger at datasource initialization when static evidence cannot resolve overrides. Record the effective URL and username and compare the password privately; do not infer runtime values from an unrelated running service.

## Database authentication branch

An error such as Oracle `ORA-01017` establishes that the contacted database rejected the submitted credentials; it does not identify which configured values were submitted.

When a database client succeeds, compare host/resolved endpoint, port, SID versus service name, username, password, connection role, and authentication mode with the application. Inspect address placeholders as well as explicit datasource overrides. Do not reset a password or publish a template password merely because two files differ. An old JDBC driver is a hypothesis only after connection/configuration differences have been checked.

In the incident behind this workflow, the user confirmed that incorrect application configuration also caused ORA-01017 despite a successful client login. Preserve that confirmed case conclusion. For a new incident, successful client login alone does not establish the same cause: first identify the failing artifact and compare its effective configuration with the successful connection.

Keep login checks limited to the confirmed account and endpoint; do not try a list of guessed passwords. Reuse the user's confirmed successful client test where possible.

## Maven output branch

By default a module writes to its own `target`; inspect effective build/plugin output settings if overridden. Determine the selected POM from command arguments, working directory, IDE Maven configuration, and build logs.

- `finalName` controls the basename, not which checkout is built.
- Spring Boot `repackage` replaces the current build's ordinary artifact with an executable archive; it does not copy it into another checkout.
- Date-based names leave differently named older JARs alongside new ones. `clean` removes the selected project's build directory, not another project's stale artifacts.
- Fix the build selector before changing output directories. Prefer an explicit POM path or repair the existing launcher; add a small script only when a reusable entrypoint is needed. Preserve naming and committed-source release boundaries unless the user requests changing them.

Example commands with placeholder paths:

```powershell
# PowerShell; resolve an existing workspace POM explicitly.
$pomPath = 'D:\example\workspace\backend\pom.xml'
mvn -f $pomPath -pl services/example-service -am package
```

```sh
# Portable shell.
mvn -f /example/workspace/backend/pom.xml -pl services/example-service -am package
```

When building a reusable PowerShell launcher, resolve the POM relative to `$PSScriptRoot` and propagate Maven failures. Validate it from a different current directory so the original path-selection failure cannot recur silently.

## Verification and reporting

After an authorized fix, verify the output path, artifact timestamp/content, and embedded configuration without exposing secrets. Then validate startup and connection behavior when authorized, accounting for startup side effects. Report untested runtime recovery explicitly.

Use a compact evidence table: observation, source/path/time, established fact, remaining uncertainty. Name the demonstrated cause separately for each symptom: a wrong build tree can explain the wrong output location while the authentication failure remains unconfirmed.

### Acceptance scenarios

Review these decisions after editing this workflow; they are behavioral review cases, not executed integration tests:

| Input evidence | Expected decision |
|---|---|
| ORA-01017 and a successful client login; application configuration confirmed incorrect, failing artifact unknown | Record incorrect application configuration as the confirmed cause; identify the failing artifact and effective configuration source to locate the mismatch before changing values |
| New incident with ORA-01017 and successful client login, but no confirmed cause | Prioritize effective connection configuration comparison; obtain launch identity and do not assume the previous incident's cause or reset credentials |
| Source uses config port A, compiled resources use B, online A has valid credentials | Verify the failing classpath/JAR and configuration source; do not claim A was used or B caused authentication failure |
| Maven logs name a release copy; user wants the main checkout's target updated | Correct selected POM/build entrypoint, preserve JAR naming, verify output from another working directory |
| New JAR builds and embeds expected config, but has not been launched | Report build/config verification success and runtime recovery unverified |
| Request fails on SQL field mapping after startup succeeds | Follow the main skill's request/contract branch; avoid unrelated build/config investigation |
