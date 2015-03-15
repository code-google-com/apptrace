# Tracking Memory Usage in Google App Engine Python Applications With Apptrace #



## Introduction ##

Python is a high-level, dynamic, interpreted programming language with
automatic memory management. This takes the burden off the programmer to
manually preallocate or deallocate memory as in languages such as C or C++. The
two mechanisms by which Python manages memory are called _reference counting_
and _garbage collection_. Thus, in most cases, developers don't have to look
out excessively for memory leaks in their applications.

Furthermore, Google App Engine guarantees that applications don't interfere
with the performance and reliability of other applications. Therefore,
processes will be torn down when their memory usage exceeds a distinct
threshold. The log entry for such a case usually looks like this: _Exceeded
soft memory limit with 201.52 MB after servicing 415 requests total_.

However, sloppy programming or a bad design can lead to leaky code, even with
Python. Besides a number of best practices, it can be extremely useful and
informative to keep track of the memory usage of an application.

The apptrace package provides a WSGI middleware for tracking memory usage in
Google App Engine Python applications.

Since apptrace is meant for development and debugging purposes only, it works
with the development appserver of the Google App Engine Python SDK and
TyphoonAE. It will definitely not work on the GAE production environment.

## Installation ##

The easiest way to install apptrace is (provided that you have setuptools
installed) to use `easy_install apptrace`. The apptrace package requires
[Guppy-PE](http://guppy-pe.sourceforge.net) to be installed on your PYTHONPATH.
It will be automatically pulled when you use `easy_install`.

You can also install and use apptrace by checking out the sources from the
repository and running the buildout:

```
  $ hg clone https://apptrace.googlecode.com/hg apptrace-dev
  $ cd apptrace-dev
  $ python bootstrap.py --distribute
  $ ./bin/buildout
```

Buildout takes care of everything, grabbing needed eggs like Guppy-PE and
installs it into an independent directory.

### Setting Up The Middleware ###

The apptrace package provides twofold components - the **WSGI middleware** and an
`apptracectl` command. The way how the WSGI middleware is installed does not
differ significantly from the way other middleware is installed in Google App
Engine Python applications. If not already present, create a file named
`appengine_config.py` in your application's root directory with the following
contents:

```
  def webapp_add_wsgi_middleware(app):
    from apptrace.middleware import apptrace_middleware
    return apptrace_middleware(app)
```

The `google.appengine.ext.webapp.util.run_wsgi_app()` method imports this file
and calls the `webapp_add_wsgi_middleware(app)` function, if found.

Next invoke `apptracectl init <application root directory>` to install the
apptrace package into your application root directory. This step is required.

### Configuring Apptrace ###

The apptrace middleware takes a number of options to specify which URLs and
modules should be traced. Let's have a look at the `appengine_config.py` file
for our [demo](http://code.google.com/p/apptrace/source/browse/#hg/demo)
guestbook application. (A slightly modified version of the guestbook demo from
the SDK.)

```
  apptrace_URL_PATTERNS  = ['^/$']
  apptrace_TRACE_MODULES = ['guestbook.py', 'handlers.py']

  def webapp_add_wsgi_middleware(app):
    from apptrace.middleware import apptrace_middleware
    return apptrace_middleware(app)
```

The `apptrace_URL_PATTERNS` option is a list of URL regex patterns to track.
Furthermore, we're interested in memory consumption of the modules specified in
`apptrace_TRACE_MODULES`.

## Running Apptrace ##

After successfully installing and configuring apptrace, we run the development
appserver as usual. Each time a URL matches one of the configured URL patterns,
apptrace traces the memory usage of the involved Python modules. Apptrace uses
the Memcache API to store records in JSON format. Here is an example of the
recorded data:

```
  {"index": 1, "entries": [{"obj_type": "WSGIApplication", "name": "application", "dominated_size": 1600,
                            "filename": "guestbook.py", "lineno": 24, "module_name": "guestbook"},
                           {"obj_type": "function", "name": "main", "dominated_size": 120,
                            "filename": "guestbook.py", "lineno": 30, "module_name": "guestbook"},
                           {"obj_type": "PropertiedClass", "name": "Greeting", "dominated_size": 5688,
                            "filename": "models.py", "lineno": 4, "module_name": "handlers"},
                           {"obj_type": "type", "name": "Guestbook", "dominated_size": 2120,
                            "filename": "handlers.py", "lineno": 37, "module_name": "handlers"},
                           {"obj_type": "type", "name": "MainPage", "dominated_size": 3112,
                            "filename": "handlers.py", "lineno": 10, "module_name": "handlers"}]}
```

Since these records are moderately human-readable, apptrace provides an
overview with two graphs showing the memory usage over a number of requests.
For making the overview accessible, add the following URL handler to your
`app.yaml` file:

```
  - url: /_ah/apptrace.*
    script: apptrace/overview.py
```

Now, use a web browser to navigate to the following URL:

> http://localhost:8080/_ah/apptrace

<img src='http://wiki.apptrace.googlecode.com/hg/overview.jpg' alt='Apptrace Overview' />

The example above shows that the memory usage of the `MainPage` object tends to
grow over a number of requests. This is very likely caused by a memory leak.

By clicking the `MainPage` object apptrace shows a simple code browser with a
marker pointing to a suspicious code block.

<img src='http://wiki.apptrace.googlecode.com/hg/codebrowser.jpg' alt='Apptrace Code Browser' />