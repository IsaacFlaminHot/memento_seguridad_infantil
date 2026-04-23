from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Cambiarestaonda'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tucorreo@gmail.com' # Pon aquí tu correo
app.config['MAIL_PASSWORD'] = '' # La contraseña de 16 letras (ir al apartado de seguridad de tu cuenta de google, luego a contraseñas de aplicaciones, y generar una contraseña para esta aplicación.)
app.config['MAIL_DEFAULT_SENDER'] = 'tucorreo@gmail.com'

mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), unique=False, nullable=True)
    password_hash = db.Column(db.String(250), nullable=False)
    its_verified = db.Column(db.Boolean, default=False)
    
class PerfilVehiculo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre_perfil = db.Column(db.String(150), nullable=False)
    
    ventanas_bloqueadas = db.Column(db.Boolean, default=False)
    puertas_bloqueadas = db.Column(db.Boolean, default=False)
    cinturon_obligatorio = db.Column(db.Boolean, default=False)
    velocidad_maxima = db.Column(db.Integer, default=120)
    
    user = db.relationship('User', backref=db.backref('perfiles_vehiculo', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- Patrón Memento ---
class Memento:
    def __init__(self, ventanas_bloqueadas, puertas_bloqueadas, cinturon_obligatorio, velocidad_maxima, perfil_activo=None):
        self.ventanas_bloqueadas = ventanas_bloqueadas
        self.puertas_bloqueadas = puertas_bloqueadas
        self.cinturon_obligatorio = cinturon_obligatorio
        self.velocidad_maxima = velocidad_maxima
        self.perfil_activo = perfil_activo

    def obtener_estado(self):
        return {
            "ventanas_bloqueadas": self.ventanas_bloqueadas,
            "puertas_bloqueadas": self.puertas_bloqueadas,
            "cinturon_obligatorio": self.cinturon_obligatorio,
            "velocidad_maxima": self.velocidad_maxima,
            "perfil_activo": self.perfil_activo
        }

# --- Originador ---
class ConfiguracionVehiculo:
    def __init__(self):
        self.ventanas_bloqueadas = False
        self.puertas_bloqueadas = False
        self.cinturon_obligatorio = False
        self.velocidad_maxima = 120

    def configurar(self, ventanas, puertas, cinturon, velocidad):
        self.ventanas_bloqueadas = ventanas
        self.puertas_bloqueadas = puertas
        self.cinturon_obligatorio = cinturon
        self.velocidad_maxima = velocidad
        print(f"Configuración actualizada en el sistema.")

    def guardar_configuraciones_de_seguridad(self, perfil_activo=None):
        """Crea un Memento con el estado actual."""
        return Memento(
            self.ventanas_bloqueadas,
            self.puertas_bloqueadas,
            self.cinturon_obligatorio,
            self.velocidad_maxima,
            perfil_activo
        )

    def restaurar_desde_memento(self, memento):
        """Restaura el estado a partir de un Memento."""
        estado = memento.obtener_estado()
        self.ventanas_bloqueadas = estado["ventanas_bloqueadas"]
        self.puertas_bloqueadas = estado["puertas_bloqueadas"]
        self.cinturon_obligatorio = estado["cinturon_obligatorio"]
        self.velocidad_maxima = estado["velocidad_maxima"]
        print(f"Configuración restaurada con éxito.")

    def mostrar_estado_actual(self):
        print(f"[ESTADO] Ventanas Bloqueadas: {self.ventanas_bloqueadas} | "
              f"Puertas: {self.puertas_bloqueadas} | "
              f"Cinturón: {self.cinturon_obligatorio} | "
              f"Velocidad Máxima: {self.velocidad_maxima} km/h")

# --- Caretaker ---
class HistorialSeguridad:
    """Gestiona el historial y los perfiles rápidos."""
    def __init__(self):
        self.historial = []
        self.perfiles_rapidos = {}

    def agregar_al_historial(self, memento):
        self.historial.append(memento)
        print("Estado guardado en el historial cronológico.")

    def deshacer_ultimo_cambio(self):
        if not self.historial:
            print("No hay historial para deshacer.")
            return None
        return self.historial.pop()
    
    def guardar_perfil_rapido(self, nombre_perfil, memento):
        self.perfiles_rapidos[nombre_perfil] = memento
        print(f"Perfil '{nombre_perfil}' guardado.")

    def obtener_perfil_rapido(self, nombre_perfil):
        if nombre_perfil in self.perfiles_rapidos:
            return self.perfiles_rapidos[nombre_perfil]
        print(f"Perfil '{nombre_perfil}' no encontrado.")
        return None
    
sistemas_activos = {}

def obtener_sistema_usuario(user_id):
    if user_id not in sistemas_activos:
        sistemas_activos[user_id] = {
            'auto' : ConfiguracionVehiculo(),
            'gestor' : HistorialSeguridad(),
            'perfil_activo': None
        }
    return sistemas_activos[user_id]
    
# ==========================================
# RUTAS DE FLASK
# ==========================================

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    sistema =  obtener_sistema_usuario(current_user.id)
    auto = sistema['auto']
    gestor = sistema['gestor']
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'aplicar_cambios':
            
            gestor.agregar_al_historial(auto.guardar_configuraciones_de_seguridad(sistema['perfil_activo']))
            
            ventanas = request.form.get('ventanas') == 'on'
            puertas = request.form.get('puertas') == 'on'
            cinturon = request.form.get('cinturon') == 'on'
            velocidad = int(request.form.get('velocidad'))
            
            auto.configurar(ventanas, puertas, cinturon, velocidad)
            sistema['perfil_activo'] = None
            flash('Cambios aplicados con éxito.', 'success')
            
        elif accion == 'guardar_perfil':
            nombre = request.form.get('nombre_perfil')
            if nombre:
                memento_actual = auto.guardar_configuraciones_de_seguridad(sistema['perfil_activo'])
                estado = memento_actual.obtener_estado()
                
                perfil_existente = PerfilVehiculo.query.filter_by(user_id=current_user.id, nombre_perfil=nombre).first()
                
                if perfil_existente:
                    perfil_existente.ventanas_bloqueadas = estado['ventanas_bloqueadas']
                    perfil_existente.puertas_bloqueadas = estado['puertas_bloqueadas']
                    perfil_existente.cinturon_obligatorio = estado['cinturon_obligatorio']
                    perfil_existente.velocidad_maxima = estado['velocidad_maxima']
                    
                else:
                    # Crear nuevo perfil
                    nuevo_perfil = PerfilVehiculo(
                        user_id=current_user.id,
                        nombre_perfil=nombre,
                        ventanas_bloqueadas=estado['ventanas_bloqueadas'],
                        puertas_bloqueadas=estado['puertas_bloqueadas'],
                        cinturon_obligatorio=estado['cinturon_obligatorio'],
                        velocidad_maxima=estado['velocidad_maxima']
                    )
                    db.session.add(nuevo_perfil)
                    
                db.session.commit()
                flash(f'Perfil "{nombre}" guardado.', 'success')
        
        elif accion == 'cargar_perfil':
            nombre = request.form.get('perfil_seleccionado')
            
            perfil_db = PerfilVehiculo.query.filter_by(user_id=current_user.id, nombre_perfil=nombre).first()
            if perfil_db:
                gestor.agregar_al_historial(auto.guardar_configuraciones_de_seguridad(sistema['perfil_activo']))
                
                memento_recuperado = Memento(
                    ventanas_bloqueadas=perfil_db.ventanas_bloqueadas,
                    puertas_bloqueadas=perfil_db.puertas_bloqueadas,
                    cinturon_obligatorio=perfil_db.cinturon_obligatorio,
                    velocidad_maxima=perfil_db.velocidad_maxima
                )
                
                auto.restaurar_desde_memento(memento_recuperado)
                sistema['perfil_activo'] = nombre
                flash(f'Perfil "{nombre}" cargado.', 'success')

        elif accion == 'deshacer':
            memento_anterior = gestor.deshacer_ultimo_cambio()
            if memento_anterior:
                auto.restaurar_desde_memento(memento_anterior)
                sistema['perfil_activo'] = memento_anterior.obtener_estado().get('perfil_activo')
                flash('Último cambio deshecho.', 'success')
            else:
                flash('No hay cambios para deshacer.', 'error')
        
        return redirect(url_for('index'))
    
    estado_actual = auto.guardar_configuraciones_de_seguridad().obtener_estado()
    perfiles = list(gestor.perfiles_rapidos.keys())
    
    cambios_en_historial = len(gestor.historial)
    
    perfiles_usuario = PerfilVehiculo.query.filter_by(user_id=current_user.id).all()
    nombres_perfiles = [p.nombre_perfil for p in perfiles_usuario]
    return render_template('index.html', estado=estado_actual, perfiles=nombres_perfiles, cambios=cambios_en_historial, perfil_activo=sistema['perfil_activo'])

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    # <-- Aquí estaba el error de indentación principal
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Verificar si el usuario existe y la contraseña es correcta
        if user and check_password_hash(user.password_hash, password):
            # Correo electrónico no verificado
            if not user.its_verified:
                flash('Tu cuenta no ha sido verificada. Por favor, verifica tu correo electrónico antes de iniciar sesión.')
                return redirect(url_for('login'))

            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos. Inténtalo de nuevo.')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('El nombre de usuario o correo electrónico ya está en uso. Por favor, elige otro.')
            return redirect(url_for('register'))

        # Crear un nuevo usuario
        new_user = User(
            username=username,
            email=email,
            name=name,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
            its_verified=False  
        )
        db.session.add(new_user)
        db.session.commit()
        
        token = s.dumps(email, salt='email-confirm')
        
        link = url_for('verify_email', token=token, _external=True)
        
        msg = Message('Confirma tu correo electrónico', recipients=[email])
        msg.body = f'Hola {name},\n\n Por favor, haz click en el siguiente enlace para verificar tu cuenta:\n{link}\n\nEste enlace expirará en 1 hora.'
        
        try:
            mail.send(msg)
            flash('Registro exitoso. Por favor, verifica tu correo electrónico para activar tu cuenta.')
        except Exception as e:
            flash(f'Error enviando el correo de verificación: {e}')
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)  #1 hora
    except SignatureExpired:
        flash('El enlace de verificación ha expirado. Por favor, regístrate nuevamente.')
        return redirect(url_for('login'))
    except BadTimeSignature:
        flash('El enlace de verificación no es válido. Por favor, regístrate nuevamente.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first_or_404()
    
    if user.its_verified:
        flash('La cuenta ya ha sido verificada. Por favor, inicia sesión.')
        return redirect(url_for('login'))
    else:
        user.its_verified = True
        db.session.add(user)
        db.session.commit()
        flash('Correo electrónico verificado con éxito. Ahora puedes iniciar sesión.')
        return redirect(url_for('login'))
        
    flash('Usuario no encontrado. Por favor, regístrate nuevamente.')
    return redirect(url_for('register'))

if __name__ == "__main__":
    app.run(debug=True)