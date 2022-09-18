from ast import Str
from flask import request
import datetime;
from flask_jwt_extended import jwt_required, create_access_token
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from modelos import db, Apuesta, ApuestaSchema, Usuario, UsuarioSchema, Carrera, CarreraSchema, CompetidorSchema, \
    Competidor, ReporteSchema, Transaccion, TransaccionSchema, Notificacion,NotificacionSchema

apuesta_schema = ApuestaSchema()
carrera_schema = CarreraSchema()
competidor_schema = CompetidorSchema()
usuario_schema = UsuarioSchema()
reporte_schema = ReporteSchema()
transaccion_schema = TransaccionSchema()
notificacion_schema = NotificacionSchema()


class VistaSignIn(Resource):

    def post(self):
        
        usuario = Usuario.query.filter(Usuario.usuario == request.json["usuario"]).first()
        db.session.commit()
        if usuario is None:
            nuevo_usuario = Usuario(usuario=request.json["usuario"], contrasena=request.json["contrasena"],nombre=request.json["nombre"], tarjeta=request.json["tarjeta"], correo=request.json["correo"])
            db.session.add(nuevo_usuario)
            db.session.commit()
            token_de_acceso = create_access_token(identity=nuevo_usuario.id)
            return {"mensaje": "usuario creado exitosamente", "token": token_de_acceso, "id": nuevo_usuario.id}
        else:
            return {"mensaje":"El usuario ingresado ya existe"}, 409

    def put(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.contrasena = request.json.get("contrasena", usuario.contrasena)
        db.session.commit()
        return usuario_schema.dump(usuario)

    def delete(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        db.session.delete(usuario)
        db.session.commit()
        return '', 204

class VistaUsuarioSaldo(Resource):

    def put(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.saldo = request.json.get("saldo", usuario.saldo)
        db.session.commit()
        return usuario_schema.dump(usuario)

class VistaUsuario(Resource):


    def get(self, id_usuario):
        return usuario_schema.dump(Usuario.query.get_or_404(id_usuario))

    def put(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.nombre = request.json.get("nombre", usuario.nombre)
        usuario.correo = request.json.get("correo", usuario.correo)
        usuario.tarjeta = request.json.get("tarjeta", usuario.tarjeta)
        db.session.commit()
        return usuario_schema.dump(usuario)

class VistaApostadores(Resource):
    @jwt_required()
    def get(self):
        return [usuario_schema.dump(apostadores) for apostadores in Usuario.query.where(Usuario.nombre!="admin")]
    

class VistaLogIn(Resource):

    def post(self):
        usuario = Usuario.query.filter(Usuario.usuario == request.json["usuario"],
                                       Usuario.contrasena == request.json["contrasena"]).first()
        db.session.commit()
        if usuario is None:
            return "El usuario no existe", 404
        else:
            token_de_acceso = create_access_token(identity=usuario.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": token_de_acceso}


class VistaCarrerasUsuario(Resource):

    @jwt_required()
    def post(self, id_usuario):
        nueva_carrera = Carrera(nombre_carrera=request.json["nombre"])
        for item in request.json["competidores"]:
            cuota = round(
                (item["probabilidad"] / (1 - item["probabilidad"])), 2)
            competidor = Competidor(nombre_competidor=item["competidor"],
                                    probabilidad=item["probabilidad"],
                                    cuota=cuota,
                                    id_carrera=nueva_carrera.id)
            nueva_carrera.competidores.append(competidor)
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.carreras.append(nueva_carrera)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 'El usuario ya tiene un carrera con dicho nombre', 409

        return carrera_schema.dump(nueva_carrera)

    @jwt_required()
    def get(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        carreras = usuario.carreras
        for carrera in carreras:
            for apuesta in carrera.apuestas:
                apuesta.nombre_apostador = apuesta.usuario.nombre
        return [carrera_schema.dump(carrera) for carrera in carreras]

class VistaCarreras(Resource):
    @jwt_required()
    def get(self):
        return [carrera_schema.dump(carrera) for carrera in Carrera.query.all()]

class VistaCarrera(Resource):

    @jwt_required()
    def get(self, id_carrera):
        return carrera_schema.dump(Carrera.query.get_or_404(id_carrera))

    @jwt_required()
    def put(self, id_carrera):
        carrera = Carrera.query.get_or_404(id_carrera)
        carrera.nombre_carrera = request.json.get(
            "nombre", carrera.nombre_carrera)
        carrera.competidores = []

        for item in request.json["competidores"]:
            probabilidad = float(item["probabilidad"])
            cuota = round((probabilidad / (1 - probabilidad)), 2)
            competidor = Competidor(nombre_competidor=item["competidor"],
                                    probabilidad=probabilidad,
                                    cuota=cuota,
                                    id_carrera=carrera.id)
            carrera.competidores.append(competidor)

        db.session.commit()
        return carrera_schema.dump(carrera)

    @jwt_required()
    def delete(self, id_carrera):
        carrera = Carrera.query.get_or_404(id_carrera)
        db.session.delete(carrera)
        db.session.commit()
        return '', 204


class VistaApuestas(Resource):

    @jwt_required()
    def post(self):
        carrera = Carrera.query.get_or_404(request.json["id_carrera"])
        competidor = Competidor.query.get_or_404(request.json["id_competidor"])
        nueva_apuesta = Apuesta(valor_apostado=request.json["valor_apostado"],
                                id_usuario=request.json["id_usuario"],
                                id_competidor=request.json["id_competidor"], 
                                id_carrera=request.json["id_carrera"],
                                nombre_apostador=request.json["nombre_apostador"],
                                nombre_carrera=carrera.nombre_carrera,
                                nombre_competidor=competidor.nombre_competidor)
        
        transaccion = Transaccion(detalle="Apuesta a evento "+carrera.nombre_carrera,
                                  valor=nueva_apuesta.valor_apostado,
                                  id_usuario=nueva_apuesta.id_usuario)
        db.session.add(nueva_apuesta)
        db.session.add(transaccion)
        db.session.commit()
        return apuesta_schema.dump(nueva_apuesta)

    @jwt_required()
    def get(self):
        apuestas = Apuesta.query.all()
        for apuesta in apuestas:
            apuesta.nombre_apostador = apuesta.usuario.nombre
            apuesta.nombre_carrera = apuesta.carrera.nombre_carrera
            apuesta.nombre_competidor = apuesta.competidor.nombre_competidor
        return [apuesta_schema.dump(ca) for ca in apuestas]


class VistaApuesta(Resource):

    @jwt_required()
    def get(self, id_apuesta):
        return apuesta_schema.dump(Apuesta.query.get_or_404(id_apuesta))

    @jwt_required()
    def put(self, id_apuesta):
        apuesta = Apuesta.query.get_or_404(id_apuesta)
        apuesta.valor_apostado = request.json.get(
            "valor_apostado", apuesta.valor_apostado)
        apuesta.id_competidor = request.json.get(
            "id_competidor", apuesta.id_competidor)
        apuesta.id_carrera = request.json.get("id_carrera", apuesta.id_carrera)
        db.session.commit()
        return apuesta_schema.dump(apuesta)

    @jwt_required()
    def delete(self, id_apuesta):
        apuesta = Apuesta.query.get_or_404(id_apuesta)
        db.session.delete(apuesta)
        db.session.commit()
        return '', 204

class VistaNotificacion(Resource):

    def post(self):
        notificaciones=Notificacion.query.filter(Notificacion.id_usuario==request.json["id_usuario"]).order_by(Notificacion.fecha.desc()).paginate(page=1 if ("page" in request.json)==False else request.json["page"], per_page=5 if ("per_page" in request.json)==False else request.json["per_page"])
        return {"items":[notificacion_schema.dump(ca) for ca in notificaciones.items],"page":notificaciones.page,"pages":notificaciones.pages,"total":notificaciones.total,"per_page":notificaciones.per_page}

   
    def put(self):
        filters=[]
        for noti in request.json:
            sqlalchemybinaryexpression = Notificacion.id == noti
            filters.append(sqlalchemybinaryexpression)
                 
        for noti in Notificacion.query.filter(or_(*filters)):
            noti.leido = True
        
        db.session.commit()
        return {"mensaje": "Notificaciones marcadas como leidas exitosamente"}
   


class VistaTerminacionCarrera(Resource):

    def put(self, id_competidor):
        competidor = Competidor.query.get_or_404(id_competidor)
        competidor.es_ganador = True
        carrera = Carrera.query.get_or_404(competidor.id_carrera)
        carrera.abierta = False

        for apuesta in carrera.apuestas:
            usuario = Usuario.query.get_or_404(apuesta.id_usuario)
            if apuesta.id_competidor == competidor.id:
                apuesta.ganancia = apuesta.valor_apostado + \
                    (apuesta.valor_apostado/competidor.cuota)
                usuario.saldo = request.json.get("saldo", usuario.saldo + apuesta.ganancia)
                nueva_notifiacion = Notificacion(
                                mensaje="<b>Felicitaciones!</b> </br> Has ganado  $"
                                +"%0.2f" % apuesta.ganancia +" por tu apuesta en "+carrera.nombre_carrera+" </br> @url",
                                id_usuario=apuesta.id_usuario,
                                leido=False)
                db.session.add(nueva_notifiacion)          
            else:
                apuesta.ganancia = 0

        db.session.commit()
        return competidor_schema.dump(competidor)


class VistaReporte(Resource):

    @jwt_required()
    def get(self, id_carrera):
        carreraReporte = Carrera.query.get_or_404(id_carrera)
        ganancia_casa_final = 0

        for apuesta in carreraReporte.apuestas:
            ganancia_casa_final = ganancia_casa_final + \
                apuesta.valor_apostado - apuesta.ganancia

        reporte = dict(carrera=carreraReporte,
                       ganancia_casa=ganancia_casa_final)
        schema = ReporteSchema()
        return schema.dump(reporte)


class VistaTransaccionesUsuario(Resource):
    @jwt_required()
    def post(self, id_usuario):
        nueva_transaccion = Transaccion(fecha = datetime.datetime.now(),
                                        detalle = request.json["detalle"],
                                        valor = request.json["valor"],
                                        id_usuario = id_usuario)
        db.session.add(nueva_transaccion)
        db.session.commit()
        return transaccion_schema.dump(nueva_transaccion)

    @jwt_required()
    def get(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        return [transaccion_schema.dump(transaccion) for transaccion in usuario.transacciones]
        