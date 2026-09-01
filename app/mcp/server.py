"""
MCP Server do CompanyMind AI.

Expõe as ferramentas de leitura da base de conhecimento corporativa via
Model Context Protocol, permitindo que qualquer cliente compatível (Claude
Desktop, outros agentes, etc.) descubra e utilize essas ferramentas sem
precisar conhecer a API REST internamente.

Todas as tools aqui são estritamente somente-leitura, na mesma lógica de
permissões usada pelo restante da plataforma.

Executar com:
    python -m app.mcp.server
"""

from mcp.server.fastmcp import FastMCP

from app.mcp import tools as company_tools

mcp = FastMCP("companymind-ai")


@mcp.tool()
def search_company_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """Busca semântica na base de conhecimento geral da empresa."""
    return company_tools.search_company_knowledge(query, top_k)


@mcp.tool()
def get_company_policy(topic: str) -> list[dict]:
    """Recupera trechos de políticas internas relacionadas a um tópico (ex: 'ferias')."""
    return company_tools.get_company_policy(topic)


@mcp.tool()
def get_product_information(product_query: str) -> list[dict]:
    """Recupera informações de produtos da empresa."""
    return company_tools.get_product_information(product_query)


@mcp.tool()
def list_company_departments() -> list[str]:
    """Lista os departamentos que possuem documentos cadastrados."""
    return company_tools.list_company_departments()


@mcp.tool()
def search_faq(question: str) -> list[dict]:
    """Busca respostas nas perguntas frequentes da empresa."""
    return company_tools.search_faq(question)


if __name__ == "__main__":
    mcp.run(transport="stdio")
