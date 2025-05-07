# Bot de Trading para DEX en Solana

Bot profesional de trading para detección y operación automática de tokens en DEX de Solana.

## Características

- Detección automática de nuevos tokens mediante Dexscreener API
- Estrategia de inversión basada en criterios configurables (perfil, booster, volumen, liquidez)
- Venta automática de tokens cuando alcanzan x3
- Arquitectura de microservicios escalable con Docker y GCP Cloud Run
- Sistema óptimo de gestión de RPC para máxima disponibilidad y rendimiento

## Arquitectura

El proyecto está organizado en microservicios independientes:

1. **RPC Service**: Selección óptima de endpoints RPC para Solana
2. **Token Scanner**: Detección de nuevos tokens mediante API de Dexscreener
3. **Trading Engine**: Análisis y ejecución de operaciones de compra/venta
4. **API Gateway**: Interfaz unificada para todos los servicios

## Instalación y Uso

Ver documentación en `/docs`
