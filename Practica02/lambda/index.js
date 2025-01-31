/* *
 * This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK (v2).
 * Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
 * session persistence, api calls, and more.
 * */
const Alexa = require('ask-sdk-core');
const https = require('https');

let pokemon_Info = {};
let contador_pistas = 0;

// SALUDOS Y DESPEDIDAS
const saludos = ['Hola, ¿estás listo para adivinar Pokémons?', 'Bienvenido al juego de adivinanzas de Pokémon. ¿Estás listo?', 'Hola, vamos a empezar a adivinar Pokémons.'];
const despedidas = ['Hasta luego, espero que te hayas divertido.', 'Adiós, ¡gracias por jugar!', 'Chao, ¡vuelve pronto!', 'Chao pescao!'];

// INICIO -> AITOR
const LaunchRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'LaunchRequest';
    },
    async handle(handlerInput) {
        let speakOutput = saludos[Math.floor(Math.random() * saludos.length)];
        pokemon_Info = {};
        contador_pistas = 0;
        await busquedaIntentHandler();
        
        speakOutput += ' ';
        speakOutput += 'Pokemon elegido, intenta adivinar, si necesitas ayuda, di "ayuda"';
        

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// OBTENER GEN -> AITOR
function obtenerGenIndentHandler(pokemonID) {
    if(pokemonID <= 151) return 1;
    if(pokemonID <= 251) return 2;
    if(pokemonID <= 386) return 3;
    if(pokemonID <= 493) return 4;
    if(pokemonID <= 649) return 5;
    if(pokemonID <= 721) return 6;
    if(pokemonID <= 809) return 7;
    if(pokemonID <= 905) return 8;
    return 9;
}

// BUSQUEDA DEL POKEMON -> AITOR
async function busquedaIntentHandler() {
    try {
            // Creo la url aleatoria
            const pokemon_random = Math.floor(Math.random() * 1017) + 1;
            const pokemon_url = 'https://pokeapi.co/api/v2/pokemon/' + pokemon_random;
            const espera_respuesta = await makeHttpRequest(pokemon_url);
            let nombre_cambiado = espera_respuesta.name.replace(/-/g, ' ');
            
            pokemon_Info = {
                nombre: nombre_cambiado,
                generacion: obtenerGenIndentHandler(pokemon_random),
                tipo1: espera_respuesta.types[0].type.name,
                tipo2: (espera_respuesta.types.length > 1) ? (espera_respuesta.types[1].type.name) : 'unico',
            };

            console.log(pokemon_Info);
            
        }   catch (error) {
                console.error('Error al acceder a la api');
            }
}

// ADIVINAR POKEMON -> TOMÁS
const AdivinaPokemonIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AdivinaPokemonIntent';
    },
    handle(handlerInput) {
        const userGuess = handlerInput.requestEnvelope.request.intent.slots.pokemonName.value;
        let speakOutput = '';

        if (userGuess.toLowerCase() === pokemon_Info.nombre.toLowerCase()) {
            speakOutput = `¡Correcto! El Pokémon es ${pokemon_Info.nombre}. ¡Felicidades! ¿Quieres jugar de nuevo?`;
            // Reinicia el juego o termina la sesión aquí
        } else {
            speakOutput = `No, no es ${userGuess}. Intenta de nuevo o pide una pista.`;
        }

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt('Intenta adivinar el Pokémon o pide una pista.')
            .getResponse();
    }
};

// PISTA INTENT HANDLER -> AITOR
const PistaIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'pista_intent';
    },
    handle(handlerInput) {
        let speakOutput = '';

        if(contador_pistas === 0) {
            speakOutput = `La primera pista que te puedo dar es que es de la generación ${pokemon_Info.generacion}.`;
            contador_pistas++;
        } else if(contador_pistas === 1) {
            speakOutput = `La segunda pista es que su primer tipo es ${pokemon_Info.tipo1}.`;
            contador_pistas++;
        } else if(contador_pistas === 2) {
            if(pokemon_Info.tipo2 === 'unico') {
                speakOutput = 'La última pista es que es de tipo único.';
            } else {
                speakOutput = `La última pista es que su segundo tipo es ${pokemon_Info.tipo2}.`;
            }
            contador_pistas++;
        } else {
            speakOutput = `Ya has usado todas tus pistas. No puedes usar más. `;
            speakOutput += `Para refrescarte la memoria: `;
            speakOutput += `La primera fue sobre su generación: ${pokemon_Info.generacion}. `;
            speakOutput += `La segunda sobre su primer tipo: ${pokemon_Info.tipo1}. `;
            if(pokemon_Info.tipo2 !== 'unico') {
                speakOutput += `La tercera fue sobre su segundo tipo: ${pokemon_Info.tipo2}.`;
            } else {
                speakOutput += `La tecera fue sobre su tipo: único.`;
            }
        }

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt('¿Quieres intentar adivinar el Pokémon o necesitas más ayuda?')
            .getResponse();
    }
};

// FUNCION REINICIAR JUEGO -> TOMÁS
async function reiniciarJuego() {
    pokemon_Info = {};
    contador_pistas = 0;

    await busquedaIntentHandler();
}

// ReiniciarJuegoIntentHandler -> TOMÁS
const ReiniciarJuegoIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'ReiniciarJuegoIntent';
    },
    async handle(handlerInput) {
        await reiniciarJuego();
        const speakOutput = 'El juego ha sido reiniciado. Intenta adivinar el nuevo Pokémon.';
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt('Intenta adivinar el Pokémon o pide una pista.')
            .getResponse();
    }
};

// FinJuegoIntentHandler -> TOMÁS
const FinJuegoIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'FinJuegoIntent';
    },
    handle(handlerInput) {
        const speakOutput = despedidas[Math.floor(Math.random() * despedidas.length)];
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .getResponse();
    }
};

// HelpIntentHandler -> AITOR
const HelpIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.HelpIntent';
    },
    handle(handlerInput) {
        const speakOutput = 'Dime "dame una pista" para obtener una pista sobre el Pokémon, o intenta adivinar diciendo "creo que es [nombre del Pokémon]".'

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// CancelAndStopIntentHandler -> TOMÁS
const CancelAndStopIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && (Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.CancelIntent'
                || Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.StopIntent');
    },
    handle(handlerInput) {
        const speakOutput = despedidas[Math.floor(Math.random() * despedidas.length)];

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .getResponse();
    }
};
/* *
 * FallbackIntent triggers when a customer says something that doesn’t map to any intents in your skill
 * It must also be defined in the language model (if the locale supports it)
 * This handler can be safely added but will be ingnored in locales that do not support it yet 
 * */
const FallbackIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.FallbackIntent';
    },
    handle(handlerInput) {
        const speakOutput = 'Lo siento, no sé nada sobre eso. Porfavor, intentalo de nuevo.';

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};
/* *
 * SessionEndedRequest notifies that a session was ended. This handler will be triggered when a currently open 
 * session is closed for one of the following reasons: 1) The user says "exit" or "quit". 2) The user does not 
 * respond or says something that does not match an intent defined in your voice model. 3) An error occurs 
 * */
const SessionEndedRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'SessionEndedRequest';
    },
    handle(handlerInput) {
        console.log(`~~~~ Sesión acabada: ${JSON.stringify(handlerInput.requestEnvelope)}`);
        // Any cleanup logic goes here.
        return handlerInput.responseBuilder.getResponse(); // notice we send an empty response
    }
};
/* *
 * The intent reflector is used for interaction model testing and debugging.
 * It will simply repeat the intent the user said. You can create custom handlers for your intents 
 * by defining them above, then also adding them to the request handler chain below 
 * */
const IntentReflectorHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest';
    },
    handle(handlerInput) {
        const intentName = Alexa.getIntentName(handlerInput.requestEnvelope);
        const speakOutput = `Acabas de desencadenar ${intentName}`;

        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};
/**
 * Generic error handling to capture any syntax or routing errors. If you receive an error
 * stating the request handler chain is not found, you have not implemented a handler for
 * the intent being invoked or included it in the skill builder below 
 * */
const ErrorHandler = {
    canHandle() {
        return true;
    },
    handle(handlerInput, error) {
        const speakOutput = 'Lo siento, tengo problemas para hacer lo que me preguntaste. Porfavor, intentalo de nuevo.';
        console.log(`~~~~ Error sujeto a: ${JSON.stringify(error)}`);

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

                                                                                // Función para realizar solicitudes HTTP
function makeHttpRequest(url) {
    return new Promise((resolve, reject) => {
        https.get(url, (response) => {
            let data = '';

            // Recibiendo datos
            response.on('data', (chunk) => {
                data += chunk;
            });

            // Al finalizar la respuesta
            response.on('end', () => {
                const jsonData = JSON.parse(data);
                resolve(jsonData);
            });
        }).on('error', (error) => {
            reject(error);
        });
    });
}

/**
 * This handler acts as the entry point for your skill, routing all request and response
 * payloads to the handlers above. Make sure any new handlers or interceptors you've
 * defined are included below. The order matters - they're processed top to bottom 
 * */
exports.handler = Alexa.SkillBuilders.custom()
    .addRequestHandlers(
        LaunchRequestHandler,
        AdivinaPokemonIntentHandler,
        PistaIntentHandler,
        ReiniciarJuegoIntentHandler,
        FinJuegoIntentHandler,
        HelpIntentHandler,
        CancelAndStopIntentHandler,
        FallbackIntentHandler,
        SessionEndedRequestHandler,
        IntentReflectorHandler
        )
    .addErrorHandlers(ErrorHandler)
    .withCustomUserAgent('sample/hello-world/v1.2')
    .lambda();