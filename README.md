# Zorza

## About
An information service for schools with an advanced timetable interface

## Setup
Install Django 2.0 or later and Python 3.4 or later.
For that, using Python virtual environments is recommended.

Now you can `git clone` the repository.
You will need to create a `zorza/localsettings.py` file and set `DEBUG`,
`SECRET_KEY`, `LANGUAGE_CODE`, `TIME_ZONE`.
`python3 ./manage.py runserver` will start a debug server.
Migrations may be necessary.

For a production setup, see
https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/
and
https://docs.djangoproject.com/en/2.0/howto/deployment/
.

## License
This project is licensed under GPLv3.

## Contributing
See CONTRIBUTING.md
