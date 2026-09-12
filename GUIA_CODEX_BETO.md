# Guía de ejecución local para BETO después de la fase H

## Cómo empezar

Abre Codex en el repositorio que contiene el proyecto y adjunta esta guía y `informe-fase-H(1).md`. El objetivo es preparar una prueba controlada de reponderación por familia y ejecutarla únicamente después de aprobar su registro prospectivo. No hace falta instalar plugins, migrar a la nube ni actualizar dependencias para comenzar.

El informe complementario explica la evidencia y las limitaciones. Esta guía es un contrato de ejecución propuesto: no es un programa ejecutable ni demuestra que sus rutas y comandos existan. Codex debe resolver las rutas, inspeccionar las interfaces y reutilizar el código real. No hay acceso implícito desde este chat a tu equipo, tus discos o tu GPU.

### Prompt de arranque para pegar en Codex

```text
Lee GUIA_CODEX_BETO.md, el informe de fase H y las instrucciones AGENTS.md
aplicables. Ejecuta solamente P0, P1 y P2. Puedes inspeccionar el repositorio,
preparar artefactos de diagnóstico, implementar el cambio mínimo de pérdida
y ejecutar pruebas sintéticas sin entrenar BETO. Preserva mis cambios existentes.

Objetivo: dejar lista una única corrida I/42 que cambie solo los pesos por familia
respecto de H/42, con el mismo train congelado. Usa H como control del efecto de
la intervención y R2 como referencia de las cuatro puertas originales.

No leas contenido ni etiquetas de S. No cambies datos, referencias, receta,
presupuesto, reservas ni permisos. No instales o actualices dependencias sin
necesidad y autorización. No lances entrenamientos, búsquedas de hiperparámetros
ni subagentes. No hagas commit o push automáticamente.

Trabaja por fases con salidas verificables. Reutiliza predicciones y cachés
válidas. Mantén un estado breve para reanudar y usa el ledger original como
autoridad. Resuelve detalles rutinarios; pregunta solo si una decisión cambia
el alcance científico, requiere permisos o impide continuar con seguridad.

Termina con: rutas verificadas, métricas reproducidas, diff mínimo, pruebas
ejecutadas y sus resultados, limitaciones, saldo conciliado y comando real de
entrenamiento propuesto. Detente antes de entrenar para que apruebe el
registro prospectivo y el presupuesto. No declares ejecutado lo solo preparado.
```

## 1 Estado conocido y reglas invariantes

Fuente factual: informe de fase H aportado. Si el ledger actual es posterior, reportar la diferencia y utilizar el estado vigente, sin sobrescribir la historia.

| Campo | Valor de referencia |
| --- | --- |
| H/42 F1 macro V original | 0.547008 |
| R2/42 F1 macro V original | 0.532392 |
| H menos R2 | +0.014616 |
| H peor delta por clase | −0.081013 en organización |
| H checkpoint seleccionado | Época 4 de 20 según V original |
| Train H congelado | 1095 unidades |
| V original | 444 unidades y 8 familias reportadas |
| Trayectorias acumuladas | 13 de 18 |
| Reserva de cierre | 3 trayectorias |
| Saldo desarrollo | 3581.27 s |
| Saldo global | 15585.33 s |
| Anotación | 1079 de 1280 únicas; 200 de las 201 libres reservadas para S |

Reglas de ejecución:

- S permanece cerrada. Solo utilizar el manifiesto de metadatos permitido por el protocolo para comprobar separación. No leer, hashear de nuevo, preprocesar, indexar ni tokenizar su contenido durante desarrollo.
- No corregir T o V dentro del experimento de pesos. Registrar observaciones aparte. Una corrección material exige otra versión y otro protocolo.
- No confundir 201 plazas libres con 201 anotaciones disponibles para desarrollo: queda una fuera de S. Auditar unidades ya anotadas no crea nuevas unidades, pero sí consume revisión y debe registrarse según el protocolo.
- Una semilla nueva es una trayectoria nueva. Un fallo o reinicio no borra el consumo. Las pruebas con actualizaciones reales del modelo deben clasificarse antes de ejecutarlas; no ocultarlas como smoke tests.
- No escoger una semilla favorable, cambiar umbrales tras ver I ni rescatar una corrida fallida usando v3.1.
- No prometer F1 de 0.70. El entrenamiento perfecto no demuestra que BETO carezca de limitaciones de representación.

## 2 Archivos de contexto y memoria operativa

No crear una infraestructura nueva si el repositorio ya dispone de estos equivalentes. Los siguientes nombres son propuestas relativas al repositorio, no rutas verificadas:

| Archivo o registro | Función |
| --- | --- |
| `AGENTS.md` existente | Reglas cortas del proyecto; preservar y ampliar solo lo pertinente |
| `docs/plan-beto-codex.md` | Copia de la guía aprobada y decisiones humanas |
| `artifacts/beto-v3/phase-i-family/STATE.md` | Estado breve, fase, bloqueos y siguiente paso |
| `.../preflight.json` | Entorno, rutas, hashes autorizados y conciliación |
| `.../preregistration.json` | Configuración científica, autorización y límites |
| `.../weights-audit.json` | Coeficientes, invariantes y grupos pequeños |
| `.../evaluation.json` | Contrastes, cuatro puertas y estadísticas |
| Ledger y recibos existentes | Única autoridad presupuestaria |
| Salidas de la corrida | Checkpoints y predicciones fuera de Git según las normas vigentes |

Mantener `STATE.md` en unas 60 líneas como objetivo práctico, con enlaces al detalle. Campos mínimos: fase; run_id; hashes del protocolo, datos y configuración; estado de autorización; ruta del ledger; saldo; proceso y comando; última salida válida; pruebas; pendientes; siguiente acción permitida. El número de líneas no es un límite de Codex.

Al cambiar de sesión: leer instrucciones aplicables, estado y registro prospectivo; comprobar proceso activo y coherencia del ledger; continuar desde la primera tarea pendiente. No volver a investigar todo ni relanzar un proceso ya activo. AGENTS.md es apropiado para instrucciones persistentes, pero no sustituye los controles del programa. [OpenAI, AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## 3 P0 Inventario y verificación del entorno

Entradas: informe H, instrucciones del repositorio, configuración existente, ledger.

1. Identificar raíz de trabajo, shell, sistema operativo e instrucciones aplicables. Ver estado Git y preservar cambios ajenos. Buscar con `rg` en rutas pertinentes; no seguir junctions ni recorrer S indiscriminadamente.
2. Localizar artefactos indicados por H: `preregistration.json`, `train-h80-v1.json`, `checkpoint-04-data-freeze.json`, `gate-seed-42.json`, `final-analysis.json`, recibos, predicciones y checkpoints de R2 y H.
3. Confirmar rutas reales y el destino de outputs. El antecedente `E:/BETO/outputs` no prueba que el enlace siga accesible. No convertir rutas Windows a WSL por conjetura ni migrar el entorno.
4. Identificar el intérprete Python exacto del proyecto; registrar versiones instaladas de PyTorch, Transformers, tokenizer, CUDA y controlador cuando estén disponibles. Comprobar GPU desde ese intérprete, además de la visibilidad del dispositivo. No mostrar secretos ni volcar variables de entorno completas.
5. Comprobar espacio libre y estimar espacio de checkpoints desde H. No borrar checkpoints para obtener espacio sin autorización específica.
6. Conciliar tiempo global, desarrollo, reserva y trayectorias. No inventar nuevos criterios de contabilización.

Salida: `preflight.json` y mapa de rutas verificadas. Parar si falta acceso, hay permisos insuficientes, hashes incompatibles o ledger contradictorio. No sustituir GPU por CPU ni otro modelo para continuar sin autorización.

## 4 P1 Reproducción y auditoría acotada

Entradas: referencias originales, predicciones R2/H, metadatos de familias y train H.

### Reproducción automática

- Unir por `unit_id`, nunca por posición accidental. Exigir 444 IDs únicos, igualdad de conjuntos y referencias coincidentes entre sistemas. No aplicar una unión interna que silenciosamente elimine unidades.
- Orden fijo de clases:
  1. `campanias_conflictos_militares`
  2. `contexto_colonial_antecedentes`
  3. `crisis_ideas_emancipadoras`
  4. `liderazgos_diplomacia_proyectos`
  5. `no_relevante`
  6. `organizacion_consecuencias_republicanas`
  7. `participacion_social_regional`
- Reproducir matrices, F1 por clase y macro; comprobar soportes `[63,23,75,32,168,23,60]`, 169 errores R2 y 161 H. Tolerancia de 1e-6 para cifras redondeadas del informe; no para decidir las puertas.
- Recuperar valores completos del evaluador original. Conservar referencias v3.1 separadas y sin reseleccionar checkpoint.
- Verificar 1095 ejemplos de T, 142 de organización y 92 de esa clase en la familia dominante. Resolver nombres reales de familia desde metadatos.
- Generar transiciones por unidad: ambos correctos, ambos incorrectos, corregido por H y deteriorado por H. No se pueden derivar sus cuentas exactas únicamente de las matrices globales.

Si las predicciones están completas y verificadas, cero nuevas inferencias. Si faltan, documentar el hueco y proponer recuperación presupuestada desde el checkpoint, sin volver a entrenar. Hasta aprobarla, no marcar la reproducción como completada.

### Revisión humana

Crear un conjunto sin duplicados de los 37 errores H en crisis↔organización, colonial↔participación y campañas↔participación, unido a las 23 referencias de organización. Se esperan 56 IDs: cuatro organización→crisis ya están en ambos conjuntos. Verificarlo en datos, no forzar el número.

Preparar texto y contexto permitido sin predicción ni etiqueta propuesta en la primera revisión. Registrar por separado: suficiencia de información, ambigüedad, etiqueta humana, extracción y notas. Priorizar los 15 errores crisis↔organización si hay poco tiempo. No estimar prevalencia de ruido con esta muestra dirigida.

Codex puede preparar, deduplicar y consolidar. La interpretación histórica corresponde a la persona revisora. Si no hubo revisión humana, escribir `human_review: pending`, nunca “validado”. Un desacuerdo no permite cambiar V. Una contaminación o extracción materialmente defectuosa bloquea la corrida; otros hallazgos pendientes se declaran como limitación.

Salida: métricas reproducidas, transiciones, conjunto de auditoría y límites. No exigir nuevas curvas por ejemplo si el entrenamiento previo no las guardó.

## 5 P2 Implementación mínima y registro prospectivo

### Intervención

Llamar I al candidato para distinguirlo de H. I usa las mismas 1095 unidades de H y parte del mismo BETO preentrenado, no del checkpoint ajustado de H.

Definiciones calculadas solo sobre T:

```text
c      = clase del ejemplo
g      = familia del ejemplo
N_c    = número de ejemplos de clase c
G_c    = número de familias con al menos un ejemplo de clase c
n_cg   = número de ejemplos de clase c y familia g
a_c    = peso de clase usado por H
r_i    = N_c / (G_c * n_cg)
w_i    = a_c * r_i

Para cada clase c:
  sum(w_i para i de clase c) = a_c * N_c
Para cada combinación observada c,g:
  sum(w_i para i de c,g) = a_c * N_c / G_c
```

Esta conservación es de coeficientes sobre T. No equivale a igualar gradientes ni garantiza masa efectiva idéntica bajo reducciones por microlote. Implementar la pérdida por ejemplo y multiplicar por `r_i` una sola vez. Si la pérdida ya incorpora `a_c`, no volver a aplicarlo.

Conservar el denominador real de H y su acumulación, incluyendo el último grupo incompleto. No dividir adicionalmente entre `sum(r_i)` o `sum(w_i)`. No asumir que `CrossEntropyLoss(weight=..., reduction="mean")` equivale a promediar pérdidas ponderadas: revisar la semántica y la versión local. [PyTorch, CrossEntropyLoss](https://docs.pytorch.org/docs/2.14/generated/torch.nn.CrossEntropyLoss.html).

No añadir muestreo ponderado, clipping de pesos, focal loss, regularización, contexto, nuevo tokenizer o nuevas etiquetas. Si la normalización existente tiene un defecto, documentarlo y pedir un protocolo separado; no arreglarlo silenciosamente junto a los pesos.

### Configuración científica que debe permanecer igual

BETO/tokenizer pinados; train H congelado; V original; seed 42; 20 épocas; longitud máxima 384; lr 2e-5; microlote 2 y acumulación 8; AdamW y AMP de H; misma fórmula de warmup, pasos, evaluaciones y selección de checkpoint. Mantener desempate original; si no está documentado, resolverlo antes de entrenar y dejar constancia.

Registrar también inicialización de la cabeza, generadores aleatorios, orden de lotes, dropout y flags del backend. Una misma semilla no garantiza identidad entre entornos distintos. [PyTorch, Reproducibility](https://docs.pytorch.org/docs/2.14/notes/randomness.html).

### Pruebas obligatorias sin entrenar BETO

| Prueba | Condición de aprobación |
| --- | --- |
| Modo sin reponderación | Misma pérdida y gradiente que H con r=1 |
| Conservación por clase | Sumas analíticas coincidentes en precisión numérica |
| Igualación por familia | Misma suma de coeficientes en familias de una clase |
| Una familia por clase | Todos sus multiplicadores son 1 |
| Grupos pequeños y extremos | Pesos finitos, positivos y diagnóstico explícito |
| Acumulación | Sigue la semántica de H, incluido lote incompleto |
| IDs y etiquetas | Duplicados, ausencias o valores desconocidos producen error |
| Evaluador | Reproduce las matrices y scores previos |
| Ejecución repetida | No duplica un run terminado ni una entrada de ledger |
| Protección de datos | La rutina de desarrollo no abre contenido de S |
| Guardado y recuperación | Configuración incompatible impide reanudar |

Usar tensores sintéticos y módulos mínimos en CPU para pruebas de gradiente y recuperación. La igualdad de acumulación con un lote grande se exige solo si esa es la semántica real de H; no reescribirla para hacer pasar una prueba incorrecta.

Guardar min, mediana, máximo y distribución de `r_i`, grupos de un ejemplo y tamaño efectivo de muestra `(sum(w))**2/sum(w**2)` global y por clase. No introducir un umbral de clipping después de ver V. Si un extremo hace inaceptable el diseño, proponer una enmienda antes de entrenar.

### Aprobación antes de P3

Preparar un `preregistration.json` con rutas resueltas, hashes autorizados, versiones, intervención, denominador documentado, puertas, receta, selección de checkpoint, contrastes, estadística, tiempos y reglas de parada. Usar identificadores de autorización humanos; Codex no se autoautoriza.

Asignación propuesta: 400 s de comprobaciones computacionales, 2200 s de corrida incluida evaluación y guardado, 100 s de análisis; contingencia 881.27 s. Conciliar con los recibos reales. El coste de planificación de Codex y revisión humana se informa aparte sin redefinir el ledger.

Al terminar P2: presentar diff mínimo, pruebas, consumo actual, limitaciones y comando real inspeccionado. No inventar una CLI de entrenamiento. Detenerse para aprobar P3.

## 6 P3 Una sola corrida I con semilla 42

Solo después de aprobación explícita:

1. Revalidar hashes, presupuesto, autorización, GPU y espacio.
2. Adquirir bloqueo exclusivo por experimento y GPU mediante el mecanismo existente o uno portátil probado. Verificar PID, hora de inicio y comando antes de tratar un bloqueo como obsoleto.
3. Registrar el inicio en el ledger; ejecutar una única vez el comando aprobado. Guardar logs en disco y mostrar resúmenes, no cada microlote.
4. Usar checkpoints reanudables. Si hay desconexión, comprobar primero si sigue vivo el proceso. No relanzar automáticamente.
5. Antes de agotar el límite, guardar y detener ordenadamente con margen medido. Un entrenamiento incompleto queda `incomplete`, no `passed`.
6. Al terminar, comprobar exit code, 20 épocas completas según receta, selección por V, predicciones completas y recibo conciliado.

No editar código ejecutado o configuración durante la corrida. No ejecutar otra corrida ni inferencia pesada en la misma GPU. No vaciar caché GPU en cada microlote ni instalar aceleradores durante la ejecución.

Ante fallo: guardar evidencia, diagnosticar y proponer una corrección mínima. No entrar en un bucle de entrenar–fallar–reintentar. Toda continuación con consumo real requiere comprobar de nuevo autorización, clasificación de trayectoria y saldo.

## 7 P4 Evaluación y decisión

### Comparaciones

- `I - H`: efecto observado de reponderar bajo datos y receta comunes.
- `I - R2`: aceptación frente a la referencia histórica. Incluye diferencias acumuladas de datos y pesos; no atribuir todo a familias.

Cuatro puertas originales, evaluadas conjuntamente con precisión completa:

```text
macro_f1_I >= 0.552392
mean_f1_I_six_historical > 0.486179
mean_f1_I_five_targets > 0.434209
min(f1_I[class] - f1_R2[class]) >= -0.05
```

Seis históricas: todas menos `no_relevante`. Cinco objetivo: colonial, crisis, liderazgos, organización y participación. El baseline por clase se recupera del evaluador, no de la tabla redondeada.

### Estadística congelada propuesta

1. Estadístico: diferencia de F1 macro de siete etiquetas a partir de conteos conjuntos, no promedio de F1 por familia.
2. Permutación principal exploratoria bilateral I–H. Con ocho bloques válidos, enumerar las 256 máscaras. Cada máscara intercambia sistemas para todas las unidades de las familias seleccionadas, sin cambiar referencias. Calcular `p = count(abs(delta_perm) >= abs(delta_obs)) / 256`, incluyendo empates. Aplicar una tolerancia numérica documentada de 1e-12 a la comparación. No usar la corrección +1 de Monte Carlo para enumeración completa.
3. Exigir justificación de intercambiabilidad bajo la nula y agrupación pertinente. Si familias comparten fuente, resolver bloques antes de la corrida; no contar fragmentos como bloques independientes. Si hay G bloques, enumerar `2**G` cuando sea viable y documentar cualquier cambio prospectivo.
4. Bootstrap pareado: 10000 réplicas, ocho familias extraídas uniformemente con reemplazo, mismas extracciones para ambos sistemas; semilla estadística 20260911 en un generador separado. Conservar las siete etiquetas y usar `zero_division=0`. IC percentil 95 %, cuantiles lineales; registrar frecuencia de ausencia de soporte por clase y valores no finitos. No eliminar réplicas desfavorables ni reextraer hasta que aparezcan todas las clases.
5. Sensibilidad: retirar una familia de V por vez, sin entrenar; publicar los ocho deltas, soportes, mínimo, máximo y cambios de signo. No llamarlo validación cruzada de entrenamiento.
6. Repetir I–R2 como análisis secundario. No seleccionar retrospectivamente cuál contraste o valor p presentar.

Optimización exacta: construir matrices enteras `[sistema, familia, referencia, predicción]` de dimensión 7×7 por sistema y familia. Las sumas o intercambios de matrices permiten todas las réplicas en CPU. Probar que este cálculo coincide con una implementación sencilla por IDs. No recalcular logits ni llamar a BETO dentro del bootstrap.

Pruebas del análisis: sistemas idénticos dan delta 0 y p 1; invertir sistemas cambia el signo y conserva p bilateral; una máscara y su complemento producen deltas opuestos; mantener etiquetas ausentes; duplicar un bloque en bootstrap duplica sus conteos, no lo deduplica; usar la misma extracción para ambos modelos.

Estas pruebas son exploratorias: ocho clústeres son pocos y V ya se usó para seleccionar checkpoints y candidatos. No afirmar cobertura garantizada del IC ni significación confirmatoria por tener p<0.05. La revisión de [Dror et al.](https://aclanthology.org/P18-1128/) sustenta la elección cuidadosa de pruebas; [Cameron y Miller](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015_February.pdf) fundamentan la precaución con clústeres; [Cawley y Talbot](https://jmlr.org/papers/v11/cawley10a.html) documentan sesgo de selección.

### Resultado

Si falla cualquier puerta, no promover I. Si pasa, denominarlo candidato provisional y reportar su incertidumbre, sin inventar nuevas puertas basadas en p o IC. Una corrida incompleta o métricas no reproducibles no permite decisión. Salidas mínimas: configuración, checkpoint, scores completos, transiciones, cuatro booleanos, ambos contrastes, estadística, consumo y limitaciones.

## 8 P5 Confirmación y cierre condicionados

No ejecutar P5 automáticamente. Recuperar primero la preinscripción de cierre y la lista de checkpoints existentes por modelo y semilla. Presentar tabla exacta de corridas faltantes, duración prevista, saldo de cada bolsa y autorizaciones necesarias.

Para estimar el efecto multisemilla de pesos se necesitan controles H y candidatos I con las mismas semillas. Si solo existen H/42 e I/42, tres pares requieren cuatro corridas más: H/43, I/43, H/44, I/44. No caben automáticamente por el simple hecho de quedar cuatro plazas; una es de desarrollo y su tiempo restante puede ser insuficiente.

Tres nuevas corridas solo de I describen estabilidad de I, no un efecto pareado contra H. Si existen R2 con esas semillas, una comparación pareada contra R2 tiene otro alcance: el cambio acumulado desde R2. No mezclar controles o semillas para crear una apariencia de pareamiento.

La regla de agregación, elección del procedimiento final y autorización para abrir S se fijan antes de ejecutarlo. Reportar todos los resultados, media y desviación estándar muestral; no presentar la mejor semilla como estimación de estabilidad. Una media favorable en V no demuestra generalización independiente.

## 9 Consejos de eficiencia específicos

- Un agente principal inicialmente. Las lecturas y comprobaciones independientes pueden ejecutarse en paralelo sin delegación, evitando competir por recursos. Si se autoriza expresamente un subagente, asignarle revisión acotada y de solo lectura; no otra GPU, ledger o edición compartida. [OpenAI, Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- No enviar toda la tesis y todos los logs en cada turno. Facilitar guía, estado y rutas precisas; abrir detalles cuando una comprobación los necesite.
- Mantener scripts pequeños y reutilizables; evitar construir un framework, una interfaz o un plugin para una sola corrida.
- Cachear solo con claves verificables: hash de datos permitidos, tokenizer, normalización, truncado, longitud y versión pertinente. No usar cachés de S.
- Distinguir acelerar Codex de acelerar BETO. Reducir nivel de razonamiento para tareas mecánicas puede reducir latencia del agente, pero no acelera la GPU de entrenamiento. Reservar razonamiento alto para decisiones científicas y fallos difíciles, según opciones disponibles.
- Mantener receta y backend de H. AMP ya está activo; volver a recomendarlo no aporta un ahorro nuevo. No introducir `torch.compile`, TF32, BF16, bucketing o cambio de lote como si fueran gratuitos y equivalentes.
- No bajar a cuatro épocas porque H seleccionó la cuarta: limitar retrospectivamente la búsqueda cambia el procedimiento. Conservar 20 y seleccionar según la regla congelada; estudiar early stopping en otro protocolo si se autoriza.
- Una prueba se marca `passed` solo con comando ejecutado, exit code y resultado. “Parece correcto” no sustituye evidencia.
- Ante un bloqueo de permisos o acceso, detenerse y pedir la habilitación pertinente. Nunca recomendar desactivar todas las protecciones para ganar tiempo.

## 10 Checklist de entrega de Codex

- [ ] No se leyó contenido ni etiquetas de S.
- [ ] Instrucciones existentes y cambios del usuario preservados.
- [ ] R2 y H reproducidos con IDs y referencias completas.
- [ ] Revisión humana separada y su estado declarado.
- [ ] Solo cambió la reponderación prevista.
- [ ] Reducción y acumulación de pérdida comprobadas.
- [ ] Datos, configuración, versiones y autorizaciones trazables.
- [ ] Una corrida inicial como máximo, sin duplicados ocultos.
- [ ] Presupuesto vigente y reservas respetados.
- [ ] Puertas calculadas automáticamente con precisión completa.
- [ ] Estadística por familias presentada con sus supuestos y límites.
- [ ] Salida de consola, recibos y checkpoint respaldan cada afirmación.
- [ ] Próxima acción separada de lo ya ejecutado.

Si I no pasa, la entrega correcta es un resultado negativo reproducible y una propuesta de continuación condicionada. No seguir probando hasta agotar reservas ni prometer alcanzar 0.70.
