# TEDU Guide

Indoor navigation web app for TED University (CMPE 491/492 senior design project).
A user asks "Where is D232?" in Turkish or English. The app understands the question,
finds the user's position inside the building, computes a walking route and draws it on the floor plan.

Team: Taci Furkan Gökalp (backend, routing), Fatima Nasir Muhammad (frontend, floor plans), Elif Nazlı Özer (NLP, WiFi positioning).
Website and reports: https://tedu-guide.vercel.app

## Folders
| Folder | Content |
|---|---|
| `backend/` | FastAPI server, database, route engine |
| `frontend/` | React web app |
| `data/` | floor plans, navigation graph, WiFi fingerprints |
| `tools/` | scripts (PDF to SVG, seed, graph check) |
| `collector/` | Android WiFi collector |
| `docs/` | API contract, backlog, notes |

## How to run
Coming soon (see `docs/`).

## Working rules
- Never commit `.env` or any key or password. Copy `.env.example` to `.env`.
- Work on a branch (`feat/<area>-<topic>`), open a Pull Request, get one approval.
- Commit messages: `feat:`, `fix:`, `docs:`, `test:`.
