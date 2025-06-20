Indirizzo: ip:5000/api

1. GENERAZIONE DOMANDA DA TEMA
/generate-question

Obbligatori:
theme: TextString (nome del tema culturale)
Facoltativi:
Nessuno
Aggiuntivi:
Nessuno

Returns:
Json:
text: TextString (domanda generata)

Pre:
Riceve un tema culturale valido in formato testo
Post:
Genera una domanda sulla cultura italiana relativa al tema specificato

2. GENERAZIONE TAG DA DOMANDA
/generate-tag

Obbligatori:
question: TextString
Facoltativi:
Nessuno
Aggiuntivi:
Nessuno

Returns:
Json:
tag: TextString

Pre:
Riceve una domanda valida
Post:
Genera un tag riassuntivo di massimo 3 parole che rappresenta l'argomento principale della domanda

3. VALIDAZIONE RISPOSTA
/validate-answer

Obbligatori:
answer: TextString (risposta da validare)
question: TextString (domanda associata)
Facoltativi:
theme: TextString (contesto culturale, default: "generale")
Aggiuntivi:
Nessuno

Returns:
Json:
ValidationResponse contenente:
- score: Float (0-10, valutazione numerica della risposta)
- is_correct: Boolean (indica se la risposta è considerata corretta)
- feedback: TextString (commento dettagliato sulla valutazione)

Pre:
Riceve una risposta da validare e la domanda associata
Post:
Fornisce una valutazione dettagliata della risposta in relazione alla domanda posta

Note Tecniche:
- Tutti gli endpoint devono rispondere entro 30 secondi
- Le risposte devono essere in italiano
- I tag generati devono essere di massimo 3 parole
- Gli score di validazione devono essere compresi tra 0 e 10
- Il feedback deve essere dettagliato ma conciso (max 200 caratteri)
