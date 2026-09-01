"""
Script de seed: popula o Supabase com documentos corporativos fictícios,
gerando embeddings reais para cada chunk. Requer .env configurado.

Uso:
    python scripts/seed_data.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chunking import chunk_text
from app.services.embeddings import generate_embeddings_batch
from app.repositories.documents_repository import insert_document, insert_chunks

SEED_DOCUMENTS = [
    {
        "title": "Política de Férias",
        "category": "policy",
        "department": "RH",
        "content": (
            "Todo colaborador tem direito a 30 dias corridos de férias por ano trabalhado, "
            "conforme a legislação vigente. As férias devem ser solicitadas com no mínimo 30 dias "
            "de antecedência através do sistema interno de RH. É permitido o fracionamento em até "
            "três períodos, sendo que um deles não pode ser inferior a 14 dias corridos e os demais "
            "não podem ser inferiores a 5 dias corridos cada. O pagamento do adicional de 1/3 "
            "constitucional é feito até dois dias antes do início do período de férias."
        ),
    },
    {
        "title": "Política de Home Office",
        "category": "policy",
        "department": "RH",
        "content": (
            "A empresa adota o modelo híbrido de trabalho, com no mínimo 2 dias presenciais por "
            "semana, definidos junto ao gestor direto. Colaboradores em regime full remoto precisam "
            "de aprovação formal da diretoria. O auxílio home office é de R$ 150,00 mensais, pago "
            "junto com o salário, e cobre despesas com internet e energia."
        ),
    },
    {
        "title": "Procedimento de Reembolso de Despesas",
        "category": "procedure",
        "department": "Financeiro",
        "content": (
            "Reembolsos devem ser solicitados em até 30 dias corridos após a data da despesa, "
            "através do formulário no sistema financeiro interno, anexando a nota fiscal ou recibo. "
            "Despesas acima de R$ 500,00 exigem aprovação prévia do gestor antes da compra. O prazo "
            "de processamento do reembolso é de até 10 dias úteis após a aprovação."
        ),
    },
    {
        "title": "Ficha do Produto: CompanyMind Assistant Pro",
        "category": "product",
        "department": "Produto",
        "content": (
            "O CompanyMind Assistant Pro é o plano corporativo da plataforma, indicado para empresas "
            "com mais de 50 funcionários. Inclui busca ilimitada na base de conhecimento, integração "
            "via MCP com outros sistemas internos, logs de auditoria completos e suporte prioritário. "
            "O plano é cobrado por usuário ativo mensalmente, com desconto de 20% em contratos anuais."
        ),
    },
    {
        "title": "FAQ: Como redefinir minha senha corporativa",
        "category": "faq",
        "department": "TI",
        "content": (
            "Para redefinir a senha corporativa, acesse o portal de identidade em id.empresa.com e "
            "clique em 'Esqueci minha senha'. Um link de redefinição será enviado ao e-mail "
            "corporativo cadastrado, válido por 1 hora. Caso não receba o e-mail, entre em contato "
            "com o suporte de TI pelo canal #suporte-ti no sistema interno de mensagens."
        ),
    },
    {
        "title": "Procedimento de Onboarding de Novos Colaboradores",
        "category": "procedure",
        "department": "RH",
        "content": (
            "No primeiro dia, o colaborador recebe o notebook corporativo, credenciais de acesso e "
            "participa da apresentação institucional com o time de RH. Nas duas primeiras semanas, "
            "são realizados treinamentos obrigatórios de segurança da informação e cultura "
            "organizacional. O período de experiência é de 90 dias, com avaliações formais aos 45 e "
            "aos 90 dias."
        ),
    },
]


def run() -> None:
    for doc in SEED_DOCUMENTS:
        document_id = insert_document(doc["title"], doc["category"], doc["department"])
        chunks = chunk_text(doc["content"])
        embeddings = generate_embeddings_batch(chunks)
        insert_chunks(document_id, chunks, embeddings)
        print(f"Inserido: {doc['title']} ({len(chunks)} chunk(s))")

    print("Seed concluído.")


if __name__ == "__main__":
    run()
