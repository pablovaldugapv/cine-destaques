"""Gera destaques.tsv: lançamentos recentes mais bem avaliados no TMDB, lidos pelo app Cine.

Roda toda semana pelo GitHub Actions (.github/workflows/destaques.yml). O app cruza a lista com o
catálogo de cada aparelho, então funciona também em aparelhos sem chave TMDB.
A credencial (chave v3 ou token de leitura) vem do segredo TMDB_KEY e nunca é gravada.
"""
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json, os, re

output = Path(__file__).resolve().parent / 'destaques.tsv'
credential = os.environ.get('TMDB_KEY', '').strip()
if not credential: raise SystemExit('Defina o segredo TMDB_KEY com a chave do TMDB.')
api_key = re.fullmatch(r'[0-9a-fA-F]{32}', credential) is not None


def get(path, **params):
    params.setdefault('language', 'pt-BR')
    if api_key: params['api_key'] = credential
    request = Request('https://api.themoviedb.org/3' + path + '?' + urlencode(params), headers={'Accept': 'application/json'})
    if not api_key: request.add_header('Authorization', 'Bearer ' + credential)
    with urlopen(request, timeout=20) as response: return json.load(response)


def clean(text): return re.sub(r'[\t\r\n]+', ' ', text or '').strip()


today = date.today(); year_ago = (today - timedelta(days=365)).isoformat()
rows = []
for page in range(1, 6):
    # Filmes lançados nos últimos 12 meses; o mínimo de votos evita notas altas com poucas avaliações.
    for movie in get('/discover/movie', sort_by='vote_average.desc', include_adult='false', page=page,
                     **{'vote_count.gte': 150, 'primary_release_date.gte': year_ago, 'primary_release_date.lte': today.isoformat()})['results']:
        rows.append(('f', movie['id'], movie['vote_average'], (movie.get('release_date') or '')[:4], movie.get('title'), movie.get('original_title')))
    # Séries com episódios no último ano, sem jornais, reality, novelas e talk shows.
    for show in get('/discover/tv', sort_by='vote_average.desc', page=page, without_genres='10763,10764,10766,10767',
                    **{'vote_count.gte': 150, 'air_date.gte': year_ago, 'air_date.lte': today.isoformat()})['results']:
        rows.append(('s', show['id'], show['vote_average'], (show.get('first_air_date') or '')[:4], show.get('name'), show.get('original_name')))

rows.sort(key=lambda row: -row[2])
lines = ['# Lançamentos mais bem avaliados no TMDB, gerado em ' + today.isoformat(),
         '# tipo\tid\tnota\tano\ttítulo\ttítulo original']
lines += [f'{kind}\t{tmdb}\t{rating:.1f}\t{year}\t{clean(title)}\t{clean(original)}' for kind, tmdb, rating, year, title, original in rows]
output.write_text('\n'.join(lines) + '\n', encoding='utf8')
print(f'{len(rows)} títulos em {output.name}.')

# temas.tsv: fileiras temáticas ("=") e sagas em ordem de lançamento ("@"), as mesmas do Cine Android (Themes.java).
THEMES = [
    ('=Super-heróis em ação', '/discover/movie', {'with_keywords': 9715}),
    ('=Baseado em fatos reais', '/discover/movie', {'with_keywords': 9672}),
    ('=Perdidos no espaço', '/discover/movie', {'with_keywords': 9882}),
    ('=Viagem no tempo', '/discover/movie', {'with_keywords': 4379}),
    ('=O assalto perfeito', '/discover/movie', {'with_keywords': 10051}),
    ('=Na linha de frente', '/discover/movie', {'with_genres': 10752}),
    ('=Quando o desastre chega', '/discover/movie', {'with_keywords': 10617}),
    ('=Apocalipse zumbi', '/discover/movie', {'with_keywords': 12377}),
    ('=Esporte e superação', '/discover/movie', {'with_keywords': 6075}),
    ('=Sessão de terror', '/discover/movie', {'with_genres': 27}),
    ('=Noite em família', '/discover/movie', {'with_genres': 10751}),
    ('=Curtinhos (menos de 100 min)', '/discover/movie', {'with_runtime.lte': 100, 'with_runtime.gte': 70}),
    ('=Épicos de fôlego (2h30+)', '/discover/movie', {'with_runtime.gte': 150}),
    ('=Clássicos dos anos 90', '/discover/movie', {'primary_release_date.gte': '1990-01-01', 'primary_release_date.lte': '1999-12-31'}),
    ('=Clássicos dos anos 80', '/discover/movie', {'primary_release_date.gte': '1980-01-01', 'primary_release_date.lte': '1989-12-31'}),
    ('=Viradas de roteiro', '/discover/movie', {'with_keywords': 10183}),
    ('=Premiados e aclamados', '/discover/movie', {'vote_count.gte': 3000, 'sort_by': 'vote_average.desc'}),
    ('=Animes', '/discover/tv', {'with_keywords': 210024}),
    ('=Séries de crime', '/discover/tv', {'with_genres': 80}),
    ('=Doramas e séries coreanas', '/discover/tv', {'with_original_language': 'ko'}),
    ('=Ação e aventura em série', '/discover/tv', {'with_genres': 10759, 'without_genres': '10763,10764,10766,10767'}),
    ('=Ficção científica e fantasia', '/discover/tv', {'with_genres': 10765, 'without_genres': '10763,10764,10766,10767'}),
    ('=Mistério e suspense', '/discover/tv', {'with_genres': 9648, 'without_genres': '10763,10764,10766,10767'}),
    ('=Comédias para maratonar', '/discover/tv', {'with_genres': 35, 'without_genres': '16,10763,10764,10766,10767'}),
    ('=Dramas aclamados', '/discover/tv', {'with_genres': 18, 'without_genres': '10763,10764,10766,10767', 'vote_count.gte': 500, 'sort_by': 'vote_average.desc'}),
    ('=Séries de super-heróis', '/discover/tv', {'with_keywords': 9715, 'without_genres': '10763,10764,10766,10767'}),
    ('=Séries médicas e hospitalares', '/discover/tv', {'with_keywords': 11612, 'without_genres': '10763,10764,10766,10767'}),
    ('=Animações adultas e clássicas', '/discover/tv', {'with_genres': 16, 'without_keywords': 210024, 'without_genres': '10763,10764,10766,10767'}),
    ('=Séries documentais', '/discover/tv', {'with_genres': 99, 'without_genres': '10763,10764,10766,10767'}),
    ('=Séries em família', '/discover/tv', {'with_genres': 10751, 'without_genres': '10763,10764,10766,10767'}),
    ('=Séries de época e guerra', '/discover/tv', {'with_genres': 10768, 'without_genres': '10763,10764,10766,10767'}),
    ('=Minisséries e histórias fechadas', '/discover/tv', {'with_type': 2, 'without_genres': '10763,10764,10766,10767'}),
]
SAGAS = [('Velozes & Furiosos', 9485), ('Missão: Impossível', 87359), ('Harry Potter', 1241), ('Vingadores', 86311),
         ('Star Wars', 10), ('O Senhor dos Anéis', 119), ('John Wick', 404609), ('Jurassic Park', 328),
         ('Piratas do Caribe', 295), ('Transformers', 8650), ('Toy Story', 10194), ('Shrek', 2150)]


def entry(kind, item):
    date_field, title_field, original_field = ('first_air_date', 'name', 'original_name') if kind == 's' else ('release_date', 'title', 'original_title')
    return f"{kind}\t{item['id']}\t{item.get('vote_average', 0):.1f}\t{(item.get(date_field) or '')[:4]}\t{clean(item.get(title_field))}\t{clean(item.get(original_field))}"


themes = ['# Fileiras temáticas (=) e sagas (@) do TMDB, gerado em ' + today.isoformat()]
for name, path, query in THEMES:
    kind = 's' if path.endswith('/tv') else 'f'
    themes.append(name)
    for page in (1, 2):
        opts = {'sort_by': 'popularity.desc', 'include_adult': 'false', 'page': page, 'vote_count.gte': 100}
        opts.update(query)
        themes += [entry(kind, item) for item in get(path, **opts)['results']]
for name, collection in SAGAS:
    themes.append('@' + name)
    themes += [entry('f', item) for item in sorted(get(f'/collection/{collection}').get('parts', []), key=lambda p: p.get('release_date') or '9999')]
(output.parent / 'temas.tsv').write_text('\n'.join(themes) + '\n', encoding='utf8')
print(f'{len(THEMES) + len(SAGAS)} listas em temas.tsv.')
