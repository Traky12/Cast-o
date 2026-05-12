import React from "react";
import { SabiondaProfile } from "../components/Sabionda";

export const CoursesPage = () => {
  return (
    <div className="container mx-auto px-4 py-10">
      <h1 className="text-3xl md:text-4xl font-bold mb-6">
        Cursos de agrovoltaica con Sabionda
      </h1>
      <p className="text-gray-600 dark:text-gray-300 mb-10 max-w-2xl">
        Sabionda te acompaña en la parte técnica (IoT, IA) y en la parte
        agronómica (microgreens, agrovoltaica, bioeconomía) para que pases de
        TRL6 a TRL9 con seguridad y trazabilidad total.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
          <SabiondaProfile variant="profile" sizeClass="h-40" />
          <h2 className="text-xl font-semibold mt-4">
            Curso básico de agrovoltaica
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
            Fundamentos de agrovoltaica, gestión de bandejas B001–B048, curvas
            pH/EC y control de sombreo para maximizar kg + kWh.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
          <SabiondaProfile variant="tech" sizeClass="h-40" />
          <h2 className="text-xl font-semibold mt-4">
            Curso avanzado de IoT agrícola
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
            MQTT, FastAPI, n8n y VeChain para orquestar sensores, decisiones
            agronómicas y trazabilidad EPCIS en tiempo real.
          </p>
        </div>
      </div>
    </div>
  );
};

