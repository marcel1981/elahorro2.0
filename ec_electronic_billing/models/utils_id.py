# -*- coding: utf-8 -*-
import logging
import pdb
class Identifier:

    @staticmethod
    def validate_ci_ruc(number, type_id):

        """validate ci/ruc of ecuador """
        total = 0
        # check ci/ruc rules
        tipo = Identifier.rules_identifier(number, type_id)
        if not tipo:
            return False

        if tipo == '0':  # c.i y r.u.c persona natural
            base = 10
            digit_v = int(number[9])
            coeficiente = (2, 1, 2, 1, 2, 1, 2, 1, 2)
        elif tipo == '1':  # r.u.c. publicos
            base = 11
            digit_v = int(number[8])
            coeficiente = (3, 2, 7, 6, 5, 4, 3, 2)
        elif tipo == '2':  # r.u.c. juridicos y extranjeros sin cedula
            base = 11
            digit_v = int(number[9])
            coeficiente = (4, 3, 2, 7, 6, 5, 4, 3, 2)
        else:
            return False

        for i in range(0, len(coeficiente)):
            subtotal = int(number[i]) * coeficiente[i]
            if tipo == '0':
                # Multiplica cada dígito de la c.i por el coeficiente, si es mayor a 10 suma entre digitps
                total += subtotal if subtotal < 10 else int(str(subtotal)[0]) + int(str(subtotal)[1])
            else:
                total += subtotal

        mod = total % base
        val = base - mod if mod != 0 else 0
        if val == digit_v:
            return True
        else:
            logging.error("c.i/ruc incorrecto")
            return False


    @staticmethod
    def rules_identifier(number, type_id):
        """Rules of the ci/ruc of ecuador"""
        num_prov = 24
        if not number.isdigit(): # verifica solo numeros
            logging.error("Tiene que ser solo numeros")
            return False
        if len(number) != 10 and type_id == '05':
            return False

        if len(number) != 13 and type_id == '04':
            logging.error("Tiene que ser longitud correcta")
            return False

        if not (int(number[0:2]) > 0 and int(number[0:2]) < num_prov):  # verifica provincia
            logging.error("Codigo de provincia no valido")
            return False

        if int(number[2]) >= 0 and int(number[2]) < 6:  # verifica 3er digito ci/ruc persona natural
            if len(number) == 10:
                tipo = '0'
            elif len(number) == 13:
                # Los 3 últimos dígitos son 001, 002, etc., dependiendo el nro de locales adicionales
                return '0' if number[10:13] != '000' else False
            else:
                logging.error("Longitud incorrecta")
                return False
        elif int(number[2]) == 6 and number[10:13] != '000':  # verifica tercer digito ruc publicos y los 3 ultimos
            tipo = '1'
        # verifica tercer digito ruc juridicos y extranjeros sin cedula
        elif int(number[2]) == 9 and number[10:13] != '000':
            tipo = '2'
        else:
            logging.error("Tercer digito no valido")
            return False

        return tipo
