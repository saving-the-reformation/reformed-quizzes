"""Build the Reformed quiz site.

Run:  python3 _build/build.py   (from the "Reformed quizzes site" folder)

Writes:
  index.html                 the whole site (hub + all quizzes) for GitHub Pages
  dort/, wcf/, systematic/   short redirect pages to index.html#<slug>
  _build/_artifact_app.html  the same app as page content for the Claude artifact
                             (AI rounds work only there, through the `sample` capability)
"""
import html, json, os, re, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QUIZ_FILES = ["data_dort", "data_wcf", "data_st"]

# What the AI round needs to know about each quiz.
META = {
    "dort": {
        "short": "the Canons of Dort",
        "scope": "The Canons of Dort (1618-19): the five heads of doctrine with their articles and Rejection of Errors, and the history of the Synod and the Remonstrant controversy.",
        "orderNote": "Head I, Head II, Heads III/IV, Head V",
        "ground": "",
        "quoteRule": "The CRCNA Dort translation is under copyright, so AI questions paraphrase it and never quote it.",
        "citeForm": "'Canons of Dort II.5' or 'Canons of Dort, Rejection of Errors III/IV.2'",
        "tagForm": "the head and article, for example 'Head II · Art. 5' or 'Head V · RE 3'",
    },
    "wcf": {
        "short": "the Westminster Confession of Faith",
        "scope": "The Westminster Confession of Faith (1646), chapters 1-33. You may also use the Larger and Shorter Catechisms where they explain a chapter.",
        "orderNote": "chapter order, 1 to 33",
        "ground": "wcf",
        "quoteRule": "Claude gets the full Westminster Confession text, and the page checks every quotation against it word for word.",
        "citeForm": "'WCF 11.1' (or 'WLC 72' for the Larger Catechism)",
        "tagForm": "the chapter number and title, for example 'Ch. 11 · Justification'",
    },
    "systematic": {
        "short": "Reformed systematic theology",
        "scope": "Reformed systematic theology across the classic loci: Prolegomena, Doctrine of God, Anthropology, Christology, Soteriology, Ecclesiology, Eschatology. Ground every answer in the Reformed confessions (WCF, Westminster catechisms, Heidelberg Catechism, Belgic Confession, Canons of Dort) or standard Reformed dogmaticians (Calvin, Turretin, Bavinck, Berkhof, Hodge, Vos).",
        "orderNote": "locus order: Prolegomena, Doctrine of God, Anthropology, Christology, Soteriology, Ecclesiology, Eschatology; cover at least five loci",
        "ground": "wcf",
        "quoteRule": "Quotations are allowed only from the Westminster Confession and Larger Catechism, and the page checks each one word for word.",
        "citeForm": "'WCF 8.2', 'WLC 50', 'Heidelberg Catechism Q. 21', or the author and work (leave out chapter or page numbers you are not sure of)",
        "tagForm": "the locus name, for example 'Christology'",
    },
}


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.QUIZ


def audit(quiz):
    seq, qs = quiz["seq"], quiz["questions"]
    problems = []
    if len(seq) != len(qs):
        problems.append(f"seq length {len(seq)} != {len(qs)} questions")
    counts = {k: seq.count(k) for k in "ABCD"}
    if max(counts.values()) - min(counts.values()) > 1:
        problems.append(f"uneven positions {counts}")
    if re.search(r"(.)\1\1", seq):
        problems.append("3+ consecutive same position")
    longest = 0
    for i, q in enumerate(qs, 1):
        wc = len(q["a"].split())
        dw = [len(d.split()) for d in q["d"]]
        if wc > max(dw):
            longest += 1
        if wc > max(dw) * 1.15:
            problems.append(f"Q{i}: correct option conspicuously long ({wc} vs {dw})")
        if len(q["d"]) != 3:
            problems.append(f"Q{i}: needs 3 distractors")
    print(f"  {quiz['slug']}: positions {counts}, correct strictly longest in {longest}/{len(qs)}")
    return problems


def to_data(quiz):
    out = []
    for q, pos in zip(quiz["questions"], quiz["seq"]):
        texts = list(q["d"])
        texts.insert("ABCD".index(pos), q["a"])
        out.append({
            "tag": q["tag"], "q": q["q"],
            "options": [{"text": t, "key": k} for t, k in zip(texts, "ABCD")],
            "correct": pos, "source": q["src"], "sourceUrl": q["url"], "explanation": q["ex"],
        })
    d = {"title": quiz["title"], "subtitle": quiz["subtitle"], "description": quiz["description"], "questions": out}
    d.update(META[quiz["slug"]])
    return d


def main():
    quizzes = [load(n) for n in QUIZ_FILES]
    print("Audit:")
    bad = []
    for q in quizzes:
        bad += [f"{q['slug']}: {p}" for p in audit(q)]
    for p in bad:
        print("  !", p)

    data = json.dumps({q["slug"]: to_data(q) for q in quizzes}, ensure_ascii=False, indent=1).replace("</", "<\\/")
    texts = {k: open(os.path.join(HERE, "texts", k + ".txt"), encoding="utf-8").read() for k in ("wcf", "wlc")}
    texts_js = json.dumps(texts, ensure_ascii=False).replace("</", "<\\/")
    body = (open(os.path.join(HERE, "app_template.html"), encoding="utf-8").read()
            .replace("__DATA__", data).replace("__TEXTS__", texts_js))

    # Claude artifact: page content only (the platform adds the document skeleton).
    with open(os.path.join(HERE, "_artifact_app.html"), "w", encoding="utf-8") as f:
        f.write(body)

    # GitHub Pages: a full document with the head parts moved into <head>.
    head_bits = re.findall(r"(<title>.*?</title>|<meta [^>]*>|<link [^>]*>|<style>.*?</style>)", body, re.S)
    rest = body
    for b in head_bits:
        rest = rest.replace(b, "", 1)
    full = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + "\n".join(head_bits) + "\n</head>\n<body>\n" + rest.strip() + "\n</body>\n</html>\n")
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(full)

    # Short links such as /dort/ redirect to the app.
    for q in quizzes:
        d = os.path.join(ROOT, q["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">'
                    f'<title>{html.escape(q["title"])}</title>'
                    f'<meta http-equiv="refresh" content="0; url=../index.html#{q["slug"]}">'
                    f'<link rel="canonical" href="../index.html#{q["slug"]}"></head>'
                    f'<body><p><a href="../index.html#{q["slug"]}">Open the {html.escape(q["title"])} quiz</a></p></body></html>\n')

    print("Built index.html, redirects, and _build/_artifact_app.html")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
