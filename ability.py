"""Static ability catalog.

An ability is a verb that receives or alters some object / from some object.
Examples: touch, wrap, align, deconnect, connect, split, merge, etc.

Central, single source of truth for the abilities table used by the seeder
(seed_abilities.py) and the runtime seeding in main.py.

This module holds data only and never imports application code.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Ability:
    name: str
    description: str = ""
    description_ru: str = ""
    category: str = ""


# --------------------------------------------------------------------------- #
# Ability verbs — actions that receive or alter an object.
# --------------------------------------------------------------------------- #

ABILITIES: list[Ability] = [
    Ability("unwrap", "remove wrapping from the object", "снять обёртку с объекта"),
    Ability(
        "align",
        "arrange the object along a shared axis",
        "выровнять объект по общей оси",
    ),
    Ability(
        "connect",
        "join the object to another object",
        "соединить объект с другим объектом",
    ),
    Ability(
        "merge",
        "combine the object with another object",
        "объединить объект с другим объектом",
    ),
    Ability("rotate", "spin the object around an axis", "вращать объект вокруг оси"),
    Ability(
        "rotate-back",
        "spin the object back to its original orientation",
        "вернуть объект в исходную ориентацию",
    ),
    Ability(
        "translate",
        "alters the object position",
        "изменить позицию объекта в локальной геометрии",
    ),
    Ability(
        "skew",
        "tilt the object off a straight line",
        "наклонить объект относительно прямой линии",
    ),
    Ability(
        "distort",
        "deform the object away from its normal shape",
        "деформировать объект, отклонив от обычной формы",
    ),
    Ability("bend", "curve the object into an angle", "согнуть объект под углом"),
    Ability("fold", "bend the object onto itself", "сложить объект пополам"),
    Ability(
        "expand",
        "grow the object into a larger volume",
        "расширить объект до большего объёма",
    ),
    Ability(
        "flatten",
        "press the object into a thin, flat form",
        "расплющить объект в тонкую плоскую форму",
    ),
    Ability(
        "extrude",
        "push the object through a shaping die",
        "протянуть объект через формующий профиль",
    ),
    Ability(
        "engrave",
        "cut a design into the object surface",
        "выгравировать рисунок на поверхности объекта",
    ),
    Ability(
        "grind", "wear the object down with an abrasive", "стачивать объект абразивом"
    ),
    Ability("trim", "cut away excess from the object", "срезать лишнее с объекта"),
    Ability("carve", "cut the object into a shape", "вырезать объект по форме"),
    Ability("mold", "shape the object in a cavity", "придать объекту форму в полости"),
    Ability("forge", "shape the object by hammering", "выковать объект ударами"),
    Ability("weld", "fuse the object with heat", "сварить объект с помощью нагрева"),
    Ability(
        "solder",
        "join the object using molten solder",
        "соединить объект расплавленным припоем",
    ),
    Ability("rivet", "fasten the object with a rivet", "скрепить объект заклёпкой"),
    Ability("glue", "adhere the object with adhesive", "приклеить объект клеем"),
    Ability("clip", "attach the object with a clip", "прикрепить объект зажимом"),
    Ability("pin", "secure the object with a pin", "закрепить объект штифтом"),
    Ability("loosen", "decrease tension on the object", "уменьшить натяжение объекта"),
    Ability(
        "seal", "make the object air- or water-tight", "сделать объект герметичным"
    ),
    Ability("fasten", "attach the object firmly", "прочно прикрепить объект"),
    Ability("mount", "place the object onto a fixture", "установить объект на крепёж"),
    Ability(
        "unload", "remove the object from its holder", "извлечь объект из держателя"
    ),
    Ability("power-on", "apply power to the object", "подать питание на объект"),
    Ability(
        "reset",
        "return the object to its initial state",
        "вернуть объект в исходное состояние",
    ),
    Ability(
        "calibrate",
        "adjust the object to a standard",
        "откалибровать объект по эталону",
    ),
    Ability(
        "recalibrate",
        "adjust the object back to a standard",
        "перекалибровать объект по эталону",
    ),
    Ability("detune", "move the object off resonance", "сбить объект с резонанса"),
    Ability(
        "encode",
        "convert the object into another form",
        "преобразовать объект в другую форму",
    ),
    Ability(
        "compress-data",
        "reduce the object's data footprint",
        "уменьшить объём данных объекта",
    ),
    Ability("format", "lay out the object's storage", "разметить хранилище объекта"),
    Ability(
        "downgrade",
        "return the object to an older version",
        "вернуть объект к старой версии",
    ),
    Ability("firm-up", "harden the object's firmware", "закрепить прошивку объекта"),
    Ability("patch", "apply a fix to the object", "применить исправление к объекту"),
    Ability(
        "repair",
        "restore the object to working order",
        "восстановить работоспособность объекта",
    ),
    Ability("lubricate", "apply lubricant to the object", "нанести смазку на объект"),
    Ability("oil", "apply oil to the object", "нанести масло на объект"),
    Ability(
        "grease", "apply grease to the object", "нанести консистентную смазку на объект"
    ),
    Ability(
        "sterilize",
        "make the object free of organisms",
        "освободить объект от микроорганизмов",
    ),
    Ability(
        "inspect",
        "examine the object for faults",
        "осмотреть объект на предмет неисправностей",
    ),
    Ability(
        "test",
        "exercise the object to check it works",
        "проверить объект на работоспособность",
    ),
    Ability("retest", "exercise the object again", "проверить объект повторно"),
    Ability("monitor", "watch the object's state", "наблюдать за состоянием объекта"),
    Ability("weigh", "measure the object's mass", "измерить массу объекта"),
    Ability(
        "empty", "remove all contents from the object", "удалить всё содержимое объекта"
    ),
    Ability(
        "freeze",
        "lower the object below freezing",
        "охладить объект ниже точки замерзания",
    ),
    Ability(
        "temper", "harden the object by reheating", "закалить объект повторным нагревом"
    ),
    Ability(
        "sharpen", "give the object a sharp edge", "заточить объект до острой кромки"
    ),
    Ability("blunt", "remove the object's sharp edge", "снять острую кромку объекта"),
    Ability(
        "magnify",
        "increase the object's apparent size",
        "увеличить видимый размер объекта",
    ),
    Ability(
        "shield", "protect the object against radiation", "защитить объект от излучения"
    ),
    Ability(
        "unshield", "expose the object to radiation", "открыть объект для излучения"
    ),
    Ability(
        "desshield", "ex pose the object to radi ati on", "открыть объект для лечения"
    ),
    Ability("insulate", "add insulation to the object", "добавить изоляцию объекту"),
    Ability(
        "kinsulate", "add kin su l ati on tot he object", "добавить изоляции на объект"
    ),
    Ability("expose", "leave the object unprotected", "оставить объект незащищённым"),
    Ability(
        "arm", "prepare the object for activation", "подготовить объект к активации"
    ),
    Ability(
        "dearm",
        "force point the object for dearmination",
        "подготовить объект к девоевированию",
    ),
    Ability("prime", "ready the object for use", "подготовить объект к использованию"),
    Ability("select", "mark the object as chosen", "отметить объект как выбранный"),
    Ability("enable", "allow the object to operate", "разрешить объекту работать"),
    Ability(
        "disable", "prevent the object from operating", "запретить объекту работать"
    ),
    Ability(
        "isolate",
        "separate the object from its surroundings",
        "отделить объект от окружения",
    ),
    Ability(
        "disintegrate", "break the object into fragments", "разбить объект на фрагменты"
    ),
    Ability("amalgamate", "blend the object with another", "смешать объект с другим"),
    Ability("sort", "order the object within a set", "упорядочить объект в наборе"),
    Ability("index", "place the object into an index", "поместить объект в индекс"),
    Ability("label", "attach a label to the object", "прикрепить ярлык к объекту"),
    Ability("relabel", "change the object's label", "сменить ярлык объекта"),
    Ability("untag", "remove the object's tag", "снять бирку с объекта"),
    Ability("brand", "apply a brand to the object", "нанести клеймо на объект"),
    Ability(
        "deregister", "remove the object from a registry", "исключить объект из реестра"
    ),
    Ability(
        "assign",
        "allocate the object to a recipient",
        "закрепить объект за получателем",
    ),
    Ability(
        "transfer",
        "move the object to another owner",
        "передать объект другому владельцу",
    ),
    Ability(
        "deliver",
        "transport the object to its destination",
        "доставить объект к месту назначения",
    ),
    Ability(
        "retrieve",
        "fetch the object from its location",
        "забрать объект из его местоположения",
    ),
    Ability("nest", "fit the object inside another", "вложить объект внутрь другого"),
    Ability(
        "unnest",
        "remove the object from a nested set",
        "извлечь объект из вложенного набора",
    ),
    Ability(
        "fold-in",
        "tuck the object into a compact form",
        "сложить объект в компактную форму",
    ),
    Ability(
        "expand-out",
        "unfurl the object to full form",
        "развернуть объект в полную форму",
    ),
    Ability(
        "package",
        "enclose the object for transport",
        "упаковать объект для транспортировки",
    ),
    Ability("unpackage", "remove the object from its package", "распаковать объект"),
]


# --------------------------------------------------------------------------- #
# Category auto-assignment: map every ability verb to a single-word category.
# --------------------------------------------------------------------------- #

# Ordered keyword -> category rules. An ability is matched by scanning its name
# (case-insensitive) for these substrings; the first hit wins. The ordering
# matters, so more specific keywords (e.g. "compress-data") come before their
# bare stem ("compress").
_CATEGORY_RULES: list[tuple[tuple[str, ...], str]] = [
    ("scan", ("measure", "meter", "serialize", "weigh", "inspect", "test", "retest",
              "monitor", "scan", "count", "probe", "gauge", "sensor", "readout")),
    ("shape", ("bend", "fold", "unfold", "stretch", "compress", "expand", "flatten",
               "extrude", "mold", "forge", "cast", "skew", "distort", "straighten",
               "magnify", "minify")),
    ("pulse", ("pressurize", "depressurize", "vent", "purge", "fill", "refill",
               "drain", "empty", "pump")),
    ("move", ("rotate", "rotate-back", "translate", "align", "misalign", "mirror",
              "move", "shift", "shift")),
    ("cut", ("cut", "trim", "carve", "drill", "bore", "ream", "tap", "thread",
             "punch", "stamp", "engrave", "etch", "dice", "slice")),
    ("finish", ("polish", "buff", "sand", "grind", "sharpen", "blunt")),
    ("join", ("weld", "braze", "solder", "rivet", "bolt", "screw", "glue", "clip",
              "pin", "clamp", "connect", "merge", "amalgamate", "fasten", "mount",
              "install", "insert", "attach")),
    ("separate", ("split", "deconnect", "isolate", "segregate", "disintegrate",
                  "unlink", "detach", "unmount", "uninstall", "extract", "remove")),
    ("thermal", ("heat", "cool", "freeze", "thaw", "melt", "anneal", "temper",
                 "quench", "harden", "soften", "firm-up", "harden-shell")),
    ("protect", ("shield", "unshield", "insulate", "seal", "unseal", "arm", "dearm",
                 "disarm", "prime", "desshield", "kinsulate", "aminsulate",
                 "expose", "insland", "outland")),
    ("power", ("charge", "discharge", "recharge", "power-on", "power-off",
               "activate", "deactivate", "enable", "disable", "hrebate")),
    ("data", ("encode", "decode", "encrypt", "decrypt", "compress-data",
              "decompress", "format", "reformat", "initialize", "configure",
              "deconfigure", "upgrade", "downgrade", "update", "patch",
              "firm-up", "reset")),
    ("maintain", ("repair", "service", "maintain", "lubricate", "oil", "grease",
                  "clean", "wash", "decontaminate", "sterilize", "calibrate",
                  "recalibrate", "tune", "detune")),
    ("manage", ("wrap", "unwrap", "package", "unpackage", "crate", "uncrate",
                "palletize", "unpalletize", "stack", "unstack", "nest", "unnest",
                "load", "unload", "deliver", "receive", "transfer", "assign",
                "dispatch", "retrieve")),
    ("state", ("reset", "select", "deselect", "sort", "index", "categorize",
               "label", "relabel", "tag", "untag", "mark", "unmark", "brand",
               "dimark", "register", "deregister")),
    ("optics", ("focus", "defocus", "polarize", "depolarize", "magnetize",
                "demagnetize")),
]

# Fallback single-word category for verbs not otherwise matched.
_DEFAULT_CATEGORY = "operate"


def ability_category(name: str) -> str:
    """Return the single-word category assigned to a given ability name."""
    lowered = name.lower()
    for category, keywords in _CATEGORY_RULES:
        for kw in keywords:
            if kw in lowered:
                return category
    return _DEFAULT_CATEGORY


# Fill in the category on every static ability (keeps this module the single
# source of truth: the DB column and the ability_category table both mirror it).
for _spec in ABILITIES:
    object.__setattr__(_spec, "category", ability_category(_spec.name))
