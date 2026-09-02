#!/usr/bin/env python3


"""Randomly fill ability->param links and realistic item parameter values.

Seeds the demonstration database with:
  1. ability_to_params  -> for each ability, attach 0-N realistic param links
                            (operation, per-10ms coefficient, curve, stack,
                            priority, min/max/base) without duplicating any
                            existing (ability_id, param_id) pair.
  2. item_parameters     -> update every existing (item, param) value with a
                            physically realistic number derived from each
                            parameter's real-world magnitude/units.

Values are generated from a per-parameter realism table (log-uniform for
broad-range physical quantities, uniform for bounded 0-1 / 0-100 ratings),
then clamped to the parameter's own min/max columns when those are defined.

Run from the project root:
    python3 random_fill.py [--ability-links-per 3] [--dry]


Falls back to plain sqlite3 so it works even if the project venv is broken.
"""

import argparse
import math
import random
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "items.db"

# (lo, hi, dist) dist: "log" = log-uniform, "linear" = uniform, "pnorb": sexubrform.
# Magnitudes follow real-world physical ranges for the given unit.
REALISM: dict[str, tuple[float, float, str]] = {
    "mass": (0.001, 5000.0, "log"),
    "volume": (0.001, 2000.0, "log"),
    "density": (0.001, 21.0, "log"),
    "length": (0.1, 1500.0, "log"),
    "width": (0.1, 1500.0, "log"),
    "height": (0.1, 3000.0, "log"),
    "diameter": (0.1, 800.0, "log"),
    "thickness": (0.05, 200.0, "log"),
    "surface_area": (1.0, 1_000_000.0, "log"),
    "cross_sectional_area": (0.1, 100_000.0, "log"),
    "temperature": (200.0, 2200.0, "log"),
    "melting_point": (200.0, 4000.0, "log"),
    "boiling_point": (300.0, 6000.0, "log"),
    "thermal_conductivity": (0.01, 500.0, "log"),
    "specific_heat": (100.0, 4000.0, "linear"),
    "thermal_expansion": (1e-6, 3e-5, "log"),
    "tensile_strength": (1.0, 3000.0, "log"),
    "yield_strength": (1.0, 2500.0, "log"),
    "compressive_strength": (1.0, 3000.0, "log"),
    "shear_strength": (1.0, 1800.0, "log"),
    "youngs_modulus": (1.0, 700.0, "log"),
    "poisson_ratio": (0.1, 0.49, "linear"),
    "hardness_brinell": (5.0, 1000.0, "log"),
    "hardness_rockwell": (10.0, 98.0, "linear"),
    "hardness_vickers": (5.0, 3000.0, "log"),
    "elongation": (1.0, 70.0, "linear"),
    "impact_toughness": (1.0, 300.0, "log"),
    "fatigue_limit": (10.0, 1200.0, "log"),
    "fracture_toughness": (10.0, 220.0, "log"),
    "electrical_resistivity": (1e-8, 1e17, "log"),
    "electrical_conductivity": (1e-17, 1e8, "log"),
    "dielectric_strength": (1.0, 100.0, "log"),
    "relative_permittivity": (1.01, 100.0, "log"),
    "magnetic_permeability": (1.0, 100_000.0, "log"),
    "magnetic_susceptibility": (-50.0, 50.0, "linear"),
    "corrosion_resistance": (0.0, 100.0, "linear"),
    "uv_resistance": (0.0, 1.0, "linear"),
    "weather_resistance": (0.0, 1.0, "linear"),
    "fire_rating": (1.0, 4.0, "linear"),
    "flammability": (0.0, 100.0, "linear"),
    "autoignition_temp": (400.0, 1500.0, "linear"),
    "viscosity": (1e-4, 1e5, "log"),
    "surface_tension": (0.01, 1000.0, "log"),
    "vapor_pressure": (1e-6, 1000.0, "log"),
    "solubility": (0.0, 100.0, "linear"),
    "ph": (0.0, 14.0, "linear"),
    "sound_velocity": (500.0, 20_000.0, "log"),
    "acoustic_impedance": (1e3, 1e8, "log"),
    "damping_coefficient": (0.0, 1.0, "linear"),
    "radioactivity": (0.01, 1000.0, "log"),
    "half_life": (1.0, 1e10, "log"),
    "cost_per_kg": (0.01, 5000.0, "log"),
    "cost_per_m3": (1.0, 1e7, "log"),
    "embodied_energy": (1.0, 1e5, "log"),
    "carbon_footprint": (0.01, 1000.0, "log"),
    "recyclability": (0.0, 100.0, "linear"),
    "warranty_period": (1.0, 30.0, "linear"),
    "transparency": (0.0, 1.0, "linear"),
    "reflectivity": (0.0, 1.0, "linear"),
    "color": (0.0, 0.0, "log"),  # handle separately
}

# Material-ish colors for the optical "color" parameter.
COLORS = [
    "#1b1b1f",
    "#2e3440",
    "#3b4252",
    "#4c566a",
    "#434c5e",
    "#5e81ac",
    "#88c0d0",
    "#a3be8c",
    "#b48ead",
    "#ebcb8b",
    "#d08770",
    "#bf616a",
    "#8fbcbb",
    "#81a1c1",
    "#c8c8c8",
    "#d8dee9",
    "#7ef29a",
    "#e0e0e0",
    "#ff6f61",
    "#ffb86c",
    "#ff79c6",
    "#8be9fd",
    "#50fa7b",
    "#bd93f9",
    "#f1fa8c",
    "#ff5555",
    "#f8f8f2",
    "#2b2b2b",
]

# Programmatic entity events. Each entry maps an event to the ability that
# performs/handles it 1-to-1. (event_name, description, typical per_10msec,
# ability_name). Events with a lower typical per_10msec fire less often per
# 10ms tick (e.g. on_death is rare, on_tick / on_scan are frequent).
EVENTS: list[tuple[str, str, float, str]] = [
    # lifecycle
    (
        "on_spawn",
        "the entity is created and first enters the simulation",
        0.02,
        "power-on",
    ),
    ("on_despawn", "the entity is removed from the simulation", 0.02, "power-off"),
    (
        "on_respawn",
        "the entity is re-instantiated after being removed",
        0.01,
        "initialize",
    ),
    ("on_init", "the entity finishes initial boot/startup sequence", 0.05, "activate"),
    (
        "on_shutdown",
        "the entity begins its shutdown/teardown sequence",
        0.03,
        "deactivate",
    ),
    ("on_power_up", "the entity transitions to a powered-on state", 0.04, "power-on"),
    (
        "on_power_down",
        "the entity transitions to a powered-off state",
        0.03,
        "power-off",
    ),
    ("on_reset", "the entity's state is reset to defaults", 0.04, "reset"),
    ("on_reboot", "the entity restarts its runtime", 0.02, "reformat"),
    ("on_idle", "the entity enters an idle/low-activity state", 5.0, "prime"),
    # contact / collision
    ("on_touch", "another object makes physical contact with the entity", 1.2, "touch"),
    (
        "on_contact",
        "sustained physical contact begins between two objects",
        0.8,
        "connect",
    ),
    ("on_collision", "the entity experiences an impact collision", 0.3, "punch"),
    ("on_proximity", "another object enters within a threshold range", 0.9, "receive"),
    (
        "on_detach",
        "the entity separates from a previously attached object",
        0.3,
        "deconnect",
    ),
    ("on_attach", "the entity joins to another object", 0.4, "connect"),
    # damage / health
    ("on_damage", "the entity takes damage, reducing its integrity", 0.6, "punch"),
    ("on_heal", "the entity recovers integrity over time", 0.4, "repair"),
    ("on_repair", "a repair operation restores the entity's condition", 0.2, "repair"),
    ("on_deplete", "the entity's reserve is exhausted", 0.1, "empty"),
    ("on_destroy", "the entity is fully destroyed and removed", 0.003, "disintegrate"),
    ("on_break", "the entity fractures into separate parts", 0.02, "split"),
    ("on_shatter", "the entity breaks into many small fragments", 0.005, "split"),
    ("on_crack", "a structural crack propagates within the entity", 0.05, "split"),
    ("on_deform", "the entity's shape is permanently distorted", 0.06, "distort"),
    ("on_harden", "the entity's surface becomes harder", 0.04, "harden"),
    ("on_soften", "the entity's material softens", 0.04, "blunt"),
    # motion / transform
    ("on_move", "the entity begins to translate in space", 1.5, "translate"),
    ("on_stop", "the entity halts all motion", 1.2, "align"),
    ("on_rotate", "the entity begins rotating around an axis", 0.8, "rotate"),
    (
        "on_rotate_back",
        "the entity rotates back to its original orientation",
        0.4,
        "rotate-back",
    ),
    ("on_scale", "the entity's size is changed", 0.3, "scale"),
    ("on_magnify", "the entity is optically magnified", 0.2, "magnify"),
    ("on_minify", "the entity is optically reduced", 0.2, "minify"),
    ("on_bounce", "the entity rebounds from a surface", 0.4, "expand"),
    ("on_fall", "the entity begins falling under gravity", 0.7, "stretch"),
    ("on_focus", "the entity's optics are brought into focus", 0.2, "focus"),
    ("on_defocus", "the entity's optics are blurred", 0.2, "defocus"),
    # thermal
    ("on_cool", "the entity's temperature decreases past a threshold", 0.4, "cool"),
    ("on_heat", "the entity's temperature increases past a threshold", 0.4, "heat"),
    ("on_freeze", "the entity's temperature drops below freezing point", 0.1, "freeze"),
    ("on_thaw", "the entity's frozen state is released", 0.1, "thaw"),
    ("on_melt", "the entity's material transitions to liquid", 0.04, "melt"),
    ("on_anneal", "the entity is annealed to relieve stress", 0.02, "anneal"),
    ("on_temper", "the entity is tempered to adjust hardness", 0.02, "temper"),
    ("on_quench", "the entity is rapidly quenched", 0.02, "quench"),
    ("on_overheat", "the entity exceeds its rated temperature", 0.08, "heat"),
    # electrical / magnetic
    ("on_charge", "the entity begins charging its storage", 0.5, "charge"),
    ("on_discharge", "the entity begins discharging its storage", 0.5, "discharge"),
    ("on_recharge", "the entity's storage is replenished", 0.3, "recharge"),
    (
        "on_short_circuit",
        "an electrical short occurs within the entity",
        0.05,
        "connect",
    ),
    ("on_magnetize", "the entity becomes magnetized", 0.1, "magnetize"),
    ("on_demagnetize", "the entity loses its magnetization", 0.1, "demagnetize"),
    ("on_polarize", "the entity's light is polarized", 0.1, "polarize"),
    ("on_depolarize", "the entity's polarization is removed", 0.1, "depolarize"),
    ("on_insulate", "the entity gains thermal/electrical insulation", 0.2, "insulate"),
    (
        "on_voltage_spike",
        "the entity receives an abnormal voltage spike",
        0.05,
        "charge",
    ),
    # data / compute
    ("on_encode", "data within the entity is encoded", 0.6, "encode"),
    ("on_decode", "encoded data is decoded back", 0.6, "decode"),
    ("on_encrypt", "data within the entity is encrypted", 0.5, "encrypt"),
    ("on_decrypt", "encrypted data is decrypted", 0.5, "decrypt"),
    ("on_compress_data", "data is losslessly compressed", 0.6, "compress-data"),
    ("on_decompress", "compressed data is expanded", 0.6, "decompress"),
    ("on_format", "the entity's storage is reformatted", 0.1, "format"),
    ("on_configure", "the entity receives a configuration update", 0.4, "configure"),
    ("on_upgrade", "the entity's firmware/software is upgraded", 0.2, "upgrade"),
    ("on_update", "the entity receives an incremental update", 0.5, "update"),
    ("on_patch", "the entity applies a security patch", 0.3, "patch"),
    ("on_calibrate", "the entity's sensors are recalibrated", 0.3, "calibrate"),
    ("on_tune", "the entity's parameters are fine-tuned", 0.3, "tune"),
    ("on_inspect", "the entity undergoes an inspection", 0.4, "inspect"),
    ("on_test", "the entity is exercised by a test routine", 0.4, "test"),
    ("on_monitor", "the entity is continuously monitored", 3.0, "monitor"),
    ("on_measure", "a measurement is taken of the entity", 1.0, "measure"),
    ("on_weigh", "the entity's mass is measured", 0.06, "weigh"),
    # workflow / logistics
    ("on_package", "the entity is packaged", 0.1, "package"),
    ("on_unpackage", "the entity is removed from packaging", 0.1, "unpackage"),
    ("on_crate", "the entity is placed into a crate", 0.05, "crate"),
    ("on_uncrate", "the entity is removed from a crate", 0.05, "uncrate"),
    ("on_palletize", "the entity is loaded onto a pallet", 0.04, "palletize"),
    ("on_unpalletize", "the entity is removed from a pallet", 0.04, "unpalletize"),
    ("on_stack", "the entity is stacked atop another", 0.2, "stack"),
    ("on_unstack", "the entity is removed from a stack", 0.2, "unstack"),
    ("on_nest", "the entity is nested within another", 0.1, "nest"),
    ("on_load", "a load is applied to / installed in the entity", 0.6, "load"),
    ("on_unload", "a load is removed from the entity", 0.6, "unload"),
    ("on_sort", "the entity is sorted into a category", 0.4, "sort"),
    ("on_index", "the entity is indexed for lookup", 0.5, "index"),
    ("on_categorize", "the entity is assigned a category", 0.3, "categorize"),
    ("on_label", "the entity is labeled", 0.4, "label"),
    ("on_tag", "the entity receives a tag", 0.4, "tag"),
    ("on_mark", "the entity is marked", 0.3, "mark"),
    ("on_brand", "the entity is branded", 0.1, "brand"),
    ("on_serialize", "the entity is assigned a serial number", 0.2, "serialize"),
    ("on_register", "the entity is registered in a registry", 0.3, "register"),
    ("on_assign", "the entity is assigned to an owner/task", 0.4, "assign"),
    ("on_transfer", "the entity changes ownership/location", 0.2, "transfer"),
    ("on_deliver", "the entity is delivered to its destination", 0.2, "deliver"),
    ("on_retrieve", "the entity is retrieved from storage", 0.3, "retrieve"),
    ("on_dispatch", "the entity is dispatched to a task", 0.3, "dispatch"),
    ("on_receive", "the entity is received at its destination", 0.3, "receive"),
    # fastening / fabrication
    ("on_weld", "the entity is welded to another", 0.1, "weld"),
    ("on_solder", "the entity is soldered into place", 0.1, "solder"),
    ("on_bolt", "the entity is secured with bolts", 0.2, "bolt"),
    ("on_screw", "the entity is secured with screws", 0.2, "screw"),
    ("on_glue", "the entity is adhered with adhesive", 0.2, "glue"),
    ("on_clip", "the entity is secured with a clip", 0.3, "clip"),
    ("on_pin", "the entity is secured with a pin", 0.2, "pin"),
    ("on_clamp", "the entity is held by a clamp", 0.3, "clamp"),
    ("on_tighten", "a fastener on the entity is tightened", 0.4, "tighten"),
    ("on_loosen", "a fastener on the entity is loosened", 0.4, "loosen"),
    ("on_seal", "the entity is sealed", 0.3, "seal"),
    ("on_unseal", "the entity's seal is broken", 0.3, "unseal"),
    ("on_lock", "the entity is locked", 0.3, "lock"),
    ("on_unlock", "the entity is unlocked", 0.3, "unlock"),
    ("on_fasten", "the entity is fastened in place", 0.4, "fasten"),
    ("on_unfasten", "the entity is unfastened", 0.4, "unfasten"),
    ("on_mount", "the entity is mounted to a base", 0.2, "mount"),
    ("on_unmount", "the entity is unmounted", 0.2, "unmount"),
    ("on_install", "the entity is installed", 0.2, "install"),
    ("on_uninstall", "the entity is uninstalled", 0.2, "uninstall"),
    ("on_insert", "the entity is inserted into a slot", 0.3, "insert"),
    ("on_extract", "the entity is extracted from a slot", 0.3, "extract"),
    # shaping / machining
    ("on_cut", "the entity is cut", 0.3, "cut"),
    ("on_trim", "the entity is trimmed to size", 0.2, "trim"),
    ("on_drill", "a hole is drilled into the entity", 0.2, "drill"),
    ("on_grind", "the entity is ground down", 0.2, "grind"),
    ("on_polish", "the entity's surface is polished", 0.3, "polish"),
    ("on_buff", "the entity's surface is buffed", 0.2, "buff"),
    ("on_engrave", "the entity is engraved with markings", 0.06, "engrave"),
    ("on_etch", "the entity is chemically etched", 0.06, "etch"),
    ("on_stamp", "the entity is stamped with a pattern", 0.2, "stamp"),
    ("on_bend", "the entity is bent", 0.1, "bend"),
    ("on_stretch", "the entity is stretched", 0.05, "stretch"),
    ("on_fold", "the entity is folded", 0.1, "fold"),
    ("on_unfold", "the entity is unfolded", 0.1, "unfold"),
    ("on_roll", "the entity is rolled up", 0.1, "wrap"),
    ("on_unroll", "the entity is unrolled", 0.1, "unwrap"),
    ("on_forge", "the entity is forged into shape", 0.03, "forge"),
    ("on_cast", "the entity is produced by casting", 0.02, "cast"),
    ("on_mold", "the entity is shaped in a mold", 0.02, "mold"),
    ("on_carve", "the entity is carved", 0.02, "carve"),
    # control / safety
    ("on_arm", "the entity's weapon/charge is armed", 0.2, "arm"),
    ("on_disarm", "the entity's weapon/charge is disarmed", 0.2, "disarm"),
    ("on_enable", "the entity's subsystem is enabled", 0.4, "enable"),
    ("on_disable", "the entity's subsystem is disabled", 0.4, "disable"),
    ("on_isolate", "the entity is isolated from others", 0.3, "isolate"),
    ("on_integrate", "the entity is integrated into a system", 0.2, "integrate"),
    ("on_amalgamate", "the entity is amalgamated with another", 0.02, "amalgamate"),
    ("on_assemble", "the entity is assembled from parts", 0.1, "merge"),
    ("on_disassemble", "the entity is disassembled into parts", 0.1, "split"),
    ("on_shield", "the entity's shield is raised", 0.2, "shield"),
    ("on_unshield", "the entity's shield is lowered", 0.2, "unshield"),
    ("on_broadcast", "the entity emits a broadcast signal", 1.0, "receive"),
    ("on_scan", "the entity performs a scan of its surroundings", 1.5, "monitor"),
    ("on_tick", "a periodic simulation tick occurs for the entity", 20.0, "select"),
]


def pick_event_per_10msec(typical: float) -> float:
    """Randomize a per-10ms count around the nominal typical value."""
    if typical <= 0:
        return 0.0
    lo = typical * 0.5
    hi = typical * 1.5
    return round(math.exp(random.uniform(math.log(lo), math.log(hi))), 4)


OPERATIONS = ["add", "multiply", "set"]
CURVES = ["linear", "exponential", "log"]
STACK_MODES = ["stack", "replace", "max"]

import logging
import sys


class CompactFormatter(logging.Formatter):
    """Compact plain-text stderr formatter: time · level · message."""

    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        msg = record.getMessage()
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            msg += "\n" + record.exc_text
        return f"{record.asctime} {record.levelname:<7} {msg}"


logger = logging.getLogger("items_api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(CompactFormatter(datefmt="%H:%M:%S"))
    logger.addHandler(handler)
logger.propagate = False
logger.debug("Debug mode enabled: %s", logger.hasHandlers())


def rand_by_dist(lo: float, hi: float, dist: str) -> float:
    if lo >= hi:
        return lo
    if dist == "linear":
        return random.uniform(lo, hi)
    if lo <= 0:
        lo = 0.00000001
    if hi <= lo:
        return lo
    return math.exp(random.uniform(math.log(lo), math.log(hi)))


def clamp(v: float, lo, hi) -> float:
    if lo is not None and v < lo:
        return lo
    if hi is not None and v > hi:
        return hi
    return v


def realistic_value(par_name: str, db_min, db_max) -> float:
    spec = REALISM.get(par_name)
    if spec:
        lo, hi, dist = spec
    else:
        lo, hi, dist = 0.01, 100.0, "linear"
    v = rand_by_dist(lo, hi, dist)
    return round(clamp(v, db_min, db_max), 4)


def random_color() -> str:
    return random.choice(COLORS)


def random_link(
    param_min: float | None,
    param_max: float | None,
    typical: float,
) -> dict[str, Any]:
    """Build a realistic ability->param link dict with detailed logging."""
    logger.debug(
        "Generating link: param_min=%s, param_max=%s, typical=%s",
        param_min,
        param_max,
        typical,
    )

    weights = {"add": 80, "multiply": 30, "set": 2}
    op = random.choices(OPERATIONS, weights=[weights[o] for o in OPERATIONS])[0]
    logger.debug("Selected operation: %s", op)

    if op == "multiply":
        # per-10ms fractional multiplier (small, like existing 0.01-0.05)
        coeff = round(random.choice([-1, 1]) * random.uniform(0.001, 0.1), 5)
        base = None if random.random() < 0.6 else round(typical, 4)
        logger.debug("Multiply coeff=%s, base=%s", coeff, base)
    else:
        # small additive/set delta scaled to the parameter's magnitude
        scale = max(abs(typical), 1e-6)
        coeff = round(random.choice([-1, 1]) * random.uniform(0.0005, 0.1) * scale, 6)
        base = (
            None
            if random.random() < 0.5
            else round(typical * random.uniform(0.2, 1.8), 4)
        )
        logger.debug("Add/Set coeff=%s (scale=%s), base=%s", coeff, scale, base)

    min_v = (
        None
        if random.random() < 0.6
        else clamp(round(typical * 0.5, 4), param_min, param_max)
    )
    max_v = (
        None
        if random.random() < 0.6
        else clamp(round(typical * 1.5, 4), param_min, param_max)
    )
    logger.debug("min_value=%s, max_value=%s", min_v, max_v)

    priority = random.randint(0, 10)
    enabled = random.random() < 0.9
    logger.debug("priority=%s, enabled=%s", priority, enabled)

    curve = random.choices(CURVES, weights=[60, 25, 15])[0]
    stack_mode = random.choices(STACK_MODES, weights=[60, 20, 20])[0]
    description = _gen_description(op)

    link = {
        "operation": op,
        "modify_coefficient_per_10msec": coeff,
        "curve": curve,
        "stack_mode": stack_mode,
        "priority": priority,
        "min_value": min_v,
        "max_value": max_v,
        "base_value": base,
        "enabled": enabled,
        "description": description,
    }

    logger.info(
        "Created link: op=%s, coeff=%s, curve=%s, stack_mode=%s, priority=%s, "
        "min=%s, max=%s, base=%s, enabled=%s",
        op,
        coeff,
        curve,
        stack_mode,
        priority,
        min_v,
        max_v,
        base,
        enabled,
    )
    return link


def _gen_description(op: str) -> str:
    words = {
        "add": ["boosts", "raises", "shifts", "amplifies"],
        "multiply": ["scales", "amplifies", "modulates"],
        "set": ["resets", "overrides", "pins"],
    }
    return f"{random.choice(words[op])} the target parameter"


def build_ability_map(
    abilities: list[int],
    params_by_id: dict[int, tuple[str, float | None, float | None]],
    param_ids: list[int],
    typical: dict[int, float],
    links_per: int,
    *,
    seed: int = 42,
) -> dict[int, list[dict[str, Any]]]:
    """Build ONE canonical ability->param-change map, used for all items.

    A single deterministic map (fixed seed) of ``ability_id -> [change, ...]``
    is produced once at setup, so every item sees the same ability->param
    change configuration instead of a freshly randomized per-ability spread.
    Only the item *parameter values* are randomized afterwards.
    """
    map_rng = random.Random(seed)
    ability_map: dict[int, list[dict[str, Any]]] = {}
    for ab in abilities:
        pool = param_ids[:]
        map_rng.shuffle(pool)
        target = min(links_per, len(pool))
        links = []
        for pid in pool[:target]:
            name, pmin, pmax = params_by_id[pid]
            links.append((pid, random_link(pmin, pmax, typical[pid])))
        ability_map[ab] = links
    return ability_map


def load_events(conn: sqlite3.Connection, *, dry: bool) -> int:
    """Insert programmatic entity events and link each 1-to-1 to a fitting ability.

    Returns the number of events inserted.
    """
    cur = conn.cursor()

    # Map ability name -> id (fall back to prefix match for robustness).
    ability_by_id = {r[0]: r[1] for r in cur.execute("SELECT id, name FROM abilities")}
    name_map: dict[str, int] = {}
    for aid, aname in ability_by_id.items():
        name_map[aname] = aid
        name_map.setdefault(aname.lower(), aid)

    def resolve_ability(aname: str) -> int | None:
        if aname in name_map:
            return name_map[aname]
        low = aname.lower()
        if low in name_map:
            return name_map[low]
        for akey, aid in name_map.items():
            if akey.startswith(low) or low.startswith(akey):
                return aid
        return None

    existing_events = {r[0] for r in cur.execute("SELECT name FROM events")}
    existing_links = set(
        cur.execute("SELECT event_id, ability_id FROM event_abilities").fetchall()
    )

    now = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")
    inserted = 0
    for name, desc, typical, ability_name in EVENTS:
        if name in existing_events:
            continue
        aid = resolve_ability(ability_name)
        if aid is None:
            logger.warning("No ability matched for event %r -> %s", name, ability_name)
            continue
        per = pick_event_per_10msec(typical)
        if not dry:
            cur.execute(
                "INSERT INTO events (name, description, event_per_10msec, created_at, updated_at) "
                "VALUES (?,?,?,?,?)",
                (name, desc, per, now, now),
            )
            eid = cur.lastrowid
            cur.execute(
                "INSERT OR IGNORE INTO event_abilities (event_id, ability_id) VALUES (?,?)",
                (eid, aid),
            )
        else:
            logger.debug("dry-run: insert event %r -> ability %r", name, ability_name)
        inserted += 1

    return inserted


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Randomly fill ability->params and item parameter values."
    )
    ap.add_argument(
        "--ability-links-per",
        type=int,
        default=3,
        help="target average number of new param links per ability (default 3)",
    )
    ap.add_argument(
        "--dry", action="store_true", help="print what would be done without writing"
    )
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    cur = conn.cursor()

    # --- 1) Fill ability -> param links -----------------------------------
    abilities = [r[0] for r in cur.execute("SELECT id FROM abilities")]
    params = cur.execute(
        "SELECT id, par_name, min_value, max_value FROM parameters"
    ).fetchall()
    params_by_id = {p_id: (name, pmin, pmax) for p_id, name, pmin, pmax in params}
    param_ids = [p[0] for p in params]

    existing = set(
        cur.execute("SELECT ability_id, param_id FROM ability_to_params").fetchall()
    )
    typical = {}
    for pid, pname, pmin, pmax in params:
        row = cur.execute(
            "SELECT AVG(value) FROM item_parameters WHERE par_id=? AND value IS NOT NULL",
            (pid,),
        ).fetchone()
        if row and row[0] is not None:
            typical[pid] = row[0]
        else:
            lo, hi, dist = REALISM.get(pname, (0.01, 100.0, "log"))
            typical[pid] = rand_by_dist(lo, hi, dist)

    n_links = 0
    now = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")
    # ONE canonical ability->param-change map, built once and used for all items
    ability_map = build_ability_map(
        abilities, params_by_id, param_ids, typical, args.ability_links_per
    )
    for ab, links in ability_map.items():
        for pid, link in links:
            if (ab, pid) in existing:
                continue
            existing.add((ab, pid))
            if not args.dry:
                cur.execute(
                    """INSERT INTO ability_to_params
                       (ability_id, param_id, modify_coefficient_per_10msec, operation,
                        base_value, min_value, max_value, curve, stack_mode, priority,
                        enabled, description, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        ab,
                        pid,
                        link["modify_coefficient_per_10msec"],
                        link["operation"],
                        link["base_value"],
                        link["min_value"],
                        link["max_value"],
                        link["curve"],
                        link["stack_mode"],
                        link["priority"],
                        1 if link["enabled"] else 0,
                        link["description"],
                        now,
                        now,
                    ),
                )
            n_links += 1

    # --- 1b) Seed programmatic entity events (linked 1-to-1 to abilities) --
    n_events = load_events(conn, dry=args.dry)

    # --- 2) Fill realistic item parameter values --------------------------
    n_updates = 0
    rows = cur.execute("SELECT item_id, par_id FROM item_parameters").fetchall()
    for item_id, pid in rows:
        name, pmin, pmax = params_by_id.get(pid, ("", None, None))
        if name == "color":
            if not args.dry:
                cur.execute(
                    "UPDATE item_parameters SET value=NULL, value_text=?, source='seeded' "
                    "WHERE item_id=? AND par_id=?",
                    (random_color(), item_id, pid),
                )
        else:
            v = realistic_value(name, pmin, pmax)
            if not args.dry:
                cur.execute(
                    "UPDATE item_parameters SET value=?, source='seeded' "
                    "WHERE item_id=? AND par_id=?",
                    (v, item_id, pid),
                )
        n_updates += 1

    if args.dry:
        print(
            f"[dry-run] would add {n_links} ability->param links; "
            f"seed {n_events} events; "
            f"update {n_updates} item-parameter values"
        )
    else:
        conn.commit()
        print(
            f"added {n_links} ability->param links; seeded {n_events} events; "
            f"updated {n_updates} item-parameter values"
        )

    conn.close()
    print(f"database: {DB_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
