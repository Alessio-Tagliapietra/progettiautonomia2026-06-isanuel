""" 
context.py

Modulo per gestire gli strumenti comuni come ocr, tracker,... 
Questi vengono memorizzati in un dizionario gestito da un getter e un setter

funzione offerte:
- get_context
- set_context


"""
try:
    import server.config as config
except ImportError as e:
    print(f"Errore nel caricamento dei moduli in context.py: {e}")


context = {}


def get_context(key: str) -> any:
    try:
        return context[key]
    except KeyError:
        if config.VERBOSE:
            print(f"⚠️  Chiave del context non trovata: {key}")
        return None
    
def set_context(key: str, value: any) -> None:
    if key is None or value is None:
        if config.VERBOSE:
            print(f"⚠️  Chiave del context non valida: {key}")
        return
    
    if key in context:
        if config.VERBOSE:
            print(f"⚠️  Chiave del context già presente: {key}")
        return
    
    if config.VERBOSE:
        print(f"📦 Aggiunta chiave del context: {key}")
        
    context[key] = value