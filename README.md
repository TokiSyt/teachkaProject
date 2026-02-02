# Teachka

A web app hub built for teachers. Manage your classes, track participation, calculate grades, and more — all in one place.

**Link to project:** https://teachka.com

## How It's Made

**Tech used:** Python, Django, PostgreSQL, Tailwind CSS

Teachka follows a modular architecture where each tool is its own Django app. They all share a core module for common functionality like user authentication and base models. This makes it easy to add new tools without touching existing ones.

The app uses a service/selector pattern to keep business logic out of views — selectors handle database queries with proper optimization, while services handle the actual operations. Groups created in one tool automatically sync to others through Django signals.

## Optimizations

- Queries are optimized with `select_related` and `prefetch_related` to minimize database hits
- Static files are compressed and served efficiently in production
- The modular structure means each tool only loads what it needs

## Lessons Learned

Building this taught me a lot about structuring larger Django projects. Initially everything was tightly coupled, but refactoring into separate apps with a shared core made the codebase much cleaner and testable. Setting up proper CI/CD also forced me to write better tests and catch issues before they hit production.

I also gained hands-on experience with deployment — configuring production settings, managing environment variables, and setting up the infrastructure to serve the app reliably. On the git side, I learned the importance of proper branch organization, meaningful commits, and keeping a clean history through rebasing and squashing.
