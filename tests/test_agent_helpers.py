"""Unit tests for config parsing and the read-only SQL guard."""

import pytest

from workshop_agent.config import _snowflake_kwargs, parse_gateway_headers
from workshop_agent.tools import check_read_only, format_rows


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1",
        "  with a as (select 1) select * from a;",
        "SHOW TABLES",
        "-- c\nSELECT 1",
    ],
)
def test_read_only_allows(sql):
    assert check_read_only(sql) is None


@pytest.mark.parametrize(
    "sql",
    ["DROP TABLE t", "DELETE FROM t", "SELECT 1; DROP TABLE t", "", "CALL p()"],
)
def test_read_only_blocks(sql):
    assert check_read_only(sql) is not None


def test_semicolon_inside_string_is_allowed():
    assert check_read_only("SELECT ';'") is None


def test_gateway_headers():
    assert parse_gateway_headers('{"X-Key": "v"}') == {"X-Key": "v"}
    assert parse_gateway_headers(None) == {}
    assert parse_gateway_headers("not json") == {}
    assert parse_gateway_headers("[1]") == {}


def test_snowflake_auth_precedence():
    base = {"SNOWFLAKE_ACCOUNT": "a", "SNOWFLAKE_USER": "u"}
    pat = {
        **base,
        "SNOWFLAKE_AUTHENTICATOR": "PROGRAMMATIC_ACCESS_TOKEN",
        "SNOWFLAKE_TOKEN": "t",
    }
    assert _snowflake_kwargs(pat)["token"] == "t"
    pw = {**base, "SNOWFLAKE_PASSWORD": "p"}
    assert _snowflake_kwargs(pw)["password"] == "p"


def test_format_rows():
    out = format_rows(["A", "B"], [(1, 2)], truncated=True)
    assert "| A | B |" in out and "truncated" in out
    assert format_rows(["A"], [], False) == "Query returned no rows."


@pytest.mark.parametrize(
    "cypher",
    [
        "MATCH (s:Supplier)<-[:SOURCED_FROM]-(p:Part) RETURN p.partKey LIMIT 5",
        "MATCH (n) WHERE n.name = 'CREATE me' RETURN n.createdDatetime",
    ],
)
def test_cypher_read_only_allows(cypher):
    from workshop_agent.tools import check_read_only_cypher

    assert check_read_only_cypher(cypher) is None


@pytest.mark.parametrize(
    "cypher",
    [
        "CREATE (n:X)",
        "MATCH (n) DETACH DELETE n",
        "MATCH (n) SET n.x = 1 RETURN n",
        "MERGE (n:X {id: 1})",
        "CALL apoc.periodic.iterate('a','b',{})",
    ],
)
def test_cypher_read_only_blocks(cypher):
    from workshop_agent.tools import check_read_only_cypher

    assert check_read_only_cypher(cypher) is not None
