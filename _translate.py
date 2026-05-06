"""One-shot script to fill empty msgstr in .po files for PT and CS."""
import re
from pathlib import Path

TRANSLATIONS = {
    # English msgid -> (pt, cs)
    "Czech Republic": ("República Checa", "Česká republika"),
    "Portugal": ("Portugal", "Portugalsko"),
    "England": ("Inglaterra", "Anglie"),
    "International": ("Internacional", "Mezinárodní"),
    "About holiday descriptions": ("Sobre as descrições dos feriados", "O popisech svátků"),
    "Help us tell the story": ("Ajude-nos a contar a história", "Pomozte nám vyprávět příběh"),
    "Teachka is still being detailed. Holiday descriptions are a work in progress and not every entry has the depth it deserves yet.": (
        "A Teachka ainda está a ser detalhada. As descrições dos feriados estão em desenvolvimento e nem todas têm ainda a profundidade que merecem.",
        "Teachka se stále vyvíjí. Popisy svátků jsou rozpracované a ne každý záznam má hloubku, kterou si zaslouží.",
    ),
    "If you know the history behind a holiday and would like to contribute, we'd love to hear from you.": (
        "Se conhece a história por trás de um feriado e gostaria de contribuir, gostaríamos muito de saber.",
        "Pokud znáte historii svátku a chtěli byste přispět, rádi se s vámi spojíme.",
    ),
    "Subject too short.": ("Assunto demasiado curto.", "Předmět je příliš krátký."),
    "Please add a bit more detail (at least 10 characters).": (
        "Adicione mais detalhes (pelo menos 10 caracteres).",
        "Přidejte prosím trochu více podrobností (alespoň 10 znaků).",
    ),
    "Bug report": ("Reportar erro", "Hlášení chyby"),
    "Feature request": ("Pedido de funcionalidade", "Žádost o funkci"),
    "Support": ("Suporte", "Podpora"),
    "Send word": ("Envie-nos uma mensagem", "Pošlete zprávu"),
    "Bug reports, questions, feature ideas": (
        "Erros, perguntas, ideias de funcionalidades",
        "Hlášení chyb, dotazy, návrhy funkcí",
    ),
    "Message received": ("Mensagem recebida", "Zpráva přijata"),
    "Your message has been logged. If a reply is needed, we'll write back to the address you left.": (
        "A sua mensagem foi registada. Se for necessária uma resposta, escreveremos para o endereço que indicou.",
        "Vaše zpráva byla zaznamenána. Pokud bude potřeba odpověď, ozveme se na adresu, kterou jste zadali.",
    ),
    "Send another": ("Enviar outra", "Poslat další"),
    "Type of message": ("Tipo de mensagem", "Typ zprávy"),
    "Required": ("Obrigatório", "Povinné"),
    "Something broke. Tell us what, where, and how to reproduce.": (
        "Algo deixou de funcionar. Diga-nos o quê, onde e como reproduzir.",
        "Něco se rozbilo. Řekněte nám co, kde a jak to reprodukovat.",
    ),
    "Stuck or unsure how something works? Ask away.": (
        "Bloqueado ou com dúvidas sobre como algo funciona? Pergunte.",
        "Nevíte si rady nebo jak něco funguje? Zeptejte se.",
    ),
    "Got an idea that would make Teachka better? We're listening.": (
        "Tem uma ideia para melhorar a Teachka? Estamos a ouvir.",
        "Máte nápad, jak Teachku vylepšit? Posloucháme.",
    ),
    "Your message": ("A sua mensagem", "Vaše zpráva"),
    "Message": ("Mensagem", "Zpráva"),
    "Tell us as much or as little as you like. Steps to reproduce help if it is a bug.": (
        "Diga-nos tanto ou tão pouco quanto quiser. Os passos para reproduzir ajudam se for um erro.",
        "Napište tolik nebo málo, kolik chcete. Postup k reprodukci pomáhá, pokud jde o chybu.",
    ),
    "We attach the page URL you were on, your browser version": (
        "Anexamos o URL da página em que estava, a versão do seu navegador",
        "Přikládáme URL stránky, na které jste byli, verzi vašeho prohlížeče",
    ),
    "and your username": ("e o seu nome de utilizador", "a vaše uživatelské jméno"),
    "Send message": ("Enviar mensagem", "Odeslat zprávu"),
    "Message received. We'll be in touch.": (
        "Mensagem recebida. Entraremos em contacto.",
        "Zpráva přijata. Ozveme se.",
    ),
    "How many members per group?": ("Quantos membros por grupo?", "Kolik členů ve skupině?"),
    "A group with this name already exists. Please choose a different name.": (
        "Já existe um grupo com este nome. Escolha outro nome.",
        "Skupina s tímto názvem již existuje. Zvolte prosím jiný název.",
    ),
    "Comma-separated names. (f.e.: \"Toki, Tina, Alice\") | We recommend not using the same exact name for different members": (
        "Nomes separados por vírgula. (ex.: \"Toki, Tina, Alice\") | Recomendamos não usar exatamente o mesmo nome para membros diferentes",
        "Jména oddělená čárkami. (např.: \"Toki, Tina, Alice\") | Doporučujeme nepoužívat stejný název pro různé členy",
    ),
    "Auto-save": ("Guardar automaticamente", "Automatické ukládání"),
    "A column named '%(name)s' already exists in %(definition)s table.": (
        "Já existe uma coluna chamada '%(name)s' na tabela %(definition)s.",
        "Sloupec s názvem '%(name)s' již existuje v tabulce %(definition)s.",
    ),
    "Column '%(name)s' not found.": ("Coluna '%(name)s' não encontrada.", "Sloupec '%(name)s' nenalezen."),
    "A column named '%(name)s' already exists.": (
        "Já existe uma coluna chamada '%(name)s'.",
        "Sloupec s názvem '%(name)s' již existuje.",
    ),
    "An account with this email address already exists.": (
        "Já existe uma conta com este endereço de email.",
        "Účet s tímto e-mailem již existuje.",
    ),
    "An account with this username already exists.": (
        "Já existe uma conta com este nome de utilizador.",
        "Účet s tímto uživatelským jménem již existuje.",
    ),
    "User stats": ("Estatísticas do utilizador", "Statistiky uživatele"),
    "— None —": ("— Nenhum —", "— Žádný —"),
    "Welcome, please check your email to complete your registration.": (
        "Bem-vindo, por favor verifique o seu email para concluir o registo.",
        "Vítejte, zkontrolujte prosím svůj e-mail pro dokončení registrace.",
    ),
    "Registration failed due to an email error. Please try again later.": (
        "O registo falhou devido a um erro de email. Por favor tente novamente mais tarde.",
        "Registrace selhala kvůli chybě e-mailu. Zkuste to prosím později.",
    ),
    "Your account has been successfully activated!": (
        "A sua conta foi ativada com sucesso!",
        "Váš účet byl úspěšně aktivován!",
    ),
    "Activation link is invalid or expired.": (
        "O link de ativação é inválido ou expirou.",
        "Aktivační odkaz je neplatný nebo vypršel.",
    ),
    "You have requested a new password": (
        "Pediu uma nova palavra-passe",
        "Požádali jste o nové heslo",
    ),
    "You will receive a password reset link in the email registered": (
        "Receberá um link de redefinição da palavra-passe no email registado",
        "Na zaregistrovaný e-mail obdržíte odkaz pro obnovení hesla",
    ),
    "Reset link is invalid or expired.": (
        "O link de redefinição é inválido ou expirou.",
        "Odkaz pro obnovení je neplatný nebo vypršel.",
    ),
    "Your password was successfully reset. You may now login again.": (
        "A sua palavra-passe foi redefinida com sucesso. Já pode iniciar sessão novamente.",
        "Vaše heslo bylo úspěšně obnoveno. Nyní se můžete znovu přihlásit.",
    ),
    "If that email is registered you'll receive a reset link shortly.": (
        "Se esse email estiver registado, receberá em breve um link de redefinição.",
        "Pokud je e-mail zaregistrován, brzy obdržíte odkaz pro obnovení.",
    ),
    "Incorrect password. Account not deleted.": (
        "Palavra-passe incorreta. Conta não eliminada.",
        "Nesprávné heslo. Účet nebyl smazán.",
    ),
    "Your account and all associated data have been permanently deleted.": (
        "A sua conta e todos os dados associados foram permanentemente eliminados.",
        "Váš účet a všechna související data byla trvale smazána.",
    ),
}


def parse_msg_block(text, start):
    """Parse msgid and msgstr at given start. Returns (msgid, msgstr_start, msgstr_end_idx_exclusive, msgid_value, msgstr_value)."""
    pass


def patch_po(path: Path, lang_index: int):
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    result = []
    i = 0
    matched = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("msgid "):
            # Collect msgid (multi-line)
            msgid_parts = [line[len("msgid "):]]
            j = i + 1
            while j < len(lines) and lines[j].startswith("\""):
                msgid_parts.append(lines[j])
                j += 1
            # j now at msgstr line
            msgid_value = "".join(eval(p) for p in msgid_parts)
            # Skip the empty msgid (header)
            if msgid_value == "":
                result.append(line)
                i += 1
                continue
            # Now read msgstr block
            if j < len(lines) and lines[j].startswith("msgstr "):
                msgstr_start = j
                msgstr_parts = [lines[j][len("msgstr "):]]
                k = j + 1
                while k < len(lines) and lines[k].startswith("\""):
                    msgstr_parts.append(lines[k])
                    k += 1
                msgstr_value = "".join(eval(p) for p in msgstr_parts)
                if msgstr_value == "" and msgid_value in TRANSLATIONS:
                    translation = TRANSLATIONS[msgid_value][lang_index]
                    # Append msgid lines as-is
                    for p_idx in range(i, j):
                        result.append(lines[p_idx])
                    # Replace msgstr block with single-line translation (escaped)
                    escaped = translation.replace("\\", "\\\\").replace("\"", "\\\"")
                    result.append(f'msgstr "{escaped}"')
                    matched += 1
                    i = k
                    continue
        result.append(line)
        i += 1
    path.write_text("\n".join(result), encoding="utf-8")
    print(f"{path}: {matched} translations applied")


for lang, idx in [("pt", 0), ("cs", 1)]:
    patch_po(Path(f"locale/{lang}/LC_MESSAGES/django.po"), idx)
