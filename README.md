# Team Mood Tracker

A lightweight internal tool for agile teams to monitor collective well-being through mood tracking and analytics.

## Quick Start

Install dependencies:

```bash
make install
```

Run the backend and frontend together:

```bash
make run
```

The app will be available at:

- FastAPI: `http://127.0.0.1:8000`
- Streamlit: `http://127.0.0.1:8501`
- OpenAPI Docs: `http://127.0.0.1:8000/docs`

## Mood History Management API

New endpoints for managing mood entry history:

- **GET /mood-entries** - List mood entries with optional filtering and sorting
  - Query parameters: `user`, `date_from`, `date_to`, `sort_by` (date/rating), `order` (asc/desc)
  - Example: `/mood-entries?user=Alice&sort_by=rating&order=desc`
- **GET /mood-entries/{id}** - Retrieve a specific mood entry by ID
- **PUT /mood-entries/{id}** - Update an existing mood entry (partial updates supported)
- **DELETE /mood-entries/{id}** - Delete a mood entry

Full API documentation is available at `/docs` when the server is running.

## Development

Run only the API:

```bash
make api
```

Run only the frontend:

```bash
make frontend
```

Run tests:

```bash
make test
```

Run tests with coverage:

```bash
make coverage
```

Generate HTML coverage report:

```bash
make coverage-html
```

Run quality checks:

```bash
make security
make audit
make load-test
```

Remove local caches:

```bash
make clean
```

## Coverage Quality Gate

This project maintains **>= 80% code coverage** (currently at 80.28%).

Coverage is enforced in CI and can be checked locally:

```bash
make coverage
```

Coverage reports are generated in `htmlcov/` directory with:

```bash
make coverage-html
```

The coverage gate ensures:
- All new code is properly tested
- Existing functionality remains covered
- Quality standards are maintained across the project
