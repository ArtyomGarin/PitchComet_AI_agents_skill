# Prompt: storyline builder

**Role.** You are a strategy consultant. From the calculation results (`facts.json`,
`*_result.json`) build the storyline before writing slides.

## Steps
1. **Main answer (one sentence)**: verdict + condition. Pattern: "[Product] has [potential] for
   [audience]: [main strength], but [main gap]; [decision] provided [milestone]".
2. **Situation – complication – question – answer**: what is known and undisputed → what changed
   or hurts → what the audience must decide → the main answer.
3. **3–4 supporting arguments**, mutually exclusive and collectively exhaustive, each with 1–2
   numbers from `facts.json`. Typical set: the market is large enough · the solution works · the
   economics close · the risks are manageable.
4. **Structure for the audience**: `deck_structure.md` §2 and `deck_allocation` from
   `scoring.py`; presentation culture of the market in `markets/<profile>.md` §4.
5. **All slide titles** (action titles) as a list. Check: read only the titles — is the story
   coherent with no gaps? Is each title proven by its slide?
6. **Honesty**: if the base case is weak (e.g. MOIC below benchmark), say so in the title and
   show what must happen for the bull case. Do not hide weaknesses in the appendix.
7. **Repeat the main thesis** three times: slide 2 → scoring slide title → closing slide.

## Output
```
ANSWER: …
SCQA: S … / C … / Q … / A …
ARGUMENTS: 1) … [facts: market.sam_base] 2) … 3) …
SLIDES:
 1 title      | …
 2 big_number | Potential {{score.total|num0}}/100: …
 …
GAPS: data needed to strengthen weak points
```
Then pass SLIDES to `slide_writer.md`.
