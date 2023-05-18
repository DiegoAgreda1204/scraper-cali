import os
import json
## selenium imports
from selenium import webdriver  # Import from seleniumwire
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import TimeoutException
import json
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
## libreria anti captcha
import time 
from tempfile import mkdtemp
import re

##codigo##

def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response

def handler(event, context):
    
    """
    API function to fetch comparendos data from Medellin website and RPA projects.
    This API works as core system to collect all the data from different sources.
    Args:
        request (POST): Json request has 
    Returns:
        object_response: Json object with the scraped data
    """
    number = event['number']
    doc_type = event['doc_type']
    
    object_response = {
        'data': list()
    }
    comparendos = {
        'comparendos': list(),
        'resoluciones': list()
    }

    start_urls = "https://serviciosdetransitodigitales.com/portal-servicios/#/public"
    #fields = ["Num_comparendo","Fecha","Hora","Dirección","Comparendo_electrónico","Fecha_notificación","Fuente_comparendo","Secretaría",
    #"Agente","Código","Descripción","Valor","S.M.D.V","Tipo_documento","Número_documento","Nombres","Apellidos","Tipo_de_infractor","Placa","Num_Licencia_del_vehículo",
    #"Tipo","Servicio","Num_Licencia","Fecha_vencimiento","Categoría","Secretaría","Municipio_comparendo","Localidad_comuna","Radio_acción"]

    # Create the webdriver object and pass the arguments
    options = webdriver.ChromeOptions()
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
    #binary = os.path.join(BASE_DIR, 'chromedriver/')
    #options.binary_location = binary
    # Ignores any certificate errors if there is any
    ### deshabilitar la sig linea cuando estas en local, habilitar en produccion #####
    options.binary_location = '/opt/chrome/chrome' 
    
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")
    # Startup the chrome webdriver with executable path and
    # pass the chrome options and desired capabilities as
    # parameters.
    driver = webdriver.Chrome('/opt/chromedriver',options=options,desired_capabilities=desired_capabilities)
    
    try:
        driver.get(start_urls)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@id='busqueda']")))
        text_area_for_id_number = driver.find_element(By.XPATH, "//input[@id='busqueda']")
        text_area_for_id_number.clear()
        
        text_area_for_id_number.send_keys(str(number))
        driver.find_element(By.XPATH, "//button[@id='btnBuscar']//*[name()='svg']").click()
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//*[@id='misMultasDos']/tbody")))

        logs = driver.get_log("performance")
        events = [process_browser_log_entry(entry) for entry in logs]
        events = [event for event in events if 'Network.response' in event['method']]
        for event in events:
            if event['method']=='Network.responseReceived' and event['params']['response']['url']=='https://serviciosdetransitodigitales.com/backavit/avit/home/findInfoHomePublic':
            
                body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': event["params"]["requestId"]}) 
                data = body['body']
                multa = json.loads(data)
                for multas in multa['consultaMultaOComparendoOutDTO']['informacionMulta']:
                    if multas['tipoComparendo'] == 'Electrónico':
                        comparendoElectronico = True
                    
                    if multas['fechaResolucion']:
                        comparendos['resoluciones'].append({
			                "estadoComparendo": "Resolucion" if multas['fechaResolucion'] else "Comparendo",
			                "fechaComparendo": multas['fechaComparendo'],
                            "fechaResolucion": multas['fechaResolucion'],
                            "numeroResolucion": multas['resolucion'],
			                "fotodeteccion": comparendoElectronico,
			                "numeroComparendo": re.sub("[^0-9]", "", multas['numeroComparendo']),
			                "placaVehiculo": multas['placa'],
			                "secretariaComparendo": 'Cali',
			                "total": str(multas['valor']),
			                "codigoInfraccion": multas['estadoCuenta']['codigoInfracciones'],
			                "descripcionInfraccion": multas['estadoCuenta']['descripcionInfracciones'],
                            "scraper": 'Juzto-cali',
                            "direccion": multas['estadoCuenta']['direccion'],
                            "nroCoactivo": None,
                            "fechaCoactivo": None,
                            "fechaNotificacion": None
                        })
                    else:
                        comparendos['comparendos'].append({
			                "estadoComparendo": "Resolucion" if multas['fechaResolucion'] else "Comparendo",
			                "fechaComparendo": multas['fechaComparendo'],
                            "fechaResolucion": multas['fechaResolucion'],
                            "numeroResolucion": multas['resolucion'],
			                "fotodeteccion": comparendoElectronico,
			                "numeroComparendo": re.sub("[^0-9]", "", multas['numeroComparendo']),
			                "placaVehiculo": multas['placa'],
			                "secretariaComparendo": 'Cali',
			                "total": str(multas['valor']),
			                "codigoInfraccion": multas['codigoInfracciones'],
			                "descripcionInfraccion": multas['descripcionInfracciones'],
                            "scraper": 'Juzto-cali',
                            "direccion": multas['estadoCuenta']['direccion'],
                            "nroCoactivo": None,
                            "fechaCoactivo": None,
                            "fechaNotificacion": None
                        })
                object_response['data'].append(comparendos) 
            
            
        object_response['status'] = 'success'
    except TimeoutException as ex:
        object_response['error'] = 'Timeout'
        object_response['status'] = 'error'
    except Exception as ex:
        object_response['error'] = str(ex)
        object_response['status'] = 'error'
    finally:
        driver.quit()
    
    return object_response
