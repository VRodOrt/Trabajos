# 🚀 IT Operations Analytics: De Datos Crudos a Estrategia con IA

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-orange)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-red)
![Status](https://img.shields.io/badge/Status-Completed-success)

## 📋 Descripción del Proyecto

En el ecosistema empresarial actual, los departamentos de TI generan miles de registros de incidencias que a menudo se infrautilizan. Este proyecto simula un caso real de consultoría de datos, cuyo objetivo es **transformar logs operativos planos en un Plan Estratégico de Negocio**.

A través de un ciclo completo de Data Science, el proyecto audita la eficiencia del servicio, detecta riesgos de capital humano (burnout) y aplica algoritmos de **Machine Learning (K-Means y Random Forest)** para segmentar incidencias y predecir cargas de trabajo.

## 🎯 Objetivos de Negocio Resueltos

El análisis responde a preguntas críticas para la dirección:
1.  **Eficiencia Operativa:** ¿Dónde están los cuellos de botella y los "agujeros negros" de productividad?
2.  **Sostenibilidad del Equipo:** ¿Existe riesgo de fuga de talento o dependencia crítica de una sola persona ("Bus Factor")?
3.  **Calidad del Servicio:** ¿Estamos resolviendo los problemas de raíz o solo poniendo parches (incidencias zombie)?
4.  **Optimización de Costes:** ¿Qué incidencias deberíamos automatizar con Chatbots/RPA?

## 🛠️ Stack Tecnológico

* **Ingeniería de Datos:** `Pandas`, `NumPy` (Limpieza robusta, manejo de encoding `latin1`/`utf-8`, ingeniería de variables temporales).
* **Visualización:** `Seaborn`, `Matplotlib` (Heatmaps, Diagramas de Pareto, Violines, Scatter Plots).
* **Machine Learning:**
    * **Scikit-Learn:** Clustering K-Means (Segmentación no supervisada), Random Forest (Simulación de escenarios).
    * **Statsmodels:** Holt’s Exponential Smoothing (Forecasting de demanda temporal).

## 📊 Estructura del Análisis

El notebook sigue una narrativa de negocio estructurada en 5 fases:

1.  **🛡️ Data Quality & Ingesta:** Pipeline de carga "fail-safe" y normalización de esquemas.
2.  **📈 Business Intelligence (BI):**
    * Ley de Pareto (80/20) en solicitantes.
    * Matriz de Desempeño Técnico (Velocidad vs. Volumen).
3.  **⚠️ Auditoría de Riesgos (RRHH):**
    * Cálculo de "Carga Oculta" (Trabajo fuera de horario).
    * Detección del "Bus Factor" (Dependencia crítica de un técnico).
4.  **📉 Calidad y Retención:**
    * Análisis de Recidiva (Problemas Zombie).
    * Riesgo de Fuga de Clientes (Churn Risk por Recencia).
5.  **🤖 Advanced Analytics & AI:**
    * **Segmentación K-Means:** Descubrimiento de 3 clusters operativos (Quick Wins, Proyectos, Bloqueos).
    * **Scorecard Ejecutivo:** Generación automática de recomendaciones estratégicas.

## 💡 Insights Clave (Resultados)

Tras el análisis, se obtuvieron las siguientes conclusiones estratégicas:

* **Riesgo Crítico:** Se detectó una dependencia del **30%** en un único técnico, lo que representa un riesgo operativo inaceptable.
* **Oportunidad de Ahorro:** El algoritmo K-Means identificó un cluster de "Quick Wins" (alto volumen, baja complejidad) ideal para ser automatizado, liberando un **20% de la carga de trabajo**.
* **Ineficiencia de Procesos:** Se identificaron cuellos de botella administrativos donde los tickets pasan semanas abiertos con menos de 1 hora de trabajo real.

## 🚀 Cómo ejecutar este proyecto

1.  Clonar el repositorio:
    ```bash
    git clone [https://github.com/TU_USUARIO/IT-Operations-Analytics.git](https://github.com/TU_USUARIO/IT-Operations-Analytics.git)
    ```
2.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ejecutar el notebook `Análisis.ipynb` en Jupyter Lab, VS Code o Google Colab.

---
*Portfolio de Data Science & Operations Analytics*
