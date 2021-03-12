"""
This package contains helper classes for the handling of XLIFF files.
It can handle XLIFF files of version 1.2 (see :mod:`~xliff.xliff1_serializer`) and 2.0 (see
:mod:`~xliff.xliff2_serializer`).
Additionally, it contains a :mod:`~xliff.base_serializer` containing shared functionality of both XLIFF versions and a
:mod:`~xliff.generic_serializer`, which inspects the given XLIFF file and delegates its deserialization to the
respective version's deserializer.

The interface follows Django's standard serialization syntax (see :doc:`django:topics/serialization`)::

    serializers.serialize("xliff", queryset)
    serializers.deserialize("xliff", xliff_file)

To faciliate the handling of XLIFF files in the views, this package also contains utilities in :mod:`~xliff.utils`.
"""
