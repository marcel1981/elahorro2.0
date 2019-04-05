# -*- coding: utf-8 -*-
import requests


class CheckDigit(object):
    # Definicion modulo 11
    _MODULO_11 = {
        'BASE': 11,
        'FACTOR': 2,
        'RETORNO11': 0,
        'RETORNO10': 1,
        'PESO': 2,
        'MAX_WEIGHT': 7
    }

    @classmethod
    def _eval_mod11(self, modulo):
        if modulo == self._MODULO_11['BASE']:
            return self._MODULO_11['RETORNO11']
        elif modulo == self._MODULO_11['BASE'] - 1:
            return self._MODULO_11['RETORNO10']
        else:
            return modulo

    @classmethod
    def compute_mod11(self, dato):
        """
        Calculo mod 11
        return int
        """
        total = 0
        weight = self._MODULO_11['PESO']
        for item in reversed(dato):
            total += int(item) * weight
            weight += 1
            if weight > self._MODULO_11['MAX_WEIGHT']:
                weight = self._MODULO_11['PESO']
        mod = 11 - total % self._MODULO_11['BASE']

        mod = self._eval_mod11(mod)
        return mod


class Xades(object):

    def sign(self, xml_document, file_pk12, password):
        """Metodo que aplica la firma digital al XML"""
        url_api = "http://wsisign.ominec.com:5000/sign"
        data = dict(signature_file=file_pk12,
                    password=password,
                    xml=str(xml_document.encode("utf-8")).replace('\\n', '').replace('\\', '').replace('b\'',
                                                                                                       '').replace('\'',
                                                                                                                   ''))

        result = requests.post(url_api, data=data)
        return result.json()
