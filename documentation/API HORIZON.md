# Horizons File API

**Versión:** 1.0 (Julio 2021)  
[change log](https://ssd.jpl.nasa.gov/api/horizons_file.api)

Esta API proporciona acceso al sistema Horizons de JPL. Se debe crear un archivo de entrada que contenga configuraciones apropiadas para los resultados de efemérides deseados. Consulte el ejemplo/instrucciones por lotes de Horizons para obtener detalles sobre las configuraciones posibles. Hay disponible una API alternativa de Horizons que usa el método HTTP GET para enviar parámetros de Horizons como parámetros de consulta a través de la URL.

## Solicitud HTTP

```
POST https://ssd.jpl.nasa.gov/api/horizons_file.api
```

## Ejemplo de Consulta de Efemérides

Dado el siguiente archivo de entrada llamado `my_input_file.txt` que solicita una efeméride de observador de Marte:

```
!$$SOF
COMMAND='499'
OBJ_DATA='YES'
MAKE_EPHEM='YES'
TABLE_TYPE='OBSERVER'
CENTER='500@399'
START_TIME='2006-01-01'
STOP_TIME='2006-01-20'
STEP_SIZE='1 d'
QUANTITIES='1,9,20,23,24,29'
```

### Ejemplo con curl

Usando curl, envía la solicitud POST a la API y guarda la salida en el archivo results.txt:

```bash
curl -s -F format=text -F input=@my_input_file.txt https://ssd.jpl.nasa.gov/api/horizons_file.api > results.txt
```

### Ejemplo con Python

Usando python, envía el archivo de entrada y guarda la salida en results.txt:

```bash
python horizons.py my_input_file.txt > results.txt
```

donde `horizons.py` es el siguiente:

```python
import sys
import requests
f = open(sys.argv[1])
url = 'https://ssd.jpl.nasa.gov/api/horizons_file.api'
r = requests.post(url, data={'format':'text'}, files={'input': f})
print(r.text)
f.close()
```

### Ejemplo con Perl

Usando perl, envía el archivo de entrada y guarda la salida en results.txt:

```bash
perl horizons.pl my_input_file.txt > results.txt
```

donde `horizons.pl` es el siguiente:

```perl
use strict;
use LWP::UserAgent;
my $file = shift;
my $ua = LWP::UserAgent->new;
my $url = 'https://ssd.jpl.nasa.gov/api/horizons_file.api';
my $res = $ua->post($url,
  Content_Type=>'form-data',
  Content=>[
    'format' => 'text',
    'input' => [ $file ],
  ],
);
print $res->content;
```

## Parámetros de Consulta

| Parámetro | Tipo | Predeterminado | Valores/Formato Permitidos | Descripción |
|-----------|------|----------------|----------------------------|-------------|
| input | string | ninguno | ver descripción abajo | Contenido del archivo de entrada de Horizons, codificado apropiadamente |
| format | string | json | json, text | formato de salida: json para JSON o text para texto plano |

## Salida de Datos

Siempre verifique el objeto "signature" del payload JSON para la "version" de la API. Si la versión no coincide con la versión en este documento (en la parte superior), no hay garantía de que el formato no haya cambiado.

Ejemplo del objeto "signature" con valor de "version" "1.0":
```json
"signature":{"version":"1.0","source":"NASA/JPL ... API"}
```

Las solicitudes de consulta exitosas resultan en un payload de datos. El formato está controlado por el parámetro format.

### Ejemplo de Salida en Formato Texto

Las primeras dos líneas son agregadas por la API. Es importante notar el valor de API VERSION al procesar programáticamente los resultados para asegurar que la versión sea la que esperas. El número de líneas en blanco después de API SOURCE puede variar pero será al menos una. Si solicitas la página de información del cuerpo (`OBJ_DATA='YES'`), habrá un bloque adicional de salida de texto después de las líneas en blanco que siguen a API SOURCE. El resto de la salida está formateada como la proporciona el sistema Horizons.

```
API VERSION: 0.2
API SOURCE: NASA/JPL Horizons API

*******************************************************************************
Ephemeris / WWW_USER Thu May 14 07:39:14 2020 Pasadena, USA      / Horizons    
*******************************************************************************
Target body name: Mars (499)                      {source: mar097}
Center body name: Earth (399)                     {source: mar097}
Center-site name: GEOCENTRIC
*******************************************************************************
Start time      : A.D. 1998-Jan-01 10:00:00.0000 UT      
Stop  time      : A.D. 1998-Jan-02 00:00:00.0000 UT      
Step-size       : 60 minutes
*******************************************************************************
Target pole/equ : IAU_MARS                        {West-longitude positive}
Target radii    : 3396.2 x 3396.2 x 3376.2 km     {Equator, meridian, pole}    
Center geodetic : 0.00000000,0.00000000,0.0000000 {E-lon(deg),Lat(deg),Alt(km)}
Center cylindric: 0.00000000,0.00000000,0.0000000 {E-lon(deg),Dxy(km),Dz(km)}
Center pole/equ : High-precision EOP model        {East-longitude positive}
Center radii    : 6378.1 x 6378.1 x 6356.8 km     {Equator, meridian, pole}    
Target primary  : Sun
Vis. interferer : MOON (R_eq= 1737.400) km        {source: mar097}
Rel. light bend : Sun, EARTH                      {source: mar097}
Rel. lght bnd GM: 1.3271E+11, 3.9860E+05 km^3/s^2                              
Atmos refraction: NO (AIRLESS)
RA format       : HMS
Time format     : CAL
EOP file        : eop.200513.p200804                                           
EOP coverage    : DATA-BASED 1962-JAN-20 TO 2020-MAY-13. PREDICTS-> 2020-AUG-03
Units conversion: 1 au= 149597870.700 km, c= 299792.458 km/s, 1 day= 86400.0 s
Table cut-offs 1: Elevation (-90.0deg=NO ),Airmass (>38.000=NO), Daylight (NO )
Table cut-offs 2: Solar elongation (  0.0,180.0=NO ),Local Hour Angle( 0.0=NO )
Table cut-offs 3: RA/DEC angular rate (     0.0=NO )                           
*****************************************************************************************
 Date__(UT)__HR:MN     R.A._____(ICRF)_____DEC  APmag  S-brt            delta      deldot
*****************************************************************************************
$$SOE
 1998-Jan-01 10:00     20 55 41.20 -18 33 23.0   1.17   4.08 2.13799045474771   5.6049390
 1998-Jan-01 11:00     20 55 49.17 -18 32 49.7   1.17   4.08 2.13812533287512   5.6044117
 1998-Jan-01 12:00     20 55 57.13 -18 32 16.5   1.17   4.08 2.13826019831403   5.6038846
 1998-Jan-01 13:00     20 56 05.09 -18 31 43.1   1.17   4.08 2.13839505107206   5.6033579
 1998-Jan-01 14:00     20 56 13.05 -18 31 09.8   1.17   4.08 2.13852989115697   5.6028315
 1998-Jan-01 15:00     20 56 21.01 -18 30 36.5   1.17   4.08 2.13866471857652   5.6023055
 1998-Jan-01 16:00     20 56 28.97 -18 30 03.1   1.17   4.08 2.13879953333835   5.6017797
 1998-Jan-01 17:00     20 56 36.93 -18 29 29.7   1.17   4.08 2.13893433545018   5.6012543
 1998-Jan-01 18:00     20 56 44.89 -18 28 56.3   1.17   4.08 2.13906912492008   5.6007292
 1998-Jan-01 19:00     20 56 52.85 -18 28 22.9   1.17   4.08 2.13920390175678   5.6002045
 1998-Jan-01 20:00     20 57 00.81 -18 27 49.4   1.17   4.08 2.13933866596968   5.5996802
 1998-Jan-01 21:00     20 57 08.76 -18 27 15.9   1.17   4.08 2.13947341756857   5.5991564
 1998-Jan-01 22:00     20 57 16.72 -18 26 42.5   1.17   4.08 2.13960815656331   5.5986329
 1998-Jan-01 23:00     20 57 24.67 -18 26 08.9   1.17   4.08 2.13974288296371   5.5981098
 1998-Jan-02 00:00     20 57 32.63 -18 25 35.4   1.17   4.08 2.13987759677950   5.5975872
$$EOE
*****************************************************************************************
```

**Significado de las columnas:**

... [parte del contenido excluida por brevedad] ...

```
Computations by ...
     Solar System Dynamics Group, Horizons On-Line Ephemeris System
     4800 Oak Grove Drive, Jet Propulsion Laboratory
     Pasadena, CA  91109   USA
     Information: http://ssd.jpl.nasa.gov/
     Connect    : telnet://ssd.jpl.nasa.gov:6775  (via browser)
                  telnet ssd.jpl.nasa.gov 6775    (via command-line)
     Author     : Jon.D.Giorgini@jpl.nasa.gov
```

Si hay errores en su archivo de entrada (como solicitar tiempos de salida de efemérides fuera del rango disponible), se mostrarán al final de la salida normal. Por lo tanto, tal detección de errores es responsabilidad del usuario.

En algunos casos, los mensajes de error proporcionarán sugerencias que solo son aplicables a la interfaz de línea de comandos. Por ejemplo, al especificar un código de observatorio que no existe, el mensaje sugiere ..., ?! para ayuda. En tales casos, si el error no es obvio, consulte la documentación del sistema Horizons.

### Ejemplo de Salida en Formato JSON

Cuando se solicita el formato json, la API intenta detectar cualquier mensaje de error de Horizon, capturarlos y reportarlos en el campo error. Por lo tanto, si el campo error está presente en la salida, se puede emitir una respuesta programática apropiada.

En la siguiente solicitud exitosa, el contenido de interés estará en el campo result de JSON.

```json
{
  "signature" : {
    "source" : "NASA/JPL Horizons API",
    "version" : "0.2"
  },
  "result" : " \n \n*******************************************************************************\nEphemeris / WWW_USER Thu May 14 08:06:02 2020 Pasadena, USA      / Horizons    \n*******************************************************************************\nTarget body name: Mars (499)                      {source: mar097}\nCenter body name: Earth (399)                     {source: mar097}\nCenter-site name: GEOCENTRIC\n*******************************************************************************\nStart time      : A.D. 1998-Jan-01 10:00:00.0000 UT      \nStop  time      : A.D. 1998-Jan-02 00:00:00.0000 UT      \nStep-size       : 60 minutes\n*******************************************************************************\nTarget pole/equ : IAU_MARS                        {West-longitude positive}\nTarget radii    : 3396.2 x 3396.2 x 3376.2 km     {Equator, meridian, pole}    \nCenter geodetic : 0.00000000,0.00000000,0.0000000 {E-lon(deg),Lat(deg),Alt(km)}\nCenter cylindric: 0.00000000,0.00000000,0.0000000 {E-lon(deg),Dxy(km),Dz(km)}\nCenter pole/equ : High-precision EOP model        {East-longitude positive}\nCenter radii    : 6378.1 x 6378.1 x 6356.8 km     {Equator, meridian, pole}    \nTarget primary  : Sun\nVis. interferer : MOON (R_eq= 1737.400) km        {source: mar097}\nRel. light bend : Sun, EARTH                      {source: mar097}\nRel. lght bnd GM: 1.3271E+11, 3.9860E+05 km^3/s^2                              \nAtmos refraction: NO (AIRLESS)\nRA format       : HMS\nTime format     : CAL \nEOP file        : eop.200513.p200804                                           \nEOP coverage    : DATA-BASED 1962-JAN-20 TO 2020-MAY-13. PREDICTS-> 2020-AUG-03\nUnits conversion: 1 au= 149597870.700 km, c= 299792.458 km/s, 1 day= 86400.0 s \nTable cut-offs 1: Elevation (-90.0deg=NO ),Airmass (>38.000=NO), Daylight (NO )\nTable cut-offs 2: Solar elongation (  0.0,180.0=NO ),Local Hour Angle( 0.0=NO )\nTable cut-offs 3: RA/DEC angular rate (     0.0=NO )                           \n*****************************************************************************************\n Date__(UT)__HR:MN     R.A._____(ICRF)_____DEC  APmag  S-brt            delta      deldot\n*****************************************************************************************\n$$SOE\n 1998-Jan-01 10:00     20 55 41.20 -18 33 23.0   1.17   4.08 2.13799045474771   5.6049390\n 1998-Jan-01 11:00     20 55 49.17 -18 32 49.7   1.17   4.08 2.13812533287512   5.6044117\n 1998-Jan-01 12:00     20 55 57.13 -18 32 16.5   1.17   4.08 2.13826019831403   5.6038846\n 1998-Jan-01 13:00     20 56 05.09 -18 31 43.1   1.17   4.08 2.13839505107206   5.6033579\n 1998-Jan-01 14:00     20 56 13.05 -18 31 09.8   1.17   4.08 2.13852989115697   5.6028315\n 1998-Jan-01 15:00     20 56 21.01 -18 30 36.5   1.17   4.08 2.13866471857652   5.6023055\n 1998-Jan-01 16:00     20 56 28.97 -18 30 03.1   1.17   4.08 2.13879953333835   5.6017797\n 1998-Jan-01 17:00     20 56 36.93 -18 29 29.7   1.17   4.08 2.13893433545018   5.6012543\n 1998-Jan-01 18:00     20 56 44.89 -18 28 56.3   1.17   4.08 2.13906912492008   5.6007292\n 1998-Jan-01 19:00     20 56 52.85 -18 28 22.9   1.17   4.08 2.13920390175678   5.6002045\n 1998-Jan-01 20:00     20 57 00.81 -18 27 49.4   1.17   4.08 2.13933866596968   5.5996802\n 1998-Jan-01 21:00     20 57 08.76 -18 27 15.9   1.17   4.08 2.13947341756857   5.5991564\n 1998-Jan-01 22:00     20 57 16.72 -18 26 42.5   1.17   4.08 2.13960815656331   5.5986329\n 1998-Jan-01 23:00     20 57 24.67 -18 26 08.9   1.17   4.08 2.13974288296371   5.5981098\n 1998-Jan-02 00:00     20 57 32.63 -18 25 35.4   1.17   4.08 2.13987759677950   5.5975872\n$$EOE\n*****************************************************************************************\nColumn meaning:\n \nTIME\n\n  Times PRIOR to 1962 are UT1, a mean-solar time closely related to the\nprior but now-deprecated GMT. Times AFTER 1962 are in UTC, the current\ncivil or \"wall-clock\" time-scale. UTC is kept within 0.9 seconds of UT1\nusing integer leap-seconds for 1972 and later years.\n\n  Conversion from the internal Barycentric Dynamical Time (TDB) of solar\nsystem dynamics to the non-uniform civil UT time-scale requested for output\nhas not been determined for UTC times after the next July or January 1st.\nTherefore, the last known leap-second is used as a constant over future\nintervals.\n\n  Time tags refer to the UT time-scale conversion from TDB on Earth\nregardless of observer location within the solar system, although clock\nrates may differ due to the local gravity field and no analog to \"UT\"\nmay be defined for that location.\n\n  Any 'b' symbol in the 1st-column denotes a B.C. date. First-column blank\n(\" \") denotes an A.D. date. Calendar dates prior to 1582-Oct-15 are in the\nJulian calendar system. Later calendar dates are in the Gregorian system.\n\n  NOTE: \"n.a.\" in output means quantity \"not available\" at the print-time.\n \n R.A._____(ICRF)_____DEC =\n  Astrometric right ascension and declination of the target center with\nrespect to the observing site (coordinate origin) in the reference frame of\nthe planetary ephemeris (ICRF). Compensated for down-leg light-time delay\naberration.\n\n  Units: RA  in hours-minutes-seconds of time   (HH MM SS.ff)\n         DEC in degrees-minutes-seconds of arc  (sDD MN SC.f)\n \n APmag S-brt =\n   Target's approximate apparent visual magnitude & surface brightness. For\nplanets and satellites, values are available only for solar phase angles in the\nrange generally visible from Earth. This is to avoid extrapolation of models\nbeyond their valid (data-based) limits.\n   Units: MAGNITUDE & VISUAL MAGNITUDES PER SQUARE ARCSECOND\n \n delta  deldot =\n   Range (\"delta\") and range-rate (\"delta-dot\") of target center with respect\nto the observer at the instant light seen by the observer at print-time would\nhave left the target center (print-time minus down-leg light-time); the\ndistance traveled by a light ray emanating from the center of the target and\nrecorded by the observer at print-time. \"deldot\" is a projection of the\nvelocity vector along this ray, the light-time-corrected line-of-sight from\nthe coordinate center, and indicates relative motion. A positive \"deldot\"\nmeans the target center is moving away from the observer (coordinate center).\nA negative \"deldot\" means the target center is moving toward the observer.\nUnits: AU and KM/S\n\n\n Computations by ...\n     Solar System Dynamics Group, Horizons On-Line Ephemeris System\n     4800 Oak Grove Drive, Jet Propulsion Laboratory\n     Pasadena, CA  91109   USA\n     Information: http://ssd.jpl.nasa.gov/\n     Connect    : telnet://ssd.jpl.nasa.gov:6775  (via browser)\n                  telnet ssd.jpl.nasa.gov 6775    (via command-line)\n     Author     : Jon.D.Giorgini@jpl.nasa.gov\n\n*****************************************************************************************\n"
}
```

## Especificación de Objeto No Único

Si el objeto especificado a través de la variable COMMAND en el archivo de entrada no es único para el sistema Horizons, obtendrá una lista de objetos coincidentes. A continuación se muestra un ejemplo de salida (formato texto) donde `COMMAND='DES=141P;'`.

```
API VERSION: 0.2
API SOURCE: NASA/JPL Horizons API

*******************************************************************************
JPL/DASTCOM            Small-body Index Search Results     2021-May-11 07:53:26

 Comet AND asteroid index search:

    DES = 141P;

 Matching small-bodies:

    Record #  Epoch-yr  >MATCH DESIG<  Primary Desig  Name  
    --------  --------  -------------  -------------  -------------------------
    90001032    2011    141P           141P            Machholz 2
    90001033    2019    141P           141P            Machholz 2
    90001034    1994    141P-A         141P-A          Machholz 2
    90001035    1997    141P-A         141P-A          Machholz 2
    90001036    1999    141P-A         141P-A          Machholz 2
    90001037    1994    141P-D         141P-D          Machholz 2
    90001038    1999    141P-D         141P-D          Machholz 2

 (7 matches. To SELECT, enter record # (integer), followed by semi-colon.)
*******************************************************************************
```

En el ejemplo anterior, hay tres cuerpos representados: el cometa padre 141P, el fragmento A 141P-A y el fragmento D 141P-D. También hay múltiples órbitas para cada uno de estos cometas representadas por el campo Epoch-yr en la tabla de resultados. Para seleccionar el objeto y la órbita de interés, debe especificar el número de registro de Horizons listado en la columna Record #. Por ejemplo, para seleccionar la órbita para el cometa padre con época 2019, especifique `COMMAND='90001033;'` en su archivo de entrada. Sin embargo, tenga en cuenta que para cuerpos pequeños (cometas y asteroides) estos números de registro están sujetos a cambios sin previo aviso.

Para la selección única de cometas sin usar números de registro de Horizons, hay banderas adicionales que se pueden usar en la especificación COMMAND. Por ejemplo, si sabe que hay fragmentos para el cometa 141P y desea el cometa padre, puede agregar la bandera NOFRAG a la especificación COMMAND como `COMMAND='DES=141P;NOFRAG'`. De manera similar, si sabe que siempre desea la órbita con la época más reciente, puede agregar la bandera CAP a la especificación COMMAND como `COMMAND='DES=141P;CAP'`. En este ejemplo, combinar CAP y NOFRAG resultará en una coincidencia única para el cometa padre 141P como en `COMMAND='DES=141P;CAP;NOFRAG'`. Para fragmentos, la designación ya es única, por lo que solo necesitaría la bandera CAP como en `COMMAND='DES=141P-A;CAP'`.

Consulte la documentación de Horizons para más detalles.

## Generación de Archivos SPK de Cuerpos Pequeños

El archivo binario SPK está codificado en base-64 al retorno y, para la salida en formato texto, comienza después del texto del encabezado de la API con la cadena base-64 `REFGL1NQ...` en el siguiente ejemplo.

```
API VERSION: 0.2
API SOURCE: NASA/JPL Horizons API

SPK Binary Data Follows -- base64 encoded:

REFGL1NQSyACAAAABgAAAFNNQl9TUEtfRklMRSAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgID4AAAA+AAAAULQAAExUTC1JRUVFAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
...
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAA==
```

Para convertir el contenido codificado en base-64 a un archivo SPK binario utilizable, extraiga la porción codificada a un archivo y use un decodificador base-64. En la mayoría de sistemas Linux esto se hace con el comando `base64 --decode {extracted_file_content}`, donde `{extracted_file_content}` es el nombre del archivo que contiene el contenido codificado de la API.

### Ejemplos de Archivos de Entrada SPK de Horizons

#### Para Cuerpo Pequeño en la Base de Datos JPL

El siguiente archivo de entrada solicita un archivo SPK que abarca desde 2020-01-01 hasta 2030-12-31 (TDB) para el asteroide 1 Ceres.

```
!$$SOF
COMMAND='1;'
EPHEM_TYPE='S'
START_TIME='2020-01-01'
STOP_TIME='2030-12-31'
OBJ_DATA='NO'
```

#### Para Cuerpo Pequeño NO en la Base de Datos JPL

El siguiente archivo de entrada solicita un archivo SPK que abarca desde 2030-01-01 hasta 2031-01-01 (TDB) para el cuerpo pequeño especificado con elementos osculadores proporcionados por el usuario y parámetros no gravitacionales:

```
!$$SOF
 COMMAND     = ';'                 ! Input asteroid/comet NOT in JPL database
 MAKE_EPHEM  = 'YES'               ! Make an ephemeris
 EPHEM_TYPE  = 'S'                 ! Set ephemeris type to SPK
 OBJ_DATA    = 'NO'                ! Suppress object data-sheet
 START_TIME  = '2030-Jan-1'        ! Start time (TDB)
 STOP_TIME   = '2031-Jan-1'        ! Stop time (TDB)
!
 OBJECT = 'User Apophis'
 EPOCH  = '2459311.5'
 FRAME  = 'J2000'
 EC     = '0.1915350975906659'
 QR     = '0.7458351838564465'
 TP     = '2459424.5839352785'
 OM     = '203.9782743995174'
 W      = '126.6377455281965'
 IN     = '3.33973556589891'
 MA     =
 A      =
 N      =
 RAD    =

! Next two (H and G) for asteroids only
 H      =
 G      =

! Next group for comets only
 M1     =
 M2     =
 K1     =
 K2     =
 PHCOF  =
 DT     =

! Next group for asteroids or comets
 A1     = '3.869431020576E-13'
 A2     = '-2.898628963521E-14'
 A3     =
 R0     = '1.'
 ALN    = '1.'
 NM     = '2.'
 NN     = '5.093'
 NK     = '0.'
 AMRAT  =
!$$EOF
```

### Ejemplos de Línea de Comandos

Un ejemplo de línea de comandos de Linux para extraer el contenido del archivo SPK binario para el asteroide 1 Ceres de una salida exitosa en formato texto se muestra abajo. Sin embargo, se advierte que tal uso no detectará fácilmente errores devueltos por la API.

```bash
curl -s -F format=text -F input=@my_input_file.txt https://ssd.jpl.nasa.gov/api/horizons_file.api | awk '/REFGL1NQ/,0' | base64 --decode > object.bsp
```

De manera similar, para la salida en formato json, el contenido codificado SPK está contenido en el objeto spk como en el siguiente ejemplo:

```json
{
  "signature" : {
    "source" : "NASA/JPL Horizons API",
    "version" : "0.2"
  },
  "spk_file_id" : "2000001",
  "spk" : "REFGL1NQSyACAAAABgAAAFNNQl9TUEtfRklMRSAgICAgICAgICAgICAgICAgICAgICAgICAgICAg\nICAgICAgICAgICAgICAgICAgID4AAAA+AAA ... AAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAA==\n"
}
```

Extraiga el contenido del objeto JSON spk excluyendo las comillas circundantes y luego decodifique para producir el archivo SPK binario correspondiente. El `spk_file_id` se puede usar como el nombre base del archivo SPK (por ejemplo, 20000001.bsp en el ejemplo anterior).

## Scripts de Ejemplo

Los siguientes scripts esperan el archivo de entrada de Horizons como argumento en la línea de comandos. Suponiendo que ese archivo de entrada vea el script de ejemplo anterior solicita un archivo SPK para un objeto específico, el archivo SPK resultante se decodifica y se escribe a un archivo binario en el directorio de trabajo actual.

### Perl

```perl
use strict;
use LWP::UserAgent;
use JSON;
use MIME::Base64;

# Define API URL and SPK filename:
my $url = 'https://ssd.jpl.nasa.gov/api/horizons_file.api';
my $spk_filename = 'spk_file.bsp';

# Get the Horizons API input file from the command-line:
my $file = shift;
die unless ( defined $file and -e $file );

# Build and submit the API request and decode the JSON-response:
my $ua = LWP::UserAgent->new;
my $response = $ua->post($url,
  Content_Type=>'form-data',
  Content=>[ 'format'=>'json', 'input'=>[$file] ],
);
my $data = decode_json($response->content);

# If the request was valid...
if ( $response->code eq '200' ) {
  #
  # If the SPK file was generated, decode it and write it to the output file:
  if ( defined $data->{spk} ) {
    #
    # If a suggested SPK file basename was provided, use it:
    if ( defined $data->{spk_file_id} ) { $spk_filename = "$data->{spk_file_id}.bsp"; }
    open (my $fh, ">", $spk_filename) or die "unable to open $spk_filename: $!\n";
    #
    # Decode and write the binary SPK file content:
    print $fh decode_base64($data->{spk});
    close $fh;
    print "wrote SPK content to $spk_filename\n";
    exit;
  }
  #
  # Otherwise, the SPK file was not generated so output an error:
  print "ERROR: SPK file not generated\n";
  if ( defined $data->{result} ) { print $data->{result}; }
  else { print $response->content; }
  exit 1;
}

# If the request was invalid, extract error content and display it:
if ( $response->code eq '400' ) {
  print "ERROR in API call: HTTPS response: ", $response->status_line, "\n";
  if ( defined $data->{message} ) { print $data->{message}, "\n"; }
  else { print $response->content; }
  exit 1;
}

# Otherwise, some other error occurred:
print "ERROR in API call: HTTPS response: ", $response->status_line, "\n";
exit 1;
```

### Python

```python
import sys
import json
import base64
import requests

# Define API URL and SPK filename:
url = 'https://ssd.jpl.nasa.gov/api/horizons_file.api'
spk_filename = 'spk_file.bsp'

# Get the Horizons API input file from the command-line:
try:
  f = open(sys.argv[1])
except OSError as err:
  print("Unable to open input file '{0}': {1}".format(sys.argv[1], err))

# Build and submit the API request and decode the JSON-response:
response = requests.post(url, data={'format':'json'}, files={'input': f})
f.close()
try:
  data = json.loads(response.text)
except ValueError:
  print("Unable to decode JSON results")

# If the request was valid...
if (response.status_code == 200):
  #
  # If the SPK file was generated, decode it and write it to the output file:
  if "spk" in data:
    #
    # If a suggested SPK file basename was provided, use it:
    if "spk_file_id" in data:
      spk_filename = data["spk_file_id"] + ".bsp"
    try:
      f = open(spk_filename, "wb")
    except OSError as err:
      print("Unable to open SPK file '{0}': {1}".format(spk_filename, err))
    #
    # Decode and write the binary SPK file content:
    f.write(base64.b64decode(data["spk"]))
    f.close()
    print("wrote SPK content to {0}".format(spk_filename))
    sys.exit()
  #
  # Otherwise, the SPK file was not generated so output an error:
  print("ERROR: SPK file not generated")
  if "result" in data:
    print(data["result"])
  else:
    print(response.text)
  sys.exit(1)

# If the request was invalid, extract error content and display it:
if (response.status_code == 400):
  data = json.loads(response.text)
  if "message" in data:
    print("MESSAGE: {}".format(data["message"]))
  else:
    print(json.dumps(data, indent=2))

# Otherwise, some other error occurred:
print("response code: {0}".format(response.status_code))
sys.exit(2)
```

## Códigos de Respuesta HTTP

La mayoría de errores se devuelven a través de códigos de respuesta HTTP apropiados. Sin embargo, es posible enviar datos de entrada de Horizons (por ejemplo, un valor START_TIME incorrecto) que resulte en errores generados por Horizons. En tales casos, se devuelve un código de no error 200, por lo que el usuario es responsable de verificar el payload si desea detectar tales errores.

| Código HTTP | Descripción | Uso Típico |
|-------------|-------------|------------|
| 200 | OK | resultado exitoso normal |
| 400 | Bad Request | la solicitud contenía palabras clave y/o contenido inválido o usó un método de solicitud diferente a GET o POST (detalles devueltos en el payload JSON o texto) |
| 405 | Method Not Allowed | la solicitud usó un método incorrecto (ver la sección de Solicitud HTTP) |
| 500 | Internal Server Error | la base de datos no está disponible en el momento de la solicitud |
| 503 | Service Unavailable | el servidor actualmente no puede manejar la solicitud debido a una sobrecarga temporal o mantenimiento del servidor, que probablemente se aliviará después de algún retraso |