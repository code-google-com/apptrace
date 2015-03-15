The apptrace package provides a WSGI middleware for tracking memory usage in Google App Engine Python applications.

Since apptrace is meant for development and debugging purposes only, it works with the development appserver of the [Google App Engine](http://code.google.com/appengine) Python SDK and [TyphoonAE](http://typhoonae.googlecode.com). **It will definitely not work on the GAE production environment**.

Apptrace utilizes [Heapy](http://guppy-pe.sourceforge.net/) for gathering object related data like their memory
footprint or relationship to other objects. Parts of the UI are built with [Flot](http://code.google.com/p/flot).

Please read the brief [usage guide](http://code.google.com/p/apptrace/wiki/UsingApptrace).

![http://wiki.apptrace.googlecode.com/hg/apptrace.jpg](http://wiki.apptrace.googlecode.com/hg/apptrace.jpg)

### Python Package Index ###

The apptrace package is also released [here](http://pypi.python.org/pypi/apptrace).