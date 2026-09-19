"""Helpers the two notebooks share.

Only the plumbing lives here — fetching one member of the published example
archive without downloading the archive. Every call to the `auroraomics`
package is written out in the notebook that makes it, because seeing those
calls is the point of the notebook.

    from quickstart import zenodo
"""

__all__ = ["zenodo"]
