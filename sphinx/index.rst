**********************************
Integreat Django CMS documentation
**********************************

This is the developer documentation for the Integreat Django backend.

For general help with the Django framework, please refer to the :doc:`django:index`.


First Steps
===========

.. toctree::
    :caption: First Steps
    :hidden:

    installation
    dev-server
    tutorials
    dev-tools
    troubleshooting

* :doc:`installation`: Installation guide
* :doc:`dev-server`: Run local development server
* :doc:`tutorials`: Step-by-step guides
* :doc:`dev-tools`: Scripts for developers
* :doc:`troubleshooting`: General problem solving guide


Basic Concepts
==============

.. toctree::
    :caption: Basic Concepts
    :hidden:

    virtualenv
    internationalization
    frontend-bundling
    documentation
    continuous-integration

* :doc:`virtualenv`: Virtual Python environment and Pipenv
* :doc:`internationalization`: Multi-language support for the backend UI
* :doc:`frontend-bundling`: Work on frontend assets
* :doc:`documentation`: This Sphinx documentation
* :doc:`continuous-integration`: Continuous Integration and Delivery with CircleCI


Deployment
==========

.. toctree::
    :caption: Deployment
    :hidden:

    packaging
    prod-server

* :doc:`packaging`: Create an easy installable package
* :doc:`prod-server`: Run the production server


Contributing
============

.. toctree::
    :caption: Contributing
    :hidden:

    issue-reporting
    code-style
    git-flow
    code-of-conduct

* :doc:`issue-reporting`: Rug Reporting and Feature Request Guidelines
* :doc:`code-style`: Coding Conventions
* :doc:`git-flow`: GitHub Workflow model
* :doc:`code-of-conduct`: Contributor Covenant Code of Conduct


Reference
=========

.. toctree::
    :caption: Reference
    :hidden:

    ref/backend
    ref/cms
    ref/api
    ref/gvz_api
    ref/sitemap
    ref/xliff

* :doc:`ref/backend`: This is the project's main app which contains all configuration files.
* :doc:`ref/cms`: This is the content management system for backend users which contains all database models, views, forms and templates.
* :doc:`ref/api`: This is the app which contains all API routes and Classes which maps the cms models to API JSON responses. This is not the API documentation itself, but the Django developer documentation. A link to the API documentation will follow soon.
* :doc:`ref/gvz_api`: This is the app to communicate with our Gemeindeverzeichnis API to automatically import coordinates and region aliases
* :doc:`ref/sitemap`: This is the app to dynamically generate a sitemap.xml for the webapp
* :doc:`ref/xliff`: The XLIFF serializer module


.. toctree::
    :caption: Extended Reference
    :hidden:

    ref-ext/backend
    ref-ext/cms
    ref-ext/api
    ref-ext/gvz_api
    ref-ext/sitemap
    ref-ext/xliff


Indices
=======

.. toctree::
    :caption: Indices
    :hidden:

    Glossary <https://wiki.tuerantuer.org/glossary>

* `Glossary <https://wiki.tuerantuer.org/glossary>`_: List of terms and definitions
* :ref:`Full Index <genindex>`: List of all documented classes, functions and attributes
* :ref:`Python Module Index <modindex>`: List of all python modules in this project
* :ref:`search`: Search documentation
