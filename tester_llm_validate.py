import requests
import time
import re
import os

BACKEND_URL = "http://localhost:5001"
USERNAME = "pippo"  # Sostituisci con utente valido
PASSWORD = "1234"  # Sostituisci con password valida

def login(username, password):
    url = f"{BACKEND_URL}/api/auth/login"
    resp = requests.post(url, json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_fake_answers(limit=100):
    risposte = []
    with open("risposte_inventate.txt", "r", encoding="utf-8") as f:
        for i, riga in enumerate(f):
            if i >= limit:
                break
            risposte.append({"id": i+1, "text": riga.strip()})
    return risposte

def get_human_answers(token, limit=100):
    url = f"{BACKEND_URL}/api/answers/question/1"  # Prende tutte le risposte della domanda 1
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    answers = resp.json()
    # Filtra solo risposte umane
    return [a for a in answers if not a["is_llm_answer"]][:limit]

def call_llm_validate(answer_id, token):
    url = f"{BACKEND_URL}/api/validate/llm-validate"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(url, params={"answer_id": answer_id}, headers=headers)
    resp.raise_for_status()
    return resp.json()

def call_llm_validate_text(answer_text, token):
    url = f"{BACKEND_URL}/api/validate/llm-validate-text"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(url, json={"answer_text": answer_text}, headers=headers)
    resp.raise_for_status()
    return resp.json()

def check_llm_format(validation):
    # Controlla che i campi siano presenti e nel formato corretto
    required_fields = ["id", "answer_id", "score", "is_correct", "feedback", "created_at"]
    for field in required_fields:
        if field not in validation:
            return False, f"Campo mancante: {field}"
    # Score deve essere float tra 0 e 10
    if not (0 <= float(validation["score"]) <= 10):
        return False, f"Score fuori range: {validation['score']}"
    # Feedback deve essere stringa non vuota
    if not isinstance(validation["feedback"], str) or not validation["feedback"]:
        return False, "Feedback vuoto o non stringa"
    return True, ""

def main():
    print("Login...")
    token = login(USERNAME, PASSWORD)
    print("Carico risposte inventate...")
    answers = get_fake_answers(limit=100)
    if not answers:
        print("Nessuna risposta inventata trovata.")
        return

    errors = []
    for i, answer in enumerate(answers):
        print(f"Test {i+1}/100 - answer_id={answer['id']}")
        try:
            result = call_llm_validate_text(answer["text"], token)
            if not isinstance(result, list) or len(result) != 2:
                errors.append((answer["id"], "Risposta non è una lista di 2 elementi"))
                continue
            for idx, validation in enumerate(result):
                ok, msg = check_llm_format(validation)
                if not ok:
                    errors.append((answer["id"], f"Errore formato nella validazione {idx}: {msg}"))
        except Exception as e:
            errors.append((answer["id"], f"Eccezione: {str(e)}"))
        time.sleep(0.5)  # Per non sovraccaricare il backend

    print("\n--- REPORT ---")
    if not errors:
        print("Tutti i test superati!")
    else:
        print(f"Errori trovati in {len(errors)} chiamate:")
        for eid, msg in errors:
            print(f"- answer_id={eid}: {msg}")

if __name__ == "__main__":
    main()