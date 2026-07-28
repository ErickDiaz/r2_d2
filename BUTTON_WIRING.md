# Cablear el botón/LED del AIY Voice Bonnet directo al GPIO

El botón del kit (con su LED) venía conectado al HAT/Bonnet de Google, cuyo
driver de audio/LED/botón no funciona en Raspberry Pi OS moderno (ver
README, sección "Por qué no usamos el HAT"). Pero el botón y su LED **no
dependen de ese driver** — están cableados directo a dos pines del header
de 40 pines del Pi:

- **Botón** → `GPIO23` (pin físico **16**)
- **LED** → `GPIO25` (pin físico **22**)

Fuente: [`docs/voice.md`](https://github.com/google/aiyprojects-raspbian/blob/aiyprojects/docs/voice.md)
del repo oficial de Google, y el código de `aiy.board.Button`/`Led`, que
usan `RPi.GPIO` puro sobre esos dos pines (sin I2C, sin el microcontrolador
del HAT).

**Importante**: el LED del botón en la Voice Bonnet es en realidad un LED
**RGB** (varios colores), pero el pin directo `GPIO25` solo controla **un
canal simple** — es el modo de compatibilidad que usaba el kit anterior
(Voice HAT v1). O sea, vas a poder encender/apagar/hacer parpadear el LED,
pero probablemente solo en un color (no vamos a poder elegir el color sin
el driver I2C roto). Para este proyecto alcanza y sobra.

## Qué vas a necesitar

- Multímetro (con modo de continuidad y modo de diodo/`diode test`) — **no
  adivines los colores de los cables**, no hay un código de colores
  documentado de forma confiable para este cable.
- Cables jumper (macho-macho o macho-hembra según cómo termine el cable del
  botón).
- Una resistencia de **330Ω a 1kΩ** (si el botón no trae ya una resistencia
  soldada cerca del LED — revisá con lupa si ves un componente chico ahí).
- Opcional: una protoboard chica para armar la resistencia + cables con
  comodidad.

## Paso 1: identificar los cables del switch (botón)

El botón tiene un conector con varios cables (probablemente 4). Dos de
ellos son el switch (el "click" mecánico), y los otros son el LED.

1. Poné el multímetro en modo **continuidad** (el que hace beep).
2. Probá pares de cables tocando las dos puntas, **sin apretar el botón**:
   no debería hacer beep en el par correcto.
3. Mantené las puntas puestas y **apretá el botón**: el par correcto va a
   hacer beep solo mientras está apretado.
4. Ese par son los cables del **switch**. Marcalos (con cinta o etiqueta).

## Paso 2: identificar los cables del LED

1. Poné el multímetro en modo **diodo** (símbolo de diodo, suele estar en
   la misma perilla que continuidad).
2. Probá pares de cables que **no** sean los del switch:
   - Un LED real solo conduce en un sentido. Vas a ver un voltaje (~1.8-3V)
     en un sentido, y "OL"/nada en el sentido contrario.
   - Si el LED es RGB puede tener más de 2 cables útiles (uno común +
     varios de color). Con el pin directo `GPIO25` alcanza con encontrar
     **un solo par** que prenda el LED (mínimo, aunque sea un color).
3. Cuando encuentres un par que prenda el LED (se ve tenue con el
   multímetro en modo diodo, a veces ni se nota a simple vista — normal),
   anotá cuál punta es la que hizo prender (esa es el ánodo/`+`) y cuál no
   (cátodo/`-` o común).

## Paso 3: conectar al Pi

Con la Pi **apagada**:

| Cable | Va a |
|---|---|
| Switch, cable 1 | `GPIO23` — pin físico **16** |
| Switch, cable 2 | Cualquier `GND` — pin físico **14** (está justo al lado) |
| LED, ánodo (`+`) | Resistencia de 330Ω-1kΩ → `GPIO25` — pin físico **22** |
| LED, cátodo (`-`)/común | Cualquier `GND` — pin físico **20** (está justo al lado) |

Numeración de pines físicos del header de 40 pines (mirando la Pi con el
puerto USB hacia abajo, pin 1 arriba a la izquierda):

```
        15  16 <-- GPIO23 (boton)
             ...
        13  14 <-- GND
        21  22 <-- GPIO25 (LED)
        19  20 <-- GND
```

Si el conector del botón termina en un JST que no entra en el header de la
Pi, cortá el conector y soldá/usá jumpers macho-macho directo a los cables
pelados, o usá un adaptador JST-a-jumper.

## Paso 4: probar antes de confiar en todo el pipeline

Con la Pi prendida y todo conectado:

```bash
cd ~/r2_d2
venv/bin/python3 test_button_led.py
```

Apretá el botón — debería imprimir "Boton presionado" y el LED debería
prenderse mientras lo mantenés apretado. `Ctrl+C` para salir.

Si el LED no prende pero el botón sí se detecta en la consola: revisá la
polaridad del LED (cambiá cuál cable va a `GPIO25` y cuál a `GND`) o que la
resistencia esté bien conectada.

Si nada funciona: revisá que identificaste bien los cables en el Paso 1/2
— es fácil confundir switch con LED si el multímetro no hace buen contacto.

## Una vez que funciona

`voice_assistant.py` ya usa `led_status.LedStatus` (GPIO25) y
`push_to_talk.PushToTalkButton` (GPIO23) automáticamente — no hace falta
tocar código. El botón funciona como alternativa a decir la wake word: al
apretarlo, empieza a escuchar el comando igual que si hubieras dicho
"arturito".
