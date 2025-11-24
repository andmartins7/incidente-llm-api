import os
import sys
import logging
from github import Github, GithubException
import openai
from typing import List

# Configuração de logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-d %H:%M:%S"
)

def get_env_var(name: str, required: bool=True) -> str:
    value = os.getenv(name)
    if required and not value:
        logging.error(f"Variável de ambiente obrigatória faltando: {name}")
        sys.exit(1)
    return value

def filter_relevant_files(files) -> List[str]:
    relevant_ext = ('.py', '.js', '.ts')  # ajuste conforme sua stack
    diffs = []
    for f in files:
        if f.filename.endswith(relevant_ext) and f.patch:
            diffs.append(f"File: {f.filename}\n{f.patch}")
    return diffs

def call_openai_model(api_key: str, diffs: List[str]) -> str:
    openai.api_key = api_key
    prompt = (
        "Você é um engenheiro de software sênior. "
        "Revise as mudanças a seguir focando em: bugs, segurança, performance, manutenção e estilo.\n\n"
        + "\n\n".join(diffs)
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-5.1-codex-mini",
            messages=[
                {"role": "system", "content": "Você é avaliador de código para Pull Requests."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )
        comment = response["choices"][0]["message"]["content"]
        return comment
    except Exception as e:
        logging.error(f"Erro na chamada à API da OpenAI: {e}")
        sys.exit(1)

def post_comment(pr, message: str):
    try:
        pr.create_issue_comment(f"🤖 Revisão automática:\n\n{message}")
        logging.info("Comentário publicado no PR com sucesso.")
    except GithubException as e:
        logging.error(f"Falha ao publicar comentário no PR: {e}")
        sys.exit(1)

def main():
    # Obter variáveis de ambiente
    openai_api_key = get_env_var("OPENAI_API_KEY")
    github_token = os.getenv("GIT_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not github_token:
        logging.error("Não foi encontrado token de GitHub. Variables GIT_TOKEN ou GITHUB_TOKEN devem estar configuradas.")
        sys.exit(1)

    pr_number_str = get_env_var("PR_NUMBER")
    repo_name = get_env_var("REPO_NAME")

    try:
        pr_number = int(pr_number_str)
    except ValueError:
        logging.error(f"PR_NUMBER inválido: {pr_number_str}")
        sys.exit(1)

    gh = Github(github_token)
    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
    except GithubException as e:
        logging.error(f"Erro ao acessar repositório ou Pull Request: {e}")
        sys.exit(1)

    files = pr.get_files()
    diffs = filter_relevant_files(files)
    if not diffs:
        logging.info("Nenhuma mudança relevante detectada para revisão automática.")
        return

    logging.info(f"Processando {len(diffs)} arquivo(s) relevantes para revisão.")

    comment = call_openai_model(openai_api_key, diffs)
    if not comment.strip():
        logging.info("API retornou sem conteúdo. Nada a comentar.")
        return

    post_comment(pr, comment)

if __name__ == "__main__":
    main()
