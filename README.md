## Compilation, Testing, and Deployment Summary

LearnPath is a Django-based web application written in Python, so there is no traditional compilation step. Rather the procedure is simple — install the dependencies and set up the database.

### Setting Up the Project

To get started, install all dependencies by running:

```bash
python -m pip install -r requirements.txt
```

Once dependencies are installed, apply the database migrations to create the needed tables:

```bash
python manage.py migrate
```

For local development, the built-in Django development server can then be started with:

```bash
python manage.py runserver
```

The application will be accessible at `http://127.0.0.1:8000/` by default. One thing to be kept in mind is that it is not for production use.

### Testing

LearnPath uses Django's built-in test framework. To run the full test suite:

```bash
python manage.py test
```

To run tests only for the main app:

```bash
python manage.py test core
```

The tests cover models, forms, views, and the topic detail functionality. This ensures that nothing which is not working properly does not get pushed into the main repository.

### Deployment

There are two supported ways to deploy the application.

#### Docker (Containerized Deployment)

The project includes a `Dockerfile` and `docker-compose.yml` for containerized deployment. To build and run the application:

```bash
docker compose up --build
```

The container automatically runs migrations on startup and serves the application using Gunicorn, which is a production-grade WSGI server suited for handling real traffic unlike the development server.

#### Render (Hosted Deployment)

The project also includes a `render.yaml` configuration file for deploying directly to Render using Docker. Before deploying, make sure you update the following environment variables so that it works:

- `DJANGO_ALLOWED_HOSTS` — the domain(s) your app will be served from
- `DJANGO_CSRF_TRUSTED_ORIGINS` — required for form submissions to work correctly in production

### Database

The project currently uses SQLite as its database. SQLite works fine for small to medium deployments, but if the application needs to scale or handle concurrent writes under heavy load, migrating to a dedicated database like PostgreSQL would be worth considering.
