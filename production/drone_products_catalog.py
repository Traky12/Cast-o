# -*- coding: utf-8 -*-
"""Catálogo de productos fabricados con drones para agritech (14+ tipos)."""
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from datetime import datetime


@dataclass
class DroneProduct:
    """Definición de un producto fabricado con drones para agritech."""
    product_id: str
    name: str
    description: str
    drone_type: str
    payload_capacity: float
    autonomy: float
    speed: float
    sensors: List[str]
    use_cases: List[str]
    compliance: List[str]
    production_cost: float
    sale_price: float
    production_time: int
    materials: List[str]
    local_suppliers: List[str]

    def to_dict(self) -> Dict:
        """Convierte el producto a diccionario para JSON."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "drone_type": self.drone_type,
            "payload_capacity": self.payload_capacity,
            "autonomy": self.autonomy,
            "speed": self.speed,
            "sensors": self.sensors,
            "use_cases": self.use_cases,
            "compliance": self.compliance,
            "production_cost": self.production_cost,
            "sale_price": self.sale_price,
            "production_time": self.production_time,
            "materials": self.materials,
            "local_suppliers": self.local_suppliers,
            "margin": round((self.sale_price - self.production_cost) / self.production_cost * 100, 2),
        }


class DroneProductsCatalog:
    """Catálogo completo de productos fabricados con drones para agritech."""

    def __init__(self) -> None:
        self.products = self._initialize_catalog()

    def _initialize_catalog(self) -> List[DroneProduct]:
        """Inicializa el catálogo con 14+ productos."""
        return [
            DroneProduct(
                product_id="CASTUO-DRONE-SPRAYER-001",
                name="PrecisionSprayer X1",
                description="Dron de fumigación de alta precisión con sistema de boquillas ajustables para aplicación variable de fitosanitarios.",
                drone_type="Multirrotor",
                payload_capacity=10.0,
                autonomy=45,
                speed=12,
                sensors=["GPS RTK", "LIDAR", "Cámara multiespectral", "Sensor de flujo"],
                use_cases=[
                    "Aplicación de herbicidas en cultivos extensivos",
                    "Tratamiento localizado de plagas",
                    "Fertilización foliar de precisión",
                    "Aplicación de bioestimulantes",
                ],
                compliance=[
                    "Reglamento (UE) 2019/787",
                    "RD 1311/2012 (uso sostenible de productos fitosanitarios)",
                    "ISO 16122 (equipos de protección de cultivos)",
                ],
                production_cost=4500,
                sale_price=8900,
                production_time=14,
                materials=["Fibra de carbono", "ABS reciclado", "Aleación de aluminio"],
                local_suppliers=[
                    "CarbonFiber Extremadura (Cáceres)",
                    "Plásticos Reciclados Badajoz",
                    "Aluminios del Tajo (Talavera)",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-SEEDER-001",
                name="SmartSeeder Pro",
                description="Dron para siembra directa con sistema de dosificación neumática y GPS RTK para patrones de siembra optimizados.",
                drone_type="Multirrotor",
                payload_capacity=15.0,
                autonomy=60,
                speed=10,
                sensors=["GPS RTK", "Sensor de profundidad", "Cámara RGB", "Sensor de humedad del suelo"],
                use_cases=[
                    "Siembra directa en cultivos extensivos",
                    "Resiembra en zonas con fallos de germinación",
                    "Siembra en terrenos difíciles o inclinados",
                    "Siembra de cubiertas vegetales",
                ],
                compliance=[
                    "Reglamento (UE) 2018/848 (producción ecológica)",
                    "ISO 11001 (siembra de precisión)",
                    "Normativa de semillas certificadas",
                ],
                production_cost=5200,
                sale_price=9800,
                production_time=16,
                materials=["Fibra de carbono", "PLA biodegradable", "Acero inoxidable"],
                local_suppliers=[
                    "Semillas Ecológicas Extremadura",
                    "BioPlásticos Iberia (Mérida)",
                    "Aceros del Guadiana",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-MULTISPECTRAL-001",
                name="AgroSense Elite",
                description="Dron equipado con cámaras multiespectrales y térmicas para análisis avanzado de cultivos.",
                drone_type="Ala fija",
                payload_capacity=2.5,
                autonomy=120,
                speed=25,
                sensors=[
                    "Cámara multiespectral (5 bandas)",
                    "Cámara térmica",
                    "GPS RTK",
                    "Sensor de humedad atmosférica",
                    "LIDAR",
                ],
                use_cases=[
                    "Detección temprana de estrés en cultivos",
                    "Mapas de vigor vegetal (NDVI)",
                    "Optimización de riego",
                    "Detección de enfermedades",
                    "Estimación de rendimiento",
                ],
                compliance=[
                    "Reglamento (UE) 2016/679 (GDPR para datos agrícolas)",
                    "ISO 19131 (especificaciones de productos de datos)",
                    "Normativa de protección de datos personales",
                ],
                production_cost=7800,
                sale_price=14500,
                production_time=20,
                materials=["Compuestos de fibra de carbono", "Aleación de magnesio", "Vidrio óptico"],
                local_suppliers=[
                    "Óptica Extremadura (Cáceres)",
                    "Aleaciones Ligeras Iberia",
                    "Electrónica Avanzada Badajoz",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-POLLINATOR-001",
                name="BeeDrone X",
                description="Dron diseñado para polinización asistida en cultivos que requieren polinización cruzada.",
                drone_type="Multirrotor",
                payload_capacity=5.0,
                autonomy=30,
                speed=8,
                sensors=["GPS", "Cámara macro", "Sensor de flujo de aire", "Sensor de humedad"],
                use_cases=[
                    "Polinización de almendros",
                    "Polinización de frutales (manzano, peral)",
                    "Polinización en invernaderos",
                    "Polinización de cultivos transgénicos controlados",
                ],
                compliance=[
                    "Reglamento (UE) 2018/848 (agricultura ecológica)",
                    "Normativa de bioseguridad para OGMs",
                    "Protocolos de polinización controlada",
                ],
                production_cost=3800,
                sale_price=7200,
                production_time=12,
                materials=["Plástico reciclado", "Aleación de aluminio", "Silicona alimentaria"],
                local_suppliers=[
                    "Reciclados Extremadura",
                    "Plásticos Agrícolas Sáenz (Badajoz)",
                    "Siliconas Ibéricas",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-CARGO-001",
                name="AgroCargo 50",
                description="Dron de carga para transporte de hasta 50kg en distancias cortas.",
                drone_type="Multirrotor (Hexacóptero)",
                payload_capacity=50.0,
                autonomy=25,
                speed=15,
                sensors=["GPS", "Sensor de peso", "Cámara de navegación", "LIDAR"],
                use_cases=[
                    "Transporte de herramientas entre parcelas",
                    "Movimiento de muestras para análisis",
                    "Distribución de suministros (semillas, fertilizantes)",
                    "Transporte de cosecha en terrenos difíciles",
                ],
                compliance=[
                    "Reglamento (UE) 2019/947 (drones)",
                    "Normativa de transporte de mercancías peligrosas (si aplica)",
                    "ISO 12405 (transporte de carga)",
                ],
                production_cost=6500,
                sale_price=12500,
                production_time=18,
                materials=["Fibra de carbono reforzada", "Acero", "Polímeros de alta resistencia"],
                local_suppliers=[
                    "CarbonFiber Extremadura",
                    "Aceros del Tajo",
                    "Polímeros Industriales Iberia",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-BIOSTIMULANT-001",
                name="BioStim Pro",
                description="Dron especializado en la aplicación de bioestimulantes y microorganismos beneficiosos.",
                drone_type="Multirrotor",
                payload_capacity=8.0,
                autonomy=40,
                speed=10,
                sensors=["GPS RTK", "Sensor de humedad", "Sensor de temperatura", "Cámara multiespectral"],
                use_cases=[
                    "Aplicación de bioestimulantes foliares",
                    "Inoculación de rizobacterias",
                    "Tratamiento con hongos micorrízicos",
                    "Aplicación de extractos de algas",
                ],
                compliance=[
                    "Reglamento (UE) 2019/1009 (fertilizantes)",
                    "Normativa de productos ecológicos",
                    "ISO 19602 (bioestimulantes)",
                ],
                production_cost=4200,
                sale_price=8200,
                production_time=14,
                materials=["PLA biodegradable", "Acero inoxidable", "Silicona médica"],
                local_suppliers=[
                    "Bioestimulantes Extremadura",
                    "Plásticos Ecológicos Iberia",
                    "Aceros Inoxidables del Guadiana",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-3DMAPPER-001",
                name="TerraMapper 3D",
                description="Dron equipado con LIDAR y cámaras estéreo para generación de modelos 3D de terrenos agrícolas.",
                drone_type="Ala fija",
                payload_capacity=3.0,
                autonomy=90,
                speed=20,
                sensors=["LIDAR", "Cámara estéreo", "GPS RTK", "IMU de alta precisión"],
                use_cases=[
                    "Generación de modelos digitales de elevación (DEM)",
                    "Planificación de sistemas de riego",
                    "Diseño de terrazas en terrenos inclinados",
                    "Evaluación de erosión del suelo",
                ],
                compliance=[
                    "ISO 19130 (modelos de sensor)",
                    "Normativa de cartografía oficial",
                    "Reglamento (UE) 2016/679 (protección de datos)",
                ],
                production_cost=8500,
                sale_price=15500,
                production_time=22,
                materials=["Fibra de carbono", "Aleación de titanio", "Vidrio óptico"],
                local_suppliers=[
                    "Óptica de Precisión Extremadura",
                    "Aleaciones Especiales Iberia",
                    "Compuestos Avanzados Cáceres",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-SOILSAMPLER-001",
                name="SoilSampler X",
                description="Dron equipado con taladro automático para toma de muestras de suelo a diferentes profundidades.",
                drone_type="Multirrotor",
                payload_capacity=12.0,
                autonomy=35,
                speed=8,
                sensors=["GPS RTK", "Sensor de profundidad", "Cámara de alta resolución", "Sensor de humedad del suelo"],
                use_cases=[
                    "Toma de muestras para análisis de suelo",
                    "Mapas de fertilidad del suelo",
                    "Detección de contaminantes",
                    "Evaluación de materia orgánica",
                ],
                compliance=[
                    "ISO 10381 (muestreo de suelo)",
                    "Normativa de gestión de residuos",
                    "Protocolos de bioseguridad",
                ],
                production_cost=5800,
                sale_price=11200,
                production_time=18,
                materials=["Acero inoxidable", "Polímeros resistentes a químicos", "Aleación de aluminio"],
                local_suppliers=[
                    "Aceros Inoxidables Extremadura",
                    "Polímeros Industriales Badajoz",
                    "Aleaciones Ligeras Iberia",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-PRUNER-001",
                name="AutoPruner 2000",
                description="Dron equipado con brazos robóticos para poda de precisión en viñedos y frutales.",
                drone_type="Multirrotor (Hexacóptero)",
                payload_capacity=15.0,
                autonomy=20,
                speed=5,
                sensors=["Cámara estéreo", "LIDAR", "GPS RTK", "Sensor de fuerza"],
                use_cases=[
                    "Poda de viñedos",
                    "Poda de frutales (olivo, almendro)",
                    "Poda de formación en cultivos leñosos",
                    "Eliminación de brotes no deseados",
                ],
                compliance=[
                    "Normativa de seguridad en maquinaria agrícola",
                    "ISO 5395 (equipos de poda)",
                    "Reglamento (UE) 2016/426 (maquinaria)",
                ],
                production_cost=7200,
                sale_price=13800,
                production_time=20,
                materials=["Aleación de aluminio", "Acero templado", "Compuestos de fibra de carbono"],
                local_suppliers=[
                    "Aleaciones del Tajo",
                    "Aceros Templados Extremadura",
                    "Compuestos Avanzados Cáceres",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-COVERCROP-001",
                name="CoverCrop Drone",
                description="Dron especializado en siembra de cubiertas vegetales entre cultivos principales.",
                drone_type="Multirrotor",
                payload_capacity=20.0,
                autonomy=45,
                speed=10,
                sensors=["GPS RTK", "Sensor de flujo de semillas", "Cámara RGB"],
                use_cases=[
                    "Siembra de cubiertas vegetales en viñedos",
                    "Siembra de leguminosas para fijación de nitrógeno",
                    "Siembra de abonos verdes",
                    "Control de malezas con cubiertas",
                ],
                compliance=[
                    "Reglamento (UE) 2018/848 (agricultura ecológica)",
                    "Normativa de rotación de cultivos",
                    "ISO 11001 (siembra de precisión)",
                ],
                production_cost=4800,
                sale_price=9200,
                production_time=15,
                materials=["Plástico reciclado", "Aleación de aluminio", "ABS"],
                local_suppliers=[
                    "Reciclados Extremadura",
                    "Plásticos Agrícolas Sáenz",
                    "Aluminios del Guadiana",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-THERMAL-001",
                name="ThermalTreatment X",
                description="Dron equipado con emisores de infrarrojos para tratamientos térmicos contra plagas.",
                drone_type="Multirrotor",
                payload_capacity=5.0,
                autonomy=30,
                speed=8,
                sensors=["GPS RTK", "Sensor de temperatura", "Cámara térmica", "Anemómetro"],
                use_cases=[
                    "Tratamiento térmico contra mosca del olivo",
                    "Control de polilla del racimo en viñedos",
                    "Tratamiento térmico en almacenes",
                    "Desinfección de suelos con calor",
                ],
                compliance=[
                    "Reglamento (UE) 2019/1009 (productos fitosanitarios)",
                    "Normativa de seguridad en tratamientos térmicos",
                    "ISO 16122 (equipos de protección de cultivos)",
                ],
                production_cost=5500,
                sale_price=10500,
                production_time=17,
                materials=["Aleación de aluminio", "Cerámica térmica", "Polímeros resistentes al calor"],
                local_suppliers=[
                    "Cerámicas Extremadura",
                    "Aleaciones del Tajo",
                    "Polímeros Térmicos Iberia",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-LIVESTOCK-001",
                name="LivestockMonitor Pro",
                description="Dron equipado con cámaras térmicas y de alta resolución para monitoreo de ganado.",
                drone_type="Ala fija",
                payload_capacity=2.0,
                autonomy=120,
                speed=22,
                sensors=["Cámara térmica", "Cámara 4K", "GPS RTK", "Micrófono direccional"],
                use_cases=[
                    "Monitoreo de rebaños en dehesas",
                    "Detección de animales enfermos o heridos",
                    "Evaluación de calidad de pastos",
                    "Localización de animales perdidos",
                ],
                compliance=[
                    "Normativa de bienestar animal",
                    "Reglamento (UE) 2016/429 (sanidad animal)",
                    "ISO 30000 (gestión de la cadena de suministro ganadera)",
                ],
                production_cost=6800,
                sale_price=12800,
                production_time=19,
                materials=["Fibra de carbono", "Aleación de magnesio", "Vidrio óptico"],
                local_suppliers=[
                    "Óptica Extremadura",
                    "Aleaciones Ligeras Iberia",
                    "Compuestos Avanzados Cáceres",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-PHEROMONE-001",
                name="PheromoneDrone X",
                description="Dron especializado en la distribución de feromonas para control de plagas mediante confusión sexual.",
                drone_type="Multirrotor",
                payload_capacity=6.0,
                autonomy=50,
                speed=10,
                sensors=["GPS RTK", "Sensor de flujo", "Cámara RGB", "Sensor de temperatura"],
                use_cases=[
                    "Control de polilla del tomate",
                    "Confusión sexual en viñedos",
                    "Control de mosca del olivo",
                    "Manejo de plagas en cultivos hortícolas",
                ],
                compliance=[
                    "Reglamento (UE) 2019/1009 (fertilizantes y mejoradores del suelo)",
                    "Normativa de productos fitosanitarios",
                    "ISO 19602 (bioestimulantes y feromonas)",
                ],
                production_cost=4700,
                sale_price=8900,
                production_time=14,
                materials=["PLA biodegradable", "Acero inoxidable", "Polímeros químicamente inertes"],
                local_suppliers=[
                    "BioPlásticos Extremadura",
                    "Aceros Inoxidables del Guadiana",
                    "Polímeros Químicos Iberia",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-INSPECTOR-001",
                name="AgroInspector 360",
                description="Dron equipado con cámaras de alta resolución y sensores para inspección de infraestructuras agrícolas.",
                drone_type="Multirrotor",
                payload_capacity=3.0,
                autonomy=60,
                speed=12,
                sensors=["Cámara 4K", "Cámara térmica", "LIDAR", "GPS RTK"],
                use_cases=[
                    "Inspección de invernaderos",
                    "Detección de fugas en sistemas de riego",
                    "Evaluación estructural de almacenes",
                    "Inspección de paneles solares en agrovoltaica",
                ],
                compliance=[
                    "Normativa de seguridad en instalaciones agrícolas",
                    "ISO 9001 (gestión de calidad)",
                    "Reglamento (UE) 305/2011 (productos de construcción)",
                ],
                production_cost=5200,
                sale_price=9800,
                production_time=16,
                materials=["Fibra de carbono", "Aleación de aluminio", "Vidrio óptico"],
                local_suppliers=[
                    "Óptica de Precisión Extremadura",
                    "Aleaciones del Tajo",
                    "Compuestos Avanzados Cáceres",
                ],
            ),
            DroneProduct(
                product_id="CASTUO-DRONE-MYCORRHIZAE-001",
                name="MycoDrone Pro",
                description="Dron especializado en la aplicación de esporas de hongos micorrícicos para mejorar la absorción de nutrientes.",
                drone_type="Multirrotor",
                payload_capacity=7.0,
                autonomy=40,
                speed=8,
                sensors=["GPS RTK", "Sensor de humedad", "Cámara multiespectral", "Sensor de flujo"],
                use_cases=[
                    "Aplicación de micorrizas en viñedos",
                    "Inoculación en cultivos extensivos",
                    "Mejora de suelos degradados",
                    "Aplicación en viveros",
                ],
                compliance=[
                    "Reglamento (UE) 2019/1009 (fertilizantes)",
                    "Normativa de productos biológicos",
                    "ISO 19602 (bioestimulantes)",
                ],
                production_cost=4300,
                sale_price=8200,
                production_time=14,
                materials=["PLA biodegradable", "Acero inoxidable", "Polímeros resistentes a UV"],
                local_suppliers=[
                    "BioPlásticos Extremadura",
                    "Aceros Inoxidables del Guadiana",
                    "Polímeros Agrícolas Sáenz",
                ],
            ),
        ]

    def get_product_by_id(self, product_id: str) -> Optional[DroneProduct]:
        """Obtiene un producto por su ID."""
        for product in self.products:
            if product.product_id == product_id:
                return product
        return None

    def get_products_by_use_case(self, use_case: str) -> List[DroneProduct]:
        """Filtra productos por caso de uso."""
        return [p for p in self.products if use_case.lower() in [uc.lower() for uc in p.use_cases]]

    def get_products_by_material(self, material: str) -> List[DroneProduct]:
        """Filtra productos por material."""
        return [p for p in self.products if material.lower() in [m.lower() for m in p.materials]]

    def calculate_production_plan(self, product_id: str, units: int) -> Dict:
        """Calcula un plan de producción para un producto específico."""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Producto {product_id} no encontrado")
        margin_pct = (product.sale_price - product.production_cost) / product.production_cost * 100
        return {
            "product": product.name,
            "units": units,
            "total_production_cost": product.production_cost * units,
            "total_sale_price": product.sale_price * units,
            "total_profit": (product.sale_price - product.production_cost) * units,
            "production_time_days": product.production_time * units,
            "materials_required": {mat: units for mat in product.materials},
            "local_suppliers": product.local_suppliers,
            "compliance_requirements": product.compliance,
            "margin_per_unit": round(margin_pct, 2),
            "total_margin": round(margin_pct, 2),
        }

    def export_catalog(self, format: str = "json") -> str:
        """Exporta el catálogo en el formato especificado."""
        if format.lower() == "json":
            return json.dumps([p.to_dict() for p in self.products], indent=2)
        if format.lower() == "csv":
            import csv
            import io
            out = io.StringIO()
            if self.products:
                writer = csv.DictWriter(out, fieldnames=list(self.products[0].to_dict().keys()))
                writer.writeheader()
                writer.writerows(p.to_dict() for p in self.products)
            return out.getvalue()
        raise ValueError(f"Formato no soportado: {format}")


if __name__ == "__main__":
    catalog = DroneProductsCatalog()
    print("Catálogo de Productos Fabricados con Drones (15):")
    for product in catalog.products:
        d = product.to_dict()
        print(f"  {product.name} ({product.product_id}) - Margen: {d['margin']}%")
    plan = catalog.calculate_production_plan("CASTUO-DRONE-SPRAYER-001", 10)
    print(f"\nPlan 10 ud PrecisionSprayer: beneficio €{plan['total_profit']:,}")
