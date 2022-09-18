import json
from unittest import TestCase

from faker import Faker
from faker.generator import random

from app import app


class TestUsuario(TestCase):

    def test_obtener_usuario_por_id(self):
        self.data_factory = Faker()
        self.client = app.test_client()
        nuevo_usuario = {
            "usuario": self.data_factory.word(),
            "contrasena": self.data_factory.word(),
            "nombre": "prueba9",
            "tarjeta": self.data_factory.random_number(digits=6),
            "correo": self.data_factory.email()
        }

        solicitud_nuevo_usuario_1 = self.client.post("/signin",
                                                   data=json.dumps(nuevo_usuario),
                                                   headers={'Content-Type': 'application/json'})
        respuesta_al_crear_usuario= json.loads(solicitud_nuevo_usuario_1.get_data())
        idUsuario = respuesta_al_crear_usuario["id"]
   
        endpoint_obtener_usuario = "/usuario/{}".format(str(idUsuario))
        
        solicitud_consultar_usuario_por_id = self.client.get(endpoint_obtener_usuario, headers={'Content-Type': 'application/json'})
        usuario_obtenido = json.loads(solicitud_consultar_usuario_por_id.get_data())

        self.assertEqual(solicitud_consultar_usuario_por_id.status_code, 200)
        self.assertEqual(usuario_obtenido["nombre"], "prueba9")



    def test_editar_usuario_por_id(self):
         self.data_factory = Faker()
         self.client = app.test_client()
         nuevo_usuario = {
            "usuario": self.data_factory.word(),
            "contrasena": self.data_factory.word(),
            "nombre": "prueba1",
            "tarjeta": self.data_factory.random_number(digits=6),
            "correo": self.data_factory.email()
        }

         nuevo_usuario2 = {
            "nombre": "pruebaEditada",
            "tarjeta": self.data_factory.random_number(digits=6),
            "correo": self.data_factory.email()
         }

         solicitud_nuevo_usuario_1 = self.client.post("/signin",
                                                   data=json.dumps(nuevo_usuario),
                                                   headers={'Content-Type': 'application/json'})
         respuesta_al_crear_usuario= json.loads(solicitud_nuevo_usuario_1.get_data())
         idUsuario = respuesta_al_crear_usuario["id"]
         
         endpoint_editar_usuario = "/usuario/{}".format(str(idUsuario))
         
         solicitud_editar_usuario = self.client.put(endpoint_editar_usuario,
                                                   data=json.dumps(nuevo_usuario2),
                                                   headers={'Content-Type': 'application/json'})

         usuario_editado = json.loads(solicitud_editar_usuario.get_data())

         self.assertEqual(solicitud_editar_usuario.status_code, 200)
         self.assertEqual(usuario_editado["nombre"], "pruebaEditada")
