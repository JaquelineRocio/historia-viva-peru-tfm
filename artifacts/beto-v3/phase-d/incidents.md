# Incidentes D

- Antes del primer ajuste, `execute_beto_phase_d_v3.py` terminó con `FileExistsError` al intentar actualizar `development-current.json` mediante el helper histórico de escritura exclusiva. El comando midió 2,8556459 s; no inició modelo ni trayectoria GPU. Se corrigió únicamente la actualización del estado a escritura temporal y reemplazo. Los snapshots ya creados se reutilizaron. Este tiempo de preparación CPU no se imputa como entrenamiento GPU; los cuatro recibos de entrenamiento incluyen su propio preflight, carga, guardado y recarga.

No se reconstruyen incidentes históricos ni duraciones de fallos antiguos desconocidas. Los errores de entrenamiento, si los hubiera, quedan en los recibos `outputs/beto-v3/phase-c/attempts/` y en los logs de cada ejecución.
