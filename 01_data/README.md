# 01_data - Datos

Contiene la fuente RAW utilizada por el proyecto.

- `raw/credit_card_clients_raw.csv`: dataset base de 33,377 registros.
- `samples/`: muestras opcionales para pruebas locales.

La data RAW no debe limpiarse ni modificarse dentro de esta carpeta. La limpieza se realiza en Silver mediante los Stored Procedures de Supabase.

Antes de cargar Bronze, verificar si la tabla ya contiene el lote. El loader actual trabaja por insercion de lote y no debe ejecutarse repetidamente sobre la misma fuente sin un control de lote.
