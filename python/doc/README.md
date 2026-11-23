# Reading the Python implementation — a lesson

This folder is a guided lesson on how the Python code of *SMARTest AI Testbook* is
structured. It is written for students who know basic Python and object-oriented
programming, but have never seen this project or FastAPI before.

The goal is not to describe every line, but to understand **why the code is split
the way it is** and to recognise three ideas that appear everywhere:

1. **The domain is independent.** The classes that describe tests, runs and
   evaluations do not know anything about the web, the database or OpenAI.
2. **Dependencies are injected.** Objects do not create their collaborators; they
   receive them from outside, from one single place.
3. **Design patterns solve recurring problems.** Builder, Strategy, Adapter and
   Repository each have a precise job in the code.

## Lesson plan

| # | Chapter | What you will learn |
|---|---|---|
| 1 | [The big picture](01-architecture.md) | What the application does, its packages and the direction of dependencies. |
| 2 | [Domain independence](02-domain-independence.md) | Why the domain does not import FastAPI, SQLAlchemy or OpenAI, and how this is achieved. |
| 3 | [Dependency injection](03-dependency-injection.md) | How `composition.py` builds and connects every object, and why tests benefit. |
| 4 | [Design patterns](04-design-patterns.md) | Builder, Strategy, Adapter, Repository and the other patterns in the code. |
| 5 | [Order of execution](05-execution-order.md) | What happens, step by step, from `python -m smartest_ai_testbook` to a finished evaluation run. |
| 6 | [How to read the code](06-reading-guide.md) | A suggested reading order, exercises and review questions. |

Read the chapters in order: each one builds on the previous.

## Appendices

Short references on the two libraries used by the infrastructure, explained through this project's code:

| | Appendix | What you will learn |
|---|---|---|
| A | [FastAPI](07-fastapi.md) | Routes, input validation with Pydantic, responses and errors, CORS, `async`, testing. |
| B | [SQLAlchemy](08-sqlalchemy.md) | Engine, tables as classes, sessions and transactions, the repository operations, row ↔ domain conversion. |

## Prerequisites

- Python classes, inheritance and type hints.
- The idea of an *interface* (a list of methods a class promises to provide).
- `async` / `await` at a basic level (chapter 5 reminds you what is needed).

## Related documents

- [Domain design](../../doc/domain-design.md): the official class diagram and responsibilities, shared with the TypeScript version.
- [Glossary](../../doc/glossary.md): the meaning of every domain term (suite, expectation, evaluator, run…).
- [Web architecture](../../doc/web-architecture.md): how servers, client and API contract fit together.
- [Python readme](../readme.md): how to install, run and test the code.
