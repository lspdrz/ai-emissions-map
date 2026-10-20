"""The shape of every record in sources/, as TypedDicts that Pydantic validates and pyright checks.

Records stay the plain dicts yaml.safe_load reads. Validating one returns the same dict; the types
describe it for the type checker. Rules that span records (organizations exist, references resolve)
are build/validate.py's.
"""
