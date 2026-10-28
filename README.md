# API de transacciones — comparación de estrategias de consulta

API de prueba para un trabajo académico de estadística. El objetivo no es un sistema bancario real, sino **medir el tiempo de respuesta real** de un mismo endpoint cuando se resuelve de tres maneras distintas.

## De qué se trata

Un servicio mínimo en FastAPI que lista las **últimas 50 transacciones** de una cuenta. Hay 1.000.000 de filas en SQLite y un caché opcional en Redis.

Las tres estrategias comparan, sobre la misma pregunta, el costo de:

| Estrategia | Qué hace |
|---|---|
| `direct` | Escaneo completo de la tabla (`NOT INDEXED`). No usa el índice. |
| `index` | La misma consulta, pero aprovechando `idx_account_date (account_id, created_at DESC)`. |
| `cache` | Busca `tx:{account_id}` en Redis. Si no está, consulta con índice, guarda el JSON 300 s y responde. |

El servidor mide el tiempo con `time.perf_counter()` desde que empieza la lógica hasta que la lista está lista. Ese `elapsed_ms` es el dato que se usa en el análisis. No hay `sleep` ni retrasos artificiales.

## Por qué existe

En estadística aplicada a sistemas interesa **comparar distribuciones de tiempos**, no solo un promedio aislado. Para eso hace falta un experimento controlado:

- misma API, mismo endpoint, mismos datos
- tres tratamientos (`direct`, `index`, `cache`)
- varias mediciones repetibles (semillas fijas: `42` para los datos, `7` para el banco de pruebas)

Así se puede argumentar, con evidencia, que el índice reduce el trabajo de búsqueda y que el caché evita ir a disco cuando el resultado ya está en memoria.

## Para qué sirve

1. Generar **10 tiempos reales por estrategia** listos para copiar a Excel, R o Python.
2. Contrastar hipótesis del tipo: *el acceso por índice es más rápido que el escaneo; el hit de caché es más rápido que ambos*.
3. Documentar un caso simple de por qué, en bases grandes, un índice y un caché cambian la latencia percibida.

`bench.py` hace flush del caché, calienta cada estrategia, fuerza hits en `cache` y escribe `resultados.csv` (`strategy`, `account_id`, `elapsed_ms`).

## Cómo ejecutarlo

Hace falta Python 3.11+ y Redis en el puerto 6379.

```
docker run -d -p 6379:6379 redis
pip install -r requirements.txt
python seed.py
uvicorn main:app
python bench.py
```

`seed.py` puede tardar: inserta 1.000.000 de filas en lotes de 50.000 y después crea el índice.

## Endpoints

- `GET /transactions/{account_id}?strategy=direct|index|cache`
- `POST /cache/flush`

Respuesta típica:

```json
{
  "strategy": "index",
  "account_id": 42,
  "rows": 50,
  "elapsed_ms": 1.234,
  "cache_hit": null,
  "data": []
}
```

`cache_hit` es `true`/`false` solo con `strategy=cache`; en las demás es `null`.
