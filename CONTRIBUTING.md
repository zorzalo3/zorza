# How to contribute?
Install all requirements and clone the repository.
Create zorza/localsettings.py and there add `DEBUG=True`.
Run the site locally with `python3 manage.py runserver`.
Create a branch with your changes and send a pull request.

# Requirements
* Python 3
* Django
* sassc

# Python style
* https://www.python.org/dev/peps/pep-0008/
* https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

# SCSS and HTML style
Classes should be lowercase with dashes between words, eg. `example-div`.

Make use of HTML5 tags like `<main>`, `<section>`.

Try not to use inline styling.

Use i18n (`{% load i18n %}` and `{% trans "string to translate" %}`).

```
$primary-color: #123456;
.class { // space before opening bracket on the same line
	font-family: "Roboto", sans-serif;
	// Prefer double quotes, put space after commas.
	// Don't have lines longer than 80 characters.
	// Use tabs for indentation.

	color: $primary-color;
	&:hover {
		text-decoration: underline;
	}
	// Make use of SCSS features like inheritance and variables.
}
```

# Translations
Extract strings to translate with `python3 manage.py makemessages -l <LANGUAGE_CODE>`.
Edit the strings in `locale/<LANGUAGE_CODE>`, then
`python3 manage.py compilemessages`.
Remember to set your `LANGUAGE_CODE` in settings.
