#!/bin/sh

# Avvia Ollama in background
ollama serve &

# Attendi che Ollama sia pronto
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "In attesa che Ollama sia pronto..."
    sleep 1
done

# Scarica il modello gemma3:1b
echo "Scaricamento del modello gemma3:1b..."
ollama pull gemma3:1b

# Mantieni il container in esecuzione
tail -f /dev/null