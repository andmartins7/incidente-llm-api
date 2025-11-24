import os
import sys
from github import Github
import openai

def main():
    # Configurações a partir de variáveis de ambiente
    openai_api_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GIT_TOKEN")
    pr_number = os.getenv("PR_NUMBER")
    repo_name = os.getenv("REPO_NAME")

    if not all([openai_api_key, github_token, pr_number, repo_name]):
        print("Faltando alguma variável de ambiente. Verifique OPENAI_API_KEY, GIT_TOKEN, PR_NUMBER, REPO_NAME.")
        sys.exit(1)

    openai.api_key = openai_api_key
    gh = Github(github_token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))

    # Obter os arquivos modificados no PR
    files = pr.get_files()
    diffs = []
    for f in files:
        # Focar em extensões relevantes (ajuste conforme sua stack)
        if f.filename.endswith(('.py', '.js', '.ts')):
            diff_text = f.patch
            if diff_text:
                diffs.append(f"File: {f.filename}\n{diff_text}")

    if not diffs:
        print("Nenhuma mudança relevante detectada para revisão automática.")
        return

    # Construir prompt para OpenAI
    prompt = (
        "Você é um engenheiro sênior de software. "
        "Revise as seguintes mudanças para bugs, segurança, performance, manutenção e estilo de código:\n\n"
        + "\n\n".join(diffs)
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-5.1",
            messages=[
                {"role": "system", "content": "Você é um avaliador de código para Pull Requests."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )
    except Exception as e:
        print("Erro ao chamar API da OpenAI:", e)
        sys.exit(1)

    review_comments = response["choices"][0]["message"]["content"]
    print("Comentários do agente:\n", review_comments)

    # Postar comentário no PR
    try:
        pr.create_issue_comment(f"🤖 Revisão automática:\n\n{review_comments}")
        print("Comentário publicado no PR.")
    except Exception as e:
        print("Erro ao publicar comentário no PR:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
