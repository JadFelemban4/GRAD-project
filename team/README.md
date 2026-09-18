# team/ — one profile per person, so the assistant knows who it is talking to

Five people share this repository and they do not share a background. One is
comfortable with engines and lost in reinforcement learning; another is the
reverse. An explanation pitched at the wrong person wastes both their time, and
the assistant has no way to guess.

So each of us keeps a file here. **It is about how to work with you, not about
how good you are.**

---

## How the assistant picks the right one

At the start of a session it reads the email git is configured with:

```bash
git config user.email
```

and opens the profile in this folder whose `email:` line matches. If none
matches, it asks once and carries on without one.

**That works because git config is per clone.** You set yours once, on your own
machine, and it never has to be agreed with anyone:

```bash
git config user.name  "Your Name"
git config user.email "you@example.com"
```

No `--global`, so it applies to this repository only.

---

## Adding yourself · about ten minutes

1. `cp team/_TEMPLATE.md team/<yourname>.md`
2. Fill it in. Write it for a stranger who will read it once and then act on it.
3. Commit it.

**Write the awkward parts.** A profile that says "I understand everything" is a
profile that gets you explanations you cannot use. The one thing that makes
these files worth keeping is that they say where the gaps are, and the gaps are
not a judgement — five undergraduates cannot each know combustion, control
theory, reinforcement learning and statistics.

---

## What belongs here, and what does not

**Here:** what to assume you know and what not to; how you like to be explained
to; which language; what you have already worked through; what you are
responsible for; corrections you have had to repeat.

**Not here:** grades, opinions about each other, anything you would not want a
supervisor to read. **This folder is committed and pushed** — treat it as
public to the team and to anyone the repository is shown to.

---

## Keep it current, and say when you last did

A profile that says "I do not know what lambda is" six months after you learned
it is worse than no profile, because it steers every explanation you get. Put
the date on anything that will age, and cross it out when it stops being true
rather than deleting it — the record of what you learned is useful to the
person who writes the thesis chapter about the team.
