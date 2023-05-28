from typing import Optional, Literal, Generator
import re

from covid19_guidance_explorer.database import database


_search_results_columns = [
    'id', 'title', 'slug', 'document_id',
    'effective_date', 'termination_date', 'headline'
]

def search(
    search_string: str,
    *,
    search_mode: Literal[
        'phrase', 'simple', 'plain',
        'normal', 'string', 'regex'
    ] = 'normal',
    case_sensitive: Optional[bool]=False,
    k: Optional[int]=None,
    n: Optional[int]=None
) -> Generator[dict, None, None]:
    """
    Searches all document versions for a particular query or search string.

    Parameters:
            search_string (str): the string, search query, or regex to search for.
            search_mode (str): the type of search to execeute.
                The available modes are:
                - 'phrase': searches for full phrases using full-text-search with 
                    `phraseto_tsquery`. This mode ignores the `case_sensitive` 
                    argument.
                - 'simple' accepts unstructured search queries using full-text-search 
                    with `websearch_to_tsquery`. This mode ignores the `case_sensitive` 
                    argument.
                - 'plain': does not accept query operators (e.g., `&`, `|`, `<->`) 
                    but still uses full-text-search with `plainto_tsquery`. This 
                    mode ignores the `case_sensitive` argument.
                - 'normal': accepts query operators (e.g., `&`, `|`, `<->`) 
                    and uses full-text-search with `to_tsquery`. This mode ignores 
                    the `case_sensitive` argument.
                - 'string': searches for string matches using `regexp_like` 
                    with the search string escaped using `re.escape`. This mode 
                    accepts the `case_sensitive` argument.
                - 'regex': searches for regex matches using `regexp_like` 
                    with the search_string not escaped. This mode accepts 
                    the `case_sensitive` argument.
            case_sensitive (bool): whether or not the search should
                be case sensitive.
            k (int): the page number if pagination is being used.
                It is indexed from 0.
            n (int): the number of search results per page if
                pagination is being used.

    Returns:
            search_results (Generator[dict, None, None]): a generator yielding
                search results returned by the database.
    """
    if k is None:
        n = None
    else:
        k *= n

    if search_mode in ('string', 'regex'):
        if case_sensitive:
            count_flags = ''
            flags = 'g'
        else:
            count_flags = 'i'
            flags = 'gi'

        if search_mode == 'string':
            search_string = re.escape(search_string)

        cursor = database.execute_sql(f"""
        SELECT
          "t1"."id",
          "t1"."title",
          "t1"."slug",
          "t1"."document_id",
          "t1"."effective_date",
          "t1"."termination_date",
          STRING_AGG(
            CONCAT(
              "t2"."matches" [1], '<mark>', "t2"."matches" [2],
              '</mark>', "t2"."matches" [3]
            ),
            ' ... '
          )
        FROM
          "documentversion" AS "t1"
        INNER JOIN (
          SELECT
            "t1"."id",
            "t1"."document_id",
            regexp_matches(
              "t1"."content",
              CONCAT(
                '((?:[^ ]+ ){{0,25}})([^ ]*', %s, '[^ ]*)((?: [^ ]+){{0,25}})'
              ),
              '{flags}'
            ) AS "matches",
            "t2"."rank"
          FROM 
            "documentversion" AS "t1" 
          INNER JOIN (
            SELECT
              "t1"."id",
              "t1"."document_id",
              "t2"."rank"
            FROM
              "documentversion" AS "t1"
            INNER JOIN (
              SELECT 
                "t2"."id",
                AVG(regexp_count("t1"."content", %s, 1, '{count_flags}')) as rank 
              FROM 
                "documentversion" AS "t1" 
              INNER JOIN
                "document" AS "t2" ON ("t1"."document_id" = "t2"."id")
              WHERE 
                regexp_like("t1"."content", %s, '{count_flags}') 
              GROUP BY
                "t2"."id"
              ORDER BY 
                rank DESC,
                "t2"."id"
              LIMIT 
                %s
              OFFSET
                %s
            ) AS "t2" ON ("t1"."document_id" = "t2"."id")
          ) AS "t2" ON ("t1"."id" = "t2"."id")
        ) AS "t2" ON ("t1"."id" = "t2"."id")
        GROUP BY
          "t1"."id"
        ORDER BY
          MAX("t2"."rank") DESC
        """, (search_string, search_string, search_string, n, k))
    else:
        tsquery_name = {
            'phrase': 'phraseto_tsquery',
            'plain': 'plainto_tsquery',
            'normal': 'to_tsquery',
            'simple': 'websearch_to_tsquery'
        }[search_mode]

        cursor = database.execute_sql(f"""
        SELECT 
          "t1"."id", 
          "t1"."title", 
          "t1"."slug", 
          "t1"."document_id", 
          "t1"."effective_date", 
          "t1"."termination_date", 
          ts_headline(
            'english', 
            "t1"."content", 
            {tsquery_name}('english', %s), 
            'StartSel=<mark>,StopSel=</mark>,MaxFragments=100,MaxWords=50,MinWords=25'
          )
        FROM 
          "documentversion" AS "t1" 
          INNER JOIN (
            SELECT
              "t1"."id",
              "t1"."document_id",
              "t2"."rank"
            FROM
              "documentversion" AS "t1"
              INNER JOIN (
                SELECT
                  "t2"."id",
                  AVG(ts_rank(
                    "t1"."search_content",
                    {tsquery_name}('english', %s)
                  )) AS rank
                FROM
                  "documentversion" AS "t1"
                INNER JOIN
                  "document" AS "t2" ON ("t1"."document_id" = "t2"."id")
                WHERE 
                (
                  "t1"."search_content" @@ {tsquery_name}('english', %s)
                ) 
                GROUP BY
                  "t2"."id"
                ORDER BY
                  rank DESC,
                  "t2"."id"
                LIMIT 
                  %s
                OFFSET
                  %s
              ) AS "t2" ON ("t1"."document_id" = "t2"."id")
          ) AS "t2" ON ("t1"."id" = "t2"."id")
        ORDER BY
          "t2"."rank" DESC
        """, (search_string, search_string, search_string, n, k))

    for row in cursor:
        yield dict(zip(_search_results_columns, row))

_num_search_results_values = ['num_documents', 'num_document_versions']

def search_num_results(
    search_string: str,
    *,
    search_mode: Literal[
        'phrase', 'simple', 'plain',
        'normal', 'string', 'regex'
    ] = 'normal',
    case_sensitive: Optional[bool]=False
) -> int:
    """
    Searches all document versions for a particular query or search string
        and returns the number of document versions found.

    Parameters:
            search_string (str): the string, search query, or regex to search for.
            search_mode (str): the type of search to execeute.
                The available modes are:
                - 'phrase': searches for full phrases using full-text-search with 
                    `phraseto_tsquery`. This mode ignores the `case_sensitive` 
                    argument.
                - 'simple' accepts unstructured search queries using full-text-search 
                    with `websearch_to_tsquery`. This mode ignores the `case_sensitive` 
                    argument.
                - 'plain': does not accept query operators (e.g., `&`, `|`, `<->`) 
                    but still uses full-text-search with `plainto_tsquery`. This 
                    mode ignores the `case_sensitive` argument.
                - 'normal': accepts query operators (e.g., `&`, `|`, `<->`) 
                    and uses full-text-search with `to_tsquery`. This mode ignores 
                    the `case_sensitive` argument.
                - 'string': searches for string matches using `regexp_like` 
                    with the search string escaped using `re.escape`. This mode 
                    accepts the `case_sensitive` argument.
                - 'regex': searches for regex matches using `regexp_like` 
                    with the search_string not escaped. This mode accepts 
                    the `case_sensitive` argument.
            case_sensitive (bool): whether or not the search should
                be case sensitive.

    Returns:
            num_search_results (int): the number of search results that match
                the given query settings.
    """
    if search_mode in ('string', 'regex'):
        if case_sensitive:
            count_flags = ''
        else:
            count_flags = 'i'

        if search_mode == 'string':
            search_string = re.escape(search_string)

        cursor = database.execute_sql(f"""
        SELECT DISTINCT
          COUNT(DISTINCT "t1"."document_id"),
          COUNT(DISTINCT "t1"."id")
        FROM
          "documentversion" AS "t1"
        WHERE
          regexp_like("t1"."content", %s, '{count_flags}')
        """, (search_string,))
    else:
        tsquery_name = {
            'phrase': 'phraseto_tsquery',
            'plain': 'plainto_tsquery',
            'normal': 'to_tsquery',
            'simple': 'websearch_to_tsquery'
        }[search_mode]

        cursor = database.execute_sql(f"""
        SELECT
          COUNT(DISTINCT "t1"."document_id"),
          COUNT(DISTINCT "t1"."id")
        FROM
          "documentversion" AS "t1"
        WHERE
          "t1"."search_content" @@ {tsquery_name}('english', %s)
        """, (search_string,))

    return dict(zip(
        _num_search_results_values,
        cursor.fetchone()
    ))
