#!/usr/bin/env bash
# Demostracion completa del flujo contra el API (local o desplegado).
# Uso:  bash scripts/demo.sh                       -> http://localhost:8000
#       BASE=https://tu-app.onrender.com bash scripts/demo.sh
BASE="${BASE:-http://localhost:8000}"
SUF="$(date +%s)"
UNIDAD="Eco-$SUF"; OPER="OP-$SUF"; ORDEN="OS-$SUF"
B64="$(printf 'contenido' | base64)"
j() { python3 -c "import sys,json; print(json.load(sys.stdin)['$1'])"; }
post() { echo; echo ">>> POST $1"; shift; curl -s -X POST "$@"; echo; }

echo "== Salud =="; curl -s "$BASE/health"; echo
post "unidad"   "$BASE/unidades"   -H 'Content-Type: application/json' -d "{\"codigo\":\"$UNIDAD\"}"
post "operador" "$BASE/operadores" -H 'Content-Type: application/json' -d "{\"identificador\":\"$OPER\"}"

echo; echo ">>> US-01 solicitar cotizacion"
FOLIO=$(curl -s -X POST "$BASE/cotizaciones" -H 'Content-Type: application/json' \
  -d '{"origen":"Monterrey","destino":"Querétaro","tipo_mercancia":"autopartes","peso_kg":"1500","valor":"80000","tipo_de_unidad":"caja seca"}' | j folio)
echo "folio: $FOLIO"
post "US-02 cotizar (Ventas)"    "$BASE/cotizaciones/$FOLIO/cotizar" -H 'X-Rol: Ventas'
post "US-03 aceptar (Cliente)"   "$BASE/cotizaciones/$FOLIO/aceptar"
echo; echo ">>> RN-02: Ventas NO puede generar la orden (espera 403)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/ordenes" -H 'X-Rol: Ventas' -H 'Content-Type: application/json' \
  -d "{\"numero\":\"$ORDEN\",\"folio_cotizacion\":\"$FOLIO\",\"unidad_id\":\"$UNIDAD\",\"operador_id\":\"$OPER\"}"
post "US-04 generar orden (Operaciones)" "$BASE/ordenes" -H 'X-Rol: Operaciones' -H 'Content-Type: application/json' \
  -d "{\"numero\":\"$ORDEN\",\"folio_cotizacion\":\"$FOLIO\",\"unidad_id\":\"$UNIDAD\",\"operador_id\":\"$OPER\"}"
post "US-05 recoleccion" "$BASE/ordenes/$ORDEN/recoleccion" -H 'Content-Type: application/json' \
  -d '{"tipo_inspeccionado":"autopartes","peso_inspeccionado":"1500"}'
post "US-06 traslado"    "$BASE/ordenes/$ORDEN/traslado"
post "US-17 llegada"     "$BASE/ordenes/$ORDEN/llegada"
echo; echo ">>> RN-03: entrega SIN firma (espera 422)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/ordenes/$ORDEN/entrega" -H 'Content-Type: application/json' \
  -d "{\"receptor_nombre\":\"Ana\",\"receptor_identificacion\":\"INE123\",\"foto_base64\":\"$B64\",\"latitud\":25.68,\"longitud\":-100.31}"
post "US-13 entrega con evidencia completa" "$BASE/ordenes/$ORDEN/entrega" -H 'Content-Type: application/json' \
  -d "{\"receptor_nombre\":\"Ana\",\"receptor_identificacion\":\"INE123\",\"foto_base64\":\"$B64\",\"firma_base64\":\"$B64\",\"latitud\":25.68,\"longitud\":-100.31}"
echo; echo ">>> US-14/US-16 consulta de estatus e historial"; curl -s "$BASE/ordenes/$ORDEN"; echo
echo; echo "Listo. Swagger: $BASE/docs"
