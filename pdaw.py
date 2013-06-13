# 2013.06.09 23:01:29 CLT
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
    def reconnect(self):
        self.__login()


    def __isloggedIn(self):
        if self.__cookie:
            r = requests.get(self.__urls['checker'], cookies=self.__cookie)
        else:
            return False
        return 'PROBLEMAS ARANCELARIOS' in r.text


    def __login(self):
        """
        Este metodo deberia darnos un cookie valido para trabajar.
        O levantar excepciones en caso de que falle la conexion
        """
        headers = self.__headers
        encoding = self.__encoding
        loggeado = self.__isloggedIn()
        if not loggeado:
            url = self.__urls['login']
            logindata = self.__logindata
            r = requests.post(url, data=logindata, headers=headers)
            if 'Bienvenido' not in r.text.encode(encoding):
                raise LoginException('Error al hacer login')
            else:
                self.__cookie = r.cookies


    def __init__(self, rut, password, ua = None, cookie = None):
        self.__urls = {}
        self.__urls['login'] = 'http://postulacion.utem.cl/valida.php'
        self.__urls['ramos'] = 'http://postulacion.utem.cl/alumnos/notas.php'
        self.__urls['notas'] = 'http://postulacion.utem.cl/alumnos/acta.php'
        self.__urls['checker'] = 'http://postulacion.utem.cl/alumnos/contacto.php'
        self.__encoding = 'utf-8'
        self.__logindata = {'rut': rut,
         'password': password,
         'tipo': 0}
        self.__headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:21.0) Gecko/20100101 Firefox/21.0'}
        if ua is None:
            self.__user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:21.0) Gecko/20100101 Firefox/21.0'
        else:
            self.__user_agent = ua
        self.__cookie = None
        if cookie is None:
            self.__login()
        else:
            self.__cookie = cookie
            loggeado = self.__isloggedIn()
            if not loggeado:
                self.__login()


    def __getInfo(self):
        loggeado = self.__isloggedIn()
        encoding = self.__encoding
        if not loggeado:
            self.__login()
        url = self.__urls['ramos']
        r = requests.get(url, cookies=self.__cookie)
        pagina = BeautifulSoup(r.text.encode(encoding))
        rut = pagina.table.find_all('td')[2].getText().encode(encoding)
        nombre = pagina.table.find_all('td')[3].getText().encode(encoding)
        return (rut, nombre)


    def __getRamos(self):
        loggeado = self.__isloggedIn()
        encoding = self.__encoding
        if not loggeado:
            self.__login()
        url = self.__urls['ramos']
        ramos = {}
        r = requests.get(url, cookies=self.__cookie)
        pagina = BeautifulSoup(r.text.encode(self.__encoding))
        for row in pagina.findAll('tr')[3:]:
            ramo = {}
            data = row.findAll('td')
            codigo = data[0].getText().encode(encoding).replace('\r\n', ' ')
            ramo['Codigo'] = codigo
            ramo['Nombre'] = data[1].getText().encode(encoding)
            ramo['Profesor'] = data[2].getText().encode(encoding)
            ramo['Seccion'] = int(data[3].getText())
            exp = '(?<=p2=)\\d+'
            ramo['link_id'] = int(re.findall(exp, data[-1].a.get('onclick'))[0])
            ramo['Notas'] = self.__getNotas(ramo['link_id'])
            ramos[codigo] = ramo

        return ramos


    def __getNotas(self, link_id):
        loggeado = self.__isloggedIn()
        encoding = self.__encoding
        if not loggeado:
            self.__login()
        url = '{0}?p2={1}'.format(self.__urls['notas'], link_id)
        notas = {}
        r = requests.get(url, cookies=self.__cookie)
        pagina = BeautifulSoup(r.text.encode(self.__encoding))
        encabezados = pagina.findAll(class_='pequena')[1].findAll('tr')[0].findAll('td')
        datos = pagina.findAll(class_='pequena')[1].findAll('tr')[1].findAll('td')
        contador_notas = 1
        contador_examenes = 1
        for (head, data,) in zip(encabezados[:-2], datos[:-2]):
            nota = {}
            re_porcentaje = re.findall('\\d+', head.br.getText()) if head.br is not None else []
            nota['nota'] = float(data.getText()) if len(re.findall('\\d.\\d+', data.getText())) else None
            if len(re_porcentaje):
                porcentaje = int(re_porcentaje[0])
                if porcentaje > 0:
                    nota['porcentaje'] = porcentaje
                    if 'Acum' in head.getText():
                        notas['Nota Acumulativa'] = nota
                    else:
                        notas['Nota {}'.format(contador_notas)] = nota
                        contador_notas += 1
            elif 'Examen' in head.getText().encode(encoding):
                if nota['nota'] is not None:
                    notas['Examen {}'.format(contador_examenes)] = nota
                    contador_examenes += 1
            elif 'Nota Final' in head.getText().encode(encoding):
                notas['Nota Final'] = nota
        
        return notas


    info = property(fget=__getInfo)
    ramos = property(fget=__getRamos)


# +++ okay decompyling pdaw.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.06.09 23:01:29 CLT
