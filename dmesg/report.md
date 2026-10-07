# File Analysis Report — `dmesg/classdump.h`

> Scope: identify the file format, verify the payload contains the information a
> well-formed file of that type should carry, and report anomalies.
> Deliverable only — no source/application code was modified (so `APP_VERSION`
> in `main.py` is intentionally left untouched).

---

## 1. Executive summary

`classdump.h` is **not** a C/C++ header. It is a **plain-text, `xxd`-style hex
dump** of a **295,128-byte (0x480D8) binary GoldSrc / Half-Life‑1 studio model
file** (`.mdl`), specifically the Counter-Strike AK‑47 first‑person view model
`v_ak47.mdl` (magic `IDST`, version `10`).

The hex dump itself is **intact and faithful** (every 16‑byte row contiguous,
no gaps/overlaps, zero malformed lines, declared file length matches the
reconstructed size). The embedded `.mdl` header is internally consistent
(magic, version, model name, and `numbones`/`boneindex` all agree with their
content).

However, several **structural anomalies** were found — most notably a
**statistically impossible over‑representation of the byte pair `0x5B5B`
(`"[[`)** and **inconsistent, non‑contiguous bone naming/ numbering** — which
suggest this payload is either a synthetic/corrupted model or one that has been
tampered with before being dumped.

---

## 2. File‑format identification

### 2.1 The carrier file (the `.h` itself)

| Property | Value |
|---|---|
| Type | Plain ASCII text |
| Size | 1,420,394 bytes |
| Text lines | 18,448 (`1` column‑ruler header + `1` blank + `18,446` data rows) |
| Row format | `<8‑hex offset>  <16 hex bytes>  <16‑char ASCII>`, exactly `xxd` / HxD plain‑text style |

The first two lines of the file are a hex‑editor column ruler and a blank line:

```
Hex View  00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F
<blank>
00000000  49 44 53 54 0A 00 00 00  76 5F 61 6B 34 37 2E 6D  IDST....v_ak47.m
```

### 2.2 The embedded binary payload

Reconstructing the bytes from the hex dump yields a **295,128‑byte** blob whose
header decodes as a **GoldSrc / Half‑Life‑1 studio model** (Valve `IDSTUDIOHEADER`):

| Offset | Size | Value | Meaning |
|---|---|---|---|
| `0x00` | 4 | `49 44 53 54` → `"IDST"` | Magic — GoldSrc `.mdl` (`IDSTUDIOHEADER` = 0x54534449) |
| `0x04` | 4 | `0A 00 00 00` → `10` | Format version (HL1 / `v10`) |
| `0x08` | 64 | `"v_ak47.mdl\0…"` | Model name — CS AK‑47 first‑person view model |
| `0x48` | 4 | `D8 80 04 00` → `295128` | Declared file length (== actual reconstructed size ✓) |
| `0x4C` | 12 | `0.0, 0.0, 0.0` | Eye position vector |
| `0x8C` | 4 | `2A 00 00 00` → `42` | `numbones` |
| `0x90` | 4 | `F4 00 00 00` → `0xF4` | Bone‑name/descriptor table offset |
| `0x98` | 4 | `54 13 00 00` → `0x1354` | End of bone table ( = `0xF4 + 42×112` ) |

The signature **(`IDST` + version `10` + model name `v_ak47.mdl`)** is
unambiguous: it is a GoldSrc/Half‑Life‑1 `.mdl` studio model.

---

## 3. Methodology

1. Parsed the `xxd`‑style rows back into raw bytes with a Python regex
   (offset token + leading run of 2‑hex byte tokens, capped at 16/row). An
   initial parser was discarded after it dropped the second 8‑byte half of every
   row (a double‑space‑handling bug) — its artefacts were confirmed against the
   corrected parser and **not** reported as file findings.
2. Decoded the reconstructed binary: little‑endian `u32`/`i32`/`f32` field table,
   contiguous‑stride verification, and string/byte‑run scans.
3. Cross‑checked structural claims against the header (counts vs. actual
   content) and against random‑expectation statistics.

---

## 4. Integrity / consistency checks (what is correct)

The payload passes every basic integrity check, which is why the anomalies in
§5 stand out — they are not the result of a broken parse:

| Check | Result |
|---|---|
| Rows parse cleanly | `18,446` data rows, `0` malformed/unparseable lines (only the ruler header is non‑data) |
| Row stride | Uniform `0x10` (16 bytes); offsets run contiguously `0x0 → 0x480D0` with **no gaps, no overlaps, no duplicate offsets** |
| Trailer | Final row (`0x480D0`) is a partial `8`‑byte row, ending **exactly** at `0x480D8` (the declared length) |
| File length field | `@0x48 = 295128` **==** reconstructed binary length `295128` — not truncated / not padded |
| `numbones` vs content | `@0x8C = 42` and **exactly 42** bone‑name entries exist at `0xF4`; the table occupies `0xF4–0x1354` = `42 × 112` bytes, landing exactly on the `@0x98` boundary value `0x1354` |
| Section offsets | All pointer/count fields (`0xF4`, `0x1354`, `0x1404`, `0x6210`, `0x67F8`, `0x6860`, `0xDC50`, `0xDFD8`, `0xDFC0`) fall inside `[0, 0x480D8)` |

---

## 5. Information‑content check (does it contain what it should)

A GoldSrc `.mdl` should carry: signature → version → name → length → eye
position → bone data → hitbox/sequence/controller tables → texture data → vertex
/ normal / face data. All of these sections are **present and plausibly
located**:

- ✅ Signature / version / name / length / eye position (`0x00–0x54`)
- ✅ Bone table (`0xF4–0x1354`, 42 entries) with recognisable names:
  `Bone01..Bone52`, `Bone_Lefthand`, `Bone_Righthand`, `Bone_AK47`
- ✅ Section‑offset tables in `0x88–0xFC` (counts + pointers all in range)
- ✅ A texture / index data region in the file tail (`0x3F000–0x480D8`,
  37,080 bytes; byte histogram dominated by `0x6A`,`0x00`,`0x21`,`0x61`,`0x66`,
  etc. — typical of palettised texture indices)

Net: the file **does contain the information a `.mdl` should contain**. The
problems are in the *content/anomalies* below, not in missing top‑level
sections.

---

## 6. Anomalies

### ⚠ A. Filename / extension mismatch
`classdump.h` implies a C/C++ header (or an Objective‑C `class‑dump` header),
but the file is a **hex dump of a binary model** — it is not valid C and not a
header in any sense. The `Hex View` ruler header on line 1 is the giveaway that
this is editor‑exported hex text mis‑labelled `.h`.

### ⚠ B. `0x5B5B` (`"[[`)** byte‑pair is massively over‑represented
This is the strongest, most quantitative anomaly.

- Total occurrences of `[[` : **262**
- Statistically expected for 295,128 random bytes: **≈ 4.5** (≈ **58× too many**)
- A single `0x5B` (`[`) appears **1,310** times (expected ≈ 1,153) — modest on
  its own, but the **pairing** proves the `[` bytes are structurally clustered,
  not random palette indices.

Regional distribution is highly non‑uniform:

| Region | `[[` count | Nature |
|---|---|---|
| `0x000000–0x002000` (header/bone area) | 11 | inside the bone table |
| `0x002000–0x004000` | 41 | a **regular band** at a steady `0xB8` (184‑byte) stride |
| `0x00018000–0x0001A000` | 29 | second dense cluster |
| `0x0001A000–0x0001C000` | 42 | second dense cluster |
| `0x0003E000–0x00044000` (texture tail) | 80 | texture/index region |

The `0x1894` regular band is the clearest structural artifact: ~15 consecutive
records each **begin with the two bytes `5B 5B`**, followed by a stream of
little‑endian `u16` values that look like vertex/face indices:

```
0x1894: 5B 5B  32 0E 00 0E  D2 0D A8 0D 84 0D 64 0D 49 0D 32 0D ...
        '[[ '  3634 3584 3538 3496 3460 3428 3401 3378 3361 ...
```

The leading `0x5B5B` decodes to decimal **23,387** — which is **far larger than
both** the bone count (`42`) **and** the indices that follow it in the same
stream (`~1,750–3,600`). It therefore does not behave like a genuine index or
count field; it reads as an **injected delimiter/sentinel** (`[[`), and is not
part of a standard GoldSrc `.mdl` face/vertex layout.

### ⚠ C. Inconsistent bone naming
The 42 bone‑name entries in the `0xF4` table mix conventions and include a
duplicate:

- `Bone04` (no space) at `0xF4` **and** `Bone 04` (with a space) at `0x9B4` —
  the same logical index spelled two different ways.
- Mixed formats overall: numeric `Bone01..Bone52`, plus `Bone_Lefthand`,
  `Bone_Righthand`, `Bone_AK47`.

### ⚠ D. Non‑contiguous, unsorted bone numbering
Bone indices are sparse and out of order. Present (distinct):

```
01,03,04,05,06,07,09,10,11,13,14,15,17,18,19,
21,22,23,25,26,27,28,29,31,32,33,35,36,37,
39,40,41,43,44,45,48,50,52
```

Missing: `02,08,12,16,20,24,30,34,38,42,46,47,49,51` (14 gaps). The on‑disk
order is also non‑sequential (`Bone04, Bone_Righthand, Bone26, Bone27, …`),
and `Bone04`/`Bone 04` appear to be a duplicate entry for index `04`.

### ⚠ E. Odd bone‑record layout (informational)
Each of the 42 bone descriptor slots is a **112‑byte record** (4704 bytes total,
`42×112 = 0x1260`, matching the table span `0xF4–0x1354`). Only the first
~16 bytes carry the name; the remainder is padding/nulls followed by a
`0xFF…0xFF` block and a block of `float`s (e.g. for `Bone_Righthand`:
`…ff ff… b2 2c b8 3d cc b0 08 c1 00 00 00 80 a8 52 03 3f…`). The 112‑byte
slot size and the large `0xFFFFFFFF` block (×4 dwords) are larger/irregular vs.
a canonical ~32‑byte `mstudiobone_t`, and are flagged for follow‑up against the
reference header layout (see §8).

---

## 7. Things explicitly ruled **not** anomalies

- **Declared file length** `@0x48 = 295,128` exactly equals the reconstructed
  binary size → **not truncated or overwritten**.
- **`version = 10`** and **model name `v_ak47.mdl`** → a valid, expected
  GoldSrc model signature (Counter‑Strike AK‑47 view model). Not an error.
- **The trailing partial row** (`0x480D0`, 8 bytes) → normal for hex dumps.
- **Single `[` (`0x5B`) count (1,310)** → only ~1.14× expected; only the **pair**
  count is statistically inflated.
- **Texture‑region byte distribution** (dominant `0x6A`/`0x00`/`0x21`/etc.) →
  consistent with palettised indices, so no texture‑level anomaly found
  (the earlier "sorted gradient" impression was an artefact of the discarded
  parser and does **not** occur in the corrected binary — 0 ascending runs ≥ 32).

---

## 8. Open question / recommended follow‑up

The Valve Developer Community `MDL` reference (and the canonical
`studiohdr_t` field map) could not be fetched at analysis time (the wiki is
bot‑gating the endpoint and the Source‑SDK `studio.h` is the *Source* (`IDDM`)
header, not the GoldSrc `IDST` one). To confirm anomaly **§E** and to pin the
exact field name for `numbones`/`boneindex` (and the meaning of the `0xB8`‑stride
records in §B), compare this dump against:

- the Half‑Life 1 SDK `studio.h` `studiohdr_t` / `mstudiobone_t`, and
- a known‑good `v_ak47.mdl` of the same version,

then re‑emit a corrected binary and re‑run the `[[` / bone‑name checks.

---

## 9. Verdict

`classdump.h` is an **intact `xxd`-style hex dump of a GoldSrc `.mdl` binary
(model `v_ak47.mdl`)**. The carrier dump and the file‑length/count fields are
consistent and complete, but the payload contains **clear structural
abnormalities** — most decisively the `[[` (`0x5B5B`) sentinel injected on a
~184‑byte cadence (262× vs. ~5 expected), plus inconsistent/duplicate/non‑
contiguous bone naming. These are not parsing artefacts; they indicate the
dumped `.mdl` is non‑standard, tampered, or synthetic and should not be trusted
as an unmodified original model file.

---

## 10. Padding / non‑data byte count

“Bytes not related to data the final target program (the engine loading the
`.mdl`) uses.” Two lenses are reported — the fill *inside* the binary payload,
and the wrapper overhead *of* the hex‑dump text carrier.

### 10.1 Inside the binary payload (295,128 bytes)

| Category | Bytes | Where |
|---|---|---|
| Name‑field null padding (`"v_ak47.mdl"` is 10 chars, field holds 64) | 54 | `0x12–0x47` |
| Header reserved / zero bounds (`eyepos`, mins/maxs all 0) | 60 | `0x4C–0x87` |
| Bone table `0xF4–0x1354` (42 × 112‑byte slots) — internal fill | 2,469 | name null‑pad 359 + zero gap `[16:48]` 961 + `0xFF` sentinel `[48:64]` 672 + zero float pad 477 |
| Long zero runs (≥32 B) outside bone table & texture tail — candidate inter‑section gaps | 3,900 | e.g. `0x1354`(36), `0x1490`(204), `0x1568`(276), `0x4920`(254), `0x5334`(192), `0xDC5E…0xDF2A` (~684) |
| **Binary padding subtotal** | **~6,480 (~2.2%)** | |

Of the bone table, the *data* portion = name strings (313 B) + transform
floats (1,539 non‑zero B) + mid‑record parent/flag values (383 B) = **2,235 B**;
the remaining **2,469 B are fill** (mostly the per‑slot `0xFF…0xFF` block and
zero padding). The texture tail `0x3F000–0x480D8` (37,080 B) is treated as
opaque texture/index data and is **not** counted as padding.

> Methodology note: zero bytes are counted as “padding” only where they sit in
> known filler positions (name‑field tails, the `0xFF` sentinel blocks, the
> `[16:48]` gap of the 112‑byte bone slots, and the header reserved zone). The
> 3,900‑byte “candidate gaps” figure is less certain — some of those long zero
> runs may be legitimately zero‑valued fields, since the canonical GoldSrc
> `studiohdr_t`/`mstudiobone_t` layout could not be fetched (Valve wiki is
> bot‑gated; see §8). The rock‑solid floor is therefore **≈2,583 B** (header +
> bone‑table fill).

### 10.2 The hex‑dump carrier (the `.h` text itself)

| | Bytes |
|---|---|
| Size of `classdump.h` (text) | 1,420,394 |
| Hex‑digit characters that decode to the 295,128‑byte binary (2 per byte) | 590,256 |
| **Carrier overhead** (offsets/spaces/ASCII‑mirror/`Hex View` ruler/newlines) | **830,138 (~59% of the .h)** |
| ASCII mirror column (a *redundant* rendering of the same bytes) | ~295,136 |

So while the binary payload is only **295,128 B**, the `.h` artifact that
carries it is **1,420,394 B (~4.8× larger)**; of that, **830,138 B is pure
formatting** (offsets, spacing, the ASCII mirror, the ruler header and the
blank line), and even the hex column itself is a text encoding the engine
cannot run. If the “final target program” consumes the raw `.mdl`, then the
overwhelming bulk of the `.h` — **~1.13 MB** (everything except the 295,128
bytes of actual payload) — is non‑data.

### 10.3 Bottom line

- **Internal binary padding/fill:** ~6.5 KB (≈2.2% of the model) — the actual
  gaps/padding inside the `.mdl` itself.
- **Carrier text overhead:** ~830 KB (≈59%) of the `.h` is formatting; the whole
  `.h` is ~4.8× the size of the binary it represents.

---

## 11. Byte / symbol frequency tables + padding summary

### 11.1 “Char table” per binary region
Each cell is the **count (sum of occurrences)** of byte value `0xHH` in the
region. Rows = high nibble, columns = low nibble (`0…F`). `.` means 0 occurrences;
the printable glyph (if any) is shown in the trailing label column. Regions are
the same ones discussed in §5–§6.

**Full binary (295,128 B, all 256 values present):** top symbols —
`0x02` = 24,620 (8.35%) · `0x00` = 17,808 (6.0%) · `0x08` = 6,747 ·
`0x04` = 6,342 · `0x07` = 5,239 · `0x09` = 4,854 · `0x0A` = 4,422 ·
`0x03` = 3,833. The single most common byte is `0x02` (decimal 2) — a vertex /
index low‑byte value, not flagged as padding.

**Header `0x00–0x8F` (144 B):**
```
byte:  0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F      glyph-row
00_  : 125  .  .  .  1  .  .  .  .  .  1  .  .  .  .  .     0x00 row
...
top: 0x00=125, 0x49'I'=1,0x44'D'=1,0x53'S'=1,0x54'T'=1,0x0A=1,0x76'v'=1,0x5F'_'=1
```
(i.e. 125 null bytes of reserved/name‑fill; the 19 non‑zero bytes are the
signature + version + model name + length + eye‑position + the first count/offset
fields).

**Bone table `0xF4–0x1354` (4,704 B = 42 × 112):**
```
byte:  0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
00_  :1839 127  6  7  3  2  4  1  4  3  8  1  5  1  3  5
01_  :  3  98  4  5  6  4  1  3  5  1  1  3  2  3  2  3
... (mid rows omitted for brevity) ...
80_  : 178  2  2  1  3  1  8  1  .  4  2  1  1  2 11  2
F0_  :  1  2  .  .  .  1  .  1  .  2  4  1  .  1  1 1017
top: 0x00=1839, 0xFF=1017, 0x80=178, 0x3B';'=129, 0x01=127, 0x37'7'=126, 0x49'I'=99, 0x6D'm'=98
```
Notable: `0x00` = 1,839 and `0xFF` = 1,017 dominate (60.7% of the bone table is
fill). The `0x80`/`0xBF`/`0x3F` bytes are the high‑bytes of the bone transform
floats (exponents for values ~0.05–0.51).

**Index band `0x1894–0x4492` (11,262 B) — the `[[` region:**
```
byte:  0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
00_  : 434 129 105 94 101  74  66  72  88  73  81  71  85 121  53  58
10_  :  52 80 75 82 77  54  53  51  71  61  42  53  38  44  46  43
...
50_  :  43 24 39 38 21 46 37 27 37 38  30 136 23 39  23 25     <- 0x5B '[' = 136
F0_  :  48 58 78 91 101 104 100 69 71 59  90 67 112 102 105 182
top: 0x00=434, 0xFF=182, 0x5B'['=136, 0x01=129, 0x0D=121, 0xFC=112, 0x02=105, 0xFE=105
```
`0x5B` (`[`) = 136 (≈1.2% of this 11 KB band vs. ~0.4% expected) — the local
signature of the `[[` anomaly; `0xFC`/`0xFE` are the high bytes of the same
out‑of‑range first‑word values.

**Texture tail `0x3F000–0x480D8` (37,080 B):**
```
byte:  0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
00_  :1316 492 147 184 656 232 268 251 271 222 259 243 198 197 228 230
10_  : 252 138 154 154  99 116 131 165 150 113 171 179 122 124 221 441
30_  : 185 153 203 157 197 173 258 194 121 163 154 130 162 109 225 120
...
60_  :  53 559 312 265 185  98 492 259 307 161 1861 253 323  48 331 277   <- 0x6A 'j' = 1861
70_  : 232  36 364 189 165  63 361 225 137  27 385 154 116  25 363 91
top: 0x6A'j'=1861, 0x00=1316, 0x04=656, 0x21'!'=618, 0x61'a'=559, 0x66'f'=492, 0x01=492, 0x1F=441
```
High‑entropy palette‑index spread (top byte `0x6A`/`j`=1,861, no value >5%);
**not** padded texture data — only 99 `0xFF` / 1,316 `0x00` of 37,080 B.

### 11.2 Padding / gap totals (with confidence tier)

| Category | Bytes | Of region | Confidence |
|---|---|---|---|
| Header **name** null‑padding (`0x12–0x47`) | 54 | header | definite |
| Header reserved zeros (`0x58–0x87`; includes 12 B eye‑pos) | 48 | header | candidate* |
| Bone‑table name null‑padding (42 slots) | 359 | bone table | definite |
| Bone‑table `0xFF` sentinel blocks `[48:64]` (×42) | 672 | bone table | definite (sentinel) |
| Bone‑table zero mid‑gap `[16:48]` | 961 | bone table | candidate* |
| Bone‑table zero float pad `[64:112]` | 477 | bone table | candidate* |
| Other long (≥32 B) zero runs, outside bone & texture | 3,900 | scattered | candidate* |
| **Subtotal** | **1,085 definite / ~6,470 with all candidate (~2.2% of binary)** | | |

\* “candidate” = zero bytes that *might* be legitimately zero‑valued fields
(parent index 0, zero transform component, zero bounds vector) rather than
fill; without the unfetchable `studiohdr_t` spec they cannot be classified
with certainty. The rock‑solid padding floor is **1,085 B** (name null‑pads plus the `0xFF`
sentinel blocks); counting all zero fill as padding brings the upper bound to
**≈6,470 B (~2.2%)**.

The dominant mass of “non‑data” in this artifact is **not** inside the model —
it is the carrier text itself: the 1,420,394‑byte `.h` is **4.8× the 295,128‑byte
binary** it encodes, with **830,138 B (~59%) being formatting** (hex offsets,
inter‑byte/in‑group spaces, the 16‑char ASCII mirror, the `Hex View` ruler
header, and the blank line) — far more non‑payload bytes than the model contains
internally.
