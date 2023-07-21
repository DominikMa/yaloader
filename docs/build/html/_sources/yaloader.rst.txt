
yaloader
=======================================

.. currentmodule:: yaloader

Base Modules
---------------------------------------
.. autosummary::
   :nosignatures:
   :toctree: generated
   :template: class-template.rst

   YAMLConfigLoader
   YAMLConfigDumper
   YAMLValueError
   ConfigLoader

   .. autosummary::
    :toctree: generated
    :template: base.rst
    loads
    get_constructor_for_class
    get_multi_constructor_for_vars

   .. autosummary::
      :nosignatures:
      :template: class-template.rst
      VarYAMLConfigBase
      YAMLBaseConfig

Utilities
---------
From the ``yaloader.utils`` module

.. currentmodule:: yaloader.utils
.. autosummary::
    :toctree: generated

    full_object_name
    remove_missing_errors

.. currentmodule:: yaloader
.. autosummary::
    :toctree: generated
    :template: module-template.rst

    representer