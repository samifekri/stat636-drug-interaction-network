"""Helpers shared by the notebooks: cached openFDA / RxNorm requests, name rules, label mining.

Every API response is saved under data/raw/ (one JSON file per request), so rerunning a
notebook reads from disk instead of the API. Delete data/raw/<source>/ to refetch.
"""

import hashlib
import json
import re
import time
from pathlib import Path

import requests

OPENFDA = "https://api.fda.gov/drug"
RXNAV = "https://rxnav.nlm.nih.gov/REST"
SUB = "patient.drug.openfda.substance_name.exact"   # harmonized substance names in reports

STATS = {"requests": 0, "cached": 0}


# --------------------------------------------------------------------------- HTTP with a disk cache
def _http_get(url, params):
    """One GET with retries. Returns parsed JSON, or {} for openFDA's 'no matches' (404)."""
    for attempt in range(6):
        try:
            r = requests.get(url, params=params, timeout=60,
                             headers={"User-Agent": "stat636-group6-research"})
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 404:
            return {}
        if r.status_code == 403 and "API_KEY" in r.text:
            raise RuntimeError("openFDA wants an API key: put OPENFDA_API_KEY in .env (see .env.example)")
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Request kept failing: {url} {params}")


def cached_get(raw_dir, source, url, params, tag, pause=0.25):
    """GET url?params, cached as raw_dir/source/<tag>__<hash>.json. The API key is never cached."""
    public = {k: v for k, v in params.items() if k != "api_key"}
    key = hashlib.sha1(json.dumps([url, public], sort_keys=True).encode()).hexdigest()[:12]
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", tag)[:60]
    path = Path(raw_dir) / source / f"{safe}__{key}.json"
    if path.exists():
        STATS["cached"] += 1
        return json.loads(path.read_text(encoding="utf-8"))
    data = _http_get(url, params)
    STATS["requests"] += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    time.sleep(pause)
    return data


def openfda(raw_dir, api_key, endpoint, params, tag):
    """openFDA query. Search clauses use '+' between terms, so the query string is built by hand."""
    q = dict(params)
    if api_key:
        q["api_key"] = api_key
    safe = "+:()_.*"
    query = "&".join(k + "=" + requests.utils.quote(str(v), safe=safe) for k, v in q.items())
    return _cached_openfda(raw_dir, endpoint, query, params, tag)


def _cached_openfda(raw_dir, endpoint, query, params, tag):
    public = {k: v for k, v in params.items() if k != "api_key"}
    key = hashlib.sha1(json.dumps([endpoint, public], sort_keys=True).encode()).hexdigest()[:12]
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", tag)[:60]
    path = Path(raw_dir) / "openfda" / f"{safe}__{key}.json"
    if path.exists():
        STATS["cached"] += 1
        return json.loads(path.read_text(encoding="utf-8"))
    data = _http_get(f"{OPENFDA}/{endpoint}.json?{query}", None)
    STATS["requests"] += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    time.sleep(0.3)   # openFDA allows 240 requests per minute
    return data


def or_query(field, names):
    """field:"a"+field:"b"  (openFDA treats '+' between clauses as OR)."""
    return "+".join(f'{field}:"{n}"' for n in names)


def total(resp):
    return resp.get("meta", {}).get("results", {}).get("total", 0)


# --------------------------------------------------------------------------- RxNorm
def rxnorm_ingredients(raw_dir, name):
    """Map a drug name to its RxNorm ingredient(s).

    Returns (status, [(rxcui, ingredient_name), ...]) with status one of
    'single' (one ingredient), 'combination' (several), 'not_found'.
    """
    d = cached_get(raw_dir, "rxnav", f"{RXNAV}/rxcui.json", {"name": name, "search": 2}, f"rxcui_{name}", pause=0.06)
    ids = (d.get("idGroup") or {}).get("rxnormId") or []
    if not ids:
        return "not_found", []
    rxcui = ids[0]
    props = cached_get(raw_dir, "rxnav", f"{RXNAV}/rxcui/{rxcui}/properties.json", {}, f"props_{rxcui}", pause=0.06)
    p = props.get("properties") or {}
    if p.get("tty") == "IN":
        return "single", [(p["rxcui"], p["name"].lower())]
    rel = cached_get(raw_dir, "rxnav", f"{RXNAV}/rxcui/{rxcui}/related.json", {"tty": "IN"}, f"in_{rxcui}", pause=0.06)
    ins = []
    for g in (rel.get("relatedGroup") or {}).get("conceptGroup") or []:
        for c in g.get("conceptProperties") or []:
            ins.append((c["rxcui"], c["name"].lower()))
    if not ins:
        return "not_found", []
    return ("single" if len(ins) == 1 else "combination"), ins


# --------------------------------------------------------------------------- name rules
# Vitamins, minerals, herbal and homeopathic ingredients (mostly from multivitamin / supplement products).
NON_DRUG = re.compile(
    r"vitamin|tocopherol|niacin|riboflavin|thiamine|pyridoxine|selenium|molybdenum|manganese|chromium"
    r"|zinc|copper|biotin|iodide|iodine|cyanocobalamin|folic acid|ascorbic|pantothen|phytonadione"
    r"|calciferol|carotene|lutein|pollen|extract|\broot\b|\bleaf\b|\bwhole\b|\boil\b|fluoride|\biron\b|ferrous"
    r"|^sodium chloride$|^water$|^dextrose|^potassium chloride$|^calcium carbonate$|^magnesium oxide$"
    r"|^oxygen$|^glycerin|^menthol$|^camphor|^alcohol$|^titanium dioxide$|^zinc oxide$"
    # electrolytes, minerals and IV-fluid components
    r"|^sodium bicarbonate$|^calcium$|^magnesium$|^potassium ion$|^sodium cation$|^glucose$|^lactate$|lactic acid"
    r"|^(magnesium|calcium|sodium|potassium) (sulfate|chloride|citrate|phosphate|carbonate|oxide|gluconate)"
    r"|tricalcium|citric acid"
    # excipients, skin-care bases and supplements
    r"|^ethanol$|^hyaluronate$|fish oil|omega-3|^benzalkonium|^dimethicone$|^petrolatum$|^melatonin$"
    r"|cobalamin|folate|ascorbate|glycol(?! 3350)|^lanolin|^mineral oil"
    # digestive-enzyme supplements
    r"|^protease$|^lipase$|^amylase$|^lactase$|^bromelain$|^papain$",
    re.I,
)

# Extra spellings labels use for an ingredient (keys: RxNorm ingredient names, lower case).
SYNONYMS = {
    "acetaminophen": ["paracetamol"],
    "aspirin": ["acetylsalicylic acid"],
    "levothyroxine": ["thyroxine"],
    "albuterol": ["salbutamol"],
    "epinephrine": ["adrenaline"],
    "cyclosporine": ["ciclosporin"],
    "valproic acid": ["valproate", "divalproex"],
}

SALT_WORDS = {
    "sodium", "potassium", "calcium", "magnesium", "hydrochloride", "hcl", "dihydrochloride", "hydrobromide",
    "sulfate", "bisulfate", "tartrate", "bitartrate", "succinate", "maleate", "besylate", "mesylate",
    "citrate", "acetate", "phosphate", "bromide", "fumarate", "hemifumarate", "dihydrate", "monohydrate",
    "trihydrate", "hydrate", "anhydrous", "nitrate", "malate", "lactate", "gluconate", "tosylate",
    "propionate", "dipropionate", "valerate", "xinafoate", "furoate", "pamoate", "benzoate", "hyclate",
}


def name_variants(ingredient, fda_names):
    """Lower-case spellings to search for in label text: the ingredient, synonyms, FDA names minus salts."""
    out = {ingredient} | set(SYNONYMS.get(ingredient, []))
    for n in fda_names:
        words = [w for w in n.lower().split() if w not in SALT_WORDS]
        if words:
            out.add(" ".join(words))
    return sorted(out, key=len, reverse=True)


# --------------------------------------------------------------------------- label mining
# Sentences matching these state that there is NO interaction, so their mentions are skipped.
NEGATION = re.compile(
    r"no (clinically )?(significant|relevant|meaningful|important) (drug )?(interaction|effect|change|difference)"
    r"|did not (significantly )?(alter|affect|change|increase|decrease|influence)"
    r"|no (pharmacokinetic |pharmacodynamic )?interactions? (was|were|has been|have been) (observed|seen|found|reported|identified)"
    r"|not (expected|likely|anticipated) to (interact|affect|alter)"
    r"|is not (expected|anticipated|likely) to"
    r"|no effect on the pharmacokinetics"
    r"|no dose adjustment( of [\w\- ]+)? is (necessary|needed|required|recommended)"
    r"|no (substantive|significant|meaningful|relevant|clinically \w+) (effect|change|interaction|difference)"
    r"|had no (substantive |significant |clinically \w+ |meaningful )?effect"
    r"|it is not known whether"
    r"|(revealed|showed|shown|demonstrated|found|had|has|have|with|produced|caused) no (\w+ ){0,3}effects?"
    r"|\d+(\.\d+)?\s?% (of (the )?patients )?(used|were (taking|receiving|treated))"
    r"|consult the label(ing)? of (the )?concomitantly used",
    re.I,
)

# Class phrase in label text -> (which openFDA class field, regex the class name must match).
CLASS_TERMS = [
    (r"\bnsaids?\b|non-?steroidal anti-?inflammatory", "epc", r"Nonsteroidal Anti-inflammatory"),
    (r"\banticoagulants?\b", "epc", r"Anticoagulant|Vitamin K Antagonist|Factor Xa Inhibitor|Thrombin Inhibitor"),
    (r"\bantiplatelet|platelet aggregation inhibitors?\b", "epc", r"Platelet Aggregation Inhibitor|P2Y12"),
    (r"\bssris?\b|selective serotonin reuptake inhibitors?", "epc", r"Serotonin Reuptake Inhibitor"),
    (r"\bsnris?\b|serotonin and norepinephrine reuptake inhibitors?", "epc", r"Norepinephrine Reuptake Inhibitor"),
    (r"\bmaois?\b|monoamine oxidase inhibitors?", "epc", r"Monoamine Oxidase Inhibitor"),
    (r"\bopioids?\b|\bopiates?\b", "epc", r"Opioid Agonist"),
    (r"\bbenzodiazepines?\b", "epc", r"Benzodiazepine"),
    (r"\bace inhibitors?\b|angiotensin[- ]converting enzyme inhibitors?", "epc", r"Angiotensin Converting Enzyme Inhibitor"),
    (r"angiotensin (ii )?receptor blockers?|\barbs\b", "epc", r"Angiotensin 2 Receptor Blocker"),
    (r"beta[- ]?(adrenergic )?blockers?|beta[- ]blocking agents?", "epc", r"beta-Adrenergic Blocker"),
    (r"\bthiazides?\b", "epc", r"Thiazide"),
    (r"loop diuretics?", "epc", r"Loop Diuretic"),
    (r"potassium[- ]sparing diuretics?", "epc", r"Potassium-sparing|Aldosterone Antagonist"),
    (r"\bcorticosteroids?\b", "epc", r"Corticosteroid"),
    (r"\bstatins?\b|hmg-?coa reductase inhibitors?", "epc", r"HMG-CoA Reductase Inhibitor"),
    (r"proton pump inhibitors?|\bppis?\b", "epc", r"Proton Pump Inhibitor"),
    (r"\bsulfonylureas?\b", "epc", r"Sulfonylurea"),
    (r"\binsulins?\b", "epc", r"Insulin"),
    (r"\bantipsychotics?\b", "epc", r"Antipsychotic"),
    (r"tricyclic antidepressants?|\btcas?\b", "epc", r"Tricyclic Antidepressant"),
    (r"strong cyp3a4? inhibitors?|cyp3a4? inhibitors?|inhibitors of cyp3a4?", "moa", r"Cytochrome P450 3A4? Inhibitors"),
    (r"cyp3a4? inducers?|inducers of cyp3a4?", "moa", r"Cytochrome P450 3A4? Inducers"),
    (r"cyp2c9 inhibitors?|inhibitors of cyp2c9", "moa", r"Cytochrome P450 2C9 Inhibitors"),
    (r"cyp2c19 inhibitors?|inhibitors of cyp2c19", "moa", r"Cytochrome P450 2C19 Inhibitors"),
    (r"cyp2d6 inhibitors?|inhibitors of cyp2d6", "moa", r"Cytochrome P450 2D6 Inhibitors"),
    (r"p-?glycoprotein (\(p-?gp\) )?inhibitors?|p-?gp inhibitors?", "moa", r"P-Glycoprotein Inhibitors"),
]


def label_classes(results):
    """Union of FDA classes over all single-ingredient labels returned (many generic labels carry none)."""
    epc, moa = set(), set()
    for r in results:
        of = r.get("openfda", {})
        if len(of.get("substance_name", [])) == 1:
            epc.update(of.get("pharm_class_epc", []))
            moa.update(of.get("pharm_class_moa", []))
    return {"epc": sorted(epc), "moa": sorted(moa)}


def pick_label(results):
    """Most recent single-ingredient label that has a drug-interactions section."""
    for r in sorted(results, key=lambda r: r.get("effective_time", "0"), reverse=True):
        if len(r.get("openfda", {}).get("substance_name", [])) == 1 and r.get("drug_interactions"):
            return r
    return None


def mine_labels(labels, patterns, classes):
    """Find label edges i -> j.

    labels:   {node_id: interactions text}
    patterns: {node_id: compiled regex matching that drug's names}
    classes:  {node_id: {"epc": [...], "moa": [...]}}  (from each drug's own label)
    Returns a list of dicts: from_id, to_id, via_name, via_class, class_terms, evidence.
    """
    def members(field, cls_regex):
        rx = re.compile(cls_regex, re.I)
        return {i for i, c in classes.items() if any(rx.search(x) for x in c.get(field, []))}

    class_members = [(re.compile(t, re.I), members(f, c)) for t, f, c in CLASS_TERMS]
    edges = {}
    for i, text in labels.items():
        for sentence in re.split(r"(?<=[.;])\s+", text):
            if NEGATION.search(sentence):
                continue
            for j, pat in patterns.items():
                if j != i and pat.search(sentence):
                    e = edges.setdefault((i, j), {"via_name": 0, "via_class": 0, "terms": set(), "evidence": sentence})
                    e["via_name"] = 1
            for term_rx, mem in class_members:
                m = term_rx.search(sentence)
                if not m or i in mem:          # a label naming its own class is describing itself
                    continue
                for j in mem - {i}:
                    e = edges.setdefault((i, j), {"via_name": 0, "via_class": 0, "terms": set(), "evidence": sentence})
                    e["via_class"] = 1
                    e["terms"].add(m.group(0).lower())
    return [{"from_id": i, "to_id": j, "via_name": e["via_name"], "via_class": e["via_class"],
             "class_terms": "|".join(sorted(e["terms"])),
             "evidence": re.sub(r"\s+", " ", e["evidence"])[:400]}
            for (i, j), e in sorted(edges.items())]
