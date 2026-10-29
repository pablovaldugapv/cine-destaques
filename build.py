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
    params['language'] = 'pt-BR'
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
