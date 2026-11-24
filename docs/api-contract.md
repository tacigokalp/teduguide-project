# API contract (v0.2 DRAFT, in review)

**Status:** DRAFT for step S-02, written by Taci with Claude. It is final only when Taci, Fatima and Elif have all approved it (see section 4).

**What this file is.** The app (frontend) and the server (backend) talk to each other by sending requests. This file is the written list of **every request** and **what comes back**. If everybody follows it, the three of us can work at the same time without waiting for each other. If someone needs a change, change **this file first**, then tell the others.

## 0. How to read this file (read this first)

| Word | Plain meaning |
|---|---|
| **Endpoint** | One address on the server, for one job. Like `/api/v1/health`. |
| **GET** | "Give me information." Like opening a web page. You send nothing big, you just get an answer. |
| **POST** | "Here is some information, give me an answer." You send a small package (JSON), you get a package back. |
| **JSON** | A way to write data as text, for example `{"floor": 2, "code": "D232"}`. Curly braces `{ }` = one thing with named fields. Square brackets `[ ]` = a list of things. |
| **Request / Response** | What you send / what you get back. |
| **Location** | **One room or place** on campus (a classroom, an office, a toilet, a lab). Its fields are written in section 1. |
| **Person** | One staff member, for example Prof. Çapın, with the room where they sit. |

Example of a list: `[Location, Location]` means "a list with two rooms in it".

## 1. The things we send around

**Location** (one room or place):
```json
{
  "locationId": 123,
  "code": "D232",
  "name": "Classroom D232",
  "type": "classroom",
  "building": "D",
  "floor": 2,
  "x": 14.2,
  "y": 7.9,
  "accessible": true
}
```
- `code` is the room number. `type` is `classroom`, `office`, `lab`, `wc` and so on.
- `x` and `y` are metres on the floor plan (origin bottom-left, y goes up). Floor numbers are integers: ground floor `0`, the roof is `5`.

**Origin** (where the user is now). The phone sends **one** of these:
- `{"nodeId": 8841}`: a point of our walking map (best choice: no coordinates leave the phone).
- `{"locationId": 123}`: the user picked a room from the list as the starting point.
- `null`: we do not know where the user is.

**Errors** always look the same, with an HTTP status number:
```json
{"error": {"code": "ROUTE_NOT_FOUND", "message": "No route found.", "details": {}}}
```
Codes: `VALIDATION_ERROR` (400, wrong request), `UNAUTHORIZED` (401, not logged in), `FORBIDDEN` (403, no permission), `NOT_FOUND` (404), `ROUTE_NOT_FOUND` (404), `NO_ACCESSIBLE_ROUTE` (409), `GRAPH_VERSION_MISMATCH` (409), `RATE_LIMITED` (429), `INTERNAL_ERROR` (500).

**General rules:** all addresses start with `/api/v1`. Data is JSON. Field names are written like `locationId` (camelCase). Only the `/admin/...` addresses need a login token; everyone else (guests) needs no login. The server **never saves or logs** a user's position or question.

## 2. The endpoints

### 2.1 Is the server alive?
`GET /api/v1/health`
- You send: nothing.
- You get: `{"status": "ok", "version": "0.1.0", "db": "ok"}`
- Used by: hosting, the demo-day check.

### 2.2 Search for a room or a person
`GET /api/v1/locations/search?q=capin`
- `q` is the text the user typed. It also finds `Çapın` when you type `capin` (Turkish letters are ignored).
- Optional: `&type=classroom`, `&building=D`, `&limit=10` (maximum results).
- You get **a list of Locations**, best match first:
```json
[{"locationId": 123, "code": "D232", "name": "Classroom D232", "type": "classroom", "building": "D", "floor": 2, "x": 14.2, "y": 7.9, "accessible": true}]
```
- Examples to try: `d232` (room code), `capin` (person), `library` (whole word).

`GET /api/v1/locations/{id}` → one Location (use the `locationId`).
`GET /api/v1/people/{id}` → one Person.

### 2.3 Ask a question in normal language
`POST /api/v1/query`
- You send:
```json
{"text": "Where is D232?", "lang": "auto", "accessible": false, "origin": {"nodeId": 8841}}
```
  `lang` is `auto`, `en` or `tr`. `accessible: true` means "step-free route only". `origin` is where the user is (section 1), or `null`.
- You get:
```json
{
  "intent": "navigate",
  "parsedBy": "fastpath",
  "verified": true,
  "answer": {"text": "D232 is Classroom D232, Block D, floor 2.", "textTr": "D232, D Blok 2. kattaki sınıftır."},
  "results": [ {"locationId": 123, "code": "D232", "name": "Classroom D232", "floor": 2} ],
  "clarification": null,
  "route": null
}
```
- `intent` is what the user wants: `navigate`, `locate`, `query_hours`, `find_person`, `general_info` or `unknown`.
- `parsedBy` is how we understood it: `fastpath` (exact room code, no AI), `llm` (OpenAI), `rules` (simple rules when OpenAI is down).
- `verified` is `true` only when every room or person in the answer **exists in our database**. The answer text is built from templates, the AI never writes it.
- `clarification` is `null`, or a question with up to 3 options when the text is unclear.
- `route` is `null`, or a Route (section 2.4) when the user wants to go somewhere and we know where they are.

### 2.4 Get a walking route
`POST /api/v1/route`
- You send:
```json
{"from": {"nodeId": 8841}, "to": {"locationId": 123}, "accessible": false}
```
- You get a **Route**:
```json
{
  "distanceM": 42.0,
  "etaSec": 70,
  "floorsInvolved": [0, 1, 2],
  "steps": [
    {"index": 0, "type": "walk", "text": "Head north 18 m", "textTr": "18 m kuzeye ilerleyin",
     "distanceM": 18, "floor": 0, "turn": null, "polyline": [[12.4, 3.1], [12.4, 21.1]]}
  ]
}
```
- `steps` is the list of instructions. `type` is `walk`, `stairs`, `elevator`, `turn` or `arrive`. `turn` is `left`, `right`, `straight` or `null`. `polyline` is the line to draw on the map (a list of `[x, y]` points).
- Errors: `404 ROUTE_NOT_FOUND` (no way there), `409 NO_ACCESSIBLE_ROUTE` (no step-free way; the standard route is suggested).
- Why POST and not GET: so a position never shows up in a web address or a log.

### 2.5 Floor plans and the walking map
- `GET /api/v1/buildings` → list of buildings, e.g. `[{"code": "D", "name": "D Block", "floors": [0, 1, 2, 3]}]`.
- `GET /api/v1/buildings/D/floors` → the floors of block D with the picture to draw: `[{"floor": 2, "svgUrl": "...", "widthM": 60.0, "heightM": 30.0}]`.
- `GET /api/v1/buildings/D/nav-graph` → the **walking map** (points and the lines between them) that the phone downloads once. The server also sends a version tag (`ETag`) so the phone does not download it again if nothing changed.
- `GET /api/v1/buildings/D/radio-map` → the WiFi fingerprint file the phone uses to find its position (same `ETag` idea).

### 2.6 Admin (login needed)
Two roles: **editor** (rooms, people, hours) and **admin** (everything).

| Address | Method | Who | What |
|---|---|---|---|
| `/admin/login` | POST | anyone | log in, get a token (max 5 tries per minute) |
| `/admin/locations` | GET, POST | editor | list rooms, add a room |
| `/admin/locations/{id}` | PUT, DELETE | editor | change or delete a room |
| `/admin/people/{id}` | PUT | editor | change a person |
| `/admin/hours/{locationId}` | PUT | editor | change opening hours |
| `/admin/graph/import` | POST | admin | load a new walking map |
| `/admin/recalibrate` | POST | admin | build and publish a new WiFi map |
| `/admin/audit` | GET | admin | who changed what and when |

Every change is saved in an audit log. No token → `401`. Wrong role → `403`. (The full list is in Project.md §10.4; we add details when we build each one.)

## 3. Who builds what

| Part | Owner |
|---|---|
| Endpoints, database, routing, admin, putting the app online | **Taci** |
| Screens, floor-plan map, calling the endpoints, mock server | **Fatima** |
| Understanding the question, checking answers, WiFi position | **Elif** |

Until the real server exists, Fatima uses a **mock server**: a fake server that returns the examples in this file.

## 4. Decisions (made by Taci on 24.11.2026; Fatima and Elif can change them by pull request)

1. **The one call between Taci and Elif (step S-11).** Elif writes **one** Python function that takes the question and returns the answer fields of `/query`: `answer_query(text, lang, accessible, origin)` in `backend/app/nlp/service.py`. Taci's `/query` endpoint only calls it and adds the `route`.
2. **Names:** `camelCase` in JSON (like `locationId`), `snake_case` inside Python code.
3. **Floors:** the ground floor of D block is `0`. *Fatima: please check this against your floor plans and tell us if it is different.*
4. **Floor-plan pictures:** the server hands out the SVG files Fatima's tool creates; the files live in `data/` and the endpoint `GET /buildings/D/floors` gives their address.
5. **Walking-map version check (`graphVersion`):** left out for now, added later in step A-21.
6. **Changing this file:** by pull request; at least one other person approves.

**Review:** this file is merged into `main` as a draft so that everybody can read it in the repo. Fatima and Elif: please read it. If something is wrong or missing, change it in a branch and open a pull request. When both of you have said "approved" in the group chat, we change "DRAFT" at the top to "v1.0".
