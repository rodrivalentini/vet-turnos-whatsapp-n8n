# 🐾 Vet Appointment Agent (n8n)

Asistente de turnos para veterinarias por **WhatsApp**, construido con **n8n**. Un agente de IA conversa con el cliente para sacar y reprogramar turnos, y una persona de la clínica aprueba cada turno antes de que el cliente reciba la confirmación.

> Agente de IA en n8n para gestionar turnos veterinarios por WhatsApp: agenda y reprograma con Google Calendar y Airtable, aprobación humana por Gmail, avisos con plantillas y recordatorios automáticos.

## ✨ Qué hace

- **Saca turnos nuevos** conversando en lenguaje natural: pide los datos, consulta la disponibilidad en Google Calendar y propone un horario libre.
- **Reprograma turnos** existentes, ya sea por chat o tocando el botón de un mensaje de WhatsApp.
- **Aprobación humana (human-in-the-loop):** todo turno queda `PENDIENTE` y la clínica recibe un mail. El cliente solo recibe la confirmación cuando alguien cambia el estado a `CONFIRMADO` en Airtable.
- **Avisos automáticos** con plantillas aprobadas de WhatsApp: confirmación, cancelación y agradecimiento por la visita.
- **Recordatorios diarios** de los turnos del día siguiente, con botones de respuesta rápida (asistiré, reprogramar, cancelar).
- **Manejo de errores:** los fallos se registran en una tabla de Airtable y el cliente nunca ve datos técnicos.
- **Seguridad:** el agente no da diagnósticos ni medicación; ante una urgencia deriva a la clínica. Los botones validan el turno con doble clave (ID del mensaje + número del cliente), así nadie puede tocar turnos ajenos.

## 🧩 Arquitectura

El proyecto es un único archivo de n8n con cuatro flujos independientes:

| Flujo | Disparador | Qué hace |
|---|---|---|
| **1. Agente de turnos** | Mensaje de WhatsApp | Clasifica el mensaje. El texto va al agente de IA; los botones van a una rama sin IA (cancelar, reprogramar, asistir, reservar). |
| **2. Aprobación por Gmail** | Turno nuevo en Airtable | Envía un mail a la clínica con los datos del turno y un link al registro. |
| **3. Avisos de estado** | Cambio del campo *Estado* en Airtable | Según el estado, actualiza o borra el evento de Calendar y envía la plantilla de WhatsApp que corresponde. |
| **4. Recordatorios** | Programado, una vez al día | Busca los turnos confirmados de mañana y envía el recordatorio con botones. |

```
Cliente ──WhatsApp──▶ Trigger ──▶ ¿texto o botón?
                                    │            │
                                  texto        botón ──▶ rama determinista (sin IA)
                                    ▼
                              Agente de IA ◀──▶ Google Calendar + Airtable
                                    │
                         turno PENDIENTE en Airtable
                                    │
                    mail a la clínica ──▶ cambia Estado a CONFIRMADO
                                                     │
                                  avisos de estado ──▶ plantilla de WhatsApp
```

## 🛠️ Tecnologías

- [n8n](https://n8n.io/)
- WhatsApp Business Cloud API (Meta)
- OpenAI (modelo de chat del agente, configurable en el nodo)
- Airtable (turnos, clientes y errores)
- Google Calendar
- Gmail

## 📋 Requisitos

- Una instancia de n8n (cloud o self-hosted). El webhook de WhatsApp necesita una URL pública con HTTPS.
- Cuenta de WhatsApp Business con acceso a la Cloud API y un número configurado.
- Cuenta de OpenAI con API key.
- Base de Airtable y un Personal Access Token con permisos de lectura y escritura sobre esa base.
- Cuenta de Google con un calendario dedicado para los turnos y acceso a Gmail.

## 🗄️ Estructura de Airtable

## 👀 Demo de la base de datos

Podés ver la estructura de las tablas (`Turnos`, `Clientes` y `Errores`) en una copia de solo lectura con datos de ejemplo:

[Ver la base en Airtable](https://airtable.com/appsSVa8o9R9nB4Kk/shr2gFESFvB2RIzBz)

Todos los datos de la demo son ficticios.

### Tabla `Turnos`

| Campo | Tipo | Uso |
|---|---|---|
| Turno | Texto | Título: `ESTADO - Nombre Apellido - Mascota` |
| Nombre / Apellido | Texto | Datos del cliente |
| WhatsApp | Texto | Número del cliente (`wa_id`), lo completa el sistema |
| Mascota | Texto | Nombre de la mascota |
| Motivo | Texto | Motivo de la consulta |
| Fecha turno | Fecha | Formato `YYYY-MM-DD` |
| Hora turno | Texto | Formato `HH:mm` |
| Estado | Selección única | `PENDIENTE`, `CONFIRMADO`, `CANCELADO`, `ATENDIDO` |
| Calendar Event ID | Texto | ID del evento en Google Calendar |
| Mensaje ID | Texto | ID del mensaje de WhatsApp de la última plantilla enviada |
| Mensaje ID recordatorio | Texto | ID del mensaje del recordatorio |
| Último aviso | Texto | Último estado notificado (evita avisos duplicados) |
| Recordatorio enviado | Checkbox | Evita recordatorios duplicados |
| Hilo de correo | Texto | Thread ID del mail de aprobación |
| Cliente | Link a `Clientes` | Cliente asociado |
| Creado | Created time | Dispara el flujo de aprobación |
| Última modificación | Last modified time | Dispara el flujo de avisos. Configurarlo solo sobre el campo **Estado**. |

### Tabla `Clientes`

Un registro por cliente, vinculado desde `Turnos`.

### Tabla `Errores`

| Campo | Tipo |
|---|---|
| Resumen | Texto |
| Fecha | Fecha y hora |
| Flujo | Texto |
| Mensaje de error | Texto largo |
| WhatsApp cliente | Texto |
| Estado | Selección única: `Nuevo`, `Revisado`, `Resuelto` |

## 💬 Plantillas de WhatsApp

Hay que crearlas y aprobarlas en Meta (idioma `es_AR`). Las que se envían fuera de la ventana de 24 h usan estos nombres:

| Plantilla | Variables del cuerpo |
|---|---|
| `turnos_confirmados` | nombre, mascota, fecha, hora |
| `turno_cancelado` | nombre, mascota, fecha, hora |
| `gracias_por_la_visita` | nombre, mascota |
| `recordatorio_turno` | nombre, mascota, fecha, hora |

`recordatorio_turno` lleva **3 botones de respuesta rápida**: *Sí, asistiré*, *Reprogramar* y *Cancelar turno*. La plantilla de cancelación puede incluir un botón *Reservar otro horario*.

## 🚀 Instalación

1. **Importá el workflow** en n8n: *Workflows → Import from file* y elegí `vet-turnos-whatsapp-n8n.json`.
2. **Creá las credenciales** y asignalas en cada nodo (el JSON trae placeholders `REEMPLAZAR_CREDENCIAL_ID`):
   - WhatsApp Trigger (OAuth) y WhatsApp API
   - Airtable (Personal Access Token)
   - Google Calendar (OAuth2)
   - Gmail (OAuth2)
   - OpenAI
3. **Reemplazá los placeholders** del JSON o reseleccioná los recursos en cada nodo:
   - `TU_AIRTABLE_BASE_ID` y `TU_AIRTABLE_TABLE_ID`: base y tablas (`Turnos`, `Errores`)
   - `TU_CALENDAR_ID`: calendario de turnos
   - `TU_PHONE_NUMBER_ID`: ID del número de WhatsApp
   - `clinica@ejemplo.com`: correo donde la clínica recibe las aprobaciones (nodo *Datos del turno nuevo*)
4. **Configurá la zona horaria** del workflow en `America/Argentina/Cordoba` (o la que corresponda). El prompt del agente y el recordatorio la usan.
5. **Ajustá el horario de atención** en el *system prompt* del nodo *AI Agent*: días, franjas, duración del turno (hoy 30 minutos) y datos de la clínica.
6. **Configurá el webhook de WhatsApp** en Meta apuntando a la URL del *WhatsApp Trigger* y suscribite al evento `messages`.
7. **Activá** el workflow.

## 🔄 Cómo funciona un turno

1. El cliente escribe por WhatsApp. El agente pide nombre, apellido, mascota, motivo y día/hora deseados.
2. Consulta Google Calendar, propone un horario libre y, al aceptarlo, crea el evento `PENDIENTE - Nombre Apellido - Mascota` y el registro en Airtable.
3. La clínica recibe un mail con el link al turno y lo aprueba cambiando **Estado** a `CONFIRMADO`.
4. Ese cambio actualiza el título del evento en Calendar y envía la plantilla de confirmación al cliente.
5. El día anterior se envía el recordatorio con botones. Si el cliente toca *Cancelar turno*, el turno pasa a `CANCELADO`, se libera el horario en Calendar y se avisa por WhatsApp.

## ⚠️ Limitaciones y notas

- Los mensajes que no son texto ni botón (audios, imágenes) se ignoran.
- La memoria del agente guarda las últimas 10 interacciones por cliente (clave: número de WhatsApp).
- Si el envío de un aviso falla, el *Último aviso* no se actualiza: se puede reintentar cambiando de nuevo el estado del turno.
- El agente reintenta ante fallos transitorios; si igual falla, registra el error y le pide disculpas al cliente.
- Este repo no incluye credenciales. Nunca subas el JSON exportado sin sanitizarlo: usá `sanitizar_workflow.py`.

## 🧹 Sanitizar el workflow antes de subirlo

```bash
python sanitizar_workflow.py mi-workflow.original.json vet-turnos-whatsapp-n8n.json
```

El script reemplaza IDs de credenciales, de Airtable, del calendario y del número de WhatsApp, además de correos, `instanceId` y `webhookId`.

## 🗺️ Próximas mejoras

- [ ] **Recordatorio personalizado por turno:** hoy el recordatorio se envía una vez al día, a la misma hora para todos los clientes. La idea es avisar **6 horas antes del horario de cada turno**. Esto implica ejecutar el flujo con más frecuencia (por ejemplo cada 15 o 30 minutos) y filtrar los turnos confirmados cuyo inicio caiga dentro de esa ventana y que no tengan el recordatorio enviado.
- [ ] **Recordatorio al reprogramar:** si el recordatorio ya se envió y después el turno se reagenda, no se vuelve a enviar para el nuevo horario, porque el turno sigue marcado como "Recordatorio enviado". La idea es destildar esa marca al reprogramar para que el nuevo horario reciba su recordatorio.

## 📄 Licencia

Elegí una licencia (por ejemplo MIT) y agregá el archivo `LICENSE`.
