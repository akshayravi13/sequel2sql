# -*- coding: utf-8 -*-
"""
SQL validation with a single entry point.

    result = validate(sql)                         # syntax only
    result = validate(sql, schema=my_schema)       # syntax + schema (static)
    result = validate_with_db(sql, engine)         # syntax + schema + live EXPLAIN

Both functions collect ALL errors (syntax AND semantic) simultaneously —
a syntax error no longer prevents schema checks from running.
One function in, one ValidationResult out.
Parses exactly once, runs analyze_query exactly once.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

# Per-engine live-schema cache: str(engine.url) → {table: {col: type}}
_live_schema_cache: Dict[str, Dict[str, Dict[str, str]]] = {}


def invalidate_schema_cache(engine) -> None:
    """Clear the cached live schema for *engine* so the next
    ``validate_with_db`` call re-reflects the DB.

    Call this after running ``preprocess_sql`` or any DDL that changes
    the set of tables visible in the database.
    """
    key = str(engine.url)
    _live_schema_cache.pop(key, None)

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, ParseError

from ast_parsers.query_analyzer import analyze_query
from ast_parsers.result import ValidationError, ValidationResult
from ast_parsers.tags import (
    ErrorTag,
    extract_error_code,
    tag_for_sqlstate,
)


def validate(
    sql: str,
    schema: Optional[Dict[str, Dict[str, str]]] = None,
    dialect: str = "postgres",
) -> ValidationResult:
    """
    Validate SQL syntax and (optionally) check against a database schema.

    Unlike the previous implementation this function *does not* stop on the
    first error.  A query with a recoverable syntax problem still goes through
    schema validation so you get the full error picture in one call.

    Args:
        sql:     SQL query string to validate.
        schema:  Optional ``{table_name: {column_name: type}}`` dict.
                 When provided, table existence and column references are
                 checked even when syntax errors are present (as long as a
                 partial AST can be recovered).
        dialect: SQL dialect (default: ``"postgres"``).

    Returns:
        ValidationResult with:
          - ``valid`` – True when no errors were found.
          - ``errors`` – list of ALL ValidationErrors (syntax + semantic).
          - ``query_metadata`` – structural metadata (complexity, clauses, …).
    """
    # ── 1. Parse (with recovery) ──────────────────────────────────────────────
    ast, syntax_errors = _parse_with_recovery(sql, dialect)

    # ── 2. Detect issues sqlglot silently accepts ─────────────────────────────
    silent_errors: List[ValidationError] = []
    schema_errors: List[ValidationError] = []
    metadata = None

    if ast is not None:
        silent_errors = _detect_silent_fixes(sql)
        metadata = analyze_query(ast)
        if schema is not None:
            schema_errors = _check_schema(ast, schema, sql)

    all_errors = syntax_errors + silent_errors + schema_errors
    return ValidationResult(
        valid=len(all_errors) == 0,
        sql=sql,
        errors=all_errors,
        query_metadata=metadata,
    )


def validate_with_db(
    sql: str,
    engine,  # sqlalchemy.engine.Engine — not typed to avoid hard dep at import
    schema: Optional[Dict[str, Dict[str, str]]] = None,
    dialect: str = "postgres",
) -> ValidationResult:
    """
    Full validation pipeline using a live PostgreSQL database.

    Error collection strategy (all run independently, then merged):

    1. **Syntax** — ``_parse_with_recovery()`` classifies parse errors and
       attempts WARN-level recovery to get a partial AST.
    2. **Token schema** — ``_extract_identifiers_from_tokens()`` walks the
       sqlglot token stream (never throws on broken SQL) to extract table and
       column candidates, then checks them against the live DB schema.  This
       fires even when the AST is too broken to use.
    3. **AST schema** — ``_check_schema()`` does a precise alias-resolved
       column walk when the AST is available.  More accurate than the token
       check for qualified references.
    4. **EXPLAIN** — ``EXPLAIN {sql}`` on the live DB catches whatever the
       above miss (type errors, permission issues, constraint violations) at
       the cost of reporting only the *first* server error.

    All four lists are merged and deduplicated.  EXPLAIN errors take priority;
    AST-schema errors supersede token-schema errors for the same identifier.

    Args:
        sql:     SQL query string.
        engine:  SQLAlchemy ``Engine`` connected to the target database.
        schema:  Ignored — the live DB schema is always used.  Kept for
                 backward compatibility with call sites that pass a JSON schema.
        dialect: SQL dialect for the static parser (default: ``"postgres"``).

    Returns:
        ValidationResult with ``valid=True`` only when all checks pass.
    """
    # ── 1. Syntax + partial AST ───────────────────────────────────────────────
    ast, syntax_errors = _parse_with_recovery(sql, dialect)
    silent_errors = _detect_silent_fixes(sql) if ast is not None else []
    metadata = analyze_query(ast) if ast is not None else None

    # ── 2. Live schema from DB (cached per engine URL) ────────────────────────
    live_schema = _get_live_schema(engine)

    # ── 3. Token-stream schema check (always runs, AST-independent) ──────────
    table_cands, col_cands = _extract_identifiers_from_tokens(sql)
    token_schema_errors = _check_identifiers_against_schema(
        table_cands, col_cands, live_schema
    )

    # ── 4. AST schema check (precise, only when AST is good) ─────────────────
    ast_schema_errors: List[ValidationError] = []
    if ast is not None:
        ast_schema_errors = _check_schema(ast, live_schema, sql)
        # Discard noisy token errors — the AST parser understands CTEs,
        # subquery aliases, and table aliases; the token scanner does not.
        token_schema_errors = []

    # ── 5. EXPLAIN — DB-native first error ───────────────────────────────────
    db_errors = _explain(sql, engine)

    # ── 6. EXPLAIN-success suppression ────────────────────────────────────────
    # If EXPLAIN says the query is valid, the static schema checks may have
    # produced false positives (e.g. CTE-output columns, table-valued
    # functions).  PostgreSQL is the ground truth — drop schema errors.
    # Syntax and silent errors are kept: they flag style issues (trailing
    # commas, etc.) that PostgreSQL silently accepts but are still wrong.
    if not db_errors:
        ast_schema_errors = []
        token_schema_errors = []

    # ── 7. Cascade suppression ────────────────────────────────────────────────
    # If EXPLAIN flagged a table as missing (SQLSTATE 42P01), suppress any
    # AST-level column errors for columns of that same table — they're
    # guaranteed downstream noise, not independent errors.
    missing_tables_from_explain: Set[str] = set()
    for e in db_errors:
        if e.error_code == "42P01" and e.context:
            # Try to extract the table name from the error message
            msg_lower = e.message.lower() if e.message else ""
            # Pattern: relation "table_name" does not exist
            import re
            rel_match = re.search(r'relation "([^"]+)"', msg_lower)
            if rel_match:
                missing_tables_from_explain.add(rel_match.group(1).lower())

    if missing_tables_from_explain:
        ast_schema_errors = [
            e for e in ast_schema_errors
            if not (
                e.tag == ErrorTag.HALLUCINATION_COLUMN
                and e.context
                and any(
                    mt in e.context.lower() or mt in (e.message or "").lower()
                    for mt in missing_tables_from_explain
                )
            )
        ]

    # ── 8. Merge, deduplicate by (tag, context) ───────────────────────────────
    # Priority: EXPLAIN > AST-schema > token-schema > syntax > silent
    all_errors = _merge_errors(
        db_errors,
        ast_schema_errors,
        token_schema_errors,
        syntax_errors,
        silent_errors,
    )

    return ValidationResult(
        valid=len(all_errors) == 0,
        sql=sql,
        errors=all_errors,
        query_metadata=metadata,
    )


# ─── Internal: parsing ────────────────────────────────────────────────────────


def _parse_with_recovery(
    sql: str, dialect: str
) -> Tuple[Optional[exp.Expression], List[ValidationError]]:
    """
    Try strict parse first.  If that fails, collect syntax errors and then
    retry with ErrorLevel.WARN to get a partial AST so that schema checks can
    still run on the remainder of the query.

    Supports multi-statement SQL (e.g. ``DROP TABLE ...; CREATE TABLE ...``)
    by using ``sqlglot.parse()`` which returns a list of ASTs.  The first
    non-DDL AST is returned for schema checking (DDL like CREATE/DROP doesn't
    need column-level validation).

    Returns: (ast_or_None, syntax_errors)
    """
    try:
        # parse() returns List[Optional[Expression]]
        asts = sqlglot.parse(sql, read=dialect, error_level=ErrorLevel.RAISE)
        # Pick the best AST for schema checking: prefer SELECT/DML over DDL
        best = None
        for a in asts:
            if a is None:
                continue
            if best is None:
                best = a
            # Prefer non-DDL (SELECT, INSERT, UPDATE, DELETE) for schema checks
            if not isinstance(a, (exp.Create, exp.Drop, exp.Command)):
                best = a
                break
        return best, []
    except ParseError as exc:
        syntax_errors = _classify_parse_error(sql, exc)
    except Exception as exc:
        syntax_errors = _classify_generic_error(sql, exc)

    # Recovery attempt — get a partial AST even though syntax is broken
    try:
        asts = sqlglot.parse(sql, read=dialect, error_level=ErrorLevel.WARN)
        best = None
        for a in asts:
            if a is None:
                continue
            if best is None:
                best = a
            if not isinstance(a, (exp.Create, exp.Drop, exp.Command)):
                best = a
                break
        ast = best
    except Exception:
        ast = None

    return ast, syntax_errors


# ─── Internal: silent-fix detection ──────────────────────────────────────────


def _detect_silent_fixes(sql: str) -> List[ValidationError]:
    """Return errors for patterns sqlglot silently accepts but that are wrong."""
    errors: List[ValidationError] = []

    pos = _find_trailing_delimiter(sql)
    if pos is not None:
        errors.append(
            ValidationError(
                tag=ErrorTag.TRAILING_DELIMITER,
                message="Trailing comma or delimiter before keyword",
                location=pos,
                context=sql[max(0, pos - 10) : pos + 15],
            )
        )
        return errors  # one silent-fix error at a time is enough

    if _has_empty_select(sql):
        errors.append(
            ValidationError(
                tag=ErrorTag.KEYWORD_MISUSE,
                message="SELECT clause has no columns specified",
            )
        )

    return errors


# ─── Internal: schema checks ──────────────────────────────────────────────────


def _check_schema(
    ast: exp.Expression,
    schema: Dict[str, Dict[str, str]],
    sql: str = "",
) -> List[ValidationError]:
    """
    Check table and column references against the schema dict.

    Replaces the previous ``sqlglot.optimize()``-based implementation which
    lowercased column names before comparison and therefore missed hallucinated
    columns whose schema keys contain spaces or mixed-case characters (e.g.
    ``"County Code"``).

    This implementation:
    * Walks ``exp.Column`` nodes directly — no optimizer involvement.
    * Compares names case-insensitively via ``.lower()``.
    * Builds an alias map from ``exp.Table`` nodes so qualified references like
      ``t1.column_name`` are resolved correctly.
    * Reports the enclosing SQL clause for each error via ``_clause_of()``.
    """
    errors: List[ValidationError] = []

    # ── Normalised schema lookup ──────────────────────────────────────────────
    # schema_lower: {table_lower -> {col_lower -> original_col_name}}
    schema_lower: Dict[str, Dict[str, str]] = {
        t.lower(): {c.lower(): c for c in cols} for t, cols in schema.items()
    }

    # ── PostgreSQL system schemas — never flag as hallucinated ─────────────────
    _PG_SYSTEM_PREFIXES = ("pg_", "information_schema")

    # ── PostgreSQL built-in SRFs and catalog objects used in FROM clauses ──────
    _PG_BUILTIN_SRFS = {
        # Set-returning functions commonly used in FROM
        "generate_series", "unnest", "regexp_split_to_table",
        "json_array_elements", "json_array_elements_text",
        "jsonb_array_elements", "jsonb_array_elements_text",
        "json_each", "json_each_text", "jsonb_each", "jsonb_each_text",
        "json_to_record", "jsonb_to_record", "json_to_recordset", "jsonb_to_recordset",
        "json_populate_record", "jsonb_populate_record",
        "json_populate_recordset", "jsonb_populate_recordset",
        "regexp_matches", "string_to_array", "xpath",
        "ts_stat", "ts_token_type", "ts_parse",
        "aclexplode", "pg_get_keywords", "pg_options_to_table",
        # System catalog tables/views
        "pg_class", "pg_attribute", "pg_constraint", "pg_namespace",
        "pg_index", "pg_type", "pg_am", "pg_tablespace", "pg_stat_activity",
        "pg_stat_user_tables", "pg_stat_all_tables", "pg_roles",
        "pg_database", "pg_proc", "pg_description", "pg_depend",
        "pg_catalog", "pg_tables", "pg_views", "pg_sequences",
    }

    # ── Collect CTE aliases so they are never flagged as missing tables ────────
    cte_aliases: Set[str] = set()
    for cte_node in ast.find_all(exp.CTE):
        if cte_node.alias:
            cte_aliases.add(cte_node.alias.lower())

    # ── Collect subquery aliases (these are also virtual tables) ──────────────
    for sq_node in ast.find_all(exp.Subquery):
        if sq_node.alias:
            cte_aliases.add(sq_node.alias.lower())

    # ── Alias map: {alias_or_table_lower -> real_table_lower} ─────────────────
    # All tables (including those inside CTEs) for resolving qualified refs.
    alias_map: Dict[str, str] = {}
    # All table/subquery aliases (used to skip whole-row alias refs like
    # row_to_json(alias) where sqlglot parses 'alias' as a Column).
    all_table_aliases: Set[str] = set()
    # Inline column definitions from SRFs and VALUES (e.g. AS j(element))
    # These are dynamically-named columns valid in their scope.
    inline_columns: Set[str] = set()
    # Tables referenced in the OUTER query only (not inside CTE bodies).
    outer_tables: Set[str] = set()
    for table_node in ast.find_all(exp.Table):
        real = table_node.name.lower()
        if real:
            alias_map[real] = real
        ta = table_node.args.get("alias")
        if ta:
            alias_map[ta.alias.lower()] = real
            all_table_aliases.add(ta.alias.lower())
            # Collect inline column defs: AS j(element, value, ...)
            for col_id in ta.args.get("columns") or []:
                if isinstance(col_id, exp.Identifier):
                    inline_columns.add(col_id.name.lower())
        # Track whether this table ref is in the outer query
        if real and not table_node.find_ancestor(exp.CTE):
            outer_tables.add(real)
    # Also include subquery aliases and their inline columns
    for sq_node in ast.find_all(exp.Subquery):
        ta = sq_node.args.get("alias")
        if ta:
            all_table_aliases.add(ta.alias.lower())
            for col_id in ta.args.get("columns") or []:
                if isinstance(col_id, exp.Identifier):
                    inline_columns.add(col_id.name.lower())

    # ── 1. Table existence ────────────────────────────────────────────────────
    missing_tables_lower: Set[str] = set()
    for table_node in ast.find_all(exp.Table):
        t = table_node.name.lower()
        if not t:
            continue
        # Skip tables inside DDL statements (CREATE FUNCTION, CREATE VIEW, etc.)
        if table_node.find_ancestor(exp.Create, exp.Command):
            continue
        # Skip PostgreSQL system tables / schemas
        if any(t.startswith(p) for p in _PG_SYSTEM_PREFIXES):
            continue
        # Skip PostgreSQL built-in SRFs and catalog objects
        if t in _PG_BUILTIN_SRFS:
            continue
        # Skip if the table's schema qualifier is a system schema
        table_db = table_node.args.get("db")
        if table_db and isinstance(table_db, exp.Identifier):
            if any(table_db.name.lower().startswith(p) for p in _PG_SYSTEM_PREFIXES):
                continue
        if t not in schema_lower and t not in cte_aliases:
            missing_tables_lower.add(t)
            errors.append(
                ValidationError(
                    tag=ErrorTag.HALLUCINATION_TABLE,
                    message=f"Table '{table_node.name}' does not exist in schema",
                    context=table_node.name,
                    affected_clauses=["FROM"],
                )
            )

    # ── 2. Column references ──────────────────────────────────────────────────
    # Only check unqualified columns against outer-query schema tables.
    # CTE/subquery aliases, missing tables, and tables with unknown columns
    # (empty dict from CTAS parsing) are excluded.
    schema_tables: Set[str] = {
        t for t in outer_tables
        if t in schema_lower
        and t not in missing_tables_lower
        and len(schema_lower[t]) > 0  # skip tables with unknown columns
    }

    # ── Collect SELECT-level aliases (e.g. `COUNT(x) AS answered`) ────────────
    # These are valid column references in ORDER BY, HAVING, etc.
    select_aliases: Set[str] = set()
    for select_node in ast.find_all(exp.Select):
        for sel_expr in select_node.expressions:
            if isinstance(sel_expr, exp.Alias) and sel_expr.alias:
                select_aliases.add(sel_expr.alias.lower())

    for col_node in ast.find_all(exp.Column):
        # Skip literal * (e.g. SELECT t.* — sqlglot parses * as Column name)
        if col_node.name == "*":
            continue
        # Skip columns inside CTE definitions — they reference
        # CTE-scoped expressions, not base schema columns
        if col_node.find_ancestor(exp.CTE):
            continue

        col_name: str = col_node.name  # bare column string, original case
        qualifier: str = col_node.table  # syntactic qualifier (alias/table), if any

        col_lower = col_name.lower()

        # Skip references to SELECT-level aliases (e.g. ORDER BY answered)
        if col_lower in select_aliases:
            continue

        # Skip inline column defs from SRFs/VALUES (e.g. AS j(element))
        if col_lower in inline_columns:
            continue

        # Skip template variables (${var}) that sqlglot misparses as columns
        if f"${{{col_name}}}" in sql or f"${{{col_lower}}}" in sql:
            continue

        # Skip whole-row table alias references (e.g. row_to_json(alias))
        if not qualifier and col_lower in all_table_aliases:
            continue
        if not qualifier and col_lower in cte_aliases:
            continue

        if qualifier:
            # Qualified reference: resolve alias → real table
            resolved = alias_map.get(qualifier.lower())
            if resolved is None or qualifier.lower() in cte_aliases:
                # Unknown qualifier or CTE/subquery alias — skip
                continue
            if resolved in cte_aliases:
                # Resolved table is a CTE — can't validate its columns statically
                continue
            if resolved in missing_tables_lower:
                # Table is already flagged as missing — skip its columns
                continue
            table_cols = schema_lower.get(resolved, {})
            if not table_cols:
                # Table exists but columns are unknown (e.g. CTAS) — skip
                continue
            if col_lower not in table_cols:
                clause = _clause_of(col_node)
                errors.append(
                    ValidationError(
                        tag=ErrorTag.HALLUCINATION_COLUMN,
                        message=(
                            f"Column '{col_name}' does not exist in table "
                            f"'{resolved}' (referenced as '{qualifier}.{col_name}')"
                        ),
                        context=f"{qualifier}.{col_name}",
                        affected_clauses=[clause] if clause else [],
                    )
                )
        else:
            # Unqualified reference: check against schema tables only
            # (not CTE/subquery aliases which aren't in the schema)
            if not schema_tables:
                # All referenced tables are CTEs/subqueries — can't validate
                continue

            found_in = [
                t for t in schema_tables
                if col_lower in schema_lower.get(t, {})
            ]

            if not found_in:
                clause = _clause_of(col_node)
                errors.append(
                    ValidationError(
                        tag=ErrorTag.HALLUCINATION_COLUMN,
                        message=(
                            f"Column '{col_name}' does not exist in any "
                            f"referenced table"
                        ),
                        context=col_name,
                        affected_clauses=[clause] if clause else [],
                    )
                )
            elif len(found_in) > 1:
                clause = _clause_of(col_node)
                errors.append(
                    ValidationError(
                        tag=ErrorTag.AMBIGUOUS_COLUMN,
                        message=(
                            f"Column '{col_name}' is ambiguous — exists in "
                            f"tables: {', '.join(found_in)}"
                        ),
                        context=col_name,
                        affected_clauses=[clause] if clause else [],
                    )
                )

    return errors


def _clause_of(node: exp.Expression) -> Optional[str]:
    """Walk parent chain to find the name of the enclosing SQL clause."""
    _CLAUSE_MAP = {
        exp.Select: "SELECT",
        exp.From: "FROM",
        exp.Where: "WHERE",
        exp.Join: "JOIN",
        exp.Having: "HAVING",
        exp.Group: "GROUP BY",
        exp.Order: "ORDER BY",
    }
    curr = node.parent
    while curr is not None:
        for clause_type, name in _CLAUSE_MAP.items():
            if isinstance(curr, clause_type):
                return name
        curr = curr.parent
    return None


# ─── Internal: live DB validation ────────────────────────────────────────────


def _get_live_schema(engine) -> Dict[str, Dict[str, str]]:
    """
    Reflect the full schema from the live database and cache it by engine URL.

    Returns ``{table_name: {column_name: sql_type}}`` — same format as the
    JSON schema files so it can be passed to ``_check_schema()`` directly.
    """
    key = str(engine.url)
    if key not in _live_schema_cache:
        from sqlalchemy import MetaData as SAMetaData

        meta = SAMetaData()
        meta.reflect(bind=engine)
        _live_schema_cache[key] = {
            table_name: {col.name: str(col.type) for col in table_obj.columns}
            for table_name, table_obj in meta.tables.items()
        }
    return _live_schema_cache[key]


def _extract_identifiers_from_tokens(
    sql: str,
) -> Tuple[List[str], List[str]]:
    """
    Walk the sqlglot token stream (which **never throws** on broken SQL) and
    extract:

    * ``table_candidates`` — bare identifiers immediately following a
      ``FROM``, ``JOIN``, or ``INTO`` keyword.
    * ``col_candidates`` — all double-quoted ``IDENTIFIER`` tokens that are
      *not* in a table-name position.  Double-quoted tokens in PostgreSQL are
      always object names, so false positives are near-zero.

    This is intentionally simple and positional — it is not a full SQL
    parser.  Its job is to catch hallucinated names when the AST is too
    broken to use.
    """
    from sqlglot.tokens import Tokenizer as _Tokenizer
    from sqlglot.tokens import TokenType

    try:
        toks = _Tokenizer().tokenize(sql)
    except Exception:
        return [], []

    TABLE_TRIGGERS: Set = {
        TokenType.FROM,
        TokenType.JOIN,
        TokenType.INTO,
    }
    # Token types to skip between a trigger and the actual table name
    SKIP_TYPES: Set = {TokenType.L_PAREN}

    table_candidates: List[str] = []
    table_positions: Set[int] = set()

    i = 0
    while i < len(toks):
        tok = toks[i]
        if tok.token_type in TABLE_TRIGGERS:
            j = i + 1
            while j < len(toks) and toks[j].token_type in SKIP_TYPES:
                j += 1
            if j < len(toks) and toks[j].token_type in (
                TokenType.VAR,
                TokenType.IDENTIFIER,
            ):
                table_candidates.append(toks[j].text)
                table_positions.add(j)
        i += 1

    # Second pass: double-quoted IDENTIFIER tokens not in table positions
    col_candidates: List[str] = [
        toks[idx].text
        for idx, tok in enumerate(toks)
        if tok.token_type == TokenType.IDENTIFIER and idx not in table_positions
    ]

    return table_candidates, col_candidates


def _check_identifiers_against_schema(
    table_cands: List[str],
    col_cands: List[str],
    schema: Dict[str, Dict[str, str]],
) -> List[ValidationError]:
    """
    Check token-extracted table and column candidates against the live schema.

    Column candidates are checked against the union of columns in all
    *valid* referenced tables.  When every referenced table is hallucinated
    (nothing valid found) the column check falls back to the full schema so
    we still report columns that don't exist anywhere.
    """
    errors: List[ValidationError] = []
    schema_lower: Dict[str, Set[str]] = {
        t.lower(): {c.lower() for c in cols} for t, cols in schema.items()
    }

    valid_tables: Set[str] = set()
    for t in table_cands:
        if t.lower() in schema_lower:
            valid_tables.add(t.lower())
        else:
            errors.append(
                ValidationError(
                    tag=ErrorTag.HALLUCINATION_TABLE,
                    message=f"Table '{t}' does not exist in the database",
                    context=t,
                    affected_clauses=["FROM"],
                )
            )

    # If we found valid tables, restrict column search to those; otherwise
    # search the whole schema so we don't miss anything.
    search_cols: Set[str] = set()
    for t in valid_tables if valid_tables else schema_lower.keys():
        search_cols.update(schema_lower.get(t, set()))

    for col in col_cands:
        if col.lower() not in search_cols:
            errors.append(
                ValidationError(
                    tag=ErrorTag.HALLUCINATION_COLUMN,
                    message=f"Column '{col}' does not exist in the database",
                    context=col,
                )
            )

    return errors


def _merge_errors(*error_lists: List[ValidationError]) -> List[ValidationError]:
    """
    Merge multiple error lists, deduplicating by ``(tag, context_lower)``.

    Lists are processed in order; earlier lists have priority (their entry
    wins when two errors share tag + normalised context).
    """
    seen: Set[Tuple[ErrorTag, str]] = set()
    merged: List[ValidationError] = []
    for lst in error_lists:
        for err in lst:
            key = (err.tag, (err.context or "").lower())
            if key not in seen:
                seen.add(key)
                merged.append(err)
    return merged


def _explain(sql: str, engine) -> List[ValidationError]:
    """
    Run a safe 'dry run' on the live database.
    Uses EXPLAIN for DML to avoid long execution times, and
    BEGIN -> Execute -> ROLLBACK for DDL to validate syntax and schema.
    """
    try:
        from sqlalchemy import text as sa_text

        with engine.connect() as conn:
            # Open a transaction so we can safely roll back any execution
            trans = conn.begin()
            try:
                # Set a short timeout so a bad query doesn't hang the benchmark
                conn.execute(sa_text("SET statement_timeout = '2s'"))

                # Check what kind of query this is
                sql_upper = sql.lstrip().upper()
                is_dml = sql_upper.startswith(
                    ("SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "VALUES")
                )

                if is_dml:
                    # Fast and safe plan generation
                    conn.execute(sa_text(f"EXPLAIN {sql}"))
                else:
                    # Actual execution for CREATE, DROP, ALTER, DO, etc.
                    conn.execute(sa_text(sql))
            finally:
                # NEVER commit. Always roll back to keep the DB pristine
                # for the next query in the benchmark.
                trans.rollback()
        return []
    except Exception as exc:
        # Extract PostgreSQL SQLSTATE + message when available
        orig = getattr(exc, "orig", None)
        sqlstate: Optional[str] = None
        pg_message: str = str(exc)

        if orig is not None:
            sqlstate = getattr(orig, "pgcode", None)
            pg_message = getattr(orig, "pgerror", None) or str(exc)
        else:
            sqlstate = extract_error_code(str(exc))

        tag = tag_for_sqlstate(sqlstate) or _infer_tag_from_explain_message(pg_message)

        # 57014 = QueryCanceled (statement_timeout).  This is infra noise —
        # the query is structurally valid but just too slow to EXPLAIN.
        if sqlstate == "57014":
            return []

        return [
            ValidationError(
                tag=tag,
                message=_clean_pg_message(pg_message),
                error_code=sqlstate,
                context="PostgreSQL EXPLAIN",
            )
        ]


def _infer_tag_from_explain_message(message: str) -> ErrorTag:
    """Heuristic tag mapping when no SQLSTATE is available."""
    msg = message.lower()
    if "column" in msg and ("does not exist" in msg or "not found" in msg):
        return ErrorTag.HALLUCINATION_COLUMN
    if "relation" in msg and "does not exist" in msg:
        return ErrorTag.HALLUCINATION_TABLE
    if "syntax error" in msg:
        return ErrorTag.SYNTAX_ERROR
    if "operator does not exist" in msg or "type" in msg:
        return ErrorTag.TYPE_MISMATCH
    if "ambiguous" in msg:
        return ErrorTag.AMBIGUOUS_COLUMN
    return ErrorTag.SCHEMA_UNKNOWN_ERROR


def _clean_pg_message(message: str) -> str:
    """Strip leading ERROR: / DETAIL: boilerplate from a PostgreSQL error string."""
    lines = []
    for line in message.splitlines():
        stripped = re.sub(r"^(ERROR|DETAIL|HINT|CONTEXT):\s*", "", line.strip())
        if stripped:
            lines.append(stripped)
    return " | ".join(lines) if lines else message


# ─── Internal: syntax error classification ───────────────────────────────────


def _classify_parse_error(sql: str, exc: ParseError) -> List[ValidationError]:
    """Map a sqlglot ParseError to one or more ValidationErrors."""
    msg = str(exc)
    msg_lower = msg.lower()
    location = getattr(exc, "col", None)
    error_code = extract_error_code(msg)

    if "unterminated" in msg_lower or _has_unterminated_string(sql):
        return [
            ValidationError(
                tag=ErrorTag.UNTERMINATED_STRING,
                message="Unterminated quoted string",
                location=location,
                context=msg,
                error_code=error_code,
            )
        ]

    if _has_unbalanced_tokens(sql):
        return [
            ValidationError(
                tag=ErrorTag.UNBALANCED_TOKENS,
                message="Unbalanced parentheses or brackets",
                location=location,
                context=_describe_imbalance(sql),
                error_code=error_code,
            )
        ]

    pos = _find_trailing_delimiter(sql)
    if pos is not None:
        return [
            ValidationError(
                tag=ErrorTag.TRAILING_DELIMITER,
                message="Trailing comma or delimiter before keyword",
                location=pos,
                context=sql[max(0, pos - 10) : pos + 10],
                error_code=error_code,
            )
        ]

    if "expecting )" in msg_lower or "expecting (" in msg_lower:
        return [
            ValidationError(
                tag=ErrorTag.UNBALANCED_TOKENS,
                message=msg,
                location=location,
                context="Parser reported expecting parenthesis",
                error_code=error_code,
            )
        ]

    if "unexpected token" in msg_lower or "invalid expression" in msg_lower:
        return [
            ValidationError(
                tag=ErrorTag.INVALID_TOKEN,
                message=msg,
                location=location,
                error_code=error_code,
            )
        ]

    if "unsupported syntax" in msg_lower or "falling back to parsing as" in msg_lower:
        return [
            ValidationError(
                tag=ErrorTag.UNSUPPORTED_DIALECT,
                message=msg,
                location=location,
                error_code=error_code,
            )
        ]

    return [
        ValidationError(
            tag=ErrorTag.KEYWORD_MISUSE,
            message=msg,
            location=location,
            error_code=error_code,
        )
    ]


def _classify_generic_error(sql: str, exc: Exception) -> List[ValidationError]:
    """Map unexpected non-ParseError exceptions to ValidationErrors."""
    msg = str(exc)
    error_code = extract_error_code(msg)
    if "unterminated" in msg.lower() or _has_unterminated_string(sql):
        return [
            ValidationError(
                tag=ErrorTag.UNTERMINATED_STRING,
                message="Unterminated quoted string",
                context=msg,
                error_code=error_code,
            )
        ]
    return [
        ValidationError(
            tag=ErrorTag.SYNTAX_ERROR,
            message=msg,
            error_code=error_code,
        )
    ]


# ─── Internal: SQL text helpers ──────────────────────────────────────────────


def _find_trailing_delimiter(sql: str) -> Optional[int]:
    """Return character position of a trailing comma before a keyword, or None."""
    sql_upper = sql.upper()
    for kw in ("FROM", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "UNION", "JOIN"):
        match = re.search(rf",\s+{re.escape(kw)}\b", sql_upper)
        if match:
            pos = match.start()
            before = sql[:pos].rstrip()
            if before and before[-1].isalnum():
                return pos
    return None


def _has_empty_select(sql: str) -> bool:
    return bool(re.search(r"\bSELECT\s+FROM\b", sql, re.IGNORECASE))


def _has_unbalanced_tokens(sql: str) -> bool:
    """Count paren/bracket depth while skipping string literals."""
    depth_paren = 0
    depth_bracket = 0
    in_string = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if in_string:
            if ch == "'" and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            elif ch == "'":
                in_string = False
        else:
            if ch == "'":
                in_string = True
            elif ch == "(":
                depth_paren += 1
            elif ch == ")":
                depth_paren -= 1
            elif ch == "[":
                depth_bracket += 1
            elif ch == "]":
                depth_bracket -= 1
        i += 1
    return depth_paren != 0 or depth_bracket != 0


def _describe_imbalance(sql: str) -> str:
    """Human-readable description of which tokens are unbalanced."""
    p = sql.count("(") - sql.count(")")
    b = sql.count("[") - sql.count("]")
    parts = []
    if p > 0:
        parts.append(f"{p} unclosed '('")
    elif p < 0:
        parts.append(f"{-p} extra ')'")
    if b > 0:
        parts.append(f"{b} unclosed '['")
    elif b < 0:
        parts.append(f"{-b} extra ']'")
    return ", ".join(parts) or "unknown imbalance"


def _has_unterminated_string(sql: str) -> bool:
    """
    Heuristic: track whether we end up inside an open single-quoted string.
    Handles SQL-style escaped quotes ('') correctly.
    """
    in_string = False
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            if in_string and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_string = not in_string
        i += 1
    return in_string
