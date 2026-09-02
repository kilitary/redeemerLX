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
    Ability(
        "touch",
        "make physical contact with the object",
        "вступить в физический контакт с объектом",
    ),
    Ability(
        "wrap",
        "enclose or fold the object in material",
        "заключить или сложить объект в материал",
    ),
    Ability("unwrap", "remove wrapping from the object", "снять обёртку с объекта"),
    Ability(
        "align",
        "arrange the object along a shared axis",
        "выровнять объект по общей оси",
    ),
    Ability(
        "misalign",
        "offset the object from its intended axis",
        "сместить объект с заданной оси",
    ),
    Ability(
        "connect",
        "join the object to another object",
        "соединить объект с другим объектом",
    ),
    Ability(
        "deconnect",
        "separate the object from another object",
        "отсоединить объект от другого объекта",
    ),
    Ability(
        "split",
        "divide the object into smaller parts",
        "разделить объект на более мелкие части",
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
    Ability("scale", "change the size of the object", "изменить размер объекта"),
    Ability(
        "translate",
        "alters the object position",
        "изменить позицию объекта в локальной геометрии",
    ),
    Ability(
        "invert",
        "turn the object inside out or upside down",
        "вывернуть объект наизнанку или вверх дном",
    ),
    Ability(
        "mirror", "flip the object as if reflected", "отразить объект как в зеркале"
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
    Ability(
        "straighten",
        "remove bends and kinks from the object",
        "устранить изгибы и перегибы объекта",
    ),
    Ability("bend", "curve the object into an angle", "согнуть объект под углом"),
    Ability("fold", "bend the object onto itself", "сложить объект пополам"),
    Ability(
        "unfold",
        "lay the folded object back out",
        "развернуть сложенный объект обратно",
    ),
    Ability(
        "stretch",
        "pull the object into a longer shape",
        "растянуть объект в более длинную форму",
    ),
    Ability(
        "compress",
        "press the object into a smaller volume",
        "сжать объект в меньший объём",
    ),
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
        "punch",
        "force a hole or blank through the object",
        "пробить отверстие или заготовку в объекте",
    ),
    Ability("stamp", "impress a mark onto the object", "отпечатать отметку на объекте"),
    Ability(
        "engrave",
        "cut a design into the object surface",
        "выгравировать рисунок на поверхности объекта",
    ),
    Ability(
        "etch",
        "corrode a pattern into the object surface",
        "вытравить узор на поверхности объекта",
    ),
    Ability(
        "polish",
        "smooth and shine the object surface",
        "отполировать и отшлифовать поверхность объекта",
    ),
    Ability("buff", "rub the object to a shine", "натереть объект до блеска"),
    Ability("sand", "abrade the object surface", "отшлифовать поверхность объекта"),
    Ability(
        "grind", "wear the object down with an abrasive", "стачивать объект абразивом"
    ),
    Ability("drill", "bore a hole into the object", "просверлить отверстие в объекте"),
    Ability(
        "bore",
        "enlarge an existing hole in the object",
        "расширить существующее отверстие в объекте",
    ),
    Ability(
        "ream",
        "smooth the inside of a hole in the object",
        "сгладить внутреннюю часть отверстия в объекте",
    ),
    Ability(
        "tap",
        "cut threads inside a hole in the object",
        "нарезать резьбу внутри отверстия в объекте",
    ),
    Ability("thread", "cut a helix onto the object", "нарезать спираль на объекте"),
    Ability("cut", "sever part of the object", "отрезать часть объекта"),
    Ability("trim", "cut away excess from the object", "срезать лишнее с объекта"),
    Ability("carve", "cut the object into a shape", "вырезать объект по форме"),
    Ability("mold", "shape the object in a cavity", "придать объекту форму в полости"),
    Ability(
        "cast",
        "form the object by pouring into a mould",
        "отлить объект, залив в форму",
    ),
    Ability("forge", "shape the object by hammering", "выковать объект ударами"),
    Ability("weld", "fuse the object with heat", "сварить объект с помощью нагрева"),
    Ability(
        "braze",
        "join the object using a filler metal",
        "соединить объект с помощью присадочного металла",
    ),
    Ability(
        "solder",
        "join the object using molten solder",
        "соединить объект расплавленным припоем",
    ),
    Ability("rivet", "fasten the object with a rivet", "скрепить объект заклёпкой"),
    Ability("bolt", "fasten the object with a bolt", "скрепить объект болтом"),
    Ability("screw", "fasten the object with a screw", "скрепить объект винтом"),
    Ability("glue", "adhere the object with adhesive", "приклеить объект клеем"),
    Ability("clip", "attach the object with a clip", "прикрепить объект зажимом"),
    Ability("pin", "secure the object with a pin", "закрепить объект штифтом"),
    Ability("clamp", "hold the object in a clamp", "зажать объект в тисках"),
    Ability("tighten", "increase tension on the object", "увеличить натяжение объекта"),
    Ability("loosen", "decrease tension on the object", "уменьшить натяжение объекта"),
    Ability(
        "seal", "make the object air- or water-tight", "сделать объект герметичным"
    ),
    Ability("unseal", "break the seal on the object", "вскрыть уплотнение объекта"),
    Ability(
        "lock", "secure the object against movement", "зафиксировать объект от движения"
    ),
    Ability("unlock", "release the object from its lock", "освободить объект от замка"),
    Ability("fasten", "attach the object firmly", "прочно прикрепить объект"),
    Ability(
        "unfasten",
        "release the object from its fastening",
        "освободить объект от крепления",
    ),
    Ability("mount", "place the object onto a fixture", "установить объект на крепёж"),
    Ability(
        "unmount", "remove the object from its fixture", "снять объект с крепления"
    ),
    Ability(
        "install",
        "put the object into its working position",
        "установить объект в рабочее положение",
    ),
    Ability(
        "uninstall", "take the object out of service", "снять объект с обслуживания"
    ),
    Ability(
        "insert",
        "put the object into a socket or cavity",
        "вставить объект в гнездо или полость",
    ),
    Ability(
        "extract",
        "pull the object out of its socket or cavity",
        "извлечь объект из гнезда или полости",
    ),
    Ability("load", "place the object into a holder", "поместить объект в держатель"),
    Ability(
        "unload", "remove the object from its holder", "извлечь объект из держателя"
    ),
    Ability(
        "charge",
        "supply power or charge to the object",
        "подать питание или заряд объекту",
    ),
    Ability(
        "discharge",
        "release stored charge from the object",
        "снять накопленный заряд с объекта",
    ),
    Ability("recharge", "restore charge to the object", "восстановить заряд объекта"),
    Ability("power-on", "apply power to the object", "подать питание на объект"),
    Ability("power-off", "remove power from the object", "отключить питание объекта"),
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
    Ability("tune", "adjust the object for resonance", "настроить объект на резонанс"),
    Ability("detune", "move the object off resonance", "сбить объект с резонанса"),
    Ability(
        "encode",
        "convert the object into another form",
        "преобразовать объект в другую форму",
    ),
    Ability(
        "decode",
        "recover the original form of the object",
        "восстановить исходную форму объекта",
    ),
    Ability(
        "encrypt", "scramble the object's content", "зашифровать содержимое объекта"
    ),
    Ability(
        "decrypt",
        "restore the object's plain content",
        "восстановить открытое содержимое объекта",
    ),
    Ability(
        "compress-data",
        "reduce the object's data footprint",
        "уменьшить объём данных объекта",
    ),
    Ability(
        "decompress",
        "restore the object's full data footprint",
        "восстановить полный объём данных объекта",
    ),
    Ability("format", "lay out the object's storage", "разметить хранилище объекта"),
    Ability(
        "reformat", "re-lay the object's storage", "переразметить хранилище объекта"
    ),
    Ability(
        "initialize",
        "set up the object for first use",
        "подготовить объект к первому использованию",
    ),
    Ability(
        "configure",
        "set the object's operating parameters",
        "задать рабочие параметры объекта",
    ),
    Ability(
        "deconfigure",
        "clear the object's operating parameters",
        "сбросить рабочие параметры объекта",
    ),
    Ability(
        "upgrade",
        "raise the object to a newer version",
        "повысить объект до новой версии",
    ),
    Ability(
        "downgrade",
        "return the object to an older version",
        "вернуть объект к старой версии",
    ),
    Ability("firm-up", "harden the object's firmware", "закрепить прошивку объекта"),
    Ability(
        "update",
        "bring the object to the latest state",
        "привести объект к актуальному состоянию",
    ),
    Ability("patch", "apply a fix to the object", "применить исправление к объекту"),
    Ability(
        "repair",
        "restore the object to working order",
        "восстановить работоспособность объекта",
    ),
    Ability(
        "service", "perform maintenance on the object", "провести обслуживание объекта"
    ),
    Ability(
        "maintain",
        "keep the object in working order",
        "поддерживать объект в рабочем порядке",
    ),
    Ability("lubricate", "apply lubricant to the object", "нанести смазку на объект"),
    Ability("oil", "apply oil to the object", "нанести масло на объект"),
    Ability(
        "grease", "apply grease to the object", "нанести консистентную смазку на объект"
    ),
    Ability("clean", "remove dirt from the object", "удалить грязь с объекта"),
    Ability("wash", "clean the object with liquid", "очистить объект жидкостью"),
    Ability(
        "decontaminate",
        "remove contaminants from the object",
        "удалить загрязнения с объекта",
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
    Ability("measure", "take measurements of the object", "снять показания объекта"),
    Ability("weigh", "measure the object's mass", "измерить массу объекта"),
    Ability(
        "meter", "measure the object's consumption", "измерить потребление объекта"
    ),
    Ability(
        "pressurize",
        "raise pressure inside the object",
        "повысить давление внутри объекта",
    ),
    Ability(
        "depressurize",
        "lower pressure inside the object",
        "понизить давление внутри объекта",
    ),
    Ability("vent", "release pressure from the object", "стравить давление из объекта"),
    Ability("purge", "flush the object of contents", "продуть объект от содержимого"),
    Ability("fill", "put contents into the object", "заполнить объект содержимым"),
    Ability(
        "refill", "top the object's contents back up", "дозаполнить содержимое объекта"
    ),
    Ability(
        "drain", "remove contents from the object", "удалить содержимое из объекта"
    ),
    Ability(
        "empty", "remove all contents from the object", "удалить всё содержимое объекта"
    ),
    Ability("cool", "lower the object's temperature", "понизить температуру объекта"),
    Ability("heat", "raise the object's temperature", "повысить температуру объекта"),
    Ability(
        "freeze",
        "lower the object below freezing",
        "охладить объект ниже точки замерзания",
    ),
    Ability(
        "thaw",
        "raise the object above freezing",
        "разогреть объект выше точки замерзания",
    ),
    Ability(
        "melt", "heat the object until it liquefies", "нагреть объект до расплавления"
    ),
    Ability(
        "anneal",
        "heat and slowly cool the object",
        "нагреть и медленно охладить объект",
    ),
    Ability(
        "temper", "harden the object by reheating", "закалить объект повторным нагревом"
    ),
    Ability("quench", "rapidly cool the object", "быстро охладить объект"),
    Ability("harden", "increase the object's hardness", "повысить твёрдость объекта"),
    Ability("soften", "decrease the object's hardness", "снизить твёрдость объекта"),
    Ability(
        "harden-shell",
        "harden the object's outer shell",
        "упрочнить внешнюю оболочку объекта",
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
        "minify",
        "decrease the object's apparent size",
        "уменьшить видимый размер объекта",
    ),
    Ability(
        "focus", "concentrate the object's output", "сконцентрировать выход объекта"
    ),
    Ability("defocus", "spread the object's output", "рассеять выход объекта"),
    Ability(
        "polarize",
        "impose polarization on the object",
        "наложить поляризацию на объект",
    ),
    Ability(
        "depolarize",
        "remove polarization from the object",
        "снять поляризацию с объекта",
    ),
    Ability("magnetize", "impart magnetism to the object", "намагнитить объект"),
    Ability("demagnetize", "remove magnetism from the object", "размагнитить объект"),
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
    Ability(
        "aminsulate",
        "add m in su lat ion to the object",
        "разбавить изоляцию со спутника",
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
    Ability(
        "disarm",
        "make the object safe against activation",
        "обезопасить объект от активации",
    ),
    Ability("prime", "ready the object for use", "подготовить объект к использованию"),
    Ability(
        "insland",
        "ready the object for interstellar use",
        "подготовить объект к исследованию",
    ),
    Ability(
        "outland",
        "link the object for interstillar de fuse",
        "подготовить объект к исчезновению",
    ),
    Ability(
        "deselect",
        "take the object out of an active set",
        "исключить объект из активного набора",
    ),
    Ability("select", "mark the object as chosen", "отметить объект как выбранный"),
    Ability("activate", "switch the object on", "включить объект"),
    Ability(
        "hrebate", "switch the object horse sex on", "подать объект на вход лошади"
    ),
    Ability("deactivate", "switch the object off", "выключить объект"),
    Ability("enable", "allow the object to operate", "разрешить объекту работать"),
    Ability(
        "disable", "prevent the object from operating", "запретить объекту работать"
    ),
    Ability(
        "isolate",
        "separate the object from its surroundings",
        "отделить объект от окружения",
    ),
    Ability("integrate", "combine the object into a whole", "включить объект в целое"),
    Ability(
        "disintegrate", "break the object into fragments", "разбить объект на фрагменты"
    ),
    Ability("amalgamate", "blend the object with another", "смешать объект с другим"),
    Ability(
        "segregate",
        "keep the object apart from others",
        "держать объект отдельно от других",
    ),
    Ability("sort", "order the object within a set", "упорядочить объект в наборе"),
    Ability("index", "place the object into an index", "поместить объект в индекс"),
    Ability(
        "categorize", "assign the object to a category", "отнести объект к категории"
    ),
    Ability("label", "attach a label to the object", "прикрепить ярлык к объекту"),
    Ability("relabel", "change the object's label", "сменить ярлык объекта"),
    Ability("tag", "attach a tag to the object", "прикрепить бирку к объекту"),
    Ability("untag", "remove the object's tag", "снять бирку с объекта"),
    Ability("mark", "put a mark on the object", "поставить отметку на объекте"),
    Ability(
        "dimark",
        "put a numeric pink noise on the object",
        "проставить пинковые помехи на объекте",
    ),
    Ability("unmark", "remove the object's mark", "убрать отметку с объекта"),
    Ability("brand", "apply a brand to the object", "нанести клеймо на объект"),
    Ability(
        "serialize",
        "give the object a serial identity",
        "присвоить объекту серийный номер",
    ),
    Ability("register", "enter the object into a registry", "внести объект в реестр"),
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
    Ability(
        "dispatch",
        "send the object to its destination",
        "отправить объект к месту назначения",
    ),
    Ability("receive", "take delivery of the object", "принять объект"),
    Ability(
        "stack", "arrange the object above another", "уложить объект поверх другого"
    ),
    Ability("unstack", "remove the object from a stack", "снять объект со стопки"),
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
    Ability("crate", "place the object in a crate", "поместить объект в ящик"),
    Ability("uncrate", "remove the object from its crate", "извлечь объект из ящика"),
    Ability(
        "palletize", "place the object on a pallet", "разместить объект на паллете"
    ),
    Ability(
        "unpalletize", "remove the object from its pallet", "снять объект с паллеты"
    ),
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
