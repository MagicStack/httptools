Releasing httptools
===================

The ``Release`` workflow builds the source distribution and builds and tests
the Linux, macOS, and Windows wheel matrix.  Unless it's a dry-run (see below),
it also merges and tags the release PR, creates a GitHub release, and uploads
the distributions to PyPI.

Dry-run a release
-----------------

Two ways of building and testing release wheels without permanent publishing:

* Add the ``release-dry-run`` label to a PR targeting ``master``, ``ci``, or a
  release branch. The label stays in effect for later commits to that PR.  It
  also works for PRs from forks and is useful to test changes to the release
  workflow itself or to test build targets that are not tested by regular PR
  CI.

* On GitHub, open **Actions > Release > Run workflow**, then select a
  repository branch, including ``master``. Manual runs are always dry runs.
  GitHub shows the **Run workflow** button once this workflow is on the
  default branch.

You can then find the ``dist`` artifact under **Artifacts** on the workflow run
page.  The wheels are built and tested by cibuildwheel.

Publish a release
-----------------

1. Update ``__version__`` in ``httptools/_version.py`` and prepare the release
   changelog. ``.github/release_log.py`` can help gather changes since the
   previous release tag::

      $ uv run --no-project --with requests \
          .github/release_log.py <previously-released-version-tag>

2. Open a PR to ``master`` with the version change and release notes in its
   body.  Without the dry-run label, the ``Release`` workflow builds the
   distributions and tests the wheels.  Check the build results, then have a
   Release Manager approve the pending ``pypi`` deployment using
   **Review deployments** on the workflow run.

3. After deployment approval, the workflow merges the PR, signs a tag on the
   merge commit, creates the GitHub release, and uploads the distributions to
   PyPI.  Check these outputs after it finishes, then edit the GitHub release
   notes as needed.

4. Open ``master`` for development by updating ``httptools/_version.py`` to the
   next development version with a ``.dev0`` suffix.
