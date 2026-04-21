# Memento
class Memento:
    def __init__(self, ventanas_bloqueadas, puertas_bloqueadas, cinturon_obligatorio, velocidad_maxima):
        self.ventanas_bloqueadas = ventanas_bloqueadas
        self.puertas_bloqueadas = puertas_bloqueadas
        self.cinturon_obligatorio = cinturon_obligatorio
        self.velocidad_maxima = velocidad_maxima

    def obtener_estado(self):
        return {
            "ventanas_bloqueadas": self.ventanas_bloqueadas,
            "puertas_bloqueadas": self.puertas_bloqueadas,
            "cinturon_obligatorio": self.cinturon_obligatorio,
            "velocidad_maxima": self.velocidad_maxima
        }

# Originador
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

    def guardar_configuraciones_de_seguridad(self):
        """Crea un Memento con el estado actual."""
        return Memento(
            self.ventanas_bloqueadas,
            self.puertas_bloqueadas,
            self.cinturon_obligatorio,
            self.velocidad_maxima
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

#Caretaker
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

if __name__ == "__main__" :
    # Inicializar el sistema y el gestor.

    auto = ConfiguracionVehiculo()
    gestor = HistorialSeguridad()

    print("--- 1. Guardando modo normal (Adulto) ---")
    auto.mostrar_estado_actual()
    #Guardar este estado como el perfil de desactivacion rápida
    gestor.guardar_perfil_rapido("MODO_ADULTO",auto.guardar_configuraciones_de_seguridad())

    print("\n--- 2. COnfigurando y Cambiando a modo infantil ---")
    auto.configurar(ventanas=True, puertas=True, cinturon=True, velocidad=80)
    auto.mostrar_estado_actual()

    #Guardar el estado como perfil de activacion rápida
    gestor.guardar_perfil_rapido("MODO_INFANTIL", auto.guardar_configuraciones_de_seguridad())
    #Guardadr en el historial cronológico para hacer Crtl+Z
    gestor.agregar_al_historial(auto.guardar_configuraciones_de_seguridad())

    print("\n--- 3. Cambiando a modo adulto usando perfil rápido ---")
    #utilizamos el Caretaker para recuperar el Memento del Modo Adulto
    memento_adulto = gestor.obtener_perfil_rapido("MODO_ADULTO")
    auto.restaurar_desde_memento(memento_adulto)
    auto.mostrar_estado_actual()

    print("\n--- 4. Usuario vuelve a activar el modo infantil rapidamente ---")
    memento_infantil = gestor.obtener_perfil_rapido("MODO_INFANTIL")
    auto.restaurar_desde_memento(memento_infantil)
    auto.mostrar_estado_actual()


