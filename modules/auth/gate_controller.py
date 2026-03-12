"""
gate_controller.py
Stub per il controllo fisico del cancello.
Sostituire il corpo di open_gate() e close_gate() con la logica reale.
"""
import modules.auth.config as config


def open_gate(gate_id: str, reason: str = ""):
    if config.VERBOSE:
        print(f"   🚧 [STUB] Cancello {gate_id} → APERTO | motivo: {reason}")
    # TODO: GPIO / HTTP / seriale


def deny_gate(gate_id: str, reason: str = ""):
    if config.VERBOSE:
        print(f"   🔒 [STUB] Cancello {gate_id} → NEGATO | motivo: {reason}")
    # TODO: segnale acustico / led rosso / ecc.