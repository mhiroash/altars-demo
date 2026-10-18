"""Isolamento da BD para os testes do ciclo completo.
Os testes corriam contra a BD real (/workspace/altars/pipeline/data/altars.db),
que ja tem dados de recolhas anteriores — isso tornava os asserts nao
deterministicos (ex.: contagens que esperavam 1 item encontravam 0 ou N).
Aqui, cada sessao de testes copia a BD real para uma pasta temporaria e
aponta ALTARS_DB para la, ANTES de o modulo de teste a ler.
"""
import os
import shutil
import tempfile
from pathlib import Path
_REAL = Path("/workspace/altars/pipeline/data/altars.db")
def pytest_configure(config):
    if os.environ.get("ALTARS_DB"):
        return  # ja foi definido explicitamente
    tmpdir = Path(tempfile.mkdtemp(prefix="altars-test-db-"))
    dst = tmpdir / "altars.db"
    if _REAL.exists():
        shutil.copy(_REAL, dst)
    else:
        dst.touch()
    os.environ["ALTARS_DB"] = str(dst)