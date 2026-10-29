# Destaques do Cine

`destaques.tsv` lista os lançamentos mais bem avaliados no TMDB (filmes dos últimos 12 meses e séries com episódios no último ano, mínimo de 150 votos). O app Cine baixa este arquivo e mostra nos Destaques os títulos que existem no catálogo de cada aparelho.

A lista é gerada automaticamente toda segunda e quinta pelo GitHub Actions (`.github/workflows/destaques.yml`), usando o segredo `TMDB_KEY` do repositório. Para gerar na hora: aba Actions → Destaques do TMDB → Run workflow.

Este produto usa a API do TMDB, mas não é endossado nem certificado pelo TMDB.
