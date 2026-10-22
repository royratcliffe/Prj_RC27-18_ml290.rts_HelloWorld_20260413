# CODESYS Safety SIL2 – IEC Programming Guidelines (English summary)

An unofficial English **summary** of the German user manual
*[H2] CODESYS Safety SIL2 – IEC Programming Guidelines* (V8.0, © 3S-Smart Software Solutions GmbH).
It is not a translation and does not replace the original. For certification work, always check the
German source. The `§H2-x.y` IDs refer to the numbered safety requirements in the original.

---

## 1. Introduction

- **Audience:** application developers who program safety controllers, and OEMs who supply safe
  function blocks. Assumes IEC 61131-3/CODESYS knowledge and a basic grasp of IEC 61508, EN 13849 and
  EN 62061.
- **Content:** mandatory safety requirements plus programming recommendations that simplify
  certification. It is based on PLCopen Safety TC5, with a few deviations and stricter rules (see §7).
- **Scope:** the level classification (chapter 4) assumes EN 13849 and/or EN 62061. Projects under other
  standards need their own guidelines, but should still follow the chapter 5 rules.
- **§H2-1.1:** the safety requirements listed in the appendix are **always mandatory**, regardless of
  standard or level.

**Key terms:** *Safety mode* (normal mode after start-up; required for running safety applications) vs.
*Debug mode* (entered explicitly for download/debug; not safe). *SAFE data types* (`SAFEBOOL`, etc.)
behave like their standard types but mark safe data. *EVL* = exchange variable list in non-safe memory.
*Non-Safe PRG* = a program that may contain uncertified code and runs without interfering with safety code.
*Closed-circuit principle*: logical TRUE = operating, all-FALSE = safe state. *LVL/FVL* = limited/full
variability language.

## 2. Product overview

- CODESYS is a general-purpose tool. Some of its features are not approved for safety use, and the
  controller vendor may restrict them further.
- **§H2-2.1:** online monitoring values come over a non-safe channel, so they are **not safe**.
- **Required compiler settings:** use the released compiler version from the SIL2 setup; turn
  *Replace constants* **on**; set warnings > 0; turn *Allow Unicode identifiers* **off**. Enable all
  warnings, and justify any you disable.
- **§H2-2.2:** the Safety page log is CRC-protected, so it detects corruption. It does **not** guarantee
  completeness, because entries may be lost if the log buffer overflows.

## 3. Standards

- EN 13849/EN 62061 separate **LVL** (graphical IEC languages such as FBD/LD) from **FVL** (ST, C,
  assembler, IL). A restricted ST subset can count as LVL. Software that uses FVLs falls under IEC 61508.
- PL→SIL mapping: a = none, b = SIL1, c = SIL1, d = SIL2, e = SIL3.
- **§H2-3.1:** a safety application must be validated/certified to the applicable standard. Every library
  it uses must be validated per §H2-4.5. LVL-only code needs a functional test. FVL parts need full
  IEC 61508 module tests.
- **§H2-3.2:** code reviews must be manual. Compiler and SIL2-extension warnings only help; they do not
  replace review rules.
- **§H2-3.3:** archive the accepted version. Copy the **identical binary image** to every machine. You can
  compare the GUIDs on the Safety page as a cross-check.

## 4. Structuring (certification levels)

| Level | Languages | Typical certification | Notes |
|---|---|---|---|
| **Basic** | LVL (FBD, LD, restricted ST) | EN 62061 / EN 13849 | Pre-certified blocks with simple interconnections. Tested in the machine integration test. No module tests needed for moderate complexity. |
| **Extended** | Same as Basic | EN 62061 | More interconnection freedom, so more certification effort. Usually shipped as libraries with `SIL2 = TRUE`. |
| **System** | Any IEC 61508-suitable language (incl. ST, C, external compiler) | IEC 61508 | Libraries must also have `SIL2 = TRUE`. |

- **§H2-4.1 / §H2-4.2 – dual execution:** if the controller vendor requires it, run safe code twice.
  Each run needs separate static/temporary data **and** separate I/O images, so the driver can compare
  the results. Recommendation: put safe parts in FBs and instantiate them twice.
- **§H2-4.3:** all software to be certified needs code reviews.
- **§H2-4.4:** safety code must compile with **zero warnings**.
- **§H2-4.5 – libraries:** use certified libraries as described in their safety manual. In the
  application, use only libraries with `SIL2 = TRUE`. Libraries with `SIL2 = FALSE` may only be used by
  non-safely connected I/O drivers (normally vendor code). Libraries without the property may only be
  used indirectly, through other certified libraries.

## 5. Programming rules

- **§H2-5.1:** only the languages in this chapter are allowed. Any other language needs separate proof
  that its compiler is suitable.
- The original gives a table per language. An "X" marks the levels (Basic / Extended / System) where a
  rule applies. The summary below lists the restrictions; the levels they apply to are in brackets
  (B = Basic, E = Extended, S = System).

### 5.1 General

- **Naming:** safe FB inputs/outputs and safe locals must start with `S_` (B, E). Hungarian prefixes are
  mandatory in Basic: `x` BOOL, `by` BYTE, `w` WORD, `dw` DWORD, `lw` LWORD, `si/usi`, `i/ui`,
  `di/udi`, `li/uli`, `r` REAL, `lr` LREAL.
- **Calls:** never call an FB instance more than once per cycle (B, E, S). In Basic, call it every cycle.
- **Declarations:** no `VAR_IN_OUT` (B, E); no globals (B); no `VAR_EXTERNAL` at FB level (E);
  no `RETAIN` (B, E).
- **Data types (§H2-5.2):** floating point is allowed in B/E only if the controller vendor explicitly
  permits it. In System level the developer owns the risk assessment. Other type rules:
  - Safe data must use SAFE types (B, E).
  - In Basic, variables of numeric or time types are not allowed; constants are.
  - `STRING` and `ANY_*` are not allowed (B, E).
  - Untyped constants are not allowed (B, E).
- **Structured types:** no arrays (B); arrays only with explicit range checks (E); no structs as an
  interface between two systems (B); only naturally aligned structs for exchange (E); no arithmetic on
  enums (B, E); no pointers or references (B, E). **§H2-5.13:** POUs that use non-aligned structs need a
  full module test.
- **Tasks (§H2-5.3, §H2-5.4):**
  - An I/O driver instance (device or fieldbus) may be used from **one task only**, and that task
    triggers the bus cycle, unless the driver vendor allows otherwise.
  - Map each I/O channel to only one variable; no partial or multiple mapping of bits/words.
  - Every task needs a watchdog (cyclic: B, E; event/freewheeling: B), with watchdog time ≤ cycle time
    and sensitivity ≤ 1.
  - Event and freewheeling tasks need a deterministic maximum cycle time.
  - In Basic, no global variable may be shared between tasks.
- **Libraries (§H2-5.5, §H2-5.6):**
  - Only libraries with the BOOL property `SIL2` may be used directly. Using one without it causes a
    compile warning; that is tolerable in debug mode only.
  - Forbidden firmware functions work in debug mode but raise an exception in safety mode.
  - A library counts as validated only if it was verified on the target hardware with the same compiler
    settings. Using the same device description ensures this.
- **Documentation:** every POU needs a visible functional description (B, E, S). Libraries need author,
  creation date, release date, version and history in their project information (B, E, S). Code must be
  adequately commented (B, E).
- **Expressions (§H2-5.14):**
  - No implicit type conversions (B, E). Exception: `AND`/`OR` converting BOOL to SAFEBOOL.
  - No explicit conversions in Basic, except `SAFE*_TO_*`.
  - `AND_THEN`/`OR_ELSE` are not allowed in Basic. Elsewhere, POUs that use them need a full module test.
- **Pragmas (§H2-5.15):** POUs with pragmas (including pragmas inside structs they use) need a full
  module test. Basic forbids pragmas, except `{attribute 'location':='16#800'}`.
- **Object orientation:**
  - No `EXTENDS` in Basic.
  - Never call `FB_Init`/`FB_Exit` of the base class explicitly (B, E, S).
  - `FB_Init`/`FB_Exit` must tolerate being called twice (B, E, S).

### 5.2 Structured Text (ST)

- **§H2-5.7:** ST counts as LVL only if the Basic/Extended rules are followed.
- **Control flow (B, E):**
  - `FOR` loops need a constant iteration count.
  - No `WHILE`/`REPEAT`.
  - No `CONTINUE`/`EXIT`.
  - No conditional or multiple `RETURN`.
- **Expressions (B, E):**
  - Nesting depth must not exceed 1, and an expression may have at most 5 operators/operands.
  - Use explicit parentheses instead of relying on precedence.
  - Constants must be typed (`UINT#5`, not `5`).
  - Only one assignment per statement.
  - System level: nested expressions must not rely on implicit casts, because intermediates are kept at
    register width.
- **Operators (B, E, S):** an `AND`/`OR` producing SAFEBOOL may have only one SAFEBOOL output. `AND`
  needs at least one SAFEBOOL input. `OR` must not take BOOL inputs.
- **Math (B, E, S):** `MOD, EXPT`, trig, `LOG`, `SQRT` only if the vendor allows them. Shifts must not
  exceed the data width.

### 5.3–5.5 FBD and LD

- **Control flow:** no jumps (B); no backward jumps (E); no conditional or multiple returns (B); no
  branches (B).
- **Operators:** the same SAFEBOOL `AND`/`OR` rules as ST apply (B, E, S). In Basic, the following are
  not allowed:
  - `XOR/NOT`
  - `ADD/MUL/SUB/DIV`
  - `MIN/MAX`
  - comparisons
  - `SEL/MUX/LIMIT`
  - `MOVE`
  - `SR/RS`
  - edge detection
- **Functions:** trig etc. only if the vendor allows them (B, E, S). Shifts are not allowed (B, E).
- **LD (B):** no FB calls, no normally-closed contacts, no negated coils.
- **FBD (B):** no negated inputs/outputs.

### 5.6 CFC

- CFC is not part of IEC 61131-3. Its free block placement makes review harder, so it is allowed only
  from Extended level, and **always** with a full module test (**§H2-5.8**).
- **§H2-5.9:** inputs/outputs only on the page border (E).
- **§H2-5.10:** no jumps or returns (E).
- Operator/function rules are similar to ST. Shifts are not allowed in E.

### 5.7 UML Statechart

- Execution semantics in CODESYS:
  - The do-action runs every cycle in which the state is active.
  - A *trigger* transition is evaluated in one cycle and takes effect in the next.
  - A *triggerless* transition takes effect in the same cycle.
  - Reaching the end state restarts the chart.
- Because of this, diagrams alone do not show the exact timing.
- **§H2-5.11:** every state transition must be tested.
- **§H2-5.12:** the internal `ReInit`/`Abort` inputs must not be used by the application.
- Basic forbids statecharts entirely. Extended forbids exception transitions, choices and fork/join.

## 6. Signal processing

- **Sources of safe data:** a device that already exposes SAFE types, or a safety protocol that verifies
  non-safe data and produces safe data.
- **§H2-6.1:** compute safe outputs **only** from safe inputs.
- **§H2-6.2:** if a device declares I/Os safe but exposes them as standard types, you may cast them to or
  from SAFE types. Review these casts against the real I/O assignment.
- **§H2-6.3 – closed-circuit principle:** FALSE/0 must always mean the safe state. Activation inputs
  default to 0 (B, E, S). With all inputs at 0, the block must not be operating (B, E, S). Write every
  output every cycle (B, E).
- **Non-safe code**, if the controller supports it:
  - *Compound Safety* – separate safety and standard applications, so the standard one can change
    without re-acceptance.
  - *Non-Safe PRGs* – untick "Safe PRG" in the properties. They have no write access to safe data and
    exchange data through their `VAR_INPUT`/`VAR_OUTPUT` or an EVL.
- **Safe FB interface (PLCopen):** `Activate`, `S_…` inputs, `S_StartReset`, `S_AutoReset`, `Reset`
  (rising edge), `Ready`, `S_…` outputs, `Error`, `DiagCode` (first error; updated in the same cycle as
  the state change).
  - In B/E every safe FB must have `Activate`, `Ready`, `Error` and `DiagCode`.
  - A `Reset` input is required if the FB can stay in a state without a timeout, unless that is an
    unrecoverable safe state.
  - Standard parameter names must keep their standard meaning (B, E, S).
- **Non-safe I/O:** no special rules apart from the single-task rule. Never derive safe outputs from
  non-safe inputs.

### 6.6 CANopen Safety (EN 50325-5)

- **§H2-6.4:** the developer must review the **whole** bus configuration:
  - PDO and SRDO mappings are correct and do not overlap.
  - COB-IDs and node IDs do not overlap.
  - All nodes use the same baud rate.
- **§H2-6.5:** if SRDO/PDO traffic bypasses the master, the developer must handle the related faults.
  Alternatively, the master can monitor the TxSRDOs.
- **§H2-6.6:** arrays/structs in slave I/O mapping are not allowed. Channels must not be partially
  mapped (bit channels are the exception).
- **§H2-6.7:** always evaluate each slave's safe diagnostics (`S_xActive`, `S_eError`). Pure actuators
  must be monitored by other means.
- **§H2-6.8:** device-tree status and monitoring are **not** safe. Use them for troubleshooting only.
- **§H2-6.9:** the non-safe master could reconfigure a slave at runtime. Mitigate with statically
  configured slaves, sensor checks within the process safety time, or restart interlocks.
- **§H2-6.10:** demo mode is disabled. Without a licence, the CANopen and CANopen Safety buses do not
  start.
- **§H2-6.11:** the Global Failsafe Command is sent over a non-safe channel. Do not rely on it.

### 6.7 FSoEBase (Safety over EtherCAT, ETG.5100)

- The library implements the protocol in the safe context. The PDU transport is non-safe and must be
  provided by the user.
- **§H2-6.15:** the FSoE conformance test must have been run on the target device.
- **§H2-6.12:** review the configuration:
  - FSoE addresses and connection IDs are unique.
  - Application parameters, communication parameters and payload layout match between master and slave.
  - The slave checks the parameters before it first uses any data.
- **§H2-6.13:** call the `Input` method at least **twice per watchdog period**.
- **§H2-6.14:** demo mode is disabled. Without a licence, communication does not start.
- **§H2-6.16 – telegram limits:** 8 or 16 safety data bits; at most 24 virtual bits; standard bits must
  be between 16 and 12144.
- **§H2-6.17:** after a detected fault and safe state, allow at most **one reset per 5 operating hours**.

## 7. Appendix – deviations from PLCopen TC5

TC5 targets SIL3 with strictly separated safety and functional processors. For SIL2 with mixed code,
CODESYS Safety SIL2 changes the following:

- Multiple tasks are allowed, and non-safe code may interrupt safe code if it is free of side effects.
- `WORD` is allowed.
- `REAL` in B/E needs vendor permission.
- `OR` is relaxed in Basic, so non-safe I/O can be wired.
- `MOVE` is forbidden only in Basic.
- `MOD`/`EXPT` are grouped with the math functions. All math functions are forbidden by default and
  can be permitted by the vendor.

**References:** IEC 61131-3, IEC 61508 (Ed. 2), EN ISO 13849, EN 62061, PLCopen TC5 Safety Part 1,
ETG.5100 (FSoE) v1.2.0 plus errata.
