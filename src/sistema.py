"""Ponto de entrada do Primeiro Passo.

    python src/sistema.py              abre o aplicativo
    python src/sistema.py --verificar  confere base, banco e IA sem abrir janela
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # garante os imports de src/


def verificar() -> int:
    from interface.contexto import Contexto
    ctx = Contexto.criar()
    resumo = ctx.resumo()
    est = resumo["conhecimentos"]
    print(f"Base: {est['total']} assuntos, {est['categorias']} categorias "
          f"({est['verificado']} verificados, {est['pendente_validacao']} pendentes)")
    print(f"Oportunidades: {resumo['oportunidades']} | Modelos de checklist: {resumo['checklists_modelo']}")
    print(f"IA externa configurada: {'sim' if resumo['ia_configurada'] else 'não (o app funciona sem ela)'}")
    for erro in resumo["erros_na_base"]:
        print(f"AVISO na base: {erro}")
    return 0


def main() -> int:
    if "--verificar" in sys.argv:
        return verificar()
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        print("CustomTkinter não está instalado. Rode: pip install -r requirements.txt", file=sys.stderr)
        return 1
    from interface.contexto import Contexto
    from interface.principal import Aplicativo
    try:
        ctx = Contexto.criar()
    except (OSError, ValueError) as erro:
        print(f"Não foi possível iniciar: {erro}", file=sys.stderr)
        return 1
    for erro in ctx.base.erros:  # registros ignorados na base: avisa no terminal
        print(f"AVISO na base: {erro}", file=sys.stderr)
    Aplicativo(ctx).mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
