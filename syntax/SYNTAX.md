# Synthex — Constructed Language Reference

Synthex is a declarative language for defining, composing, and mutating **abilities**, **parameters**, and **units** in a structured, human-readable format.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Lexical Rules](#lexical-rules)
- [Units](#units)
- [Parameters](#parameters)
- [Abilities](#abilities)
- [Alterations](#alterations)
- [Imports](#imports)
- [Full Example](#full-example)
- [Using from Python](#using-from-python)

---

## Quick Start

```
unit meter {
  symbol: "m";
  factor: 1.0;
  offset: 0.0;
}

param speed {
  type: "physical";
  physical: "velocity";
  default: 5.0;
  range: [0.0, 50.0];
  unit: meter;
}

ability dash {
  category: "move";
  desc: "rapid short-distance movement";
  desc_ru: "быстрое перемещение на короткое расстояние";
  params: [speed];
}

alter speed -> speed {
  op: "mul";
  value: 2.0;
}
```

---

## Lexical Rules

| Element    | Syntax                   | Example                       |
| ---------- | ------------------------ | ----------------------------- |
| Identifier | `[a-zA-Z][a-zA-Z0-9_-]*` | `dash`, `fire-rate`, `max_hp` |
| String     | `"..."`                  | `"move quickly"`              |
| Number     | integer or float         | `42`, `3.14`                  |
| Comment    | `# ...` (line comment)   | `# boost damage`              |

---

## Units

Units define measurement systems for parameters.

### Grammar

```
unit <name> {
  symbol: "<symbol>";
  base: <parent_unit>;      # optional — for derived units
  factor: <number>;         # multiplier from base
  offset: <number>;         # additive offset from base
}
```

### Examples

**Base units** — the foundation of the system:

```
unit meter {
  symbol: "m";
  factor: 1.0;
  offset: 0.0;
}

unit kilogram {
  symbol: "kg";
  factor: 1.0;
  offset: 0.0;
}

unit second {
  symbol: "s";
  factor: 1.0;
  offset: 0.0;
}
```

**Derived units** — built on top of base units:

```
unit newton {
  symbol: "N";
  base: kilogram;
  factor: 1.0;
  offset: 0.0;
}

unit kelvin {
  symbol: "K";
  factor: 1.0;
  offset: 0.0;
}

unit celsius {
  symbol: "°C";
  base: kelvin;
  factor: 1.0;
  offset: 273.15;
}

unit watt {
  symbol: "W";
  base: newton;
  factor: 1.0;
  offset: 0.0;
}
```

---

## Parameters

Parameters are tunable numeric values that abilities read or write.

### Grammar

```
param <name> {
  type: "<type>";
  physical: "<physical_kind>";
  default: <number>;
  range: [<min>, <max>];
  unit: <unit_name>;
  formula: "<expression>";   # optional — computed parameter
}
```

### Field Reference

| Field      | Type         | Required | Description                                                 |
| ---------- | ------------ | -------- | ----------------------------------------------------------- |
| `type`     | string       | yes      | Category: `"physical"`, `"logical"`, `"meta"`               |
| `physical` | string       | no       | Physical kind: `"force"`, `"velocity"`, `"impedance"`, etc. |
| `default`  | number       | yes      | Initial value                                               |
| `range`    | `[min, max]` | yes      | Permissible bounds                                          |
| `unit`     | identifier   | yes      | Reference to a declared unit                                |
| `formula`  | string       | no       | Expression for derived parameters                           |

### Examples

**Simple physical parameter:**

```
param strength {
  type: "physical";
  physical: "force";
  default: 10.0;
  range: [0.0, 100.0];
  unit: newton;
}
```

**Velocity parameter:**

```
param speed {
  type: "physical";
  physical: "velocity";
  default: 5.0;
  range: [0.0, 50.0];
  unit: meter;
}
```

**Derived parameter with formula:**

```
param resistance {
  type: "physical";
  physical: "impedance";
  default: 1.0;
  range: [0.0, 10.0];
  formula: "strength / speed";
}
```

**Thermal parameter:**

```
param heat_capacity {
  type: "physical";
  physical: "thermal_capacity";
  default: 4186.0;
  range: [0.0, 10000.0];
  unit: joule;
}
```

**Logical parameter (no unit):**

```
param cooldown {
  type: "logical";
  default: 1.5;
  range: [0.0, 10.0];
}
```

---

## Abilities

Abilities are verb-like actions that operate on objects.

### Grammar

```
ability <name> {
  category: "<category>";
  desc: "<english description>";
  desc_ru: "<russian description>";
  params: [<param1>, <param2>, ...];
}
```

### Field Reference

| Field      | Type           | Required | Description                                     |
| ---------- | -------------- | -------- | ----------------------------------------------- |
| `category` | string         | yes      | Grouping key (e.g. `"move"`, `"scan"`, `"cut"`) |
| `desc`     | string         | yes      | English description                             |
| `desc_ru`  | string         | no       | Russian description                             |
| `params`   | `[ident, ...]` | no       | Parameters this ability reads or modifies       |

### Examples

**Movement ability:**

```
ability push {
  category: "move";
  desc: "apply force to move the object";
  desc_ru: "приложить силу для перемещения объекта";
  params: [strength, speed];
}
```

**Scanning ability:**

```
ability scan-area {
  category: "scan";
  desc: "detect objects within range";
  desc_ru: "обнаружить объекты в пределах досягаемости";
  params: [range, resolution];
}
```

**Cutting ability:**

``
ability slice {
category: "cut";
desc: "divide the object along a plane";
desc_ru: "разделить объект вдоль плоскости";
params: [strength, precision];
}

```

**Ability with no params:**

```

ability idle {
category: "state";
desc: "remain in current state";
desc_ru: "оставаться в текущем состоянии";
}

```

---

## Alterations

Alterations modify existing parameters at runtime.

### Grammar

```

alter <source> -> <target> {
op: "<operation>";
value: <number>;
min: <number>; # optional — for clamp
max: <number>; # optional — for clamp
}

```

### Operations

| Op | Behavior | Formula |
|----|----------|---------|
| `set` | Assign a fixed value | `target = value` |
| `add` | Add to current value | `target += value` |
| `mul` | Multiply current value | `target *= value` |
| `clamp` | Bound between min/max | `target = clamp(target, min, max)` |

### Examples

**Boost strength by 50%:**

```

alter strength -> strength {
op: "mul";
value: 1.5;
}

```

**Set speed to a fixed value:**

```

alter speed -> speed {
op: "set";
value: 12.0;
}

```

**Add extra resistance:**

```

alter resistance -> resistance {
op: "add";
value: 2.5;
}

```

**Clamp health between bounds:**

```

alter health -> health {
op: "clamp";
value: 0.0;
min: 0.0;
max: 100.0;
}

```

**Chain multiple alters on the same param:**

```

alter strength -> strength {
op: "mul";
value: 2.0;
}

alter strength -> strength {
op: "add";
value: 5.0;
}

alter strength -> strength {
op: "clamp";
value: 0.0;
min: 0.0;
max: 50.0;
}

```

---

## Imports

Import definitions from another `.sx` file.

### Grammar

```

import "path/to/file.sx";

```

### Example

```

import "units/base.sx";
import "params/combat.sx";
import "abilities/movement.sx";

```

---

## Full Example

A complete Synthex program defining a combat system:

```

# ── Units ──────────────────────────────────────────────────────────────────

unit meter {
symbol: "m";
factor: 1.0;
offset: 0.0;
}

unit kilogram {
symbol: "kg";
factor: 1.0;
offset: 0.0;
}

unit second {
symbol: "s";
factor: 1.0;
offset: 0.0;
}

unit newton {
symbol: "N";
base: kilogram;
factor: 1.0;
offset: 0.0;
}

unit joule {
symbol: "J";
base: newton;
factor: 1.0;
offset: 0.0;
}

# ── Parameters ─────────────────────────────────────────────────────────────

param strength {
type: "physical";
physical: "force";
default: 10.0;
range: [0.0, 100.0];
unit: newton;
}

param speed {
type: "physical";
physical: "velocity";
default: 5.0;
range: [0.0, 50.0];
unit: meter;
}

param resistance {
type: "physical";
physical: "impedance";
default: 1.0;
range: [0.0, 10.0];
formula: "strength / speed";
}

param energy {
type: "physical";
physical: "energy";
default: 100.0;
range: [0.0, 500.0];
unit: joule;
}

param cooldown {
type: "logical";
default: 1.5;
range: [0.0, 10.0];
}

# ── Abilities ──────────────────────────────────────────────────────────────

ability touch {
category: "contact";
desc: "make physical contact with the object";
desc_ru: "вступить в физический контакт с объектом";
params: [strength, resistance];
}

ability push {
category: "move";
desc: "apply force to move the object";
desc_ru: "приложить силу для перемещения объекта";
params: [strength, speed];
}

ability shield {
category: "protect";
desc: "absorb incoming force";
desc_ru: "поглотить входящую силу";
params: [resistance, strength];
}

ability strike {
category: "attack";
desc: "deliver a focused impact";
desc_ru: "нанести точный удар";
params: [strength, energy, cooldown];
}

ability dash {
category: "move";
desc: "rapid short-distance movement";
desc_ru: "быстрое перемещение на короткое расстояние";
params: [speed, energy, cooldown];
}

# ── Alterations ────────────────────────────────────────────────────────────

# Upgrade: boost strength by 50%

alter strength -> strength {
op: "mul";
value: 1.5;
}

# Fix: set speed to a known good value

alter speed -> speed {
op: "set";
value: 12.0;
}

# Buff: add extra resistance

alter resistance -> resistance {
op: "add";
value: 2.5;
}

# Nerf: reduce energy pool

alter energy -> energy {
op: "mul";
value: 0.8;
}

# Safety: clamp cooldown to minimum

alter cooldown -> cooldown {
op: "clamp";
value: 0.0;
min: 0.5;
max: 5.0;
}

````

---

## Using from Python

```python
from syntax import execute, dump
from syntax.default import Lexer, Parser

# ── Execute a Synthex program ──────────────────────────────────────────────

source = open("combat.sx").read()
result = execute(source)

print(result["abilities"])   # dict of AbilityDecl
print(result["params"])      # dict of param dicts
print(result["units"])       # dict of UnitDecl

# ── Parse and inspect the AST ──────────────────────────────────────────────

tokens = Lexer(source).tokenize()
ast = Parser(tokens).parse()

for stmt in ast.statements:
    if hasattr(stmt, "name"):
        print(f"{type(stmt).__name__}: {stmt.name}")

# ── Pretty-print back to Synthex ───────────────────────────────────────────

print(dump(ast))

# ── Feed into an Evaluator with custom registries ──────────────────────────

from syntax.default import Evaluator

abilities = {}   # pre-existing ability registry
params = {}      # pre-existing param registry

evaluator = Evaluator(abilities, params)
result = evaluator.run(ast)
````
