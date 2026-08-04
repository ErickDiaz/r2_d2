# Cablear el botón/LED RGB directo al GPIO (Raspberry Pi o Jetson Nano)

El botón del kit (con su LED) venía conectado al HAT/Bonnet de Google, cuyo
driver de audio/LED/botón no funciona en Raspberry Pi OS moderno (ver
README, sección "Por qué no usamos el HAT"). Pero el botón y su LED **no
dependen de ese driver** — van directo a pines del header de 40 pines.

Esto vale igual para Raspberry Pi y para Jetson Nano: el header de 40 pines
(J41 en la Jetson) tiene el **mismo layout mecánico** en ambas placas, y la
numeración por posición física de pin coincide. Lo único que cambia entre
placas es el código que lee/escribe esos pines (`gpiozero` en la Pi vs.
`Jetson.GPIO` en la Jetson — ver `led_status.py`/`push_to_talk.py`), no el
cableado físico.

**Confirmado en hardware real**: es un LED **RGB de ánodo común**, con 4
cables — uno común (`+`) y tres cátodos individuales, uno por color.
Conectando cualquiera de los 3 cátodos a tierra con el común alimentado,
prende ese color. El botón (switch) es aparte, 2 cables más.

| Función | Pin físico | BCM (solo Pi) |
|---|---|---|
| Botón (switch) | **16** | GPIO23 |
| LED, común (`+`) | **22** | GPIO25 |
| LED, rojo | **15** | GPIO22 |
| LED, verde | **13** | GPIO27 |
| LED, azul | **18** | GPIO24 |

Fuente del pinout del botón/LED común: [`docs/voice.md`](https://github.com/google/aiyprojects-raspbian/blob/aiyprojects/docs/voice.md)
del repo oficial de Google. Los pines de rojo/verde/azul se identificaron
a mano en este mismo hardware (ver "Identificar los canales de color" más
abajo) — no hay un código de colores documentado para este cable.

**Nota eléctrica para Jetson**: el GPIO de la Jetson entrega menos corriente
que el de la Pi — si algún color queda muy tenue, puede necesitar una
resistencia más chica (probá 330Ω) o, si sigue muy débil, un transistor NPN
chico como driver en vez de conectar el LED directo al pin.

## Qué vas a necesitar

- Multímetro (con modo de continuidad y modo de diodo/`diode test`) — **no
  adivines los colores de los cables**.
- Cables jumper (macho-macho o macho-hembra según cómo termine el cable del
  botón).
- Una resistencia de **330Ω a 1kΩ** por cada cable de color (si el botón no
  trae ya resistencias soldadas — revisá con lupa).
- Opcional: una protoboard chica para armar las resistencias + cables con
  comodidad.

## Paso 1: identificar los cables del switch (botón)

El botón tiene un conector con varios cables (6 en total: 2 del switch + 4
del LED RGB).

1. Poné el multímetro en modo **continuidad** (el que hace beep).
2. Probá pares de cables tocando las dos puntas, **sin apretar el botón**:
   no debería hacer beep en el par correcto.
3. Mantené las puntas puestas y **apretá el botón**: el par correcto va a
   hacer beep solo mientras está apretado.
4. Ese par son los cables del **switch**. Marcalos (con cinta o etiqueta).

## Paso 2: identificar el cable común del LED

1. Poné el multímetro en modo **diodo** (símbolo de diodo, suele estar en
   la misma perilla que continuidad).
2. De los 4 cables que quedan (no son del switch), probá pares: un LED real
   solo conduce en un sentido — vas a ver un voltaje (~1.8-3V) en un
   sentido, y "OL"/nada en el contrario.
3. El cable que aparece como `+` (ánodo) en **los 3 pares que prenden algo**
   es el **común**. Los otros 3 son los cátodos de rojo/verde/azul (todavía
   no sabés cuál es cuál — eso se identifica ya conectado, en el Paso 4).

## Paso 3: conectar al header de 40 pines

Con la placa **apagada**:

| Cable | Va a |
|---|---|
| Switch, cable 1 | Pin físico **16** |
| Switch, cable 2 | Cualquier `GND` — pin físico **14** (está justo al lado) |
| LED, común (`+`) | Pin físico **22** (sin resistencia — es la alimentación compartida) |
| LED, cátodo 1 | Resistencia de 330Ω-1kΩ → pin físico **15** |
| LED, cátodo 2 | Resistencia de 330Ω-1kΩ → pin físico **13** |
| LED, cátodo 3 | Resistencia de 330Ω-1kΩ → pin físico **18** |

No importa el orden en que conectes los 3 cátodos a los pines 15/13/18 —
eso se resuelve en software una vez que sabés qué color prende cada uno
(Paso 4).

Numeración de pines físicos del header de 40 pines (mirando la placa con el
puerto USB hacia abajo, pin 1 arriba a la izquierda) — igual en Pi y Jetson:

```
        13  14 <-- GND
        15  16 <-- boton
        17  18
             ...
        21  22 <-- LED comun
```

Si el conector del botón termina en un JST que no entra en el header,
cortá el conector y soldá/usá jumpers macho-macho directo a los cables
pelados, o usá un adaptador JST-a-jumper.

## Paso 4: identificar los canales de color

Con todo conectado como en el Paso 3 (asumiendo que cableaste cátodo1→15,
cátodo2→13, cátodo3→18 — si lo hiciste distinto, `led_status.py` ya asume
**rojo=pin15, verde=pin13, azul=pin18**, así que cablealo en ese orden para
no tener que tocar código):

```bash
cd ~/r2_d2
venv/bin/python3 test_button_led.py
```

Esto ya usa el mapeo final (`led_status.LedStatus`): apretar el botón
muestra rojo fijo, soltarlo lo apaga. Si los colores salen cambiados
(p. ej. lo que debería ser rojo prende verde), es porque cableaste los
cátodos en otro orden — o intercambiá los cables físicamente, o ajustá las
constantes `_RED_PIN`/`_GREEN_PIN`/`_BLUE_PIN` en `led_status.py` para que
coincidan con cómo quedó tu cableado real.

Si el botón no se detecta o el LED no prende: revisá que el común (pin 22)
y el `GND` del switch tengan buen contacto — ambos circuitos comparten
tierra, así que una conexión floja ahí puede hacer que ninguno de los dos
responda aunque el cableado se vea bien a simple vista.

## Una vez que funciona

`voice_assistant.py` ya usa `led_status.LedStatus` y
`push_to_talk.PushToTalkButton` automáticamente — no hace falta tocar
código. El botón funciona como alternativa a decir la wake word: al
apretarlo, empieza a escuchar el comando igual que si hubieras dicho
"arturito". El LED muestra **rojo fijo** mientras escucha, **rojo/azul al
azar** mientras procesa el comando (el look clásico de R2-D2), y se apaga
cuando queda en espera.
