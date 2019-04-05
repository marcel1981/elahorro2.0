# -*- coding: utf-8 -*-

import requests

# table 3: tipos de comprobantes
type_voucher = {
    '01': '01',  # factura
    '04': '04',  # Nota de credito
    '05': '05',  # Nota de debito
    '06': '06',  # Guia de remision
    '07': '07',  # COmprobante retencion
}

# table 4: ambiente

# table 6: identificaciòn
type_identifier = {
    'ruc': '04',
    'cedula': '05',
    'pasaporte': '06',
    'venta_consumidor_final': '07',
    'identificacion_exterior': '08',
    'placa': '09',
}

tabla16 = {
    'IVA 0': '2',
    'IVA 12': '2',
    'IVA 14': '2',
    'ice': '3',
    'irbpnr': '5'
}

tabla17 = {
    'IVA 0': '0',
    'IVA 12': '2',
    'IVA 14': '3',
    'No Objeto de Impuesto': '6',
    'Exento de IVA': '7'
}

# tipos de comprobantes que pueden generar los contr. de manera electronica
# FACTURA, NOTA DE CREDITO , NOTA DE DEBITO, GUIA DE REMISION, COMRROBANTE DE RETENCION
tipoDocumento = {
    '01': '01',
    '04': '04',
    '05': '05',
    '06': '06',
    '07': '07',
    '18': '07',
}
