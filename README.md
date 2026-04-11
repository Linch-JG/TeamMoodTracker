# Team Mood Tracker

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

The Streamlit dashboard include a small external well-being tip widget supported by the FastAPI backend.

Run only the API:

```bash
make api
```

Run only the submission UI:

```bash
make frontend
```

Run tests:

```bash
make test
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
