from datetime import datetime

from .. import repo
from .. import pretty
from .. import bibstruct
from ..uis import get_ui


class InvalidQuery(ValueError):
    pass


def parser(subparsers, conf):
    parser = subparsers.add_parser('list', help="list papers")
    parser.add_argument('-k', '--citekeys-only', action='store_true',
                        default=False, dest='citekeys',
                        help='Only returns citekeys of matching papers.')
    parser.add_argument('-i', '--ignore-case', action='store_false',
                        default=None, dest='case_sensitive')
    parser.add_argument('-I', '--force-case', action='store_true',
                        dest='case_sensitive')
    parser.add_argument('-a', '--alphabetical', action='store_true',
                        dest='alphabetical', default=False,
                        help='lexicographic order on the citekeys.')
    parser.add_argument('--no-docs', action='store_true',
                        dest='nodocs', default=False,
                        help='list only pubs without attached documents.')
    parser.add_argument('query', nargs='*',
                        help='Paper query ("author:Einstein", "title:learning",'
                             '"year:2000" or "tags:math")')
    return parser


def date_added(p):
    return p.added or datetime(1, 1, 1)


def command(conf, args):
    ui = get_ui()
    rp = repo.Repository(conf)
    papers = filter(get_paper_filter(args.query,
                                     case_sensitive=args.case_sensitive),
                    rp.all_papers())
    if args.nodocs:
        papers = [p for p in papers if p.docpath is None]
    if args.alphabetical:
        papers = sorted(papers, key=lambda p: p.citekey)
    else:
        papers = sorted(papers, key=date_added)
    if len(papers) > 0:
        ui.message('\n'.join(
            pretty.paper_oneliner(p, citekey_only=args.citekeys)
            for p in papers))

    rp.close()


FIELD_ALIASES = {
    'a': 'author',
    'authors': 'author',
    't': 'title',
    'tags': 'tag',
    'y': 'year',
}


class QueryFilter(object):

    def __init__(self, query, case_sensitive=None):
        if case_sensitive is None:
            case_sensitive = not query.islower()
        self.case = case_sensitive
        self.query = self._lower(query)

    def __call__(self, paper):
        raise NotImplementedError

    def _lower(self, s):
        return s if self.case else s.lower()


class FieldFilter(QueryFilter):
    """Generic filter of form `query in paper['field']`"""

    def __init__(self, field, query, case_sensitive=None):
        super(FieldFilter, self).__init__(query, case_sensitive=case_sensitive)
        self.field = field

    def __call__(self, paper):
        return (self.field in paper.bibdata and
                self.query in self._lower(paper.bibdata[self.field]))


class AuthorFilter(QueryFilter):

    def __call__(self, paper):
        """Only checks within last names."""
        if 'author' not in paper.bibdata:
            return False
        else:
            return any([self.query in self._lower(bibstruct.author_last(author))
                        for author in paper.bibdata['author']])


class TagFilter(QueryFilter):

    def __call__(self, paper):
        return any([self.query in self._lower(t) for t in paper.tags])


def _get_field_value(query_block):
    split_block = query_block.split(':')
    if len(split_block) != 2:
        raise InvalidQuery("Invalid query (%s)" % query_block)
    field = split_block[0]
    if field in FIELD_ALIASES:
        field = FIELD_ALIASES[field]
    value = split_block[1]
    return (field, value)


def _query_block_to_filter(query_block, case_sensitive=None):
    field, value = _get_field_value(query_block)
    if field == 'tag':
        return TagFilter(value, case_sensitive=case_sensitive)
    elif field == 'author':
        return AuthorFilter(value, case_sensitive=case_sensitive)
    else:
        return FieldFilter(field, value, case_sensitive=case_sensitive)


# TODO implement search by type of document
def get_paper_filter(query, case_sensitive=None):
    """If case_sensitive is not given, only check case if query
    is not lowercase.

    :args query: list of query blocks (strings)
    """
    filters = [_query_block_to_filter(query_block, case_sensitive=case_sensitive)
               for query_block in query]
    return lambda paper: all([f(paper) for f in filters])
