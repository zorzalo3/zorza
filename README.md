# Zorza
(/'zɔʐa/ ZAW-zha - Polish for *aurora*)  
An informational website for schools with an advanced timetable interface.

<p style="float: left">
<img src="https://user-images.githubusercontent.com/35867657/50306538-c6940500-048d-11e9-92c7-30e17ef75930.png" height="390px">
<img src="https://user-images.githubusercontent.com/35867657/50116506-4a59b180-0242-11e9-8762-03b7207a20dc.png" height="390px">
<img src="https://user-images.githubusercontent.com/35867657/50116513-4e85cf00-0242-11e9-8049-800552640229.png" height="390px">
</p>

* View class, group, teacher, classroom timetables
* Set a default timetable for easy repeated access
* Find out about upcoming schedule changes, cancelled lessons and teacher substitutions
* Fast experience - minimal use of JavaScript and good caching
* No registration - everything works without user accounts
* Use on any device - fully responsive design
* Check which classrooms are occupied at a given time
* Access school documents and files quickly
* *Not* a [student information system](https://en.wikipedia.org/wiki/Student_information_system), but can be complementary to one
* See remaining break time and substitutions also on a publicly installed screen

## Setup
Install Python 3.5 or later and set up a Python virtual environment, then
install Django 2.2.28 or later (you can use `pip install -r requirements.txt`).

Now you can `git clone` the repository.
You will need to create a `zorza/localsettings.py` file and set `DEBUG`,
`SECRET_KEY`, `LANGUAGE_CODE`, `TIME_ZONE`.

The root (`/`) url is an alias for `/pages/home/`, which is a [Django flatpage](https://docs.djangoproject.com/en/2.2/ref/contrib/flatpages/). Create a flatpage with the URL `/home/` in Django administration (`/admin/`), otherwise you will get a 404. You have to create an account first with `./manage.py createsuperuser`.
In the footer there is a link to the flatpage with URL `/about/`.

Populating the timetable database should be done by scripts. The [`zorza_scripts`](https://github.com/zorzalo3/zorza_scripts) repository is a collection of scripts for importing timetables generated by aSc TimeTables and tailoring the database for a specific usecase.

Very basic example timetable and flatpage data can be loaded by `./manage.py loaddata fixtures/demo.json`.

For a production setup, consult
https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/
and
https://docs.djangoproject.com/en/2.2/howto/deployment/
.

The directories `mediafiles`, `staticfiles`, and favicons have to be served directly by the web server. Example nginx configuration for that:

```
	location /media  {
		alias /sites/zorza/mediafiles;
	}
	location /static {
		alias /sites/zorza/staticfiles;
	}
	location ~ ^/(android|apple-touch-icon|browserconfig|favicon|manifest|safari)(.*)\.(png|xml|ico|json|svg)$ {
		root /sites/zorza/staticfiles/favicons;
	}
```

This software is designed with response caching in mind because the content is mostly static and by nature not requiring urgent updates. Set `CACHE_MIDDLEWARE_SECONDS` in `localsettings.py` and configure your web server for response caching.

The page `/timetable/display/` displays remaining break/period time and teacher substitutions. It's intended to be run fullscreen in a browser on a public big screen.
Use browser zoom to make it look right.

## Administration
Custom admin commands (see `./manage.py COMMAND --help`):
* `uploaddir` - uploads a directory of files to a category
* `cleanup` - removes old substitutions etc.

To access substitution editing forms or the calendar (DayPlan formset) the user needs the `add_substitution` or `add_dayplan` permission respectively.
To access Django Admin `is_staff` is needed, as is normal with Django.

After timetable changes or group changes in real world, such that teacher/class/group ids saved in the default timetable cookie correspond to a different thing than before, you must increment/add the integer `TIMETABLE_VERSION` in `localsettings.py`. Otherwise you risk default timetables being wrong or 404s.

## License and credits
This project is licensed under AGPLv3.

The header image is a modified photograph by [Simo "Ximonic" Räsänen](https://commons.wikimedia.org/wiki/File:Aurora_borealis_above_Lyngenfjorden,_2012_March.jpg) and is available under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/deed.en).

The logo font is [Raleway](https://github.com/impallari/Raleway/).

This project includes [medium-editor](https://github.com/yabwe/medium-editor/) by Davi Ferreira (http://www.daviferreira.com) licensed under the MIT license.

## Contributing
See CONTRIBUTING.md
