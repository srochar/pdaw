# -*- coding: utf-8 -*-

"""
Created on 08/06/2013

@author: srocha
@author: pperez
"""

import requests
from bs4 import BeautifulSoup
import re

class LoginException(Exception):
    def __init__(self, msg):
        self.value = msg

    def __str__(self):
        return repr(self.value)


class Dirdoc(object):
    # Comprueba si tenemos una cookie valida, si no hay cookie retorna false inmediatamente
    # La validez de la cookie se comprueba accediendo a una seccion que requiere autenticacion
    # Cada request se hace con spoof del user agent del navegador
    def __isloggedIn(self):
        if self.__cookie:
            req = requests.get(self.__urls['checker'], cookies = self.__cookie, headers = self.__headers)
        else:
            return False
        return 'PROBLEMAS ARANCELARIOS' in req.text

    # Este metodo hace un login, enviando los datos de usuario al script que autentica en dirdoc
    def __login(self):
        url = self.__urls['login'] # Obtenemos la url que autentica en dirdoc
        
        # Enviamos los datos del login de dirdoc: rut, password y tipo (0 para estudiante)
        req = requests.post(url, data = self.__logindata, headers = self.__headers)
        if 'Bienvenido' not in req.text:
            raise LoginException('Error al hacer login') # Si no nos da la bienvenida algo malo paso ...
        else:
            self.__cookie = req.cookies # Si entramos, almacenamos la cookie, con ella trabajaremos en la sesion

    def __init__(self, rut, password, ua = None, cookie = None):
        self.__urls = dict(
            login = 'http://postulacion.utem.cl/valida.php', # Valida rut/password/tipo contra dirdoc
            ramos = 'http://postulacion.utem.cl/alumnos/notas.php', # Muestra los ramos tomados por el estudiante
            checker = 'http://postulacion.utem.cl/alumnos/contacto.php', # URL para validar si estamos loggeados, parece livianita ...
            notas = 'http://postulacion.utem.cl/alumnos/acta.php' # URL donde se ven las notas, recibe el link del ramo como parametro
        )
        self.__encoding = 'utf-8'
        self.__logindata = dict(
            rut = rut, # Rut del estudiante
            password = password, # Su password
            tipo = 0 # El tipo de usuario es 0 para el estudiante
        )
        
        if ua is None: # Si no recibimos un user-agent usaremos este por defecto
            self.__headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:21.0) Gecko/20100101 Firefox/21.0'}
        else: # Si lo recibimos lo establecemos
            self.__headers = {'User-agent': ua}
        
        if cookie is None: # Si no recibimos un cookie debemos hacer el login
            self.__login()
        else: # Si la recibimos, la establecemos y comprobamos si es valida, si no lo es hacemos login
            self.__cookie = cookie
            loggeado = self.__isloggedIn()
            if not loggeado:
                self.__login()
    
    # Obtiene informacion del usuario, actualmente es solo su rut y nombre en sistema ...
    def __getInfo(self):
        loggeado = self.__isloggedIn()
        if not loggeado:
            self.__login()
        url = self.__urls['ramos'] # Raramente la url de ramos tambien dice la informacion del estudiante ...
        
        req = requests.get(url, cookies = self.__cookie, headers = self.__headers)
        html = BeautifulSoup(req.text)
        rut = html.table.find_all('td')[2].text
        nombre = html.table.find_all('td')[3].text
        return (rut, nombre)

    # Genera el diccionario de ramos
    # Las llaves son los codigos de la malla (i.e: INF-648)
    # Tambien tiene otros campos como el nombre del ramo,
    # profesor asignado, seccion y notas (diccionario de notas)
    def __getRamos(self):
        loggeado = self.__isloggedIn()
        if not loggeado:
            self.__login()
        url = self.__urls['ramos']
        
        req = requests.get(url, cookies=self.__cookie, headers = self.__headers)
        html = BeautifulSoup(req.text)
        ramos = {}
        
        reg_exp_link = r'(?<=p2=)\d+'
        
        for row in html.find_all('tr')[3:]: # Desde el 4to tr son ramos
            data = row.find_all('td') # Data de la tabla, para ese row
            codigo = data[0].text.replace('\r\n', ' ') # Codigo del ramo, key del diccionario generado
            link_id = re.findall(reg_exp_link, data[-1].a.get('onclick'))[0] # Esto es para obtener las notas del ramo
            
            notas = self.__getNotas(link_id)
            # Armamos la informacion del ramo
            ramo = dict(
                nombre = data[1].text, # Nombre del ramo (i.e: Analisis de algoritmos)
                profesor = data[2].text, # Nombre del profesor asignado
                seccion = int(data[3].text), # Seccion asignada
                notas = notas # Notas del ramo, examenes, etc
            )
            
            # Finalmente agregamos el ramo al diccionario
            ramos[codigo] = ramo

        return ramos

    # Retorna un diccionario de notas
    def __getNotas(self, link_id):
        loggeado = self.__isloggedIn()
        encoding = self.__encoding
        if not loggeado:
            self.__login()
        # Formateamos la url (i.e: http://postulacion.utem.cl/alumnos/acta.php?p2=111293)
        url = '{url}?p2={link_id}'.format(url = self.__urls['notas'], link_id = link_id)
        req = requests.get(url, cookies = self.__cookie, headers = self.__headers)
        html = BeautifulSoup(req.text)
        
        notas = {}
        encabezados = html.find_all(class_='pequena')[1].find_all('tr')[0].find_all('td')[:-2] # Medio truco, pero es puro parseo ...
        datos = html.find_all(class_='pequena')[1].find_all('tr')[1].find_all('td')[:-2]
        contador_notas = 1
        contador_examenes = 1
        for (head, data) in zip(encabezados, datos):
            nota = {}
            re_porcentaje = re.findall(r'\d+', head.text) # Vemos si pillamos un numero en el header, quiere decir que es una nota normal
            nota['nota'] = float(data.text) if len(re.findall(r'\d.\d+', data.text)) else None
            if re_porcentaje: # Si logro hacer un match a un porcentaje de notas ...
                porcentaje = int(re_porcentaje[0]) # Obtenemos el porcentaje y le hacemos cast a entero
                if porcentaje > 0: # Dirdoc pone porcentaje 0 para las notas que no van ... oh god why
                    nota['porcentaje'] = porcentaje
                    if 'Acum' in head.text: # Si es la acumulativa lo hacemos notar
                        notas['Nota Acumulativa'] = nota
                    else:
                        notas['Nota {numero}'.format(numero = contador_notas)] = nota
                        contador_notas += 1
            elif 'Examen' in head.text.encode(encoding): # Si no es una nota, vemos si es examen
                if nota['nota'] is not None:
                    notas['Examen {numero}'.format(numero = contador_examenes)] = nota
                    contador_examenes += 1
            elif 'Nota Final' in head.text.encode(encoding): # Y si no es examen vemos si es la nota final
                notas['Nota Final'] = nota
        
        return notas
    
    # Propiedades de la clase
    info = property(fget=__getInfo)
    ramos = property(fget=__getRamos)