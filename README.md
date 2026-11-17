# Reformed Quizzes

Interactive quizzes on Reformed confessions and doctrine. One static page, no server needed.

- `index.html#dort` – Canons of Dort (20 core questions, Heads I–V in order)
- `index.html#wcf` – Westminster Confession of Faith (20 core questions, chapters 1–29 in order)
- `index.html#systematic` – Reformed systematic theology (20 core questions, prolegomena to last things)

The `dort/`, `wcf/` and `systematic/` folders only redirect to those links.

## AI rounds

In the Claude artifact version, a reader can ask Claude for 10 new questions after any quiz. The page sends Claude every question the reader has already seen in that browser, and it also removes any near-duplicate itself, so no question repeats. This uses the reader's own Claude account. On GitHub Pages there is no Claude access, so the AI button stays hidden.

## Edit or add questions

Core questions live in `_build/data_*.py`. The page design and the AI prompt live in `_build/app_template.html`. After you edit them, run:

```bash
python3 _build/build.py
```

The build checks that correct answers are spread evenly across A–D and that no correct answer is much longer than its wrong options. It writes `index.html` for GitHub and `_build/_artifact_app.html` for the Claude artifact.
