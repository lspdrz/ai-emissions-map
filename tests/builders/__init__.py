"""Test data builders: one function per kind of record, each returning a fresh, valid record.

Defaults describe one organization (acme) serving one model (m-70b) on the Swiss grid (ch). A test passes only the values it is about, so everything its result depends on is
written in the test itself.

Every builder validates what it returns against build/schemas/, so a test cannot build a record the
real data could not contain. A test that needs an invalid record builds a valid one and breaks it.
"""
