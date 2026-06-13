"""Offline evaluation harness for the SecOps graph (Phase 5a).

Made a package so sibling modules import as ``evals.*`` from the repo root — this keeps
the ``evals/datasets/`` data folder namespaced as ``evals.datasets`` instead of shadowing
the top-level PyPI ``datasets`` package that lancedb optionally imports.
"""
