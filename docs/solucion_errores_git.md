SOLUCIÓN ERRORES:

Problemas con merge/pull  requests - Conectar visual studio code con nuevo repositorio remoto en github:

Primero, chequear la conexión remota acutal:

git remote –v

Se debería algo similar a:
origin  https://github.com/personal-account/old-repository.git (fetch)
origin  https://github.com/personal-account/old-repository.git (push)

Copiar la nueva conexión http del nuevo repositorio github remoto. Luego ejecutar el siguiente comando in la terminal bahs del the VS code:
git remote set-url origin https://github.com/team-account/new-repository.git

Verificar la nueva conexión:
git remote –v

Se debería ver algo como:
origin  https://github.com/team-account/new-repository.git (fetch)
origin  https://github.com/team-account/new-repository.git (push)

Si al hacer push aparece un error, por ejemplo:
git push origin developer
remote: Permission to henrydatasciencegrupo/Outfit_Analytics_DataScience_Proyecto_Final.git denied to ignaciosironi.
fatal: unable to access 'https://github.com/henrydatasciencegrupo/Outfit_Analytics_DataScience_Proyecto_Final.git/': The requested URL returned error: 403

Es posible que se esté autenticado con otra cuenta de github. Se debe desconectar de la actual cuenta y conectar la nueva cuenta o invitar a esa cuenta como colaborador:

Ir a la cuenta github principal y añadir a otros como colaboradores:

Ingresar al repositorio el cual será compartido -> luego sobre el menú superior seleccionar "settings" -> sobre la barra izquierda, debajo de la sección "accesos" seleccionar "colaborador" -> cliquear "add new people" y añadir el mail o github username de la otra cuenta a la que será enviado la invitación como colaborador.

Luego ir a la otra cuenta de github e ir a notificaciones y aceptar la invitación.

PROBLEMA AL HACER MERGE REQUESTS AL CAMBIAR REPOSITORIO REMOTO:

Cuando los archivos de vs code están conectados con cierto github repositorio y luego se necesita conectarse a otro repositorio remoto, tal vez suceda un conflicto al hacer push al remoto ya que no aparecerá el merge requests in the nuevo repositorio remoto github. Esto es un problema de "historias entre los ramas". Las ramas tendrán diferentes historiales de commits y entonces no estarán conectadas. Esto se debe a que al trabajo con el primer repositorio remoto, posiblemente se hayan hecho algunos commits. Luego se cambió a otro repositorio y fueron hecho nuevos commits, entonces se produjo una desconeccción entre las ramas al tener distintos commits de distintos repositorios.
Para solucionar el conflicto de historio entre ramas, se tiene que correr algunos comandos git en la RAMA DE TRABAJO LOCAL (NO LA MAIN LOCAL). Localmente, habrá dos ramas, en la que uno trabajo y la main (en la cual se descargarán los cambios desde remoto). Lo que se debe hacer es sincronizar el contenido remoto con el local y unir con un "merge" el contenido de las ramas. Eo comando git para correr sobre una terminal bash es:

“git branch backup-nombreramabackup nombre-ramalocal”

Se crea un backup de la historia del commit de la rama local de trabajo (no main)

“git fetch origin” -> se descarga la ultima actualizacion del commit remoto sin modificar la rama actual

Se podría ejecutar git fetch origin desde main o la rama de trabajo, ya que no modifica los archivos de la rama en la que se está posicionado.

“git merge origin/main --allow-unrelated-histories” -> este comando debe ser ejecutado en la rama de trabajo local

El comando le dice a git to unir la historia remota main con la rama local de tarbajo

Si hay conflictos, git parará para preguntar qué hacer y aparecerá en la parte superior diferentes opciones:

•  Accept Current Change
•  Accept Incoming Change
•  Accept Both Changes
•  Compare Changes

Este paso es importante: Si se quiere mantener el contenido local, se debe hacer click en “accept current change”. Si se quiere reemplazar el contenido local opr el remoto, hacer click en “accept incoming change”. Guardar los cambios.

Así, el contenido local y remoto están sincronizados con las mismas historias y los commits y merge requests deberían trabajar correctamente y se debería poder relizar la suba de archivos correctamente.
Si al hacer push, no aparece automaticamente en la pantalla principal del repositorio, se lo puedo realizar de forma manual.

CÓMO CREAR MERGE REQUESTS DE FORMA MANUAL:

Ir al repositorio. Seleccionar sobre el menú superior la optión "pull request". Seleccionar "new pull request". Sobre la izquierda habra dos botones. En el que dice "base" se debe seleccioanr "main", donde los cambios serán cargados. En el de la derecha que dice "compare" seleccionar la rama del cual se quiere pasar la información que está viniendo localmente. Luego seleccionar "create merge request". En la siguiente pantalla seguir los pasos de forma tradicional al hacer merge requests.



