import os
import requests
import openai
from github import Github

def get_pr_diff(owner: str, repo_name: str, pr_number: int, github_token: str) -> str:
    """
    Obtém o diff da Pull Request via GitHub API.
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"token {github_token}"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text  # o diff completo como texto

def call_openai_review(diff: str, openai_api_key: str) -> str:
    """
    Envia o diff para OpenAI e obtém uma resposta simples de revisão.
    """
    openai.api_key = openai_api_key
    prompt = (
        "Você é um revisor de código. Analise o seguinte diff de código e indique "
        "possíveis melhorias, erros de estilo ou bugs. Seja objetivo:\n\n"
        f"{diff}\n\n"
        "Por favor, responda em português."
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente inteligente para revisão de código."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.2
    )
    # extraímos o texto da primeira escolha
    review = resp.choices[0].message.content.strip()
    return review

def post_pr_comment(owner: str, repo_name: str, pr_number: int, github_token: str, comment: str):
    """
    Publica um comentário na Pull Request via PyGithub.
    """
    g = Github(github_token)
    repo = g.get_repo(f"{owner}/{repo_name}")
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(comment)

def main():
    # variáveis de ambiente esperadas
    openai_api_key = os.getenv("OPENAI_API_KEY")
    github_token    = os.getenv("GITHUB_TOKEN")
    # as variáveis passadas pelo workflow
    pr_number       = int(os.getenv("PR_NUMBER", "0"))
    repo_full       = os.getenv("REPO_NAME", "")
    # separa owner / repo
    if "/" not in repo_full:
        raise ValueError("REPO_NAME esperado no formato owner/repo")
    owner, repo_name = repo_full.split("/", 1)

    if not openai_api_key or not github_token or pr_number == 0:
        raise RuntimeError("Faltam variáveis de ambiente obrigatórias")

    print(f"Revisando PR #{pr_number} no repositório {owner}/{repo_name}…")

    try:
        diff = get_pr_diff(owner, repo_name, pr_number, github_token)
    except Exception as e:
        print(f"Erro ao obter diff da PR: {e}")
        raise

    print("Diff obtido, chamando OpenAI…")
    try:
        review = call_openai_review(diff, openai_api_key)
    except Exception as e:
        print(f"Erro na chamada à OpenAI: {e}")
        raise

    print("Resposta da OpenAI recebida, publicando comentário na PR…")
    comment_body = (
        "### Revisão automática de código\n\n"
        review + "\n\n"
        "_Este comentário foi gerado automaticamente._"
    )
    try:
        post_pr_comment(owner, repo_name, pr_number, github_token, comment_body)
    except Exception as e:
        print(f"Erro ao postar comentário na PR: {e}")
        raise

    print("Comentário publicado com sucesso.")

if __name__ == "__main__":
    main()
