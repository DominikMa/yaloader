
yaloader — Type-Safe Object Factories from YAML
=================================================

yaloader lets you define configuration classes in Python and load them from YAML files.
Configs are validated with Pydantic v2, layered with priorities, inherited through class hierarchies, and composed across multiple files — then constructed into real Python objects with a single ``.load()`` call.

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   overview
   getting-started
   why-yaloader

.. toctree::
   :maxdepth: 1
   :caption: Core Concepts

   configuration-classes
   loading-and-priority
   configuration-inheritance

.. toctree::
   :maxdepth: 1
   :caption: Advanced Features

   variable-configs
   cross-document-anchors
   dumping

.. toctree::
   :maxdepth: 1
   :caption: Guides

   ml-pipeline-tutorial
   best-practices

.. toctree::
   :maxdepth: 1
   :caption: Python API

   yaloader
